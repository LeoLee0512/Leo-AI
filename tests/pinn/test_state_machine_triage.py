"""Amended workflow: no PARTIAL advancement, one entry to ACCEPTED, FAIL triaged by root cause.

The triage tests exercise the A-0002 (Constitution 1.2) semantics, so they run
under a simulated acceptance: ``effective_1_2`` adds "1.2" to the runtime's
supported versions for the duration of each test.  Without it "1.2" is refused
(see test_constitution_version_isolation.py).
"""

import pytest

from pinn.governance import locking
from pinn.governance.state_machine import (
    ADMISSIBLE_ROOT_CAUSES_BY_VERSION,
    FACTOR_CONTROL,
    INTERVENTION_CONTROLS,
    INTERVENTION_FACTORS,
    MATRIX_SCOPE,
    MAX_DIAGNOSIS_ROUNDS,
    ROOT_CAUSE_GATE,
    SIGNATURE_EVIDENCE,
    FailureSignature as Sig,
    GateStatus,
    IllegalTransition,
    RootCauseClass as RC,
    TriageRoute,
    WorkflowState as S,
    advance,
    advancement_allowed,
    diagnose as _diagnose,
    discriminating_experiment_errors as _discriminating_experiment_errors,
    enter_validation,
    failure_state,
    from_gate_status,
    gate5_status,
    reenter,
    revise,
)
from pinn.governance.trust_vector import DIMENSIONS, TrustStatus as T

JUDGED_BY = {1: ("math",), 2: (), 3: ("impl",), 4: ("train",), 5: ("physics", "external"), 6: ("repro",)}
V = "1.2"
ADMISSIBLE_ROOT_CAUSES = ADMISSIBLE_ROOT_CAUSES_BY_VERSION[V]


@pytest.fixture(autouse=True)
def effective_1_2(monkeypatch):
    """Simulate A-0002 ACCEPTED: the recipe adds "1.2" to SUPPORTED_CONSTITUTION_VERSIONS and nothing else."""

    monkeypatch.setattr(locking, "SUPPORTED_CONSTITUTION_VERSIONS", ("1.0", "1.1", "1.2"))


def diagnose(*args, constitution_version=V, **kwargs):
    return _diagnose(*args, constitution_version=constitution_version, **kwargs)


def discriminating_experiment_errors(*args, constitution_version=V, **kwargs):
    return _discriminating_experiment_errors(*args, constitution_version=constitution_version, **kwargs)


def vector_through(gate):
    """Dimensions judged by gates up to ``gate`` are PASS; everything later is NOT_CHECKED."""

    passed = {d for number, dims in JUDGED_BY.items() if number <= gate for d in dims}
    return {d: (T.PASS if d in passed else T.NOT_CHECKED) for d in DIMENSIONS}


def intervention(factor, levels=3, seeds=5, medians=None, **overrides):
    control = FACTOR_CONTROL[factor]
    medians = medians or [0.041, 0.021, 0.011, 0.006][:levels]
    result = {
        "factor": factor,
        "changed": [control],
        "heldFixed": [item for item in INTERVENTION_CONTROLS if item != control],
        "levels": [{"level": f"L{index}", "seeds": seeds, "medianError": median} for index, median in enumerate(medians)],
        "optimizationDiagnosticsClean": True,
    }
    result.update(overrides)
    return result


def replay(max_divergence=0.03, epsilon=1e-10, located="dropout left enabled in eval mode"):
    result = {"sameSeedRuns": 2, "maxDivergence": max_divergence, "epsilonDet": epsilon}
    if located is not None:
        result["defectLocated"] = located
    return result


def experiment_for(signature, root_cause):
    """A discriminating experiment that excluded every other admissible root cause of the signature."""

    result = {
        "experimentId": "exp-001",
        "excludes": {
            cause.value: {"experiment": "P8", "observed": f"{cause.value} predicted a change that did not occur"}
            for cause in ADMISSIBLE_ROOT_CAUSES[signature] if cause is not root_cause
        },
    }
    if root_cause in INTERVENTION_FACTORS:
        result["intervention"] = intervention(INTERVENTION_FACTORS[root_cause])
    if signature is Sig.SEED_SENSITIVE and root_cause is RC.IMPLEMENTATION_DEFECT:
        result["determinismReplay"] = replay()
    if signature is Sig.SEED_SENSITIVE and root_cause is RC.SPEC_DEFECT:
        result["identifiability"] = identifiability()
    return result


def identifiability(**overrides):
    """P34 on a pure-Neumann Poisson with an absolute-value claim and no gauge condition: a spec defect."""

    result = {"ambiguityType": "nullspace", "claimRequiresUniqueEvaluation": True,
              "specResolvesAmbiguity": False, "ambiguityIntent": "unintended", "nullspaceProjectionFraction": 0.98}
    result.update(overrides)
    return result


def evidence_for(signature, root_cause=RC.UNDETERMINED):
    return {key: "artifact" for key in SIGNATURE_EVIDENCE[signature]} | {
        "discriminatingExperiment": experiment_for(signature, root_cause)}


def test_happy_path_reaches_accepted_only_through_every_gate():
    state = advance(S.DRAFT, 1, GateStatus.PASS, vector_through(1))
    assert state is S.SPEC_LOCKED
    state = advance(state, 2, GateStatus.PASS, vector_through(2))
    assert state is S.BASELINE_VERIFIED
    state = advance(state, 3, GateStatus.PASS, vector_through(3))
    assert state is S.IMPLEMENTATION_VERIFIED
    state = advance(state, 4, GateStatus.PASS, vector_through(4))
    assert state is S.TRAINING_COMPLETED
    state = enter_validation(state)
    assert state is S.VALIDATION
    state = advance(state, 5, gate5_status(physics=GateStatus.PASS, external=GateStatus.PASS), vector_through(5))
    assert state is S.REPRODUCIBILITY_CHECK
    state = advance(state, 6, GateStatus.PASS, vector_through(6), claim_decision_signed=True)
    assert state is S.ACCEPTED


@pytest.mark.parametrize("result", [GateStatus.PARTIAL, GateStatus.BLOCKED])
def test_partial_and_blocked_never_advance(result):
    assert advance(S.IMPLEMENTATION_VERIFIED, 4, result, vector_through(4)) is S.IMPLEMENTATION_VERIFIED


@pytest.mark.parametrize("state", [S.TRAINING_COMPLETED, S.VALIDATION, S.FAILURE_RECORDED, S.DIAGNOSED, S.REVISED, S.DRAFT])
def test_accepted_has_a_single_entry(state):
    with pytest.raises(IllegalTransition):
        advance(state, 6, GateStatus.PASS, vector_through(6), claim_decision_signed=True)


@pytest.mark.parametrize("signed", [False, None, "yes", 1])
def test_accepted_needs_a_literally_signed_decision(signed):
    with pytest.raises(IllegalTransition):
        advance(S.REPRODUCIBILITY_CHECK, 6, GateStatus.PASS, vector_through(6), claim_decision_signed=signed)


def test_premature_or_non_pass_dimensions_block_advancement():
    early = vector_through(4)
    early["external"] = T.PARTIAL
    with pytest.raises(IllegalTransition):
        advance(S.IMPLEMENTATION_VERIFIED, 4, GateStatus.PASS, early)
    weak = vector_through(4)
    weak["impl"] = T.PARTIAL
    with pytest.raises(IllegalTransition):
        advance(S.IMPLEMENTATION_VERIFIED, 4, GateStatus.PASS, weak)
    assert advancement_allowed(vector_through(4), 4)
    assert not advancement_allowed(early, 4)
    with pytest.raises(ValueError):
        advancement_allowed(vector_through(4), 7)


def test_gate_must_execute_in_its_own_state():
    with pytest.raises(IllegalTransition):
        advance(S.SPEC_LOCKED, 4, GateStatus.PASS, vector_through(4))
    with pytest.raises(IllegalTransition):
        enter_validation(S.SPEC_LOCKED)
    with pytest.raises(ValueError):
        advance(S.DRAFT, 9, GateStatus.PASS, vector_through(1))
    with pytest.raises(TypeError):
        advance("DRAFT", 1, GateStatus.PASS, vector_through(1))
    with pytest.raises(TypeError):
        advance(S.DRAFT, 1, "PASS", vector_through(1))


def test_fail_records_failure_then_stops_the_line():
    assert advance(S.VALIDATION, 5, GateStatus.FAIL, vector_through(4)) is S.FAILURE_RECORDED
    assert failure_state(MAX_DIAGNOSIS_ROUNDS - 1) is S.FAILURE_RECORDED
    assert failure_state(MAX_DIAGNOSIS_ROUNDS) is S.STOPPED_THE_LINE
    assert advance(S.VALIDATION, 5, GateStatus.FAIL, vector_through(4),
                   rounds_completed=MAX_DIAGNOSIS_ROUNDS) is S.STOPPED_THE_LINE
    with pytest.raises(ValueError):
        failure_state(-1)
    with pytest.raises(ValueError):
        failure_state(True)


def test_gate5_needs_both_must_groups():
    assert gate5_status(physics=GateStatus.PASS, external=GateStatus.PASS) is GateStatus.PASS
    assert gate5_status(physics=GateStatus.PASS, external=GateStatus.FAIL) is GateStatus.FAIL
    assert gate5_status(physics=GateStatus.BLOCKED, external=GateStatus.PARTIAL) is GateStatus.BLOCKED
    assert gate5_status(physics=GateStatus.PARTIAL, external=GateStatus.PASS) is GateStatus.PARTIAL
    with pytest.raises(TypeError):
        gate5_status(physics="PASS", external=GateStatus.PASS)


def test_failed_validation_cannot_reach_reproducibility_check():
    state = advance(S.VALIDATION, 5, GateStatus.FAIL, vector_through(4))
    with pytest.raises(IllegalTransition):
        advance(state, 6, GateStatus.PASS, vector_through(6), claim_decision_signed=True)
    with pytest.raises(IllegalTransition):
        advance(state, 5, GateStatus.PASS, vector_through(5))


# --------------------------------------------------------- two-layer triage

def test_route_follows_the_root_cause_not_the_signature():
    """A localized error is not automatically an implementation problem (review finding 1)."""

    sig = Sig.LOCALIZED_ERROR
    _, singular = diagnose(S.FAILURE_RECORDED, sig, RC.SINGULARITY_TREATMENT, evidence_for(sig, RC.SINGULARITY_TREATMENT))
    _, capacity = diagnose(S.FAILURE_RECORDED, sig, RC.CAPACITY_LIMIT, evidence_for(sig, RC.CAPACITY_LIMIT))
    _, reference = diagnose(S.FAILURE_RECORDED, sig, RC.REFERENCE_DEFECT, evidence_for(sig, RC.REFERENCE_DEFECT))
    _, boundary = diagnose(S.FAILURE_RECORDED, sig, RC.IMPLEMENTATION_DEFECT, evidence_for(sig, RC.IMPLEMENTATION_DEFECT))
    assert (singular.gate, singular.reentry_state) == (1, S.DRAFT)
    assert (capacity.gate, capacity.reentry_state) == (4, S.IMPLEMENTATION_VERIFIED)
    assert (reference.gate, reference.reentry_state) == (2, S.SPEC_LOCKED)
    assert (boundary.gate, boundary.reentry_state) == (3, S.BASELINE_VERIFIED)
    assert singular == TriageRoute(sig, RC.SINGULARITY_TREATMENT, 1, S.DRAFT)


def test_pde_residual_can_be_an_ad_defect_routed_to_implementation():
    state, route = diagnose(S.FAILURE_RECORDED, Sig.PDE_RESIDUAL, RC.IMPLEMENTATION_DEFECT,
                            evidence_for(Sig.PDE_RESIDUAL, RC.IMPLEMENTATION_DEFECT))
    assert state is S.DIAGNOSED
    assert route.gate == 3
    assert route.reentry_state is S.BASELINE_VERIFIED


@pytest.mark.parametrize("signature,root_cause", [
    (Sig.PDE_RESIDUAL, RC.REFERENCE_DEFECT),
    (Sig.SEED_SENSITIVE, RC.REFERENCE_DEFECT),
    (Sig.SEED_SENSITIVE, RC.DATA_DEFECT),
    (Sig.CONSERVATION, RC.REFERENCE_DEFECT),
    (Sig.CONSERVATION, RC.SINGULARITY_TREATMENT),
    (Sig.BC_RESIDUAL, RC.REFERENCE_DEFECT),
    (Sig.PDE_RESIDUAL, RC.DATA_DEFECT),
    (Sig.LOCALIZED_ERROR, RC.DATA_DEFECT),
])
def test_inadmissible_root_causes_are_refused(signature, root_cause):
    with pytest.raises(IllegalTransition):
        diagnose(S.FAILURE_RECORDED, signature, root_cause, evidence_for(signature, root_cause))


@pytest.mark.parametrize("signature", list(Sig))
def test_every_admissible_root_cause_has_a_gate(signature):
    for root_cause in ADMISSIBLE_ROOT_CAUSES[signature]:
        assert root_cause in ROOT_CAUSE_GATE
        _, route = diagnose(S.FAILURE_RECORDED, signature, root_cause, evidence_for(signature, root_cause))
        assert route.gate == ROOT_CAUSE_GATE[root_cause]


@pytest.mark.parametrize("signature,root_cause,gate", [
    (Sig.BC_RESIDUAL, RC.CAPACITY_LIMIT, 4),
    (Sig.PINN_CFD, RC.CAPACITY_LIMIT, 4),
    (Sig.LOCALIZED_ERROR, RC.SPEC_DEFECT, 1),
    (Sig.PINN_CFD, RC.SAMPLING_DEFICIENCY, 4),
    (Sig.SEED_SENSITIVE, RC.IMPLEMENTATION_DEFECT, 3),
    (Sig.SEED_SENSITIVE, RC.SPEC_DEFECT, 1),
    (Sig.PDE_RESIDUAL, RC.SINGULARITY_TREATMENT, 1),
    (Sig.BC_RESIDUAL, RC.SINGULARITY_TREATMENT, 1),
])
def test_a0002_cells_are_admissible_and_add_an_exclusion_duty(signature, root_cause, gate):
    """A-0002: the three DeepSeek R2 cells route as expected, and every other cause must now exclude them."""

    state, route = diagnose(S.FAILURE_RECORDED, signature, root_cause, evidence_for(signature, root_cause))
    assert state is S.DIAGNOSED and route.gate == gate
    other = next(cause for cause in ADMISSIBLE_ROOT_CAUSES[signature] if cause is not root_cause)
    evidence = evidence_for(signature, other)
    del evidence["discriminatingExperiment"]["excludes"][root_cause.value]
    with pytest.raises(ValueError, match=root_cause.value):
        diagnose(S.FAILURE_RECORDED, signature, other, evidence)


def test_undetermined_cause_stops_the_line_for_a_human():
    state, route = diagnose(S.FAILURE_RECORDED, Sig.PINN_CFD, RC.UNDETERMINED, evidence_for(Sig.PINN_CFD))
    assert state is S.STOPPED_THE_LINE
    assert route is None
    assert discriminating_experiment_errors(Sig.PINN_CFD, RC.UNDETERMINED, {"experimentId": "exp-9"}) == []


def test_diagnosis_requires_the_signature_evidence_and_a_discriminating_experiment():
    with pytest.raises(ValueError, match="gridConvergence"):
        diagnose(S.FAILURE_RECORDED, Sig.PINN_CFD, RC.REFERENCE_DEFECT,
                 {"pinnProvenance": "a", "referenceProvenance": "b",
                  "discriminatingExperiment": experiment_for(Sig.PINN_CFD, RC.REFERENCE_DEFECT)})
    with pytest.raises(ValueError, match="discriminatingExperiment"):
        diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE, {"multiSeedStatistics": "a"})
    complete = evidence_for(Sig.PINN_CFD, RC.REFERENCE_DEFECT)
    with pytest.raises(IllegalTransition):
        diagnose(S.VALIDATION, Sig.PINN_CFD, RC.REFERENCE_DEFECT, complete)
    with pytest.raises(TypeError):
        diagnose(S.FAILURE_RECORDED, "sPinnCfd", RC.REFERENCE_DEFECT, complete)
    with pytest.raises(TypeError):
        diagnose(S.FAILURE_RECORDED, Sig.PINN_CFD, "rReferenceDefect", complete)
    with pytest.raises(TypeError):
        diagnose(S.FAILURE_RECORDED, Sig.PINN_CFD, RC.REFERENCE_DEFECT, ["a", "b"])


def test_a_root_cause_is_what_is_left_not_what_is_chosen():
    """Adversarial audit item 1: naming the cheapest Gate's cause without excluding the others is refused."""

    sig = Sig.LOCALIZED_ERROR
    evidence = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    del evidence["discriminatingExperiment"]["excludes"]["rImplementationDefect"]
    with pytest.raises(ValueError, match="rImplementationDefect"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, evidence)
    free_text = dict(evidence_for(sig, RC.SAMPLING_DEFICIENCY), discriminatingExperiment="P11 looked fine")
    with pytest.raises(ValueError, match="excludes"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, free_text)
    empty = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    empty["discriminatingExperiment"]["excludes"]["rCapacityLimit"] = {}
    with pytest.raises(ValueError, match="empty exclusion record"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, empty)
    self_excluding = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    self_excluding["discriminatingExperiment"]["excludes"]["rSamplingDeficiency"] = {"experiment": "P11", "observed": "x"}
    with pytest.raises(ValueError, match="cannot exclude itself"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, self_excluding)
    unknown = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    unknown["discriminatingExperiment"]["excludes"]["rBadLuck"] = {"experiment": "P1", "observed": "x"}
    with pytest.raises(ValueError, match="not a RootCauseClass"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, unknown)


def test_seed_sensitivity_diagnosed_as_optimization_routes_back_to_training():
    state, route = diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE,
                            evidence_for(Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE))
    assert state is S.DIAGNOSED
    assert route.reentry_state is S.IMPLEMENTATION_VERIFIED
    state = revise(state)
    assert state is S.REVISED
    assert reenter(state, route, vector_through(3)) is S.IMPLEMENTATION_VERIFIED
    with pytest.raises(IllegalTransition):
        reenter(state, route, vector_through(5))


def test_reentry_requires_revised_and_upstream_pass():
    route = TriageRoute(Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE, 4, S.IMPLEMENTATION_VERIFIED)
    with pytest.raises(IllegalTransition):
        reenter(S.DIAGNOSED, route, vector_through(3))
    broken = vector_through(3)
    broken["impl"] = T.FAIL
    with pytest.raises(IllegalTransition):
        reenter(S.REVISED, route, broken)
    with pytest.raises(IllegalTransition):
        revise(S.REVISED)
    with pytest.raises(TypeError):
        reenter(S.REVISED, ("sSeedSensitive", 4), vector_through(3))


def test_spec_defect_reentry_resets_everything():
    route = TriageRoute(Sig.PDE_RESIDUAL, RC.SPEC_DEFECT, 1, S.DRAFT)
    assert reenter(S.REVISED, route, vector_through(0)) is S.DRAFT
    with pytest.raises(IllegalTransition):
        reenter(S.REVISED, route, vector_through(1))


def test_reentry_leaves_no_stale_downstream_pass():
    """Adversarial audit item 7: re-entering Gate k requires every dimension from k onwards to be reset."""

    route = TriageRoute(Sig.PINN_CFD, RC.REFERENCE_DEFECT, 2, S.SPEC_LOCKED)
    stale = vector_through(1)
    stale["external"] = T.PASS
    with pytest.raises(IllegalTransition):
        reenter(S.REVISED, route, stale)
    stale_blocked = vector_through(1)
    stale_blocked["repro"] = T.BLOCKED
    with pytest.raises(IllegalTransition):
        reenter(S.REVISED, route, stale_blocked)
    assert reenter(S.REVISED, route, vector_through(1)) is S.SPEC_LOCKED


def test_gate_status_converts_only_explicitly():
    assert from_gate_status(GateStatus.PASS) is T.PASS
    assert from_gate_status(GateStatus.BLOCKED) is T.BLOCKED
    with pytest.raises(TypeError):
        from_gate_status("PASS")
    with pytest.raises(TypeError):
        from_gate_status(T.PASS)



# ------------------------------------------- A-0002 draft 2: causal admissibility

def test_matrix_scope_is_forward_mvp():
    assert MATRIX_SCOPE == "forward-problem-mvp"
    for signature in (Sig.PDE_RESIDUAL, Sig.CONSERVATION):
        assert RC.DATA_DEFECT not in ADMISSIBLE_ROOT_CAUSES[signature]


def test_sampling_causality_needs_a_controlled_multi_level_intervention():
    """sPinnCfd + a sampling refinement trend supports rSamplingDeficiency; less than that does not."""

    sig = Sig.PINN_CFD
    good = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    state, route = diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, good)
    assert state is S.DIAGNOSED and route.gate == 4
    one_level = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    one_level["discriminatingExperiment"]["intervention"] = intervention("sampling", levels=1)
    with pytest.raises(ValueError, match="at least 3 levels"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, one_level)
    with_arch = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    with_arch["discriminatingExperiment"]["intervention"] = intervention("sampling", changed=["sampling", "architecture"])
    with pytest.raises(ValueError, match="changing anything else"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, with_arch)
    not_held = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    not_held["discriminatingExperiment"]["intervention"] = intervention("sampling", heldFixed=["spec"])
    with pytest.raises(ValueError, match="must hold"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, not_held)
    no_trend = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    no_trend["discriminatingExperiment"]["intervention"] = intervention("sampling", medians=[0.041, 0.011, 0.021])
    with pytest.raises(ValueError, match="strictly decrease"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, no_trend)
    few_seeds = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    few_seeds["discriminatingExperiment"]["intervention"] = intervention("sampling", seeds=1)
    with pytest.raises(ValueError, match="seeds per level"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, few_seeds)
    absent = evidence_for(sig, RC.SAMPLING_DEFICIENCY)
    del absent["discriminatingExperiment"]["intervention"]
    with pytest.raises(ValueError, match="controlled sampling intervention"):
        diagnose(S.FAILURE_RECORDED, sig, RC.SAMPLING_DEFICIENCY, absent)


def test_capacity_needs_a_controlled_intervention_and_clean_optimization_diagnostics():
    sig = Sig.BC_RESIDUAL
    single = evidence_for(sig, RC.CAPACITY_LIMIT)
    single["discriminatingExperiment"]["intervention"] = intervention("capacity", levels=2)
    with pytest.raises(ValueError, match="at least 3 levels"):
        diagnose(S.FAILURE_RECORDED, sig, RC.CAPACITY_LIMIT, single)
    trend = evidence_for(sig, RC.CAPACITY_LIMIT)
    assert diagnose(S.FAILURE_RECORDED, sig, RC.CAPACITY_LIMIT, trend)[1].gate == 4
    dirty = evidence_for(sig, RC.CAPACITY_LIMIT)
    dirty["discriminatingExperiment"]["intervention"] = intervention("capacity", optimizationDiagnosticsClean=False)
    with pytest.raises(ValueError, match="optimization diagnostics are not clean"):
        diagnose(S.FAILURE_RECORDED, sig, RC.CAPACITY_LIMIT, dirty)
    wrong_factor = evidence_for(sig, RC.CAPACITY_LIMIT)
    wrong_factor["discriminatingExperiment"]["intervention"] = intervention("sampling")
    with pytest.raises(ValueError, match="factor: must be 'capacity'"):
        diagnose(S.FAILURE_RECORDED, sig, RC.CAPACITY_LIMIT, wrong_factor)


def test_seed_sensitive_implementation_defect_needs_a_diverging_replay_and_a_located_defect():
    sig = Sig.SEED_SENSITIVE
    diverging = evidence_for(sig, RC.IMPLEMENTATION_DEFECT)
    state, route = diagnose(S.FAILURE_RECORDED, sig, RC.IMPLEMENTATION_DEFECT, diverging)
    assert state is S.DIAGNOSED and route.gate == 3
    agreeing = evidence_for(sig, RC.IMPLEMENTATION_DEFECT)
    agreeing["discriminatingExperiment"]["determinismReplay"] = replay(max_divergence=0.0)
    with pytest.raises(ValueError, match="excluded, not supported"):
        diagnose(S.FAILURE_RECORDED, sig, RC.IMPLEMENTATION_DEFECT, agreeing)
    unlocated = evidence_for(sig, RC.IMPLEMENTATION_DEFECT)
    unlocated["discriminatingExperiment"]["determinismReplay"] = replay(located=None)
    with pytest.raises(ValueError, match="defectLocated"):
        diagnose(S.FAILURE_RECORDED, sig, RC.IMPLEMENTATION_DEFECT, unlocated)
    missing = evidence_for(sig, RC.IMPLEMENTATION_DEFECT)
    del missing["discriminatingExperiment"]["determinismReplay"]
    with pytest.raises(ValueError, match="deterministic replay"):
        diagnose(S.FAILURE_RECORDED, sig, RC.IMPLEMENTATION_DEFECT, missing)
    # Naming optimization for a seed-sensitive run must now also exclude the implementation candidate.
    optimization = evidence_for(sig, RC.OPTIMIZATION_FAILURE)
    del optimization["discriminatingExperiment"]["excludes"]["rImplementationDefect"]
    with pytest.raises(ValueError, match="rImplementationDefect"):
        diagnose(S.FAILURE_RECORDED, sig, RC.OPTIMIZATION_FAILURE, optimization)


def test_every_added_candidate_adds_an_exclusion_duty():
    for signature in Sig:
        admissible = ADMISSIBLE_ROOT_CAUSES[signature]
        for root_cause in admissible:
            evidence = evidence_for(signature, root_cause)
            assert set(evidence["discriminatingExperiment"]["excludes"]) == {c.value for c in admissible if c is not root_cause}
