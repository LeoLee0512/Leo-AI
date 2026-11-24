"""Block A — facts about the Windows account this is running under.

A1-A7 need a *different* Windows account than the one that built the product.
Nothing here can create one, and DPAPI is per-user by design, so no amount of
collection can answer A6 from inside this account.

What it can do is record which account this is, where the per-user data lives,
and whether credential files exist here -- so that the same command
run under the new account produces a second file that can be compared with this
one. A6's expected result is that the new account *cannot* read this account's
key, and having both records is what makes that observable rather than asserted.

    python tools/manual_acceptance/collect_windows_account_env.py --save
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

COVERS = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]


def _account_identity(report: Report) -> str | None:
    whoami = run(["whoami", "/user"])
    report.check(
        "windows account identity",
        PASS if whoami["returncode"] == 0 else UNDETERMINED,
        "the SID identifies the account; a second account produces a different one",
        stdout=whoami["stdout"].strip(),
        returncode=whoami["returncode"],
    )
    for line in whoami["stdout"].splitlines():
        if line.strip().startswith("S-1-"):
            return line.split()[-1]
        parts = line.split()
        if parts and parts[-1].startswith("S-1-"):
            return parts[-1]
    return None


def main() -> int:
    argument_parser = parser(__doc__.splitlines()[0])
    argument_parser.add_argument("--app-root", type=pathlib.Path,
                                default=pathlib.Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio"),
                                help="installed product to inspect; does not redirect the product")
    args = argument_parser.parse_args()
    report = Report("collect_windows_account_env", "A", COVERS)

    if os.name != "nt":
        report.check(
            "platform", NOT_APPLICABLE,
            "block A is about Windows accounts; this is not Windows",
            os_name=os.name,
        )
        report.note("Run this on the Windows machine, under each account in turn.")
        return emit(report, args)

    sid = _account_identity(report)
    report.check(
        "account SID recorded",
        PASS if sid else UNDETERMINED,
        "compare this SID between the two runs; if it is the same, the second run "
        "was not under a new account and A1-A7 have not been exercised",
        sid=sid,
    )

    # The actual product is portable: AppPaths puts state below the install root.
    # LOCALAPPDATA is an account fact, not the current credential-store authority.
    sys.path.insert(0, str(REPO))
    from leo_shell.paths import AppPaths
    paths = AppPaths.from_root(args.app_root.resolve())
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    data_dir = paths.user
    report.check(
        "installed product user-data directory",
        PASS if paths.root.is_dir() else UNDETERMINED,
        "AppPaths places portable state below the installed product; fresh-account "
        "tests need a fresh install with no inherited user directory",
        localappdata=local_appdata,
        install_root=str(paths.root), expected_data_dir=str(data_dir),
        expected_credentials_dir=str(paths.credentials),
        exists=data_dir.exists(),
        entries=sorted(p.name for p in data_dir.iterdir()) if data_dir.is_dir() else [],
    )

    # A6 is about DPAPI. Inventory only: never decrypt or print a user's secret.
    secrets = _dpapi_state(report, data_dir)
    report.check(
        "credential store state", secrets["verdict"], secrets["detail"], **secrets["evidence"]
    )

    override = os.environ.get("LEO_STUDIO_ROOT", "")
    report.check(
        "no path override in effect" if not override else "path override in effect",
        PASS if not override else UNDETERMINED,
        "A7 asks for zero manual patching. An override set here means the run was "
        "steered and does not answer A7."
        if override else
        "nothing is steering the install root, which is what A7 requires",
        LEO_STUDIO_ROOT=override or None,
    )

    for item in COVERS:
        report.suggestion(
            item, UNDETERMINED,
            "requires a person to log in to a second Windows account and observe the "
            "application; this tool records the environment, not the outcome",
        )

    report.note(
        "Run once under the building account and once under the new account, then "
        "compare the two saved files. These files establish account/store identities "
        "only, not DPAPI decryption behavior. A6 additionally needs a controlled "
        "cross-account test of a non-secret test blob and a real save/readback; "
        "do not copy or expose a real user's API key."
    )
    report.note(
        "A1-A5 are visual: window shows, warm launch page with the lion and two buttons, "
        "no auto-advance without an API key, browse-mode bar after 'look around', bar gone "
        "after saving a key. No script can see those."
    )
    return emit(report, args)


def _dpapi_state(report: Report, data_dir: pathlib.Path | None) -> dict:
    """Whether credential files exist; this does not test decryption."""
    if data_dir is None or not data_dir.is_dir():
        return {
            "verdict": UNDETERMINED,
            "detail": "no per-user data directory yet, so there is no credential to test",
            "evidence": {"data_dir": str(data_dir) if data_dir else None},
        }
    blobs = sorted(str(p.relative_to(data_dir)) for p in data_dir.rglob("*") if p.is_file()
                   and (p.suffix in (".dpapi", ".bin") or p.name.endswith("secrets.json")))
    if not blobs:
        return {
            "verdict": UNDETERMINED,
            "detail": "no credential file found; save an API key first, then re-run",
            "evidence": {"data_dir": str(data_dir), "candidates": blobs},
        }

    sys.path.insert(0, str(REPO))
    try:
        from leo_shell import secrets_store  # noqa: F401
    except Exception as error:
        return {
            "verdict": UNDETERMINED,
            "detail": f"leo_shell.secrets_store could not be imported here: {error}",
            "evidence": {"data_dir": str(data_dir), "candidates": blobs},
        }
    return {
        "verdict": PASS,
        "detail": (
            "credential files exist below the product user directory. No file was "
            "decrypted. Presence and account comparison cannot establish A6."
        ),
        "evidence": {"data_dir": str(data_dir), "candidates": blobs, "decryption_tested": False},
    }


if __name__ == "__main__":
    raise SystemExit(main())
