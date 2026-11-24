"""A-0001 v1.1 adversarial closure audit (2026-09-15).

Each test is an Agent that obeys the schemas and tries to reach a higher claim
level than its evidence licenses.  Every path must be closed by a validator,
not by a sentence in the amendment.
"""

import copy

import pytest

from pinn.governance.canonical import canonical_sha256
from pinn.governance.claim_set_ledger import make_event
from pinn.governance.trust_loop import (
    code_hash_from_manifest,
    validate_claim_gate_decision,
    validate_diagnosis_record,
    validate_problem_definition,
    validate_run_record,
    validate_trust_vector,
)
from pinn.governance.trust_vector import EnvironmentFingerprint, environment_id, seed_set_id
from test_trust_loop_documents import (
    ART,
    CLAIM,
    CODE,
    ENV_A,
    ENV_B,
    checks_for,
    decision,
    ledger,
    opened_definition,
    problem_definition,
    rehashed,
    run_records,
    trust_vector,
    validated,
)


# ------------------------------------------------------------- applicability

def test_all_not_applicable_checks_are_an_illegal_registration_in_a_vector():
    vector = trust_vector(physics="PASS")
    vector["dimensions"]["physics"]["checks"] = [
        {"checkId": "PH1-fluxBalance", "applicability": "NOT_APPLICABLE", "reason": "claims not to owe it"},
        {"checkId": "PH4-symmetry", "applicability": "NOT_APPLICABLE", "reason": "claims not to owe it"},
        {"checkId": "PH10-momentumBudget", "applicability": "NOT_APPLICABLE", "reason": "scalar"},
    ]
    errors = validate_trust_vector(vector)
    assert any("INV-A1" in error for error in errors)
    vector["dimensions"]["physics"]["status"] = "NOT_CHECKED"
    for key in ("evidencePointers", "judgedAt", "judgedBy"):
        del vector["dimensions"]["physics"][key]
    assert any("executed no check" in error for error in validate_trust_vector(vector))


def test_all_not_applicable_is_refused_at_spec_level_too():
    document = problem_definition()
    for entry in document["checkApplicability"]:
        if entry["dimension"] == "physics":
            entry["applicability"] = "NOT_APPLICABLE"
            entry["reason"] = "declared exempt"
    errors = validate_problem_definition(rehashed(document))
    assert any("INV-A1" in error and "physics" in error for error in errors)


def test_hiding_a_failing_check_behind_not_applicable_is_caught_by_the_frozen_registry():
    document = problem_definition()
    vector = trust_vector(document, physics="PASS")
    vector["dimensions"]["physics"]["checks"] = [
        {"checkId": "PH1-fluxBalance", "applicability": "APPLICABLE", "status": "PASS", "evidencePointers": [ART]},
        {"checkId": "PH4-symmetry", "applicability": "NOT_APPLICABLE", "reason": "asymmetric case (it failed)"},
        {"checkId": "PH10-momentumBudget", "applicability": "NOT_APPLICABLE", "reason": "scalar"},
    ]
    assert validate_trust_vector(vector) == []                       # self-consistent on its own
    errors = validate_trust_vector(vector, document)                 # but not against the frozen spec
    assert any("PH4-symmetry" in error and "fixed at SPEC_LOCKED" in error for error in errors)


def test_a_required_check_cannot_silently_disappear_and_unregistered_checks_do_not_count():
    document = problem_definition()
    vector = trust_vector(document, physics="PASS")
    vector["dimensions"]["physics"]["checks"] = [
        {"checkId": "PH1-fluxBalance", "applicability": "APPLICABLE", "status": "PASS", "evidencePointers": [ART]},
        {"checkId": "PH10-momentumBudget", "applicability": "NOT_APPLICABLE", "reason": "scalar"},
    ]
    errors = validate_trust_vector(vector, document)
    assert any("PH4-symmetry" in error and "silently omitted" in error for error in errors)
    vector["dimensions"]["physics"]["checks"].append(
        {"checkId": "PH99-looksGood", "applicability": "APPLICABLE", "status": "PASS"})
    assert any("PH99-looksGood" in error and "not registered" in error for error in validate_trust_vector(vector, document))


def test_an_executed_dimension_without_checks_cannot_claim_pass():
    vector = trust_vector()
    del vector["dimensions"]["train"]["checks"]
    assert any("must show the checks" in error for error in validate_trust_vector(vector))


def test_changing_applicability_changes_the_spec_hash():
    document = problem_definition()
    before = document["specHash"]
    document["checkApplicability"][4]["applicability"] = "APPLICABLE"
    document["checkApplicability"][4]["reason"] = ""
    assert any("specHash" in error for error in validate_problem_definition(document))
    assert rehashed(document)["specHash"] != before


# ---------------------------------------------------------- dataset isolation

def manifest(role, points, artifact):
    return {"schemaVersion": "pinn.evaluationSet/1.0", "artifactId": artifact, "role": role, "inputNames": ["x"],
            "samples": [{"inputs": [point], "kind": "interior"} for point in points]}


def spec_with_sets(train, dev, claim, *, min_separation=None):
    document = problem_definition()
    manifests = {"train": manifest("train", train, "set-train"), "dev": manifest("dev", dev, "set-dev"),
                 "claim": manifest("claim", claim, "set-claim")}
    for role, item in manifests.items():
        document["evaluationSets"][role] = {"artifactId": item["artifactId"], "sha256": canonical_sha256(item)}
    if min_separation is not None:
        document["evaluationSets"]["minSeparation"] = min_separation
    return rehashed(document), manifests


def test_distinct_hashes_with_overlapping_samples_fail_the_spec():
    document, manifests = spec_with_sets([0.1, 0.2, 0.3], [0.4, 0.5], [0.1, 0.6])
    assert validate_problem_definition(document) == []                       # hashes alone look fine
    errors = validate_problem_definition(document, evaluation_sets=manifests)
    assert any("train and claim share 1 sample" in error for error in errors)


def test_manifests_must_hash_to_the_registered_artifacts():
    document, manifests = spec_with_sets([0.1], [0.4], [0.6])
    manifests["claim"]["samples"].append({"inputs": [0.1], "kind": "interior"})
    errors = validate_problem_definition(document, evaluation_sets=manifests)
    assert any("claim.sha256" in error for error in errors)
    del manifests["dev"]
    assert any("dev: manifest not supplied" in error for error in validate_problem_definition(document, evaluation_sets=manifests))


def test_near_duplicates_are_caught_only_through_the_preregistered_separation():
    loose, manifests = spec_with_sets([0.1], [0.4], [0.1 + 1e-12])
    assert validate_problem_definition(loose, evaluation_sets=manifests) == []
    strict, manifests = spec_with_sets([0.1], [0.4], [0.1 + 1e-12], min_separation=1e-6)
    assert any("minimum separation" in error for error in validate_problem_definition(strict, evaluation_sets=manifests))
    assert loose["specHash"] != strict["specHash"]


# --------------------------------------------------------------- claim sealing

def test_sealed_to_opened_to_sealed_is_rejected_with_and_without_the_ledger():
    document = problem_definition()
    document["evaluationSets"]["claimSetHistory"] = [{"sha256": CLAIM["sha256"], "openedAtRevision": 1}]
    errors = validate_problem_definition(rehashed(document))
    assert any("never sealed again" in error for error in errors)
    opened, events = opened_definition()
    resealed = copy.deepcopy(opened)
    resealed["evaluationSets"]["claimSetStatus"] = "SEALED"
    del resealed["evaluationSets"]["claimSetOpenedAtRevision"]
    resealed["evaluationSets"]["claimSetHistory"] = []
    rehashed(resealed)
    errors = validate_problem_definition(resealed, claim_set_events=events)
    assert any("ledger derives OPENED" in error for error in errors)
    assert any("claimSetHistory" in error for error in errors)


def test_deleting_the_opened_event_from_the_ledger_is_detected():
    opened, events = opened_definition()
    forged = [events[0]]
    errors = validate_problem_definition(opened, claim_set_events=forged)
    assert any("ledger derives SEALED" in error for error in errors)
    rewritten = copy.deepcopy(events)
    rewritten[1]["event"] = "SEALED"
    assert any("claimSetLedger" in error for error in validate_problem_definition(opened, claim_set_events=rewritten))


def test_an_opened_hash_cannot_be_reused_at_a_later_revision_even_with_a_clean_looking_document():
    opened, events = opened_definition()
    later = copy.deepcopy(opened)
    later["revision"] = 2
    later["evaluationSets"]["claimSetStatus"] = "SEALED"
    del later["evaluationSets"]["claimSetOpenedAtRevision"]
    later["evaluationSets"]["claimSetHistory"] = []
    rehashed(later)
    events2 = events + [make_event(prev_event_id=events[-1]["eventId"], problemId=later["problemId"], revision=2,
                                   specHash=later["specHash"], claimSetSha256=CLAIM["sha256"], event="SEALED",
                                   actor="governance", at="2026-09-15T00:00:00Z")]
    errors = validate_problem_definition(later, claim_set_events=events2)
    assert any("claimSetLedger" in error and "burnt" in error for error in errors)


# ------------------------------------------------------ environment / C3 runs

def test_fake_environment_ids_and_renamed_seed_sets_do_not_count():
    pd, events = opened_definition()
    runs = run_records(5, spec=pd["specHash"])
    runs[1]["environmentId"] = "f" * 64
    errors = validated({}, ("C0", "C1", "C2", "C3"), c2_runs=runs)
    assert any("environmentId: does not recompute" in error for error in errors)
    runs = run_records(5, spec=pd["specHash"], seeds=[[1, 2, 3]] * 5)
    for index, run in enumerate(runs):
        run["seedSetId"] = seed_set_id([1, 2, 3])
    errors = validated({}, ("C0", "C1", "C2", "C3"), c2_runs=runs)
    assert any("distinct seed set" in error for error in errors)
    runs = run_records(5, spec=pd["specHash"], seeds=[[1, 2, 3], [3, 2, 1], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
    errors = validated({}, ("C0", "C1", "C2", "C3"), c2_runs=runs)
    assert any("distinct seed set" in error for error in errors)


def test_same_machine_same_installation_with_a_new_hostname_is_one_environment():
    pd, events = opened_definition()
    hostnames = ({**ENV_A}, {**ENV_A, "osVersion": "11.0.99999", "pythonVersion": "3.12.9"})
    runs = run_records(5, environments=hostnames, spec=pd["specHash"])
    errors = validated({}, ("C0", "C1", "C2", "C3"), c2_runs=runs)
    assert any("only 1 distinct environment" in error for error in errors)
    independent = run_records(5, environments=({**ENV_A}, {**ENV_A, "installationId": "venv-2"}), spec=pd["specHash"])
    assert validated({}, ("C0", "C1", "C2", "C3"), c2_runs=independent) == []


def test_runs_of_another_code_identity_do_not_count_for_c3():
    pd, events = opened_definition()
    runs = run_records(3, spec=pd["specHash"]) + run_records(2, spec=pd["specHash"], code="d" * 64)
    for index, run in enumerate(runs[3:], start=3):
        run["runId"] = f"run-{index}"
    errors = validated({}, ("C0", "C1", "C2", "C3"), c2_runs=runs)
    assert any("different spec or code identity" in error for error in errors)


def test_qualified_runs_must_match_the_registered_run_records():
    pd, events = opened_definition()
    vector = trust_vector(pd)
    runs = run_records(5, spec=pd["specHash"])
    registry = {run["runId"]: dict(run) for run in runs}
    document = decision(vector, ("C0", "C1", "C2", "C3"), document=pd, events=events, c2_runs=runs)
    assert validate_claim_gate_decision(document, vector, pd, claim_set_events=events, run_records=registry) == []
    registry["run-2"]["seeds"] = [99]
    errors = validate_claim_gate_decision(document, vector, pd, claim_set_events=events, run_records=registry)
    assert any("run-2" not in error and "seeds: differ" in error for error in errors)
    del registry["run-4"]
    errors = validate_claim_gate_decision(document, vector, pd, claim_set_events=events, run_records=registry)
    assert any("not a registered run record" in error for error in errors)


def test_run_record_identities_are_derived():
    manifest = [{"path": "src/residual.py", "sha256": "1" * 64}, {"path": "configs/train.yaml", "sha256": "2" * 64}]
    record = {
        "schemaVersion": "pinn.runRecord/1.0", "runId": "run-7", "problemId": "pdef-poisson1d-v1.0", "revision": 1,
        "specHash": "a" * 64, "codeHash": code_hash_from_manifest(manifest), "codeManifest": manifest,
        "environment": dict(ENV_A), "environmentId": environment_id(EnvironmentFingerprint.from_mapping(ENV_A)),
        "seeds": [1, 2, 3], "seedSetId": seed_set_id([1, 2, 3]),
        "startedAt": "2026-09-14T00:00:00Z", "finishedAt": "2026-09-14T01:00:00Z", "executedBy": "runner",
    }
    assert validate_run_record(record) == []
    assert code_hash_from_manifest(list(reversed(manifest))) == record["codeHash"]
    tampered = dict(record, codeHash="9" * 64)
    assert any("codeHash: does not recompute" in error for error in validate_run_record(tampered))
    assert any("environmentId" in error for error in validate_run_record(dict(record, environmentId="9" * 64)))
    assert any("seedSetId" in error for error in validate_run_record(dict(record, seedSetId="9" * 64)))
    assert any("finishedAt" in error for error in validate_run_record(dict(record, finishedAt="2026-09-13T00:00:00Z")))
    with_hostname = dict(record, environment={**ENV_A, "hostname": "box"})
    assert validate_run_record(with_hostname)


# -------------------------------------------------------- adversarial closure

def test_reference_evidence_level_cannot_be_relabelled_at_decision_time():
    errors = validated({"referenceEvidenceLevel": "B"}, ("C0", "C1", "C2"))
    assert any("not re-labelled" in error for error in errors)


def test_code_changed_after_the_claim_set_was_opened_needs_a_new_revision():
    pd, events = opened_definition()
    vector = trust_vector(pd)
    document = decision(vector, ("C0", "C1", "C2"), document=pd, events=events, code="d" * 64)
    errors = validate_claim_gate_decision(document, vector, pd, claim_set_events=events)
    assert any("code changed after the claim set was seen" in error for error in errors)


def test_a_decision_must_cite_the_ledger_head_and_an_opened_claim_set():
    errors = validated({"ledgerHead": "e" * 64}, ("C0", "C1", "C2"))
    assert any("ledgerHead" in error for error in errors)
    pd = problem_definition()
    sealed_only = ledger(pd)
    vector = trust_vector(pd)
    document = decision(vector, ("C0", "C1", "C2"), document=pd, events=sealed_only)
    errors = validate_claim_gate_decision(document, vector, pd, claim_set_events=sealed_only)
    assert any("no OPENED event" in error for error in errors)
    low = trust_vector(pd, physics="NOT_CHECKED", external="NOT_CHECKED", repro="NOT_CHECKED")
    document = decision(low, ("C0", "C1"), document=pd, events=sealed_only)
    assert validate_claim_gate_decision(document, low, pd, claim_set_events=sealed_only) == []
    document = decision(low, ("C0", "C1"), document=pd, events=[])
    document["ledgerHead"] = "e" * 64
    errors = validate_claim_gate_decision(document, low, pd, claim_set_events=[])
    assert any("no SEALED event" in error for error in errors)


def test_manual_override_can_only_go_down():
    pd, events = opened_definition()
    vector = trust_vector(pd, physics="PARTIAL")
    vector["dimensions"]["physics"]["checks"] = checks_for("physics", "PASS")
    errors = validate_claim_gate_decision(decision(vector, ("C0", "C1"), document=pd, events=events), vector, pd,
                                          claim_set_events=events)
    assert errors == []
    upward = trust_vector(pd, physics="PASS")
    upward["dimensions"]["physics"]["checks"] = checks_for("physics", "PARTIAL")
    errors = validate_claim_gate_decision(decision(upward, ("C0", "C1", "C2"), document=pd, events=events), upward, pd,
                                          claim_set_events=events)
    assert any("above the meet" in error for error in errors)


def test_the_vector_must_belong_to_the_same_revision_and_spec_as_the_decision():
    pd, events = opened_definition()
    vector = trust_vector(pd)
    vector["revision"] = 2
    errors = validate_claim_gate_decision(decision(vector, ("C0", "C1", "C2"), document=pd, events=events), vector, pd,
                                          claim_set_events=events)
    assert any("revision: differs from the problem definition" in error for error in errors)


# -------------------------------------------------------------- diagnosis

@pytest.fixture
def effective_1_2(monkeypatch):
    """The diagnosis fixtures are A-0002 (1.2) records; simulate the amendment being ACCEPTED."""

    from pinn.governance import locking
    monkeypatch.setattr(locking, "SUPPORTED_CONSTITUTION_VERSIONS", ("1.0", "1.1", "1.2"))


def diagnosis(root_cause="rSamplingDeficiency", **overrides):
    excludes = {cause: {"experiment": "P11", "observed": "no change under local refinement"}
                for cause in ("rSingularityTreatment", "rReferenceDefect", "rImplementationDefect",
                              "rCapacityLimit", "rOptimizationFailure", "rSamplingDeficiency", "rSpecDefect")
                if cause != root_cause}
    document = {
        "schemaVersion": "pinn.diagnosisRecord/1.0", "diagnosisId": "dg-0001", "problemId": "pdef-poisson1d-v1.0",
        "revision": 1, "specHash": "a" * 64, "constitutionVersion": "1.2", "problemClass": "forward",
        "signature": "sLocalizedError",
        "signatureEvidence": {"errorSpatialDistribution": ART, "samplingConfigDiff": ART},
        "rootCause": root_cause,
        "discriminatingExperiment": {"experimentId": "exp-001", "evaluationSet": "dev", "excludes": excludes,
                                     "intervention": {"factor": "sampling", "changed": ["sampling"],
                                                      "heldFixed": ["architecture", "optimizer", "lrSchedule", "lossWeights",
                                                                    "trainingBudget", "spec", "reference", "seedProtocol"],
                                                      "levels": [{"level": "1e4", "seeds": 5, "medianError": 0.041},
                                                                 {"level": "2.5e4", "seeds": 5, "medianError": 0.021},
                                                                 {"level": "5e4", "seeds": 5, "medianError": 0.011}]},
                                     "evidencePointers": [ART]},
        "round": 1, "decidedBy": "captain", "decidedAt": "2026-09-15T00:00:00Z",
    }
    document.update(overrides)
    return document


def test_diagnosis_record_needs_every_alternative_excluded(effective_1_2):
    assert validate_diagnosis_record(diagnosis()) == []
    assert validate_diagnosis_record(diagnosis(gate=4)) == []
    partial = diagnosis()
    del partial["discriminatingExperiment"]["excludes"]["rImplementationDefect"]
    assert any("rImplementationDefect" in error for error in validate_diagnosis_record(partial))
    assert any("Gate is derived" in error for error in validate_diagnosis_record(diagnosis(gate=3)))
    assert any("not admissible" in error for error in validate_diagnosis_record(diagnosis("rDataDefect")))
    assert validate_diagnosis_record(diagnosis("rSpecDefect", gate=1)) == []   # A-0002 cell
    assert any("requires" in error for error in validate_diagnosis_record(diagnosis(signatureEvidence={"errorSpatialDistribution": ART})))
    on_claim = diagnosis()
    on_claim["discriminatingExperiment"]["evaluationSet"] = "claim"
    assert validate_diagnosis_record(on_claim)
    undetermined = diagnosis("rUndetermined")
    undetermined["discriminatingExperiment"]["excludes"] = {}
    assert validate_diagnosis_record(undetermined) == []
    assert any("no Gate" in error for error in validate_diagnosis_record(diagnosis("rUndetermined", gate=1)))
    assert any("round" in error for error in validate_diagnosis_record(diagnosis(round=4)))



def test_diagnosis_record_scope_signatures_and_causal_evidence(effective_1_2):
    """A-0002 draft 2: forward scope in the schema, observed signatures bind the root cause, evidence is structural."""

    assert validate_diagnosis_record(diagnosis(problemClass="inverse"))
    record = diagnosis()
    del record["problemClass"]
    assert any("problemClass" in error for error in validate_diagnosis_record(record))
    # A record explains a subset of what was observed (draft 3): one record for the localized error is valid on its
    # own while sPinnCfd was also observed; whether sPinnCfd is explained is the coverage invariant's business.
    assert validate_diagnosis_record(diagnosis(observedSignatures=["sLocalizedError", "sPinnCfd"])) == []
    # Explaining a second signature with the same cause requires that cause to be admissible there too.
    errors = validate_diagnosis_record(diagnosis("rReferenceDefect", observedSignatures=["sLocalizedError", "sPdeResidual"],
                                                 explainedSignatures=["sPdeResidual"]))
    assert any("not admissible for sPdeResidual" in error for error in errors)
    assert any("were not observed" in error for error in
               validate_diagnosis_record(diagnosis(observedSignatures=["sLocalizedError"], explainedSignatures=["sPinnCfd"])))
    assert any("must include the primary" in error for error in
               validate_diagnosis_record(diagnosis(observedSignatures=["sPinnCfd"])))
    # Naming sampling without the controlled intervention is refused at the document level too.
    stripped = diagnosis()
    del stripped["discriminatingExperiment"]["intervention"]
    assert any("controlled sampling intervention" in error for error in validate_diagnosis_record(stripped))
    two_levels = diagnosis()
    two_levels["discriminatingExperiment"]["intervention"]["levels"] = two_levels["discriminatingExperiment"]["intervention"]["levels"][:2]
    assert any("at least 3 levels" in error for error in validate_diagnosis_record(two_levels))
    seed_record = diagnosis("rImplementationDefect", signature="sSeedSensitive",
                            signatureEvidence={"multiSeedStatistics": ART})
    seed_record["discriminatingExperiment"]["excludes"] = {
        cause: {"experiment": "P33", "observed": "replay diverged; other candidates excluded"}
        for cause in ("rCapacityLimit", "rOptimizationFailure", "rSamplingDeficiency", "rSpecDefect")}
    assert any("deterministic replay" in error for error in validate_diagnosis_record(seed_record))
    seed_record["discriminatingExperiment"]["determinismReplay"] = {
        "sameSeedRuns": 3, "maxDivergence": 0.02, "epsilonDet": 1e-10, "defectLocated": "worker RNG not reseeded"}
    assert validate_diagnosis_record(seed_record) == []
