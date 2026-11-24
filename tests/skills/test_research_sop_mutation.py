"""Mutation tests: each evidence-chain guarantee must be load-bearing.

A passing suite proves the code does what the tests say today. It does not prove
the tests would notice if the code stopped. These do: each case takes the shipped
kernel, removes exactly one guarantee, loads the damaged copy, and asserts the
property actually breaks.

A mutation that leaves everything passing is the finding. It means either the
guarantee was never doing anything, or nothing tests it -- and both are ways an
evidence chain quietly stops being one.

The mutations correspond to the properties the run/manifest/history audit
depends on:

1. an incompatible manifest must not read back as valid;
2. a document that no longer matches its record must invalidate its stage;
3. a rollback must verify its archive before clearing anything;
4. a rollback must archive before it clears;
5. changed role prompts must make a run incompatible;
6. a corrupt manifest must not be treated as absent;
7. an incompatible run must not be resumed in place;
8. a manifest must be checked against its own task text, not just for presence;
9. a stage document must be re-hashed on read, not merely found non-empty;
10. a rollback archive must be re-hashed when audited, not only when written.

Nothing here modifies the shipped kernel: each mutant is written to a temporary
skill root and loaded through ``LEO_SKILLS_ROOT``.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from test_research_sop import (  # noqa: F401
    FakeHost,
    TASK_A,
    _load_kernel,
    _passing_outputs,
    _skill_root,
    schema_valid_output,
)

KERNEL = _skill_root() / "kernel.py"


def _mutant(tmp_path: pathlib.Path, monkeypatch, old: str, new: str):
    """Load a copy of the shipped kernel with one guarantee removed."""
    source = KERNEL.read_text(encoding="utf-8")
    assert source.count(old) == 1, (
        f"mutation anchor is not unique ({source.count(old)} matches); "
        "update this test rather than weakening the anchor"
    )
    root = tmp_path / "skills" / "research-sop"
    root.mkdir(parents=True)
    (root / "kernel.py").write_text(source.replace(old, new), encoding="utf-8")
    monkeypatch.setenv("LEO_SKILLS_ROOT", str(tmp_path / "skills"))
    host = FakeHost(outputs=_passing_outputs())
    return _load_kernel(host), host


def _pristine():
    host = FakeHost(outputs=_passing_outputs())
    return _load_kernel(host), host


# ------------------------------------------------------------------ mutants


def test_mutation_read_manifest_ignoring_state_is_caught(tmp_path, monkeypatch):
    """(1) If sop_read_manifest stops filtering, an incompatible run reads valid."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        'return report["manifest"] if report["state"] == MANIFEST_VALID else None',
        'return report["manifest"]',
    )
    first = kernel.orchestrate_research(TASK_A)
    kernel.ROLE_MISSIONS["modeler"] += "\nEdited."
    assert kernel.sop_read_manifest(first["run_id"]) is not None, (
        "the mutation did not take effect"
    )
    # ... which is exactly what test_research_sop_semantics asserts must not happen.
    with pytest.raises(AssertionError):
        assert kernel.sop_read_manifest(first["run_id"]) is None


def test_mutation_dropping_the_document_requirement_is_caught(tmp_path, monkeypatch):
    """(2) Without the document check, a vanished paper is still 'complete'."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        "    if not sop_document_ok(run_id, role, record):",
        "    if False:",
    )
    first = kernel.orchestrate_research(TASK_A)
    document = kernel.sop_stage_path(first["run_id"], "paper-writer", "md")
    del host.files[document]

    host.delegate_calls.clear()
    kernel.orchestrate_research(TASK_A, resume=True)
    assert host.delegate_calls == [], "the mutation did not take effect"
    assert document not in host.files, (
        "with the guarantee removed the run claims a paper whose file is gone -- "
        "which is the failure the corrected semantics forbid"
    )


def test_mutation_unverified_archive_is_caught(tmp_path, monkeypatch):
    """(3) Archiving without reading back lets a rollback lose evidence silently."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        "        readback = sop_read_text(target)\n        if readback != body:",
        "        readback = sop_read_text(target)\n        if False:",
    )

    class DropsArchive(FakeHost):
        def write_file(self, path, content):
            if "/history/" in path:
                return {"path": path, "bytes": 0}  # silently discards the archive
            return super().write_file(path, content)

    fake = DropsArchive(outputs=_passing_outputs())
    mutated = _load_kernel(fake)
    first = mutated.orchestrate_research(TASK_A)
    superseded = fake.files[mutated.sop_stage_path(first["run_id"], "modeler", "json")]
    event = mutated.sop_clear_from(first["run_id"], "modeler")

    for entry in event["archived"]:
        assert entry["archived_to"] not in fake.files, "the mutation did not take effect"
    assert fake.files[mutated.sop_stage_path(first["run_id"], "modeler", "json")] == ""
    assert superseded, (
        "with verification removed the manifest records an archive that does not "
        "exist, and the superseded bytes are gone"
    )


def test_mutation_clearing_without_archiving_is_caught(tmp_path, monkeypatch):
    """(4) Clearing first destroys exactly what the rollback is supposed to keep."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        "    archived = []\n    for target_role in downstream:\n"
        "        archived.extend(sop_archive_stage(run_id, target_role, event_id))",
        "    archived = []",
    )
    first = kernel.orchestrate_research(TASK_A)
    event = kernel.sop_clear_from(first["run_id"], "modeler")
    assert event["archived"] == [], "the mutation did not take effect"
    history = [path for path in host.files if "/history/" in path]
    assert history == [], (
        "nothing was archived, so the superseded modelling and results are gone. "
        "The pristine kernel must archive and verify before it clears"
    )


def test_mutation_ignoring_prompt_hashes_is_caught(tmp_path, monkeypatch):
    """(5) Without the prompt-hash comparison, two methods merge under one run."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        '        changed = sorted(\n'
        '            role for role, digest in current.items() if stored.get(role) != digest\n'
        '        )',
        '        changed = []',
    )
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    kernel.ROLE_MISSIONS["modeler"] += "\nA different method entirely."

    host.delegate_calls.clear()
    second = kernel.orchestrate_research(TASK_A, resume=True)
    assert second["run_id"] == original, "the mutation did not take effect"
    assert host.delegate_calls == [], (
        "with the guarantee removed, stages produced under the old prompts are "
        "reported as results of the new pipeline, with nothing re-run"
    )


def test_mutation_treating_corrupt_as_missing_survives_on_a_second_defence(
    tmp_path, monkeypatch
):
    """(6a) A surviving mutant, recorded rather than hidden.

    Relabelling unparseable JSON from CORRUPT to MISSING does *not* destroy the
    guarantee. ``sop_resolve_run`` finds the run through ``sop_run_branches``,
    which asks whether the directory has anything in it, not whether its manifest
    parses. An unrecognised state therefore falls through to the fork path: the
    damaged bytes survive and the old stages are not adopted.

    A mutation test whose mutant lives is a result about the code, not a failure
    of the test. Written down here because "we mutated it and everything still
    passed" is otherwise indistinguishable from a test that checks nothing --
    and because if ``sop_run_branches`` is ever changed, this is where the second
    defence was recorded.
    """
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        '            "state": MANIFEST_CORRUPT,\n'
        '            "manifest": None,\n'
        '            "reason": f"manifest is not valid JSON: {error}",',
        '            "state": MANIFEST_MISSING,\n'
        '            "manifest": None,\n'
        '            "reason": f"manifest is not valid JSON: {error}",',
    )
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    damaged = "{ not json"
    host.files[kernel.sop_manifest_path(run_id)] = damaged

    second = kernel.orchestrate_research(TASK_A, resume=True)
    assert host.files[kernel.sop_manifest_path(run_id)] == damaged, (
        "the damaged bytes must survive even with the classification weakened"
    )
    assert second["run_id"] != run_id, "the run must have been forked, not resumed"


def test_mutation_hiding_a_damaged_run_from_branch_discovery_is_caught(
    tmp_path, monkeypatch
):
    """(6b) The mutation that does break it: make the damaged run invisible.

    If ``sop_run_branches`` counted only runs whose manifest reads back valid, a
    corrupt manifest would make its own run disappear. ``sop_resolve_run`` would
    then take the "no branches yet" path, write a fresh manifest over the damaged
    one, and adopt every stage file sitting beside it as this task's evidence.
    That is the original contamination bug, reachable through a different door.
    """
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        "        if sop_run_dir_exists(run_id):\n            found.append(run_id)",
        "        if sop_read_manifest(run_id) is not None:\n            found.append(run_id)",
    )
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    damaged = "{ not json"
    host.files[kernel.sop_manifest_path(run_id)] = damaged

    host.delegate_calls.clear()
    second = kernel.orchestrate_research(TASK_A, resume=True)

    assert second["run_id"] == run_id, "the mutation did not take effect"
    assert host.files[kernel.sop_manifest_path(run_id)] != damaged, (
        "with the guarantee removed the damaged manifest is overwritten in place"
    )
    assert host.delegate_calls == [], (
        "and the stage files beside it are adopted as this task's evidence with "
        "nothing re-run -- which is exactly the contamination the pristine kernel "
        "refuses by raising"
    )


def test_mutation_resuming_an_incompatible_run_is_caught(tmp_path, monkeypatch):
    """(7) Resuming instead of forking adopts another pipeline's stages."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        "            return sop_fork_run(task, parent_run_id=latest, reason=report[\"reason\"]), False",
        "            return report[\"manifest\"], True",
    )
    first = kernel.orchestrate_research(TASK_A)
    original = first["run_id"]
    kernel.ROLE_MISSIONS["validator"] += "\nA looser bar."

    host.delegate_calls.clear()
    second = kernel.orchestrate_research(TASK_A, resume=True)
    assert second["run_id"] == original, "the mutation did not take effect"
    assert host.delegate_calls == [], (
        "the incompatible run was resumed in place and its stages adopted"
    )


def test_mutation_not_checking_manifest_against_its_task_text_is_caught(
    tmp_path, monkeypatch
):
    """(8) F-007. Without self-consistency, audit and execution split."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        '    if manifest.get("task_sha256") != recomputed:',
        "    if False:",
    )
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    path = kernel.sop_manifest_path(run_id)
    manifest = json.loads(host.files[path])
    manifest["task_sha256"] = "0" * 64
    host.files[path] = json.dumps(manifest)

    assert kernel.sop_inspect_manifest(run_id)["state"] == kernel.MANIFEST_VALID
    with pytest.raises(ValueError):
        kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)


def test_mutation_not_rehashing_the_document_on_read_is_caught(tmp_path, monkeypatch):
    """(9) F-001. Without the digest comparison, rewritten bytes are evidence."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        "    actual = sop_document_digest(body)\n    if actual != claimed:",
        "    actual = sop_document_digest(body)\n    if False:",
    )
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    document = kernel.sop_stage_path(run_id, "paper-writer", "md")
    body = host.files[document]
    host.files[document] = body[:-1] + ("X" if not body.endswith("X") else "Y")
    assert next(
        s for s in kernel.sop_status(run_id)["stages"]
        if s["role"] == "paper-writer"
    )["complete"] is True

    host.delegate_calls.clear()
    kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)
    assert host.delegate_calls == []


def _same_length_rewrite(text):
    victim = text[-1]
    return text[:-1] + ("X" if victim != "X" else "Y")


def test_mutation_not_rehashing_history_on_audit_is_caught(tmp_path, monkeypatch):
    """(10) F-002. Without the re-hash, rewritten history audits clean."""
    kernel, host = _mutant(
        tmp_path, monkeypatch,
        '    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]\n'
        "    if actual != claimed:",
        '    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]\n'
        "    if False:",
    )
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]
    event = kernel.sop_clear_from(run_id, "modeler", findings=["mutation probe"])
    target = event["archived"][0]["archived_to"]
    host.files[target] = _same_length_rewrite(host.files[target])
    assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_OK
    assert kernel.sop_status(run_id)["history_state"] == kernel.HISTORY_OK


# ------------------------------------------------- the pristine kernel is fine


@pytest.mark.parametrize(
    "check",
    [
        "incompatible-not-valid",
        "missing-document-reruns",
        "rollback-archives",
        "corrupt-fails-closed",
        "incompatible-forks",
        "forged-manifest-is-corrupt",
        "tampered-document-reruns",
        "rewritten-history-is-corrupt",
    ],
)
def test_the_pristine_kernel_holds_every_mutated_property(check):
    """The other half of a mutation test: the real kernel must pass all of them.

    Without this, a mutation test can pass because the property never held.
    """
    kernel, host = _pristine()
    first = kernel.orchestrate_research(TASK_A)
    run_id = first["run_id"]

    if check == "incompatible-not-valid":
        kernel.ROLE_MISSIONS["modeler"] += "\nEdited."
        assert kernel.sop_read_manifest(run_id) is None
        assert kernel.sop_inspect_manifest(run_id)["state"] == kernel.MANIFEST_INCOMPATIBLE

    elif check == "missing-document-reruns":
        del host.files[kernel.sop_stage_path(run_id, "paper-writer", "md")]
        host.delegate_calls.clear()
        again = kernel.orchestrate_research(TASK_A, resume=True)
        assert [c["role"] for c in host.delegate_calls] == ["paper-writer"]
        assert host.files[again["paper"]].strip()

    elif check == "rollback-archives":
        superseded = host.files[kernel.sop_stage_path(run_id, "modeler", "json")]
        event = kernel.sop_clear_from(run_id, "modeler")
        assert event["archived"]
        recovered = next(
            host.files[e["archived_to"]] for e in event["archived"]
            if e["from"] == kernel.sop_stage_path(run_id, "modeler", "json")
        )
        assert recovered == superseded

    elif check == "corrupt-fails-closed":
        damaged = "{ not json"
        host.files[kernel.sop_manifest_path(run_id)] = damaged
        with pytest.raises(ValueError, match="corrupt"):
            kernel.orchestrate_research(TASK_A, resume=True)
        assert host.files[kernel.sop_manifest_path(run_id)] == damaged

    elif check == "incompatible-forks":
        kernel.ROLE_MISSIONS["modeler"] += "\nEdited."
        host.delegate_calls.clear()
        second = kernel.orchestrate_research(TASK_A, resume=True)
        assert second["run_id"] != run_id
        assert second["parent_run_id"] == run_id
        assert host.delegate_calls

    elif check == "forged-manifest-is-corrupt":
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["task_sha256"] = "0" * 64
        host.files[path] = json.dumps(manifest)
        assert kernel.sop_inspect_manifest(run_id)["state"] == kernel.MANIFEST_CORRUPT
        with pytest.raises(ValueError):
            kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)

    elif check == "tampered-document-reruns":
        document = kernel.sop_stage_path(run_id, "paper-writer", "md")
        body = host.files[document]
        host.files[document] = body[:-1] + ("X" if not body.endswith("X") else "Y")
        paper = next(
            s for s in kernel.sop_status(run_id)["stages"]
            if s["role"] == "paper-writer"
        )
        assert paper["complete"] is False
        assert paper["document_state"] == kernel.DOCUMENT_HASH_MISMATCH
        host.delegate_calls.clear()
        again = kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)
        assert [c["role"] for c in host.delegate_calls] == ["paper-writer"]
        assert host.files[again["paper"]].strip()

    elif check == "rewritten-history-is-corrupt":
        event = kernel.sop_clear_from(run_id, "modeler", findings=["pristine probe"])
        target = event["archived"][0]["archived_to"]
        intact = host.files[target]
        host.files[target] = _same_length_rewrite(intact)
        history = kernel.sop_inspect_history(run_id)
        assert history["state"] == kernel.HISTORY_CORRUPT
        assert any(
            a["state"] == kernel.ARCHIVE_HASH_MISMATCH
            for a in history["archives"]
        )
        assert kernel.sop_status(run_id)["history_state"] == kernel.HISTORY_CORRUPT
        del host.files[target]
        assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_CORRUPT
        host.files[target] = intact
        assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_OK
