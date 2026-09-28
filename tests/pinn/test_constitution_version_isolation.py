"""A-0002 final closure review: GovernanceSemantics = f(constitutionVersion), not latest code on master.

Issue 1 -- a PROPOSED amendment must not change the effective Constitution's
runtime behaviour: 1.1 rejects every A-0002-only cell, 1.2 allows them only once
the version is effective, the direct API cannot bypass the gate, and PRELOCK's
version agrees with the runtime matrix.
Issue 2 -- several DiagnosisRecords on one failure: signature coverage invariant.
Issue 3 -- sSeedSensitive -> rSpecDefect only for unintended non-identifiability.
"""

from pathlib import Path

import pytest

from pinn.governance import locking
from pinn.governance.amendments import load_amendment_register, validate_amendment_register
from pinn.governance.prelock import PrelockPaths, declared_constitution_version, run_prelock
from pinn.governance.state_machine import (
    ADMISSIBLE_ROOT_CAUSES_BY_VERSION,
    NAMING_OBLIGATIONS_BY_VERSION,
    ROOT_CAUSE_GATE,
    SIGNATURE_EVIDENCE,
    ConstitutionVersionError,
    FailureSignature as Sig,
    IllegalTransition,
    RootCauseClass as RC,
    TriageRoute,
    WorkflowState as S,
    admissible_root_causes,
    diagnose,
    discriminating_experiment_errors,
    earliest_route,
    effective_constitution_versions,
    identifiability_errors,
    naming_obligations,
)
from pinn.governance.trust_loop import diagnosis_coverage_errors, validate_diagnosis_record

ROOT = Path(__file__).resolve().parents[2]
ART = {"artifactId": "art-1", "sha256": "b" * 64}
M11 = ADMISSIBLE_ROOT_CAUSES_BY_VERSION["1.1"]
M12 = ADMISSIBLE_ROOT_CAUSES_BY_VERSION["1.2"]
#: The eight A-0002 cells: in 1.2, not in 1.1.
A0002_CELLS = [(sig, cause) for sig in Sig for cause in M12[sig] if cause not in M11[sig]]
#: Constitution 1.1's matrix as accepted on 2026-09-15 (A-0001), frozen here so a
#: later edit of the runtime table cannot silently change 1.1 behaviour.
FROZEN_1_1 = {
    Sig.PDE_RESIDUAL: {RC.SPEC_DEFECT, RC.IMPLEMENTATION_DEFECT, RC.CAPACITY_LIMIT, RC.OPTIMIZATION_FAILURE, RC.SAMPLING_DEFICIENCY},
    Sig.BC_RESIDUAL: {RC.SPEC_DEFECT, RC.DATA_DEFECT, RC.IMPLEMENTATION_DEFECT, RC.OPTIMIZATION_FAILURE, RC.SAMPLING_DEFICIENCY},
    Sig.CONSERVATION: {RC.SPEC_DEFECT, RC.IMPLEMENTATION_DEFECT, RC.CAPACITY_LIMIT, RC.OPTIMIZATION_FAILURE, RC.SAMPLING_DEFICIENCY},
    Sig.PINN_CFD: {RC.SPEC_DEFECT, RC.DATA_DEFECT, RC.SINGULARITY_TREATMENT, RC.REFERENCE_DEFECT, RC.IMPLEMENTATION_DEFECT, RC.OPTIMIZATION_FAILURE},
    Sig.SEED_SENSITIVE: {RC.CAPACITY_LIMIT, RC.OPTIMIZATION_FAILURE, RC.SAMPLING_DEFICIENCY},
    Sig.LOCALIZED_ERROR: {RC.SINGULARITY_TREATMENT, RC.REFERENCE_DEFECT, RC.IMPLEMENTATION_DEFECT, RC.CAPACITY_LIMIT, RC.OPTIMIZATION_FAILURE, RC.SAMPLING_DEFICIENCY},
}


@pytest.fixture
def effective_1_2(monkeypatch):
    monkeypatch.setattr(locking, "SUPPORTED_CONSTITUTION_VERSIONS", ("1.0", "1.1", "1.2"))


@pytest.fixture
def proposed_state(monkeypatch):
    """Simulate the pre-acceptance runtime (A-0002 PROPOSED, 2026-09-15 morning): only 1.0 / 1.1 effective."""

    monkeypatch.setattr(locking, "SUPPORTED_CONSTITUTION_VERSIONS", ("1.0", "1.1"))


def excludes_for(version, signatures, root_cause):
    matrix = ADMISSIBLE_ROOT_CAUSES_BY_VERSION[version]
    return {cause.value: {"experiment": "P8", "observed": f"{cause.value} predicted a change that did not occur"}
            for sig in signatures for cause in matrix[sig] if cause is not root_cause}


def intervention(factor):
    control = {"capacity": "architecture", "sampling": "sampling"}[factor]
    return {"factor": factor, "changed": [control],
            "heldFixed": [c for c in ("architecture", "sampling", "optimizer", "lrSchedule", "lossWeights",
                                      "trainingBudget", "spec", "reference", "seedProtocol") if c != control],
            "levels": [{"level": f"L{i}", "seeds": 5, "medianError": m} for i, m in enumerate((0.04, 0.02, 0.01))],
            "optimizationDiagnosticsClean": True}


def identifiability(**overrides):
    result = {"ambiguityType": "nullspace", "claimRequiresUniqueEvaluation": True,
              "specResolvesAmbiguity": False, "ambiguityIntent": "unintended", "nullspaceProjectionFraction": 0.98}
    result.update(overrides)
    return result


def experiment(version, signature, root_cause, explained=()):
    signatures = [signature] + [s for s in explained if s is not signature]
    result = {"experimentId": "exp-001", "excludes": excludes_for(version, signatures, root_cause)}
    if root_cause is RC.CAPACITY_LIMIT:
        result["intervention"] = intervention("capacity")
    if root_cause is RC.SAMPLING_DEFICIENCY:
        result["intervention"] = intervention("sampling")
    if Sig.SEED_SENSITIVE in signatures and root_cause is RC.IMPLEMENTATION_DEFECT:
        result["determinismReplay"] = {"sameSeedRuns": 2, "maxDivergence": 0.03, "epsilonDet": 1e-10,
                                       "defectLocated": "dropout left enabled in eval mode"}
    if Sig.SEED_SENSITIVE in signatures and root_cause is RC.SPEC_DEFECT:
        result["identifiability"] = identifiability()
    return result


def evidence(version, signature, root_cause, explained=()):
    return {key: "artifact" for key in SIGNATURE_EVIDENCE[signature]} | {
        "discriminatingExperiment": experiment(version, signature, root_cause, explained)}


def record(version, signature, root_cause, *, observed=None, explained=None, diagnosis_id="dg-0001", **overrides):
    document = {
        "schemaVersion": "pinn.diagnosisRecord/1.0", "diagnosisId": diagnosis_id, "problemId": "pdef-poisson1d-v1.0",
        "revision": 1, "specHash": "a" * 64, "constitutionVersion": version, "problemClass": "forward",
        "signature": signature.value,
        "signatureEvidence": {key: ART for key in SIGNATURE_EVIDENCE[signature]},
        "rootCause": root_cause.value,
        "discriminatingExperiment": dict(experiment(version, signature, root_cause, explained or ()),
                                         evaluationSet="dev", evidencePointers=[ART]),
        "round": 1, "decidedBy": "captain", "decidedAt": "2026-09-15T00:00:00Z",
    }
    for key, value in document["discriminatingExperiment"]["excludes"].items():
        value["experiment"] = "P8"
    if observed is not None:
        document["observedSignatures"] = [s.value for s in observed]
    if explained is not None:
        document["explainedSignatures"] = [s.value for s in explained]
    document.update(overrides)
    return document


# ------------------------------------------------------------- Issue 1: version isolation

def test_the_real_runtime_has_1_2_effective_after_a0002():
    """A-0002 ACCEPTED 2026-09-15: the acceptance recipe added "1.2" to the supported versions and nothing else."""

    assert effective_constitution_versions() == ("1.0", "1.1", "1.2")
    assert set(ADMISSIBLE_ROOT_CAUSES_BY_VERSION) == {"1.1", "1.2"}
    assert len(A0002_CELLS) == 8


@pytest.mark.parametrize("signature,root_cause", A0002_CELLS)
def test_1_1_rejects_every_a0002_only_admissible_cell(signature, root_cause):
    """A run bound to Constitution 1.1 cannot name an A-0002 cell, in the state machine or in the document validator."""

    with pytest.raises(IllegalTransition, match="under Constitution 1.1"):
        diagnose(S.FAILURE_RECORDED, signature, root_cause, evidence("1.1", signature, root_cause), constitution_version="1.1")
    errors = validate_diagnosis_record(record("1.1", signature, root_cause))
    assert any("not admissible" in error and "Constitution 1.1" in error for error in errors)


@pytest.mark.parametrize("signature,root_cause", A0002_CELLS)
def test_1_2_allows_a0002_cells_after_dependency_and_effective_checks(signature, root_cause, effective_1_2):
    """Once "1.2" is effective (the acceptance recipe), the cells route to their Gate and the documents validate."""

    state, route = diagnose(S.FAILURE_RECORDED, signature, root_cause, evidence("1.2", signature, root_cause),
                            constitution_version="1.2")
    assert state is S.DIAGNOSED and route.gate == ROOT_CAUSE_GATE[root_cause]
    assert validate_diagnosis_record(record("1.2", signature, root_cause)) == []
    register = [{"amendmentId": "A-0001", "oldVersion": "1.0", "newVersion": "1.1", "status": "ACCEPTED", "effectiveDate": "2026-09-15"},
                {"amendmentId": "A-0002", "oldVersion": "1.1", "newVersion": "1.2", "status": "ACCEPTED", "effectiveDate": "2026-09-16",
                 "dependsOn": [{"amendmentId": "A-0001", "requiredStatus": "ACCEPTED", "requiredConstitutionVersion": "1.1"}]}]
    assert validate_amendment_register(register, constitution_version="1.2", effective_versions=("1.0", "1.1", "1.2")) == []


def test_proposed_a0002_does_not_change_1_1_behavior(proposed_state):
    """With A-0002 PROPOSED the 1.1 matrix and obligations are exactly what A-0001 accepted."""

    assert {sig: set(causes) for sig, causes in admissible_root_causes("1.1").items()} == FROZEN_1_1
    assert admissible_root_causes("1.1") is M11
    assert naming_obligations("1.1") == frozenset() and NAMING_OBLIGATIONS_BY_VERSION["1.1"] == frozenset()
    # Under 1.1 naming capacity for a PDE residual needs the excludes only: the A-0002 intervention is not owed.
    plain = evidence("1.1", Sig.PDE_RESIDUAL, RC.CAPACITY_LIMIT)
    del plain["discriminatingExperiment"]["intervention"]
    state, route = diagnose(S.FAILURE_RECORDED, Sig.PDE_RESIDUAL, RC.CAPACITY_LIMIT, plain, constitution_version="1.1")
    assert state is S.DIAGNOSED and route.gate == 4
    # ... and the 1.1 exclusion duty is the 1.1 candidate set, not the 1.2 one.
    errors = discriminating_experiment_errors(Sig.PINN_CFD, RC.SPEC_DEFECT, plain["discriminatingExperiment"] | {
        "excludes": excludes_for("1.1", [Sig.PINN_CFD], RC.SPEC_DEFECT)}, constitution_version="1.1")
    assert errors == []
    assert validate_diagnosis_record(record("1.1", Sig.PINN_CFD, RC.SPEC_DEFECT)) == []
    # Under 1.2 the same record would also have to exclude the two new sPinnCfd candidates.
    two_more = discriminating_experiment_errors(Sig.PINN_CFD, RC.SPEC_DEFECT, {"experimentId": "exp-1",
        "excludes": excludes_for("1.1", [Sig.PINN_CFD], RC.SPEC_DEFECT)}, constitution_version="1.2")
    assert two_more == ["Constitution 1.2 is not effective: its amendment is not ACCEPTED, so its matrix cannot be used "
                        "(effective versions ('1.0', '1.1'))"]


def test_direct_diagnosis_api_cannot_bypass_version_gating(proposed_state):
    """No default version, no future version, no unknown version -- in every entry point."""

    good = evidence("1.1", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY)
    with pytest.raises(TypeError):
        diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, good)  # type: ignore[call-arg]
    with pytest.raises(ConstitutionVersionError, match="not effective"):
        diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, good, constitution_version="1.2")
    with pytest.raises(ConstitutionVersionError, match="no admissible matrix"):
        diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, good, constitution_version="1.0")
    with pytest.raises(ConstitutionVersionError):
        admissible_root_causes("9.9")
    with pytest.raises(TypeError):
        admissible_root_causes(1.1)  # type: ignore[arg-type]
    assert discriminating_experiment_errors(Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, good["discriminatingExperiment"],
                                            constitution_version="1.2")[0].startswith("Constitution 1.2 is not effective")
    errors = validate_diagnosis_record(record("1.2", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY))
    assert errors == ["constitutionVersion: Constitution 1.2 is not effective: its amendment is not ACCEPTED, so its matrix "
                      "cannot be used (effective versions ('1.0', '1.1'))"]
    # A record without a version is rejected by the schema; a record bound to another version than the run is rejected too.
    missing = record("1.1", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY)
    del missing["constitutionVersion"]
    assert any("constitutionVersion" in error for error in validate_diagnosis_record(missing))
    assert any("bound to 1.1 but the run is bound to 1.0" in error for error in
               validate_diagnosis_record(record("1.1", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY), constitution_version="1.0"))
    assert validate_diagnosis_record(record("1.1", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY), constitution_version="1.1") == []


def test_prelock_version_and_runtime_matrix_agree():
    """PRELOCK: declared version is effective, the register chain ends there, and no PROPOSED version is effective."""

    result = run_prelock(PrelockPaths.defaults(ROOT))
    assert result["prelockStatus"] == "PASS" and result["checks"]["amendmentRegister"]["status"] == "PASS"
    declared = declared_constitution_version((ROOT / "governance/PINN_RESEARCH_CONSTITUTION.md").read_bytes())
    assert declared == "1.2" and declared in effective_constitution_versions() and declared in ADMISSIBLE_ROOT_CAUSES_BY_VERSION
    register = load_amendment_register(ROOT / "governance/AMENDMENTS")
    for entry in register:
        assert entry["newVersion"] in ADMISSIBLE_ROOT_CAUSES_BY_VERSION
        assert (entry["status"] == "ACCEPTED") == (entry["newVersion"] in effective_constitution_versions()), entry["amendmentId"]
    # R5: a PROPOSED amendment whose version is already effective is a leak; an ACCEPTED one that is not effective is a gap.
    proposed = [dict(entry) for entry in register]
    proposed[1].update(status="PROPOSED", effectiveDate="PENDING")
    leaked = validate_amendment_register(proposed, constitution_version="1.1", effective_versions=("1.0", "1.1", "1.2"))
    assert any("A-0002: PROPOSED" in error and "leaked" in error for error in leaked)
    gap = validate_amendment_register(register, constitution_version="1.2", effective_versions=("1.0", "1.1"))
    assert any("A-0002: ACCEPTED but Constitution 1.2 is not an effective runtime version" in error for error in gap)
    assert validate_amendment_register(register, constitution_version="1.2", effective_versions=effective_constitution_versions()) == []


# ------------------------------------------------------------- Issue 2: signature coverage

def test_two_signatures_two_root_causes_are_two_records_that_cover_everything(effective_1_2):
    observed = [Sig.PDE_RESIDUAL, Sig.LOCALIZED_ERROR]
    first = record("1.2", Sig.PDE_RESIDUAL, RC.OPTIMIZATION_FAILURE, observed=observed, diagnosis_id="dg-0001")
    second = record("1.2", Sig.LOCALIZED_ERROR, RC.SINGULARITY_TREATMENT, observed=observed, diagnosis_id="dg-0002")
    assert validate_diagnosis_record(first) == [] and validate_diagnosis_record(second) == []
    assert diagnosis_coverage_errors([first, second]) == []
    # rUndetermined for one of them still covers it (the line stops for that signature).
    stopped = record("1.2", Sig.LOCALIZED_ERROR, RC.UNDETERMINED, observed=observed, diagnosis_id="dg-0002")
    stopped["discriminatingExperiment"]["excludes"] = {}
    assert diagnosis_coverage_errors([first, stopped]) == []
    routes = [TriageRoute(Sig.PDE_RESIDUAL, RC.OPTIMIZATION_FAILURE, 4, S.IMPLEMENTATION_VERIFIED),
              TriageRoute(Sig.LOCALIZED_ERROR, RC.SINGULARITY_TREATMENT, 1, S.DRAFT)]
    assert earliest_route(routes).gate == 1
    with pytest.raises(TypeError):
        earliest_route([])


def test_a_signature_no_record_explains_is_a_coverage_failure(effective_1_2):
    observed = [Sig.PDE_RESIDUAL, Sig.LOCALIZED_ERROR, Sig.SEED_SENSITIVE]
    first = record("1.2", Sig.PDE_RESIDUAL, RC.OPTIMIZATION_FAILURE, observed=observed, diagnosis_id="dg-0001")
    second = record("1.2", Sig.LOCALIZED_ERROR, RC.SINGULARITY_TREATMENT, observed=observed, diagnosis_id="dg-0002")
    errors = diagnosis_coverage_errors([first, second])
    assert errors == ["diagnosisRecords: observed signatures ['sSeedSensitive'] are explained by no record (coverage must be 100%)"]
    assert diagnosis_coverage_errors([]) and diagnosis_coverage_errors("dg-0001")
    # Records that disagree about what was observed cannot be combined.
    other = record("1.2", Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE, observed=[Sig.SEED_SENSITIVE], diagnosis_id="dg-0003")
    assert any("same observedSignatures" in error for error in diagnosis_coverage_errors([first, second, other]))
    # A member bound to another Constitution version does not belong to the same failure.
    other_version = record("1.1", Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE, observed=observed, diagnosis_id="dg-0003")
    assert any("different (problemId, revision, specHash, constitutionVersion, round)" in error
               for error in diagnosis_coverage_errors([first, second, other_version]))
    # An invalid member fails the set before coverage is even considered.
    broken = record("1.2", Sig.SEED_SENSITIVE, RC.OPTIMIZATION_FAILURE, observed=observed, diagnosis_id="dg-0003")
    del broken["discriminatingExperiment"]["excludes"]["rCapacityLimit"]
    assert any(error.startswith("diagnosisRecords[2]: ") and "rCapacityLimit" in error
               for error in diagnosis_coverage_errors([first, second, broken]))


def test_conflicting_attribution_of_one_signature_is_refused(effective_1_2):
    observed = [Sig.PDE_RESIDUAL]
    first = record("1.2", Sig.PDE_RESIDUAL, RC.OPTIMIZATION_FAILURE, observed=observed, diagnosis_id="dg-0001")
    second = record("1.2", Sig.PDE_RESIDUAL, RC.SAMPLING_DEFICIENCY, observed=observed, diagnosis_id="dg-0002")
    errors = diagnosis_coverage_errors([first, second])
    assert len(errors) == 1 and "sPdeResidual is explained by several records ['dg-0001', 'dg-0002']" in errors[0]
    assert "rOptimizationFailure" in errors[0] and "rSamplingDeficiency" in errors[0] and "rUndetermined" in errors[0]


def test_one_record_may_explain_several_signatures_but_owes_the_union_of_exclusions(effective_1_2):
    observed = [Sig.LOCALIZED_ERROR, Sig.PINN_CFD]
    both = record("1.2", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, observed=observed, explained=observed)
    assert validate_diagnosis_record(both) == []
    assert diagnosis_coverage_errors([both]) == []
    narrow = record("1.2", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, observed=observed, explained=observed)
    narrow["discriminatingExperiment"]["excludes"] = excludes_for("1.2", [Sig.LOCALIZED_ERROR], RC.SAMPLING_DEFICIENCY)
    errors = validate_diagnosis_record(narrow)
    assert any("missing ['rDataDefect']" in error for error in errors)   # the only sPinnCfd-only candidate under 1.2
    # Picking the cheap signature alone leaves the other uncovered.
    cheap = record("1.2", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, observed=observed)
    assert any("['sPinnCfd'] are explained by no record" in error for error in diagnosis_coverage_errors([cheap]))
    # The state machine takes the same widening through evidence["explainedSignatures"].
    wide = evidence("1.2", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, explained=[Sig.PINN_CFD]) | {
        "explainedSignatures": [Sig.PINN_CFD]}
    assert diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, wide, constitution_version="1.2")[1].gate == 4
    short = dict(wide, discriminatingExperiment=experiment("1.2", Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY))
    with pytest.raises(ValueError, match="rDataDefect"):
        diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, short, constitution_version="1.2")
    with pytest.raises(TypeError):
        diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SAMPLING_DEFICIENCY, dict(wide, explainedSignatures=["sPinnCfd"]),
                 constitution_version="1.2")


# ------------------------------------------------------------- Issue 3: P34 / rSpecDefect

def test_neumann_poisson_absolute_claim_without_gauge_is_a_spec_defect(effective_1_2):
    state, route = diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.SPEC_DEFECT,
                            evidence("1.2", Sig.SEED_SENSITIVE, RC.SPEC_DEFECT), constitution_version="1.2")
    assert state is S.DIAGNOSED and route.gate == 1
    assert validate_diagnosis_record(record("1.2", Sig.SEED_SENSITIVE, RC.SPEC_DEFECT)) == []
    assert identifiability_errors(identifiability(ambiguityType="gauge", nullspaceProjectionFraction=None)) == []


@pytest.mark.parametrize("overrides,message", [
    ({"claimRequiresUniqueEvaluation": False, "ambiguityType": "branch"}, "legitimate multiplicity is not a spec defect"),
    ({"ambiguityIntent": "intended", "ambiguityType": "branch"}, "intended by the spec"),
    ({"specResolvesAmbiguity": True}, "already resolves the ambiguity"),
])
def test_legitimate_multiplicity_is_not_a_spec_defect(overrides, message, effective_1_2):
    """A branch-aware claim on a multi-branch nonlinear PDE, an intended multi-solution study, or a spec that fixes the gauge."""

    ev = evidence("1.2", Sig.SEED_SENSITIVE, RC.SPEC_DEFECT)
    ev["discriminatingExperiment"]["identifiability"] = identifiability(**overrides)
    with pytest.raises(ValueError, match=message):
        diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.SPEC_DEFECT, ev, constitution_version="1.2")
    document = record("1.2", Sig.SEED_SENSITIVE, RC.SPEC_DEFECT)
    document["discriminatingExperiment"]["identifiability"] = identifiability(**overrides)
    assert any(message in error for error in validate_diagnosis_record(document))


def test_undecided_ambiguity_stops_the_line_instead_of_naming_a_spec_defect(effective_1_2):
    ev = evidence("1.2", Sig.SEED_SENSITIVE, RC.SPEC_DEFECT)
    ev["discriminatingExperiment"]["identifiability"] = identifiability(ambiguityIntent="undecided")
    with pytest.raises(ValueError, match="name rUndetermined and stop the line"):
        diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.SPEC_DEFECT, ev, constitution_version="1.2")
    undetermined = evidence("1.2", Sig.SEED_SENSITIVE, RC.UNDETERMINED)
    undetermined["discriminatingExperiment"] = {"experimentId": "exp-P34"}
    assert diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.UNDETERMINED, undetermined, constitution_version="1.2") == (S.STOPPED_THE_LINE, None)
    missing = evidence("1.2", Sig.SEED_SENSITIVE, RC.SPEC_DEFECT)
    del missing["discriminatingExperiment"]["identifiability"]
    with pytest.raises(ValueError, match="requires a P34 identifiability record"):
        diagnose(S.FAILURE_RECORDED, Sig.SEED_SENSITIVE, RC.SPEC_DEFECT, missing, constitution_version="1.2")
    assert identifiability_errors({"ambiguityType": "fog", "claimRequiresUniqueEvaluation": "yes",
                                   "specResolvesAmbiguity": False, "ambiguityIntent": "maybe", "nullspaceProjectionFraction": 1.5})
    # The identifiability record is owed only when sSeedSensitive is among the explained signatures.
    plain = evidence("1.2", Sig.LOCALIZED_ERROR, RC.SPEC_DEFECT)
    assert "identifiability" not in plain["discriminatingExperiment"]
    assert diagnose(S.FAILURE_RECORDED, Sig.LOCALIZED_ERROR, RC.SPEC_DEFECT, plain, constitution_version="1.2")[1].gate == 1
