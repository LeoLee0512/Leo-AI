"""Corrected review semantics for research-sop, plus the run/manifest/history audit.

Two statements from the review round were wrong as written, and had to be
restated before they could be tested. This file is where the corrected wording
lives as executable assertions, so that "what the system is supposed to do" is
not carried only by prose that turned out to be mistaken.

**Correction A — a missing stage document.**

    Wrong:   "after the paper document is deleted the system must return
              paper=None."
    Right:   a missing stage artifact means that *stage* is no longer complete.
             When the upstream evidence is still valid, the stage is re-run and
             a real new document is produced. ``paper=None`` is the outcome only
             when the writer genuinely cannot produce one; it is not the
             definition of correct recovery.

The wrong version is worse than imprecise: a system that "correctly" answered
None would be a system that lost the ability to finish the work. What must never
happen is the opposite — reporting a paper whose file is not there.

**Correction B — a changed role prompt.**

    Wrong:   "after the prompt changes, the old run is still usable as a valid
              run via sop_read_manifest."
    Right:   the old run's bytes and history must survive untouched and stay
             auditable, but relative to the new prompts it is no longer a
             valid-compatible run. It is classified ``incompatible``. It must
             not be silently accepted as evidence produced under the new prompt.

``sop_read_manifest`` returning None for such a run is therefore correct, and is
not the same thing as the run being deleted or unreadable: ``sop_inspect_manifest``
and ``sop_list_runs`` still return its contents, labelled.

The rest of the file audits the properties those two corrections sit inside:
original evidence is never silently overwritten, a re-run keeps the old bytes,
history is readable, and the manifest can tell compatible from incompatible.

These tests are additional to, and separate from, the 41-item reconstructed
adversarial suite in ``test_research_sop_integrity_adversarial.py``; that file is
kept at its reconstructed contents so it stays comparable with the reviewer's
original when it arrives. See ``manifests/test-suites.json``.
"""

from __future__ import annotations

import json

import pytest

from test_research_sop import (  # noqa: F401 - fixtures come from the sibling module
    FakeHost,
    TASK_A,
    TASK_B,
    _load_kernel,
    _passing_outputs,
    host,
    kernel,
    schema_valid_output,
)


def _stage_files(host, run_id):
    """Every workspace path currently belonging to *run_id*."""
    return {k: v for k, v in host.files.items() if k.startswith(f"research-runs/{run_id}/")}


# ===================================================================
# Correction A — a deleted stage document means re-run, not paper=None
# ===================================================================


@pytest.mark.parametrize("removal", ["blanked", "deleted"])
def test_correction_a_missing_paper_document_is_re_run_and_a_real_document_returned(
    kernel, host, removal
):
    """The corrected semantics, asserted end to end.

    Whether the document is blanked or removed from the workspace entirely, the
    stage must be recognised as needing re-execution, the paper-writer must
    actually run again, and the run must end holding a real document -- not None,
    and not a stale path to a file that is gone.
    """
    first = kernel.orchestrate_research(TASK_A)
    assert first["status"] == "complete"
    run_id = first["run_id"]
    document = kernel.sop_stage_path(run_id, "paper-writer", "md")
    original_body = host.files[document]
    assert original_body.strip()

    if removal == "blanked":
        host.files[document] = ""
    else:
        del host.files[document]

    host.delegate_calls.clear()
    again = kernel.orchestrate_research(TASK_A, resume=True)

    # 1. the stage was identified as needing re-execution
    assert [c["role"] for c in host.delegate_calls] == ["paper-writer"], (
        "exactly the stage whose artifact went missing must be re-run"
    )
    # 2. and it produced a real document, which is the corrected expectation
    assert again["paper"] == document, again
    assert host.files[document].strip(), "the re-run must leave a real document behind"
    assert again["status"] == "complete"


def test_correction_a_upstream_evidence_is_not_re_run_when_it_is_still_valid(kernel, host):
    """Recovery is scoped to the broken stage; valid upstream stays untouched."""
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    upstream = {
        role: host.files[kernel.sop_stage_path(run_id, role, "json")]
        for role in ("literature-surveyor", "modeler", "numerical-experimenter", "validator")
    }

    del host.files[kernel.sop_stage_path(run_id, "paper-writer", "md")]
    host.delegate_calls.clear()
    kernel.orchestrate_research(TASK_A, resume=True)

    assert "literature-surveyor" not in [c["role"] for c in host.delegate_calls]
    for role, body in upstream.items():
        assert host.files[kernel.sop_stage_path(run_id, role, "json")] == body, (
            f"{role} was still valid evidence and must not have been rewritten"
        )


def test_correction_a_a_missing_mid_pipeline_document_re_runs_from_that_stage(kernel, host):
    """The property is general, not a special case for the paper writer.

    ``ROLE_REQUIRES_DOCUMENT`` currently names only paper-writer, so a missing
    *document* mid-pipeline is tolerated. A missing *record* is not: it is the
    same "this stage is no longer complete" signal, and must re-run that stage.
    """
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    del host.files[kernel.sop_stage_path(run_id, "modeler", "json")]

    host.delegate_calls.clear()
    again = kernel.orchestrate_research(TASK_A, resume=True)

    assert "modeler" in [c["role"] for c in host.delegate_calls], (
        "a stage whose record vanished must be re-run"
    )
    assert again["status"] == "complete", again
    assert host.files[kernel.sop_stage_path(run_id, "modeler", "json")].strip()


def test_correction_a_paper_none_is_reserved_for_a_writer_that_produced_nothing(host):
    """paper=None still means what it should: no document was ever produced.

    The correction removes "must return None" as the definition of recovery. It
    does not remove None as the honest answer when there is genuinely no paper --
    that half was right and stays asserted here.
    """

    class NoDocument(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "paper-writer":
                output = schema_valid_output("paper-writer")
                output.pop("document")
                return {"output": output, "task_status": "completed"}
            return super().delegate(request, **kwargs)

    fake = NoDocument(outputs=_passing_outputs())
    kernel = _load_kernel(fake)
    result = kernel.orchestrate_research(TASK_A)
    assert result["paper"] is None
    assert result["status"] != "complete"


def test_correction_a_a_stale_paper_path_is_never_reported_without_the_work(host):
    """Mutation guard: if the re-run cannot write, the paper is not claimed anyway.

    This is the failure the corrected wording still has to exclude. A host that
    drops the document write on the second attempt must not yield a run that
    keeps pointing at the file that is gone.

    The kernel's answer is stronger than "report None": ``sop_write_stage`` reads
    the document back and raises when it is not there, so the run aborts instead
    of returning at all. Both are acceptable outcomes of the corrected semantics;
    what is asserted here is the property common to them -- no path to a file
    that does not exist -- plus the specific behaviour actually implemented, so
    that a change from "raise" to "return something" cannot pass unnoticed.
    """

    class WriteOnceThenRefuse(FakeHost):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.refuse_documents = False

        def write_file(self, path, content):
            if self.refuse_documents and path.endswith("05-paper-writer.md"):
                return {"path": path, "bytes": 0}  # silently drops the write
            return super().write_file(path, content)

    fake = WriteOnceThenRefuse(outputs=_passing_outputs())
    kernel = _load_kernel(fake)
    first = kernel.orchestrate_research(TASK_A)
    document = kernel.sop_stage_path(first["run_id"], "paper-writer", "md")
    assert first["paper"] == document

    del fake.files[document]
    fake.refuse_documents = True

    with pytest.raises(RuntimeError, match="could not be verified"):
        kernel.orchestrate_research(TASK_A, resume=True)

    # Nothing was invented to stand in for the missing document.
    assert document not in fake.files


# ==========================================================================
# Correction B — a changed prompt makes the old run incompatible, not gone
# ==========================================================================


def test_correction_b_old_run_bytes_survive_a_prompt_change_untouched(kernel, host):
    """Nothing about the earlier run may be deleted or rewritten."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    before = dict(_stage_files(host, original))
    assert before

    kernel.ROLE_MISSIONS["modeler"] += "\nAn edit that changes the method."
    kernel.orchestrate_research(TASK_A, resume=True)

    after = _stage_files(host, original)
    assert after == before, (
        "the previous run's bytes must be preserved exactly across a prompt change"
    )


def test_correction_b_old_run_is_classified_incompatible_not_valid(kernel, host):
    """The corrected classification, asserted directly."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    kernel.ROLE_MISSIONS["validator"] += "\nA different acceptance bar."

    report = kernel.sop_inspect_manifest(original)
    assert report["state"] == kernel.MANIFEST_INCOMPATIBLE, report
    assert report["state"] != kernel.MANIFEST_VALID
    assert report["state"] != kernel.MANIFEST_CORRUPT, (
        "an incompatible run is not a damaged one; conflating them would be a "
        "different, and wrong, story about what happened"
    )
    assert "validator" in (report["reason"] or ""), report["reason"]


def test_correction_b_incompatible_run_stays_readable_and_auditable(kernel, host):
    """"Not valid evidence for the new prompt" must not mean "not readable"."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    kernel.ROLE_MISSIONS["modeler"] += "\nEdited."

    report = kernel.sop_inspect_manifest(original)
    manifest = report["manifest"]
    assert manifest is not None, "the manifest content must still be retrievable"
    assert manifest["run_id"] == original
    assert manifest["task_sha256"] == kernel.sop_task_sha256(TASK_A)
    assert manifest["role_prompt_hashes"], "the hashes it was produced under must remain"

    listed = {entry["run_id"]: entry for entry in kernel.sop_list_runs()}
    assert original in listed, "an incompatible run must still be listed"
    assert listed[original]["state"] == kernel.MANIFEST_INCOMPATIBLE
    assert listed[original]["manifest"]["run_id"] == original


def test_correction_b_read_manifest_returns_none_and_that_is_the_point(kernel, host):
    """sop_read_manifest is the "is this valid for the pipeline I am running" door.

    The old wording asked for the opposite. Locking the corrected behaviour in
    stops a future change from making an incompatible run look valid again.
    """
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    assert kernel.sop_read_manifest(original) is not None

    kernel.ROLE_MISSIONS["paper-writer"] += "\nEdited."
    assert kernel.sop_read_manifest(original) is None, (
        "an incompatible run must not be handed back as a valid manifest"
    )
    # ... and the bytes are still there to be inspected by the auditing door.
    assert kernel.sop_inspect_manifest(original)["manifest"]["run_id"] == original


def test_correction_b_new_prompt_evidence_is_produced_fresh_not_inherited(kernel, host):
    """The new run must do the work; it may not adopt the old stages."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    kernel.ROLE_MISSIONS["modeler"] += "\nEdited."

    host.delegate_calls.clear()
    second = kernel.orchestrate_research(TASK_A, resume=True)

    assert second["run_id"] != original
    assert second["parent_run_id"] == original
    assert [c["role"] for c in host.delegate_calls] == list(kernel.ROLE_ORDER), (
        "every stage under the new prompts must actually run"
    )
    new_manifest = kernel.sop_read_manifest(second["run_id"])
    assert new_manifest["role_prompt_hashes"] == kernel.sop_role_prompt_hashes()
    assert new_manifest["role_prompt_hashes"] != kernel.sop_inspect_manifest(
        original
    )["manifest"]["role_prompt_hashes"]


def test_correction_b_an_incompatible_run_is_never_read_as_a_completed_stage(kernel, host):
    """The strongest form: its stages must not leak into the new run's report."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    kernel.ROLE_MISSIONS["modeler"] += "\nEdited."
    second = kernel.orchestrate_research(TASK_A, resume=True)

    for stage in second["stages"]:
        assert stage["document"].startswith(f"research-runs/{second['run_id']}/"), (
            "a stage in the new run must not point into the incompatible run"
        )
    assert second["run_id"] not in kernel.sop_run_lineage(original)[0]["run_id"]


# ==================================================================
# Run / manifest / history semantics (the properties around A and B)
# ==================================================================


def test_a_rerun_never_silently_overwrites_the_original_evidence(kernel, host):
    """resume=False keeps the earlier attempt byte for byte."""
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    before = dict(_stage_files(host, original))

    second = kernel.orchestrate_research(TASK_A, resume=False)
    assert second["run_id"] != original
    assert _stage_files(host, original) == before
    assert _stage_files(host, second["run_id"]), "the new branch has its own evidence"


def test_rollback_keeps_the_superseded_bytes_and_history_reads_back(kernel, host):
    """A send-back archives, then clears. Both halves are asserted."""
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    modeler_json = kernel.sop_stage_path(run_id, "modeler", "json")
    superseded = host.files[modeler_json]

    event = kernel.sop_clear_from(run_id, "modeler", findings=["assumption unverified"])

    assert event["archived"], "a rollback with content must archive something"
    archived_paths = {entry["archived_to"] for entry in event["archived"]}
    for path in archived_paths:
        assert path.startswith(f"research-runs/{run_id}/history/{event['event_id']}/")
        assert host.files[path].strip(), "an archived file must have content"
    recovered = next(
        host.files[e["archived_to"]] for e in event["archived"]
        if e["from"] == modeler_json
    )
    assert recovered == superseded, "the archive must be byte-identical to what it replaced"

    manifest = kernel.sop_read_manifest(run_id)
    assert manifest["rollbacks"][-1]["event_id"] == event["event_id"]
    assert manifest["rollbacks"][-1]["findings"] == ["assumption unverified"]


def test_history_accumulates_and_earlier_events_are_not_disturbed(kernel, host):
    """A second rollback must not overwrite the first one's archive."""
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]

    one = kernel.sop_clear_from(run_id, "validator")
    kernel.orchestrate_research(TASK_A, resume=True)
    frozen = {e["archived_to"]: host.files[e["archived_to"]] for e in one["archived"]}

    two = kernel.sop_clear_from(run_id, "validator")
    assert two["event_id"] != one["event_id"]
    for path, body in frozen.items():
        assert host.files[path] == body, "an earlier rollback's archive was disturbed"

    manifest = kernel.sop_read_manifest(run_id)
    assert [e["event_id"] for e in manifest["rollbacks"]] == [one["event_id"], two["event_id"]]


def test_rollback_is_refused_on_a_run_whose_manifest_is_not_valid(kernel, host):
    """History may not be written against a run the kernel cannot vouch for."""
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    host.files[kernel.sop_manifest_path(run_id)] = "{ not json"
    with pytest.raises(ValueError, match="corrupt"):
        kernel.sop_clear_from(run_id, "modeler")


def test_artifact_hash_is_recorded_and_tracks_the_document(kernel, host):
    """document_sha256 must describe the document that is actually on disk."""
    import hashlib

    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    record = json.loads(host.files[kernel.sop_stage_path(run_id, "paper-writer", "json")])
    body = host.files[kernel.sop_stage_path(run_id, "paper-writer", "md")]
    assert record["document_sha256"] == hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    assert record["document_path"] == kernel.sop_stage_path(run_id, "paper-writer", "md")


def test_stage_binding_covers_run_task_and_role(kernel, host):
    """Each of the three binding fields must independently disqualify a stage."""
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    digest = kernel.sop_task_sha256(TASK_A)
    path = kernel.sop_stage_path(run_id, "modeler", "json")
    good = json.loads(host.files[path])
    assert kernel.sop_read_stage(run_id, "modeler", digest) is not None

    for field, value in (
        ("run_id", "0" * 16),
        ("task_sha256", "0" * 64),
        ("role", "validator"),
        ("state", "in-progress"),
    ):
        tampered = dict(good)
        tampered[field] = value
        host.files[path] = json.dumps(tampered)
        assert kernel.sop_read_stage(run_id, "modeler", digest) is None, (
            f"a stage with a wrong {field} must not be read as evidence"
        )
    host.files[path] = json.dumps(good)
    assert kernel.sop_read_stage(run_id, "modeler", digest) is not None


def test_manifest_records_the_prompt_hashes_the_run_was_produced_under(kernel, host):
    """Without this the incompatible classification has nothing to compare."""
    first = kernel.orchestrate_research(TASK_A)
    manifest = kernel.sop_read_manifest(first["run_id"])
    assert manifest["role_prompt_hashes"] == kernel.sop_role_prompt_hashes()
    assert set(manifest["role_prompt_hashes"]) == set(kernel.ROLE_ORDER)
    assert manifest["pipeline_version"] == kernel.PIPELINE_VERSION
    assert manifest["schema_version"] == kernel.SCHEMA_VERSION
    assert manifest["task_sha256"] == kernel.sop_task_sha256(TASK_A)


def test_status_reports_the_manifest_state_rather_than_hiding_it(kernel, host):
    """sop_status must surface incompatibility instead of reporting an empty run."""
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    assert kernel.sop_status(run_id)["manifest_state"] == kernel.MANIFEST_VALID

    kernel.ROLE_MISSIONS["modeler"] += "\nEdited."
    status = kernel.sop_status(run_id)
    assert status["manifest_state"] == kernel.MANIFEST_INCOMPATIBLE
    assert status["manifest_reason"]
    assert status["manifest"] is not None, "the manifest must still be shown"
