"""2D Gate 6: reproduction judgement, the frozen tolerance and the reproduction package (PART 22)."""

import copy
import json
from pathlib import Path

import pytest

from pinn.experiments2d.runner2d import judge_reproduction
from pinn.governance.trust_loop import validate_claim_gate_decision, validate_trust_vector

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "experiments/poisson2d/runs"
ORIGINAL = RUNS / "exp2d-poisson-calibration-r1"
REPRODUCTION = RUNS / "repro-envb2d-r1"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _skip_unless_executed():
    if not (REPRODUCTION / "run_record.json").exists():
        pytest.skip("the 2D reproduction has not been executed in this checkout")


def test_independent_reproduction_of_the_2d_run_passes(monkeypatch):
    monkeypatch.chdir(ROOT)
    _skip_unless_executed()
    report = judge_reproduction(ORIGINAL, REPRODUCTION, write=False)
    assert report["sameSpec"] and report["sameCode"] and report["differentSeedSet"] and report["independentEnvironments"]
    assert report["cRepro"] == "PASS", report["summaryLine"]
    assert report["metrics"]["medianAbsDiff"] <= report["tolerance"]["devRelL2MedianAbsDiff"]
    assert report["metrics"]["medianAbsDiff"] <= report["tolerance"]["devRelL2MedianRelDiff"] * report["metrics"]["medianA"]
    assert report["claimSetTouched"] is False


def test_the_tightened_relative_limit_is_enforced_as_well_as_the_inherited_absolute_one(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    _skip_unless_executed()
    base = judge_reproduction(ORIGINAL, REPRODUCTION, write=False)
    tolerance = base["tolerance"]
    assert tolerance["devRelL2MedianAbsDiff"] == 1e-4 and tolerance["devRelL2MedianRelDiff"] == 0.5
    # a reproduction whose median is 3x the original is inside the 1e-4 absolute limit at this error scale but
    # far outside the relative one: the relative limit is what does the work in 2D.
    drifted = tmp_path / "drifted"
    drifted.mkdir()
    for name in ("run_record.json", "training_report.json"):
        (drifted / name).write_bytes((REPRODUCTION / name).read_bytes())
    training = load(drifted / "training_report.json")
    original_median = load(ORIGINAL / "training_report.json")["seedStatistics"]["median"]
    training["seedStatistics"]["median"] = original_median * 3.0
    (drifted / "training_report.json").write_text(json.dumps(training, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = judge_reproduction(ORIGINAL, drifted, write=False)
    assert report["metrics"]["medianAbsDiff"] <= tolerance["devRelL2MedianAbsDiff"], "still inside the inherited absolute limit"
    assert report["withinTolerance"] is False and report["cRepro"] != "PASS"


def test_same_seed_set_or_same_environment_never_qualifies(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)
    _skip_unless_executed()
    original_record = load(ORIGINAL / "run_record.json")
    for mutation, expected in (("seeds", "seedSetId"), ("environment", "environmentId")):
        sandbox = tmp_path / mutation
        sandbox.mkdir()
        record = copy.deepcopy(load(REPRODUCTION / "run_record.json"))
        if mutation == "seeds":
            record["seeds"] = original_record["seeds"]
            record["seedSetId"] = original_record["seedSetId"]
        else:
            record["environment"] = copy.deepcopy(original_record["environment"])
            record["environmentId"] = original_record["environmentId"]
        (sandbox / "run_record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (sandbox / "training_report.json").write_bytes((REPRODUCTION / "training_report.json").read_bytes())
        report = judge_reproduction(ORIGINAL, sandbox, write=False)
        assert report["cRepro"] != "PASS", f"{expected} identical must not qualify as an independent reproduction"


def test_final_g6_trust_vector_and_claim_decision_revalidate(monkeypatch):
    monkeypatch.chdir(ROOT)
    if not (ORIGINAL / "trust_vector_g6.json").exists():
        pytest.skip("Gate 6 has not been applied in this checkout")
    pdef = load(ORIGINAL / "problem_definition.json")
    vector = load(ORIGINAL / "trust_vector_g6.json")
    decision = load(ORIGINAL / "claim_gate_decision_g6.json")
    assert not validate_trust_vector(vector, pdef)
    events = load(ROOT / "experiments/poisson2d/ledger/pdef-poisson2d-cal-v1.json")
    run_records = {load(ORIGINAL / "run_record.json")["runId"]: load(ORIGINAL / "run_record.json")}
    assert not validate_claim_gate_decision(decision, vector, pdef, claim_set_events=events, run_records=run_records)
    assert all(entry["status"] == "PASS" for entry in vector["dimensions"].values())
    allowed = [claim["level"] for claim in decision["allowedClaims"]]
    assert allowed == ["C0", "C1", "C2"], allowed
    blocked = {claim["level"]: claim["reason"] for claim in decision["blockedClaims"]}
    assert "C3" in blocked


def test_reproduction_package_carries_the_frozen_tolerance_and_the_code_identity_instruction(monkeypatch):
    monkeypatch.chdir(ROOT)
    manifest_path = ROOT / "experiments/poisson2d/repro_package/PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        pytest.skip("the reproduction package has not been written in this checkout")
    manifest = load(manifest_path)
    assert manifest["packageType"] == "PINN_G6_REPRODUCTION_PACKAGE_2D" and manifest["spatialDimension"] == 2
    tolerance = manifest["expectedTolerance"]
    assert tolerance["devRelL2MedianAbsDiff"] == 1e-4 and tolerance["devRelL2MedianRelDiff"] == 0.5
    assert tolerance["seedProtocolVerdictMustAgree"] is True
    assert "10000" in manifest["reproductionSeedRule"]
    assert any("codeHash" in step for step in manifest["instructions"])
    assert any("never opens a claim set" in step for step in manifest["instructions"])
    assert manifest["specHash"] == load(ORIGINAL / "problem_definition.json")["specHash"]
