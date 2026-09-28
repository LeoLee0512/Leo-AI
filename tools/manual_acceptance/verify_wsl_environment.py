"""Block C — which WSL distributions and users actually exist here.

C1-C5 ask what happens with a WSL user who is not ``leo``, a distribution that is
not the configured default, no WSL at all, and WSL with no distribution. The
paths are parameterised (``LEO_WSL_DISTRO`` / ``LEO_WSL_USER`` /
``LEO_WSL_SKILLS``), but parameterised is not the same as verified under another
value, which is exactly why these rows are NOT TESTED.

This lists what is installed, resolves the default user of each distribution, and
-- where a second distribution or user *does* exist -- actually exercises the
override rather than assuming it works. That last part is the only way any of
block C moves without a second machine.

    python tools/manual_acceptance/verify_wsl_environment.py --save
    python tools/manual_acceptance/verify_wsl_environment.py --distro Debian --user alice
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

COVERS = ["C1", "C2", "C3", "C4", "C5"]


def _configured_target() -> tuple[str, str]:
    """The distro and user the skills bridge would target, from the bridge."""
    import importlib.util

    path = REPO / "tools" / "sync_skills.py"
    spec = importlib.util.spec_from_file_location("leo_sync_skills_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WSL_DISTRO, module.WSL_USER


def _wsl_text(result: dict) -> str:
    """wsl.exe output, already decoded by ``_common.run``.

    wsl.exe writes UTF-16LE. Letting subprocess decode it with the locale
    encoding raises inside its reader threads on a non-UTF-8 code page and the
    output is lost silently -- which looked, from the outside, like a collector
    that found nothing.
    """
    return result["stdout"]


def main() -> int:
    argument_parser = parser(__doc__.splitlines()[0])
    argument_parser.add_argument("--distro", help="exercise LEO_WSL_DISTRO with this value")
    argument_parser.add_argument("--user", help="exercise LEO_WSL_USER with this value")
    args = argument_parser.parse_args()
    report = Report("verify_wsl_environment", "C", COVERS)

    if os.name != "nt":
        report.check("platform", NOT_APPLICABLE, "the WSL bridge is Windows-side",
                     os_name=os.name)
        return emit(report, args)

    status = run(["wsl.exe", "--status"])
    if status["returncode"] is None:
        report.check("wsl.exe present", FAIL,
                     "wsl.exe could not be executed -- this machine is the C3 scenario",
                     stderr=status["stderr"])
        report.suggestion("C3", UNDETERMINED,
                          "this machine has no usable wsl.exe, which is the C3 environment. "
                          "C3 asks what the *application* does there; run it and observe")
        for item in ("C1", "C2", "C4", "C5"):
            report.suggestion(item, UNDETERMINED, "no WSL here to test against")
        return emit(report, args)

    listing = run(["wsl.exe", "--list", "--quiet"])
    distros = [
        line.strip()
        for line in _wsl_text(listing).splitlines()
        if line.strip()
    ]
    report.check(
        "installed distributions",
        PASS if distros else FAIL,
        f"{len(distros)} installed: {distros}" if distros
        else "WSL is present but no distribution is installed -- this is the C4 scenario",
        distributions=distros,
        raw=_wsl_text(listing).strip(),
    )

    # Read the configured values from the bridge itself rather than repeating
    # its defaults here. A second copy of the distro and user literals would be a
    # new machine binding of exactly the kind block C exists to find, and it
    # would drift the moment the bridge's defaults changed.
    configured_distro, configured_user = _configured_target()
    report.check(
        "configured target",
        PASS,
        "the values the bridge would use unless overridden",
        LEO_WSL_DISTRO=configured_distro,
        LEO_WSL_USER=configured_user,
        LEO_WSL_SKILLS=os.environ.get("LEO_WSL_SKILLS"),
    )

    users = {}
    for distro in distros:
        who = run(["wsl.exe", "-d", distro, "--", "sh", "-lc", "id -un; echo :; echo $HOME"])
        text = _wsl_text(who)
        parts = [p.strip() for p in text.split(":")] if who["returncode"] == 0 else []
        users[distro] = {
            "returncode": who["returncode"],
            "output": text.strip(),
            "user": parts[0].splitlines()[0] if parts and parts[0] else None,
        }
    report.check(
        "default user per distribution",
        PASS if users else UNDETERMINED,
        "C1 needs one of these to not be the configured user",
        users=users,
    )

    # C5: does the discovery path in sync_skills.py report what is really there?
    discover = run(
        [sys.executable, str(REPO / "tools" / "sync_skills.py"), "--discover"], cwd=REPO
    )
    discovered_ok = discover["returncode"] == 0 and any(
        distro in discover["stdout"] for distro in distros
    )
    report.check(
        "sync_skills.py --discover",
        PASS if discovered_ok else FAIL if distros else UNDETERMINED,
        "lists the distributions actually installed" if discovered_ok
        else "discovery output does not match what wsl.exe reports",
        returncode=discover["returncode"],
        stdout=discover["stdout"].strip()[:2000],
    )
    report.suggestion(
        "C5", PASS if discovered_ok else FAIL if distros else UNDETERMINED,
        "this one is fully decidable here: discovery either lists the installed "
        "distributions or it does not",
    )

    _exercise_overrides(report, args, distros, users, configured_distro, configured_user)

    non_default_user = [
        distro for distro, info in users.items()
        if info["user"] and info["user"] != configured_user
    ]
    report.suggestion(
        "C1",
        UNDETERMINED,
        f"a distribution with a different default user is available ({non_default_user}); "
        "re-run with --user to exercise it, then run the application against it"
        if non_default_user
        else f"every installed distribution defaults to '{configured_user}', so C1 cannot "
             "be exercised on this machine",
    )
    report.suggestion(
        "C2",
        UNDETERMINED,
        f"more than one distribution is installed ({distros}); re-run with --distro to "
        "exercise the override, then run the application against it"
        if len(distros) > 1
        else "only one distribution is installed, so C2 cannot be exercised here",
    )
    report.suggestion("C3", UNDETERMINED,
                      "WSL is present here; C3 needs a machine without it")
    report.suggestion("C4", UNDETERMINED,
                      "at least one distribution is installed here" if distros
                      else "this machine is the C4 scenario; run the application and "
                           "check the message is clear rather than a crash")
    return emit(report, args)


def _exercise_overrides(report, args, distros, users, configured_distro, configured_user):
    """Actually set the override and see whether it reaches the command line."""
    distro = args.distro
    user = args.user
    if not distro and not user:
        report.note(
            "No --distro/--user given, so no override was exercised. Pass them to test "
            "C1/C2 against a real second distribution or user."
        )
        return

    if distro and distro not in distros:
        report.check("override target exists", FAIL,
                     f"--distro {distro!r} is not installed; available: {distros}",
                     requested=distro, available=distros)
        return

    environment = dict(os.environ)
    if distro:
        environment["LEO_WSL_DISTRO"] = distro
    if user:
        environment["LEO_WSL_USER"] = user
        environment.pop("LEO_WSL_SKILLS", None)

    import subprocess

    from _common import decode

    done = subprocess.run(
        [sys.executable, str(REPO / "tools" / "sync_skills.py"), "--check"],
        cwd=REPO, env=environment, capture_output=True, timeout=600,
    )
    combined = decode(done.stdout) + decode(done.stderr)
    reached = (not distro or distro in combined) and (not user or user in combined)
    report.check(
        "override reaches the bridge",
        PASS if reached else FAIL,
        "the overridden distribution/user appears in what the sync actually did"
        if reached else
        "the override was set but does not appear in the sync output; it may not be "
        "taking effect",
        LEO_WSL_DISTRO=distro, LEO_WSL_USER=user,
        returncode=done.returncode,
        output=combined.strip()[:4000],
    )
    report.note(
        "An override reaching the command line is necessary, not sufficient: C1/C2 ask "
        "that skills land in the right home and the bridge works, which needs the "
        "application run against that distribution."
    )


if __name__ == "__main__":
    raise SystemExit(main())
