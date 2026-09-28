"""Driver of annulus revision 3 (240k steps, DAC-M2): attempt -> (Tier-1 || G6 reproduction) -> closure.

DECLARED IN CODE IDENTITY (``codeIdentityExtraFiles`` of ``exp_annulus_r3_240k.json``):
it chooses the attempt, the revision, the claim member and the order of the closing
steps, so its bytes can change a verdict. It holds no numerics; everything it calls
lives under ``pinn/``. Preregistration: EXPERIMENT_ANNULUS_R3_PREREGISTRATION_20260926.md.

    PYTHONPATH=. python experiments/annulus/run_formal_annulus_r3.py --workers 10 \
        --env-b-python <Env B interpreter>

Why revision 3 exists: r2 passed Gates 1-5 and then its bookkeeping crashed; the record
it left omitted two registered checks, and the owner ruled it void (2026-09-26, option B).
This driver's attempt runs a PREFLIGHT before the claim set is opened (the trust vector
and the decision are built and validated with what is known at that point), and the whole
chain was smoke-run in a sandbox worktree first -- see the preregistration.

The chain stops at the first step the rules do not let through, and records why. Tier-1
and the Env B reproduction are independent (Tier-1 reads the finished attempt, the
reproduction trains its own seeds), so they run side by side; each keeps its own worker
pool. The Env B interpreter is an argument (or LEO_ENV_B_PYTHON), never a path in the repo.
The other overrides exist for the sandbox smoke only; the defaults ARE the formal run.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path

from pinn.experiments.common import code_hash_from_manifest, code_manifest, load_json, utc_now
from pinn.experiments_annulus import closure_annulus as closure
from pinn.experiments_annulus.runner_annulus import AttemptAnnulus, EXPERIMENT_DIR, log, repo_root, run_tier1_for_attempt

CONFIG = Path("experiments/annulus/configs/exp_annulus_r3_240k.json")
PROBLEM_ID = "pdef-annulus-poisson-v1"
REVISION = 3
CLAIM_MEMBER = "DAC-M2"
ATTEMPT_ID = "exp-geometry1-annulus-poisson-r3"


def keep_awake(on: bool) -> None:
    """Ask Windows not to sleep while the chain runs (ES_CONTINUOUS | ES_SYSTEM_REQUIRED)."""

    if sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 if on else 0x80000000)


def current_code_hash(config: Path) -> str:
    extra = [config.as_posix(), *load_json(config).get("codeIdentityExtraFiles", [])]
    return code_hash_from_manifest(code_manifest(repo_root(), extra))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--env-b-python", default=os.environ.get("LEO_ENV_B_PYTHON"))
    parser.add_argument("--out-root", type=Path, default=EXPERIMENT_DIR / "runs")
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--problem-id", default=PROBLEM_ID)
    parser.add_argument("--revision", type=int, default=REVISION)
    parser.add_argument("--claim-pool-member", default=CLAIM_MEMBER)
    parser.add_argument("--attempt-id", default=ATTEMPT_ID)
    args = parser.parse_args(argv)
    if not args.env_b_python:
        parser.error("--env-b-python (or LEO_ENV_B_PYTHON) is required: G6 needs an independent environment")
    # lower case: runId must match ^run-[a-z0-9][a-z0-9-]*$ (r2 named it "-repro-envB"; the sandbox smoke caught it)
    repro_id = args.attempt_id + "-repro-envb"

    report: dict = {"startedAt": utc_now(), "attemptId": args.attempt_id, "workers": args.workers, "steps": []}
    report_path = args.out_root / f"{args.attempt_id}-CHAIN_REPORT.json"

    def note(step: str, **fields) -> None:
        report["steps"].append({"step": step, "at": utc_now(), **fields})
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        log(f"[chain] {step}: {fields}")

    keep_awake(True)
    repro = None
    try:
        attempt = AttemptAnnulus(config_path=args.config, attempt_id=args.attempt_id, problem_id=args.problem_id,
                                 revision=args.revision, out_root=args.out_root,
                                 claim_pool_member=args.claim_pool_member, device="cpu", workers=args.workers)
        summary = attempt.run()
        note("attempt", finalState=summary["finalState"], trustVector=summary.get("trustVector"),
             allowedClaims=summary.get("allowedClaims"), training=summary.get("training"),
             codeHash=summary.get("codeHash"), preflight=summary.get("preflight"))
        attempt_dir = args.out_root / args.attempt_id
        if summary["finalState"] != "REPRODUCIBILITY_CHECK":
            note("stop", reason="Gate 4 or Gate 5 did not pass; Tier-1 and G6 do not run")
            return 0

        command = [args.env_b_python, "-m", "pinn.experiments_annulus.runner_annulus", "attempt",
                   "--config", str(args.config), "--attempt-id", repro_id, "--problem-id", args.problem_id,
                   "--revision", str(args.revision), "--out-root", str(args.out_root),
                   "--claim-pool-member", args.claim_pool_member,
                   "--seed-offset", str(load_json(args.config)["reproduction"]["seedOffset"]),
                   "--reproduction-of", args.attempt_id, "--stop-after-gate", "4", "--workers", str(args.workers)]
        env = dict(os.environ, PYTHONPATH=str(Path.cwd()))
        console = (args.out_root / f"{repro_id}-console.log").open("w", encoding="utf-8")
        repro = subprocess.Popen(command, env=env, stdout=console, stderr=subprocess.STDOUT)
        note("reproduction-started", pid=repro.pid)

        tier1 = run_tier1_for_attempt(attempt_dir, device="cpu", workers=args.workers)
        note("tier1", dimensionImpact=tier1["dimensionImpact"], passed=tier1["passed"])
        note("tier1-merge", closureCodeHash=current_code_hash(args.config), **closure.merge_tier1(attempt_dir))

        code = repro.wait()
        console.close()
        repro_dir = args.out_root / repro_id
        repro_state = (load_json(repro_dir / "RUN_SUMMARY.json")["finalState"]
                       if (repro_dir / "RUN_SUMMARY.json").exists() else None)
        note("reproduction", returnCode=code, finalState=repro_state)
        if code != 0 or repro_state != "TRAINING_COMPLETED":
            note("stop", reason="the reproduction attempt did not pass its Gate 4; G6 is not applied")
            return 0
        judged = closure.judge_reproduction(attempt_dir, repro_dir)
        note("g6-judge", cRepro=judged["cRepro"], line=judged["summaryLine"])
        final = closure.apply_g6(attempt_dir, repro_dir)
        note("g6-apply", finalState=final["finalState"], allowedClaims=final["allowedClaimsFinal"],
             trustVector=final["trustVectorFinal"], held=final["g6"]["heldReason"],
             closureCodeHash=current_code_hash(args.config))
        return 0
    except BaseException as exc:  # recorded, then re-raised: a crash is a result too
        note("crash", error=f"{type(exc).__name__}: {exc}")
        if repro is not None and repro.poll() is None:
            note("reproduction-left-running", pid=repro.pid,
                 reason="not killed by the driver; the owner decides whether its result is used")
        raise
    finally:
        report["finishedAt"] = utc_now()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        keep_awake(False)


if __name__ == "__main__":
    raise SystemExit(main())
