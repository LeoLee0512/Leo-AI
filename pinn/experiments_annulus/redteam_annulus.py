"""Tier-1 Red Team for the annular Poisson calibration (one retrain per perturbation, D_dev only).

Preregistered before any formal run. Baseline = the formal seed-0 run of the attempt
under review. Metrics on D_dev / D_phys: e2 (relative L2), delta_q = |QoI' - QoI| / QoI
with QoI = int_Omega u dA on the geometry-native quadrature (exact value
pi (1 - a^2)^3 / 6), residual max on D_dev. Thresholds (inherited, dimensionless):
delta_q <= 1 % maintain; 1-5 % PARTIAL; > 5 % FAIL; P4 additionally: a residual max
changing by more than one order of magnitude with the dtype -> C_impl FAIL. The Red
Team can maintain or downgrade a dimension, never upgrade it.

Applicability re-judged for the annulus, not copied:

* **P7 (boundary-neighbourhood densification)** stays APPLICABLE and now covers
  **both** boundary bands: the inner circle is a second, shorter boundary whose
  neighbourhood the collocation set must resolve, and its band has a smaller area
  than the outer one at the same width.
* **P11 (residual-adaptive local refinement)** is **APPLICABLE and mandatory**
  (protocol compilation: the Tier-1 set must run before C2; the earlier
  NOT_APPLICABLE ruling for the square was overturned on 2026-09-16). The
  refinement region is expressed in the geometry-native cells, not in Cartesian
  tiles.
* **P8 (domain rescaling)** rescales the annulus to radii (L a, L R) and the hard
  parameterization with it -- the harness defect the 1D Tier-1 run 1 hit and which
  must not repeat on a curved domain either.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.geometry import annulus as geo
from pinn.reference import analytic_annulus as reference

from . import pinn_torch_annulus as pinn
from . import parallel_annulus as parallel

MAINTAIN = 0.01
FAIL = 0.05
#: Width of the boundary band, in radius, on each component.
BOUNDARY_BAND = 0.1
#: P11: the residual quantile that defines the refinement region and the densification factor.
P11_QUANTILE = 0.95
P11_FACTOR = 2.0

TIER1: list[dict[str, Any]] = [
    {"id": "P1", "dimension": "train",
     "change": "collocation resampled from the same pool (sampling seed +900)",
     "perturbation": {"resampleSeed": 900}, "expected": "result depends on the particular collocation draw"},
    {"id": "P4", "dimension": "impl", "change": "training in float32 (residual re-evaluated in float64)",
     "perturbation": {"dtype": "float32"}, "expected": "ill-conditioned second derivatives"},
    {"id": "P6", "dimension": "train", "change": "10 % of the collocation points removed",
     "perturbation": {"dropFraction": 0.1}, "expected": "dependence on individual points"},
    {"id": "P7", "dimension": "train",
     "change": f"collocation redrawn with double density inside BOTH boundary bands of width {BOUNDARY_BAND}",
     "perturbation": {"boundaryBandBias": BOUNDARY_BAND},
     "expected": "under-resolved neighbourhood of either circle -- the inner band is the new one"},
    {"id": "P8", "dimension": "math",
     "change": "domain rescaled to radii (2a, 2R) (v(xi,eta) = u(xi/2,eta/2), f_L = f/4, hard factor rescaled), "
               "results mapped back",
     "perturbation": {"domainScale": 2.0}, "expected": "scaling / unscaling error or ill-conditioning at one scale"},
    {"id": "P9", "dimension": "train", "change": "optimizer Adam -> L-BFGS (same function-evaluation budget)",
     "perturbation": {"optimizer": "LBFGS"}, "expected": "multimodal loss landscape"},
    {"id": "P11", "dimension": "train",
     "change": f"residual-adaptive refinement: the collocation density is doubled inside the geometry-native cells "
               f"that hold a dev point with |residual| above its p{int(P11_QUANTILE * 100)}",
     "perturbation": {"residualAdaptive": True},
     "expected": "spatial error concentration that uniform sampling under-resolves"},
    {"id": "P16", "dimension": "train", "change": "activation tanh -> sin", "perturbation": {"activation": "sin"},
     "expected": "spectral-bias sensitivity"},
]


def boundary_band_indices(pool: Sequence[Sequence[float]], count: int, seed: int, band: float) -> dict[str, Any]:
    """Collocation indices with twice the natural density inside BOTH boundary bands."""

    import numpy as np

    rng = np.random.default_rng(int(seed))
    inside = [i for i, point in enumerate(pool)
              if min(geo.OUTER_RADIUS - geo.radius(point), geo.radius(point) - geo.INNER_RADIUS) < band]
    outside = [i for i in range(len(pool)) if i not in set(inside)]
    natural = len(inside) / len(pool)
    target = min(1.0, 2.0 * natural)
    n_in = min(len(inside), int(round(count * target)))
    n_out = min(len(outside), count - n_in)
    chosen = list(rng.choice(inside, size=n_in, replace=False)) + list(rng.choice(outside, size=n_out, replace=False))
    return {"indices": sorted(int(i) for i in chosen), "naturalShare": natural, "targetShare": target,
            "bandWidth": band, "components": ["outer", "inner"], "poolInBand": len(inside)}


def residual_adaptive_indices(model, pool: Sequence[Sequence[float]], dev_points: Sequence[Sequence[float]],
                              count: int, seed: int, radial_bins: int, angular_sectors: int,
                              *, threads: int = 1) -> dict[str, Any]:
    """P11: double the density inside the cells where the baseline's dev residual is largest.

    The region is defined on D_dev (never on the claim set) and expressed in the
    geometry-native partition, so no refinement region can straddle the hole.
    """

    import numpy as np

    fields = pinn.fields(model, dev_points, threads=threads)
    residuals = [abs(-(xx + yy) - reference.forcing(x, y))
                 for xx, yy, (x, y) in zip(fields["uxx"], fields["uyy"], dev_points)]
    threshold = float(np.quantile(np.asarray(residuals), P11_QUANTILE))
    region = {geo.cell_index(point, radial_bins, angular_sectors)
              for point, residual in zip(dev_points, residuals) if residual >= threshold}
    inside = [i for i, point in enumerate(pool)
              if geo.cell_index(point, radial_bins, angular_sectors) in region]
    outside = [i for i in range(len(pool)) if i not in set(inside)]
    natural = len(inside) / len(pool)
    target = min(1.0, P11_FACTOR * natural)
    rng = np.random.default_rng(int(seed))
    n_in = min(len(inside), int(round(count * target)))
    n_out = min(len(outside), count - n_in)
    chosen = list(rng.choice(inside, size=n_in, replace=False)) + list(rng.choice(outside, size=n_out, replace=False))
    return {"indices": sorted(int(i) for i in chosen), "residualThreshold": threshold,
            "residualMedian": float(np.median(residuals)), "residualMax": max(residuals),
            "cellsInRegion": len(region), "cellsTotal": radial_bins * angular_sectors,
            "naturalShare": natural, "targetShare": target, "densificationFactor": P11_FACTOR,
            "quantile": P11_QUANTILE, "evaluationSet": "dev"}


def qoi_integral(model, phys_points: Sequence[Sequence[float]], phys_weights: Sequence[float], **kw) -> float:
    u = pinn.values(model, phys_points, **kw)
    return math.fsum(w * value for w, value in zip(phys_weights, u))


def measure(model, dev_points: Sequence[Sequence[float]], phys_points: Sequence[Sequence[float]],
            phys_weights: Sequence[float], **kw) -> dict[str, float]:
    from pinn.experiments.pinn_torch import rel_l2

    fields = pinn.fields(model, dev_points, **kw)
    exact = [reference.solution(x, y) for x, y in dev_points]
    residuals = [abs(-(xx + yy) - reference.forcing(x, y))
                 for xx, yy, (x, y) in zip(fields["uxx"], fields["uyy"], dev_points)]
    return {"e2": rel_l2(fields["u"], exact), "residualMax": max(residuals),
            "qoi1": qoi_integral(model, phys_points, phys_weights, **kw)}


def verdict(entry: Mapping[str, Any], base: Mapping[str, float], perturbed: Mapping[str, float]) -> dict[str, Any]:
    drift = abs(perturbed["qoi1"] - base["qoi1"]) / abs(base["qoi1"])
    status = "PASS" if drift <= MAINTAIN else ("PARTIAL" if drift <= FAIL else "FAIL")
    notes = [f"delta_q = {drift:.3e} ({'<= 1%' if drift <= MAINTAIN else '1-5%' if drift <= FAIL else '> 5%'})"]
    if entry["id"] == "P4":
        ratio = perturbed["residualMax"] / base["residualMax"] if base["residualMax"] > 0 else math.inf
        notes.append(f"residual max ratio float32/float64 = {ratio:.2f}")
        if ratio > 10.0 or ratio < 0.1:
            status = "FAIL"
            notes.append("residual magnitude changed by more than one order of magnitude with dtype -> C_impl FAIL")
    return {"status": status, "deltaQ": drift, "notes": "; ".join(notes)}


def run_tier1(config: Mapping[str, Any], pool: Sequence[Sequence[float]], dev_points: Sequence[Sequence[float]],
              phys_points: Sequence[Sequence[float]], phys_weights: Sequence[float],
              baseline_run: Mapping[str, Any], radial_bins: int, angular_sectors: int, log=print,
              device: str = "cpu", workers: int = 1) -> dict[str, Any]:
    # ``device`` trains the eight perturbed models; every measurement below runs on the CPU,
    # exactly as in the formal attempt, so a Tier-1 verdict never depends on the accelerator.
    threads = int(config["optimizer"].get("threads", 1))
    seeds = baseline_run["seeds"]
    base_model = pinn.model_from_weights(config, baseline_run["weights"], threads=threads)
    base = measure(base_model, dev_points, phys_points, phys_weights, threads=threads)
    collocation_count = int(config["sampling"]["collocationCount"])
    results = []
    prepared = []
    for entry in TIER1:
        perturbation = dict(entry["perturbation"])
        detail: dict[str, Any] = {}
        if "boundaryBandBias" in perturbation:
            detail = boundary_band_indices(pool, collocation_count, seeds["sample"] + 900,
                                           float(perturbation["boundaryBandBias"]))
            perturbation = {"collocationIndices": detail["indices"],
                            "label": f"boundary bands {BOUNDARY_BAND} on both components"}
        elif perturbation.get("residualAdaptive"):
            detail = residual_adaptive_indices(base_model, pool, dev_points, collocation_count,
                                               seeds["sample"] + 1100, radial_bins, angular_sectors, threads=threads)
            perturbation = {"collocationIndices": detail["indices"],
                            "label": f"residual-adaptive densification x{P11_FACTOR} in {detail['cellsInRegion']} cells"}
        elif "resampleSeed" in perturbation:
            perturbation = {"resampleSeed": seeds["sample"] + int(perturbation["resampleSeed"])}
        prepared.append((entry, detail, perturbation))
    # The perturbed trainings are independent; parallel_annulus runs them side by side
    # with exactly the arguments the sequential loop used to pass.
    jobs = [{"config": config, "pool": pool, "dev_points": dev_points, "seeds": seeds,
             "collocation_count": collocation_count, "perturbation": perturbation, "device": device}
            for _, _, perturbation in prepared]
    trained = parallel.train_many(jobs, workers=workers, log=log)
    for (entry, detail, _), run in zip(prepared, trained):
        kw: dict[str, Any] = {"threads": threads}
        if entry["id"] == "P8":
            kw["domain_scale"] = 2.0
        model = pinn.model_from_weights(config, run["weights"], activation=entry["perturbation"].get("activation"),
                                        domain_scale=2.0 if entry["id"] == "P8" else 1.0, threads=threads)
        measured = measure(model, dev_points, phys_points, phys_weights, **kw)
        judged = verdict(entry, base, measured)
        results.append({"id": entry["id"], "dimension": entry["dimension"], "applicability": "APPLICABLE",
                        "change": entry["change"], "expectedFailureMode": entry["expected"],
                        "perturbation": entry["perturbation"], "perturbationDetail": detail,
                        "baseline": base, "perturbed": measured, "status": judged["status"],
                        "deltaQ": judged["deltaQ"], "notes": judged["notes"],
                        "trainingCompleted": run["completed"], "nan": run["nanEncountered"],
                        "elapsedSeconds": run["elapsedSeconds"]})
        log(f"  {entry['id']} ({entry['dimension']}): e2 {measured['e2']:.3e}, "
            f"delta_q {judged['deltaQ']:.3e} -> {judged['status']}")
    order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2}
    impact: dict[str, str] = {}
    worst: dict[str, str] = {}
    for result in results:
        dimension = result["dimension"]
        if dimension not in impact or order[result["status"]] > order[impact[dimension]]:
            impact[dimension] = result["status"]
            worst[dimension] = f"{result['id']}: {result['notes']}"
    for dimension in ("math", "impl", "train", "physics", "external", "repro"):
        impact.setdefault(dimension, "PASS")
        worst.setdefault(dimension, "no applicable Tier-1 perturbation targets this dimension")
    return {"tier": 1, "evaluationSet": "dev", "baselineSeeds": dict(seeds), "baseline": base,
            "trainingDevice": device, "evaluationDevice": "cpu",
            "geometryId": geo.GEOMETRY["geometryId"],
            "thresholds": {"maintain": MAINTAIN, "fail": FAIL,
                           "rule": "delta_q <= 1 % maintain; 1-5 % PARTIAL; > 5 % FAIL; only maintain or downgrade"},
            "results": results, "dimensionImpact": impact, "worstCase": worst,
            "coverage": {"executed": [r["id"] for r in results], "notApplicable": []},
            "passed": all(r["status"] == "PASS" for r in results)}
