"""EXPLORATORY performance smoke for the annular Poisson experiment (Geometry Lift 1 section 11.1).

PERFORMANCE-ONLY. This is not an architecture search: the square-2D baseline
(4 x 64 tanh, Adam 1e-3 -> 1e-5, 10000 steps, batch 512, 1024 collocation points,
float64, deterministic) is carried over unchanged, and the only question asked
here is whether it is FEASIBLE on the annulus -- runtime, memory, the geometry
sampler, the hard factor, and whether the runner machinery works at all.

    marking          EXPLORATORY
    claimEligibility <= C1
    formalEvidence   false
    evaluationSets   train pool + D_dev only; the claim pool does not exist yet
    seeds            20261200 / 20261210 / 20261220 -- disjoint from the formal bases

A change of architecture before the freeze would need this to show the frozen
one is not viable at all; a better number on one variant is not a reason.
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

from pinn.experiments_annulus import datasets_annulus as ds
from pinn.experiments_annulus import pinn_torch_annulus as pinn
from pinn.geometry import annulus as geo
from pinn.reference import analytic_annulus as ref

OUT = Path("experiments/annulus/smoke/SMOKE_RESULT.json")

CONFIG = {
    "configId": "annulus-smoke-exploratory",
    "network": {"hiddenLayers": 4, "width": 64, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "(R^2-s)(s-a^2)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": 10000, "batchSize": 512, "threads": 1},
    "lossWeights": {"pde": 1.0},
    "sampling": {"poolSize": 2048, "poolSeed": 20261230, "collocationCount": 1024},
    "sets": {"devSize": 1024, "devSeed": 20261240},
}
SEEDS = {"init": 20261200, "sample": 20261210, "batch": 20261220}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    pool = ds.area_uniform_interior(CONFIG["sampling"]["poolSize"], CONFIG["sampling"]["poolSeed"])
    dev = ds.area_uniform_interior(CONFIG["sets"]["devSize"], CONFIG["sets"]["devSeed"])
    sampling_seconds = time.perf_counter() - started

    run = pinn.train_run(CONFIG, pool, dev, SEEDS, collocation_count=CONFIG["sampling"]["collocationCount"],
                         log_every=1000)
    model = pinn.model_from_weights(CONFIG, run["weights"])

    boundary = {}
    for component in geo.BOUNDARY_COMPONENTS:
        nodes, weights = geo.boundary_nodes(component, 64)
        values = pinn.values(model, nodes)
        boundary[component] = {"maxAbsU": max(abs(v) for v in values), "nodes": len(nodes)}

    dev_fields = pinn.fields(model, dev)
    residuals = [-(xx + yy) - ref.forcing(x, y)
                 for xx, yy, (x, y) in zip(dev_fields["uxx"], dev_fields["uyy"], dev)]
    residual_rms = (sum(r * r for r in residuals) / len(residuals)) ** 0.5 / ref.F_RMS

    record = {
        "marking": "EXPLORATORY",
        "claimEligibility": "<= C1",
        "formalEvidence": False,
        "purpose": "performance / feasibility only (Geometry Lift 1 section 11.1); no architecture comparison",
        "geometryId": geo.GEOMETRY["geometryId"],
        "config": CONFIG,
        "seeds": SEEDS,
        "evaluationSets": {"trainPool": len(pool), "dev": len(dev), "claim": "not touched (no pool sealed yet)"},
        "samplingSeconds": sampling_seconds,
        "trainingSeconds": run["elapsedSeconds"],
        "devRelL2": run["devRelL2"],
        "normalizedResidualRms": residual_rms,
        "hardBoundaryMaxAbsU": boundary,
        "lossHistory": run["lossHistory"],
        "completed": run["completed"],
        "nanEncountered": run["nanEncountered"],
        "interpreter": sys.version,
        "platform": platform.platform(),
        "tenSeedCostEstimateSeconds": run["elapsedSeconds"] * 10,
    }
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"dev relative L2 {run['devRelL2']:.3e} in {run['elapsedSeconds']:.1f} s; "
          f"residual {residual_rms:.3e}; hard BC outer {boundary['outer']['maxAbsU']:.2e} "
          f"inner {boundary['inner']['maxAbsU']:.2e}")
    print(f"10-seed estimate {record['tenSeedCostEstimateSeconds'] / 60:.1f} min -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
