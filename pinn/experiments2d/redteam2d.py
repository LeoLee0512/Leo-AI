"""Tier-1 Red Team for the 2D Poisson calibration (one retrain per perturbation, D_dev only).

Preregistered in ``experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md``
section 9 before any formal run.  Baseline = the formal seed-0 run of the attempt
under review.  Metrics on D_dev / D_phys: e2 (relative L2), delta_q =
|QoI' - QoI| / QoI with QoI = int int u on the D_phys tensor grid (exact value
4/pi^2), residual max on D_dev.  Thresholds (1D inherited, dimensionless):
delta_q <= 1 % maintain; 1-5 % PARTIAL; > 5 % FAIL; P4 additionally: residual max
changing by more than one order of magnitude -> C_impl FAIL.  Red Team can
maintain or downgrade a dimension, never upgrade it.

Applicability re-judged for 2D (PART 18), not copied from the 1D table:

* **P7 (boundary-neighbourhood densification) is APPLICABLE in 2D**, unlike in 1D.
  In 1D the boundary is two points that are evaluated exactly; in 2D the boundary
  is a curve and the collocation set has to resolve a two-dimensional band next to
  it, so the density there is a real degree of freedom of the method.
* **P11 (residual-adaptive local refinement) stays NOT_APPLICABLE**: the
  manufactured solution is analytic with no localized feature, and the localized
  error structure is *measured* by the acceptance criterion AC2D-9 rather than
  probed by an adaptive-refinement perturbation.
* **P8 (domain rescaling) rescales the hard parameterization with the domain**
  (u = xi(L - xi) eta(L - eta) N), which is exactly the harness defect the 1D
  Tier-1 run 1 hit and which must not repeat.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.reference import analytic_poisson2d as reference

from . import pinn_torch2d as pinn2d

MAINTAIN = 0.01
FAIL = 0.05
BOUNDARY_BAND = 0.1

TIER1: list[dict[str, Any]] = [
    {"id": "P1", "dimension": "train", "change": "collocation resampled from the same pool (sampling seed 20261000+900)",
     "perturbation": {"resampleSeed": 20261000 + 900}, "expected": "result depends on the particular collocation draw"},
    {"id": "P4", "dimension": "impl", "change": "training in float32 (residual re-evaluated in float64)",
     "perturbation": {"dtype": "float32"}, "expected": "ill-conditioned second derivatives in two dimensions"},
    {"id": "P6", "dimension": "train", "change": "10 % of the collocation points removed", "perturbation": {"dropFraction": 0.1},
     "expected": "dependence on individual points"},
    {"id": "P7", "dimension": "train", "change": f"collocation redrawn with double density inside the boundary band of width {BOUNDARY_BAND}",
     "perturbation": {"boundaryBandBias": BOUNDARY_BAND}, "expected": "under-resolved boundary neighbourhood in 2D"},
    {"id": "P8", "dimension": "math", "change": "domain rescaled to (0,2)^2 (v(xi,eta) = u(xi/2,eta/2), f_L = f/4, hard parameterization rescaled), results mapped back",
     "perturbation": {"domainScale": 2.0}, "expected": "scaling / unscaling error or ill-conditioning at one scale"},
    {"id": "P9", "dimension": "train", "change": "optimizer Adam -> L-BFGS (same function-evaluation budget)",
     "perturbation": {"optimizer": "LBFGS"}, "expected": "multimodal loss landscape"},
    {"id": "P11", "dimension": "train", "applicable": False,
     "reason": "the manufactured solution is analytic with no localized feature; spatial error concentration is measured by the "
               "acceptance criterion AC2D-9 instead of being probed by residual-adaptive refinement (2D applicability judgement, "
               "preregistered; not copied from the 1D table)"},
    {"id": "P16", "dimension": "train", "change": "activation tanh -> sin", "perturbation": {"activation": "sin"},
     "expected": "spectral-bias sensitivity"},
]


def boundary_band_indices(pool: Sequence[Sequence[float]], count: int, seed: int, band: float) -> list[int]:
    """Collocation indices with twice the natural density inside the boundary band."""

    import numpy as np

    rng = np.random.default_rng(int(seed))
    inside = [i for i, (x, y) in enumerate(pool) if min(x, 1.0 - x, y, 1.0 - y) < band]
    outside = [i for i in range(len(pool)) if i not in set(inside)]
    natural = len(inside) / len(pool)
    target = min(1.0, 2.0 * natural)
    n_in = min(len(inside), int(round(count * target)))
    n_out = min(len(outside), count - n_in)
    chosen = list(rng.choice(inside, size=n_in, replace=False)) + list(rng.choice(outside, size=n_out, replace=False))
    return sorted(int(i) for i in chosen)


def qoi_integral(model, phys_points: Sequence[Sequence[float]], phys_weights: Sequence[float], **kw) -> float:
    u = pinn2d.values(model, phys_points, **kw)
    return math.fsum(w * value for w, value in zip(phys_weights, u))


def measure(model, dev_points: Sequence[Sequence[float]], phys_points: Sequence[Sequence[float]],
            phys_weights: Sequence[float], **kw) -> dict[str, float]:
    from pinn.experiments.pinn_torch import rel_l2

    fld = pinn2d.fields(model, dev_points, **kw)
    exact = [reference.solution(x, y) for x, y in dev_points]
    residuals = [abs(-(xx + yy) - reference.forcing(x, y)) for xx, yy, (x, y) in zip(fld["uxx"], fld["uyy"], dev_points)]
    return {"e2": rel_l2(fld["u"], exact), "residualMax": max(residuals),
            "qoi1": qoi_integral(model, phys_points, phys_weights, **kw)}


def verdict(entry: Mapping[str, Any], base: Mapping[str, float], pert: Mapping[str, float]) -> dict[str, Any]:
    drift = abs(pert["qoi1"] - base["qoi1"]) / abs(base["qoi1"])
    status = "PASS" if drift <= MAINTAIN else ("PARTIAL" if drift <= FAIL else "FAIL")
    notes = [f"delta_q = {drift:.3e} ({'<= 1%' if drift <= MAINTAIN else '1-5%' if drift <= FAIL else '> 5%'})"]
    if entry["id"] == "P4":
        ratio = pert["residualMax"] / base["residualMax"] if base["residualMax"] > 0 else math.inf
        notes.append(f"residual max ratio float32/float64 = {ratio:.2f}")
        if ratio > 10.0 or ratio < 0.1:
            status = "FAIL"
            notes.append("residual magnitude changed by more than one order of magnitude with dtype -> C_impl FAIL")
    return {"status": status, "deltaQ": drift, "notes": "; ".join(notes)}


def run_tier1(config: Mapping[str, Any], pool: Sequence[Sequence[float]], dev_points: Sequence[Sequence[float]],
              phys_points: Sequence[Sequence[float]], phys_weights: Sequence[float], baseline_run: Mapping[str, Any],
              log=print, workers: int = 1) -> dict[str, Any]:
    from .parallel2d import train_many

    threads = int(config["optimizer"].get("threads", 1))
    seeds = baseline_run["seeds"]
    base_model = pinn2d.model_from_weights(config, baseline_run["weights"], threads=threads)
    base = measure(base_model, dev_points, phys_points, phys_weights, threads=threads)
    collocation_count = int(config["sampling"]["collocationCount"])
    # Every applicable perturbation is one independent retrain; they are trained first (side by side
    # when workers > 1, bit-identical to one after another) and then measured in the fixed order.
    jobs = []
    for entry in TIER1:
        if entry.get("applicable", True) is False:
            continue
        perturbation = dict(entry["perturbation"])
        if "boundaryBandBias" in perturbation:
            perturbation = {"collocationIndices": boundary_band_indices(pool, collocation_count, seeds["sample"] + 900,
                                                                        float(perturbation["boundaryBandBias"])),
                            "label": f"boundary band {BOUNDARY_BAND}"}
        jobs.append({"config": config, "pool": pool, "dev_points": dev_points, "seeds": seeds,
                     "collocation_count": collocation_count, "perturbation": perturbation})
    trained = iter(train_many(jobs, workers=workers, log=log))
    results = []
    for entry in TIER1:
        if entry.get("applicable", True) is False:
            results.append({"id": entry["id"], "dimension": entry["dimension"], "applicability": "NOT_APPLICABLE", "reason": entry["reason"]})
            log(f"  {entry['id']}: NOT_APPLICABLE")
            continue
        run = next(trained)
        kw: dict[str, Any] = {"threads": threads}
        if entry["id"] == "P8":
            kw["domain_scale"] = 2.0
        model = pinn2d.model_from_weights(config, run["weights"], activation=entry["perturbation"].get("activation"),
                                          domain_length=2.0 if entry["id"] == "P8" else 1.0, threads=threads)
        measured = measure(model, dev_points, phys_points, phys_weights, **kw)
        judged = verdict(entry, base, measured)
        results.append({"id": entry["id"], "dimension": entry["dimension"], "applicability": "APPLICABLE", "change": entry["change"],
                        "expectedFailureMode": entry["expected"], "perturbation": entry["perturbation"], "baseline": base,
                        "perturbed": measured, "status": judged["status"], "deltaQ": judged["deltaQ"], "notes": judged["notes"],
                        "trainingCompleted": run["completed"], "nan": run["nanEncountered"], "elapsedSeconds": run["elapsedSeconds"]})
        log(f"  {entry['id']} ({entry['dimension']}): e2 {measured['e2']:.3e}, delta_q {judged['deltaQ']:.3e} -> {judged['status']}")
    order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2}
    impact: dict[str, str] = {}
    worst: dict[str, str] = {}
    for result in results:
        if result.get("applicability") != "APPLICABLE":
            continue
        dim = result["dimension"]
        if dim not in impact or order[result["status"]] > order[impact[dim]]:
            impact[dim] = result["status"]
            worst[dim] = f"{result['id']}: {result['notes']}"
    for dim in ("math", "impl", "train", "physics", "external", "repro"):
        impact.setdefault(dim, "PASS")
        worst.setdefault(dim, "no applicable Tier-1 perturbation targets this dimension")
    return {"tier": 1, "evaluationSet": "dev", "baselineSeeds": dict(seeds), "baseline": base, "thresholds":
            {"maintain": MAINTAIN, "fail": FAIL, "rule": "delta_q <= 1 % maintain; 1-5 % PARTIAL; > 5 % FAIL; only maintain or downgrade"},
            "results": results, "dimensionImpact": impact, "worstCase": worst,
            "passed": all(r["status"] == "PASS" for r in results if r.get("applicability") == "APPLICABLE")}
