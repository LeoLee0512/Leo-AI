"""Driver of annulus revision 2 (240k steps, DAC-M1): attempt -> Tier-1 -> G6, in one go.

DECLARED IN CODE IDENTITY (``codeIdentityExtraFiles`` of ``exp_annulus_r2_240k.json``):
it chooses the attempt, the revision, the claim member and the order of the closing
steps, so its bytes can change a verdict. It holds no numerics; everything it calls
lives under ``pinn/``. Preregistration: EXPERIMENT_ANNULUS_R2_PREREGISTRATION_20260926.md.

    PYTHONPATH=. python experiments/annulus/run_formal_annulus_r2.py --workers 10 \
        --env-b-python <Env B interpreter>

The chain stops at the first step the rules do not let through, and records why:
Gate 4 / Gate 5 not passing ends it inside the attempt (FAILURE_RECORDED); Tier-1
only runs after Gate 5 PASS; G6 is judged and applied only if the reproduction
attempt passed its own Gate 4. The Env B interpreter is an argument (or the
LEO_ENV_B_PYTHON environment variable), never a path written into the repository.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path

from pinn.experiments.common import load_json, utc_now
from pinn.experiments_annulus import closure_annulus as closure
from pinn.experiments_annulus.runner_annulus import AttemptAnnulus, EXPERIMENT_DIR, log, run_tier1_for_attempt

CONFIG = Path("experiments/annulus/configs/exp_annulus_r2_240k.json")
PROBLEM_ID = "pdef-annulus-poisson-v1"
REVISION = 2
CLAIM_MEMBER = "DAC-M1"
ATTEMPT_ID = "exp-geometry1-annulus-poisson-r2"
REPRO_ID = ATTEMPT_ID + "-repro-envB"


def keep_awake(on: bool) -> None:
    """Ask Windows not to sleep while the chain runs (ES_CONTINUOUS | ES_SYSTEM_REQUIRED)."""

    if sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 if on else 0x80000000)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--env-b-python", default=os.environ.get("LEO_ENV_B_PYTHON"))
    parser.add_argument("--out-root", type=Path, default=EXPERIMENT_DIR / "runs")
    args = parser.parse_args()
    if not args.env_b_python:
        parser.error("--env-b-python (or LEO_ENV_B_PYTHON) is required: G6 needs an independent environment")

    report: dict = {"startedAt": utc_now(), "attemptId": ATTEMPT_ID, "workers": args.workers, "steps": []}
    report_path = args.out_root / f"{ATTEMPT_ID}-CHAIN_REPORT.json"

    def note(step: str, **fields) -> None:
        report["steps"].append({"step": step, "at": utc_now(), **fields})
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        log(f"[chain] {step}: {fields}")

    keep_awake(True)
    try:
        attempt = AttemptAnnulus(config_path=CONFIG, attempt_id=ATTEMPT_ID, problem_id=PROBLEM_ID, revision=REVISION,
                                 out_root=args.out_root, claim_pool_member=CLAIM_MEMBER, device="cpu",
                                 workers=args.workers)
        summary = attempt.run()
        note("attempt", finalState=summary["finalState"], trustVector=summary.get("trustVector"),
             allowedClaims=summary.get("allowedClaims"), training=summary.get("training"))
        attempt_dir = args.out_root / ATTEMPT_ID
        if summary["finalState"] != "REPRODUCIBILITY_CHECK":
            note("stop", reason="Gate 4 or Gate 5 did not pass; Tier-1 and G6 do not run")
            return 0

        tier1 = run_tier1_for_attempt(attempt_dir, device="cpu", workers=args.workers)
        note("tier1", dimensionImpact=tier1["dimensionImpact"], passed=tier1["passed"])
        note("tier1-merge", **closure.merge_tier1(attempt_dir))

        command = [args.env_b_python, "-m", "pinn.experiments_annulus.runner_annulus", "attempt",
                   "--config", str(CONFIG), "--attempt-id", REPRO_ID, "--problem-id", PROBLEM_ID,
                   "--revision", str(REVISION), "--out-root", str(args.out_root),
                   "--claim-pool-member", CLAIM_MEMBER,
                   "--seed-offset", str(load_json(CONFIG)["reproduction"]["seedOffset"]),
                   "--reproduction-of", ATTEMPT_ID, "--stop-after-gate", "4", "--workers", str(args.workers)]
        env = dict(os.environ, PYTHONPATH=str(Path.cwd()))
        completed = subprocess.run(command, env=env)
        repro_dir = args.out_root / REPRO_ID
        repro_state = load_json(repro_dir / "RUN_SUMMARY.json")["finalState"] if (repro_dir / "RUN_SUMMARY.json").exists() else None
        note("reproduction", returnCode=completed.returncode, finalState=repro_state)
        if completed.returncode != 0 or repro_state != "TRAINING_COMPLETED":
            note("stop", reason="the reproduction attempt did not pass its Gate 4; G6 is not applied")
            return 0
        judged = closure.judge_reproduction(attempt_dir, repro_dir)
        note("g6-judge", cRepro=judged["cRepro"], line=judged["summaryLine"])
        final = closure.apply_g6(attempt_dir, repro_dir)
        note("g6-apply", finalState=final["finalState"], allowedClaims=final["allowedClaimsFinal"],
             trustVector=final["trustVectorFinal"], held=final["g6"]["heldReason"])
        return 0
    except BaseException as exc:  # recorded, then re-raised: a crash is a result too
        note("crash", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        report["finishedAt"] = utc_now()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        keep_awake(False)


if __name__ == "__main__":
    raise SystemExit(main())
