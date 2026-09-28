"""Claim-set identity follows the samples (2026-09-16 protocol clarification), fresh G5, G6 qualification, criterion."""

import copy
import math
from pathlib import Path

import pytest

from pinn.experiments import claim_metrics, criteria
from pinn.governance.canonical import canonical_sha256
from pinn.governance.claim_set_ledger import derive_claim_set_state, make_event, validate_claim_set_ledger
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set, sample_set_hash
from pinn.governance.trust_loop import validate_problem_definition
from pinn.governance.trust_vector import EnvironmentFingerprint, RunQualification, environment_id, independent_environments, reproduction_status, TrustStatus
from pinn.validation import fixtures as control_fixtures
from pinn.validation.poisson import evaluate_samples, load_candidate_protocol, sample_callable_fixture

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_trust_loop_documents import problem_definition, rehashed  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CODE = "c" * 64


def manifest(artifact_id, points, *, role="claim", generator="g", order=None):
    samples = [{"inputs": [p], "kind": "interior"} for p in (points if order is None else [points[i] for i in order])]
    return {"schemaVersion": "pinn.evaluationSet/1.0", "artifactId": artifact_id, "role": role, "inputNames": ["x"],
            "generator": {"generatorId": generator, "generatorVersion": "1"}, "samples": samples}


POINTS = [0.11, 0.37, 0.52, 0.83]


# --------------------------------------------------------------- identity

def test_same_samples_in_different_order_or_wrapping_share_one_sample_set_hash():
    a = manifest("set-claim-a", POINTS)
    b = manifest("set-claim-b", POINTS, generator="other", order=[3, 1, 0, 2])
    assert canonical_sha256(a) != canonical_sha256(b)
    assert sample_set_hash(a) == sample_set_hash(b)
    c = manifest("set-claim-c", POINTS[:3] + [0.84])
    assert sample_set_hash(c) != sample_set_hash(a)


def events_for(document, claim, *, sample_hash=None, open_it=True):
    kwargs = {} if sample_hash is None else {"sampleSetHash": sample_hash}
    events = [make_event(prev_event_id="GENESIS", problemId=document["problemId"], revision=1, specHash=document["specHash"],
                         claimSetSha256=claim, event="SEALED", actor="g", at="2026-09-16T00:00:00Z", **kwargs)]
    if open_it:
        events.append(make_event(prev_event_id=events[-1]["eventId"], problemId=document["problemId"], revision=1,
                                 specHash=document["specHash"], claimSetSha256=claim, event="OPENED", codeHash=CODE, actor="g",
                                 at="2026-09-16T01:00:00Z", **kwargs))
    return events


def test_rewrapped_samples_are_burnt_in_the_ledger_and_refused_by_the_spec():
    a = manifest("set-claim-a", POINTS)
    b = manifest("set-claim-b", POINTS, generator="other")
    document = problem_definition()
    h = sample_set_hash(a)
    events = events_for(document, canonical_sha256(a), sample_hash=h)
    # a second SEALED of the same samples under a new artifact at a new revision is refused
    resealed = events + [make_event(prev_event_id=events[-1]["eventId"], problemId=document["problemId"], revision=2,
                                    specHash=document["specHash"], claimSetSha256=canonical_sha256(b), event="SEALED", actor="g",
                                    at="2026-09-16T02:00:00Z", sampleSetHash=h)]
    assert any("re-wrapped claim set is not blind" in e for e in validate_claim_set_ledger(resealed))
    # legacy events without the field are caught through the manifest resolver
    legacy = events_for(document, canonical_sha256(a))
    legacy_reseal = legacy + [make_event(prev_event_id=legacy[-1]["eventId"], problemId=document["problemId"], revision=2,
                                         specHash=document["specHash"], claimSetSha256=canonical_sha256(b), event="SEALED", actor="g",
                                         at="2026-09-16T02:00:00Z")]
    assert validate_claim_set_ledger(legacy_reseal) == []                       # blind to identity without the resolver
    resolver = {canonical_sha256(a): h, canonical_sha256(b): sample_set_hash(b)}
    assert any("not blind" in e for e in validate_claim_set_ledger(legacy_reseal, sample_set_hashes=resolver))
    # the ProblemDefinition of revision 2 naming the re-wrapped set is refused when the manifest is supplied
    later = copy.deepcopy(document)
    later["revision"] = 2
    later["evaluationSets"]["claim"] = {"artifactId": "set-claim-b", "sha256": canonical_sha256(b)}
    later["evaluationSets"]["claimSetHistory"] = [{"sha256": canonical_sha256(a), "openedAtRevision": 1}]
    rehashed(later)
    train = manifest("set-train", [0.2, 0.6], role="train")
    dev = manifest("set-dev", [0.3], role="dev")
    later["evaluationSets"]["train"] = {"artifactId": "set-train", "sha256": canonical_sha256(train)}
    later["evaluationSets"]["dev"] = {"artifactId": "set-dev", "sha256": canonical_sha256(dev)}
    rehashed(later)
    seal_b = legacy + [make_event(prev_event_id=legacy[-1]["eventId"], problemId=document["problemId"], revision=2,
                                  specHash=later["specHash"], claimSetSha256=canonical_sha256(b), event="SEALED", actor="g",
                                  at="2026-09-16T02:00:00Z")]
    errors = validate_problem_definition(later, claim_set_events=seal_b, evaluation_sets={"train": train, "dev": dev, "claim": b})
    assert errors == []                                                       # without the resolver the legacy ledger hides it
    errors = validate_problem_definition(later, claim_set_events=seal_b, evaluation_sets={"train": train, "dev": dev, "claim": b},
                                         sample_set_hashes={canonical_sha256(a): h})
    assert any("re-wrapped" in e or "burnt" in e for e in errors)
    # a genuinely fresh sample set at revision 2 is allowed
    fresh = manifest("set-claim-fresh", [0.12, 0.41, 0.77])
    later["evaluationSets"]["claim"] = {"artifactId": "set-claim-fresh", "sha256": canonical_sha256(fresh)}
    rehashed(later)
    seal_fresh = legacy + [make_event(prev_event_id=legacy[-1]["eventId"], problemId=document["problemId"], revision=2,
                                      specHash=later["specHash"], claimSetSha256=canonical_sha256(fresh), event="SEALED", actor="g",
                                      at="2026-09-16T02:00:00Z", sampleSetHash=sample_set_hash(fresh))]
    assert validate_problem_definition(later, claim_set_events=seal_fresh, evaluation_sets={"train": train, "dev": dev, "claim": fresh},
                                       sample_set_hashes={canonical_sha256(a): h}) == []


def test_opened_sample_set_cannot_be_opened_again_under_another_artifact_and_binding_is_unique():
    a = manifest("set-claim-a", POINTS)
    b = manifest("set-claim-b", POINTS, generator="other")
    document = problem_definition()
    h = sample_set_hash(a)
    events = events_for(document, canonical_sha256(a), sample_hash=h)
    # SEALED of b slipped in without sampleSetHash, then OPENED with it: still refused by sample identity
    sneak = events + [make_event(prev_event_id=events[-1]["eventId"], problemId=document["problemId"], revision=2,
                                 specHash=document["specHash"], claimSetSha256=canonical_sha256(b), event="SEALED", actor="g", at="2026-09-16T02:00:00Z")]
    sneak.append(make_event(prev_event_id=sneak[-1]["eventId"], problemId=document["problemId"], revision=2, specHash=document["specHash"],
                            claimSetSha256=canonical_sha256(b), event="OPENED", codeHash=CODE, actor="g", at="2026-09-16T03:00:00Z", sampleSetHash=h))
    assert any("opened once, ever, by sample identity" in e for e in validate_claim_set_ledger(sneak))
    # one artifact bound to two sample identities is forged
    forged = events_for(document, canonical_sha256(a), sample_hash=h, open_it=False)
    forged.append(make_event(prev_event_id=forged[-1]["eventId"], problemId=document["problemId"], revision=1, specHash=document["specHash"],
                             claimSetSha256=canonical_sha256(a), event="OPENED", codeHash=CODE, actor="g", at="2026-09-16T01:00:00Z", sampleSetHash="9" * 64))
    assert any("bound to another sample identity" in e for e in validate_claim_set_ledger(forged))
    state = derive_claim_set_state(events, problem_id=document["problemId"], revision=1, claim_set_sha256=canonical_sha256(a))
    assert h in state.burnt_samples and state.burnt_sample_artifacts[h] == canonical_sha256(a)


def test_real_experiment_ledgers_reveal_the_reused_sample_set():
    import json

    a = json.loads((ROOT / "experiments/poisson1d/runs/exp1-calibration-r1/sets/claim.json").read_text(encoding="utf-8"))
    b = json.loads((ROOT / "experiments/poisson1d/runs/exp2-revised-r1/sets/claim.json").read_text(encoding="utf-8"))
    assert canonical_sha256(a) != canonical_sha256(b) and sample_set_hash(a) == sample_set_hash(b)
    events = json.loads((ROOT / "experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json").read_text(encoding="utf-8")) + \
        json.loads((ROOT / "experiments/poisson1d/ledger/pdef-poisson1d-cal-v1-exp2.json").read_text(encoding="utf-8"))
    # the two ledgers are separate chains; re-validate the second against the burnt samples of the first
    first = json.loads((ROOT / "experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json").read_text(encoding="utf-8"))
    second = json.loads((ROOT / "experiments/poisson1d/ledger/pdef-poisson1d-cal-v1-exp2.json").read_text(encoding="utf-8"))
    assert validate_claim_set_ledger(first) == [] and validate_claim_set_ledger(second) == []
    resolver = {canonical_sha256(a): sample_set_hash(a), canonical_sha256(b): sample_set_hash(b)}
    state = derive_claim_set_state(first, problem_id="pdef-poisson1d-cal-v1", revision=1, claim_set_sha256=canonical_sha256(a), sample_set_hashes=resolver)
    assert sample_set_hash(b) in state.burnt_samples          # exp2's claim set was burnt before it was opened


def test_claim_pool_members_are_mutually_disjoint_and_isolated():
    from pinn.experiments import datasets

    pytest.importorskip("numpy")
    pool = datasets.claim_pool_manifests({"GL640-CGL2400": (640, 2400), "GL768-CGL2800": (768, 2800)}, label="t")
    hashes = {name: sample_set_hash(doc) for name, doc in pool.items()}
    assert len(set(hashes.values())) == 2
    loaded = {f"claim": load_evaluation_set(pool["GL640-CGL2400"])}
    other = load_evaluation_set(pool["GL768-CGL2800"])
    assert not (set(loaded["claim"].identities) & set(other.identities))
    train = load_evaluation_set(manifest("set-train", [0.2, 0.6], role="train"))
    assert disjointness_errors({"train": train, "claim": loaded["claim"]}, min_separation=1e-9) == []


# --------------------------------------------------------------- criterion

def test_paired_intervention_criterion_requires_effect_and_consistency():
    seeds = [{"init": i, "sample": i, "batch": i} for i in range(10)]
    strong = [{"level": "L", "seedTriplets": seeds, "errors": [1e-2] * 10},
              {"level": "M", "seedTriplets": seeds, "errors": [4e-3] * 10},
              {"level": "H", "seedTriplets": seeds, "errors": [1e-3] * 10}]
    assert criteria.paired_intervention_errors(strong) == []
    weak = copy.deepcopy(strong)
    weak[2]["errors"] = [3e-3] * 10                                   # ratio 0.75, not < 0.5
    assert any("not below rho" in e for e in criteria.paired_intervention_errors(weak))
    inconsistent = copy.deepcopy(strong)
    inconsistent[2]["errors"] = [1e-3] * 7 + [5e-3] * 3               # median fine, only 7/10 improve
    assert any("q = 0.8" in e for e in criteria.paired_intervention_errors(inconsistent))
    unpaired = copy.deepcopy(strong)
    unpaired[1]["seedTriplets"] = [{"init": 99 + i} for i in range(10)]
    assert any("paired" in e for e in criteria.paired_intervention_errors(unpaired))
    few = copy.deepcopy(strong)
    for lvl in few:
        lvl["errors"] = lvl["errors"][:5]; lvl["seedTriplets"] = seeds[:5]
    assert any("at least 10" in e for e in criteria.paired_intervention_errors(few))
    # Experiment 2's historical numbers would NOT meet the strengthened rule (recorded, not applied retroactively)
    exp2 = [{"level": "4", "seedTriplets": seeds[:5], "errors": [3.41e-2, 1.19e-2, 2.29e-2, 4.29e-3, 2.89e-3]},
            {"level": "8", "seedTriplets": seeds[:5], "errors": [3.65e-3, 4.90e-4, 2.33e-4, 5.89e-4, 9.83e-4]},
            {"level": "16", "seedTriplets": seeds[:5], "errors": [5.09e-4, 4.34e-4, 3.96e-4, 1.12e-3, 4.83e-3]}]
    assert criteria.paired_intervention_errors(exp2)


# --------------------------------------------------------------- metrics

def test_claim_metrics_matches_trusted_validator_on_the_frozen_grids():
    protocol = load_candidate_protocol(ROOT)
    for fixture in control_fixtures.FIXTURES[:4]:
        samples = sample_callable_fixture(protocol, fixture.solution, fixture.first_derivative, fixture.second_derivative)
        try:
            trusted = evaluate_samples(protocol, samples)
        except Exception:
            continue
        ours = claim_metrics.evaluate_on_grids(
            gl_nodes=list(protocol.quadrature_nodes), gl_weights=list(protocol.quadrature_weights), cgl_nodes=list(protocol.pointwise_nodes),
            u_gl=list(samples.u_quadrature), du_gl=list(samples.du_quadrature), d2u_gl=list(samples.d2u_quadrature),
            u_cgl=list(samples.u_pointwise), u_boundary=list(samples.u_boundary), du_boundary=list(samples.du_boundary), grid_label="GL512-CGL2000")
        for key in trusted["metrics"]:
            assert ours["metrics"][key]["value"] == trusted["metrics"][key]["value"], (fixture.fixture_id, key)
        assert ours["failedMustCriteria"] == trusted["failedMustCriteria"]


# --------------------------------------------------------------- G6

def test_environment_qualification_rejects_renamed_or_duplicated_installations():
    a = {"machineId": "m", "osFamily": "windows", "acceleratorClass": "cpu-only", "frameworkVersion": "torch-2.12", "blasBackend": "mkl",
         "dependencyLockHash": "a" * 64, "installationId": "prefix-1"}
    same_renamed = {**a, "osVersion": "10.0.26200", "pythonVersion": "3.12.9"}
    fa, fb = EnvironmentFingerprint.from_mapping(a), EnvironmentFingerprint.from_mapping(same_renamed)
    assert not independent_environments(fa, fb) and environment_id(fa) == environment_id(fb)
    with pytest.raises(ValueError):
        EnvironmentFingerprint.from_mapping({**a, "hostname": "box-2"})       # a hostname is not identity
    independent = EnvironmentFingerprint.from_mapping({**a, "installationId": "prefix-2", "dependencyLockHash": "b" * 64})
    assert independent_environments(fa, independent)
    original = RunQualification(run_id="run-a", spec_hash="s" * 64, code_hash=CODE, environment_id=environment_id(fa), seed_set_id="1" * 64)
    same_env = RunQualification(run_id="run-b", spec_hash="s" * 64, code_hash=CODE, environment_id=environment_id(fb), seed_set_id="2" * 64)
    assert reproduction_status(original, same_env, within_tolerance=True).status is TrustStatus.BLOCKED
    fake = RunQualification(run_id="run-c", spec_hash="s" * 64, code_hash=CODE, environment_id="f" * 64, seed_set_id="2" * 64)
    # a hand-written environment id is not derivable from any fingerprint; the validator recomputes it (test_trust_loop_adversarial)
    assert fake.environment_id != environment_id(fa)
    good = RunQualification(run_id="run-d", spec_hash="s" * 64, code_hash=CODE, environment_id=environment_id(independent), seed_set_id="2" * 64)
    assert reproduction_status(original, good, within_tolerance=True).status is TrustStatus.PASS
    assert reproduction_status(original, good, within_tolerance=False).status is TrustStatus.FAIL
