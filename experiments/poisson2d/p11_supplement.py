"""Supplemental Tier-1 P11 run (residual-adaptive local refinement), Final Closure Audit issue 2.

Preregistered in ``experiments/poisson2d/P11_SUPPLEMENT_PREREGISTRATION_20260916.md``
and committed before this script runs.  The driver deliberately lives OUTSIDE the
code identity manifest (``experiments/`` is not a code-identity prefix), so the
perturbation retrains under exactly the code identity of the formal run; it only
calls the unmodified ``pinn.experiments2d`` modules.

    PYTHONPATH=. PYTHONIOENCODING=utf-8 <mamba python> -B experiments/poisson2d/p11_supplement.py

D_dev only; the claim set is never touched.  One retrain, no retries.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from pinn.experiments.common import ArtifactStore, code_hash_from_manifest, code_manifest, load_json, utc_now
from pinn.experiments2d import datasets2d as ds
from pinn.experiments2d import pinn_torch2d as pinn2d
from pinn.experiments2d import redteam2d
from pinn.governance.trust_loop import validate_trust_vector
from pinn.reference import analytic_poisson2d as reference

ATTEMPT = Path("experiments/poisson2d/runs/exp2d-poisson-calibration-r1")
TILES = 8
DENSIFICATION = 2.0
PERCENTILE = 0.95


def percentile(values, q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    low = int(math.floor(position))
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def tile_of(point) -> tuple[int, int]:
    return (min(int(point[0] * TILES), TILES - 1), min(int(point[1] * TILES), TILES - 1))


def residuals(model, points, threads: int):
    field = pinn2d.fields(model, points, threads=threads)
    return [abs(-(xx + yy) - reference.forcing(x, y)) for xx, yy, (x, y) in zip(field["uxx"], field["uyy"], points)]


def main() -> int:
    identity = load_json(ATTEMPT / "identity.json")
    config = load_json(Path(identity["configPath"]))
    threads = int(config["optimizer"].get("threads", 1))
    current_code_hash = code_hash_from_manifest(code_manifest(Path(".").resolve(), [identity["configPath"]]))
    if current_code_hash != identity["codeHash"]:
        raise SystemExit(f"code identity moved ({current_code_hash[:12]} != {identity['codeHash'][:12]}); "
                         "the supplemental perturbation must run under the formal run's code identity")
    pool = ds.points_of(load_json(ATTEMPT / "sets/train.json"))
    dev = ds.points_of(load_json(ATTEMPT / "sets/dev.json"))
    phys_points, phys_weights = ds.gauss_legendre_square(config["sets"]["physOrder"])
    baseline_run = load_json(ATTEMPT / "runs/run-00.json")
    baseline_model = pinn2d.model_from_weights(config, baseline_run["weights"], threads=threads)

    # 1. residual statistics on the independent dense set (Red Team deliverable section 1 header)
    dev_residuals = residuals(baseline_model, dev, threads)
    tau = percentile(dev_residuals, PERCENTILE)
    hot_points = [p for p, r in zip(dev, dev_residuals) if r >= tau]
    hot_tiles = {tile_of(p) for p in hot_points}
    # 2. region A and the densified collocation draw (total budget unchanged)
    import numpy as np

    inside = [i for i, p in enumerate(pool) if tile_of(p) in hot_tiles]
    outside = [i for i in range(len(pool)) if tile_of(pool[i]) not in hot_tiles]
    count = int(config["sampling"]["collocationCount"])
    natural = len(inside) / len(pool)
    target_inside = min(len(inside), int(round(count * min(1.0, DENSIFICATION * natural))))
    target_outside = min(len(outside), count - target_inside)
    rng = np.random.default_rng(int(baseline_run["seeds"]["sample"]) + 1100)
    chosen = sorted(int(i) for i in list(rng.choice(inside, size=target_inside, replace=False))
                    + list(rng.choice(outside, size=target_outside, replace=False)))
    print(f"[P11] dev residual median {percentile(dev_residuals, 0.5):.3e}, p95 tau {tau:.3e}, "
          f"max {max(dev_residuals):.3e}; region A = {len(hot_tiles)}/{TILES * TILES} tiles, "
          f"natural pool share {natural:.3f} -> densified share {target_inside / count:.3f}", flush=True)

    # 3. one retrain, everything else frozen
    run = pinn2d.train_run(config, pool, dev, baseline_run["seeds"], collocation_count=count,
                           perturbation={"collocationIndices": chosen, "label": "P11 residual-adaptive refinement"})
    model = pinn2d.model_from_weights(config, run["weights"], threads=threads)

    # 4. metrics
    base = redteam2d.measure(baseline_model, dev, phys_points, phys_weights, threads=threads)
    pert = redteam2d.measure(model, dev, phys_points, phys_weights, threads=threads)
    entry = {"id": "P11", "dimension": "train"}
    judged = redteam2d.verdict(entry, base, pert)
    after_residuals = residuals(model, dev, threads)
    in_region = [r for p, r in zip(dev, after_residuals) if tile_of(p) in hot_tiles]
    in_region_before = [r for p, r in zip(dev, dev_residuals) if tile_of(p) in hot_tiles]
    exact = [reference.solution(x, y) for x, y in dev]
    reference_rms = math.sqrt(math.fsum(v * v for v in exact) / len(exact))

    def worst_tile_relative(values):
        tiles: dict[tuple[int, int], list[float]] = {}
        for p, u, e in zip(dev, values, exact):
            tiles.setdefault(tile_of(p), []).append((u - e) ** 2)
        return max(math.sqrt(math.fsum(v) / len(v)) for v in tiles.values()) / reference_rms

    document = {
        "tier": 1, "perturbation": "P11", "supplemental": True, "evaluationSet": "dev", "claimSetTouched": False,
        "preregistration": "experiments/poisson2d/P11_SUPPLEMENT_PREREGISTRATION_20260916.md",
        "reasonForSupplement": ("the Tier-1 set of the protocol compilation lists P11 as mandatory before C2 and the "
                               "earlier NOT_APPLICABLE verdict had no formal protocol basis (Final Closure Audit issue 2)"),
        "codeHash": current_code_hash, "baselineSeeds": dict(baseline_run["seeds"]),
        "residualStatistics": {"set": "dev", "n": len(dev), "median": percentile(dev_residuals, 0.5), "p95": tau,
                               "max": max(dev_residuals),
                               "argmaxPoint": list(dev[max(range(len(dev)), key=lambda i: dev_residuals[i])])},
        "region": {"definition": "union of the preregistered 8x8 tiles containing at least one dev point with |R| >= p95",
                   "tiles": sorted(f"{i},{j}" for i, j in hot_tiles), "tileCount": len(hot_tiles),
                   "naturalPoolShare": natural, "densificationFactor": DENSIFICATION,
                   "collocationInsideRegion": target_inside, "collocationTotal": count,
                   "densifiedShare": target_inside / count},
        "baseline": base, "perturbed": pert,
        "localResidual": {"p95InRegionBefore": percentile(in_region_before, PERCENTILE),
                          "p95InRegionAfter": percentile(in_region, PERCENTILE),
                          "maxInRegionBefore": max(in_region_before), "maxInRegionAfter": max(in_region),
                          "devP95After": percentile(after_residuals, PERCENTILE), "devMaxAfter": max(after_residuals)},
        "localizedErrorAfter": {"worstTileRelativeRms": worst_tile_relative(
            pinn2d.values(model, dev, threads=threads)), "note": "AC2D-9 form evaluated on D_dev, diagnostics only"},
        "thresholds": {"maintain": redteam2d.MAINTAIN, "fail": redteam2d.FAIL,
                       "rule": "delta_q <= 1 % maintain; 1-5 % PARTIAL; > 5 % FAIL; only maintain or downgrade; "
                               "crossing the line additionally routes to the localized-error triage with C_train PARTIAL"},
        "status": judged["status"], "deltaQ": judged["deltaQ"], "notes": judged["notes"],
        "trainingCompleted": run["completed"], "nan": run["nanEncountered"], "elapsedSeconds": run["elapsedSeconds"],
        "recordedAt": utc_now(),
    }
    store = ArtifactStore(ATTEMPT, producer="experiments/poisson2d/p11_supplement.py (Claude, captain)")
    ref = store.write_json("tier1_p11_supplement.json", document, role="RED_TEAM_REPORT", parents=["runs/run-00.json"])
    print(f"[P11] status {judged['status']}, delta_q {judged['deltaQ']:.3e}, e2 {pert['e2']:.3e} "
          f"(baseline {base['e2']:.3e}); region p95 {document['localResidual']['p95InRegionBefore']:.3e} -> "
          f"{document['localResidual']['p95InRegionAfter']:.3e}", flush=True)

    # 5. supplemental TrustVector + ClaimGateDecision on top of the G6 vector
    prior = load_json(ATTEMPT / "trust_vector_g6.json")
    pdef = load_json(ATTEMPT / "problem_definition.json")
    order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2, "BLOCKED": 3, "NOT_CHECKED": 4}
    dims = copy.deepcopy(prior["dimensions"])
    train = dims["train"]
    train["perturbationsRun"] = sorted(set(train.get("perturbationsRun", [])) | {"P11"})
    if order[judged["status"]] > order[train["status"]]:
        train["status"] = judged["status"]
        train["notes"] = (train.get("notes", "") + f"; supplemental Tier-1 P11 downgraded to {judged['status']}: "
                          f"{judged['notes']}").strip("; ")
    else:
        train["notes"] = (train.get("notes", "") + f"; supplemental Tier-1 P11 maintained ({judged['notes']})").strip("; ")
    train["evidencePointers"] = train.get("evidencePointers", []) + [ref]
    train["judgedAt"] = utc_now()
    vector = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"tv-{ATTEMPT.name}-g6-p11", "problemId": pdef["problemId"],
              "revision": pdef["revision"], "specHash": pdef["specHash"], "supersedesRecordId": prior["recordId"],
              "dimensions": dims}
    errors = validate_trust_vector(vector, pdef)
    if errors:
        raise SystemExit(f"supplemental TrustVector invalid: {errors}")
    store.write_canonical("trust_vector_g6_p11.json", vector, role="TRUST_VECTOR", parents=[ref["artifactId"]])
    print("[P11] trust vector:", {k: v["status"] for k, v in dims.items()})
    print("[P11] wrote trust_vector_g6_p11.json; the ClaimGateDecision is produced by the runner's decision path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
