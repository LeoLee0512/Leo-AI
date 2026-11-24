"""Block B — what WebView2 is available, and whether the runtime path is shaped right.

B1-B3 need machines this one is not: a fresh machine, a machine with only the
system WebView2, a machine with none. This reports which of those three
situations the current machine is in, which is the fact the person running B
needs first.

It also checks the one trap that regression test ``test_webview2_runtime.py``
locks down, and that a static test cannot observe on a real install:
``WEBVIEW2_RUNTIME_PATH`` must point at the *directory containing*
``msedgewebview2.exe``, not at the exe. Pointed at the exe, CoreWebView2 fails
with 0x80070002 and the window is black while the process stays alive -- the
worst possible failure mode, because it looks like a hang rather than an error.

    python tools/manual_acceptance/verify_webview2_runtime.py --save
"""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    FAIL,
    NOT_APPLICABLE,
    PASS,
    REPO,
    UNDETERMINED,
    Report,
    emit,
    parser,
    run,
)

COVERS = ["B1", "B2", "B3"]

#: Where the Evergreen runtime registers itself. Read only; nothing is installed.
REGISTRY_KEYS = (
    r"HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    r"HKCU\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
)


def main() -> int:
    args = parser(__doc__.splitlines()[0]).parse_args()
    report = Report("verify_webview2_runtime", "B", COVERS)

    if os.name != "nt":
        report.check("platform", NOT_APPLICABLE,
                     "WebView2 is a Windows component", os_name=os.name)
        return emit(report, args)

    system_version = _system_runtime(report)
    fixed = _fixed_runtime(report)

    if fixed["present"]:
        situation = "fixed-version runtime shipped with this install"
    elif system_version:
        situation = "system (Evergreen) runtime only"
    else:
        situation = "no WebView2 runtime found"
    report.check(
        "which B scenario this machine is",
        PASS,
        situation,
        fixed_runtime=fixed["path"],
        system_version=system_version,
    )

    report.suggestion(
        "B1", PASS if fixed["present"] and fixed["shape_ok"] else UNDETERMINED,
        "a fixed-version runtime directory is present and correctly shaped here; "
        "B1 still asks for a *new* machine, which this is not"
        if fixed["present"] and fixed["shape_ok"]
        else "no correctly shaped fixed-version runtime on this machine",
    )
    report.suggestion(
        "B2", UNDETERMINED,
        "needs a machine with the system runtime and no fixed-version copy; "
        f"this machine is: {situation}",
    )
    report.suggestion(
        "B3", UNDETERMINED,
        "needs a machine with no WebView2 at all; removing it here would not be the "
        "same test and is not something this tool will do",
    )

    report.note(
        "The failure to watch for in B is a black window with a live process. That is "
        "WEBVIEW2_RUNTIME_PATH pointing at msedgewebview2.exe instead of the directory "
        "that contains it (CoreWebView2 returns 0x80070002)."
    )
    return emit(report, args)


def _system_runtime(report: Report) -> str | None:
    version = None
    for key in REGISTRY_KEYS:
        done = run(["reg", "query", key, "/v", "pv"])
        if done["returncode"] == 0:
            for line in done["stdout"].splitlines():
                if "pv" in line:
                    version = line.split()[-1]
                    break
        if version:
            break
    report.check(
        "system WebView2 runtime",
        PASS if version else UNDETERMINED,
        f"Evergreen runtime version {version}" if version
        else "no Evergreen runtime registered for this machine or user",
        version=version,
        keys_checked=list(REGISTRY_KEYS),
    )
    return version


def _fixed_runtime(report: Report) -> dict:
    """Whether a shipped fixed-version runtime is present and usable.

    Mirrors ``leo_shell.webview2_runtime._locate_runtime_exe`` rather than
    inventing a stricter rule: the shipped code searches the runtime directory
    recursively and pins the exe's *parent*, so a nested
    ``webview2/<version>/Microsoft.WebView2.FixedVersionRuntime.../`` layout is
    correct, not a defect. It requires exactly one match -- two is ambiguous and
    raises there, so it is a FAIL here.
    """
    configured = os.environ.get("WEBVIEW2_RUNTIME_PATH", "")
    candidates = []
    if configured:
        candidates.append(pathlib.Path(configured))
    app_root = pathlib.Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio")
    candidates.append(app_root / "runtime" / "webview2")

    for candidate in candidates:
        if not candidate.exists():
            continue
        if candidate.is_file():
            report.check(
                "WEBVIEW2_RUNTIME_PATH shape", FAIL,
                "the path is a file. It must be the DIRECTORY containing "
                "msedgewebview2.exe -- pointed at the exe, CoreWebView2 fails with "
                "0x80070002 and the window is black while the process stays alive",
                path=str(candidate),
            )
            return {"present": True, "shape_ok": False, "path": str(candidate)}

        direct = candidate / "msedgewebview2.exe"
        matches = [direct] if direct.is_file() else sorted(
            path for path in candidate.rglob("msedgewebview2.exe") if path.is_file()
        )
        if len(matches) == 1:
            report.check(
                "fixed-version runtime is locatable", PASS,
                "exactly one msedgewebview2.exe below the runtime directory; the app "
                f"would pin BrowserExecutableFolder to {matches[0].parent}",
                runtime_dir=str(candidate),
                exe=str(matches[0]),
                pinned_directory=str(matches[0].parent),
            )
            return {"present": True, "shape_ok": True, "path": str(candidate)}
        if len(matches) > 1:
            report.check(
                "fixed-version runtime is locatable", FAIL,
                f"{len(matches)} copies of msedgewebview2.exe below the runtime "
                "directory. The shipped locator requires exactly one and raises "
                "WebView2RuntimeError otherwise",
                runtime_dir=str(candidate), found=[str(p) for p in matches],
            )
            return {"present": True, "shape_ok": False, "path": str(candidate)}
        report.check(
            "fixed-version runtime is locatable", FAIL,
            "the runtime directory exists but contains no msedgewebview2.exe",
            runtime_dir=str(candidate),
        )
        return {"present": True, "shape_ok": False, "path": str(candidate)}

    report.check(
        "fixed-version runtime", UNDETERMINED,
        "no fixed-version runtime directory found at the configured or default location",
        checked=[str(c) for c in candidates],
        WEBVIEW2_RUNTIME_PATH=configured or None,
    )
    return {"present": False, "shape_ok": False, "path": None}


if __name__ == "__main__":
    raise SystemExit(main())
