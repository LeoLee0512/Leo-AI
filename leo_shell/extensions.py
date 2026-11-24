"""Desktop services that live beside the chat: approval modes, scheduled messages, (3.1.0)
opening web links in the system browser, (3.2.1) the person's own terminal and (3.2.3) skill
collections switched as one.

Installed by the window at start-up and shut down when it closes. Everything the page asks of
them goes through ``workbench_request`` operations registered here; nothing touches the research
code identity (``api.py`` and the research modules are unchanged).
"""
from __future__ import annotations

import logging

from . import workbench
from .approvals import ApprovalCenter
from .model_usage import ModelUsage
from .schedules import Scheduler
from .skill_groups import SkillGroups
from .user_terminal import UserTerminals
from .web_links import LinkOpener

APPROVAL_OPERATIONS = ("approval_mode", "approval_set_mode", "approvals", "approval_decide")
SCHEDULE_OPERATIONS = ("schedules", "schedule_save", "schedule_toggle", "schedule_delete",
                       "schedule_send_now", "schedule_dismiss")
LINK_OPERATIONS = ("open_link",)
PLUGIN_OPERATIONS = ("connector_add",)
TERMINAL_OPERATIONS = UserTerminals.OPERATIONS
SKILL_GROUP_OPERATIONS = SkillGroups.OPERATIONS
USAGE_OPERATIONS = ModelUsage.OPERATIONS


class Extensions:
    def __init__(self, api, paths, client_url, *, logger=None, start=True, distro=None) -> None:
        self._api = api
        self._logger = logger or logging.getLogger(__name__)
        gateway = workbench.WorkbenchGateway(client_url)
        self._gateway = gateway
        self.approvals = ApprovalCenter(paths.user, gateway, client_url, logger=self._logger, start_watcher=start)
        self.scheduler = Scheduler(paths.user, self.send, logger=self._logger, start=start)
        workbench.register_local(APPROVAL_OPERATIONS, self._approval)
        workbench.register_local(SCHEDULE_OPERATIONS, self._schedule)
        # The confirmation belongs to the Leo window, so a page script can never answer it.
        self.links = LinkOpener(lambda: getattr(getattr(api, "_ui", None), "_window", None))
        workbench.register_local(LINK_OPERATIONS, self.links.open)
        workbench.register_local(PLUGIN_OPERATIONS, gateway.add_connector)
        # 3.2.1 · 「终端」 is the person's own shell (same WSL distro as the daemon), never the AI's.
        self.terminals = UserTerminals(distro)
        workbench.register_local(TERMINAL_OPERATIONS, self.terminals.handle)
        # 3.2.3 · A skill collection has one switch; biology is off by default (once, then the person decides).
        self.skill_groups = SkillGroups(paths.user, gateway, logger=self._logger, start=start)
        workbench.register_local(SKILL_GROUP_OPERATIONS, self.skill_groups.handle)
        # 3.2.11 · 「用量」: temperature per model and the local model's latest request.
        bridge_script = getattr(paths, "bridge_script", None)
        self.usage = ModelUsage(bridge_script.parent if bridge_script else None, distro)
        workbench.register_local(USAGE_OPERATIONS, self.usage.handle)

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
        workbench.unregister_local(APPROVAL_OPERATIONS + SCHEDULE_OPERATIONS + LINK_OPERATIONS + PLUGIN_OPERATIONS
                                   + TERMINAL_OPERATIONS + SKILL_GROUP_OPERATIONS + USAGE_OPERATIONS)
        self.skill_groups.close()
        self.terminals.close()
        self.scheduler.close()
        self.approvals.close()
