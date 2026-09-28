"""Document contracts for the trust loop: structure by schema, everything else fail-closed in Python."""

import copy

import pytest

from pinn.governance.claim_set_ledger import make_event
from pinn.governance.trust_loop import (
    problem_definition_spec_hash,
    trust_vector_statuses,
    validate_claim_gate_decision,
    validate_problem_definition,
    validate_trust_vector,
)
from pinn.governance.trust_vector import (
    CLAIM_LEVELS,
    DIMENSIONS,
    RunQualification,
    TrustStatus,
    claim_gate,
    environment_id,
    EnvironmentFingerprint,
    seed_set_id,
)

ART = {"artifactId": "art-0001", "sha256": "0" * 64}
WHEN = "2026-09-14T00:00:00Z"
CODE = "b" * 64
TRAIN = {"artifactId": "set-train", "sha256": "1" * 64}
DEV = {"artifactId": "set-dev", "sha256": "2" * 64}
CLAIM = {"artifactId": "set-claim", "sha256": "3" * 64}
PROBLEM = "pdef-poisson1d-v1.0"

#: The frozen check registry of the fixture spec (INV-A1: every dimension has an APPLICABLE check).
REGISTRY = [
    {"checkId": "M1-fieldCount", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "T1-adFirstDerivative", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "seedProtocol", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "PH1-fluxBalance", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH4-symmetry", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH10-momentumBudget", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "scalar Poisson equation has no momentum variable"},
    {"checkId": "cfdAgreement", "dimension": "external", "applicability": "APPLICABLE"},
    {"checkId": "independentReproduction", "dimension": "repro", "applicability": "APPLICABLE"},
]

ENV_A = {"machineId": "machine-a", "osFamily": "windows", "acceleratorClass": "cpu-only",
         "frameworkVersion": "torch-2.4", "blasBackend": "openblas", "dependencyLockHash": "c" * 64,
         "installationId": "venv-a"}
ENV_B = {**ENV_A, "machineId": "machine-b", "osFamily": "linux", "installationId": "venv-b"}


def problem_definition():
    document = {
        "schemaVersion": "pinn.problemDefinition/1.2",
        "problemId": PROBLEM,
        "revision": 1,
        "pde": {
            "form": "strong",
            "transient": False,
            "equations": [
                {"name": "poisson", "expressionRef": ART, "independentVars": ["x"], "dependentVars": ["u"]},
            ],
        },
        "boundaryConditions": [
            {"name": "left", "type": "dirichlet", "regionRef": "x0", "expressionRef": ART, "enforcement": "soft"},
            {"name": "right", "type": "dirichlet", "regionRef": "x1", "expressionRef": ART, "enforcement": "soft"},
        ],
        "geometry": {
            "domainType": "interval",
            "dimension": 1,
            "regions": [
                {"id": "interior", "description": "0 < x < 1"},
                {"id": "x0", "description": "x = 0"},
                {"id": "x1", "description": "x = 1"},
            ],
        },
        "parameters": [{"name": "k", "value": 1.0, "unitRef": "1"}],
        "units": {"system": "nondimensional", "entries": [{"quantity": "length", "unit": "1", "symbolRef": "x"}]},
        "nondimensionalization": {
            "applied": True,
            "scales": [{"quantity": "length", "scaleValue": 1.0, "unitFrom": "m", "unitTo": "1"}],
        },
        "variables": [
            {"name": "x", "role": "independent", "domainRange": [0.0, 1.0], "unitRef": "1"},
            {"name": "u", "role": "dependent", "domainRange": [-2.0, 2.0], "unitRef": "1"},
        ],
        "referenceSolution": {
            "sources": [
                {"sourceId": "src-analytic", "method": "analytical", "evidenceLevel": "A",
                 "independenceDeclaration": True, "provenance": ART},
                {"sourceId": "src-fdm", "method": "numerical", "evidenceLevel": "B",
                 "independenceDeclaration": True, "provenance": ART},
            ],
            "primarySourceId": "src-analytic",
        },
        "checkApplicability": copy.deepcopy(REGISTRY),
        "preregistration": {"errorNorm": "relativeL2", "epsilonSpec": 1e-3, "seedRuns": 10,
                            "seedFactors": ["init", "sample", "batch"], "worstSeedFactor": 3.0, "dispersionLimit": 1.0},
        "evaluationSets": {
            "train": TRAIN,
            "dev": DEV,
            "claim": CLAIM,
            "claimSetStatus": "SEALED",
            "claimSetHistory": [],
        },
        "status": "FROZEN",
        "frozenAt": WHEN,
        "frozenBy": "captain",
    }
    document["specHash"] = problem_definition_spec_hash(document)
    return document


def rehashed(document):
    document["specHash"] = problem_definition_spec_hash(document)
    return document


def ledger(document, *, opened=False, code=CODE, claim=None, revision=None):
    """A SEALED event (and optionally the OPENED event) for the document's claim set."""

    claim = claim or document["evaluationSets"]["claim"]["sha256"]
    revision = revision or document["revision"]
    events = [make_event(prev_event_id="GENESIS", problemId=document["problemId"], revision=revision,
                         specHash=document["specHash"], claimSetSha256=claim, event="SEALED",
                         actor="governance", at="2026-09-14T00:00:00Z")]
    if opened:
        events.append(make_event(prev_event_id=events[-1]["eventId"], problemId=document["problemId"],
                                 revision=revision, specHash=document["specHash"], claimSetSha256=claim,
                                 event="OPENED", codeHash=code, actor="governance", at="2026-09-14T06:00:00Z"))
    return events


def opened_definition():
    """The fixture spec after its claim set was opened at revision 1, with the matching ledger."""

    document = problem_definition()
    document["evaluationSets"]["claimSetStatus"] = "OPENED"
    document["evaluationSets"]["claimSetOpenedAtRevision"] = 1
    document["evaluationSets"]["claimSetHistory"] = [{"sha256": CLAIM["sha256"], "openedAtRevision": 1}]
    rehashed(document)
    return document, ledger(document, opened=True)


def checks_for(dimension, status):
    """The registry's checks for ``dimension``, every applicable one at ``status``."""

    results = []
    for entry in REGISTRY:
        if entry["dimension"] != dimension:
            continue
        if entry["applicability"] == "APPLICABLE":
            results.append({"checkId": entry["checkId"], "applicability": "APPLICABLE", "status": status,
                            "evidencePointers": [ART]})
        else:
            results.append({"checkId": entry["checkId"], "applicability": "NOT_APPLICABLE", "reason": entry["reason"]})
    return results


def trust_vector(document=None, **statuses):
    document = document or problem_definition()
    dimensions = {}
    for dimension in DIMENSIONS:
        status = statuses.get(dimension, "PASS")
        entry = {"status": status}
        if status != "NOT_CHECKED":
            entry.update({"evidencePointers": [ART], "judgedAt": WHEN, "judgedBy": "gate-runner",
                          "checks": checks_for(dimension, status)})
            if dimension == "external":
                entry["evaluationSet"] = "claim"
                entry["claimSetSha256"] = document["evaluationSets"]["claim"]["sha256"]
        if status == "PARTIAL":
            entry["notes"] = "covered the in-domain check, missing the boundary refinement"
        dimensions[dimension] = entry
    return {
        "schemaVersion": "pinn.trustVector/1.2",
        "recordId": "tv-0001",
        "problemId": document["problemId"],
        "revision": document["revision"],
        "specHash": document["specHash"],
        "dimensions": dimensions,
    }


def run_records(count=5, environments=(ENV_A, ENV_B), spec=None, code=CODE, seeds=None):
    spec = spec or problem_definition()["specHash"]
    records = []
    for index in range(count):
        environment = environments[index % len(environments)]
        run_seeds = seeds[index] if seeds else [10 * index + 1, 10 * index + 2, 10 * index + 3]
        records.append({
            "runId": f"run-{index}", "specHash": spec, "codeHash": code, "environment": dict(environment),
            "environmentId": environment_id(EnvironmentFingerprint.from_mapping(environment)),
            "seeds": list(run_seeds), "seedSetId": seed_set_id(run_seeds),
        })
    return records


def decision(vector, allowed, *, document=None, events=None, level="A", run_mode="FORMAL", c2_runs=(),
             blocked=None, weakest=None, code=CODE):
    document = document or problem_definition()
    events = events if events is not None else ledger(document, opened=True, code=code)
    records = [RunQualification(run_id=r["runId"], spec_hash=r["specHash"], code_hash=r["codeHash"],
                                environment_id=r["environmentId"], seed_set_id=r["seedSetId"]) for r in c2_runs]
    gate = claim_gate(trust_vector_statuses(vector), evidence_level=level, c2_runs=records,
                      spec_hash=document["specHash"], code_hash=code, exploratory=run_mode == "EXPLORATORY")
    if blocked is None:
        blocked = tuple(item for item in CLAIM_LEVELS if item not in allowed)
    if weakest is None:
        weakest = {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value, "evidenceRef": ART}
    return {
        "schemaVersion": "pinn.claimGateDecision/1.2",
        "decisionId": "cgd-0001",
        "problemId": vector["problemId"],
        "revision": vector["revision"],
        "specHash": vector["specHash"],
        "codeHash": code,
        "claimSetSha256": document["evaluationSets"]["claim"]["sha256"],
        "ledgerHead": events[-1]["eventId"] if events else "GENESIS",
        "trustVectorRef": {"artifactId": vector["recordId"], "sha256": "b" * 64},
        "referenceEvidenceLevel": level,
        "runMode": run_mode,
        "qualifiedC2Runs": list(c2_runs),
        "allowedClaims": [
            {"level": item, "statementRef": ART, "evidenceRefs": [ART],
             "failureConditions": [{"condition": "reference solution revised", "consequence": "INVALIDATE_DECISION"}]}
            for item in allowed
        ],
        "blockedClaims": [{"level": item, "reason": "not licensed"} for item in blocked],
        "weakestLink": weakest,
        "generatedAt": WHEN,
        "decidedBy": "captain",
    }


def validated(document, allowed, *, level="A", run_mode="FORMAL", c2_runs=(), blocked=None, weakest=None,
              code=CODE, **statuses):
    """Build the opened spec + ledger + vector + decision and validate the decision."""

    pd, events = opened_definition()
    vector = trust_vector(pd, **statuses)
    doc = decision(vector, allowed, document=pd, events=events, level=level, run_mode=run_mode,
                   c2_runs=c2_runs, blocked=blocked, weakest=weakest, code=code)
    doc.update(document)
    return validate_claim_gate_decision(doc, vector, pd, claim_set_events=events)


# ------------------------------------------------------------ ProblemDefinition

def test_t01_minimal_poisson_definition_is_valid():
    assert validate_problem_definition(problem_definition()) == []


def test_t02_missing_pde_is_a_schema_error():
    document = problem_definition()
    del document["pde"]
    assert any("pde" in error for error in validate_problem_definition(document))


def test_t03_unknown_evidence_level_is_rejected():
    document = problem_definition()
    document["referenceSolution"]["sources"][0]["evidenceLevel"] = "E"
    assert any("evidenceLevel" in error for error in validate_problem_definition(rehashed(document)))


def test_t04_transient_problem_needs_initial_conditions():
    document = problem_definition()
    document["pde"]["transient"] = True
    assert any("initialConditions" in error for error in validate_problem_definition(rehashed(document)))
    document["initialConditions"] = [{"name": "ic", "regionRef": "interior", "expressionRef": ART}]
    assert validate_problem_definition(rehashed(document)) == []


def test_t05_at_least_one_dependent_variable():
    document = problem_definition()
    document["variables"][1]["role"] = "independent"
    errors = validate_problem_definition(rehashed(document))
    assert any("dependent" in error for error in errors)


def test_t06_spec_hash_must_be_hex64():
    document = problem_definition()
    document["specHash"] = "zzz"
    assert any("specHash" in error for error in validate_problem_definition(document))


def test_t07_region_references_must_resolve():
    document = problem_definition()
    document["boundaryConditions"][0]["regionRef"] = "edge-9"
    assert any("regionRef" in error for error in validate_problem_definition(rehashed(document)))


def test_t08_primary_source_must_be_registered():
    document = problem_definition()
    document["referenceSolution"]["primarySourceId"] = "src-missing"
    assert any("primarySourceId" in error for error in validate_problem_definition(rehashed(document)))


def test_t09_frozen_field_change_without_rehash_is_detected():
    document = problem_definition()
    document["parameters"][0]["value"] = 2.0
    assert any("specHash" in error for error in validate_problem_definition(document))
    assert validate_problem_definition(rehashed(document)) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d.__setitem__("extra", 1), "extra"),
    (lambda d: d["nondimensionalization"]["scales"][0].__setitem__("scaleValue", 0), "scaleValue"),
    (lambda d: d["variables"][0].__setitem__("domainRange", [1.0, 0.0]), "domainRange"),
    (lambda d: d["variables"][0].__setitem__("unitRef", "furlong"), "unitRef"),
    (lambda d: d.__delitem__("frozenBy"), "frozenBy"),
    (lambda d: d["pde"]["equations"][0]["dependentVars"].append("v"), "dependentVars"),
    (lambda d: d["pde"]["equations"][0].__setitem__("independentVars", ["u"]), "independentVars"),
    (lambda d: d["referenceSolution"]["sources"][1].__setitem__("sourceId", "src-analytic"), "unique"),
    (lambda d: d["referenceSolution"]["sources"][0].__setitem__("independenceDeclaration", False), "independenceDeclaration"),
    (lambda d: d.__delitem__("revision"), "revision"),
    (lambda d: d.__delitem__("checkApplicability"), "checkApplicability"),
    (lambda d: d.__delitem__("preregistration"), "preregistration"),
    (lambda d: d["preregistration"].__setitem__("epsilonSpec", 0), "epsilonSpec"),
    (lambda d: d["preregistration"].__setitem__("dispersionLimit", -1), "dispersionLimit"),
    (lambda d: d["evaluationSets"].__setitem__("minSeparation", 0), "minSeparation"),
])
def test_cross_field_rules_fail_closed(mutate, needle):
    document = problem_definition()
    mutate(document)
    errors = validate_problem_definition(rehashed(document))
    assert errors and any(needle in error for error in errors), errors


def test_spec_hash_covers_the_method_but_not_the_claim_set_state():
    """Opening the claim set or bumping the revision must not change the method identity; the sets you train on must."""

    document = problem_definition()
    before = document["specHash"]
    opened, _ = opened_definition()
    assert opened["specHash"] == before
    document["revision"] = 7
    assert problem_definition_spec_hash(document) == before
    document["evaluationSets"]["claim"] = {"artifactId": "set-claim-2", "sha256": "4" * 64}
    assert problem_definition_spec_hash(document) == before
    document["evaluationSets"]["train"] = {"artifactId": "set-train-2", "sha256": "5" * 64}
    assert problem_definition_spec_hash(document) != before


# ------------------------------------------------- evaluation-set discipline

def test_train_dev_claim_sets_must_be_distinct():
    document = problem_definition()
    document["evaluationSets"]["claim"] = dict(DEV)
    errors = validate_problem_definition(rehashed(document))
    assert any("distinct artifacts" in error for error in errors)


def test_opened_claim_set_is_recorded_for_the_current_revision():
    document = problem_definition()
    sets = document["evaluationSets"]
    sets["claimSetStatus"] = "OPENED"
    errors = validate_problem_definition(rehashed(document))
    assert any("claimSetOpenedAtRevision" in error for error in errors)
    assert any("claimSetHistory" in error for error in errors)
    sets["claimSetOpenedAtRevision"] = 1
    sets["claimSetHistory"] = [{"sha256": CLAIM["sha256"], "openedAtRevision": 1}]
    assert validate_problem_definition(rehashed(document)) == []


def test_a_claim_set_opened_for_an_earlier_revision_is_burnt():
    document = problem_definition()
    document["revision"] = 2
    document["evaluationSets"]["claimSetHistory"] = [{"sha256": CLAIM["sha256"], "openedAtRevision": 1}]
    errors = validate_problem_definition(rehashed(document))
    assert any("no longer blind" in error for error in errors)
    document["evaluationSets"]["claim"] = {"artifactId": "set-claim-v2", "sha256": "4" * 64}
    assert validate_problem_definition(rehashed(document)) == []


def test_sealed_claim_set_carries_no_open_revision_and_history_cannot_be_in_the_future():
    document = problem_definition()
    document["evaluationSets"]["claimSetOpenedAtRevision"] = 1
    assert any("only allowed while" in error for error in validate_problem_definition(rehashed(document)))
    document = problem_definition()
    document["evaluationSets"]["claimSetHistory"] = [{"sha256": "5" * 64, "openedAtRevision": 3}]
    assert any("later than the current" in error for error in validate_problem_definition(rehashed(document)))


def test_claim_set_state_is_derived_from_the_ledger():
    document = problem_definition()
    assert validate_problem_definition(document, claim_set_events=ledger(document)) == []
    assert any("no SEALED event" in error for error in validate_problem_definition(document, claim_set_events=[]))
    opened, events = opened_definition()
    assert validate_problem_definition(opened, claim_set_events=events) == []
    errors = validate_problem_definition(document, claim_set_events=events)
    assert any("ledger derives OPENED" in error for error in errors)


# ------------------------------------------------------------------ TrustVector

def test_t10_fully_judged_vector_is_valid():
    document = problem_definition()
    assert validate_trust_vector(trust_vector(document), document) == []
    assert validate_trust_vector(trust_vector(document)) == []
    assert trust_vector_statuses(trust_vector(document, train="PARTIAL"))["train"] is TrustStatus.PARTIAL


def test_t11_missing_dimension_is_rejected():
    vector = trust_vector()
    del vector["dimensions"]["physics"]
    assert any("physics" in error for error in validate_trust_vector(vector))


def test_t12_statuses_are_a_closed_enumeration():
    vector = trust_vector()
    vector["dimensions"]["train"]["status"] = "PASS_WITH_NOTES"
    assert any("PASS_WITH_NOTES" in error for error in validate_trust_vector(vector))


def test_t13_partial_must_explain_the_gap():
    vector = trust_vector(train="PARTIAL")
    vector["dimensions"]["train"]["notes"] = "   "
    assert any("notes" in error for error in validate_trust_vector(vector))


def test_not_checked_carries_no_judgement_and_judged_needs_evidence():
    vector = trust_vector(repro="NOT_CHECKED")
    assert validate_trust_vector(vector) == []
    vector["dimensions"]["repro"]["judgedBy"] = "someone"
    assert any("NOT_CHECKED" in error for error in validate_trust_vector(vector))
    judged = trust_vector()
    judged["dimensions"]["math"]["evidencePointers"] = []
    assert any("evidencePointers" in error for error in validate_trust_vector(judged))
    del judged["dimensions"]["math"]["judgedAt"]
    assert any("judgedAt" in error for error in validate_trust_vector(judged))


def test_perturbation_codes_follow_the_red_team_numbering_and_need_a_worst_case():
    vector = trust_vector()
    vector["dimensions"]["train"]["perturbationsRun"] = ["P2", "P15"]
    assert any("worstCase" in error for error in validate_trust_vector(vector))
    vector["dimensions"]["train"]["worstCase"] = "P15: worst seed 2.4e-3"
    assert validate_trust_vector(vector) == []
    vector["dimensions"]["train"]["perturbationsRun"] = ["seed-swap"]
    assert any("perturbationsRun" in error for error in validate_trust_vector(vector))


def test_external_can_only_pass_on_the_claim_set_it_names():
    vector = trust_vector()
    vector["dimensions"]["external"]["evaluationSet"] = "dev"
    del vector["dimensions"]["external"]["claimSetSha256"]
    assert any("claim set" in error for error in validate_trust_vector(vector))
    del vector["dimensions"]["external"]["evaluationSet"]
    assert any("claim set" in error for error in validate_trust_vector(vector))
    partial = trust_vector(external="PARTIAL")
    partial["dimensions"]["external"]["evaluationSet"] = "dev"
    del partial["dimensions"]["external"]["claimSetSha256"]
    assert validate_trust_vector(partial) == []
    unnamed = trust_vector()
    del unnamed["dimensions"]["external"]["claimSetSha256"]
    assert any("claimSetSha256" in error for error in validate_trust_vector(unnamed))
    other = trust_vector()
    other["dimensions"]["external"]["claimSetSha256"] = "9" * 64
    assert any("not the claim set" in error for error in validate_trust_vector(other, problem_definition()))


def test_dimension_status_must_be_the_meet_of_its_applicable_checks():
    vector = trust_vector(physics="PARTIAL")
    vector["dimensions"]["physics"]["checks"] = [
        {"checkId": "PH1-fluxBalance", "applicability": "APPLICABLE", "status": "PASS", "evidencePointers": [ART]},
        {"checkId": "PH4-symmetry", "applicability": "APPLICABLE", "status": "PARTIAL"},
        {"checkId": "PH10-momentumBudget", "applicability": "NOT_APPLICABLE", "reason": "scalar problem"},
    ]
    assert validate_trust_vector(vector, problem_definition()) == []
    vector["dimensions"]["physics"]["status"] = "PASS"
    assert any("above the meet" in error for error in validate_trust_vector(vector))
    vector["dimensions"]["physics"]["status"] = "FAIL"
    del vector["dimensions"]["physics"]["notes"]
    assert any("manual downgrade must be explained" in error for error in validate_trust_vector(vector))
    vector["dimensions"]["physics"]["notes"] = "auditor holds physics at FAIL: PH4 asymmetry exceeds the band"
    assert validate_trust_vector(vector) == []


def test_not_applicable_is_not_a_status():
    vector = trust_vector(physics="NOT_CHECKED")
    checks = [{"checkId": "PH10-momentumBudget", "applicability": "NOT_APPLICABLE", "reason": "scalar problem"}]
    vector["dimensions"]["physics"]["checks"] = checks
    assert any("NOT_CHECKED dimension has executed no check" in error for error in validate_trust_vector(vector))
    vector = trust_vector(physics="PASS")
    vector["dimensions"]["physics"]["checks"] = [dict(checks[0], status="PASS")]
    assert any("carries no status" in error for error in validate_trust_vector(vector))
    vector["dimensions"]["physics"]["checks"] = [{"checkId": "PH10-momentumBudget", "applicability": "NOT_APPLICABLE"}]
    assert any("reason" in error for error in validate_trust_vector(vector))
    vector["dimensions"]["physics"]["checks"] = [{"checkId": "PH1-fluxBalance", "applicability": "APPLICABLE"}]
    assert any("status: required" in error for error in validate_trust_vector(vector))
    vector["dimensions"]["physics"]["checks"] = [{"checkId": "x", "applicability": "NOT_APPLICABLE", "status": "NOT_APPLICABLE"}]
    assert any("NOT_APPLICABLE" in error for error in validate_trust_vector(vector))


# ------------------------------------------------------------ ClaimGateDecision

def test_consistent_decision_is_valid():
    assert validated({}, ("C0", "C1", "C2")) == []


def test_t19_c2_with_level_d_reference_is_refused():
    pd, events = opened_definition()
    pd["referenceSolution"]["primarySourceId"] = "src-d"
    pd["referenceSolution"]["sources"].append({"sourceId": "src-d", "method": "published", "evidenceLevel": "D",
                                               "independenceDeclaration": True, "provenance": ART})
    rehashed(pd)
    events = ledger(pd, opened=True)
    vector = trust_vector(pd)
    errors = validate_claim_gate_decision(decision(vector, ("C0", "C1", "C2"), document=pd, events=events, level="D"),
                                          vector, pd, claim_set_events=events)
    assert any("C2" in error and "not licensed" in error for error in errors)


def test_t21_weakest_link_is_derived_not_declared():
    errors = validated({"weakestLink": {"dimensions": ["math"], "status": "PASS", "evidenceRef": ART}},
                       ("C0", "C1"), external="FAIL")
    assert any("weakestLink.status" in error for error in errors)
    assert any("weakestLink.dimensions" in error for error in errors)


def test_t22_c3_needs_independently_qualified_runs():
    pd, events = opened_definition()
    assert any("C3" in error for error in validated({}, ("C0", "C1", "C2", "C3")))
    assert validated({}, ("C0", "C1", "C2", "C3"), c2_runs=run_records(5, spec=pd["specHash"])) == []
    single = validated({}, ("C0", "C1", "C2", "C3"), c2_runs=run_records(5, environments=(ENV_A,), spec=pd["specHash"]))
    assert any("environment" in error for error in single)


def test_allowed_claims_may_be_stricter_but_never_looser_than_the_calculus():
    assert validated({}, ("C0",), train="PARTIAL") == []
    errors = validated({}, ("C0", "C1"), train="PARTIAL")
    assert any("C1" in error and "train=PARTIAL" in error for error in errors)
    assert validated({}, ("C0",)) == []


def test_every_level_needs_a_verdict_and_only_one():
    missing = validated({}, ("C0", "C1", "C2"), blocked=())
    assert any("neither allowed nor blocked" in error for error in missing)
    double = validated({}, ("C0", "C1", "C2"), blocked=("C2", "C3"))
    assert any("both allowed and blocked" in error for error in double)


def test_levels_are_closed_to_c0_c3():
    pd, events = opened_definition()
    vector = trust_vector(pd)
    document = decision(vector, ("C0",), document=pd, events=events)
    document["blockedClaims"].append({"level": "C4", "reason": "out of scope"})
    assert any("C4" in error for error in validate_claim_gate_decision(document, vector, pd, claim_set_events=events))


def test_exploratory_mode_caps_at_c1():
    assert any("EXPLORATORY" in error for error in validated({}, ("C0", "C1", "C2"), run_mode="EXPLORATORY"))
    assert validated({}, ("C0", "C1"), run_mode="EXPLORATORY") == []


def test_decision_must_bind_the_same_vector_and_spec():
    errors = validated({"trustVectorRef": {"artifactId": "tv-9999", "sha256": "b" * 64}, "specHash": "c" * 64},
                       ("C0", "C1", "C2"))
    assert any("trustVectorRef" in error for error in errors)
    assert any("specHash" in error for error in errors)


def test_invalid_vector_invalidates_the_decision():
    pd, events = opened_definition()
    vector = trust_vector(pd)
    document = decision(vector, ("C0", "C1", "C2"), document=pd, events=events)
    broken = copy.deepcopy(vector)
    broken["dimensions"]["math"]["status"] = "MAYBE"
    assert any(error.startswith("trustVector:") for error in
               validate_claim_gate_decision(document, broken, pd, claim_set_events=events))


def test_invalid_spec_invalidates_the_decision():
    pd, events = opened_definition()
    vector = trust_vector(pd)
    document = decision(vector, ("C0", "C1", "C2"), document=pd, events=events)
    pd["preregistration"]["epsilonSpec"] = 0
    rehashed(pd)
    assert any(error.startswith("problemDefinition:") for error in
               validate_claim_gate_decision(document, vector, pd, claim_set_events=events))
