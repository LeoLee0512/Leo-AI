"""Push the canonical skills to the two places that actually load them.

Why this exists
---------------
A skill edit used to reach nothing. The daemon loads skills from its own data
directory inside WSL. Editing the copy under ``LeoAIStudio/user/user-skills/`` —
what a Windows-side editor sees — changed a file the running agent never reads.
During one session the daemon was still executing a copy from two days earlier,
so an experiment-environment rule that had been "fixed" had never been live.

Direction of truth, one way only::

    LeoAIStudio-build/skills/          canonical, version controlled
      -> LeoAIStudio/user/user-skills/ deployed copy (what the shell shows)
      -> WSL data/user-skills/         what the daemon actually loads

Modes
-----
    python tools/sync_skills.py                     sync, then re-verify
    python tools/sync_skills.py --check             verify only
    python tools/sync_skills.py --check --require-wsl   release gate

``--require-wsl`` is the release gate: if the daemon copy cannot be reached it
exits non-zero. Without it an unreachable WSL is reported as NOT TESTED and does
not fail a developer run — but NOT TESTED is never folded into success.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
CANONICAL = REPO / "skills"
DEFAULT_APP_ROOT = pathlib.Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio")

#: No default is pretended to be "discovered". These are the configured values;
#: --discover reports what is actually installed so a wrong guess is visible.
WSL_DISTRO = os.environ.get("LEO_WSL_DISTRO", "Ubuntu-24.04")
WSL_USER = os.environ.get("LEO_WSL_USER", "leo")
WSL_SKILLS = os.environ.get(
    "LEO_WSL_SKILLS", f"/home/{WSL_USER}/.local/share/leo-ai-studio/data/user-skills"
)

#: Files that are never part of a skill's shipped content.
IGNORED = ("__pycache__", ".pytest_cache")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def digest(path: pathlib.Path) -> str:
    return digest_bytes(path.read_bytes())


def run_wsl(args: list[str], *, timeout: int = 120) -> tuple[int, str]:
    """Run a command in WSL. Bytes, not text: wsl.exe emits UTF-16 diagnostics."""
    try:
        done = subprocess.run(
            ["wsl.exe", "-d", WSL_DISTRO, "-u", WSL_USER, *args],
            capture_output=True,
            timeout=timeout,
        )
    except Exception as error:  # noqa: BLE001 - reported, never swallowed
        return 1, f"{type(error).__name__}: {error}"
    return done.returncode, done.stdout.decode("utf-8", errors="replace").strip()


def canonical_skills() -> list[pathlib.Path]:
    if not CANONICAL.is_dir():
        return []
    return sorted(p for p in CANONICAL.iterdir() if p.is_dir())


def skill_files(skill: pathlib.Path) -> list[pathlib.Path]:
    """Every shipped file in a skill, recursively.

    Previously only four fixed filenames were copied, so a skill that grew a
    module or a data file would have shipped incomplete while the tool reported
    it as synced.
    """
    files = []
    for path in sorted(skill.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED for part in path.parts):
            continue
        files.append(path)
    return files


def to_wsl_path(path: pathlib.Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    rest = resolved.as_posix()[len(resolved.drive):]
    return f"/mnt/{drive}{rest}"


# ------------------------------------------------------------------ windows


def sync_windows(app_root: pathlib.Path, *, check: bool) -> dict:
    dest_root = app_root / "user" / "user-skills"
    drift, synced, extra = [], [], []
    for skill in canonical_skills():
        dest = dest_root / skill.name
        wanted = set()
        for src in skill_files(skill):
            rel = src.relative_to(skill)
            wanted.add(rel.as_posix())
            target = dest / rel
            if target.is_file() and digest(target) == digest(src):
                continue
            drift.append(f"windows:{skill.name}/{rel.as_posix()}")
            if check:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            if digest(target) != digest(src):
                raise RuntimeError(f"copy to {target} did not verify")
            synced.append(f"windows:{skill.name}/{rel.as_posix()}")
        if dest.is_dir():
            for path in dest.rglob("*"):
                if not path.is_file() or any(p in IGNORED for p in path.parts):
                    continue
                rel = path.relative_to(dest).as_posix()
                if rel not in wanted:
                    extra.append(f"windows:{skill.name}/{rel}")
    return {"drift": drift, "synced": synced, "extra": extra}


# --------------------------------------------------------------------- wsl


def wsl_reachable() -> bool:
    return run_wsl(["true"], timeout=60)[0] == 0


def wsl_digests(skill_name: str) -> dict[str, str] | None:
    """sha256 of every file the daemon currently holds for this skill."""
    root = f"{WSL_SKILLS}/{skill_name}"
    code, out = run_wsl(["sh", "-c", f"find '{root}' -type f -exec sha256sum {{}} +"])
    if code != 0:
        return {}
    result = {}
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        rel = parts[1].strip()
        if rel.startswith(root + "/"):
            result[rel[len(root) + 1:]] = parts[0][:16]
    return result


def sync_wsl(*, check: bool, require: bool) -> dict:
    if not wsl_reachable():
        message = f"WSL distro {WSL_DISTRO!r} (user {WSL_USER!r}) is not reachable"
        return {"drift": [], "synced": [], "extra": [], "not_tested": [message]}
    drift, synced, extra = [], [], []
    for skill in canonical_skills():
        remote = wsl_digests(skill.name) or {}
        wanted = set()
        for src in skill_files(skill):
            rel = src.relative_to(skill).as_posix()
            wanted.add(rel)
            if remote.get(rel) == digest(src):
                continue
            drift.append(f"wsl:{skill.name}/{rel}")
            if check:
                continue
            target = f"{WSL_SKILLS}/{skill.name}/{rel}"
            parent = target.rsplit("/", 1)[0]
            code, out = run_wsl(["mkdir", "-p", parent])
            if code != 0:
                raise RuntimeError(f"mkdir {parent} failed: {out}")
            code, out = run_wsl(["cp", "-f", to_wsl_path(src), target])
            if code != 0:
                raise RuntimeError(f"cp to {target} failed: {out}")
            synced.append(f"wsl:{skill.name}/{rel}")
        for rel in sorted(set(remote) - wanted):
            extra.append(f"wsl:{skill.name}/{rel}")
    if synced:
        # Re-verify rather than trusting the copy we just made.
        for skill in canonical_skills():
            remote = wsl_digests(skill.name) or {}
            for src in skill_files(skill):
                rel = src.relative_to(skill).as_posix()
                if remote.get(rel) != digest(src):
                    raise RuntimeError(f"post-sync verification failed for {skill.name}/{rel}")
    return {"drift": drift, "synced": synced, "extra": extra, "not_tested": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift, change nothing")
    parser.add_argument(
        "--require-wsl",
        action="store_true",
        help="release gate: an unreachable daemon copy is a failure, not a skip",
    )
    parser.add_argument("--discover", action="store_true", help="list installed WSL distros and exit")
    parser.add_argument("--app-root", type=pathlib.Path, default=DEFAULT_APP_ROOT)
    args = parser.parse_args()

    if args.discover:
        try:
            done = subprocess.run(["wsl.exe", "-l", "-q"], capture_output=True, timeout=60)
            listed = done.stdout.decode("utf-16-le", errors="replace")
        except Exception as error:  # noqa: BLE001
            print(f"[fail] could not list WSL distros: {error}")
            return 1
        names = [n.strip() for n in listed.splitlines() if n.strip()]
        print(f"[configured] distro={WSL_DISTRO!r} user={WSL_USER!r} skills={WSL_SKILLS}")
        print(f"[installed ] {names}")
        if WSL_DISTRO not in names:
            print(f"[warn] configured distro {WSL_DISTRO!r} is not installed; "
                  "set LEO_WSL_DISTRO")
            return 1
        return 0

    skills = canonical_skills()
    if not skills:
        print(f"[fail] no canonical skills under {CANONICAL}")
        return 1
    print(f"[canonical] {CANONICAL} - {', '.join(s.name for s in skills)}")

    windows = sync_windows(args.app_root, check=args.check)
    wsl = sync_wsl(check=args.check, require=args.require_wsl)

    drift = windows["drift"] + wsl["drift"]
    synced = windows["synced"] + wsl["synced"]
    extra = windows["extra"] + wsl["extra"]
    not_tested = wsl.get("not_tested") or []

    for item in synced:
        print(f"[synced] {item}")
    for item in extra:
        print(f"[extra ] {item}  (not part of canonical; left in place, reported)")
    for item in not_tested:
        print(f"[NOT TESTED] {item}")

    if args.check:
        for item in drift:
            print(f"[drift ] {item}")
        if drift:
            print(f"[FAIL] {len(drift)} file(s) differ from canonical")
            return 1

    if not_tested:
        if args.require_wsl:
            print("[FAIL] --require-wsl was given but the daemon copy could not be verified")
            return 1
        print("[PARTIAL] Windows copy verified; daemon copy NOT TESTED")
        return 0

    print("[OK] canonical, deployed and daemon copies agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
