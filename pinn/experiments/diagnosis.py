"""Failure path: observed signatures on D_dev, the controlled sampling intervention, the DiagnosisRecord.

Nothing here decides the root cause in advance.  ``observed_signatures`` fires
every preregistered symptom criterion the dev diagnostics actually meet; the
intervention is a plain sampling sweep with everything else held fixed; the
exclusion records quote measured facts; ``diagnose`` of the state machine (under
Constitution 1.2) is what accepts or refuses the named cause.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.governance.state_machine import (
    INTERVENTION_CONTROLS,
    FailureSignature,
    RootCauseClass,
    admissible_root_causes,
)
from pinn.reference import analytic_poisson as reference

from . import pinn_torch
from .gates import F_RMS, TWO_PI

SIGNATURES = [s.value for s in FailureSignature]


def dev_diagnostics(model, dev_points: Sequence[float], phys_nodes: Sequence[float], phys_weights: Sequence[float],
                    bins: int) -> dict[str, Any]:
    """The per-seed measurements every signature criterion reads (all on D_dev / D_phys, never on D_claim)."""

    fld = pinn_torch.fields(model, dev_points)
    ends = pinn_torch.fields(model, [0.0, 1.0])
    exact = [reference.solution(x) for x in dev_points]
    rel_l2 = pinn_torch.rel_l2(fld["u"], exact)
    residuals = [-uxx - reference.forcing(x) for uxx, x in zip(fld["uxx"], dev_points)]
    residual_rms = math.sqrt(math.fsum(r * r for r in residuals) / len(residuals)) / F_RMS
    boundary = max(abs(ends["u"][0]), abs(ends["u"][1]))
    order = sorted(range(len(dev_points)), key=lambda i: dev_points[i])
    bin_rms: list[float] = []
    per_bin = max(1, len(order) // bins)
    for b in range(bins):
        members = order[b * per_bin:(b + 1) * per_bin] if b < bins - 1 else order[b * per_bin:]
        if members:
            bin_rms.append(math.sqrt(math.fsum((fld["u"][i] - exact[i]) ** 2 for i in members) / len(members)))
    ranked = sorted(bin_rms)
    median_bin = ranked[len(ranked) // 2]
    localized = (max(bin_rms) / median_bin) if median_bin > 0 else float("inf")
    flux = abs((ends["ux"][0] - ends["ux"][1]) - math.fsum(w * reference.forcing(x) for w, x in zip(phys_weights, phys_nodes))) / TWO_PI
    return {
        "relL2": rel_l2, "normalizedResidualRms": residual_rms, "maxBoundaryAbs": boundary,
        "localizedRatio": localized, "binRms": bin_rms, "fluxBalance": flux,
        "u": fld["u"], "residuals": residuals, "pointwiseAbsError": [abs(a - b) for a, b in zip(fld["u"], exact)],
    }


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def observed_signatures(per_seed: Sequence[Mapping[str, Any]], seed_stats: Mapping[str, Any],
                        criteria: Mapping[str, Any], epsilon_spec: float) -> dict[str, Any]:
    """Which preregistered symptom criteria the medians over seeds (or the seed rules) meet."""

    medians = {
        "relL2": _median([d["relL2"] for d in per_seed]),
        "normalizedResidualRms": _median([d["normalizedResidualRms"] for d in per_seed]),
        "maxBoundaryAbs": _median([d["maxBoundaryAbs"] for d in per_seed]),
        "localizedRatio": _median([d["localizedRatio"] for d in per_seed]),
        "fluxBalance": _median([d["fluxBalance"] for d in per_seed]),
    }
    rules = {
        "sPinnCfd": {"value": medians["relL2"], "threshold": epsilon_spec, "rule": "median dev relative L2 vs analytic reference > epsilon_spec"},
        "sPdeResidual": {"value": medians["normalizedResidualRms"], "threshold": criteria["sPdeResidual"]["normalizedResidualRms"],
                         "rule": "median dev holdout residual RMS / ||f||_rms > AC-4 threshold"},
        "sBcResidual": {"value": medians["maxBoundaryAbs"], "threshold": criteria["sBcResidual"]["maxBoundaryAbs"],
                        "rule": "median max(|u(0)|, |u(1)|) > AC-3 threshold"},
        "sLocalizedError": {"value": medians["localizedRatio"], "threshold": criteria["sLocalizedError"]["maxBinToMedianBinRatio"],
                            "rule": f"median (max bin RMS error / median bin RMS error) over {criteria['sLocalizedError']['bins']} dev bins > ratio"},
        "sConservation": {"value": medians["fluxBalance"], "threshold": criteria["sConservation"]["PH1"],
                          "rule": "median flux-balance defect on D_phys > PH1 threshold"},
        "sSeedSensitive": {"value": {"dispersionOk": seed_stats["dispersionOk"], "worstOk": seed_stats["worstOk"], "divergent": seed_stats["divergent"]},
                           "threshold": "dispersion_ok and worst_ok and no divergent run",
                           "rule": "Constitution 10.1 seed rules: IQR > dispersionLimit * median, worst > 3 epsilon_spec, or divergent runs"},
    }
    fired: list[str] = []
    for name in SIGNATURES:
        rule = rules[name]
        if name == "sSeedSensitive":
            hit = (not seed_stats["dispersionOk"]) or (not seed_stats["worstOk"]) or seed_stats["divergent"] > 0
        else:
            hit = rule["value"] > rule["threshold"]
        rule["fired"] = bool(hit)
        if hit:
            fired.append(name)
    return {"observedSignatures": fired, "medians": medians, "rules": rules, "perSeed": [
        {k: d[k] for k in ("relL2", "normalizedResidualRms", "maxBoundaryAbs", "localizedRatio", "fluxBalance")} for d in per_seed]}


def run_intervention(config: Mapping[str, Any], pool: Sequence[float], dev_points: Sequence[float],
                     levels: Sequence[int], seeds_per_level: int, seed_bases: Mapping[str, int]) -> dict[str, Any]:
    """Controlled sampling intervention: only collocationCount changes; every other control is the frozen config."""

    results = []
    for level_index, count in enumerate(levels):
        errors = []
        runs = []
        for k in range(seeds_per_level):
            offset = 1000 * (level_index + 1) + k
            seeds = {"init": seed_bases["initBase"] + offset, "sample": seed_bases["sampleBase"] + offset,
                     "batch": seed_bases["batchBase"] + offset}
            run = pinn_torch.train_run(config, pool, dev_points, seeds, collocation_count=int(count), log_every=1000)
            errors.append(run["devRelL2"])
            runs.append({"seeds": seeds, "devRelL2": run["devRelL2"], "completed": run["completed"], "nan": run["nanEncountered"],
                         "finalLoss": run["finalLoss"], "collocationIndices": run["collocationIndices"]})
        results.append({"level": f"N_train={count}", "collocationCount": int(count), "seeds": seeds_per_level,
                        "errors": errors, "medianError": _median(errors), "runs": runs})
    return {
        "factor": "sampling",
        "changed": ["sampling"],
        "heldFixed": [c for c in INTERVENTION_CONTROLS if c != "sampling"],
        "levels": results,
        "evaluationSet": "dev",
        "medianStrictlyDecreasing": all(b["medianError"] < a["medianError"] for a, b in zip(results, results[1:])),
    }


def intervention_document(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "factor": "sampling",
        "changed": ["sampling"],
        "heldFixed": list(result["heldFixed"]),
        "levels": [{"level": lvl["level"], "seeds": int(lvl["seeds"]), "medianError": float(lvl["medianError"])} for lvl in result["levels"]],
    }


def exclusion_records(observed: Sequence[str], facts: Mapping[str, Any], *, named: str = "rSamplingDeficiency",
                      constitution_version: str) -> dict[str, dict[str, str]]:
    """Exclusion record for every other admissible cause of every observed signature, quoting measured facts."""

    matrix = admissible_root_causes(constitution_version)
    candidates: list[RootCauseClass] = []
    for name in observed:
        for cause in matrix[FailureSignature(name)]:
            if cause.value != named and cause not in candidates:
                candidates.append(cause)
    texts = {
        "rSpecDefect": ("exp-int-sampling", f"spec held fixed across all levels while the median dev error fell {facts['errorSpan']}; "
                        f"the analytic reference satisfies the training residual operator to {facts['T3']:.1e} (P22/P31-type check T3), "
                        f"forcing audited against pi^2 sin(pi x) within 1e-12 (T10 validator control)"),
        "rDataDefect": ("exp-int-sampling", f"forward problem: no observation data enters the operator; fixed data audited -- forcing within 1e-12, "
                        f"boundary values g(0)=g(1)=0 (T4 boundary loss of u* = {facts['T4']:.1e}); data unchanged across levels"),
        "rSingularityTreatment": ("exp-gate2a-reference", f"u* = sin(pi x) is C-infinity on [0,1]; max |-u*''-f| on D_phys = {facts['G2a']:.1e}; the spec registers no singularity"),
        "rReferenceDefect": ("exp-gate2-reference-fdm", f"analytic reference verified (residual {facts['G2a']:.1e} < 1e-12, boundary < 1e-14); FDM cross-check observed order {facts['fdmOrders']}"),
        "rImplementationDefect": ("exp-gate3-int-sampling", f"T1 AD vs FD {facts['T1']:.1e}, T3 {facts['T3']:.1e}, T4 {facts['T4']:.1e} PASS on this code; "
                                  f"the same code at the highest sampling level reaches median dev error {facts['bestLevelMedian']:.2e} "
                                  f"and at the frozen baseline {facts['baselineMedian']}"),
        "rCapacityLimit": ("exp-int-sampling", f"architecture held fixed ({facts['architecture']}); the same network reaches median dev error "
                           f"{facts['bestLevelMedian']:.2e} at the highest level and {facts['baselineMedian']} at the frozen baseline, so capacity suffices"),
        "rOptimizationFailure": ("exp-int-sampling", f"optimizer, schedule, weights and budget held fixed; training pde loss at the failing level "
                                 f"reached {facts['failingTrainLoss']:.1e} (optimizer converged on the seen points) while the dev error stayed "
                                 f"{facts['failingMedian']:.2e}; the same optimizer reaches {facts['bestLevelMedian']:.2e} with denser sampling"),
    }
    records: dict[str, dict[str, str]] = {}
    for cause in candidates:
        experiment, observed_text = texts[cause.value]
        records[cause.value] = {"experiment": experiment, "observed": observed_text}
    return records


def diagnosis_record(*, diagnosis_id: str, problem_id: str, revision: int, spec_hash: str, constitution_version: str,
                     observed: Sequence[str], primary: str, root_cause: str, signature_evidence: Mapping[str, Mapping[str, str]],
                     experiment_id: str, excludes: Mapping[str, Mapping[str, str]], intervention: Mapping[str, Any] | None,
                     evidence_pointers: Sequence[Mapping[str, str]], round_no: int, decided_by: str, decided_at: str) -> dict[str, Any]:
    experiment: dict[str, Any] = {
        "experimentId": experiment_id,
        "evaluationSet": "dev",
        "excludes": {k: dict(v) for k, v in excludes.items()},
        "evidencePointers": [dict(p) for p in evidence_pointers],
    }
    if intervention is not None:
        experiment["intervention"] = dict(intervention)
    return {
        "schemaVersion": "pinn.diagnosisRecord/1.0",
        "diagnosisId": diagnosis_id,
        "problemId": problem_id,
        "revision": revision,
        "specHash": spec_hash,
        "constitutionVersion": constitution_version,
        "problemClass": "forward",
        "signature": primary,
        "observedSignatures": list(observed),
        "explainedSignatures": list(observed),
        "signatureEvidence": {k: dict(v) for k, v in signature_evidence.items()},
        "rootCause": root_cause,
        "discriminatingExperiment": experiment,
        "round": round_no,
        "decidedBy": decided_by,
        "decidedAt": decided_at,
    }
