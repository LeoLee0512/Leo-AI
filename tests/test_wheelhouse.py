"""P0-5: the wheelhouse must be complete, checkable, and honest about itself.

A pinned lock file makes a build *declared*. It does not make it reproducible:
pip still resolves each pin against a live index, so a yanked release or an
unreachable mirror changes the build or stops it. The wheelhouse closes that by
making every wheel a local file with a recorded hash, installed with
``--no-index``.

Most of these tests build a synthetic wheelhouse in ``tmp_path`` rather than
leaning on the real one. That is deliberate. ``wheelhouse/`` is a generated
artifact and is not committed, so a suite that only checked the real directory
would quietly pass on a machine that has never built one -- which is precisely
the machine the check exists for. The synthetic fixtures exercise the failure
paths for real: a missing wheel, a tampered hash, a lock that has drifted.

What none of this proves is that a clean machine can build the product from a
fresh clone. That is F1/F2 in ``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md`` and
stays NOT TESTED until a person runs it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import zipfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
REAL_MANIFEST = REPO / "manifests" / "wheelhouse.json"
REAL_WHEELHOUSE = REPO / "wheelhouse"
DEPENDENCY_LOCK = REPO / "manifests" / "dependency-lock.json"
REQUIREMENTS = REPO / "requirements.lock"


def _tool():
    path = REPO / "tools" / "build_wheelhouse.py"
    assert path.is_file(), f"wheelhouse tool missing at {path}"
    spec = importlib.util.spec_from_file_location("leo_build_wheelhouse", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_wheel(directory: pathlib.Path, name: str, version: str,
                tags: str = "py3-none-any") -> pathlib.Path:
    """A structurally real wheel file, so file-name parsing is exercised."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}-{version}-{tags}.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{name}/__init__.py", "")
        archive.writestr(f"{name}-{version}.dist-info/METADATA",
                         f"Name: {name}\nVersion: {version}\n")
    return path


@pytest.fixture
def wheelhouse(tmp_path):
    """A synthetic wheelhouse plus the lock file that should describe it."""
    tool = _tool()
    directory = tmp_path / "wheelhouse"
    _fake_wheel(directory, "alpha", "1.0")
    _fake_wheel(directory, "beta", "2.5", tags="cp312-cp312-win_amd64")
    requirements = tmp_path / "requirements.lock"
    requirements.write_text("# comment\nalpha==1.0\nbeta==2.5\n", encoding="utf-8")
    manifest = tool.build_manifest(
        requirements, directory, pathlib.Path("python"), index="https://example.invalid/simple"
    )
    return {
        "tool": tool,
        "dir": directory,
        "requirements": requirements,
        "manifest": manifest,
        "text": requirements.read_text(encoding="utf-8"),
    }


# ------------------------------------------------------------- the happy path


def test_a_complete_wheelhouse_verifies(wheelhouse):
    problems = wheelhouse["tool"].verify(
        wheelhouse["manifest"], wheelhouse["dir"], wheelhouse["text"]
    )
    assert problems == [], problems


def test_the_manifest_records_the_tags_a_reviewer_needs(wheelhouse):
    """filename, package, version, python/abi/platform tag, hash, size, origin."""
    entries = {entry["package"]: entry for entry in wheelhouse["manifest"]["wheels"]}
    beta = entries["beta"]
    assert beta["version"] == "2.5"
    assert beta["python_tag"] == "cp312"
    assert beta["abi_tag"] == "cp312"
    assert beta["platform_tag"] == "win_amd64"
    assert len(beta["sha256"]) == 64
    assert beta["size_bytes"] > 0
    assert beta["origin"] == "published-wheel"
    assert entries["alpha"]["platform_tag"] == "any"


def test_the_manifest_records_how_it_was_resolved(wheelhouse):
    """Provenance without the resolution metadata is not provenance."""
    resolution = wheelhouse["manifest"]["resolution"]
    assert resolution["index_url"] == "https://example.invalid/simple"
    assert resolution["only_binary"] is True
    for field in ("built_at", "pip", "python_version", "host_platform", "host_machine"):
        assert resolution[field], f"resolution.{field} is empty"


def test_the_offline_install_command_disables_the_index(wheelhouse):
    """--find-links on its own still falls back to PyPI; --no-index is the point."""
    command = wheelhouse["tool"].install_command(
        pathlib.Path("python"), wheelhouse["dir"], wheelhouse["requirements"]
    )
    assert "--no-index" in command
    assert "--find-links" in command
    assert command[command.index("--find-links") + 1] == str(wheelhouse["dir"])
    assert "--no-index" in wheelhouse["manifest"]["offline_install"]["flags"]


# ------------------------------------------------------------ the failure paths


def test_a_missing_wheel_file_fails_verification(wheelhouse):
    """A manifest entry whose file is gone is not a warning."""
    (wheelhouse["dir"] / wheelhouse["manifest"]["wheels"][0]["filename"]).unlink()
    problems = wheelhouse["tool"].verify(
        wheelhouse["manifest"], wheelhouse["dir"], wheelhouse["text"]
    )
    assert "missing-file" in {p["kind"] for p in problems}, problems


def test_a_tampered_wheel_fails_verification(wheelhouse):
    """Changing a wheel's bytes must be caught by its recorded hash."""
    target = wheelhouse["dir"] / wheelhouse["manifest"]["wheels"][0]["filename"]
    with zipfile.ZipFile(target, "a") as archive:
        archive.writestr("evil.py", "import os; os.system('...')\n")
    kinds = {
        p["kind"]
        for p in wheelhouse["tool"].verify(
            wheelhouse["manifest"], wheelhouse["dir"], wheelhouse["text"]
        )
    }
    assert "hash-mismatch" in kinds, kinds


def test_a_tampered_manifest_hash_fails_verification(wheelhouse):
    """The other direction: editing the manifest to match a swapped file."""
    manifest = json.loads(json.dumps(wheelhouse["manifest"]))
    manifest["wheels"][0]["sha256"] = "0" * 64
    kinds = {
        p["kind"]
        for p in wheelhouse["tool"].verify(manifest, wheelhouse["dir"], wheelhouse["text"])
    }
    assert "hash-mismatch" in kinds, kinds


def test_a_wheel_missing_for_a_pinned_package_fails(wheelhouse):
    """lock -> wheelhouse: every pin must have a wheel."""
    requirements = wheelhouse["text"] + "gamma==9.9\n"
    kinds = {
        p["kind"]
        for p in wheelhouse["tool"].verify(wheelhouse["manifest"], wheelhouse["dir"], requirements)
    }
    assert "missing-wheel" in kinds, kinds


def test_a_wheel_at_the_wrong_version_fails(wheelhouse):
    """A wheel for the right package at the wrong version is not coverage."""
    requirements = "alpha==1.0\nbeta==9.9\n"
    problems = wheelhouse["tool"].verify(
        wheelhouse["manifest"], wheelhouse["dir"], requirements
    )
    assert "version-mismatch" in {p["kind"] for p in problems}, problems


def test_a_wheel_nobody_pinned_fails(wheelhouse):
    """wheelhouse -> lock: the correspondence is checked in both directions.

    An extra wheel is how something unreviewed gets installed by a build that
    calls itself locked.
    """
    problems = wheelhouse["tool"].verify(
        wheelhouse["manifest"], wheelhouse["dir"], "alpha==1.0\n"
    )
    assert "unlocked-package" in {p["kind"] for p in problems}, problems


def test_an_undeclared_wheel_in_the_directory_fails(wheelhouse):
    """A file dropped into the wheelhouse must not be installable unnoticed."""
    _fake_wheel(wheelhouse["dir"], "smuggled", "0.1")
    problems = wheelhouse["tool"].verify(
        wheelhouse["manifest"], wheelhouse["dir"], wheelhouse["text"]
    )
    assert "undeclared-wheel" in {p["kind"] for p in problems}, problems


def test_a_changed_lock_file_fails_verification(wheelhouse):
    """A wheelhouse built for a different lock is not this build's wheelhouse."""
    problems = wheelhouse["tool"].verify(
        wheelhouse["manifest"], wheelhouse["dir"], wheelhouse["text"] + "# edited\n"
    )
    assert "requirements-drift" in {p["kind"] for p in problems}, problems


def test_an_unpinned_requirement_is_rejected_outright(wheelhouse):
    """A lock file with a range in it is not a lock file."""
    with pytest.raises(wheelhouse["tool"].WheelhouseError, match="not a pin"):
        wheelhouse["tool"].parse_requirements("alpha>=1.0\n")


def test_building_a_manifest_fails_when_a_pin_has_no_wheel(tmp_path, wheelhouse):
    """The build refuses rather than producing a wheelhouse with a hole in it."""
    requirements = tmp_path / "more.lock"
    requirements.write_text("alpha==1.0\nbeta==2.5\ngamma==0.1\n", encoding="utf-8")
    with pytest.raises(wheelhouse["tool"].WheelhouseError, match="no wheel was obtained"):
        wheelhouse["tool"].build_manifest(
            requirements, wheelhouse["dir"], pathlib.Path("python")
        )


def test_a_locally_built_wheel_must_be_declared_and_carry_its_sdist_hash(wheelhouse):
    """The sdist escape hatch cannot be used without saying so."""
    tool = wheelhouse["tool"]
    manifest = json.loads(json.dumps(wheelhouse["manifest"]))
    manifest["wheels"][0]["origin"] = "built-from-sdist"
    kinds = {
        p["kind"] for p in tool.verify(manifest, wheelhouse["dir"], wheelhouse["text"])
    }
    assert "undeclared-sdist-build" in kinds, kinds
    assert "missing-sdist-hash" in kinds, kinds


def test_an_unknown_origin_fails(wheelhouse):
    manifest = json.loads(json.dumps(wheelhouse["manifest"]))
    manifest["wheels"][0]["origin"] = "somewhere"
    kinds = {
        p["kind"]
        for p in wheelhouse["tool"].verify(manifest, wheelhouse["dir"], wheelhouse["text"])
    }
    assert "unknown-origin" in kinds, kinds


def test_verification_catches_a_forged_tag(wheelhouse):
    """A manifest entry must describe the file it names, not something else."""
    manifest = json.loads(json.dumps(wheelhouse["manifest"]))
    entry = next(e for e in manifest["wheels"] if e["package"] == "beta")
    entry["platform_tag"] = "manylinux_2_17_x86_64"
    problems = wheelhouse["tool"].verify(manifest, wheelhouse["dir"], wheelhouse["text"])
    assert "tag-mismatch" in {p["kind"] for p in problems}, problems


# -------------------------------------------------- the declared build policy


def test_the_dependency_lock_declares_the_wheelhouse():
    data = json.loads(DEPENDENCY_LOCK.read_text(encoding="utf-8"))
    assert data["vendored_wheelhouse"] is True, (
        "the wheelhouse exists now; this must say so, and must go back to false "
        "if it is ever removed"
    )
    wheelhouse = data["wheelhouse"]
    assert wheelhouse["manifest"] == "manifests/wheelhouse.json"
    assert "--no-index" in wheelhouse["offline_install"]
    assert wheelhouse["committed"] is False, (
        "the wheel binaries are not in git; claiming otherwise would mislead anyone "
        "trying to build from a clone"
    )
    assert wheelhouse["build"] and wheelhouse["verify"], (
        "a reader must be told how to produce and check one"
    )


def test_source_builds_are_named_rather_than_implicit():
    """Which packages may be built from sdist is declared data, not a flag."""
    data = json.loads(DEPENDENCY_LOCK.read_text(encoding="utf-8"))
    allowed = data.get("sdist_build_allowed")
    assert isinstance(allowed, list), "the policy must be present even when empty"
    assert data.get("sdist_build_allowed_note", "").strip(), (
        "an allowance without a stated reason is one nobody can review"
    )
    tool = _tool()
    canonical = {tool.canonical_name(name) for name in allowed}
    pins = {
        pin["canonical_name"]
        for pin in tool.parse_requirements(REQUIREMENTS.read_text(encoding="utf-8"))
    }
    assert canonical <= pins, (
        f"sdist_build_allowed names package(s) not in the lock: {sorted(canonical - pins)}"
    )


def test_the_wheelhouse_is_ignored_but_its_manifest_is_tracked():
    rules = [
        line.strip()
        for line in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert "wheelhouse/" in rules, "wheel binaries must not enter git history"
    assert not any("wheelhouse.json" in rule for rule in rules), (
        "the manifest is the committed, reviewable half and must stay tracked"
    )
    # And ask git rather than inferring: an ignore rule that does not match is
    # not the same as a file that is actually in the index.
    import subprocess

    done = subprocess.run(
        ["git", "check-ignore", "-q", "manifests/wheelhouse.json"], cwd=REPO, timeout=120
    )
    assert done.returncode != 0, "manifests/wheelhouse.json is ignored by git"


# --------------------------------------- the real wheelhouse, when it is there


def test_the_committed_manifest_matches_the_lock_file():
    """Checkable on any machine: no wheel files needed, only the manifest.

    This is the part of the wheelhouse guarantee that survives not having built
    one -- the manifest must still cover every pin at the right version.
    """
    if not REAL_MANIFEST.is_file():
        pytest.skip("no wheelhouse manifest yet; run tools/build_wheelhouse.py build")
    tool = _tool()
    manifest = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
    text = REQUIREMENTS.read_text(encoding="utf-8")
    assert manifest["requirements_sha256"] == tool.sha256_requirements(text), (
        "requirements.lock has changed since the wheelhouse manifest was built; "
        "re-run tools/build_wheelhouse.py build"
    )
    pins = tool.parse_requirements(text)
    covered = {
        (entry["canonical_name"], entry["version"]) for entry in manifest["wheels"]
    }
    missing = [
        pin["requirement"]
        for pin in pins
        if (pin["canonical_name"], pin["version"]) not in covered
    ]
    assert not missing, f"the manifest does not cover: {missing}"
    assert manifest["wheel_count"] == len(manifest["wheels"])


def test_the_real_wheelhouse_verifies_when_it_is_present():
    """A local wheelhouse must actually match its manifest, hash by hash."""
    if not REAL_MANIFEST.is_file() or not REAL_WHEELHOUSE.is_dir():
        pytest.skip("no local wheelhouse; run tools/build_wheelhouse.py build")
    tool = _tool()
    problems = tool.verify(
        json.loads(REAL_MANIFEST.read_text(encoding="utf-8")),
        REAL_WHEELHOUSE,
        REQUIREMENTS.read_text(encoding="utf-8"),
    )
    assert problems == [], problems


def test_every_locally_built_wheel_in_the_real_manifest_is_declared():
    """No silent source build may have crept into the shipped manifest."""
    if not REAL_MANIFEST.is_file():
        pytest.skip("no wheelhouse manifest yet")
    tool = _tool()
    manifest = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
    allowed = {tool.canonical_name(n) for n in tool.sdist_build_allowed()}
    for entry in manifest["wheels"]:
        if entry.get("origin") != "built-from-sdist":
            continue
        assert entry["canonical_name"] in allowed, (
            f"{entry['filename']} was built from source without being declared"
        )
        assert len(entry.get("sdist_sha256", "")) == 64
        assert "not byte-identical" in entry.get("reproducibility", ""), (
            "a locally built wheel must not imply a byte-for-byte guarantee it does "
            "not have"
        )


def test_a_verified_wheelhouse_is_not_recorded_as_a_clean_machine_build():
    """The scope limit must be stated where someone reading the output will see it."""
    source = (REPO / "tools" / "build_wheelhouse.py").read_text(encoding="utf-8")
    assert "P0_MANUAL_ACCEPTANCE_CHECKLIST" in source, (
        "the tool must point at the manual items it does not discharge"
    )
    assert "NOT TESTED" in source


# ------------------------------------------- the environment the build runs on


def test_environment_audit_accepts_an_exact_match(monkeypatch):
    """A venv holding exactly the locked set has no problems."""
    tool = _tool()
    listing = json.dumps(
        [{"name": "alpha", "version": "1.0"}, {"name": "beta", "version": "2.5"}]
    )
    monkeypatch.setattr(
        tool.subprocess, "run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": listing, "stderr": ""})(),
    )
    assert tool.audit_environment(pathlib.Path("python"), "alpha==1.0\nbeta==2.5\n") == []


@pytest.mark.parametrize(
    "installed, requirements, expected",
    [
        ([{"name": "alpha", "version": "1.0"}], "alpha==1.0\nbeta==2.5\n", "not-installed"),
        ([{"name": "alpha", "version": "9.9"}], "alpha==1.0\n", "version-drift"),
        (
            [{"name": "alpha", "version": "1.0"}, {"name": "sneaky", "version": "0.1"}],
            "alpha==1.0\n",
            "undeclared-package",
        ),
    ],
)
def test_environment_audit_catches_drift(monkeypatch, installed, requirements, expected):
    """Each way a build environment can stop being the declared one."""
    tool = _tool()
    listing = json.dumps(installed)
    monkeypatch.setattr(
        tool.subprocess, "run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": listing, "stderr": ""})(),
    )
    problems = tool.audit_environment(pathlib.Path("python"), requirements)
    assert expected in {p["kind"] for p in problems}, problems


def test_environment_audit_ignores_only_venv_bootstrap_packages(monkeypatch):
    """pip and setuptools come with a venv; anything else must be declared."""
    tool = _tool()
    listing = json.dumps(
        [
            {"name": "alpha", "version": "1.0"},
            {"name": "pip", "version": "24.3.1"},
            {"name": "wheel", "version": "0.45"},
        ]
    )
    monkeypatch.setattr(
        tool.subprocess, "run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": listing, "stderr": ""})(),
    )
    assert tool.audit_environment(pathlib.Path("python"), "alpha==1.0\n") == []


def test_the_hermetic_build_audits_its_environment():
    """The build must check its inputs, not just assert the lock file exists.

    Until this was added, "built from requirements.lock" described an intention:
    the build ran on whatever .venv happened to contain.
    """
    script = (REPO / "tools" / "build_launcher.ps1").read_text(encoding="utf-8")
    assert "audit-env" in script, "the hermetic build must audit its environment"
    index = script.index("audit-env")
    following = script[index: index + 600]
    assert "throw" in following, (
        "a mismatched build environment must stop the build, not print a warning"
    )


def test_the_provisioner_refuses_to_reach_for_an_index_unasked():
    """Falling back to PyPI silently is the failure the wheelhouse exists to stop."""
    script = (REPO / "tools" / "provision_venv.ps1").read_text(encoding="utf-8")
    assert "--no-index" in script
    assert "AllowIndex" in script, "reaching for an index must be an explicit choice"
    assert "throw" in script, "no wheelhouse and no -AllowIndex must fail, not proceed"
    assert "audit-env" in script, "the provisioner must check what it produced"


def test_the_build_documentation_states_the_sdist_exception():
    """A reader must not have to discover proxy_tools from a build failure."""
    document = REPO / "docs" / "BUILD.md"
    assert document.is_file(), "there must be build documentation"
    text = document.read_text(encoding="utf-8")
    assert "proxy_tools" in text
    assert "--no-index" in text
    assert "NOT TESTED" in text, (
        "the build documentation must say which acceptance items it does not discharge"
    )
