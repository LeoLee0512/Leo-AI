"""The claim-set ledger: SEALED -> OPENED is one way, and rewriting history is detectable (draft 3, issue 3)."""

import copy

import pytest

from pinn.governance.claim_set_ledger import (
    GENESIS,
    derive_claim_set_state,
    event_id,
    make_event,
    validate_claim_set_ledger,
)

PROBLEM = "pdef-poisson1d-v1.0"
SPEC = "a" * 64
CODE = "b" * 64
CLAIM1 = "3" * 64
CLAIM2 = "4" * 64


def chain(*steps):
    """steps: (event, revision, claim, at, extra) tuples, chained in order."""

    events = []
    prev = GENESIS
    for kind, revision, claim, at, *extra in steps:
        fields = {"problemId": PROBLEM, "revision": revision, "specHash": SPEC, "claimSetSha256": claim,
                  "event": kind, "actor": "governance", "at": at}
        if kind == "OPENED":
            fields["codeHash"] = CODE
        if extra:
            fields.update(extra[0])
        events.append(make_event(prev_event_id=prev, **fields))
        prev = events[-1]["eventId"]
    return events


def test_sealed_then_opened_is_a_valid_ledger_and_the_status_derives():
    events = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"))
    assert validate_claim_set_ledger(events) == []
    state = derive_claim_set_state(events, problem_id=PROBLEM, revision=1, claim_set_sha256=CLAIM1)
    assert state.status == "OPENED" and state.opened_at_revision == 1 and state.opened_code_hash == CODE
    assert state.history == ({"sha256": CLAIM1, "openedAtRevision": 1},)
    assert state.burnt == frozenset({CLAIM1}) and state.head == events[-1]["eventId"]
    sealed_only = events[:1]
    assert derive_claim_set_state(sealed_only, problem_id=PROBLEM, revision=1, claim_set_sha256=CLAIM1).status == "SEALED"
    assert derive_claim_set_state([], problem_id=PROBLEM, revision=1, claim_set_sha256=CLAIM1).status == "NEVER_SEALED"


def test_opened_to_sealed_is_rejected():
    events = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"),
                   ("SEALED", 1, CLAIM1, "2026-09-14T07:00:00Z"))
    assert any("cannot be sealed again" in error for error in validate_claim_set_ledger(events))
    later = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"),
                  ("SEALED", 2, CLAIM1, "2026-09-15T00:00:00Z"))
    assert any("cannot be sealed again" in error for error in validate_claim_set_ledger(later))


def test_history_deletion_reordering_and_rewriting_break_the_chain():
    events = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"),
                   ("SEALED", 2, CLAIM2, "2026-09-15T00:00:00Z"))
    assert validate_claim_set_ledger(events) == []
    deleted = [events[0], events[2]]
    assert any("chain broken" in error for error in validate_claim_set_ledger(deleted))
    reordered = [events[0], events[2], events[1]]
    assert any("chain broken" in error for error in validate_claim_set_ledger(reordered))
    rewritten = copy.deepcopy(events)
    rewritten[1]["event"] = "SEALED"
    assert any("does not recompute" in error for error in validate_claim_set_ledger(rewritten))
    truncated = events[:2]
    assert validate_claim_set_ledger(truncated) == []
    assert derive_claim_set_state(truncated, problem_id=PROBLEM, revision=2, claim_set_sha256=CLAIM2).head != events[-1]["eventId"]


def test_a_claim_set_is_opened_once_ever_and_once_per_revision():
    twice = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"),
                  ("OPENED", 1, CLAIM1, "2026-09-14T07:00:00Z"))
    errors = validate_claim_set_ledger(twice)
    assert any("opened once, ever" in error for error in errors)
    assert any("same problem and revision" in error for error in errors)
    reuse = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"),
                  ("SEALED", 2, CLAIM1, "2026-09-15T00:00:00Z"))
    assert any("burnt" in error for error in validate_claim_set_ledger(reuse))
    two_sets_one_revision = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"), ("SEALED", 1, CLAIM2, "2026-09-14T00:00:00Z"),
                                  ("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"), ("OPENED", 1, CLAIM2, "2026-09-14T07:00:00Z"))
    assert any("same problem and revision" in error for error in validate_claim_set_ledger(two_sets_one_revision))


def test_opened_needs_a_matching_sealed_event_and_the_code_identity():
    unsealed = chain(("OPENED", 1, CLAIM1, "2026-09-14T06:00:00Z"))
    assert any("without a preceding SEALED" in error for error in validate_claim_set_ledger(unsealed))
    other_spec = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"))
    other_spec.append(make_event(prev_event_id=other_spec[-1]["eventId"], problemId=PROBLEM, revision=1,
                                 specHash="9" * 64, claimSetSha256=CLAIM1, event="OPENED", codeHash=CODE,
                                 actor="governance", at="2026-09-14T06:00:00Z"))
    assert any("sealed for" in error for error in validate_claim_set_ledger(other_spec))
    no_code = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"))
    no_code.append(make_event(prev_event_id=no_code[-1]["eventId"], problemId=PROBLEM, revision=1, specHash=SPEC,
                              claimSetSha256=CLAIM1, event="OPENED", actor="governance", at="2026-09-14T06:00:00Z"))
    assert any("codeHash" in error for error in validate_claim_set_ledger(no_code))


def test_time_runs_forward_and_events_are_well_formed():
    backwards = chain(("SEALED", 1, CLAIM1, "2026-09-14T06:00:00Z"), ("OPENED", 1, CLAIM1, "2026-09-14T00:00:00Z"))
    assert any("earlier than the previous" in error for error in validate_claim_set_ledger(backwards))
    assert any("expected type" in error or "missing required" in error for error in validate_claim_set_ledger([{"eventId": "x"}]))
    assert validate_claim_set_ledger("not a ledger")
    event = chain(("SEALED", 1, CLAIM1, "2026-09-14T00:00:00Z"))[0]
    assert event["eventId"] == event_id(event)
    assert validate_claim_set_ledger([]) == []
