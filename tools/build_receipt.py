"""Bind a completed build to a clean source snapshot and exact package bytes.

This is local build evidence, not a signature or permission to issue a claim.
Creation is exclusive; a previous failed/successful receipt is never replaced.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys

RECEIPT = "build-receipt.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo).decode("utf-8").strip()


def inventory(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): {"sha256": sha(p), "size": p.stat().st_size}
            for p in sorted(root.rglob("*")) if p.is_file() and p.name != RECEIPT}


def source_state(repo: Path) -> dict:
    if git(repo, "status", "--porcelain"):
        raise ValueError("build source is dirty")
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo).decode("utf-8").split("\0")
    return {"commit": git(repo, "rev-parse", "HEAD"), "dirty": False,
            "files": {name: sha(repo / name) for name in names if name}}


def verify(receipt: dict, repo: Path, app: Path) -> list[str]:
    problems = []
    if receipt.get("schema_version") != 1 or receipt.get("mode") != "hermetic":
        problems.append("not a hermetic build receipt")
    try:
        start = datetime.datetime.fromisoformat(receipt["started_at"])
        end = datetime.datetime.fromisoformat(receipt["completed_at"])
        if start.tzinfo is None or end.tzinfo is None or start > end:
            raise ValueError("invalid build time interval")
        env = receipt["environment"]
        if not (env["python"] and env["platform"] and env["packages"] and receipt["command_template"]):
            raise ValueError("incomplete build environment")
    except (KeyError, TypeError, ValueError):
        problems.append("missing/invalid build execution metadata")
    source = receipt.get("source", {})
    if source != source_state(repo):
        problems.append("source snapshot mismatch")
    artifacts = receipt.get("artifacts")
    required = {"LeoAIStudio.exe", "_launcher/base_library.zip", "_launcher/python312.dll", "theme/shell.html"}
    if not isinstance(artifacts, dict) or not required.issubset(artifacts):
        return problems + ["missing artifact inventory"]
    for relative, expected in artifacts.items():
        path = (app / relative).resolve()
        if not path.is_relative_to(app.resolve()) or not path.is_file():
            problems.append(f"missing/unsafe artifact: {relative}")
        elif {"sha256": sha(path), "size": path.stat().st_size} != expected:
            problems.append(f"artifact mismatch: {relative}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("begin", "finish", "verify"))
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    args = parser.parse_args()
    if args.action == "begin":
        data = {"schema_version": 1, "mode": "hermetic", "source": source_state(args.repo),
                "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "environment": {"python": sys.version, "platform": platform.platform(),
                    "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}},
                "command_template": "tools/build_launcher.ps1 -BuildRoot <clean-checkout> -OutputRoot <fresh-output>"}
        with args.snapshot.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    elif args.action == "finish":
        data = json.loads(args.snapshot.read_text(encoding="utf-8"))
        if data["source"] != source_state(args.repo):
            raise ValueError("source changed while building")
        data["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data["artifacts"] = inventory(args.dist)
        with (args.dist / RECEIPT).open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    else:
        data = json.loads((args.dist / RECEIPT).read_text(encoding="utf-8"))
        problems = verify(data, args.repo, args.dist)
        print(json.dumps({"problems": problems}, indent=2))
        return bool(problems)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
