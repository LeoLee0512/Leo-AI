"""Adversarial integrity tests for research-sop (P0-2 hardening, round 2).

Reconstructed from the nine failures enumerated in
``LeoAIStudio-P0-Gate二次复核报告.md`` §2.4 and detailed in §5. The reviewer's own
``test_research_sop_integrity_adversarial.py`` was referenced but not supplied,
so these are an independent reconstruction from the described behaviour. They
should be run alongside the original file when it arrives, not instead of it.

**This file is not the reviewer's file, and passing it is not independent
confirmation by the reviewer.** That distinction is recorded in
``manifests/test-suites.json`` and enforced by ``tests/test_suite_provenance.py``:
the reviewer's suite has a reserved path of its own, this one may not be renamed
into it, and none of these tests may be deleted when it arrives. The outstanding
confirmation is carried as a release caveat, not as something P0-2 already has.

Two statements from the review turned out to be wrong as written, and the
corrected wording is asserted in ``test_research_sop_semantics.py`` rather than
here, so this file stays comparable with the reviewer's original:

- a vanished stage document means **re-run that stage and produce a real new
  document**, not "return ``paper=None``";
- a changed role prompt makes an old run **``incompatible`` but still readable
  and byte-intact**, not a run that keeps counting as valid evidence.

Each test states the failure it locks out. The theme is that separating tasks by
path was necessary but nowhere near sufficient: an evidence chain also needs
trustworthy state, validated schemas, artifacts that exist, history that cannot
be overwritten, version compatibility and path safety.
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


# ------------------------------------------------------------------- (1)


def test_corrupt_manifest_fails_closed_and_is_not_overwritten(kernel, host):
    """A damaged manifest must never be treated as an absent one.

    Before: sop_read_manifest swallowed the JSON error and returned None,
    'missing' and 'corrupt' collapsed together, a fresh manifest was written over
    the run id, and the stage files beside it were then reported as this task's
    completed evidence with zero delegate calls.
    """
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    manifest_path = kernel.sop_manifest_path(run_id)
    damaged = "{ this is not json"
    host.files[manifest_path] = damaged

    host.delegate_calls.clear()
    with pytest.raises(ValueError, match="corrupt"):
        kernel.orchestrate_research(TASK_A, resume=True)

    assert host.delegate_calls == [], "nothing may run off a corrupt manifest"
    assert host.files[manifest_path] == damaged, "the damaged bytes must be preserved"


def test_empty_manifest_is_corrupt_not_missing(kernel, host):
    """A half-written manifest is damage, not absence."""
    first = kernel.orchestrate_research(TASK_A)
    host.files[kernel.sop_manifest_path(first["run_id"])] = ""
    with pytest.raises(ValueError, match="corrupt"):
        kernel.orchestrate_research(TASK_A, resume=True)


# ------------------------------------------------------------------- (2)


def test_stage_without_binding_fields_is_not_evidence(kernel, host):
    """Exact binding. A stage missing run_id or task_sha256 is not evidence.

    Before: the check allowed None ('record.get("run_id") not in (None, run_id)'),
    so an unbound or hand-placed stage was accepted as a completed result.
    """
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    digest = first["task_sha256"]
    path = kernel.sop_stage_path(run_id, "modeler")

    record = json.loads(host.files[path])
    assert record["run_id"] == run_id and record["task_sha256"] == digest

    for mutation in ({"run_id": None}, {"task_sha256": None}, {"run_id": "0" * 16},
                     {"task_sha256": "0" * 64}, {"role": "validator"}):
        broken = dict(record)
        broken.update(mutation)
        host.files[path] = json.dumps(broken)
        assert kernel.sop_read_stage(run_id, "modeler", digest) is None, mutation


def test_unbound_stage_is_rerun_rather_than_trusted(kernel, host):
    """Stripping the binding forces the stage to run again, not to be inherited."""
    first = kernel.orchestrate_research(TASK_A)
    run_id, digest = first["run_id"], first["task_sha256"]
    path = kernel.sop_stage_path(run_id, "modeler")
    record = json.loads(host.files[path])
    record.pop("task_sha256")
    host.files[path] = json.dumps(record)

    host.delegate_calls.clear()
    kernel.orchestrate_research(TASK_A, resume=True)
    assert "modeler" in [c["role"] for c in host.delegate_calls]


# ------------------------------------------------------------------- (3)


def test_failed_delegate_is_never_complete(host):
    """task_status=failed with an error must not be written as a complete stage.

    Before: state defaulted to 'complete' and only flipped when output was None
    *and* there was no final message, so a failure carrying any output at all was
    recorded as a finished stage.
    """

    class Failing(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "modeler":
                return {
                    "output": schema_valid_output("modeler"),
                    "task_status": "failed",
                    "error": "boom",
                }
            return super().delegate(request, **kwargs)

    fake = Failing(outputs=_passing_outputs())
    k = _load_kernel(fake)
    result = k.orchestrate_research(TASK_A)
    assert result["status"] == "blocked", result
    assert result["paper"] is None
    record = json.loads(fake.files[k.sop_stage_path(result["run_id"], "modeler")])
    assert record["state"] == "incomplete"
    assert any("task_status" in p for p in record["problems"]), record["problems"]
    assert record["error"] == "boom", "the raw failure payload must be kept"


@pytest.mark.parametrize("field,value", [("stop_reason", "timeout"), ("error", "nope")])
def test_failure_signals_block_completion(host, field, value):
    """A failure stop_reason or a non-empty error blocks the stage."""

    class Signalling(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            result = super().delegate(request, **kwargs)
            if role == "modeler":
                result[field] = value
            return result

    fake = Signalling(outputs=_passing_outputs())
    k = _load_kernel(fake)
    assert k.orchestrate_research(TASK_A)["status"] == "blocked"


# ------------------------------------------------------------------- (4)


def test_output_schema_is_revalidated_locally(host):
    """A malformed output must not pass just because the host accepted it.

    Before: output_schema was handed to host.delegate and the response was then
    trusted. A modeler returning only {"document": ...} -- no summary, equations
    or assumptions -- still produced a complete pipeline.
    """

    class Malformed(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "modeler":
                return {
                    "output": {"document": "# missing required fields"},
                    "task_status": "completed",
                }
            return super().delegate(request, **kwargs)

    fake = Malformed(outputs=_passing_outputs())
    k = _load_kernel(fake)
    result = k.orchestrate_research(TASK_A)
    assert result["status"] == "blocked", result
    record = json.loads(fake.files[k.sop_stage_path(result["run_id"], "modeler")])
    assert record["state"] == "incomplete"
    problems = " ".join(record["problems"])
    for key in ("summary", "equations", "assumptions"):
        assert key in problems, problems


def test_validator_verdict_must_be_a_known_value(host):
    """An unknown verdict is a failure to validate, not a pass."""

    class Weird(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "validator":
                return {
                    "output": schema_valid_output("validator", verdict="probably fine"),
                    "task_status": "completed",
                }
            return super().delegate(request, **kwargs)

    fake = Weird(outputs=_passing_outputs())
    k = _load_kernel(fake)
    result = k.orchestrate_research(TASK_A)
    assert result["status"] != "complete", result
    assert result["validator"] != "pass"


# ------------------------------------------------------------------- (5)


def test_paper_path_only_when_the_document_exists(host):
    """paper != None must mean a document is really there.

    Before: paper was returned whenever the paper-writer role appeared in the
    completed set, but the .md was only written when the output carried a
    'document'. A writer that satisfied the required keys without a document
    produced status=complete and a path to a file that did not exist.
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
    k = _load_kernel(fake)
    result = k.orchestrate_research(TASK_A)
    assert result["paper"] is None, result
    assert result["status"] != "complete"


def test_missing_paper_document_forces_a_rerun_rather_than_a_stale_claim(kernel, host):
    """A vanished document must re-run the stage, not be reported as still done.

    The property is not "paper becomes None" -- re-running and producing a real
    document is a perfectly good outcome. The property is that the orchestrator
    must not keep pointing at a paper whose file is no longer there without
    doing the work again.
    """
    first = kernel.orchestrate_research(TASK_A)
    assert first["paper"] is not None
    host.files[kernel.sop_stage_path(first["run_id"], "paper-writer", "md")] = ""

    host.delegate_calls.clear()
    again = kernel.orchestrate_research(TASK_A, resume=True)
    assert "paper-writer" in [c["role"] for c in host.delegate_calls], (
        "the stage whose document disappeared must be re-run"
    )
    # Having actually re-run it, the document is real again.
    assert again["paper"] is not None
    assert host.files[again["paper"]].strip()


def test_missing_paper_document_is_not_reported_as_complete_without_a_rerun(host):
    """When the writer cannot produce a document, the run must not claim one."""

    class NeverWritesDocument(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "paper-writer":
                output = schema_valid_output("paper-writer")
                output.pop("document")
                return {"output": output, "task_status": "completed"}
            return super().delegate(request, **kwargs)

    fake = NeverWritesDocument(outputs=_passing_outputs())
    k = _load_kernel(fake)
    result = k.orchestrate_research(TASK_A)
    assert result["paper"] is None
    assert result["status"] != "complete"


# ------------------------------------------------------------------- (6)


def test_rollback_archives_evidence_instead_of_blanking_it(host):
    """A send-back must preserve the superseded work, byte for byte.

    Before: rollback wrote an empty string over each downstream file and recorded
    only the path. The superseded model assumptions, results and the
    pre-rejection version were destroyed; a path in a manifest is not evidence.
    """
    verdicts = iter(["revise", "pass"])

    class Reviewing(FakeHost):
        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "validator":
                verdict = next(verdicts, "pass")
                return {
                    "output": schema_valid_output(
                        "validator",
                        verdict=verdict,
                        findings=["boundary condition unverified"],
                        send_back_to="modeler",
                    ),
                    "task_status": "completed",
                }
            return super().delegate(request, **kwargs)

    fake = Reviewing(outputs={})
    k = _load_kernel(fake)
    result = k.orchestrate_research(TASK_A, max_rollbacks=2)
    assert result["rollbacks"] == 1, result

    manifest = k.sop_read_manifest(result["run_id"])
    events = manifest["rollbacks"]
    assert len(events) == 1, events
    event = events[0]
    assert event["findings"] == ["boundary condition unverified"]
    assert event["archived"], "the rollback must archive what it superseded"

    for entry in event["archived"]:
        archived = fake.files.get(entry["archived_to"])
        assert archived, f"archived copy missing at {entry['archived_to']}"
        assert archived.strip(), "archived copy must not be blank"
        assert entry["sha256"], "the archive must record a hash"


def test_rollback_fails_closed_when_archiving_fails(host):
    """If evidence cannot be archived, the rollback must abort, not proceed."""
    verdicts = iter(["revise", "pass"])

    class ArchiveBreaks(FakeHost):
        def write_file(self, path, content):
            if "/history/" in path:
                raise OSError("disk full")
            return super().write_file(path, content)

        def delegate(self, request, **kwargs):
            role = kwargs.get("name")
            self.delegate_calls.append({"role": role, "request": request})
            if role == "validator":
                return {
                    "output": schema_valid_output(
                        "validator", verdict=next(verdicts, "pass"),
                        findings=["x"], send_back_to="modeler",
                    ),
                    "task_status": "completed",
                }
            return super().delegate(request, **kwargs)

    fake = ArchiveBreaks(outputs={})
    k = _load_kernel(fake)
    with pytest.raises(OSError):
        k.orchestrate_research(TASK_A, max_rollbacks=2)
    # The stage that was about to be superseded is still intact.
    runs = [r for r in k.sop_list_runs() if r["state"] == "valid"]
    assert runs
    modeler = fake.files.get(k.sop_stage_path(runs[0]["run_id"], "modeler"))
    assert modeler and modeler.strip(), "the old stage must survive a failed rollback"


# ------------------------------------------------------------------- (7)


@pytest.mark.parametrize(
    "roles",
    [
        ["paper-writer", "literature-surveyor"],       # out of order
        ["modeler", "modeler"],                        # repeated
        ["validator", "modeler"],                      # out of order
    ],
)
def test_roles_must_be_an_ordered_unique_subsequence(kernel, roles):
    """An arbitrary role list is not a pipeline."""
    with pytest.raises(ValueError):
        kernel.orchestrate_research(TASK_A, roles=roles)


def test_ordered_subsequence_is_accepted(kernel, host):
    """Skipping roles is fine; reordering them is not."""
    result = kernel.orchestrate_research(
        TASK_A, roles=["literature-surveyor", "numerical-experimenter"]
    )
    assert result["status"] == "partial"


# ------------------------------------------------------------------- (8)


@pytest.mark.parametrize(
    "run_id",
    ["../evil", "a/b", "..", ".", "", "0" * 15, "0" * 16 + "-r0", "ZZZZ" * 4,
     "0" * 16 + "/../../x"],
)
def test_run_id_cannot_escape_the_runs_directory(kernel, run_id):
    """run_id is a strict fullmatch; traversal and stray separators are refused."""
    with pytest.raises(ValueError):
        kernel.sop_run_dir(run_id)


@pytest.mark.parametrize("suffix", ["exe", "../x", "json/../..", "", "py"])
def test_stage_suffix_is_an_enum(kernel, suffix):
    """Only the record and the document may be addressed."""
    with pytest.raises(ValueError):
        kernel.sop_stage_path("0" * 16, "modeler", suffix)


def test_valid_run_id_stays_inside_its_directory(kernel):
    run_id = "0" * 16
    path = kernel.sop_stage_path(run_id, "modeler", "md")
    assert path.startswith(f"{kernel.RUNS_DIR}/{run_id}/")
    assert ".." not in path


# ------------------------------------------------------------------- (9)


def test_changed_role_prompt_does_not_silently_reuse_old_stages(kernel, host):
    """A different pipeline is a different experiment.

    Before: resume compared only the task hash, so editing ROLE_MISSIONS and
    resuming reused all five stages with zero delegate calls, mixing results
    produced by two different methods under one run.
    """
    first = kernel.orchestrate_research(TASK_A)
    original_run = first["run_id"]

    kernel.ROLE_MISSIONS["modeler"] = kernel.ROLE_MISSIONS["modeler"] + "\nExtra instruction."
    host.delegate_calls.clear()

    second = kernel.orchestrate_research(TASK_A, resume=True)
    assert second["run_id"] != original_run, "an incompatible run must not be resumed in place"
    assert second["parent_run_id"] == original_run, second
    assert host.delegate_calls, "the new pipeline must actually run"
    # The old run is still on disk. sop_read_manifest returns None for it now,
    # and that is correct: under the edited prompts it is no longer a *valid*
    # manifest for this pipeline. It must still be readable as evidence, and it
    # must be classified as incompatible rather than quietly discarded.
    old = kernel.sop_inspect_manifest(original_run)
    assert old["state"] == kernel.MANIFEST_INCOMPATIBLE, old
    assert old["manifest"]["run_id"] == original_run
    assert "modeler" in (old["reason"] or ""), old["reason"]


def test_incompatible_run_can_be_made_to_fail_closed(kernel, host):
    """The fork policy is explicit and can be set to refuse instead."""
    kernel.orchestrate_research(TASK_A)
    kernel.ROLE_MISSIONS["modeler"] = kernel.ROLE_MISSIONS["modeler"] + "\nAnother edit."
    with pytest.raises(ValueError, match="different pipeline"):
        kernel.orchestrate_research(TASK_A, resume=True, on_incompatible="fail")


# ------------------------------------------------------- branch semantics


def test_resume_continues_the_latest_branch_not_the_base(kernel, host):
    """After a rework, resume must not silently fall back to the original run."""
    first = kernel.orchestrate_research(TASK_A)
    base = first["run_id"]
    forked = kernel.orchestrate_research(TASK_A, resume=False)
    assert forked["run_id"] != base

    resumed = kernel.orchestrate_research(TASK_A, resume=True)
    assert resumed["run_id"] == forked["run_id"], "resume followed the wrong branch"


def test_explicit_run_id_resumes_exactly_that_run(kernel, host):
    """The user can name the branch to continue."""
    first = kernel.orchestrate_research(TASK_A)
    base = first["run_id"]
    kernel.orchestrate_research(TASK_A, resume=False)

    pinned = kernel.orchestrate_research(TASK_A, resume=True, run_id=base)
    assert pinned["run_id"] == base
    assert pinned["resumed"] is True


def test_explicit_run_id_from_another_task_is_refused(kernel, host):
    """A run id belonging to a different question cannot be borrowed."""
    other = kernel.orchestrate_research(TASK_B)
    with pytest.raises(ValueError, match="different research question"):
        kernel.orchestrate_research(TASK_A, run_id=other["run_id"])


def test_lineage_is_walkable(kernel, host):
    """A fork records where it came from, and the chain can be followed back."""
    first = kernel.orchestrate_research(TASK_A)
    forked = kernel.orchestrate_research(TASK_A, resume=False)
    chain = kernel.sop_run_lineage(forked["run_id"])
    assert [entry["run_id"] for entry in chain] == [forked["run_id"], first["run_id"]]


# --------------------------------------------------- write-failure safety


def test_manifest_write_failure_is_not_swallowed(host):
    """If the manifest cannot be persisted, the run must not proceed."""

    class NoManifest(FakeHost):
        def write_file(self, path, content):
            if path.endswith("manifest.json"):
                raise OSError("read-only workspace")
            return super().write_file(path, content)

    fake = NoManifest(outputs=_passing_outputs())
    k = _load_kernel(fake)
    with pytest.raises(OSError):
        k.orchestrate_research(TASK_A)


def test_legacy_fixed_path_stages_are_never_adopted(kernel, host):
    """Material from the old unbound layout must not become evidence."""
    host.files["research-sop/02-modeler.json"] = json.dumps(
        {"role": "modeler", "state": "complete", "output": schema_valid_output("modeler")}
    )
    host.delegate_calls.clear()
    result = kernel.orchestrate_research(TASK_A)
    assert "modeler" in [c["role"] for c in host.delegate_calls], "legacy stage was adopted"
    assert result["run_id"].startswith(kernel.sop_task_sha256(TASK_A)[:16])
