"""G6 reproduction judgement: same spec + same code + independent environment + different seeds + frozen tolerance."""

import copy
import json
from pathlib import Path

from pinn.experiments.runner import judge_reproduction
from pinn.governance.trust_loop import validate_claim_gate_decision, validate_trust_vector

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments/poisson1d/runs"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_frozen_code_reproduction_passes_and_new_code_reproduction_is_blocked(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    good = judge_reproduction(RUNS / "exp3c-hard-bc-r2", RUNS / "repro-envb-frozen-r2", write=False)
    assert good["cRepro"] == "PASS" and good["sameCode"] and good["sameSpec"] and good["differentSeedSet"] and good["independentEnvironments"]
    assert set(good["strongFieldsDiffering"]) == {"dependencyLockHash", "installationId"}
    assert good["metrics"]["medianAbsDiff"] <= good["tolerance"]["devRelL2MedianAbsDiff"]
    blocked = judge_reproduction(RUNS / "exp3c-hard-bc-r2", RUNS / "repro-envb-r2", write=False)
    assert blocked["cRepro"] == "BLOCKED" and not blocked["sameCode"]
    assert any("same method" in p for p in blocked["problems"])


def test_reproduction_outside_tolerance_or_same_environment_or_same_seeds_does_not_pass(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    src = RUNS / "repro-envb-frozen-r2"
    original = RUNS / "exp3c-hard-bc-r2"

    def variant(name, mutate_record=None, mutate_training=None):
        d = tmp_path / name
        d.mkdir()
        record = load(src / "run_record.json")
        training = load(src / "training_report.json")
        if mutate_record:
            mutate_record(record)
        if mutate_training:
            mutate_training(training)
        (d / "run_record.json").write_text(json.dumps(record), encoding="utf-8")
        (d / "training_report.json").write_text(json.dumps(training), encoding="utf-8")
        return d

    def widen(t):
        t["seedStatistics"]["median"] = t["seedStatistics"]["median"] + 5e-4

    far = judge_reproduction(original, variant("far", mutate_training=widen), write=False)
    assert far["cRepro"] == "FAIL" and not far["withinTolerance"]

    orig_record = load(original / "run_record.json")

    def same_env(r):
        r["environment"] = orig_record["environment"]
        r["environmentId"] = orig_record["environmentId"]

    same = judge_reproduction(original, variant("same_env", mutate_record=same_env), write=False)
    assert same["cRepro"] == "BLOCKED" and not same["independentEnvironments"]

    def same_seeds(r):
        r["seeds"] = orig_record["seeds"]
        r["seedSetId"] = orig_record["seedSetId"]

    dup = judge_reproduction(original, variant("same_seeds", mutate_record=same_seeds), write=False)
    assert dup["cRepro"] == "BLOCKED" and not dup["differentSeedSet"]


def test_final_g6_vector_and_c2_decision_revalidate():
    attempt = RUNS / "exp3c-hard-bc-r2"
    pdef = load(attempt / "problem_definition.json")
    vector = load(attempt / "trust_vector_g6.json")
    assert validate_trust_vector(vector, pdef) == []
    assert {d: v["status"] for d, v in vector["dimensions"].items()} == {d: "PASS" for d in vector["dimensions"]}
    decision = load(attempt / "claim_gate_decision_g6.json")
    events = load(ROOT / "experiments/poisson1d/ledger/pdef-poisson1d-cal-v1.json")
    records = {load(attempt / "run_record.json")["runId"]: load(attempt / "run_record.json")}
    assert validate_claim_gate_decision(decision, vector, pdef, claim_set_events=events, run_records=records) == []
    assert [c["level"] for c in decision["allowedClaims"]] == ["C0", "C1", "C2"]
    assert [c["level"] for c in decision["blockedClaims"]] == ["C3"]
    assert load(attempt / "attempt_state.json")["state"] == "ACCEPTED"
