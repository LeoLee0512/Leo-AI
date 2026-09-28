"""F-002: rollback history is verified whenever it is audited."""

from __future__ import annotations

import json

from test_research_sop import TASK_A, host, kernel  # noqa: F401


def _complete(kernel):
    result = kernel.orchestrate_research(TASK_A)
    assert result["status"] == "complete", result.get("findings")
    return result


def _same_length_rewrite(text):
    victim = text[-1]
    return text[:-1] + ("X" if victim != "X" else "Y")


class TestRollbackHistoryIsReHashedOnAudit:
    @staticmethod
    def _with_history(kernel, host):
        run_id = _complete(kernel)["run_id"]
        event = kernel.sop_clear_from(run_id, "modeler", findings=["audit probe"])
        assert event["archived"]
        return run_id, event

    def test_intact_history_audits_clean(self, kernel, host):
        run_id, event = self._with_history(kernel, host)
        history = kernel.sop_inspect_history(run_id)
        assert history["state"] == kernel.HISTORY_OK
        assert history["problems"] == []
        assert len(history["archives"]) == len(event["archived"])
        assert all(a["state"] == kernel.ARCHIVE_OK for a in history["archives"])

    def test_run_without_rollbacks_reports_empty_not_ok(self, kernel, host):
        run_id = _complete(kernel)["run_id"]
        assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_EMPTY

    def test_length_preserving_rewrite_is_caught(self, kernel, host):
        run_id, event = self._with_history(kernel, host)
        target = event["archived"][0]["archived_to"]
        host.files[target] = _same_length_rewrite(host.files[target])
        history = kernel.sop_inspect_history(run_id)
        assert history["state"] == kernel.HISTORY_CORRUPT
        assert any(
            item["state"] == kernel.ARCHIVE_HASH_MISMATCH
            and item["archived_to"] == target
            for item in history["archives"]
        )

    def test_appending_to_archive_is_caught(self, kernel, host):
        run_id, event = self._with_history(kernel, host)
        target = event["archived"][0]["archived_to"]
        host.files[target] += "\nFORGED"
        assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_CORRUPT

    def test_deleted_archive_is_reported_missing(self, kernel, host):
        run_id, event = self._with_history(kernel, host)
        target = event["archived"][0]["archived_to"]
        del host.files[target]
        history = kernel.sop_inspect_history(run_id)
        assert history["state"] == kernel.HISTORY_CORRUPT
        assert any(a["state"] == kernel.ARCHIVE_MISSING for a in history["archives"])

    def test_archive_entry_without_digest_is_not_accepted(self, kernel, host):
        run_id, _ = self._with_history(kernel, host)
        path = kernel.sop_manifest_path(run_id)
        manifest = json.loads(host.files[path])
        del manifest["rollbacks"][0]["archived"][0]["sha256"]
        host.files[path] = json.dumps(manifest)
        history = kernel.sop_inspect_history(run_id)
        assert history["state"] == kernel.HISTORY_CORRUPT
        assert any(a["state"] == kernel.ARCHIVE_UNHASHED for a in history["archives"])

    def test_status_surfaces_history_corruption(self, kernel, host):
        run_id, event = self._with_history(kernel, host)
        target = event["archived"][0]["archived_to"]
        assert kernel.sop_status(run_id)["history_state"] == kernel.HISTORY_OK
        host.files[target] = _same_length_rewrite(host.files[target])
        status = kernel.sop_status(run_id)
        assert status["history_state"] == kernel.HISTORY_CORRUPT
        assert target in " ".join(status["history_problems"])

    def test_restoring_original_bytes_clears_finding(self, kernel, host):
        run_id, event = self._with_history(kernel, host)
        target = event["archived"][0]["archived_to"]
        intact = host.files[target]
        host.files[target] = _same_length_rewrite(intact)
        assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_CORRUPT
        host.files[target] = intact
        assert kernel.sop_inspect_history(run_id)["state"] == kernel.HISTORY_OK
