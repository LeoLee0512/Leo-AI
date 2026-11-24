"""R3 minimal runner: the pure-Python parts run everywhere; the torch / numpy parts skip where the frameworks are absent."""

import copy
import math
from pathlib import Path

import pytest

from pinn.experiments import datasets, diagnosis, gates
from pinn.experiments.common import ArtifactStore, environment_fingerprint, environment_identity
from pinn.governance.state_machine import FailureSignature, RootCauseClass, admissible_root_causes
from pinn.governance.trust_loop import (
    diagnosis_coverage_errors,
    validate_diagnosis_record,
    validate_problem_definition,
    validate_run_record,
)
from pinn.governance.trust_vector import TrustStatus

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "experiments/poisson1d/configs/exp1_baseline.json"


def load_config():
    import json

    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_registry_satisfies_inv_a1_and_the_frozen_problem_definition_validates():
    from pinn.experiments.runner import build_problem_definition

    config = load_config()
    sets = {
        "train": datasets.manifest("set-train-t", "train", datasets.interior([0.1, 0.2]) + [{"inputs": [0.0], "kind": "boundary"}],
                                   generator={"generatorId": "g", "generatorVersion": "1"}),
        "dev": datasets.manifest("set-dev-t", "dev", datasets.interior([0.3]), generator={"generatorId": "g", "generatorVersion": "1"}),
        "phys": datasets.manifest("set-phys-t", "phys", datasets.interior([0.4]), generator={"generatorId": "g", "generatorVersion": "1"}),
        "claim": datasets.manifest("set-claim-t", "claim", datasets.interior([0.5]), generator={"generatorId": "g", "generatorVersion": "1"}),
    }
    pdef = build_problem_definition(config, sets, problem_id="pdef-poisson1d-test", revision=1, root=ROOT, frozen_at="2026-09-15T00:00:00Z")
    assert validate_problem_definition(pdef, evaluation_sets=sets) == []
    dims = {entry["dimension"] for entry in gates.REGISTRY if entry["applicability"] == "APPLICABLE"}
    assert dims == {"math", "impl", "train", "physics", "external", "repro"}
    assert all(e.get("reason") for e in gates.REGISTRY if e["applicability"] == "NOT_APPLICABLE")
    checks = gates.gate1_math(pdef, [{"artifactId": "a", "sha256": "0" * 64}])
    assert gates.dimension_status(checks) is TrustStatus.PASS


def test_dimension_status_is_the_meet_and_not_applicable_never_enters():
    checks = [gates.check("A", TrustStatus.PASS, "ok"), gates.check("B", TrustStatus.PARTIAL, "partly"), gates.not_applicable("PH10-momentumBudget")]
    assert gates.dimension_status(checks) is TrustStatus.PARTIAL
    checks[1]["status"] = "FAIL"
    assert gates.dimension_status(checks) is TrustStatus.FAIL


def test_gate4_judges_seed_statistics_without_the_best_seed():
    runs = []
    for i in range(10):
        err = 5e-4 if i < 9 else 4e-3
        runs.append({"devRelL2": err, "completed": True, "nanEncountered": False, "stepsRequested": 10, "seeds": {"init": i},
                     "lossHistory": [{"step": 1, "total": 1.0, "pde": 1.0, "bc": 0.0, "devRelL2": 0.5}, {"step": 10, "total": 1e-3, "pde": 1e-3, "bc": 0.0, "devRelL2": err}],
                     "finalLoss": {"total": 1e-3, "pde": 1e-3, "bc": 0.0}})
    pre = {"epsilonSpec": 1e-3, "worstSeedFactor": 3.0, "dispersionLimit": 1.0, "seedRuns": 10}
    checks, detail = gates.gate4_training(runs, pre, [])
    stats = detail["seedStatistics"]
    assert stats["successRate"] == "9/10" and stats["worstOk"] is False       # worst seed 4e-3 > 3 * 1e-3
    assert gates.dimension_status(checks) is TrustStatus.PARTIAL              # capped by the worst seed
    runs[9]["devRelL2"] = float("nan")
    runs[9]["nanEncountered"] = True
    checks, detail = gates.gate4_training(runs, pre, [])
    assert detail["seedStatistics"]["divergent"] == 1 and gates.dimension_status(checks) is TrustStatus.FAIL


def test_observed_signatures_fire_only_the_criteria_the_medians_meet():
    per_seed = [{"relL2": 1.2e-2, "normalizedResidualRms": 5e-3, "maxBoundaryAbs": 1e-6, "localizedRatio": 1.4, "fluxBalance": 2e-3}] * 5
    stats = {"dispersionOk": True, "worstOk": True, "divergent": 0}
    criteria = load_config()["signatureCriteria"]
    observed = diagnosis.observed_signatures(per_seed, stats, criteria, 1e-3)
    assert observed["observedSignatures"] == ["sPinnCfd"]
    stats = {"dispersionOk": False, "worstOk": True, "divergent": 0}
    per_seed = [{"relL2": 1e-4, "normalizedResidualRms": 5e-2, "maxBoundaryAbs": 1e-6, "localizedRatio": 8.0, "fluxBalance": 2e-3}] * 5
    observed = diagnosis.observed_signatures(per_seed, stats, criteria, 1e-3)
    assert observed["observedSignatures"] == ["sPdeResidual", "sSeedSensitive", "sLocalizedError"]


def test_exclusion_records_cover_every_other_candidate_of_every_observed_signature():
    observed = ["sPinnCfd", "sPdeResidual", "sLocalizedError"]
    facts = {"errorSpan": "1e-1 -> 1e-3", "T1": 1e-9, "T3": 1e-13, "T4": 1e-32, "G2a": 1e-14, "fdmOrders": [2.0], "bestLevelMedian": 1e-3,
             "baselineMedian": "3e-4", "architecture": "3x32 tanh", "failingTrainLoss": 1e-5, "failingMedian": 1e-2}
    records = diagnosis.exclusion_records(observed, facts, constitution_version="1.2")
    matrix = admissible_root_causes("1.2")
    expected = {c.value for s in observed for c in matrix[FailureSignature(s)]} - {"rSamplingDeficiency"}
    assert set(records) == expected and all(r["observed"] for r in records.values())


def test_diagnosis_record_with_a_valid_intervention_is_accepted_and_covers_all_signatures():
    observed = ["sPinnCfd", "sPdeResidual"]
    facts = {"errorSpan": "x", "T1": 1e-9, "T3": 1e-13, "T4": 1e-32, "G2a": 1e-14, "fdmOrders": [2.0], "bestLevelMedian": 1e-3,
             "baselineMedian": "3e-4", "architecture": "3x32 tanh", "failingTrainLoss": 1e-5, "failingMedian": 1e-2}
    excludes = diagnosis.exclusion_records(observed, facts, constitution_version="1.2")
    art = {"artifactId": "run_record.json", "sha256": "a" * 64}
    intervention = {"factor": "sampling", "changed": ["sampling"],
                    "heldFixed": ["architecture", "optimizer", "lrSchedule", "lossWeights", "trainingBudget", "spec", "reference", "seedProtocol"],
                    "levels": [{"level": "N=4", "seeds": 5, "medianError": 0.1}, {"level": "N=8", "seeds": 5, "medianError": 0.01}, {"level": "N=16", "seeds": 5, "medianError": 0.003}]}
    record = diagnosis.diagnosis_record(
        diagnosis_id="dg-test-r1", problem_id="pdef-poisson1d-test", revision=1, spec_hash="b" * 64, constitution_version="1.2",
        observed=observed, primary="sPinnCfd", root_cause="rSamplingDeficiency",
        signature_evidence={"pinnProvenance": art, "referenceProvenance": art, "gridConvergence": art}, experiment_id="exp-int-sampling",
        excludes=excludes, intervention=intervention, evidence_pointers=[art], round_no=1, decided_by="captain", decided_at="2026-09-15T00:00:00Z")
    assert validate_diagnosis_record(record, constitution_version="1.2") == []
    assert diagnosis_coverage_errors([record]) == []
    flat = copy.deepcopy(record)
    flat["discriminatingExperiment"]["intervention"]["levels"][2]["medianError"] = 0.02      # not strictly decreasing
    assert any("strictly decrease" in e for e in validate_diagnosis_record(flat, constitution_version="1.2"))


def test_environment_fingerprint_is_material_and_derives_an_identity(tmp_path):
    fingerprint = environment_fingerprint()
    assert fingerprint["osFamily"] in {"windows", "linux", "macos"} and len(fingerprint["dependencyLockHash"]) == 64
    identity = environment_identity(fingerprint)
    assert len(identity) == 64
    record = {
        "schemaVersion": "pinn.runRecord/1.0", "runId": "run-t", "problemId": "pdef-poisson1d-test", "revision": 1, "specHash": "a" * 64,
        "codeHash": "c" * 64, "codeManifest": [{"path": "pinn/x.py", "sha256": "d" * 64}], "environment": fingerprint,
        "environmentId": identity, "seeds": [1, 2, 3], "seedSetId": "e" * 64,
        "startedAt": "2026-09-15T00:00:00Z", "finishedAt": "2026-09-15T00:10:00Z", "executedBy": "test",
    }
    errors = validate_run_record(record)
    assert any("codeHash" in e for e in errors) and any("seedSetId" in e for e in errors) and not any("environmentId" in e for e in errors)
    store = ArtifactStore(tmp_path / "attempt")
    ref = store.write_canonical("doc.json", {"b": 1, "a": [1.5]}, role="TEST")
    assert store.ref("doc.json") == ref and (tmp_path / "attempt/PROVENANCE_MANIFEST.json").exists()
    store.transition("DRAFT", "SPEC_LOCKED", gate=1, result="PASS")
    assert store.transitions[0]["to"] == "SPEC_LOCKED"


def test_datasets_are_sample_disjoint_when_numpy_is_available():
    pytest.importorskip("numpy")
    config = load_config()
    nodes, weights = datasets.gauss_legendre_unit(16)
    assert abs(math.fsum(weights) - 1.0) < 1e-14
    sets = datasets.build_sets(config, claim_nodes=nodes, claim_pointwise=datasets.cgl_unit(20), claim_label="t")
    report = datasets.isolation_report(sets, min_separation=1e-9)
    assert report["disjoint"] and report["sizes"]["train"] == config["sampling"]["poolSize"] + 2
    assert 0.0 not in datasets.points_of(sets["claim"]) and 1.0 not in datasets.points_of(sets["claim"])


def test_trainer_reports_completion_and_autograd_fields_when_torch_is_available():
    pytest.importorskip("torch")
    from pinn.experiments import pinn_torch

    config = copy.deepcopy(load_config())
    config["optimizer"]["steps"] = 20
    pool = datasets.uniform_interior(64, 1)
    dev = datasets.uniform_interior(50, 2)
    run = pinn_torch.train_run(config, pool, dev, {"init": 1, "sample": 2, "batch": 3}, collocation_count=32, log_every=10)
    assert run["completed"] and not run["nanEncountered"] and len(run["collocationIndices"]) == 32
    model = pinn_torch.model_from_weights(config, run["weights"])
    fld = pinn_torch.fields(model, [0.25, 0.5])
    assert len(fld["uxx"]) == 2 and math.isfinite(fld["uxx"][0])
    again = pinn_torch.train_run(config, pool, dev, {"init": 1, "sample": 2, "batch": 3}, collocation_count=32, log_every=10)
    assert again["devRelL2"] == run["devRelL2"]      # deterministic replay
