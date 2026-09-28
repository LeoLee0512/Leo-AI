"""Driver of the formal annular Poisson attempt (Geometry Lift 1).

This script is DECLARED IN CODE IDENTITY (``config["codeIdentityExtraFiles"]``):
it chooses which attempt runs, under which revision and against which sealed claim
member, so its bytes can change a scientific verdict and must be inside the
manifest the run records. It contains no numerics of its own -- everything it calls
lives under ``pinn/``.

    PYTHONPATH=. python experiments/annulus/run_formal_annulus.py --attempt-id exp-geometry1-annulus-poisson-r1

``--device`` selects the TRAINING device only. It is deliberately a command-line
argument and not a config field: the config is hashed into codeHash, and the G6
reproduction has to run the same codeHash on a CPU-only environment. Evaluation always
runs on the CPU. The device does change ``acceleratorClass``, which is an environment
field, and that is recorded in identity.json and in the run record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pinn.experiments_annulus.runner_annulus import AttemptAnnulus, EXPERIMENT_DIR, run_tier1_for_attempt

CONFIG = Path("experiments/annulus/configs/exp_annulus_baseline.json")
PROBLEM_ID = "pdef-annulus-poisson-v1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--attempt-id")
    parser.add_argument("--tier1", type=Path,
                        help="run the Tier-1 Red Team against this finished attempt directory instead of "
                             "starting an attempt; it refuses unless that attempt passed Gate 5")
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--claim-pool-member", default="DAC-M0")
    parser.add_argument("--seed-offset", type=int, default=0)
    parser.add_argument("--stop-after-gate", type=int)
    parser.add_argument("--reproduction-of")
    parser.add_argument("--out-root", type=Path, default=EXPERIMENT_DIR / "runs")
    parser.add_argument("--device", default="cpu", help="training device (cpu / cuda / cuda:N); execution, not method")
    args = parser.parse_args()

    if args.tier1 is not None:
        print(json.dumps(run_tier1_for_attempt(args.tier1, device=args.device), ensure_ascii=False, indent=2)[:4000])
        return 0
    if not args.attempt_id:
        parser.error("--attempt-id is required unless --tier1 is given")

    attempt = AttemptAnnulus(config_path=CONFIG, attempt_id=args.attempt_id, problem_id=PROBLEM_ID,
                             revision=args.revision, out_root=args.out_root,
                             claim_pool_member=args.claim_pool_member, seed_offset=args.seed_offset,
                             reproduction_of=args.reproduction_of, stop_after_gate=args.stop_after_gate,
                             device=args.device)
    summary = attempt.run()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
