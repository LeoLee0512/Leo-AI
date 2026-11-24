"""Experiment 3 rules: weight-only intervention, hard BC as an independent intervention, exclusions, revision gating."""

import copy
import json
from pathlib import Path

import pytest

from pinn.experiments import bc_diagnosis, criteria, diagnosis
from pinn.governance.state_machine import FailureSignature, admissible_root_causes
from pinn.governance.trust_loop import validate_diagnosis_record

ROOT = Path(__file__).resolve().parents[2]
ART = {"artifactId": "art-1", "sha256": "b" * 64}
SEEDS = [{"init": 20260900 + i, "sample": 20261000 + i, "batch": 20261100 + i} for i in range(10)]


def level(lam, bc, sol=3e-4, pde=5e-3):
    return {"level": f"lambda_BC={lam:g}", "lambda": lam, "seedTriplets": SEEDS, "errors": [bc] * 10, "pdeErrors": [pde] * 10,
            "solutionErrors": [sol] * 10, "runs": [], "medians": {"bcError": bc, "pdeError": pde, "solutionError": sol}}


def weight_result(bcs, sols=(3e-4, 3e-4, 3e-4), pdes=(5e-3, 5e-3, 5e-3)):
    levels = [level(lam, bc, sol, pde) for lam, bc, sol, pde in zip(bc_diagnosis.LAMBDA_LEVELS, bcs, sols, pdes)]
    return {"experiment": "3A", "factor": "lossWeights.bc", "changed": ["lossWeights"], "levels": levels, "evaluationSet": "dev",
            "criterion": criteria.paired_intervention_errors(levels, metric="errors"),
            "criterionSummary": criteria.paired_intervention_summary(levels, metric="errors")}


def hard_result(bc=0.0, sol=2e-4, pde=4e-3):
    return {"experiment": "3B", "runs": [{"seeds": s, "bcError": bc, "pdeError": pde, "solutionError": sol} for s in SEEDS],
            "medians": {"bcError": bc, "pdeError": pde, "solutionError": sol}, "allSeedsBelowAC3": bc < bc_diagnosis.AC3}


def test_weight_intervention_supports_optimization_when_criterion_met_without_degradation():
    weight = weight_result((1.5e-4, 3e-5, 5e-6))
    decision = bc_diagnosis.decide_root_cause(weight, hard_result())
    assert decision["rootCause"] == "rOptimizationFailure" and decision["criterionMet"]
    choice = bc_diagnosis.revision_choice(decision, weight)
    assert choice == {"change": "lossWeights.bc", "value": 100.0, "rule": "smallest preregistered level with every seed below AC-3"}


def test_weak_or_degrading_weight_response_falls_to_hard_bc_or_undetermined():
    weak = weight_result((1.5e-4, 1.2e-4, 1.0e-4))                 # ratios 0.8: criterion not met
    decision = bc_diagnosis.decide_root_cause(weak, hard_result())
    assert decision["rootCause"] == "rSpecDefect" and not decision["criterionMet"]
    assert bc_diagnosis.revision_choice(decision, weak)["change"] == "boundaryConditions.enforcement"
    degrading = weight_result((1.5e-4, 3e-5, 5e-6), sols=(3e-4, 4e-4, 2e-3))   # solution error above epsilon_spec at lambda 1000
    decision = bc_diagnosis.decide_root_cause(degrading, hard_result(sol=5e-3))  # hard also inadmissible
    assert decision["rootCause"] == "rUndetermined"
    assert bc_diagnosis.revision_choice(decision, degrading)["change"] is None


def test_weight_plus_architecture_change_is_not_a_valid_single_factor_intervention():
    from pinn.governance.state_machine import intervention_errors

    bad = {"factor": "capacity", "changed": ["architecture", "lossWeights"],
           "heldFixed": ["sampling", "optimizer", "lrSchedule", "trainingBudget", "spec", "reference", "seedProtocol"],
           "levels": [{"level": "a", "seeds": 10, "medianError": 1e-2}, {"level": "b", "seeds": 10, "medianError": 4e-3}, {"level": "c", "seeds": 10, "medianError": 1e-3}],
           "optimizationDiagnosticsClean": True}
    assert any("changing anything else" in e for e in intervention_errors(bad, "capacity"))
    # the 3A record itself declares exactly one changed control
    weight = weight_result((1.5e-4, 3e-5, 5e-6))
    assert weight["changed"] == ["lossWeights"] and "outputParameterization" not in weight["changed"]


def test_hard_bc_is_an_independent_intervention_with_its_own_record():
    hard = hard_result()
    assert hard["experiment"] == "3B" and hard["allSeedsBelowAC3"]
    result = bc_diagnosis.exclusions(weight_result((1.5e-4, 3e-5, 5e-6)), hard, {"T1": 1e-9, "T3": 1e-13, "T4": 1e-32, "G2a": 0.0},
                                     named="rOptimizationFailure", constitution_version="1.2")
    matrix = admissible_root_causes("1.2")
    expected = {c.value for c in matrix[FailureSignature.BC_RESIDUAL]} - {"rOptimizationFailure"}
    assert set(result) == expected and all(r["observed"] for r in result.values())
    assert result["rSpecDefect"]["experiment"] == "exp-3b-hard-bc"


def test_diagnosis_without_exclusions_is_rejected():
    record = diagnosis.diagnosis_record(
        diagnosis_id="dg-t-bc", problem_id="pdef-poisson1d-test", revision=1, spec_hash="a" * 64, constitution_version="1.2",
        observed=["sBcResidual"], primary="sBcResidual", root_cause="rOptimizationFailure",
        signature_evidence={"boundaryResidualDistribution": ART, "samplingConfigDiff": ART, "hardConstraintDiff": ART},
        experiment_id="exp-3a-weight", excludes={}, intervention=None, evidence_pointers=[ART], round_no=1, decided_by="t", decided_at="2026-09-16T00:00:00Z")
    errors = validate_diagnosis_record(record, constitution_version="1.2")
    assert any("once every other admissible root cause is excluded" in e for e in errors)
    full = bc_diagnosis.exclusions(weight_result((1.5e-4, 3e-5, 5e-6)), hard_result(), {"T1": 1e-9, "T3": 1e-13, "T4": 1e-32, "G2a": 0.0},
                                   named="rOptimizationFailure", constitution_version="1.2")
    record["discriminatingExperiment"]["excludes"] = full
    assert validate_diagnosis_record(record, constitution_version="1.2") == []


def test_revision_consumes_only_the_designated_pool_member():
    pool = json.loads((ROOT / "experiments/poisson1d/problems/pdef-poisson1d-cal-v1-claim-pool.json").read_text(encoding="utf-8"))
    members = pool["members"]
    assert [m["designatedRevision"] for m in members.values()] == [2, 3, 4]
    assert len({m["sampleSetHash"] for m in members.values()}) == 3
    assert all(m["antiCollisionOk"] and not m["isolationErrors"] and not any(m["sharedWithOtherMembers"].values()) and not m["burnt"] for m in members.values())
    ledger = json.loads((ROOT / "experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json").read_text(encoding="utf-8"))
    sealed = {e["sampleSetHash"] for e in ledger if e["event"] == "SEALED" and "sampleSetHash" in e}
    assert {m["sampleSetHash"] for m in members.values()} <= sealed
