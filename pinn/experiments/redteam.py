"""Tier-1 Red Team (one retrain per perturbation, D_dev only) for the Poisson 1D revised run.

Preregistered in ``EXPERIMENT3_PREREGISTRATION_20260916.md`` section 9 before any
run.  Baseline = the formal seed-0 run of the attempt under review.  Metrics on
D_dev / D_phys: e2 (relative L2), delta_q = |QoI-1' - QoI-1| / QoI-1 with
QoI-1 = int u on the GL256 phys nodes, residual max on D_dev.  Thresholds:
delta_q <= 1 % maintain; 1-5 % PARTIAL; > 5 % FAIL; P4 additionally: residual
max changing by more than one order of magnitude -> C_impl FAIL; P8: the
mapped-back QoI drift is judged against the same 1 % / 5 % lines for C_math.
Red Team can maintain or downgrade a dimension, never upgrade it.  P7 and P11
are registered NOT_APPLICABLE for this problem class with the reasons below.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping, Sequence

from pinn.reference import analytic_poisson as reference

from . import pinn_torch

MAINTAIN = 0.01
FAIL = 0.05

TIER1: list[dict[str, Any]] = [
    {"id": "P1", "dimension": "train", "change": "collocation resampled from the same pool (sampling seed 20261000+900)",
     "perturbation": {"resampleSeed": 20261000 + 900}, "expected": "result depends on the particular collocation draw"},
    {"id": "P4", "dimension": "impl", "change": "training in float32 (residual re-evaluated in float64)", "perturbation": {"dtype": "float32"},
     "expected": "ill-conditioned second derivatives"},
    {"id": "P6", "dimension": "train", "change": "10 % of the collocation points removed", "perturbation": {"dropFraction": 0.1},
     "expected": "dependence on individual points"},
    {"id": "P7", "dimension": "physics", "applicable": False,
     "reason": "Poisson 1D has no boundary layer; the Dirichlet data are enforced at the two exact endpoints, so the collocation density near the boundary does not enter the BC term (Red Team deliverable section 5)"},
    {"id": "P8", "dimension": "math", "change": "domain rescaled y = 2x (v(y) = u(y/2), f_L = pi^2/4 sin(pi y / 2)), results mapped back to [0,1]",
     "perturbation": {"domainScale": 2.0}, "expected": "scaling / unscaling error or ill-conditioning at one scale"},
    {"id": "P9", "dimension": "train", "change": "optimizer Adam -> L-BFGS (same function-evaluation budget)", "perturbation": {"optimizer": "LBFGS"},
     "expected": "multimodal loss landscape"},
    {"id": "P11", "dimension": "train", "applicable": False,
     "reason": "no sLocalizedError was observed; residual-adaptive local refinement targets the CFD problems (Red Team deliverable section 5)"},
    {"id": "P16", "dimension": "train", "change": "activation tanh -> sin", "perturbation": {"activation": "sin"}, "expected": "spectral-bias sensitivity"},
]


def qoi_integral(model, phys_nodes: Sequence[float], phys_weights: Sequence[float], **kw) -> float:
    fld = pinn_torch.fields(model, phys_nodes, **kw)
    return math.fsum(w * u for w, u in zip(phys_weights, fld["u"]))


def measure(model, dev_points: Sequence[float], phys_nodes: Sequence[float], phys_weights: Sequence[float], **kw) -> dict[str, float]:
    fld = pinn_torch.fields(model, dev_points, **kw)
    exact = [reference.solution(x) for x in dev_points]
    residuals = [abs(-uxx - reference.forcing(x)) for uxx, x in zip(fld["uxx"], dev_points)]
    return {"e2": pinn_torch.rel_l2(fld["u"], exact), "residualMax": max(residuals),
            "qoi1": qoi_integral(model, phys_nodes, phys_weights, **kw)}


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


def run_tier1(config: Mapping[str, Any], pool: Sequence[float], dev_points: Sequence[float], phys_nodes: Sequence[float],
              phys_weights: Sequence[float], baseline_run: Mapping[str, Any], log=print) -> dict[str, Any]:
    seeds = baseline_run["seeds"]
    base_model = pinn_torch.model_from_weights(config, baseline_run["weights"])
    base = measure(base_model, dev_points, phys_nodes, phys_weights)
    results = []
    for entry in TIER1:
        if entry.get("applicable", True) is False:
            results.append({"id": entry["id"], "dimension": entry["dimension"], "applicability": "NOT_APPLICABLE", "reason": entry["reason"]})
            continue
        pert = dict(entry["perturbation"])
        run = pinn_torch.train_run(config, pool, dev_points, seeds, collocation_count=int(config["sampling"]["collocationCount"]),
                                   log_every=1000, perturbation=pert)
        kw: dict[str, Any] = {}
        if "dtype" in pert:
            kw["dtype"] = pert["dtype"]
        if "domainScale" in pert:
            kw["domain_scale"] = pert["domainScale"]
        model = pinn_torch.model_from_weights(config, run["weights"], dtype=pert.get("dtype", "float64"), activation=pert.get("activation"),
                                              domain_length=float(pert.get("domainScale", 1.0)))
        measured = measure(model, dev_points, phys_nodes, phys_weights, **kw)
        if entry["id"] == "P4":       # residual re-evaluated in float64 from the float32 weights
            model64 = pinn_torch.model_from_weights(config, {k: v for k, v in run["weights"].items()}, dtype="float64")
            measured = {**measured, **{k: v for k, v in measure(model64, dev_points, phys_nodes, phys_weights).items() if k == "residualMax"}}
        v = verdict(entry, base, measured)
        results.append({"id": entry["id"], "dimension": entry["dimension"], "applicability": "APPLICABLE", "change": entry["change"],
                        "heldFixed": "everything else of the frozen config, same seed triplet", "expectedFailureMode": entry["expected"],
                        "baseline": base, "observed": measured, "completed": run["completed"], "nan": run["nanEncountered"],
                        "status": v["status"] if run["completed"] and not run["nanEncountered"] else "FAIL",
                        "deltaQ": v["deltaQ"], "notes": v["notes"] + ("" if run["completed"] else "; perturbed run did not complete")})
        log(f"  Tier-1 {entry['id']}: e2={measured['e2']:.2e} deltaQ={v['deltaQ']:.2e} -> {results[-1]['status']}")
    impacts: dict[str, str] = {}
    order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2}
    for r in results:
        if r.get("applicability") == "APPLICABLE":
            current = impacts.get(r["dimension"], "PASS")
            impacts[r["dimension"]] = r["status"] if order[r["status"]] > order[current] else current
    worst = {}
    for dim in impacts:
        candidates = [r for r in results if r.get("applicability") == "APPLICABLE" and r["dimension"] == dim]
        w = max(candidates, key=lambda r: r["deltaQ"])
        worst[dim] = f"{w['id']}: delta_q {w['deltaQ']:.3e}, e2 {w['observed']['e2']:.3e}"
    return {"tier": "Tier-1", "evaluationSet": "dev", "baselineSeeds": seeds, "baseline": base, "thresholds": {"maintain": MAINTAIN, "fail": FAIL},
            "results": results, "dimensionImpact": impacts, "worstCase": worst,
            "passed": all(r["status"] == "PASS" for r in results if r.get("applicability") == "APPLICABLE")}
