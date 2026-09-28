"""Claim-set lifecycle has exactly one source of truth: the ledger (Final Closure Audit issue 4)."""

import json
from pathlib import Path

import pytest

from pinn.experiments2d.runner2d import derived_claim_status
from pinn.governance.claim_set_ledger import make_event, validate_claim_set_ledger

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "experiments/poisson2d/ledger/pdef-poisson2d-cal-v1.json"
POOL = ROOT / "experiments/poisson2d/problems/pdef-poisson2d-cal-v1-claim-pool.json"
REGISTRY = ROOT / "experiments/poisson2d/ledger/sample_set_registry.json"
PROBLEM = "pdef-poisson2d-cal-v1"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def consumed_member():
    events = load(LEDGER)
    opened = next(e for e in events if e["event"] == "OPENED")
    members = load(POOL)["members"]
    name = next(n for n, m in members.items() if m["artifactHash"] == opened["claimSetSha256"])
    return name, members[name], events


def test_stale_manifest_status_cannot_override_the_ledger(monkeypatch):
    monkeypatch.chdir(ROOT)
    name, member, events = consumed_member()
    assert member.get("status") == "SEALED", "the committed manifest still carries the registration-time value"
    status, _ = derived_claim_status(events, problem_id=PROBLEM, revision=1,
                                     artifact_hash=member["artifactHash"], sample_hash=member["sampleSetHash"])
    assert status in ("OPENED", "BURNT"), f"{name} was consumed; the ledger must say so regardless of the manifest"


def test_burn_follows_the_samples_across_revisions(monkeypatch):
    monkeypatch.chdir(ROOT)
    _name, member, events = consumed_member()
    # the same samples, queried for a revision that never sealed this artifact, are still burnt
    status, _ = derived_claim_status(events, problem_id=PROBLEM, revision=3,
                                     artifact_hash=member["artifactHash"], sample_hash=member["sampleSetHash"])
    assert status == "BURNT"


def test_an_unconsumed_member_is_sealed_and_usable(monkeypatch):
    monkeypatch.chdir(ROOT)
    events = load(LEDGER)
    opened = {e["claimSetSha256"] for e in events if e["event"] == "OPENED"}
    members = load(POOL)["members"]
    fresh = {n: m for n, m in members.items() if m["artifactHash"] not in opened}
    assert fresh, "the pool must still hold unconsumed members"
    for name, member in fresh.items():
        # at revision 1 the preregistration seal is visible; at the designated revision the key was never sealed yet
        # (the attempt of that revision seals it itself). Either way the member is USABLE: not OPENED, not BURNT.
        at_seal = derived_claim_status(events, problem_id=PROBLEM, revision=1,
                                       artifact_hash=member["artifactHash"], sample_hash=member["sampleSetHash"])[0]
        at_designated = derived_claim_status(events, problem_id=PROBLEM, revision=member["designatedRevision"],
                                             artifact_hash=member["artifactHash"], sample_hash=member["sampleSetHash"])[0]
        assert at_seal == "SEALED", f"{name} lost its preregistration seal: {at_seal}"
        assert at_designated in ("SEALED", "NEVER_SEALED"), f"{name} is not usable: {at_designated}"
        assert at_designated not in ("OPENED", "BURNT")


def test_early_guard_and_final_ledger_validator_agree(monkeypatch):
    """Whatever the early guard refuses, the ledger validator refuses too -- and the other way round."""

    monkeypatch.chdir(ROOT)
    _name, member, events = consumed_member()
    registry = load(REGISTRY)
    # (a) re-OPEN of the consumed set
    again = list(events) + [make_event(prev_event_id=events[-1]["eventId"], problemId=PROBLEM, revision=1,
                                       specHash=events[-1]["specHash"], claimSetSha256=member["artifactHash"],
                                       sampleSetHash=member["sampleSetHash"], event="OPENED",
                                       codeHash="a" * 64, actor="test", at="2026-09-16T23:59:59Z")]
    guard_status, _ = derived_claim_status(events, problem_id=PROBLEM, revision=1,
                                           artifact_hash=member["artifactHash"], sample_hash=member["sampleSetHash"])
    assert guard_status in ("OPENED", "BURNT")
    assert validate_claim_set_ledger(again, sample_set_hashes=registry), "the validator must refuse a second OPENED"
    # (b) the same samples re-wrapped under a new artifact and sealed again
    rewrapped = list(events) + [make_event(prev_event_id=events[-1]["eventId"], problemId=PROBLEM, revision=2,
                                           specHash=events[-1]["specHash"], claimSetSha256="f" * 64,
                                           sampleSetHash=member["sampleSetHash"], event="SEALED",
                                           actor="test", at="2026-09-16T23:59:59Z")]
    errors = validate_claim_set_ledger(rewrapped, sample_set_hashes=registry)
    assert any("re-wrapped" in e or "burnt" in e for e in errors), errors
    guard_rewrapped, _ = derived_claim_status(events, problem_id=PROBLEM, revision=2,
                                              artifact_hash="f" * 64, sample_hash=member["sampleSetHash"])
    assert guard_rewrapped == "BURNT", "the early guard must catch a re-wrapped sample set too"


def test_runner_guard_reads_the_ledger_not_the_manifest():
    source = (ROOT / "pinn/experiments2d/runner2d.py").read_text(encoding="utf-8")
    guard = source[source.index("def phase_problem"):source.index("def phase_upstream_gates")]
    assert "derived_claim_status(" in guard, "phase_problem must derive the status from the ledger"
    assert 'member["status"]' not in guard, "phase_problem must not branch on the manifest's static status field"
    early = guard.index("derived_claim_status(")
    assert early < guard.index("isolation_report"), "the guard must run before the isolation scan and the gates"
