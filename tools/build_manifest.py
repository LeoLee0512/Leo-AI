"""Record what a release is actually made of.

P0-1's acceptance question is "from the canonical repo, can you explain what the
current release consists of?" Before this existed the answer was no: there was no
version control on any Leo code, three copies of the theme with no declared
source of truth, and nothing tying a built EXE to the inputs that produced it.

Every field is either measured or explicitly ``"unknown"``. Nothing is guessed —
a manifest that invents a value is worse than one that admits a gap, because the
whole point is to be able to trust it later.

    python tools/build_manifest.py                    # print
    python tools/build_manifest.py -o manifests/x.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
# The installed product lives inside the checkout (git-ignored); LEO_APP_ROOT
# or --app-root points elsewhere.
DEFAULT_APP_ROOT = pathlib.Path(os.environ.get("LEO_APP_ROOT") or REPO / "LeoAIStudio")
UNKNOWN = "unknown"


def run(args, cwd=None) -> str | None:
    try:
        done = subprocess.run(args, cwd=cwd, capture_output=True, timeout=120)
    except Exception:
        return None
    if done.returncode != 0:
        return None
    return done.stdout.decode("utf-8", errors="replace").strip() or None


def sha256(path: pathlib.Path) -> str:
    if not path.is_file():
        return UNKNOWN
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_state(root: pathlib.Path) -> dict:
    if not (root / ".git").exists():
        return {"commit": UNKNOWN, "reason": f"{root} is not a git repository"}
    commit = run(["git", "rev-parse", "HEAD"], cwd=root)
    if commit is None:
        return {"commit": UNKNOWN, "reason": "no commit yet"}
    dirty = run(["git", "status", "--porcelain"], cwd=root)
    return {
        "commit": commit,
        "committed_at": run(["git", "log", "-1", "--format=%cI"], cwd=root) or UNKNOWN,
        "dirty": bool(dirty),
        "dirty_files": len(dirty.splitlines()) if dirty else 0,
    }


#: Every document and script the shell loads, copied verbatim from stage/ to theme/.
#: (The upstream-page injection bundle this section used to describe was removed
#: on 2026-09-26; nothing is assembled any more, so each file is its own record.)
FRONTEND_FILES = ("shell.html", "workbench.html", "workbench.css", "workbench.js", "research-panel.js")


def frontend_record(app_root: pathlib.Path) -> dict:
    """Pair each document the shell loads with its committed source and deployed copy."""
    return {
        "sources": {f"stage/{name}": sha256(REPO / "stage" / name) for name in FRONTEND_FILES},
        "deployed": {f"theme/{name}": sha256(app_root / "theme" / name) for name in FRONTEND_FILES},
        "themes": theme_assets(app_root),
    }


def theme_assets(app_root: pathlib.Path) -> dict:
    """Tie every runtime-read theme asset to a committed source and a deployed copy.

    The registry, the artwork, the logos and the opening animation are read by
    the runtime or shipped with it, so each needs a canonical source. Each entry pairs the repository's copy with
    the installed one, so ``verify_release.py`` can prove the deployment came
    from the tree rather than from whatever was already on the machine.
    """
    staged = REPO / "stage"
    installed = app_root / "theme"
    out: dict[str, dict[str, str]] = {}
    relatives = ["themes.json"]
    for directory in ("backgrounds", "logos", "intro"):
        assets = staged / directory
        if assets.is_dir():
            relatives += sorted(
                item.relative_to(staged).as_posix()
                for item in assets.rglob("*") if item.is_file()
            )
    for relative in relatives:
        out[relative] = {
            "source_sha256": sha256(staged / relative),
            "deployed_sha256": sha256(installed / relative),
        }
    masters = REPO / "assets" / "backgrounds"
    if masters.is_dir():
        out["masters"] = {
            item.name: sha256(item) for item in sorted(masters.iterdir()) if item.is_file()
        }
    return out


def runtime_state(app_root: pathlib.Path) -> dict:
    """Runtime metadata and deployed bridge bytes, not daemon execution claims."""
    out: dict = {}
    for name in ("runtime-manifest.json", "runtime-dependencies.json"):
        path = app_root / "runtime" / name
        if not path.is_file():
            path = app_root / name
        if path.is_file():
            try:
                out[name] = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                out[name] = {"error": "unreadable"}
        else:
            out[name] = UNKNOWN
    # The identity overlay is a deployed startup input. These hashes establish
    # which helper shipped; application to the active WSL source and a running
    # daemon's responses still require independent live verification.
    out["bridge_resources"] = {
        relative: {
            "source_sha256": sha256(REPO / relative),
            "deployed_sha256": sha256(app_root / relative),
        }
        for relative in (
            "bridge/leo_local_relay.py",
            "bridge/leo_model_selection.py",
            "bridge/leo_identity.py",
            "bridge/leo_runtime_compat.py",
            "bridge/leo_example_persistence.py",
            "bridge/leo_runtime_features.py",
            "bridge/leo_reasoning.py",
            "bridge/leo_turn_binding.py",
            "bridge/leo_turn_binding_runtime.py",
            "bridge/leo_thought_runtime.py",
        )
    }
    return out


def toolchain() -> dict:
    versions = {"python": sys.version.split()[0]}
    for module in ("PyInstaller", "webview", "cryptography"):
        try:
            versions[module] = __import__(module).__version__
        except Exception:
            versions[module] = UNKNOWN
    return versions


def build_manifest(app_root: pathlib.Path) -> dict:
    upstream = app_root / "upstream" / "OpenAI4S"
    exe = app_root / "LeoAIStudio.exe"
    return {
        "schema_version": 1,
        "product": __import__("release_identity").product_identity(),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "leo_repo": git_state(REPO),
        "upstream_openai4s": {
            **git_state(upstream),
            "remote": run(["git", "remote", "get-url", "origin"], cwd=upstream) or UNKNOWN,
        },
        "frontend": frontend_record(app_root),
        "runtime": runtime_state(app_root),
        "toolchain": toolchain(),
        "deployed_exe_sha256": sha256(exe),
        "build_receipt_sha256": sha256(app_root / "build-receipt.json"),
        "skills": {
            path.name: {
                file.name: sha256(file)
                for file in sorted(path.iterdir())
                if file.is_file()
            }
            for path in sorted((REPO / "skills").iterdir())
            if path.is_dir()
        }
        if (REPO / "skills").is_dir()
        else UNKNOWN,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--output", type=pathlib.Path)
    parser.add_argument("--app-root", type=pathlib.Path, default=DEFAULT_APP_ROOT)
    args = parser.parse_args()

    manifest = build_manifest(args.app_root)
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"[ok] wrote {args.output}")
    else:
        print(text)

    if manifest["leo_repo"].get("dirty"):
        print(
            f"[warn] the Leo repo has {manifest['leo_repo']['dirty_files']} uncommitted "
            "file(s): this build is not reproducible from a commit",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
