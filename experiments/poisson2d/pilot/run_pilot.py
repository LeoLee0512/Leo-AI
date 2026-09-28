"""EXPLORATORY / PERFORMANCE-ONLY PILOT for the 2D Poisson calibration (PART 4).

Purpose, and the only purpose: CPU practicality, batch size, memory, approximate
runtime, and whether the preregistered acceptance level is attainable at all on
D_dev before the thresholds and the architecture are frozen.

NOT used for: picking the best architecture by claim data, picking a seed,
tuning any claim threshold, choosing D_claim, or supporting any claim.

    EXPLORATORY
    Claim eligibility <= C1
    not part of formal evidence

The pilot uses its own seed bases (20260800 / 20260810 / 20260820), which are
disjoint from the formal seed bases registered in the preregistration, and only
D_dev / D_train pool points.  Output: experiments/poisson2d/pilot/PILOT_RESULT.json
(kept separate from every formal attempt directory).
"""

from __future__ import annotations

import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pinn.experiments2d import datasets2d as ds
from pinn.experiments2d import pinn_torch2d as pinn2d
from pinn.reference import analytic_poisson2d as reference

OUT = Path("experiments/poisson2d/pilot/PILOT_RESULT.json")
POOL_SIZE = 2048
POOL_SEED = 20260917
DEV_SIZE = 1024
DEV_SEED = 20260918
SEEDS = {"init": 20260800, "sample": 20260810, "batch": 20260820}


def config(hidden: int, width: int, steps: int, batch: int, threads: int) -> dict:
    return {
        "configId": f"pilot-{hidden}x{width}-s{steps}-b{batch}-t{threads}",
        "network": {"hiddenLayers": hidden, "width": width, "activation": "tanh", "input": "x,y", "output": "u",
                    "initialization": "torch default (Kaiming uniform) under init seed",
                    "outputParameterization": "x(1-x)y(1-y)N"},
        "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "schedule": "exponential decay lr -> finalLr over steps",
                      "steps": steps, "batchSize": batch, "threads": threads, "stopping": "fixed step count; no early stopping"},
        "lossWeights": {"pde": 1.0},
        "sampling": {"poolSize": POOL_SIZE, "poolSeed": POOL_SEED, "collocationCount": 1024,
                     "rule": "collocationCount pool indices drawn without replacement by the run's sampling seed"},
    }


def parameter_count(hidden: int, width: int) -> int:
    total = (2 + 1) * width
    for _ in range(hidden - 1):
        total += (width + 1) * width
    return total + width + 1


def main() -> int:
    pool = ds.uniform_interior(POOL_SIZE, POOL_SEED)
    dev = ds.uniform_interior(DEV_SIZE, DEV_SEED)
    exact = [reference.solution(x, y) for x, y in dev]
    variants = [
        # (hiddenLayers, width, steps, batchSize, collocationCount, threads)
        (3, 32, 6000, 256, 1024, 1),      # the frozen 1D architecture and step budget, transplanted unchanged
        (4, 64, 10000, 512, 1024, 1),
        (4, 64, 20000, 1024, 2048, 1),
        (5, 64, 20000, 1024, 2048, 1),
        (4, 128, 20000, 1024, 2048, 1),
    ]
    results = []
    for hidden, width, steps, batch, collocation, threads in variants:
        cfg = config(hidden, width, steps, batch, threads)
        cfg["sampling"]["collocationCount"] = collocation
        started = time.perf_counter()
        run = pinn2d.train_run(cfg, pool, dev, SEEDS, collocation_count=collocation, log_every=max(steps // 6, 1))
        elapsed = time.perf_counter() - started
        model = pinn2d.model_from_weights(cfg, run["weights"], threads=threads)
        fld = pinn2d.fields(model, dev, threads=threads)
        residuals = [abs(-(xx + yy) - reference.forcing(x, y)) for xx, yy, (x, y) in zip(fld["uxx"], fld["uyy"], dev)]
        errors = [abs(a - b) for a, b in zip(fld["u"], exact)]
        entry = {
            "variant": cfg["configId"], "hiddenLayers": hidden, "width": width, "steps": steps, "batchSize": batch,
            "collocationCount": collocation, "threads": threads, "parameters": parameter_count(hidden, width),
            "elapsedSeconds": elapsed, "secondsPerThousandSteps": elapsed / (steps / 1000.0),
            "devRelL2": run["devRelL2"], "devMaxAbsError": max(errors), "devResidualMax": max(residuals),
            "finalLoss": run["finalLoss"], "completed": run["completed"], "nan": run["nanEncountered"],
        }
        results.append(entry)
        print(f"[pilot] {entry['variant']}: devRelL2={entry['devRelL2']:.3e} maxAbs={entry['devMaxAbsError']:.3e} "
              f"{elapsed:.1f}s ({entry['secondsPerThousandSteps']:.1f} s / 1000 steps)", flush=True)
    document = {
        "marking": "EXPLORATORY",
        "claimEligibility": "<= C1",
        "formalEvidence": False,
        "purpose": "CPU practicality, batch size, memory, approximate runtime, attainability of the acceptance level on D_dev",
        "forbiddenUses": ["architecture selection by claim data", "seed selection", "claim threshold tuning",
                          "D_claim selection", "supporting any claim"],
        "evaluationSets": {"trainPool": f"{POOL_SIZE} uniform interior points, default_rng({POOL_SEED})",
                           "dev": f"{DEV_SIZE} uniform interior points, default_rng({DEV_SEED})",
                           "claim": "not touched"},
        "seeds": SEEDS,
        "seedNote": "pilot seed bases are disjoint from the formal seed bases; no pilot run may be reused as a formal run",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "startedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "variants": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[pilot] written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
