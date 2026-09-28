"""Local, reversible session visibility. Upstream content is never removed here.

Only IDs, optional display names and folder/project membership are stored. Corrupt or
unknown files fail closed; they are never replaced with an empty document.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path


def _identity(value):
    if not isinstance(value, str) or not value or len(value) > 240 or any(ord(c) < 32 or c in "/\\" for c in value):
        raise ValueError("ENTITY_INVALID")
    return value


class EntityStore:
    def __init__(self, user: Path):
        self.user = Path(user)
        self.path = self.user / "entity-states.json"
        self.lock = threading.RLock()

    def _safe(self):
        for path in (self.user, self.path):
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ValueError("ENTITY_STORE_UNAVAILABLE")

    def _read(self):
        self._safe()
        if not self.path.exists():
            return {"version": 1, "revision": 0, "entities": []}
        if self.path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("ENTITY_STORE_UNAVAILABLE")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1 or type(data.get("revision")) is not int or data["revision"] < 0 or not isinstance(data.get("entities"), list):
            raise ValueError("ENTITY_STORE_UNAVAILABLE")
        seen = set()
        for record in data["entities"]:
            self._record(record)
            key = (record["entity_type"], record["entity_id"])
            if key in seen or record["revision"] > data["revision"]:
                raise ValueError("ENTITY_STORE_UNAVAILABLE")
            seen.add(key)
        return data

    @staticmethod
    def _record(record):
        if not isinstance(record, dict) or record.get("entity_type") not in ("session", "folder", "project") or record.get("state") not in ("archived", "trashed"):
            raise ValueError("ENTITY_INVALID")
        _identity(record.get("entity_id"))
        if type(record.get("revision")) is not int or record["revision"] < 1:
            raise ValueError("ENTITY_INVALID")
        if not isinstance(record.get("title", ""), str) or len(record.get("title", "")) > 160:
            raise ValueError("ENTITY_INVALID")
        stamp = record.get("updated_at")
        if not isinstance(stamp, str):
            raise ValueError("ENTITY_INVALID")
        datetime.fromisoformat(stamp)
        if record["entity_type"] in ("folder", "project"):
            snapshot = record.get("snapshot")
            if not isinstance(snapshot, dict) or snapshot.get("snapshot_version") != 1 or not isinstance(snapshot.get("member_session_ids"), list):
                raise ValueError("ENTITY_INVALID")
            if len(snapshot["member_session_ids"]) > 20000:
                raise ValueError("ENTITY_INVALID")
            for value in snapshot["member_session_ids"]:
                _identity(value)

    def _write(self, data):
        self._safe()
        self.user.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        if len(encoded) > 4 * 1024 * 1024:
            raise ValueError("ENTITY_STORE_UNAVAILABLE")
        fd, temporary = tempfile.mkstemp(prefix=".entity-", suffix=".tmp", dir=self.user)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(encoded)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def list(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("ENTITY_INVALID")
        offset, limit = payload.get("offset", 0), payload.get("limit", 1000)
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("ENTITY_INVALID")
        with self.lock:
            data = self._read()
            end = offset + limit
            return {"ok": True, "entities": data["entities"][offset:end], "next_offset": end if end < len(data["entities"]) else None}

    def mark(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("ENTITY_INVALID")
        with self.lock:
            data = self._read()
            record = {key: payload[key] for key in ("entity_type", "entity_id", "state", "title", "snapshot") if key in payload}
            record.update(revision=data["revision"] + 1, updated_at=datetime.now(timezone.utc).isoformat())
            self._record(record)
            records = data["entities"]
            records[:] = [r for r in records if (r["entity_type"], r["entity_id"]) != (record["entity_type"], record["entity_id"])]
            records.append(record)
            data["revision"] += 1
            self._write(data)
            return {"ok": True, "entity": record}

    def remove(self, payload):
        if not isinstance(payload, dict) or payload.get("entity_type") not in ("session", "folder", "project"):
            raise ValueError("ENTITY_INVALID")
        identity = _identity(payload.get("entity_id"))
        if type(payload.get("expected_revision")) is not int:
            raise ValueError("ENTITY_INVALID")
        with self.lock:
            data = self._read()
            record = next((r for r in data["entities"] if r["entity_type"] == payload["entity_type"] and r["entity_id"] == identity), None)
            if record is None or record["revision"] != payload["expected_revision"]:
                raise ValueError("ENTITY_REVISION_CONFLICT")
            data["entities"].remove(record)
            data["revision"] += 1
            self._write(data)
            return {"ok": True}
