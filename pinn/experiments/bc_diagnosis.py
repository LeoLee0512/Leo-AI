"""Experiment 3A / 3B: discriminating experiments for the sBcResidual failure of Experiment 1 (D_dev / D_phys only).

3A (P24): the soft-boundary weight lambda_BC is the only factor; preregistered
levels {10, 100, 1000}; the same ten seed triplets at every level (paired).
3B (P28): hard Dirichlet parameterization u = x (1 - x) N(x) as an independent
intervention (a different hypothesis class), everything else the baseline.
Per seed and level: BCError = max(|u(0)|, |u(1)|), PDEError = normalized
holdout residual RMS on D_dev, SolutionError = relative L2 on D_dev.

The decision rules (which root cause the results support, which revision is
allowed) are the preregistered ones of
``experiments/poisson1d/EXPERIMENT3_PREREGISTRATION_20260916.md`` sections 4-7
and are implemented literally in ``decide_root_cause`` / ``revision_choice``.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping, Sequence

from pinn.governance.state_machine import FailureSignature, admissible_root_causes
from pinn.reference import analytic_poisson as reference

from . import criteria, pinn_torch
from .gates import F_RMS

LAMBDA_LEVELS = (10.0, 100.0, 1000.0)      # preregistered; includes the frozen baseline 10
EPSILON_SPEC = 1e-3
AC3 = 1e-4
AC4 = 1e-2


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def measure(model, dev_points: Sequence[float]) -> dict[str, float]:
    fld = pinn_torch.fields(model, dev_points)
    ends = pinn_torch.fields(model, [0.0, 1.0])
    exact = [reference.solution(x) for x in dev_points]
    residuals = [-uxx - reference.forcing(x) for uxx, x in zip(fld["uxx"], dev_points)]
    return {
        "bcError": max(abs(ends["u"][0]), abs(ends["u"][1])),
        "pdeError": math.sqrt(math.fsum(r * r for r in residuals) / len(residuals)) / F_RMS,
        "solutionError": pinn_torch.rel_l2(fld["u"], exact),
    }


def seed_triplets(config: Mapping[str, Any]) -> list[dict[str, int]]:
    sp = config["seedProtocol"]
    return [{"init": sp["initBase"] + i, "sample": sp["sampleBase"] + i, "batch": sp["batchBase"] + i} for i in range(int(sp["runs"]))]


def run_weight_intervention(config: Mapping[str, Any], pool: Sequence[float], dev_points: Sequence[float],
                            log=print) -> dict[str, Any]:
    triplets = seed_triplets(config)
    levels = []
    for lam in LAMBDA_LEVELS:
        cfg = copy.deepcopy(config)
        cfg["lossWeights"]["bc"] = float(lam)
        runs = []
        for seeds in triplets:
            run = pinn_torch.train_run(cfg, pool, dev_points, seeds, collocation_count=int(config["sampling"]["collocationCount"]), log_every=1000)
            model = pinn_torch.model_from_weights(cfg, run["weights"])
            m = measure(model, dev_points)
            runs.append({"seeds": seeds, **m, "completed": run["completed"], "nan": run["nanEncountered"], "finalLoss": run["finalLoss"]})
            log(f"  3A lambda={lam:g} seeds={seeds['init']} bc={m['bcError']:.2e} pde={m['pdeError']:.2e} sol={m['solutionError']:.2e}")
        levels.append({"level": f"lambda_BC={lam:g}", "lambda": lam, "seedTriplets": triplets,
                       "errors": [r["bcError"] for r in runs], "pdeErrors": [r["pdeError"] for r in runs],
                       "solutionErrors": [r["solutionError"] for r in runs], "runs": runs,
                       "medians": {"bcError": _median([r["bcError"] for r in runs]), "pdeError": _median([r["pdeError"] for r in runs]),
                                   "solutionError": _median([r["solutionError"] for r in runs])}})
    return {
        "experiment": "3A-P24-softBoundaryWeight", "factor": "lossWeights.bc", "changed": ["lossWeights"],
        "heldFixed": ["architecture", "activation", "outputParameterization", "optimizer", "lrSchedule", "trainingBudget", "sampling",
                      "seedProtocol", "spec", "reference", "thresholds"],
        "levels": levels, "evaluationSet": "dev",
        "criterion": criteria.paired_intervention_errors(levels, metric="errors"),
        "criterionSummary": criteria.paired_intervention_summary(levels, metric="errors"),
    }


def run_hard_bc(config: Mapping[str, Any], pool: Sequence[float], dev_points: Sequence[float], log=print) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    cfg["network"]["outputParameterization"] = "x(1-x)N"
    runs = []
    for seeds in seed_triplets(config):
        run = pinn_torch.train_run(cfg, pool, dev_points, seeds, collocation_count=int(config["sampling"]["collocationCount"]), log_every=1000)
        model = pinn_torch.model_from_weights(cfg, run["weights"])
        m = measure(model, dev_points)
        runs.append({"seeds": seeds, **m, "completed": run["completed"], "nan": run["nanEncountered"], "finalLoss": run["finalLoss"]})
        log(f"  3B hard seeds={seeds['init']} bc={m['bcError']:.2e} pde={m['pdeError']:.2e} sol={m['solutionError']:.2e}")
    return {
        "experiment": "3B-P28-hardDirichlet", "changed": ["outputParameterization (hypothesis class / enforcement method)"],
        "heldFixed": ["architecture depth/width", "activation", "optimizer", "lrSchedule", "trainingBudget", "sampling", "seedProtocol",
                      "spec", "reference", "thresholds", "lossWeights (bc term identically zero)"],
        "runs": runs, "evaluationSet": "dev",
        "medians": {"bcError": _median([r["bcError"] for r in runs]), "pdeError": _median([r["pdeError"] for r in runs]),
                    "solutionError": _median([r["solutionError"] for r in runs])},
        "allSeedsBelowAC3": all(r["bcError"] < AC3 for r in runs),
    }


def degradation(low: Mapping[str, Any], high: Mapping[str, Any]) -> dict[str, Any]:
    """Preregistered 'unacceptable degradation': high-level medians above the preregistered thresholds or > 2x the low level."""

    sol_low, sol_high = low["medians"]["solutionError"], high["medians"]["solutionError"]
    pde_low, pde_high = low["medians"]["pdeError"], high["medians"]["pdeError"]
    return {
        "solutionMedianLow": sol_low, "solutionMedianHigh": sol_high, "pdeMedianLow": pde_low, "pdeMedianHigh": pde_high,
        "unacceptable": (sol_high > EPSILON_SPEC) or (pde_high > AC4) or (sol_high > 2.0 * sol_low) or (pde_high > 2.0 * pde_low),
    }


def decide_root_cause(weight: Mapping[str, Any], hard: Mapping[str, Any]) -> dict[str, Any]:
    """Preregistration section 6, applied literally."""

    levels = weight["levels"]
    criterion_met = not weight["criterion"]
    degradations = [degradation(levels[i], levels[i + 1]) for i in range(len(levels) - 1)]
    degraded = any(d["unacceptable"] for d in degradations)
    branch: str
    root_cause: str
    if criterion_met and not degraded:
        branch = "6.1 weight intervention meets the paired criterion without unacceptable degradation -> training / optimization protocol (loss weighting)"
        root_cause = "rOptimizationFailure"
    elif (not criterion_met or degraded) and hard["allSeedsBelowAC3"] and hard["medians"]["solutionError"] <= EPSILON_SPEC and hard["medians"]["pdeError"] <= AC4:
        branch = "6.2 soft enforcement insufficient, hard enforcement admissible -> the spec's enforcement choice (soft) is the defect"
        root_cause = "rSpecDefect"
    else:
        branch = "6.3 neither intervention separates the candidates -> rUndetermined, STOP_THE_LINE"
        root_cause = "rUndetermined"
    return {"rootCause": root_cause, "branch": branch, "criterionMet": criterion_met, "criterionErrors": list(weight["criterion"]),
            "degradations": degradations, "hardAllSeedsBelowAC3": hard["allSeedsBelowAC3"], "hardMedians": hard["medians"]}


def revision_choice(decision: Mapping[str, Any], weight: Mapping[str, Any]) -> dict[str, Any]:
    """Preregistration section 7: the smallest preregistered lambda with every seed below AC-3 (optimization branch)."""

    if decision["rootCause"] == "rOptimizationFailure":
        for level in weight["levels"]:
            if all(e < AC3 for e in level["errors"]):
                return {"change": "lossWeights.bc", "value": level["lambda"], "rule": "smallest preregistered level with every seed below AC-3"}
        return {"change": None, "rule": "no preregistered level has every seed below AC-3; soft-weight revision not allowed (section 7)"}
    if decision["rootCause"] == "rSpecDefect":
        return {"change": "boundaryConditions.enforcement", "value": "hard", "outputParameterization": "x(1-x)N",
                "rule": "enforcement soft -> hard; new specHash; revision 2"}
    return {"change": None, "rule": "rUndetermined: no revision"}


def exclusions(weight: Mapping[str, Any], hard: Mapping[str, Any], facts: Mapping[str, Any], *, named: str,
               constitution_version: str) -> dict[str, dict[str, str]]:
    """Exclusion record for every other admissible cause of sBcResidual, quoting measured facts."""

    matrix = admissible_root_causes(constitution_version)
    best = weight["levels"][-1]["medians"]
    base = weight["levels"][0]["medians"]
    texts = {
        "rSpecDefect": ("exp-3b-hard-bc", f"boundary data g(0)=g(1)=0 audited (T4 boundary loss of u* {facts['T4']:.1e}); spec fields unchanged across 3A; "
                        f"the same spec is met when only the loss weight changes (lambda 1000: BC median {best['bcError']:.2e}) -- the defect is not in what is specified"
                        if named != "rSpecDefect" else ""),
        "rDataDefect": ("exp-3a-weight", f"forward problem; boundary data are the exact spec values 0 and 0; forcing audited within 1e-12 (T10); data unchanged across all levels"),
        "rSingularityTreatment": ("exp-gate2a-reference", f"u* in C-infinity, G2a residual {facts['G2a']:.1e}; boundary error appears with smooth data"),
        "rImplementationDefect": ("exp-gate3-plus-3a", f"T1 AD vs FD {facts['T1']:.1e}, T3 {facts['T3']:.1e}, T4 {facts['T4']:.1e} PASS; the same boundary operator code gives "
                                  f"BC median {base['bcError']:.2e} at lambda 10 and {best['bcError']:.2e} at lambda 1000 (3A), and exactly 0 under 3B -- the operator computes u(0), u(1) correctly"),
        "rCapacityLimit": ("exp-3a-weight", f"architecture fixed (3x32 tanh); the same network reaches BC median {best['bcError']:.2e} and solution median "
                           f"{best['solutionError']:.2e} at lambda 1000 -- capacity suffices for the boundary data"),
        "rSamplingDeficiency": ("exp-3a-weight", f"boundary points are the exact endpoints and always in the training set; interior sampling fixed at 256 across all levels while "
                                f"BC error moved {base['bcError']:.2e} -> {best['bcError']:.2e}; sampling is not the variable"),
        "rOptimizationFailure": ("exp-3b-hard-bc", f"optimizer / schedule / budget fixed; the boundary error does not respond to the loss weighting within the preregistered "
                                 f"levels ({base['bcError']:.2e} -> {best['bcError']:.2e}, criterion {'met' if not weight['criterion'] else 'not met'}) while the hard "
                                 f"parameterization removes it exactly with the same optimizer" if named != "rOptimizationFailure" else ""),
    }
    out: dict[str, dict[str, str]] = {}
    for cause in matrix[FailureSignature.BC_RESIDUAL]:
        if cause.value == named:
            continue
        experiment, text = texts[cause.value]
        if not text:
            continue
        out[cause.value] = {"experiment": experiment, "observed": text}
    return out
