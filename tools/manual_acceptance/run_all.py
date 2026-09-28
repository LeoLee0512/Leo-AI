"""Run every manual-acceptance collector and write one combined evidence file.

    python tools/manual_acceptance/run_all.py --save

This is a convenience, not an acceptance run. It cannot pass a single row of
``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md``: the collectors only report what they
can see from where they are running, and all 27 rows stay NOT TESTED until a
person executes them in the environments those rows are about.

The exit code describes the *collection*: 0 when every collector reached a
determination, 2 when something was undetermined, 1 when a collector found an
actual failure. A non-zero exit is not a checklist FAIL.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import decode  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVIDENCE_DIR = REPO / "docs" / "manual-acceptance-evidence"

COLLECTORS = (
    ("A", "collect_windows_account_env.py"),
    ("B", "verify_webview2_runtime.py"),
    ("C", "verify_wsl_environment.py"),
    ("D", "verify_lean_real_toolchain.py"),
    ("E", "verify_research_sop_live.py"),
    ("F", "verify_clean_build.py"),
)


def main() -> int:
    save = "--save" in sys.argv
    combined = {
        "collected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checklist": "docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md",
        "authority": (
            "Collected evidence only. All 27 checklist rows remain NOT TESTED until a "
            "person runs them in the required environment and records what they saw. "
            "Nothing in this file may be transcribed into the checklist as a PASS."
        ),
        "blocks": {},
    }
    worst = 0
    for block, script in COLLECTORS:
        command = [sys.executable, str(HERE / script), "--json"]
        # Bytes, then decode: the collectors emit UTF-8 JSON, and letting
        # subprocess decode with the console code page loses the whole payload on
        # a non-UTF-8 machine -- which reads afterwards as "the collector found
        # nothing" rather than "the runner could not read it".
        done = subprocess.run(command, cwd=REPO, capture_output=True, timeout=3600)
        stdout, stderr = decode(done.stdout), decode(done.stderr)
        try:
            payload = json.loads(stdout)
        except ValueError:
            payload = {
                "tool": script,
                "error": "collector produced no parseable output",
                "stdout": stdout[-4000:],
                "stderr": stderr[-4000:],
            }
        combined["blocks"][block] = {"exit_code": done.returncode, "report": payload}
        worst = max(worst, 1 if done.returncode == 1 else 2 if done.returncode == 2 else 0)

        checks = payload.get("checks", []) if isinstance(payload, dict) else []
        failures = sum(1 for c in checks if c.get("verdict") == "FAIL")
        undetermined = sum(1 for c in checks if c.get("verdict") == "UNDETERMINED")
        print(f"  block {block}  {script:36s} exit={done.returncode}  "
              f"{failures} fail  {undetermined} undetermined")

    if save:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = EVIDENCE_DIR / f"manual-acceptance-{stamp}.json"
        destination.write_text(
            json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\n  evidence saved: {destination}")

    print()
    print("  All 27 checklist rows remain NOT TESTED. These collectors record what this")
    print("  machine can see; they do not and cannot execute the acceptance items.")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
