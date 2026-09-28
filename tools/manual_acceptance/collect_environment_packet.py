"""Collect current-environment subfacts into a new, exclusive evidence directory.

This wrapper never creates accounts, changes WSL/WebView2, modifies credentials,
or marks a human checklist row accepted. Existing collectors' raw output and
exit codes are preserved. Lean is opt-in: inspect its actual toolchain first;
any theorem probe writes only inside this new evidence directory.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COLLECTORS = {"A": "collect_windows_account_env.py", "B": "verify_webview2_runtime.py",
              "C": "verify_wsl_environment.py", "D": "verify_lean_real_toolchain.py"}


def _save_json(path: Path, payload: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def collect(output: Path, app_root: Path, *, include_lean: bool = False) -> dict:
    output = output.resolve()
    app_root = app_root.resolve()
    if not (app_root / "LeoAIStudio.exe").is_file():
        raise ValueError("--app-root must name an actual installed product containing LeoAIStudio.exe")
    output.mkdir(parents=True, exist_ok=False)
    work = output / "isolated-probe-workdir"
    work.mkdir()
    environment = dict(os.environ)
    environment["LEO_APP_ROOT"] = str(app_root)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    records = {}
    for block in ("A", "B", "C", "D") if include_lean else ("A", "B", "C"):
        source = HERE / COLLECTORS[block]
        command = [sys.executable, str(source), "--json"]
        if block == "A":
            command += ["--app-root", str(app_root)]
        started = datetime.now(timezone.utc).isoformat()
        try:
            done = subprocess.run(command, cwd=work, env=environment, capture_output=True, timeout=600)
            raw_stdout, raw_stderr, exit_code = done.stdout, done.stderr, done.returncode
        except subprocess.TimeoutExpired as error:
            raw_stdout, raw_stderr, exit_code = error.stdout or b"", error.stderr or b"", None
            raw_stderr += b"\ncollector exceeded 600 seconds; no acceptance result exists\n"
        with (output / f"block-{block}.stdout.json").open("xb") as handle:
            handle.write(raw_stdout)
        with (output / f"block-{block}.stderr.txt").open("xb") as handle:
            handle.write(raw_stderr)
        try:
            payload = json.loads(raw_stdout.decode("utf-8"))
            parse_ok = isinstance(payload, dict) and "checks" in payload and "authority" in payload
        except (UnicodeDecodeError, ValueError):
            parse_ok = False
        records[block] = {"command": command, "startedAt": started, "exitCode": exit_code,
                          "parseableCollectorEvidence": parse_ok,
                          "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                          "manualRowDecision": "HUMAN REVIEW REQUIRED"}
    def git(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else "UNAVAILABLE"
    summary = {
        "kind": "P0_MANUAL_ENVIRONMENT_SUBFACTS", "createdAt": datetime.now(timezone.utc).isoformat(),
        "sourceCommit": git("rev-parse", "HEAD"), "sourceStatus": git("status", "--porcelain=v1"),
        "pythonExecutable": sys.executable, "pythonVersion": sys.version,
        "installedProduct": str(app_root),
        "installedExeSha256": hashlib.sha256((app_root / "LeoAIStudio.exe").read_bytes()).hexdigest(),
        "blocks": records, "notCollected": [block for block in ("D", "E", "F") if block not in records],
        "authority": "Evidence only. No manual row is signed; no P0 Gate is awarded.",
        "limitations": ["Current-account observations do not establish a fresh-account environment.",
                        "A collector suggested_verdict is not the manual-row decision.",
                        "D6 directory metadata cannot prove absence of all downloads.",
                        "A6 file inventory does not decrypt any secret or prove cross-account isolation."],
    }
    _save_json(output / "collection.json", summary)
    _save_json(output / "files.sha256.json", {
        path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.rglob("*")) if path.is_file()
    })
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--include-lean", action="store_true",
                        help="only after verifying Lean probing cannot trigger a toolchain installation")
    args = parser.parse_args()
    summary = collect(args.output, args.app_root, include_lean=args.include_lean)
    print(json.dumps({"evidence": str(args.output.resolve()), "blocks": summary["blocks"],
                      "manualReview": "HUMAN REVIEW REQUIRED"}, ensure_ascii=False))
    records = list(summary["blocks"].values())
    if any(row["exitCode"] not in (0, 2) or not row["parseableCollectorEvidence"] for row in records):
        return 1
    return 2 if any(row["exitCode"] == 2 for row in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
