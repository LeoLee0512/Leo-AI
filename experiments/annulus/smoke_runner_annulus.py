"""Sandbox smoke of the FULL annulus pipeline (not a formal run, not evidence).

The 2D round learned this the hard way and so did this one: a three-hour formal
attempt is a bad place to discover an API mismatch. This driver runs the entire
runner -- identity, problem, Gates 1-5, the failure path -- against a tiny
configuration in a throwaway sandbox with its own ledger, its own claim pool and
its own sample registry, so nothing it does can touch the real experiment.

    marking         SANDBOX
    formalEvidence  false
    claim pool      a sandbox pool sealed inside the sandbox ledger
    thresholds      the real ones (a smoke run is expected to FAIL them; that is
                    the point -- the failure path must work too)

Everything it writes lives under ``experiments/annulus/.smoke`` and is deleted by
the caller afterwards (repository hygiene: created and deleted, both logged).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from pinn.experiments_annulus import runner_annulus as runner

SANDBOX = Path("experiments/annulus/.smoke")


def sandbox_config(steps: int, seeds: int) -> dict:
    config = json.loads(Path("experiments/annulus/configs/exp_annulus_baseline.json").read_text(encoding="utf-8"))
    config["configId"] = "annulus-smoke-sandbox"
    config["optimizer"]["steps"] = steps
    config["optimizer"]["batchSize"] = 128
    config["sampling"]["poolSize"] = 256
    config["sampling"]["collocationCount"] = 128
    config["sampling"]["poolSeed"] = 20269001
    config["sets"].update({"devSize": 192, "devSeed": 20269002, "physRadialOrder": 12, "physAngularCount": 32,
                           "boundaryNodes": 32})
    config["seedProtocol"].update({"runs": seeds, "initBase": 20269100, "sampleBase": 20269200,
                                   "batchBase": 20269300})
    # a sandbox claim member: smaller grids, still covering all 64 cells
    config["claimPool"] = {"label": "SMOKE", "rule": "sandbox only", "members": {
        "SMOKE-M0": {"quadratureRadialOrder": 12, "quadratureAngularCount": 41, "angularOffset": 0.023,
                     "pointwiseCglCount": 26, "pointwiseAngularCount": 33, "pointwiseAngularOffset": 0.031}}}
    config["codeIdentityExtraFiles"] = []
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    (SANDBOX / "configs").mkdir(parents=True)
    config_path = SANDBOX / "configs" / "smoke_config.json"
    config_path.write_text(json.dumps(sandbox_config(args.steps, args.seeds), ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")

    # redirect every piece of state the runner writes outside the attempt directory
    runner.LEDGER_DIR = SANDBOX / "ledger"
    runner.PROBLEMS_DIR = SANDBOX / "problems"
    runner.REGISTRY_PATH = SANDBOX / "sample_set_registry.json"

    runner.run_register_pool("pdef-annulus-smoke", ["SMOKE-M0"], 1, config_path)
    attempt = runner.AttemptAnnulus(config_path=config_path, attempt_id="smoke-annulus",
                                    problem_id="pdef-annulus-smoke", revision=1,
                                    out_root=SANDBOX / "runs", claim_pool_member="SMOKE-M0",
                                    device=args.device)
    summary = attempt.run()
    print(json.dumps({k: summary[k] for k in sorted(summary) if k not in ("evaluationSets",)},
                     ensure_ascii=False, indent=2)[:4000])
    files = sum(1 for _ in SANDBOX.rglob("*") if _.is_file())
    size = sum(path.stat().st_size for path in SANDBOX.rglob("*") if path.is_file())
    print(f"\nsandbox produced {files} files / {size} bytes under {SANDBOX}")
    if not args.keep:
        shutil.rmtree(SANDBOX)
        print("sandbox deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
