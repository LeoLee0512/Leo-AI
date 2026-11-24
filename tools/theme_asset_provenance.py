"""Report which theme assets the runtime reads have a tracked canonical source.

This is the standing evidence for Grok F-008 (UNVERSIONED PRODUCT ASSET), kept
as a tool rather than a paragraph so the answer is re-measurable instead of
asserted.  It walks every file :class:`leo_shell.theme_runtime.ThemeRuntime`
opens on a real installation and asks three questions of each:

1. is there a source and origin record committed at HEAD,
2. do the working source and deployed bytes match that committed identity, and
3. are required upstream license notices present with the recorded hashes?

An asset that fails (1) ships from whatever happened to be on the build machine
and cannot be reproduced from the repository.  An asset that fails (2) means the
deployment drifted from the tree. Every asset is copied verbatim from stage/
(the assembled upstream-injection bundle was removed on 2026-09-26). Native
content-addressed ICO files are exact source ICO copies under the naming recipe in
``leo_shell/windows_branding.py``; arbitrary extra icons remain gaps. Neither
generated resource is exempt from byte checking.

    python tools/theme_asset_provenance.py
    python tools/theme_asset_provenance.py --strict   # non-zero while gaps remain

Exit code is 0 unless ``--strict`` is given and something is unversioned or has
drifted, so the default form can be run for information without failing a build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_APP_ROOT = Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio")

# Every asset maps to the file of the same name under stage/.
ORIGINS = "manifests/runtime-asset-origins.json"

# Fixed set, in the order ThemeRuntime reaches for them. The backgrounds are
# discovered from the installation because their manifest decides what exists.
FIXED = (
    "workbench.html",
    "workbench.css",
    "workbench.js",
    "research-panel.js",
    "shell.html",
    "themes.json",
    "logos/leo-lion.svg",
    "logos/leo-favicon.svg",
    "logos/leo-lion-1024.png",
    "logos/leo-lion.ico",
)


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def tracked_files() -> set[str]:
    done = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, text=True, encoding="utf-8", check=False
    )
    return set(done.stdout.split("\0")) - {""} if done.returncode == 0 else set()


def committed_sha256(relative: str) -> str | None:
    done = subprocess.run(
        ["git", "show", f"HEAD:{relative}"], cwd=REPO, capture_output=True, check=False
    )
    return hashlib.sha256(done.stdout).hexdigest() if done.returncode == 0 else None


def source_mapping(relative: str) -> tuple[str, tuple[str, ...], str | None]:
    """Recognize only the runtime's exact content-addressed ICO recipe."""
    generated = re.fullmatch(r"logos/leo-lion\.([0-9a-f]{16})\.ico", relative)
    if generated:
        return "stage/logos/leo-lion.ico", ("stage/logos/leo-lion.ico", "leo_shell/windows_branding.py"), generated[1]
    candidate = f"stage/{relative}"
    return candidate, (candidate,), None


def runtime_assets(theme: Path) -> list[str]:
    assets = list(FIXED)
    for directory in ("backgrounds", "logos", "intro"):
        # Include both source and deployed files: a missing deployed icon must
        # still be checked, and an extra legacy asset must remain visible.
        for asset_root in (theme, REPO / "stage"):
            folder = asset_root / directory
            if folder.is_dir():
                assets += sorted(
                    p.relative_to(asset_root).as_posix()
                    for p in folder.rglob("*") if p.is_file()
                )
    return list(dict.fromkeys(assets))


def audit_assets(theme: Path) -> list[tuple[str, str, str, str]]:
    """Fail closed for missing, uncommitted, modified or unregistered sources."""
    tracked = tracked_files()
    try:
        origins = json.loads((REPO / ORIGINS).read_text("utf-8"))["assets"]
        if not isinstance(origins, dict):
            raise ValueError("assets must be a mapping")
    except (OSError, ValueError, KeyError) as exc:
        return [("GAP", ORIGINS, ORIGINS, f"origin manifest unavailable: {exc}")]
    rows: list[tuple[str, str, str, str]] = []
    for relative in runtime_assets(theme):
        candidate, layers, icon_digest = source_mapping(relative)
        needed = (*layers, ORIGINS)
        if any(path not in tracked or committed_sha256(path) is None for path in needed):
            rows.append(("GAP", relative, candidate, "source or origin manifest has no HEAD commit"))
            continue
        if any(sha256(REPO / path) != committed_sha256(path) for path in needed):
            rows.append(("DRIFT", relative, candidate, "working source differs from committed bytes"))
            continue
        origin_key = "logos/leo-lion.ico" if icon_digest else relative
        origin = origins.get(origin_key)
        if not isinstance(origin, dict) or origin.get("provenance_status") not in {
            "COMMITTED_PROJECT_SOURCE", "PINNED_UPSTREAM_REPRODUCED", "PROJECT_AUTHORED_REPLACEMENT"
        }:
            rows.append(("GAP", relative, candidate, "SOURCE UNKNOWN or missing origin record"))
            continue
        support_error = None
        supporting = origin.get("supporting_files", {})
        if not isinstance(supporting, dict) or any(not isinstance(path, str) for path in supporting):
            rows.append(("GAP", relative, candidate, "malformed supporting-file origin record"))
            continue
        for path, expected_hash in supporting.items():
            support = Path(path)
            if support.is_absolute() or ".." in support.parts or ":" in path or "\\" in path:
                support_error = "GAP", "unsafe supporting-file path in origin manifest"
                break
            if path not in tracked or committed_sha256(path) is None:
                support_error = "GAP", f"supporting source is not committed: {path}"
                break
            if not (sha256(REPO / path) == committed_sha256(path) == expected_hash == sha256(theme.parent / path)):
                support_error = "DRIFT", f"supporting license source/deployment/hash mismatch: {path}"
                break
        if support_error:
            rows.append((support_error[0], relative, candidate, support_error[1]))
            continue
        expected = sha256(REPO / candidate)
        if expected != origin.get("expected_sha256"):
            rows.append(("DRIFT", relative, candidate, "origin hash differs from source/recipe bytes"))
        elif icon_digest and (expected is None or not expected.startswith(icon_digest)):
            rows.append(("DRIFT", relative, candidate, "generated ICO filename is not its source digest"))
        elif expected is None or expected != sha256(theme / relative):
            rows.append(("DRIFT", relative, candidate, "deployed bytes differ from committed source/recipe"))
        else:
            note = "derived ICO name and bytes match tracked source" if icon_digest else "committed source/recipe and deployed bytes match"
            rows.append(("OK", relative, candidate, note))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--app-root", type=Path, default=DEFAULT_APP_ROOT)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero while any asset is unversioned or has drifted",
    )
    args = parser.parse_args(argv)

    theme = args.app_root.resolve() / "theme"
    if not theme.is_dir():
        print(f"no theme directory at {theme}", file=sys.stderr)
        return 2

    tracked = tracked_files()
    if not tracked:
        print("git ls-files returned nothing; not a repository?", file=sys.stderr)
        return 2

    rows = audit_assets(theme)
    gaps = sum(row[0] == "GAP" for row in rows)
    drifted = sum(row[0] == "DRIFT" for row in rows)
    versioned = len(rows) - gaps

    width = max(len(row[1]) for row in rows)
    for mark, relative, candidate, note in rows:
        print(f"  [{mark:<5}] {relative:<{width}}  {candidate:<38} {note}")

    total = len(rows)
    gaps = total - versioned
    print(
        f"\n  {versioned}/{total} runtime-read theme assets have a tracked canonical source"
        f"; {gaps} unversioned, {drifted} drifted."
    )
    if gaps or drifted:
        print("  F-008 remains OPEN for the assets marked GAP or DRIFT.")
    else:
        print("  F-008 is CLOSED: every runtime-read theme asset is versioned.")
    return 1 if args.strict and (gaps or drifted) else 0


if __name__ == "__main__":
    raise SystemExit(main())
