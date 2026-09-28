"""F-001 document integrity and the corrected B08 attempt contract."""

from __future__ import annotations

import json

from test_research_sop import (  # noqa: F401
    FakeHost,
    TASK_A,
    _load_kernel,
    _passing_outputs,
    host,
    kernel,
    schema_valid_output,
)

PAPER = "paper-writer"


def _complete(kernel):
    result = kernel.orchestrate_research(TASK_A)
    assert result["status"] == "complete", result.get("findings")
    return result


def _paper_stage(kernel, run_id):
    return next(
        stage for stage in kernel.sop_status(run_id)["stages"]
        if stage["role"] == PAPER
    )


def _same_length_rewrite(text):
    victim = text[-1]
    return text[:-1] + ("X" if victim != "X" else "Y")


class TestStageDocumentIsBoundToItsDigest:
    def test_untouched_document_remains_valid(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        stage = _paper_stage(kernel, run_id)
        assert stage["complete"] is True
        assert stage["document_state"] == kernel.DOCUMENT_OK
        assert stage["document_problem"] is None

    def test_a_deleted_document_invalidates_the_stage(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        del host.files[kernel.sop_stage_path(run_id, PAPER, "md")]
        stage = _paper_stage(kernel, run_id)
        assert stage["complete"] is False
        assert stage["document_state"] == kernel.DOCUMENT_MISSING

    def test_an_emptied_document_invalidates_the_stage(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        host.files[kernel.sop_stage_path(run_id, PAPER, "md")] = ""
        stage = _paper_stage(kernel, run_id)
        assert stage["complete"] is False
        assert stage["document_state"] == kernel.DOCUMENT_EMPTY

    def test_a_one_byte_rewrite_invalidates_the_stage(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        host.files[path] = _same_length_rewrite(host.files[path])
        stage = _paper_stage(kernel, run_id)
        assert stage["complete"] is False
        assert stage["document_state"] == kernel.DOCUMENT_HASH_MISMATCH

    def test_a_nonempty_truncation_invalidates_the_stage(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        host.files[path] = host.files[path][:8]
        assert host.files[path].strip()
        assert _paper_stage(kernel, run_id)["document_state"] == (
            kernel.DOCUMENT_HASH_MISMATCH
        )

    def test_valid_looking_replacement_is_refused(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        host.files[path] = "# Paper\n\nPlausible but unrelated evidence.\n"
        assert _paper_stage(kernel, run_id)["complete"] is False

    def test_removing_the_digest_does_not_switch_the_check_off(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER)
        record = json.loads(host.files[path])
        del record["document_sha256"]
        host.files[path] = json.dumps(record)
        stage = _paper_stage(kernel, run_id)
        assert stage["complete"] is False
        assert stage["document_state"] == kernel.DOCUMENT_UNHASHED

    def test_problem_names_the_rewritten_document(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        host.files[path] = _same_length_rewrite(host.files[path])
        stage = _paper_stage(kernel, run_id)
        assert "hashes to" in stage["document_problem"]
        assert path in stage["document_problem"]

    def test_tampered_document_is_rerun(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        host.files[path] = _same_length_rewrite(host.files[path])
        host.delegate_calls.clear()
        again = kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)
        assert [call["role"] for call in host.delegate_calls] == [PAPER]
        assert again["status"] == "complete"
        assert _paper_stage(kernel, run_id)["document_state"] == kernel.DOCUMENT_OK

    def test_orchestrator_does_not_report_unvouched_paper(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        host.files[path] = _same_length_rewrite(host.files[path])

        class Refuses(FakeHost):
            def delegate(self, request, **kwargs):
                result = super().delegate(request, **kwargs)
                if kwargs.get("name") == PAPER:
                    return {**result, "task_status": "failed"}
                return result

        replacement = Refuses(outputs=_passing_outputs())
        replacement.files = host.files
        blocked = _load_kernel(replacement).orchestrate_research(
            TASK_A, resume=True, run_id=run_id
        )
        assert blocked["status"] != "complete"
        assert blocked["paper"] is None

    def test_role_without_document_contract_is_unaffected(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, "modeler")
        record = json.loads(host.files[path])
        del record["document_sha256"]
        host.files[path] = json.dumps(record)
        del host.files[kernel.sop_stage_path(run_id, "modeler", "md")]
        assert kernel.sop_document_state(run_id, "modeler", record)[0] == (
            kernel.DOCUMENT_OK
        )

    def test_any_recorded_digest_is_enforced(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        digest = kernel.sop_task_sha256(TASK_A)
        path = kernel.sop_stage_path(run_id, "modeler", "md")
        host.files[path] = _same_length_rewrite(host.files[path])
        assert kernel.sop_read_stage(run_id, "modeler", digest) is None

    def test_stale_bytes_cannot_certify_attempt_without_digest(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_stage_path(run_id, PAPER, "md")
        original = host.files[path]
        host.outputs[PAPER] = schema_valid_output(PAPER)
        del host.outputs[PAPER]["document"]
        json_path = kernel.sop_stage_path(run_id, PAPER)
        record = json.loads(host.files[json_path])
        record["state"] = "incomplete"
        host.files[json_path] = json.dumps(record)
        result = kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)
        assert host.files[path] == original
        assert result["status"] != "complete"
        assert result["paper"] is None
