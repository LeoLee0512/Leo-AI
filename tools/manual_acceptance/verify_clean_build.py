"""Block F — how close this machine is to a clean-machine build, and what is missing.

F1-F3 are about machines this is not: one with no previous ``LeoAIStudio.exe``,
one with a fresh clone, and one willing to build the same commit twice and
account for the difference.

This machine has a previous release installed, which is precisely why F1 cannot
be answered here: removing it would not recreate the situation, it would only
destroy the evidence. What this tool does instead is enumerate, concretely, every
input the build would need from outside a fresh clone -- so the person doing F1
knows what to provision rather than discovering it from a build failure at
minute forty.

    python tools/manual_acceptance/verify_clean_build.py --save
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    FAIL,
    PASS,
    REPO,
    UNDETERMINED,
    Report,
    emit,
    parser,
    run,
)

COVERS = ["F1", "F2", "F3"]


def main() -> int:
    args = parser(__doc__.splitlines()[0]).parse_args()
    report = Report("verify_clean_build", "F", COVERS)

    _previous_release(report)
    _external_inputs(report)
    _wheelhouse(report)
    _environment_audit(report)

    report.suggestion(
        "F1", UNDETERMINED,
        "a previous release is installed on this machine (see above), so a build here "
        "cannot demonstrate that one without it succeeds. Uninstalling would not "
        "recreate a clean machine, only destroy the rollback point",
    )
    report.suggestion(
        "F2", UNDETERMINED,
        "needs a fresh clone into a directory with none of this machine's state. The "
        "external inputs listed above are what such a clone would still need",
    )
    report.suggestion(
        "F3", UNDETERMINED,
        "needs the same commit built twice with the outputs compared. PyInstaller "
        "embeds timestamps and paths, so 'differences are explainable' is the bar, not "
        "byte identity -- and the explanation has to be written down",
    )
    return emit(report, args)


def _previous_release(report: Report) -> None:
    app_root = pathlib.Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio")
    exe = app_root / "LeoAIStudio.exe"
    launcher = app_root / "_launcher"
    report.check(
        "previous release on this machine",
        PASS if exe.exists() else UNDETERMINED,
        f"{exe} exists, so this machine is NOT the F1 environment" if exe.exists()
        else f"no previous release at {exe}; this machine may be usable for F1",
        exe=str(exe),
        exe_exists=exe.exists(),
        launcher_exists=launcher.exists(),
        launcher_files=sum(1 for _ in launcher.rglob("*")) if launcher.is_dir() else 0,
    )


def _external_inputs(report: Report) -> None:
    """Everything a fresh clone would still need from outside the repository."""
    python_dll = run([sys.executable, "-c",
                      "import os,sys;print(os.path.join(sys.base_prefix,'python312.dll'))"])
    dll_path = python_dll["stdout"].strip()
    library_bin = run([sys.executable, "-c",
                       "import os,sys;print(os.path.join(sys.base_prefix,'Library','bin'))"])
    bin_path = library_bin["stdout"].strip()

    inputs = [
        {
            "input": "python312.dll",
            "from": "the declared Python toolchain's base prefix",
            "path": dll_path,
            "present": bool(dll_path) and pathlib.Path(dll_path).is_file(),
            "why": "PyInstaller bootloader ABI",
        },
        {
            "input": "native DLLs (ffi-8, sqlite3, libbz2, liblzma, libexpat)",
            "from": "<base_prefix>/Library/bin, because this is a conda Python",
            "path": bin_path,
            "present": bool(bin_path) and pathlib.Path(bin_path).is_dir(),
            "why": "without them the frozen app dies on `import _ctypes` before main()",
        },
        {
            "input": "upstream OpenAI4S checkout",
            "from": json.loads((REPO / "manifests" / "upstream-pin.json").read_text(
                encoding="utf-8"))["repository"],
            "path": str(pathlib.Path(
                os.environ.get("LEO_UPSTREAM_ROOT")
                or REPO / "LeoAIStudio" / "upstream" / "OpenAI4S")),
            "present": pathlib.Path(
                os.environ.get("LEO_UPSTREAM_ROOT")
                or REPO / "LeoAIStudio" / "upstream" / "OpenAI4S").is_dir(),
            "why": "pinned revision; the build embeds its identity in the manifest",
        },
        {
            "input": "WebView2 fixed-version runtime",
            "from": "shipped alongside the app under runtime/",
            "path": str(pathlib.Path(
                os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio") / "runtime"),
            "present": (pathlib.Path(
                os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio") / "runtime").is_dir(),
            "why": "the window is black without a runtime CoreWebView2 can load",
        },
    ]
    missing = [item["input"] for item in inputs if not item["present"]]
    report.check(
        "inputs a fresh clone still needs",
        PASS if not missing else UNDETERMINED,
        "all four are present here; a clean machine must provide each of them"
        if not missing else f"not present on this machine: {missing}",
        inputs=inputs,
    )
    report.note(
        "A fresh clone is not sufficient on its own: the four inputs above come from "
        "outside the repository. F2 means 'clone plus these', and the list is what "
        "someone has to install first."
    )


def _wheelhouse(report: Report) -> None:
    manifest = REPO / "manifests" / "wheelhouse.json"
    if not manifest.is_file():
        report.check("wheelhouse", UNDETERMINED,
                     "no wheelhouse manifest; dependencies would resolve from an index")
        return
    verify = run([sys.executable, str(REPO / "tools" / "build_wheelhouse.py"), "verify"],
                 cwd=REPO, timeout=900)
    report.check(
        "wheelhouse verifies",
        PASS if verify["returncode"] == 0 else FAIL,
        "dependencies are installable with --no-index on this machine"
        if verify["returncode"] == 0 else "the wheelhouse does not verify",
        returncode=verify["returncode"],
        stdout=verify["stdout"].strip()[:4000],
    )
    report.note(
        "The wheelhouse itself is not committed. A clean machine gets requirements.lock "
        "and manifests/wheelhouse.json from the clone and must either rebuild the "
        "wheelhouse (needs an index, once) or be handed one to verify against the "
        "manifest."
    )


def _environment_audit(report: Report) -> None:
    audit = run(
        [sys.executable, str(REPO / "tools" / "build_wheelhouse.py"), "audit-env",
         "--python", sys.executable, "--json"],
        cwd=REPO, timeout=900,
    )
    try:
        problems = json.loads(audit["stdout"] or "{}").get("problems", [])
    except ValueError:
        problems = None
    report.check(
        "build environment matches the lock",
        PASS if problems == [] else FAIL if problems else UNDETERMINED,
        "every pin installed at its pinned version, nothing undeclared"
        if problems == [] else f"{len(problems)} problem(s)" if problems
        else "the audit output could not be parsed",
        problems=problems,
        returncode=audit["returncode"],
    )


if __name__ == "__main__":
    raise SystemExit(main())
