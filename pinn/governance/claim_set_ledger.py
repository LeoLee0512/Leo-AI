"""Append-only ledger of claim-set events (Amendment A-0001, draft 3; sample identity 2026-09-16).

Review finding (2026-09-15, issue 3): ``claimSetStatus`` as a plain writable
field lets SEALED -> OPENED -> SEALED pass as "never opened".  The status is
therefore no longer a source of truth: it is *derived* from this ledger, and
the ledger is a hash chain that the validator re-walks.

Post-experiment finding (2026-09-16, Poisson 1D Experiment 2): the burn rule
was keyed on ``claimSetSha256`` -- the canonical hash of the manifest *document*
-- so the same samples re-wrapped under another ``artifactId`` counted as a
fresh, blind claim set.  Constitution 9.1 burns the *claim set*, i.e. the
samples that were looked at; the artifact hash was an implementation choice.
Every event may therefore carry ``sampleSetHash`` (``evaluation_sets.
sample_set_hash``: the canonical hash of the sorted sample identities, blind
to artifactId, generator metadata and ordering), and the burn invariants are
enforced on the sample identity as well.  Legacy events without the field are
resolved through ``sample_set_hashes`` (``{claimSetSha256: sampleSetHash}``)
supplied by whoever holds the manifests.  This is a protocol clarification and
bug fix, not a change of constitutional meaning.

Governance guarantee, stated honestly: a JSON file is not an immutable
store.  What the chain gives is *detectability*: any deletion, reordering or
rewrite of an event breaks every later event id, and the ledger head is what
a ClaimGateDecision must cite.

Event shape (``claim-set-event.schema.json``)::

    {eventId, prevEventId | "GENESIS", problemId, revision, specHash,
     claimSetSha256, sampleSetHash?, event: SEALED | OPENED, actor, at, codeHash?}

``eventId = canonical_sha256(all fields except eventId)``.

Invariants (``validate_claim_set_ledger``):

* L1 chain; L2 non-decreasing ``at``;
* L3 SEALED precedes OPENED for (problemId, revision, claimSetSha256) with the
  same specHash, and OPENED records codeHash;
* L4 one OPENED per claimSetSha256 -- ever; **L4s one OPENED per sampleSetHash
  -- ever** (same samples under another artifact are the same claim set);
* L5 one OPENED per (problemId, revision);
* L6 / L7 a claim set is never SEALED again after its OPENED event, at any
  revision, **by artifact hash or by sample identity**; at most one SEALED per
  (problemId, revision, claimSetSha256);
* L8 a claimSetSha256 is bound to one sampleSetHash: an event that names a
  different sample identity for a known artifact is forged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256
from .jsonschema_lite import validate as validate_schema

SCHEMA_DIR = Path(__file__).with_name("schemas")
CLAIM_SET_EVENT_SCHEMA = "claim-set-event.schema.json"
GENESIS = "GENESIS"
SEALED = "SEALED"
OPENED = "OPENED"


def _load_schema() -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / CLAIM_SET_EVENT_SCHEMA).read_text(encoding="utf-8"))


def event_id(event: Mapping[str, Any]) -> str:
    """The id an event must carry: a hash over every field except eventId."""

    return canonical_sha256({key: value for key, value in event.items() if key != "eventId"})


def make_event(*, prev_event_id: str, **fields: Any) -> dict[str, Any]:
    """Build a well-formed event (the id is computed, never chosen)."""

    event = {"prevEventId": prev_event_id, **fields}
    event["eventId"] = event_id(event)
    return event


def _sample_hash(event: Mapping[str, Any], resolver: Mapping[str, str] | None) -> str | None:
    declared = event.get("sampleSetHash")
    resolved = resolver.get(event["claimSetSha256"]) if resolver else None
    if declared is not None and resolved is not None and declared != resolved:
        return "MISMATCH"
    return declared or resolved


def validate_claim_set_ledger(events: Sequence[Any], *, sample_set_hashes: Mapping[str, str] | None = None) -> list[str]:
    """L1-L8 over the whole chain; returns every violation found."""

    errors: list[str] = []
    if isinstance(events, (str, bytes, Mapping)):
        return ["ledger must be a sequence of events"]
    schema = _load_schema()
    previous_id = GENESIS
    previous_at = ""
    opened_hashes: dict[str, tuple[str, int]] = {}
    opened_samples: dict[str, str] = {}            # sampleSetHash -> claimSetSha256 that opened it
    opened_per_revision: set[tuple[str, int]] = set()
    sealed: dict[tuple[str, int, str], dict[str, Any]] = {}
    bound_samples: dict[str, str] = {}             # claimSetSha256 -> sampleSetHash (L8)
    for index, event in enumerate(events):
        path = f"events[{index}]"
        structural = validate_schema(event, schema)
        if structural:
            errors.extend(f"{path}: {error}" for error in structural)
            return errors
        if event["prevEventId"] != previous_id:
            errors.append(f"{path}.prevEventId: chain broken (expected {previous_id[:12]}...)")
            return errors
        if event["eventId"] != event_id(event):
            errors.append(f"{path}.eventId: does not recompute; the event was altered or forged")
            return errors
        if event["at"] < previous_at:
            errors.append(f"{path}.at: earlier than the previous event")
        sample_hash = _sample_hash(event, sample_set_hashes)
        if sample_hash == "MISMATCH":
            errors.append(f"{path}.sampleSetHash: differs from the sample identity of the supplied manifest for this artifact")
            sample_hash = None
        if sample_hash is not None:
            known = bound_samples.setdefault(event["claimSetSha256"], sample_hash)
            if known != sample_hash:
                errors.append(f"{path}.sampleSetHash: artifact {event['claimSetSha256'][:12]} was bound to another sample identity earlier in the ledger")
        key = (event["problemId"], event["revision"], event["claimSetSha256"])
        kind = event["event"]
        if kind == SEALED:
            if event["claimSetSha256"] in opened_hashes:
                errors.append(f"{path}: claim set was already OPENED (burnt); it cannot be sealed again")
            elif sample_hash is not None and sample_hash in opened_samples:
                errors.append(
                    f"{path}: the samples of this claim set were already OPENED under artifact "
                    f"{opened_samples[sample_hash][:12]} (sample identity {sample_hash[:12]} is burnt); a re-wrapped claim set is not blind"
                )
            elif key in sealed:
                errors.append(f"{path}: claim set already SEALED for this problem and revision")
            else:
                sealed[key] = event
        elif kind == OPENED:
            seal = sealed.get(key)
            if seal is None:
                errors.append(f"{path}: OPENED without a preceding SEALED for this problem, revision and claim set")
            elif seal["specHash"] != event["specHash"]:
                errors.append(f"{path}.specHash: differs from the spec the claim set was sealed for")
            if "codeHash" not in event:
                errors.append(f"{path}.codeHash: an OPENED event must record the code identity validated on the set")
            if event["claimSetSha256"] in opened_hashes:
                errors.append(f"{path}: claim set was already OPENED; a set is opened once, ever")
            if sample_hash is not None and sample_hash in opened_samples and opened_samples[sample_hash] != event["claimSetSha256"]:
                errors.append(
                    f"{path}: the samples of this claim set were already OPENED under artifact {opened_samples[sample_hash][:12]}; "
                    "a set is opened once, ever, by sample identity"
                )
            if (event["problemId"], event["revision"]) in opened_per_revision:
                errors.append(f"{path}: a second OPENED for the same problem and revision; bump the revision first")
            opened_hashes.setdefault(event["claimSetSha256"], (event["problemId"], event["revision"]))
            if sample_hash is not None:
                opened_samples.setdefault(sample_hash, event["claimSetSha256"])
            opened_per_revision.add((event["problemId"], event["revision"]))
        previous_id = event["eventId"]
        previous_at = event["at"]
    return errors


@dataclass(frozen=True)
class ClaimSetState:
    status: str                         # SEALED or OPENED (for the current claim set), or NEVER_SEALED
    opened_at_revision: int | None
    history: tuple[dict[str, Any], ...]  # [{sha256, openedAtRevision}] for this problem, in ledger order
    burnt: frozenset[str]               # every claim-set artifact hash with an OPENED event anywhere in the ledger
    head: str                           # eventId of the last event, or GENESIS
    opened_code_hash: str | None        # codeHash recorded on the OPENED event of the current set, if any
    burnt_samples: frozenset[str] = frozenset()   # every sampleSetHash with an OPENED event anywhere (by field or resolver)
    burnt_sample_artifacts: Mapping[str, str] = None  # type: ignore[assignment]  # sampleSetHash -> artifact that opened it


def derive_claim_set_state(events: Sequence[Mapping[str, Any]], *, problem_id: str,
                           revision: int, claim_set_sha256: str,
                           sample_set_hashes: Mapping[str, str] | None = None) -> ClaimSetState:
    """What the ledger says about ``problem_id``'s claim set at ``revision`` (ledger assumed valid)."""

    history: list[dict[str, Any]] = []
    burnt: set[str] = set()
    burnt_samples: dict[str, str] = {}
    status = "NEVER_SEALED"
    opened_at: int | None = None
    opened_code: str | None = None
    head = GENESIS
    for event in events:
        head = event["eventId"]
        if event["event"] == OPENED:
            burnt.add(event["claimSetSha256"])
            sample_hash = _sample_hash(event, sample_set_hashes)
            if sample_hash and sample_hash != "MISMATCH":
                burnt_samples.setdefault(sample_hash, event["claimSetSha256"])
            if event["problemId"] == problem_id:
                history.append({"sha256": event["claimSetSha256"], "openedAtRevision": event["revision"]})
        if event["problemId"] != problem_id or event["claimSetSha256"] != claim_set_sha256:
            continue
        if event["event"] == SEALED and event["revision"] == revision:
            status = SEALED
        elif event["event"] == OPENED:
            status = OPENED
            opened_at = event["revision"]
            opened_code = event.get("codeHash")
    return ClaimSetState(status, opened_at, tuple(history), frozenset(burnt), head, opened_code,
                         frozenset(burnt_samples), dict(burnt_samples))
