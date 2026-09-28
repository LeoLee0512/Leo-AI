"""B08 contract: attempts differ; their artifact bytes need not."""

from __future__ import annotations

import json

from test_research_sop import TASK_A, host, kernel  # noqa: F401

PAPER = "paper-writer"


def test_rerun_has_new_attempt_identity_even_when_artifact_bytes_are_identical(
    kernel, host
):
    first = kernel.orchestrate_research(TASK_A)
    assert first["status"] == "complete"
    run_id = first["run_id"]
    json_path = kernel.sop_stage_path(run_id, PAPER)
    md_path = kernel.sop_stage_path(run_id, PAPER, "md")
    old_record = json.loads(host.files[json_path])
    old_bytes = host.files[md_path]

    # Force a genuine rerun without changing the deterministic delegate output.
    host.files[json_path] = json.dumps({**old_record, "state": "incomplete"})
    host.files[md_path] = ""
    host.delegate_calls.clear()
    again = kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)
    new_record = json.loads(host.files[json_path])

    assert again["status"] == "complete"
    assert [call["role"] for call in host.delegate_calls] == [PAPER]
    assert old_record["attempt_id"]
    assert new_record["attempt_id"] != old_record["attempt_id"]
    assert host.files[md_path] == old_bytes
    assert new_record["document_sha256"] == old_record["document_sha256"]
