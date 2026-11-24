"""F-007: the manifest audit and execution surfaces must agree."""

from __future__ import annotations

import json

import pytest

from test_research_sop import (  # noqa: F401
    TASK_A,
    TASK_B,
    host,
    kernel,
)


def _complete(kernel, task=TASK_A):
    result = kernel.orchestrate_research(task)
    assert result["status"] == "complete", result.get("findings")
    return result


class TestManifestAuditAndExecutionAgree:
    def test_an_untouched_manifest_still_reads_valid(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        report = kernel.sop_inspect_manifest(run_id)
        assert report["state"] == kernel.MANIFEST_VALID
        assert report["reason"] is None

    def test_a_forged_task_sha256_is_corrupt_on_the_audit_surface(
        self, kernel, host
    ):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["task_sha256"] = "0" * 64
        host.files[path] = json.dumps(manifest)
        report = kernel.sop_inspect_manifest(run_id)
        assert report["state"] == kernel.MANIFEST_CORRUPT
        assert "task_sha256" in report["reason"]

    def test_the_two_surfaces_give_the_same_answer(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["task_sha256"] = "0" * 64
        host.files[path] = json.dumps(manifest)

        assert kernel.sop_inspect_manifest(run_id)["state"] != kernel.MANIFEST_VALID
        with pytest.raises(ValueError):
            kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)

    def test_a_manifest_belonging_to_another_run_is_corrupt(self, kernel, host):
        first = _complete(kernel, TASK_A)["run_id"]
        second = _complete(kernel, TASK_B)["run_id"]
        assert first != second
        host.files[kernel.sop_manifest_path(second)] = host.files[
            kernel.sop_manifest_path(first)
        ]
        report = kernel.sop_inspect_manifest(second)
        assert report["state"] == kernel.MANIFEST_CORRUPT
        assert "run_id" in report["reason"]

    def test_a_manifest_without_its_task_text_is_corrupt(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        del manifest["task_text"]
        host.files[path] = json.dumps(manifest)
        report = kernel.sop_inspect_manifest(run_id)
        assert report["state"] == kernel.MANIFEST_CORRUPT
        assert "task_text" in report["reason"]

    def test_rewriting_the_task_text_alone_is_corrupt(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["task_text"] = "An entirely different research question?"
        host.files[path] = json.dumps(manifest)
        assert kernel.sop_inspect_manifest(run_id)["state"] == kernel.MANIFEST_CORRUPT

    def test_a_rollback_list_that_is_not_a_list_is_corrupt(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["rollbacks"] = {"event_id": "rollback-001"}
        host.files[path] = json.dumps(manifest)
        assert kernel.sop_inspect_manifest(run_id)["state"] == kernel.MANIFEST_CORRUPT

    def test_whitespace_rewrapping_the_task_text_is_still_the_same_task(
        self, kernel, host
    ):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["task_text"] = TASK_A.replace(" ", "\n   ")
        host.files[path] = json.dumps(manifest)
        assert kernel.sop_inspect_manifest(run_id)["state"] == kernel.MANIFEST_VALID

    def test_a_corrupt_manifest_is_never_repaired_in_place(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        manifest["task_sha256"] = "0" * 64
        damaged = json.dumps(manifest)
        host.files[path] = damaged
        with pytest.raises(ValueError):
            kernel.orchestrate_research(TASK_A, resume=True, run_id=run_id)
        assert host.files[path] == damaged
