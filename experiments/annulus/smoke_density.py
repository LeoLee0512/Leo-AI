"""Feasibility probes for the FROZEN architecture on the annulus (EXPLORATORY, D_dev only).

Not an architecture search: the network is the frozen square-2D one in every probe
(4 x 64 tanh, Adam 1e-3 -> 1e-5, batch 512, float64, deterministic). What varies is
the sampling DENSITY and the step budget, because the annulus has area 2.757 while
the unit square has area 1: the carried-over 1024 collocation points are 2.76 times
sparser per unit area than they were on the square.

    probe A   collocation 2824 (density-matched), 10000 steps
    probe B   collocation 2824 (density-matched), 20000 steps

Seeds are the smoke seeds; the claim pool does not exist yet and D_dev is the only
set read. claimEligibility <= C1, formalEvidence false.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from pinn.experiments_annulus import datasets_annulus as ds
from pinn.experiments_annulus import pinn_torch_annulus as pinn
from pinn.geometry import annulus as geo
from pinn.reference import analytic_annulus as ref

import sys as _sys

OUT = Path("experiments/annulus/smoke/SMOKE_DENSITY_PROBES{}.json".format(
    "_EXTRAPOLATION" if "--extrapolation" in _sys.argv else ""))

BASE = {
    "configId": "annulus-smoke-density",
    "network": {"hiddenLayers": 4, "width": 64, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "(R^2-s)(s-a^2)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": 10000, "batchSize": 512, "threads": 1},
    "lossWeights": {"pde": 1.0},
}
SEEDS = {"init": 20261200, "sample": 20261210, "batch": 20261220}
#: 1024 points on the unit square is a density of 1024 per unit area; the annulus area
#: is pi (1 - a^2) = 2.7567, so the density-matched count is round(1024 * 2.7567) = 2823.
DENSITY_MATCHED = round(1024 * geo.area())


def probe(label: str, collocation: int, steps: int, pool, dev) -> dict:
    config = json.loads(json.dumps(BASE))
    config["optimizer"]["steps"] = steps
    started = time.perf_counter()
    run = pinn.train_run(config, pool, dev, SEEDS, collocation_count=collocation, log_every=2000)
    model = pinn.model_from_weights(config, run["weights"])
    fields = pinn.fields(model, dev)
    residuals = [-(xx + yy) - ref.forcing(x, y)
                 for xx, yy, (x, y) in zip(fields["uxx"], fields["uyy"], dev)]
    record = {"probe": label, "collocationCount": collocation, "steps": steps,
              "devRelL2": run["devRelL2"],
              "normalizedResidualRms": (sum(r * r for r in residuals) / len(residuals)) ** 0.5 / ref.F_RMS,
              "seconds": run["elapsedSeconds"], "completed": run["completed"],
              "tenSeedMinutes": run["elapsedSeconds"] * 10 / 60.0}
    print(f"{label}: collocation {collocation}, {steps} steps -> dev rel L2 {run['devRelL2']:.3e}, "
          f"residual {record['normalizedResidualRms']:.3e}, {run['elapsedSeconds']:.0f} s "
          f"({record['tenSeedMinutes']:.1f} min for 10 seeds)")
    return record


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pool = ds.area_uniform_interior(4096, 20261230)
    dev = ds.area_uniform_interior(1024, 20261240)
    import sys

    if "--extrapolation" in sys.argv:
        records = [probe("C-densityMatched-40k", DENSITY_MATCHED, 40000, pool, dev),
                   probe("D-baselineCollocation-40k", 1024, 40000, pool, dev)]
    else:
        records = [probe("A-densityMatched-10k", DENSITY_MATCHED, 10000, pool, dev),
                   probe("B-densityMatched-20k", DENSITY_MATCHED, 20000, pool, dev)]
    OUT.write_text(json.dumps({
        "marking": "EXPLORATORY", "claimEligibility": "<= C1", "formalEvidence": False,
        "purpose": "feasibility of the FROZEN square-2D architecture on the annulus; sampling density and step budget "
                   "only, no architecture comparison",
        "annulusArea": geo.area(), "densityMatchedCollocation": DENSITY_MATCHED,
        "network": BASE["network"], "seeds": SEEDS, "poolSize": 4096, "devSize": 1024,
        "probes": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
