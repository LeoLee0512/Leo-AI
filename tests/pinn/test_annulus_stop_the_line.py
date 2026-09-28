"""The annulus r1 attempt stopped the line on 2026-09-26 (owner's decision), and the record must say so honestly."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pinn.governance.state_machine import FailureSignature, RootCauseClass, admissible_root_causes
from pinn.governance.trust_loop import validate_diagnosis_record

REPO = Path(__file__).resolve().parents[2]
R1 = REPO / "experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_record_is_a_valid_undetermined_diagnosis_with_no_gate():
    record = _json(R1 / "diagnosis_record.json")
    assert validate_diagnosis_record(record, constitution_version="1.2") == []
    assert record["rootCause"] == RootCauseClass.UNDETERMINED.value
    assert "gate" not in record, "rUndetermined routes to no Gate; the line stops for a human"
    assert record["specHash"] == _json(R1 / "problem_definition.json")["specHash"]


def test_only_the_two_causes_the_round_excluded_are_written_as_excluded():
    record = _json(R1 / "diagnosis_record.json")
    verdict = _json(R1 / "diagnosis_verdict.json")
    excluded = set(record["discriminatingExperiment"]["excludes"])
    assert excluded == {"rImplementationDefect", "rSpecDefect"}
    candidates = {c.value for c in admissible_root_causes("1.2")[FailureSignature.LOCALIZED_ERROR]}
    # Everything else stays open, including the favoured hypothesis: it was supported, never shown necessary.
    assert set(verdict["notExcluded"]) == candidates - excluded
    assert "rOptimizationFailure" in verdict["notExcluded"] and "rCapacityLimit" in verdict["notExcluded"]


def test_state_and_transition_log_agree_and_nothing_was_rewritten():
    assert _json(R1 / "attempt_state.json")["state"] == "STOPPED_THE_LINE"
    transitions = _json(R1 / "STATE_TRANSITIONS.json")["transitions"]
    assert [t["to"] for t in transitions[-2:]] == ["FAILURE_RECORDED", "STOPPED_THE_LINE"]
    assert transitions[-1]["result"] == "STOP:rUndetermined" and transitions[-1]["gate"] is None
    # The run's own summary is history: it still says how the run ended.
    assert _json(R1 / "RUN_SUMMARY.json")["finalState"] == "FAILURE_RECORDED"


def test_the_new_files_are_registered_with_their_real_hashes():
    manifest = {a["artifactId"]: a["sha256"] for a in _json(R1 / "PROVENANCE_MANIFEST.json")["artifacts"]}
    for name in ("diagnosis_record.json", "diagnosis_verdict.json", "attempt_state.json"):
        assert manifest[name] == hashlib.sha256((R1 / name).read_bytes()).hexdigest(), name


def test_stopping_the_line_opened_no_claim_set():
    path = REPO / "experiments/annulus/ledger/pdef-annulus-poisson-v1.json"
    events = _json(path)
    assert [event["event"] for event in events[:2]] == ["SEALED", "OPENED"]
    # r1's two events, serialised exactly as write_ledger writes them, are the same bytes as
    # when the exclusion round closed its claim firewall; revision 2 may only append after them.
    prefix = (json.dumps(events[:2], ensure_ascii=False, indent=2) + chr(10)).encode("utf-8")
    firewall = _json(REPO / "experiments/annulus/diagnosis/exclusions/EXCLUSIONS.json")["claimFirewall"]
    assert hashlib.sha256(prefix).hexdigest() == firewall["ledgerSha256AtEnd"]
    verdict = _json(R1 / "diagnosis_verdict.json")
    assert verdict["claimSets"]["DAC-M1"] == "NEVER_SEALED"
