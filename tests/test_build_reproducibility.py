"""P0-5: a new build must not need an old one.

The build used to depend on the previous release in five places: a python312.dll
ABI comparison against ``_launcher``, a cryptography version comparison against
its dist-info, extraction of six modules out of the old EXE's PYZ archive, a
``--paths`` into ``_launcher``, and a Copy-MissingTree backfill from the old
onedir. A machine that had never built Leo AI Studio could not build it.

Two of those turned out to be genuinely vestigial and one did not: the PYZ
recovery was unnecessary (every module it recovered is in the PYZ of a normal
build), but the backfill was masking missing native DLLs. This is a conda
Python, which keeps ffi-8.dll and friends under ``<base_prefix>/Library/bin``
where PyInstaller does not look, so without them the frozen app died on
``import _ctypes`` before reaching main(). They now come from the declared Python
toolchain instead of from a previous release.

A sixth coupling was missed, and only turned up when the build was actually run:
``--additional-hooks-dir`` pointed into ``_launcher/webview/__pyinstaller``, and
the previous onedir and EXE were in the unconditional required-inputs list. That
combination was self-invalidating -- a hermetic build's own output has no
``webview/__pyinstaller``, so deploying one made the next build fail before
PyInstaller started. It is covered at the bottom of this file.

The lesson is in the shape of the miss: the earlier tests enumerated the
couplings someone had already found, so they could not report one nobody had.
Running the build is what found it.

These are static checks on the build script. Whether a build actually succeeds
on a machine with no prior release installed is a manual acceptance item.
"""

from __future__ import annotations

import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
BUILD_SCRIPT = REPO / "tools" / "build_launcher.ps1"


def script() -> str:
    return BUILD_SCRIPT.read_text(encoding="utf-8")


def test_dependencies_are_declared_in_a_lock_file():
    lock = REPO / "requirements.lock"
    assert lock.is_file(), "requirements.lock must declare the build inputs"
    pins = [
        line
        for line in lock.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert pins, "the lock file declares nothing"
    unpinned = [p for p in pins if "==" not in p]
    assert not unpinned, f"every dependency must be pinned: {unpinned}"
    # The modules the old build recovered out of the previous EXE must be here.
    names = {p.split("==")[0].lower().replace("_", "-") for p in pins}
    for required in ("bottle", "cffi", "pythonnet", "clr-loader", "proxy-tools", "pywebview"):
        assert required in names, f"{required} must be declared, not recovered from an old build"


def test_dependency_manifest_is_honest_about_the_wheelhouse():
    """The flag must track reality in both directions.

    This test used to assert ``vendored_wheelhouse is False``, because there was
    no wheelhouse and claiming one would have been false. There is one now, so
    the assertion is no longer "it must be False" but "whatever it says must be
    backed by something": True obliges a manifest that covers the lock, and False
    forbids the wheelhouse machinery from being advertised as available.
    """
    manifest = REPO / "manifests" / "dependency-lock.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["index"], "the wheel source must be recorded"
    assert data["packages"], "the manifest records no packages"

    claimed = data["vendored_wheelhouse"]
    assert isinstance(claimed, bool)
    wheelhouse_manifest = REPO / "manifests" / "wheelhouse.json"

    if not claimed:
        assert not wheelhouse_manifest.is_file(), (
            "a wheelhouse manifest exists but the dependency lock says there is none"
        )
        return

    assert wheelhouse_manifest.is_file(), (
        "vendored_wheelhouse is true but manifests/wheelhouse.json is missing; "
        "claiming offline reproducibility without the manifest that backs it is "
        "exactly the false claim this test exists to stop"
    )
    wheels = json.loads(wheelhouse_manifest.read_text(encoding="utf-8"))
    covered = {(entry["canonical_name"], entry["version"]) for entry in wheels["wheels"]}
    pins = [
        line
        for line in (REPO / "requirements.lock").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    missing = []
    for pin in pins:
        name, _, version = pin.partition("==")
        canonical = re.sub(r"[-_.]+", "-", name.strip()).lower()
        if (canonical, version.strip()) not in covered:
            missing.append(pin)
    assert not missing, f"vendored_wheelhouse is true but these pins are not covered: {missing}"
    assert data["wheelhouse"]["committed"] is False, (
        "the wheels are not in git; the lock must say so"
    )


def test_hermetic_is_the_default():
    """A plain build must not reach for the previous release."""
    text = script()
    assert "[switch]$Legacy" in text, "the escape hatch should be -Legacy, not -Hermetic"
    assert "$Hermetic = -not $Legacy" in text, "hermetic must be the default"


def test_every_dependency_on_a_previous_release_is_guarded():
    """The five couplings known before this round must sit behind the legacy switch.

    The sixth, found by running the build rather than reading it, is covered by
    the two tests at the bottom of this file.
    """
    text = script()
    couplings = {
        "PYZ extraction": "Invoke-PythonChecked -Arguments @($extractScript)",
        "launcher backfill": "Copy-MissingTree -Source $launcherDeps -Destination $distLauncher",
    }
    for label, needle in couplings.items():
        assert needle in text, f"{label}: anchor not found, update this test"
        index = text.index(needle)
        window = text[max(0, index - 400): index]
        assert "if (-not $Hermetic)" in window, (
            f"{label} is not guarded by the hermetic switch"
        )

    # The ABI and cryptography comparisons against _launcher sit in one guarded
    # block. Check containment by brace depth rather than by a fixed lookback,
    # which would silently start passing if the block grew.
    lines = text.splitlines()
    guarded_spans = []
    for number, line in enumerate(lines):
        if line.strip().startswith("if (-not $Hermetic)"):
            depth = 0
            for end in range(number, len(lines)):
                depth += lines[end].count("{") - lines[end].count("}")
                if depth == 0 and end > number:
                    guarded_spans.append((number, end))
                    break
    assert guarded_spans, "no hermetic guard block found"

    def is_guarded(needle: str) -> bool:
        for number, line in enumerate(lines):
            if needle in line:
                return any(start < number < end for start, end in guarded_spans)
        return False

    for needle in ("$baselinePython = Join-Path $launcherDeps", "$baselineCryptography ="):
        assert needle in text, f"{needle}: anchor not found, update this test"
        assert is_guarded(needle), f"{needle} is not guarded by the hermetic switch"


def test_native_dlls_come_from_the_declared_python_not_an_old_build():
    """The conda Library/bin fix must be present and explained."""
    text = script()
    assert "Library" in text and "base_prefix" in text, (
        "hermetic mode must source native DLLs from the declared Python toolchain"
    )
    assert "_ctypes" in text, (
        "the reason for the PATH addition should be recorded where it is done -- "
        "without it the frozen app dies on import _ctypes"
    )


def test_legacy_mode_is_documented_as_not_reproducible():
    text = script()
    assert re.search(r"LEGACY BUILD.*not reproducible", text), (
        "choosing the legacy path must say plainly what it costs"
    )


# ------------------------------------ the sixth coupling, found by building

def test_pywebview_hooks_come_from_the_package_not_the_previous_release():
    """The coupling that made a hermetic build unrepeatable.

    ``--additional-hooks-dir`` pointed at ``<AppRoot>/_launcher/webview/__pyinstaller``
    -- inside the previous release -- and it was in the unconditional required-inputs
    list, so it was never behind the hermetic switch. It was also self-invalidating:
    a hermetic build's own output does not contain ``webview/__pyinstaller``, so
    deploying one made the *next* build fail its precondition check before
    PyInstaller started. That is what happened here: the build refused to run at all
    until this was fixed.

    pywebview ships these hooks inside the installed package, so in hermetic mode
    they come from the declared dependency set like everything else.
    """
    text = script()
    assert "$legacyWebviewHooks" in text, (
        "the previous release's hooks directory should survive only as the -Legacy path"
    )
    assert "import os, webview" in text, (
        "hermetic mode must resolve pywebview's hooks from the installed package"
    )
    hermetic_branch = text[text.index("$legacyWebviewHooks"): text.index("$legacyWebviewHooks") + 700]
    assert "if ($Hermetic)" in hermetic_branch
    assert "$webviewHooks = $legacyWebviewHooks" in hermetic_branch, (
        "-Legacy must still use the old source"
    )


def test_the_previous_release_is_not_a_precondition_of_a_hermetic_build():
    """A machine that never installed Leo AI Studio must get past the input check.

    The required-inputs loop demanded the previous onedir and EXE unconditionally,
    so a clean machine failed before any of the guarded couplings mattered. Every
    *use* of them is behind the hermetic switch; the precondition now is too.
    """
    text = script()
    assert "$requiredInputs = @(" in text, "anchor not found, update this test"
    unconditional = text[text.index("$requiredInputs = @("): text.index("foreach ($required in $requiredInputs)")]
    head = unconditional.split("if (-not $Hermetic)")[0]
    for needle in ("$launcherDeps", "$baselineExe"):
        assert needle not in head, (
            f"{needle} is required unconditionally; a clean machine cannot build"
        )
    assert "if (-not $Hermetic) {" in unconditional, (
        "the previous release must be required only by the legacy path"
    )
    # The safety scan over the old tree must not run when there is no old tree.
    guard = text[text.index("Assert-SafeBaselineTree -Root $launcherDeps") - 120:
                 text.index("Assert-SafeBaselineTree -Root $launcherDeps")]
    assert "if (-not $Hermetic)" in guard


def test_the_hermetic_build_records_where_its_dependencies_came_from():
    """A build log that does not say wheelhouse-or-index cannot support a claim."""
    text = script()
    assert "wheelhouse verified" in text
    assert "no wheelhouse on this machine" in text
