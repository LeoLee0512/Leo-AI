"""Build, describe and verify an offline wheelhouse for the Leo AI Studio build.

Why this exists
---------------
``requirements.lock`` pins versions, which makes the build *declared*. It does
not make it *reproducible*: pip still resolves each pin against a live index, so
the build depends on that index continuing to serve those files, unchanged. A
yanked release, a re-uploaded artifact or an unreachable mirror all turn a
"pinned" build into a different build, or no build at all.

A wheelhouse closes that: every wheel is a local file with a recorded SHA-256,
and installation runs with ``--no-index``, so there is no index to resolve
against and nothing to drift.

What this deliberately does not claim
-------------------------------------
Generating a wheelhouse here proves that *this* machine can produce and verify
one. It does not prove a clean machine can build the product from a fresh clone
-- that is a manual acceptance item (F1/F2 in the historical manual checklist
preserved in ``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md``) and stays NOT TESTED until someone
runs it. The wheel binaries are also not committed to git: they are large, and a
manifest with hashes is what makes them checkable. ``wheelhouse/`` is ignored;
``manifests/wheelhouse.json`` is tracked.

Usage
-----
    python tools/build_wheelhouse.py build      # download wheels + write manifest
    python tools/build_wheelhouse.py verify     # check manifest, hashes, lock coverage
    python tools/build_wheelhouse.py install --python <interpreter>   # offline install
    python tools/build_wheelhouse.py audit-env --python <interpreter>  # env == lock?
    python tools/build_wheelhouse.py print-install-command

``build`` refuses source distributions (``--only-binary=:all:``): a package with
no wheel for this platform is a hard failure with the package named, never a
silent fall back to building from source or to the index at install time.

The one exception is explicit and recorded. ``proxy_tools==0.1.0`` is published
only as an sdist, so no wheelhouse of this dependency set can be built from
published wheels alone. Rather than let that quietly reintroduce an index at
install time, packages allowed to be built locally are named in
``manifests/dependency-lock.json`` under ``sdist_build_allowed``, the sdist's own
SHA-256 goes into the wheelhouse manifest beside the wheel built from it, and the
entry is marked ``origin: built-from-sdist``. A locally built wheel is *not*
byte-identical across machines the way a published one is; the manifest says so
rather than implying a guarantee that does not hold. Anything not on that list
with no wheel is still a hard failure.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import platform
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_WHEELHOUSE = REPO / "wheelhouse"
DEFAULT_MANIFEST = REPO / "manifests" / "wheelhouse.json"
DEFAULT_REQUIREMENTS = REPO / "requirements.lock"
DEPENDENCY_LOCK = REPO / "manifests" / "dependency-lock.json"

MANIFEST_SCHEMA_VERSION = 1

#: PEP 427 wheel file name:
#:   {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl
_WHEEL_NAME = re.compile(
    r"""\A
    (?P<distribution>[^-]+)
    -(?P<version>[^-]+)
    (?:-(?P<build>\d[^-]*))?
    -(?P<python_tag>[^-]+)
    -(?P<abi_tag>[^-]+)
    -(?P<platform_tag>[^-]+)
    \.whl\Z
    """,
    re.VERBOSE,
)


class WheelhouseError(RuntimeError):
    """A condition that must stop the build rather than degrade it."""


def sdist_build_allowed(lock_path: pathlib.Path = DEPENDENCY_LOCK) -> list[str]:
    """Packages this project has decided may be built from source, canonicalised.

    Kept in the dependency lock rather than in a command-line flag: which
    packages are allowed to be built locally is a property of the declared build
    inputs and belongs where a reviewer will look for it, not in whatever someone
    happened to type. An empty list means "published wheels only".
    """
    if not lock_path.is_file():
        return []
    data = json.loads(lock_path.read_text(encoding="utf-8"))
    return [canonical_name(name) for name in data.get("sdist_build_allowed", [])]


# ------------------------------------------------------------------ helpers


def canonical_name(name: str) -> str:
    """PEP 503 normalisation, so ``clr_loader`` and ``clr-loader`` are one package."""
    return re.sub(r"[-_.]+", "-", name).lower()


def sha256_requirements(text: str) -> str:
    """Identity of a lock file, over its *normalised text*, not its raw bytes.

    .gitattributes checks this repository out with CRLF on Windows and LF
    elsewhere, so the same committed lock file has two different byte hashes
    depending on the machine. Hashing the decoded text makes a wheelhouse
    manifest built on Windows verifiable on Linux, which is the whole point of
    recording it.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_requirements(text: str) -> list[dict]:
    """Every ``name==version`` pin in a lock file, in file order.

    Anything that is not a plain pin is an error rather than a skip: a lock file
    that quietly contains a range is not a lock file, and letting it through here
    is how an unpinned dependency reaches a build that calls itself reproducible.
    """
    pins = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "==" not in line:
            raise WheelhouseError(
                f"requirements line {number} is not a pin: {raw.strip()!r}"
            )
        name, _, version = line.partition("==")
        pins.append(
            {
                "requirement": line,
                "name": name.strip(),
                "canonical_name": canonical_name(name.strip()),
                "version": version.strip(),
            }
        )
    if not pins:
        raise WheelhouseError("the requirements file declares nothing")
    return pins


def parse_wheel_filename(filename: str) -> dict:
    """Split a wheel file name into the tags the manifest records."""
    match = _WHEEL_NAME.match(filename)
    if not match:
        raise WheelhouseError(f"not a PEP 427 wheel file name: {filename!r}")
    fields = match.groupdict()
    return {
        "filename": filename,
        "package": fields["distribution"],
        "canonical_name": canonical_name(fields["distribution"]),
        "version": fields["version"],
        "build_tag": fields["build"],
        "python_tag": fields["python_tag"],
        "abi_tag": fields["abi_tag"],
        "platform_tag": fields["platform_tag"],
    }


def _repo_relative(path: pathlib.Path) -> str:
    """Repo-relative when it can be; absolute otherwise, never an exception.

    Tests build synthetic wheelhouses under tmp_path, which is outside the
    repository. A manifest builder that raised there would be untestable exactly
    where its failure paths need exercising.
    """
    resolved = pathlib.Path(path).resolve()
    if resolved.is_relative_to(REPO):
        return resolved.relative_to(REPO).as_posix()
    return resolved.as_posix()


def collect_wheels(wheelhouse: pathlib.Path) -> list[pathlib.Path]:
    return sorted(wheelhouse.glob("*.whl"))


def describe_wheel(path: pathlib.Path) -> dict:
    entry = parse_wheel_filename(path.name)
    entry["sha256"] = sha256_file(path)
    entry["size_bytes"] = path.stat().st_size
    return entry


def resolution_metadata(index: str | None, python: pathlib.Path) -> dict:
    """What produced this wheelhouse, recorded so a rebuild can be compared.

    ``index`` is what was actually used, which is not necessarily pypi.org: this
    machine has a mirror configured globally, and recording the declared index
    instead of the effective one is precisely the sort of small dishonesty that
    makes a provenance record useless.
    """
    # `pip --version` prints "pip X.Y.Z from <site-packages path> (python 3.12)".
    # Only the version is provenance; the path is the build machine's home
    # directory, and writing it into a tracked manifest would bind this repo to
    # one computer -- the exact defect tools/portability_check.py exists to catch.
    raw_version = subprocess.run(
        [str(python), "-m", "pip", "--version"], capture_output=True, text=True, timeout=120
    ).stdout.strip()
    pip_version = raw_version.split(" from ", 1)[0].strip() or raw_version
    effective_index = index or _configured_index(python)
    return {
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "index_url": effective_index,
        "index_url_source": "--index argument" if index else "pip configuration or default",
        "pip": pip_version,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "host_platform": platform.platform(),
        "host_machine": platform.machine(),
        "only_binary": True,
    }


def _configured_index(python: pathlib.Path) -> str:
    done = subprocess.run(
        [str(python), "-m", "pip", "config", "list"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    for line in done.stdout.splitlines():
        if line.startswith("global.index-url=") or line.startswith("install.index-url="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return "https://pypi.org/simple"


# -------------------------------------------------------------------- build


def _pip(python: pathlib.Path, args: list[str], index: str | None, what: str) -> str:
    command = [str(python), "-m", "pip", *args]
    if index:
        command += ["--index-url", index]
    done = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    if done.returncode != 0:
        raise WheelhouseError(
            f"{what} failed; the wheelhouse was not completed.\n"
            f"command: {' '.join(command)}\n{done.stdout}\n{done.stderr}"
        )
    return done.stdout


def download(
    requirements: pathlib.Path,
    wheelhouse: pathlib.Path,
    python: pathlib.Path,
    index: str | None = None,
    allow_sdist: list[str] | None = None,
) -> dict[str, dict]:
    """Fetch every pinned wheel into *wheelhouse*.

    Published wheels are downloaded with ``--only-binary=:all:``, so a package
    with no wheel is a named failure rather than a source build that happens to
    work on the machine doing the packaging.

    Packages named in *allow_sdist* are the declared exception: their sdist is
    downloaded, hashed, and built into a wheel locally. Returns the provenance of
    those, keyed by canonical package name, so the manifest can record which
    wheels were not published as wheels upstream.
    """
    allow = set(allow_sdist or ())
    wheelhouse.mkdir(parents=True, exist_ok=True)
    pins = parse_requirements(requirements.read_text(encoding="utf-8"))
    published = [pin for pin in pins if pin["canonical_name"] not in allow]
    from_source = [pin for pin in pins if pin["canonical_name"] in allow]

    unknown = allow - {pin["canonical_name"] for pin in pins}
    if unknown:
        raise WheelhouseError(
            "sdist_build_allowed names package(s) that are not in the lock file: "
            + ", ".join(sorted(unknown))
        )

    if published:
        # The lock is the whole dependency set; --no-deps keeps pip from adding
        # to it, so the wheelhouse and the lock describe the same build.
        filtered = wheelhouse / "_requirements.published.txt"
        filtered.write_text(
            "\n".join(pin["requirement"] for pin in published) + "\n", encoding="utf-8"
        )
        try:
            _pip(
                python,
                ["download", "--requirement", str(filtered), "--dest", str(wheelhouse),
                 "--only-binary=:all:", "--no-deps"],
                index,
                "pip download (published wheels)",
            )
        finally:
            filtered.unlink(missing_ok=True)

    provenance: dict[str, dict] = {}
    for pin in from_source:
        provenance[pin["canonical_name"]] = _build_from_sdist(
            pin, wheelhouse, python, index
        )
    return provenance


def _build_from_sdist(
    pin: dict, wheelhouse: pathlib.Path, python: pathlib.Path, index: str | None
) -> dict:
    """Download one sdist, hash it, and build a wheel from it into *wheelhouse*.

    The sdist's SHA-256 is what keeps this auditable. The wheel built from it is
    a local artifact and is not claimed to be byte-identical to one built
    elsewhere; the sdist is the thing whose identity can be checked.
    """
    import shutil
    import tempfile

    staging = pathlib.Path(tempfile.mkdtemp(prefix="leo-sdist-"))
    try:
        _pip(
            python,
            ["download", f"{pin['name']}=={pin['version']}", "--dest", str(staging),
             "--no-binary=:all:", "--no-deps"],
            index,
            f"pip download (sdist for {pin['requirement']})",
        )
        sdists = [
            path for path in sorted(staging.iterdir())
            if path.name.endswith((".tar.gz", ".tar.bz2", ".zip"))
        ]
        if len(sdists) != 1:
            raise WheelhouseError(
                f"expected exactly one sdist for {pin['requirement']}, got "
                f"{[p.name for p in sdists]}"
            )
        sdist = sdists[0]
        sdist_sha256 = sha256_file(sdist)

        # Build into an empty directory rather than straight into the wheelhouse.
        # pip overwrites a wheel of the same name in place, so a "what is new
        # here?" diff against the wheelhouse silently finds nothing on a rebuild
        # -- and the bytes have changed underneath it anyway, because a wheel
        # built from source is not byte-stable (its zip entries carry build
        # timestamps). Building somewhere empty makes the result unambiguous.
        #
        # --no-build-isolation is required, not a shortcut: pip's default is to
        # create an isolated build environment and install the backend into it
        # from an index, which --no-index then blocks. Using the ambient
        # setuptools keeps the build offline *and* keeps its version inside the
        # declared set, rather than resolving a build-time dependency that
        # appears nowhere in requirements.lock.
        built = staging / "built"
        built.mkdir()
        _pip(
            python,
            ["wheel", str(sdist), "--wheel-dir", str(built), "--no-deps",
             "--no-index", "--no-build-isolation"],
            None,
            f"pip wheel ({pin['requirement']})",
        )
        produced = collect_wheels(built)
        if len(produced) != 1:
            raise WheelhouseError(
                f"building {pin['requirement']} from sdist produced "
                f"{[p.name for p in produced]!r}, expected exactly one wheel"
            )
        wheel = wheelhouse / produced[0].name
        shutil.copy2(produced[0], wheel)
        return {
            "origin": "built-from-sdist",
            "wheel": wheel.name,
            "sdist_filename": sdist.name,
            "sdist_sha256": sdist_sha256,
            "sdist_size_bytes": sdist.stat().st_size,
            "reason": "no wheel is published for this version on the index",
            "reproducibility": (
                "the sdist hash is stable and checkable; the wheel built from it is a "
                "local artifact and is not byte-identical between builds. Observed: two "
                "builds of this sdist on the same machine minutes apart produced wheels "
                "with different SHA-256 values, because the zip entries carry build "
                "timestamps. Verify this entry against sdist_sha256; treat the wheel's "
                "own sha256 as describing the file now present, not as a cross-machine "
                "guarantee."
            ),
        }
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def build_manifest(
    requirements: pathlib.Path,
    wheelhouse: pathlib.Path,
    python: pathlib.Path,
    index: str | None = None,
    provenance: dict[str, dict] | None = None,
) -> dict:
    pins = parse_requirements(requirements.read_text(encoding="utf-8"))
    wheels = [describe_wheel(path) for path in collect_wheels(wheelhouse)]
    provenance = provenance or {}
    for wheel in wheels:
        record = provenance.get(wheel["canonical_name"])
        if record and record["wheel"] == wheel["filename"]:
            wheel.update(
                {
                    "origin": record["origin"],
                    "sdist_filename": record["sdist_filename"],
                    "sdist_sha256": record["sdist_sha256"],
                    "sdist_size_bytes": record["sdist_size_bytes"],
                    "origin_reason": record["reason"],
                    "reproducibility": record["reproducibility"],
                }
            )
        else:
            wheel["origin"] = "published-wheel"
    by_name: dict[str, list[dict]] = {}
    for wheel in wheels:
        by_name.setdefault(wheel["canonical_name"], []).append(wheel)

    missing = [
        pin["requirement"]
        for pin in pins
        if not any(
            w["version"] == pin["version"]
            for w in by_name.get(pin["canonical_name"], ())
        )
    ]
    if missing:
        raise WheelhouseError(
            "no wheel was obtained for: " + ", ".join(missing) + "\n"
            "Every pinned dependency must be present as a wheel. Falling back to "
            "the index at install time would defeat the point of the wheelhouse."
        )

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "_comment": (
            "Contents of the offline wheelhouse. The wheel files themselves are not "
            "committed; this manifest is what makes them checkable. Regenerate with "
            "tools/build_wheelhouse.py build, verify with ... verify."
        ),
        "requirements_file": _repo_relative(requirements),
        "requirements_sha256": sha256_requirements(
            requirements.read_text(encoding="utf-8")
        ),
        "wheelhouse_dir": _repo_relative(wheelhouse),
        "resolution": resolution_metadata(index, python),
        "offline_install": {
            "flags": ["--no-index", "--find-links", "<wheelhouse>"],
            "note": "--no-index is what makes this offline; --find-links alone would still fall back to the index",
        },
        "sdist_build_allowed": sorted(provenance),
        "built_from_sdist": sorted(
            w["filename"] for w in wheels if w.get("origin") == "built-from-sdist"
        ),
        "origin_note": (
            "published-wheel entries are byte-identical to what the index served and are "
            "fully checkable by sha256. built-from-sdist entries were compiled here because "
            "no wheel is published; for those the *sdist* hash is the stable identity, and "
            "the wheel is a local artifact that another machine may rebuild with different "
            "bytes. Both are recorded rather than averaged into one claim."
        ),
        "wheel_count": len(wheels),
        "wheels": sorted(wheels, key=lambda w: (w["canonical_name"], w["version"])),
    }


# ------------------------------------------------------------------- verify


def verify(
    manifest: dict,
    wheelhouse: pathlib.Path,
    requirements_text: str | None = None,
) -> list[dict]:
    """Every way this wheelhouse could fail to be what the manifest says.

    Returns a list of problems; empty means verified. Each problem carries a
    ``kind`` so a caller (and a test) can assert on the specific failure rather
    than on a message.
    """
    problems: list[dict] = []

    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        problems.append(
            {
                "kind": "schema-version",
                "detail": f"manifest schema_version {manifest.get('schema_version')!r} "
                f"!= {MANIFEST_SCHEMA_VERSION!r}",
            }
        )

    declared = manifest.get("wheels") or []
    if manifest.get("wheel_count") != len(declared):
        problems.append(
            {
                "kind": "count-mismatch",
                "detail": f"wheel_count {manifest.get('wheel_count')!r} != {len(declared)} entries",
            }
        )

    # 1. every declared wheel is present, and is the file it claims to be
    for entry in declared:
        path = wheelhouse / entry["filename"]
        if not path.is_file():
            problems.append(
                {"kind": "missing-file", "wheel": entry["filename"],
                 "detail": f"declared in the manifest but not in {wheelhouse}"}
            )
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256"):
            problems.append(
                {"kind": "hash-mismatch", "wheel": entry["filename"],
                 "detail": f"sha256 {actual} != declared {entry.get('sha256')}"}
            )
        if path.stat().st_size != entry.get("size_bytes"):
            problems.append(
                {"kind": "size-mismatch", "wheel": entry["filename"],
                 "detail": f"{path.stat().st_size} bytes != declared {entry.get('size_bytes')}"}
            )
        try:
            parsed = parse_wheel_filename(entry["filename"])
        except WheelhouseError as error:
            problems.append({"kind": "bad-filename", "wheel": entry["filename"],
                             "detail": str(error)})
            continue
        for field in ("package", "version", "python_tag", "abi_tag", "platform_tag"):
            if entry.get(field) != parsed[field]:
                problems.append(
                    {"kind": "tag-mismatch", "wheel": entry["filename"],
                     "detail": f"{field} recorded as {entry.get(field)!r}, "
                               f"file name says {parsed[field]!r}"}
                )

    # 1b. every wheel says where it came from, and a locally built one carries
    #     the sdist hash that is its actual identity
    allowed_sdist = set(manifest.get("sdist_build_allowed") or ())
    for entry in declared:
        origin = entry.get("origin")
        if origin not in ("published-wheel", "built-from-sdist"):
            problems.append(
                {"kind": "unknown-origin", "wheel": entry["filename"],
                 "detail": f"origin {origin!r} is neither published-wheel nor built-from-sdist"}
            )
            continue
        if origin != "built-from-sdist":
            continue
        if entry.get("canonical_name") not in allowed_sdist:
            problems.append(
                {"kind": "undeclared-sdist-build", "wheel": entry["filename"],
                 "detail": "built from source without being named in sdist_build_allowed"}
            )
        if not entry.get("sdist_sha256"):
            problems.append(
                {"kind": "missing-sdist-hash", "wheel": entry["filename"],
                 "detail": "a locally built wheel must record the hash of the sdist it came from"}
            )

    # 2. nothing in the directory that the manifest does not account for
    declared_names = {entry["filename"] for entry in declared}
    for path in collect_wheels(wheelhouse):
        if path.name not in declared_names:
            problems.append(
                {"kind": "undeclared-wheel", "wheel": path.name,
                 "detail": "present in the wheelhouse but absent from the manifest"}
            )

    # 3. the lock and the wheelhouse describe the same build, item by item
    if requirements_text is not None:
        if manifest.get("requirements_sha256"):
            if sha256_requirements(requirements_text) != manifest["requirements_sha256"]:
                problems.append(
                    {"kind": "requirements-drift",
                     "detail": "the lock file has changed since this manifest was built; "
                               "rebuild the wheelhouse"}
                )
        try:
            pins = parse_requirements(requirements_text)
        except WheelhouseError as error:
            problems.append({"kind": "bad-requirements", "detail": str(error)})
            pins = []
        by_name: dict[str, set[str]] = {}
        for entry in declared:
            by_name.setdefault(
                canonical_name(entry.get("package", "")), set()
            ).add(entry.get("version"))
        for pin in pins:
            versions = by_name.get(pin["canonical_name"])
            if not versions:
                problems.append(
                    {"kind": "missing-wheel", "package": pin["requirement"],
                     "detail": "pinned in the lock file with no wheel in the wheelhouse"}
                )
            elif pin["version"] not in versions:
                problems.append(
                    {"kind": "version-mismatch", "package": pin["requirement"],
                     "detail": f"wheelhouse has {sorted(versions)}, lock pins {pin['version']}"}
                )
        locked = {pin["canonical_name"] for pin in pins}
        for name in sorted(by_name):
            if name and name not in locked:
                problems.append(
                    {"kind": "unlocked-package", "package": name,
                     "detail": "in the wheelhouse but not pinned in the lock file"}
                )

    return problems


def audit_environment(python: pathlib.Path, requirements_text: str) -> list[dict]:
    """Whether an interpreter's installed packages are exactly the declared set.

    A wheelhouse guarantees what *can* be installed offline. It says nothing
    about what is installed in the environment a build actually runs on. This is
    the other half: a build that calls itself reproducible from declared inputs
    must be able to show that the environment it used holds those inputs and
    nothing else at another version.

    Returns a list of problems; empty means the environment matches the lock.
    """
    done = subprocess.run(
        [str(python), "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if done.returncode != 0:
        return [{"kind": "pip-list-failed", "detail": done.stderr.strip()}]
    installed = {
        canonical_name(entry["name"]): entry["version"]
        for entry in json.loads(done.stdout)
    }
    problems: list[dict] = []
    pins = parse_requirements(requirements_text)
    for pin in pins:
        actual = installed.get(pin["canonical_name"])
        if actual is None:
            problems.append(
                {"kind": "not-installed", "package": pin["requirement"],
                 "detail": "declared in the lock but absent from this environment"}
            )
        elif actual != pin["version"]:
            problems.append(
                {"kind": "version-drift", "package": pin["requirement"],
                 "detail": f"installed {actual}, lock pins {pin['version']}"}
            )
    locked = {pin["canonical_name"] for pin in pins}
    # pip and its bootstrap companions are part of any venv and are not build
    # inputs; naming them here beats an "extras are fine" rule that would let a
    # real undeclared dependency through.
    bootstrap = {"pip", "wheel", "setuptools", "pkg-resources", "distribute"}
    for name, version in sorted(installed.items()):
        if name in locked or name in bootstrap:
            continue
        problems.append(
            {"kind": "undeclared-package", "package": f"{name}=={version}",
             "detail": "installed in the build environment but not in the lock file"}
        )
    return problems


def install_command(python: pathlib.Path, wheelhouse: pathlib.Path,
                    requirements: pathlib.Path) -> list[str]:
    """The offline install. ``--no-index`` is the part that makes it offline."""
    return [
        str(python), "-m", "pip", "install",
        "--no-index",
        "--find-links", str(wheelhouse),
        "--requirement", str(requirements),
    ]


# --------------------------------------------------------------------- cli


def _load_manifest(path: pathlib.Path) -> dict:
    if not path.is_file():
        raise WheelhouseError(
            f"no wheelhouse manifest at {path}. Run: python tools/build_wheelhouse.py build"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "action",
        choices=["build", "verify", "install", "audit-env", "print-install-command"],
    )
    parser.add_argument("--wheelhouse", type=pathlib.Path, default=DEFAULT_WHEELHOUSE)
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--requirements", type=pathlib.Path, default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--index", default=None, help="index to download from (build only)")
    parser.add_argument(
        "--allow-sdist-build",
        default=None,
        help="comma-separated packages that may be built from source, overriding "
             "sdist_build_allowed in manifests/dependency-lock.json. Pass an empty "
             "string to forbid source builds entirely.",
    )
    parser.add_argument(
        "--python",
        type=pathlib.Path,
        default=pathlib.Path(sys.executable),
        help="interpreter to download for / install into",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.action == "build":
            allow = (
                [canonical_name(n) for n in args.allow_sdist_build.split(",") if n.strip()]
                if args.allow_sdist_build is not None
                else sdist_build_allowed()
            )
            provenance = download(
                args.requirements, args.wheelhouse, args.python, args.index, allow
            )
            manifest = build_manifest(
                args.requirements, args.wheelhouse, args.python, args.index, provenance
            )
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            args.manifest.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"wheelhouse: {args.wheelhouse}")
            print(f"manifest:   {args.manifest}")
            print(f"{manifest['wheel_count']} wheel(s) for "
                  f"{len(parse_requirements(args.requirements.read_text(encoding='utf-8')))} pin(s)")
            print(f"index:      {manifest['resolution']['index_url']}")
            return 0

        if args.action == "audit-env":
            problems = audit_environment(
                args.python, args.requirements.read_text(encoding="utf-8")
            )
            if args.json:
                print(json.dumps({"problems": problems}, ensure_ascii=False, indent=2))
            else:
                for problem in problems:
                    print(f"  [FAIL] {problem['kind']:<20} "
                          f"{problem.get('package', '')} -- {problem['detail']}")
                print(f"\n  {len(problems)} problem(s) in {args.python}")
            return 1 if problems else 0

        if args.action in ("verify", "install"):
            manifest = _load_manifest(args.manifest)
            requirements_text = (
                args.requirements.read_text(encoding="utf-8")
                if args.requirements.is_file()
                else None
            )
            problems = verify(manifest, args.wheelhouse, requirements_text)
            if args.json:
                print(json.dumps({"problems": problems}, ensure_ascii=False, indent=2))
            else:
                for problem in problems:
                    subject = problem.get("wheel") or problem.get("package") or ""
                    print(f"  [FAIL] {problem['kind']:<20} {subject} -- {problem['detail']}")
                print(
                    f"\n  {len(problems)} problem(s); "
                    f"{manifest.get('wheel_count', 0)} wheel(s) declared"
                )
                if not problems:
                    print("  NOTE: a verified wheelhouse is not a clean-machine build. "
                          "F1/F2 in CHANGELOG.md#archive-p0-manual-acceptance-checklist (P0_MANUAL_ACCEPTANCE_CHECKLIST) stay NOT TESTED\n"
                          "        until someone builds from a fresh clone on a machine "
                          "with no previous release.")
            if problems:
                return 1
            if args.action == "verify":
                return 0

            command = install_command(args.python, args.wheelhouse, args.requirements)
            print("  " + " ".join(command))
            done = subprocess.run(command, timeout=3600)
            return done.returncode

        command = install_command(args.python, args.wheelhouse, args.requirements)
        print(" ".join(command))
        return 0
    except WheelhouseError as error:
        print(f"  [FAIL] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
