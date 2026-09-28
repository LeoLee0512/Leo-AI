"""Honest device benchmark: is CUDA actually faster for THIS run? (EXPLORATORY, D_dev only)

Nothing here is evidence. The network is tiny (4 x 64 tanh, batch 512), the
Constitution fixes float64, and this GPU (RTX 4060 Laptop, cc 8.9) has an FP64
throughput of 1/64 of its FP32. A GPU is therefore not obviously the faster device
for this workload, and assuming it is would be exactly the kind of unchecked premise
this project does not allow. So the same short training is run on both devices and
the per-step cost is measured.

    marking            EXPLORATORY
    formalEvidence     false
    sets read          D_dev only (D_claim is sealed and is not touched)
    seeds              20261200 / 20261210 / 20261220 -- the smoke bases, disjoint from
                       the formal bases 20261400 / 20261500 / 20261600

It also reports the CPU-vs-CUDA agreement of the trained weights after an identical
number of steps: both devices run float64 with deterministic algorithms, so the two
results should be close, and any large divergence is itself a finding worth having
before a ten-seed run is started.

    PYTHONPATH=. PYTHONIOENCODING=utf-8 <mamba python> -u -B experiments/annulus/bench_device_annulus.py --steps 2000
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

from pinn.experiments_annulus import datasets_annulus as ds
from pinn.experiments_annulus import pinn_torch_annulus as pinn

OUT_TEMPLATE = "experiments/annulus/smoke/DEVICE_BENCHMARK_{label}.json"

#: the frozen architecture and optimizer, copied from the frozen config; only the step
#: count is cut down, because the question here is seconds per step, not accuracy.
BASE = {
    "configId": "annulus-device-benchmark",
    "network": {"hiddenLayers": 4, "width": 64, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "(R^2-s)(s-a^2)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": 2000, "batchSize": 512, "threads": 1},
    "lossWeights": {"pde": 1.0},
}
SEEDS = {"init": 20261200, "sample": 20261210, "batch": 20261220}
FORMAL_STEPS = 120000
FORMAL_SEEDS = 10


def probe(device: str, steps: int, pool, dev) -> dict:
    config = json.loads(json.dumps(BASE))
    config["optimizer"]["steps"] = steps
    started = time.perf_counter()
    run = pinn.train_run(config, pool, dev, SEEDS, collocation_count=1024, log_every=max(steps, 1), device=device)
    wall = time.perf_counter() - started
    per_step = run["elapsedSeconds"] / max(run["stepsCompleted"], 1)
    record = {
        "device": device,
        "resolvedDevice": run["determinism"]["device"],
        "deviceName": run["determinism"]["deviceName"],
        "cublasWorkspaceConfig": run["determinism"]["cublasWorkspaceConfig"],
        "dtype": run["determinism"]["dtype"],
        "steps": steps,
        "stepsCompleted": run["stepsCompleted"],
        "completed": run["completed"],
        "trainSeconds": run["elapsedSeconds"],
        "wallSecondsIncludingSetup": wall,
        "secondsPerStep": per_step,
        "devRelL2": run["devRelL2"],
        "projectedSecondsPerSeedAtFormalBudget": per_step * FORMAL_STEPS,
        "projectedHoursForTenSeeds": per_step * FORMAL_STEPS * FORMAL_SEEDS / 3600.0,
    }
    print(f"{device:>6}: {run['stepsCompleted']} steps in {run['elapsedSeconds']:.1f} s "
          f"= {per_step * 1000:.3f} ms/step -> {record['projectedHoursForTenSeeds']:.2f} h for "
          f"{FORMAL_SEEDS} seeds x {FORMAL_STEPS} steps; devRelL2 {run['devRelL2']:.6e}")
    return record, run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--devices", default="cpu,cuda")
    parser.add_argument("--label", default="default",
                        help="each invocation writes its own file: a same-process comparison and a "
                             "fresh-process-per-device comparison are different measurements and are kept apart")
    args = parser.parse_args()

    out = Path(OUT_TEMPLATE.format(label=args.label))
    out.parent.mkdir(parents=True, exist_ok=True)
    pool = ds.area_uniform_interior(2048, 20261230)
    dev = ds.area_uniform_interior(1024, 20261240)

    records: list[dict] = []
    runs: dict[str, dict] = {}
    for device in [d.strip() for d in args.devices.split(",") if d.strip()]:
        record, run = probe(device, args.steps, pool, dev)
        records.append(record)
        runs[device] = run

    agreement = None
    if "cpu" in runs and "cuda" in runs:
        a, b = runs["cpu"]["weights"], runs["cuda"]["weights"]
        def flat(value, out=None):
            out = [] if out is None else out
            if isinstance(value, list):
                for item in value:
                    flat(item, out)
            else:
                out.append(float(value))
            return out

        worst = 0.0
        for name in a:
            for x, y in zip(flat(a[name]), flat(b[name])):
                worst = max(worst, abs(x - y))
        agreement = {
            "maxAbsWeightDifference": worst,
            "devRelL2Cpu": runs["cpu"]["devRelL2"],
            "devRelL2Cuda": runs["cuda"]["devRelL2"],
            "devRelL2AbsDifference": abs(runs["cpu"]["devRelL2"] - runs["cuda"]["devRelL2"]),
            "note": "float64 with deterministic algorithms on both devices; the difference is the "
                    "accumulated effect of a different reduction order, not of a different method",
        }
        print(f"agreement after {args.steps} steps: max |dW| = {worst:.3e}, "
              f"devRelL2 {runs['cpu']['devRelL2']:.6e} (cpu) vs {runs['cuda']['devRelL2']:.6e} (cuda), "
              f"|diff| = {agreement['devRelL2AbsDifference']:.3e}")
    speedup = None
    if len(records) == 2:
        speedup = records[0]["secondsPerStep"] / records[1]["secondsPerStep"]
        print(f"{records[0]['device']} / {records[1]['device']} per-step ratio = {speedup:.3f}x "
              f"({'second device faster' if speedup > 1 else 'second device SLOWER'})")

    out.write_text(json.dumps({
        "marking": "EXPLORATORY", "claimEligibility": "<= C1", "formalEvidence": False,
        "label": args.label, "devicesInThisProcess": args.devices,
        "purpose": "measure the per-step cost of the frozen annulus training on cpu vs cuda before a ten-seed "
                   "formal attempt is started; no threshold, no method value and no acceptance decision depends "
                   "on this file",
        "setsRead": ["D_dev (exploratory instance)"],
        "seeds": SEEDS,
        "network": BASE["network"], "optimizer": BASE["optimizer"],
        "formalBudget": {"steps": FORMAL_STEPS, "seeds": FORMAL_SEEDS},
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "probes": records, "cpuVsCudaAgreement": agreement,
        "perStepRatioFirstOverSecond": speedup,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
