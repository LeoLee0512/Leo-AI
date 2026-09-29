"""Desktop services that live beside the chat: approval modes and scheduled messages.

Installed by the window at start-up and shut down when it closes. Everything the page asks of
them goes through ``workbench_request`` operations registered here; nothing touches the research
code identity (``api.py`` and the research modules are unchanged).
"""
from __future__ import annotations

import logging

from . import workbench
from .approvals import ApprovalCenter
from .schedules import Scheduler

APPROVAL_OPERATIONS = ("approval_mode", "approval_set_mode", "approvals", "approval_decide")
SCHEDULE_OPERATIONS = ("schedules", "schedule_save", "schedule_toggle", "schedule_delete",
                       "schedule_send_now", "schedule_dismiss")


class Extensions:
    def __init__(self, api, paths, client_url, *, logger=None, start=True) -> None:
        self._api = api
        self._logger = logger or logging.getLogger(__name__)
        gateway = workbench.WorkbenchGateway(client_url)
        self.approvals = ApprovalCenter(paths.user, gateway, client_url, logger=self._logger, start_watcher=start)
        self.scheduler = Scheduler(paths.user, self.send, logger=self._logger, start=start)
        workbench.register_local(APPROVAL_OPERATIONS, self._approval)
        workbench.register_local(SCHEDULE_OPERATIONS, self._schedule)

    # -- page operations ---------------------------------------------------------------------------

    def _approval(self, payload):
        op, frame = payload["operation"], payload.get("frameId")
        if op == "approval_mode":
            return self.approvals.mode(frame)
        if op == "approval_set_mode":
            return self.approvals.set_mode(frame, payload.get("mode"))
        if op == "approvals":
            return self.approvals.pending(frame)
        return self.approvals.decide(frame, payload.get("decisionId"), payload.get("allow"), payload.get("scope"))

    def _schedule(self, payload):
        op = payload["operation"]
        if op == "schedules":
            return self.scheduler.list()
        if op == "schedule_save":
            return self.scheduler.save(payload)
        if op == "schedule_toggle":
            return self.scheduler.toggle(payload.get("id"), payload.get("enabled"))
        if op == "schedule_delete":
            return self.scheduler.delete(payload.get("id"))
        if op == "schedule_send_now":
            return self.scheduler.send_now(payload.get("recordId"))
        return self.scheduler.dismiss(payload.get("recordId"))

    # -- sending a scheduled message ----------------------------------------------------------------

    def send(self, frame_id, text):
        """Send as the page would: the conversation's own model binding, default reasoning."""
        listed = self._api.list_session_models({"frame_id": frame_id})
        if not listed.get("ok"):
            raise ValueError(listed.get("code") or listed.get("message") or "MODEL_SELECTION_UNAVAILABLE")
        binding = listed.get("binding") or {}
        if not binding.get("profile_id") or not binding.get("native_profile_id"):
            raise ValueError("MODEL_SELECTION_REQUIRED")
        if binding.get("credential_ready") is not True:
            selected = self._api.select_session_model({"frame_id": frame_id, "native_profile_id": binding["native_profile_id"],
                "expected_binding": {"profile_id": binding["profile_id"], "revision": binding["revision"]}})
            if not selected.get("ok"):
                raise ValueError(selected.get("code") or selected.get("message") or "MODEL_SELECTION_UNAVAILABLE")
            binding = (self._api.list_session_models({"frame_id": frame_id}).get("binding") or binding)
        reasoning = binding.get("reasoning") or {}
        if not isinstance(reasoning.get("revision"), str):
            raise ValueError("REASONING_CAPABILITY_CHANGED")
        # The conversation's approval mode is in force before anything runs, and its requests are watched.
        self.approvals.mode(frame_id)
        self.approvals.watch(frame_id)
        result = self._api.workbench_request({"operation": "send", "frameId": frame_id, "text": text,
            "modelBinding": {"profile_id": binding["profile_id"], "revision": binding["revision"]},
            "reasoningSelection": {"choice": "default", "capability_revision": reasoning["revision"]}})
        if not result.get("ok"):
            raise ValueError(result.get("message") or "WORKBENCH_REQUEST_FAILED")

    def close(self):
        workbench.unregister_local(APPROVAL_OPERATIONS + SCHEDULE_OPERATIONS)
        self.scheduler.close()
        self.approvals.close()
