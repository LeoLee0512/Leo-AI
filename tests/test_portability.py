"""P0-4: no source file may be bound to one machine.

A static scan only. It cannot tell you the app installs and starts for someone
else -- that needs a real fresh Windows account and a WSL user who is not
``leo``, and neither can be self-certified from inside this environment. Those
remain NOT TESTED in ``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md``.

Keeping the two apart is the point: a green scan here is necessary, not
sufficient, and must never be reported as a successful portability acceptance.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]


def _scanner():
    path = REPO / "tools" / "portability_check.py"
    assert path.is_file(), f"portability scanner missing at {path}"
    spec = importlib.util.spec_from_file_location("leo_portability_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_hard_machine_bindings_in_tracked_sources():
    """Every remaining machine-specific value must be overridable."""
    scanner = _scanner()
    hard, _configurable, _historical = scanner.partition_findings(scanner.scan())
    assert not hard, "machine-bound paths found:\n" + "\n".join(
        f"  {f['file']}:{f['line']}  {f['rule']}  {f['text']}" for f in hard
    )


def _historical_fixture(
    scanner,
    tmp_path,
    monkeypatch,
    *,
    tracked_rel="governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md",
    policy_rel="governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md",
    text='source = "C:/Users/reviewer/Desktop/pinns/model.pt"\n',
    finding_type="windows-user-home",
):
    target = tmp_path / pathlib.PurePosixPath(tracked_rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    policy_target = tmp_path / scanner.HISTORICAL_EVIDENCE_POLICY
    policy_target.parent.mkdir(parents=True, exist_ok=True)
    policy_target.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "file": policy_rel,
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "classification": "immutable-historical-evidence",
                        "finding_type": finding_type,
                        "expected_occurrences": 1,
                        "ruling": "test fixture ruling",
                        "constraint": "test fixture constraint",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(scanner, "REPO", tmp_path)
    monkeypatch.setattr(scanner, "tracked_files", lambda: [target])
    return target


def test_exact_path_hash_and_finding_are_reported_as_historical_evidence():
    """Every remaining finding is an approved, exactly matched immutable evidence record.

    The set is pinned file by file: an absolute path appearing anywhere else fails
    this test instead of blending into a count.
    """

    scanner = _scanner()
    hard, configurable, historical = scanner.partition_findings(scanner.scan())
    assert not hard
    assert len(historical) == 8
    assert not [f for f in historical if f["configurable_default"]]
    assert {(f["file"], f["rule"], f["line"]) for f in historical} == {
        ("governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md", "windows-user-home", 58),
        ("governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md", "windows-user-home", 170),
        ("governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md", "windows-user-home", 407),
        ("experiments/poisson1d/environment_b_qualification.json", "windows-user-home", 42),
        ("experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json", "windows-user-home", 103),
        ("experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json", "desktop-path", 103),
        ("experiments/poisson1d/runs/repro-envb-r2/POST_AUDIT_ANNOTATION.md", "windows-user-home", 19),
        ("experiments/poisson2d/environment_b_qualification.json", "windows-user-home", 46),
    }
    assert {f["audit_marker"] for f in historical} == {
        "EXEMPT-HISTORICAL-EVIDENCE"
    }
    assert configurable


def test_mutating_approved_historical_bytes_invalidates_the_classification(
    tmp_path, monkeypatch
):
    scanner = _scanner()
    target = _historical_fixture(scanner, tmp_path, monkeypatch)
    _hard, _configurable, historical = scanner.partition_findings(scanner.scan())
    assert len(historical) == 1

    target.write_text(
        'source = "C:/Users/reviewer/Desktop/pinns/model.pt" # mutated\n',
        encoding="utf-8",
    )
    hard, _configurable, historical = scanner.partition_findings(scanner.scan())
    assert [f["rule"] for f in hard] == ["windows-user-home"]
    assert not historical


def test_identical_bytes_at_a_different_path_are_not_classified(tmp_path, monkeypatch):
    scanner = _scanner()
    _historical_fixture(
        scanner,
        tmp_path,
        monkeypatch,
        tracked_rel="governance/copied-audit.md",
    )
    hard, _configurable, historical = scanner.partition_findings(scanner.scan())
    assert [f["file"] for f in hard] == ["governance/copied-audit.md"]
    assert not historical


@pytest.mark.parametrize(
    "tracked_rel",
    [
        "leo_shell/runtime_probe.py",
        "tools/build_probe.ps1",
        "tools/deploy_probe.ps1",
        "manifests/config_probe.json",
        # the approved scope extension opened experiments/ for *evidence*; the driver
        # scripts that wrote that evidence sit in the same tree and stay out of reach
        "experiments/poisson2d/qualify_environment_b.py",
        "experiments/poisson1d/run_probe.ps1",
        "specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json",
        "pinn/experiments2d/runner2d.py",
    ],
)
def test_consumed_sources_cannot_inherit_the_historical_classification(
    tracked_rel, tmp_path, monkeypatch
):
    scanner = _scanner()
    _historical_fixture(
        scanner,
        tmp_path,
        monkeypatch,
        tracked_rel=tracked_rel,
        policy_rel=tracked_rel,
    )
    with pytest.raises(RuntimeError, match="non-evidence file"):
        scanner.scan()


@pytest.mark.parametrize(
    ("policy_rel", "message"),
    [
        ("experiments/poisson1d/*.json", "wildcard or pattern"),
        ("experiments/poisson1d/runs/?/PROVENANCE_MANIFEST.json", "wildcard or pattern"),
        ("experiments/poisson1d/", "directory"),
    ],
)
def test_the_classification_cannot_be_written_as_a_pattern_or_a_directory(
    policy_rel, message, tmp_path, monkeypatch
):
    """A pattern would let one approval cover files nobody reviewed."""

    scanner = _scanner()
    _historical_fixture(
        scanner,
        tmp_path,
        monkeypatch,
        tracked_rel="experiments/poisson1d/evidence.json",
        policy_rel=policy_rel,
    )
    with pytest.raises(RuntimeError, match=message):
        scanner.scan()


def test_a_classification_without_a_human_ruling_is_refused(tmp_path, monkeypatch):
    """An entry nobody signed is an exemption nobody can review."""

    scanner = _scanner()
    _historical_fixture(
        scanner,
        tmp_path,
        monkeypatch,
        tracked_rel="experiments/poisson1d/evidence.json",
        policy_rel="experiments/poisson1d/evidence.json",
    )
    policy_target = tmp_path / scanner.HISTORICAL_EVIDENCE_POLICY
    document = json.loads(policy_target.read_text(encoding="utf-8"))
    document["entries"][0].pop("ruling")
    policy_target.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(RuntimeError, match="has no ruling"):
        scanner.scan()


def test_an_approved_evidence_record_outside_governance_is_classified(tmp_path, monkeypatch):
    """What the extension is for: an immutable experiment record can now be approved.

    The match stays exactly as strict -- file, hash, finding type, occurrence count.
    """

    scanner = _scanner()
    _historical_fixture(
        scanner,
        tmp_path,
        monkeypatch,
        tracked_rel="experiments/poisson2d/environment_b_qualification.json",
        policy_rel="experiments/poisson2d/environment_b_qualification.json",
        text='{"constructionB": "venv at C:/Users/reviewer/LeoAI-envB2D/venv"}\n',
    )
    hard, _configurable, historical = scanner.partition_findings(scanner.scan())
    assert not hard
    assert [f["file"] for f in historical] == [
        "experiments/poisson2d/environment_b_qualification.json"
    ]


def test_unapproved_finding_type_in_approved_file_remains_hard(tmp_path, monkeypatch):
    scanner = _scanner()
    _historical_fixture(
        scanner,
        tmp_path,
        monkeypatch,
        text=(
            'windows = "C:/Users/reviewer/Desktop/pinns/model.pt"\n'
            'linux = "/home/reviewer/pinns/model.pt"\n'
        ),
    )
    hard, _configurable, historical = scanner.partition_findings(scanner.scan())
    assert [f["rule"] for f in historical] == ["windows-user-home"]
    assert [f["rule"] for f in hard] == ["linux-user-home"]


def test_human_output_keeps_the_historical_findings_visible(capsys, monkeypatch):
    scanner = _scanner()
    monkeypatch.setattr("sys.argv", ["portability_check.py"])
    assert scanner.main() == 0
    output = capsys.readouterr().out
    assert output.count("EXEMPT-HISTORICAL-EVIDENCE") == 8
    assert "8 historical evidence finding(s)" in output
    for approved in (
        "experiments/poisson1d/environment_b_qualification.json",
        "experiments/poisson2d/environment_b_qualification.json",
    ):
        assert approved in output, "an approved finding must stay visible, not vanish"


def test_the_scanner_actually_detects_a_binding(tmp_path, monkeypatch):
    """Negative control: a planted personal path must be caught.

    Without this the suite would pass just as happily if the scanner's patterns
    stopped matching anything at all.
    """
    scanner = _scanner()
    planted = REPO / "tools" / "_portability_probe.tmp.py"
    planted.write_text(
        'LEAN = "/home/someone/.elan/toolchains/x"\n', encoding="utf-8"
    )
    try:
        monkeypatch.setattr(scanner, "tracked_files", lambda: [planted])
        findings = scanner.scan()
        rules = {f["rule"] for f in findings}
        assert "linux-user-home" in rules, findings
    finally:
        planted.unlink(missing_ok=True)


def test_lean_math_is_not_pinned_to_one_home_or_toolchain():
    """The specific binding that made lean-math unusable for anyone else."""
    source = (REPO / "skills" / "lean-math" / "kernel.py").read_text(encoding="utf-8")
    assert "/home/leo" not in source
    assert "v4.34.0-rc2" not in source
    for name in ("LEO_LEAN_TOOLCHAIN", "LEO_LEAN_PROJECT", "LEO_MATHLIB_DIR"):
        assert name in source, f"{name} must be an available override"


def test_wsl_location_is_configurable():
    """distro, user and skills path must all be settable from the environment."""
    source = (REPO / "tools" / "sync_skills.py").read_text(encoding="utf-8")
    for name in ("LEO_WSL_DISTRO", "LEO_WSL_USER", "LEO_WSL_SKILLS"):
        assert name in source, f"{name} must be an available override"


def test_deploy_does_not_assert_one_literal_install_path():
    """The deploy guard must check that a target is a Leo install, not a Desktop."""
    source = (REPO / "tools" / "deploy_release.ps1").read_text(encoding="utf-8")
    assert "Assert-ExactPath" not in source, (
        "the exact-path guard pinned deployment to one machine"
    )
    assert "Assert-LooksLikeAppRoot" in source, (
        "the safety guard must remain, checking structure instead of a literal path"
    )


# ------------------------------------------------------- exemption discipline
#
# The scanner exempts some files from the literal-pattern rules. That mechanism
# is the obvious way to make this gate meaningless: exempt the file, get a green
# scan, ship the binding. These tests are what stop that. They do not check that
# the current exemptions are convenient -- they check that no exemption can ever
# cover something the app, the build or the installer actually reads.


def test_no_executable_or_consumed_file_is_exempt():
    """Exemptions may only cover prose, frozen evidence, and the scanner.

    Walks every tracked file rather than the exemption list, so a future entry
    that quietly covers a .py/.ps1/.js/.json is caught here, not in production.
    """
    scanner = _scanner()
    smuggled = []
    for path in scanner.tracked_files():
        rel = path.relative_to(REPO).as_posix()
        if not scanner.is_exempt(rel):
            continue
        kind = scanner.exemption_kind(rel)
        if kind is None:
            smuggled.append(rel)
    assert not smuggled, (
        "these files are exempt from the portability scan but are not prose, "
        "frozen evidence or the scanner itself:\n  " + "\n  ".join(smuggled)
    )


def test_every_exemption_kind_is_explained():
    """An exemption without a stated reason is an exemption nobody can review."""
    scanner = _scanner()
    for kind in ("frozen-evidence", "documentation", "the-scanner-itself"):
        assert scanner.EXEMPT_KINDS.get(kind, "").strip(), f"{kind} has no stated reason"
    used = {
        scanner.exemption_kind(p.relative_to(REPO).as_posix())
        for p in scanner.tracked_files()
        if scanner.is_exempt(p.relative_to(REPO).as_posix())
    }
    assert used <= set(scanner.EXEMPT_KINDS), f"undeclared exemption kind(s): {used}"


def test_a_binding_in_a_consumed_file_is_still_caught(tmp_path, monkeypatch):
    """Negative control for the class exemption.

    docs/*.md became exempt as a class so that writing a report about a path no
    longer turned the suite red. This asserts the same path in a file that *is*
    consumed is still a finding -- i.e. that the widening did not leak.
    """
    scanner = _scanner()
    planted = REPO / "tools" / "_exempt_leak_probe.tmp.py"
    planted.write_text('WSL = "/home/someone/skills"\n', encoding="utf-8")
    try:
        monkeypatch.setattr(scanner, "tracked_files", lambda: [planted])
        hard = [f for f in scanner.scan() if not f["configurable_default"]]
        assert [f["rule"] for f in hard] == ["linux-user-home"], hard
    finally:
        planted.unlink(missing_ok=True)


def test_allow_marker_waives_only_the_rule_it_names(tmp_path, monkeypatch):
    """The per-line escape hatch must be rule-specific, not a blanket mute."""
    scanner = _scanner()
    planted = REPO / "tools" / "_allow_marker_probe.tmp.py"
    planted.write_text(
        'HINT = "/home/someone/.elan"  # portability-allow: linux-user-home\n'
        'OTHER = "C:/Users/someone/AppData"  # portability-allow: linux-user-home\n',
        encoding="utf-8",
    )
    try:
        monkeypatch.setattr(scanner, "tracked_files", lambda: [planted])
        rules = {f["rule"] for f in scanner.scan()}
        assert "linux-user-home" not in rules, "the named rule should have been waived"
        assert "windows-user-home" in rules, (
            "a marker naming one rule must not suppress a different binding"
        )
    finally:
        planted.unlink(missing_ok=True)
