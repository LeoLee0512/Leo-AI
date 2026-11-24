"""3.2.3 · Skill collections switched as one, and the biology collection off by default.

The daemon keeps one enabled flag per skill. A bundled collection (bioSkills: 561 third-party
bioinformatics recipes from Open4S) is switched here by setting each member through the daemon's
own per-skill route, the same one the 插件 page uses for a single skill.

Owner, 2026-09-30: biology skills are off by default. The first time Leo reaches the daemon after
this version is installed, the collections in DEFAULT_OFF are switched off once and a marker is
written in the user folder; after that only the person's own choices on the 插件 page count.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import threading
from pathlib import Path

COLLECTION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
DEFAULT_OFF = ("bioskills",)
MARKER = "skill-defaults.json"


class SkillGroups:
    OPERATIONS = ("skill_collection_toggle",)

    def __init__(self, user_dir, gateway, *, logger, start=True, retry_seconds=20, attempts=45):
        self._marker = Path(user_dir) / MARKER
        self._gateway = gateway
        self._logger = logger
        self._retry = retry_seconds
        self._attempts = attempts
        self._stop = threading.Event()
        self._lock = threading.Lock()
        if start and not self.defaults_applied():
            threading.Thread(target=self._apply_defaults_until_done, name="leo-skill-defaults", daemon=True).start()

    # -- page operation -----------------------------------------------------------------------------

    def handle(self, payload):
        collection = payload.get("collection")
        enabled = payload.get("enabled")
        if not isinstance(collection, str) or not COLLECTION.fullmatch(collection) or type(enabled) is not bool:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        return self.set_collection(collection, enabled)

    def set_collection(self, collection, enabled):
        """Switch every member of one collection; only members in the other state are sent."""
        with self._lock:
            skills = self._gateway.request({"operation": "skills"})["data"]["skills"]
            members = [s for s in skills if s.get("collection") == collection]
            if not members:
                raise ValueError("SKILL_COLLECTION_NOT_FOUND")
            changed = 0
            for skill in members:
                if skill.get("enabled") is not enabled:
                    self._gateway.request({"operation": "skill_toggle", "name": skill["name"], "enabled": enabled})
                    changed += 1
            return {"collection": collection, "members": len(members), "changed": changed, "enabled": enabled}

    # -- default off, once --------------------------------------------------------------------------

    def defaults_applied(self):
        try:
            data = json.loads(self._marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return isinstance(data, dict) and all(name in (data.get("defaultOff") or {}) for name in DEFAULT_OFF)

    def apply_defaults(self):
        done = {}
        for collection in DEFAULT_OFF:
            try:
                result = self.set_collection(collection, False)
            except ValueError as exc:
                if str(exc) != "SKILL_COLLECTION_NOT_FOUND":
                    raise
                result = {"members": 0, "changed": 0}  # nothing to switch in this installation
            done[collection] = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                                "members": result["members"], "switchedOff": result["changed"]}
        tmp = self._marker.with_name(self._marker.name + ".tmp")
        tmp.write_text(json.dumps({"schemaVersion": 1, "defaultOff": done}, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        os.replace(tmp, self._marker)
        self._logger.info("skill defaults applied: %s", {k: v["switchedOff"] for k, v in done.items()})
        return done

    def _apply_defaults_until_done(self):
        # The daemon may still be starting; try again for a while, and on the next launch if needed.
        for _ in range(self._attempts):
            if self._stop.is_set():
                return
            try:
                self.apply_defaults()
                return
            except Exception as exc:  # noqa: BLE001 - logged and retried; never breaks the window
                self._logger.info("skill defaults not applied yet (%s); retrying", type(exc).__name__)
            if self._stop.wait(self._retry):
                return

    def close(self):
        self._stop.set()
