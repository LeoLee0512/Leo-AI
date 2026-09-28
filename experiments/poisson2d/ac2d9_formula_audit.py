"""AC2D-9 formula audit (Final Closure Audit issue 1): what does the number actually measure?

Recomputes, from the STORED formal predictions (no retraining, no claim set
reopened), the two readings of "max block RMS / global RMS" side by side on
D_dev, and re-derives the machine artifact's AC2D-9 value from its own stored
components.  Writes experiments/poisson2d/AC2D9_FORMULA_AUDIT.json.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from pinn.experiments.common import load_json, utc_now
from pinn.experiments2d import datasets2d as ds
from pinn.experiments2d import pinn_torch2d as pinn2d
from pinn.governance.poisson2d_contract import METRICS, THRESHOLD_SOURCES
from pinn.reference import analytic_poisson2d as reference
from pinn.validation.poisson2d import TILES_PER_AXIS

ATTEMPT = Path("experiments/poisson2d/runs/exp2d-poisson-calibration-r1")
OUT = Path("experiments/poisson2d/AC2D9_FORMULA_AUDIT.json")


def tile_of(point):
    return (min(int(point[0] * TILES_PER_AXIS), TILES_PER_AXIS - 1),
            min(int(point[1] * TILES_PER_AXIS), TILES_PER_AXIS - 1))


def main() -> int:
    identity = load_json(ATTEMPT / "identity.json")
    config = load_json(Path(identity["configPath"]))
    threads = int(config["optimizer"].get("threads", 1))
    dev = ds.points_of(load_json(ATTEMPT / "sets/dev.json"))
    exact = [reference.solution(x, y) for x, y in dev]

    per_seed = []
    for path in sorted(ATTEMPT.glob("runs/run-*.json")):
        run = load_json(path)
        model = pinn2d.model_from_weights(config, run["weights"], threads=threads)
        values = pinn2d.values(model, dev, threads=threads)
        errors = [a - b for a, b in zip(values, exact)]
        tiles: dict[tuple[int, int], list[float]] = {}
        for point, error in zip(dev, errors):
            tiles.setdefault(tile_of(point), []).append(error * error)
        counts = {key: len(v) for key, v in tiles.items()}
        tile_rms = {key: math.sqrt(math.fsum(v) / len(v)) for key, v in tiles.items()}
        max_block = max(tile_rms.values())
        global_error_rms = math.sqrt(math.fsum(e * e for e in errors) / len(errors))
        reference_rms = math.sqrt(math.fsum(e * e for e in exact) / len(exact))
        per_seed.append({
            "run": path.name,
            "readingImplemented_maxBlockOverReferenceRms": max_block / reference_rms,
            "readingReviewer_maxBlockOverGlobalErrorRms": max_block / global_error_rms,
            "globalRelativeError_sameGrid": global_error_rms / reference_rms,
            "maxBlockRms": max_block, "globalErrorRms": global_error_rms, "referenceRms": reference_rms,
            "tileCount": len(tiles), "minTileSamples": min(counts.values()), "maxTileSamples": max(counts.values()),
        })

    reviewer = [s["readingReviewer_maxBlockOverGlobalErrorRms"] for s in per_seed]
    implemented = [s["readingImplemented_maxBlockOverReferenceRms"] for s in per_seed]
    global_same_grid = [s["globalRelativeError_sameGrid"] for s in per_seed]
    claim = load_json(ATTEMPT / "gate5b_external.json")
    artifact_check = []
    for entry in claim["perSeed"]:
        recomputed = entry["diagnostics"]["worstTile"]["rms"] / entry["diagnostics"]["referenceRmsPointwise"]
        artifact_check.append({"AC2D-9": entry["metrics"]["AC2D-9"], "recomputedFromStoredComponents": recomputed,
                               "identical": abs(entry["metrics"]["AC2D-9"] - recomputed) <= 1e-18,
                               "AC2D-1": entry["metrics"]["AC2D-1"],
                               "ratioAC2D9overAC2D1": entry["metrics"]["AC2D-9"] / entry["metrics"]["AC2D-1"]})

    document = {
        "purpose": "Final Closure Audit issue 1: identify what the machine value AC2D-9 measures",
        "auditedAt": utc_now(),
        "noRetraining": True, "claimSetReopened": False,
        "recomputationSet": "dev (never blind); the claim-set value is re-derived from its own stored components only",
        "preregisteredFormula": "8x8 分块的最大分块 RMS 误差 / 全域 u* 的 RMS  (EXPERIMENT2D_PREREGISTRATION_20260916.md line 82)",
        "contractFormula": METRICS["AC2D-9"][0],
        "contractGrid": METRICS["AC2D-9"][1],
        "thresholdSource": THRESHOLD_SOURCES["AC2D-9"],
        "implementationSymbols": "validator: tile_rms[worst_tile] / reference_rms_p, where reference_rms_p = sqrt(mean_grid u*^2) "
                                 "and tile_rms[j] = sqrt(mean_{B_j} (u_theta - u*)^2)",
        "invariant": {
            "statement": "with any block partition, max_j RMS_j(e) >= RMS_grid(e); therefore max_j RMS_j(e) / RMS_grid(e) >= 1, "
                         "but max_j RMS_j(e) / RMS_grid(u*) is a RELATIVE local error and is far below 1 for an accurate model",
            "reviewerReadingMin": min(reviewer), "reviewerReadingMax": max(reviewer),
            "reviewerReadingAlwaysAtLeastOne": all(v >= 1.0 for v in reviewer),
            "implementedReadingMin": min(implemented), "implementedReadingMax": max(implemented),
            "sameGridGlobalRelativeErrorMax": max(global_same_grid),
            "implementedDominatesSameGridGlobal": all(i >= g for i, g in zip(implemented, global_same_grid)),
        },
        "perSeedOnDev": per_seed,
        "claimArtifactSelfConsistency": artifact_check,
        "verdict": "CASE A -- preregistration, contract formula, validator implementation and machine artifact agree; "
                   "only the abbreviated label in the report's section 3.2 ('8x8 分块最大块 RMS / 全域 RMS') dropped the "
                   "'u*' from the denominator and invited a reading under which values below 1 are impossible",
    }
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: document["invariant"][k] for k in
                      ("reviewerReadingMin", "reviewerReadingMax", "implementedReadingMin", "implementedReadingMax",
                       "reviewerReadingAlwaysAtLeastOne", "implementedDominatesSameGridGlobal")}, indent=2))
    print("artifact self-consistency:", all(a["identical"] for a in artifact_check))
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
