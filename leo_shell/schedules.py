"""Scheduled messages: at a chosen minute, Leo sends a prepared message into a conversation.

Owner's rules (2026-09-29): minute precision; once, daily, weekdays or weekly; pause, edit or
delete at any time; only while Leo is open. A time missed while the app was closed is recorded
as missed on the next start and never sent automatically; the person may send it by hand.
A scheduled message is an ordinary chat message: it can never start a formal research run,
whose confirmations stay native dialogs.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import os
import re
import tempfile
import threading
import uuid
from pathlib import Path

REPEATS = ("once", "daily", "weekdays", "weekly")
GRACE = timedelta(minutes=2)        # a tick this late still counts as on time
TICK_SECONDS = 15
MAX_ITEMS = 100
MAX_HISTORY = 60
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _stamp(moment: datetime | None) -> str | None:
    return moment.strftime("%Y-%m-%dT%H:%M") if moment else None


def _parse(stamp: str | None) -> datetime | None:
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M") if stamp else None


def occurrence_after(item: dict, after: datetime) -> datetime | None:
    """The first occurrence strictly after ``after`` (local wall time), or None when there is none."""
    day = datetime.strptime(item["date"], "%Y-%m-%d")
    hour, minute = (int(x) for x in item["time"].split(":"))
    first = day.replace(hour=hour, minute=minute)
    if item["repeat"] == "once":
        return first if first > after else None
    candidate = max(first, (after + timedelta(minutes=1)).replace(hour=hour, minute=minute, second=0, microsecond=0))
    for _ in range(8):
        if candidate > after and candidate >= first and (
                item["repeat"] == "daily"
                or (item["repeat"] == "weekdays" and candidate.weekday() < 5)
                or (item["repeat"] == "weekly" and candidate.weekday() == first.weekday())):
            return candidate
        candidate += timedelta(days=1)
    return None


def validate(payload: dict) -> dict:
    frame, text = payload.get("frameId"), payload.get("text")
    if not isinstance(frame, str) or not _ID.fullmatch(frame):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    if not isinstance(text, str) or not text.strip() or len(text) > 8000:
        raise ValueError("WORKBENCH_SCHEDULE_TEXT_INVALID")
    date, clock, repeat = payload.get("date"), payload.get("time"), payload.get("repeat")
    if not isinstance(date, str) or not _DATE.fullmatch(date) or not isinstance(clock, str) or not _TIME.fullmatch(clock):
        raise ValueError("WORKBENCH_SCHEDULE_TIME_INVALID")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("WORKBENCH_SCHEDULE_TIME_INVALID") from None
    if repeat not in REPEATS:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    name = payload.get("frameName")
    name = name.strip()[:120] if isinstance(name, str) and name.strip() else "对话"
    return {"frameId": frame, "frameName": name, "text": text.strip(), "date": date, "time": clock, "repeat": repeat}


class ScheduleStore:
    """``user/schedules.json``: the schedules and a short record of what happened."""

    def __init__(self, user_dir: Path) -> None:
        self._path = Path(user_dir) / "schedules.json"
        self.lock = threading.RLock()

    def read(self) -> dict:
        with self.lock:
            try:
                if self._path.is_symlink():
                    raise OSError
                document = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(document, dict) and isinstance(document.get("items"), list) and isinstance(document.get("history"), list):
                    return document
            except (OSError, ValueError):
                pass
            return {"version": 1, "items": [], "history": []}

    def write(self, document: dict) -> None:
        with self.lock:
            document["history"] = document["history"][-MAX_HISTORY:]
            self._path.parent.mkdir(parents=True, exist_ok=True)
            handle, temp = tempfile.mkstemp(dir=self._path.parent, prefix=".schedules-", suffix=".tmp")
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    json.dump(document, stream, ensure_ascii=False, sort_keys=True)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, self._path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)


class Scheduler:
    def __init__(self, user_dir: Path, send, *, logger=None, now=datetime.now, start=True) -> None:
        self._store = ScheduleStore(user_dir)
        self._send = send                  # send(frame_id, text) -> None, raises ValueError(code)
        self._logger = logger or logging.getLogger(__name__)
        self._now = now
        self._stop = threading.Event()
        self._thread = None
        if start:
            self._thread = threading.Thread(target=self._run, name="leo-scheduler", daemon=True)
            self._thread.start()

    # -- page operations -----------------------------------------------------------------------

    def list(self) -> dict:
        document = self._store.read()
        items = sorted(document["items"], key=lambda i: (not i["enabled"], i.get("nextRun") or "9999"))
        return {"items": items, "history": list(reversed(document["history"]))[:20],
                "now": _stamp(self._now())}

    def save(self, payload: dict) -> dict:
        fields = validate(payload)
        now = self._now().replace(second=0, microsecond=0)
        with self._store.lock:
            document = self._store.read()
            ident = payload.get("id")
            existing = next((i for i in document["items"] if i["id"] == ident), None) if ident else None
            if ident and existing is None:
                raise ValueError("WORKBENCH_NOT_FOUND")
            if existing is None and len(document["items"]) >= MAX_ITEMS:
                raise ValueError("WORKBENCH_SCHEDULE_LIMIT")
            item = existing or {"id": "sch_" + uuid.uuid4().hex[:16], "createdAt": _stamp(now), "enabled": True}
            item.update(fields)
            upcoming = occurrence_after(item, now)
            if upcoming is None:
                raise ValueError("WORKBENCH_SCHEDULE_TIME_PASSED")
            item.update({"nextRun": _stamp(upcoming) if item["enabled"] else None, "updatedAt": _stamp(now)})
            if existing is None:
                document["items"].append(item)
            self._store.write(document)
            return {"item": item}

    def toggle(self, ident: str, enabled: bool) -> dict:
        if type(enabled) is not bool:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        now = self._now().replace(second=0, microsecond=0)
        with self._store.lock:
            document = self._store.read()
            item = self._find(document, ident)
            upcoming = occurrence_after(item, now) if enabled else None
            if enabled and upcoming is None:
                raise ValueError("WORKBENCH_SCHEDULE_TIME_PASSED")
            item.update({"enabled": enabled, "nextRun": _stamp(upcoming), "updatedAt": _stamp(now)})
            self._store.write(document)
            return {"item": item}

    def delete(self, ident: str) -> dict:
        with self._store.lock:
            document = self._store.read()
            item = self._find(document, ident)
            document["items"].remove(item)
            self._store.write(document)
            return {"deleted": ident}

    def send_now(self, record: str) -> dict:
        """Send a missed or failed occurrence by hand; the person decides, never the scheduler."""
        with self._store.lock:
            document = self._store.read()
            entry = next((h for h in document["history"] if h["id"] == record), None)
            if entry is None or entry["status"] not in ("missed", "failed"):
                raise ValueError("WORKBENCH_NOT_FOUND")
            frame, text = entry["frameId"], entry["text"]
        status, detail = self._deliver(frame, text)
        with self._store.lock:
            document = self._store.read()
            for h in document["history"]:
                if h["id"] == record:
                    h.update({"status": "sent_late" if status == "sent" else "failed", "detail": detail,
                              "at": _stamp(self._now())})
            self._store.write(document)
        return {"status": status, "detail": detail}

    def dismiss(self, record: str) -> dict:
        with self._store.lock:
            document = self._store.read()
            entry = next((h for h in document["history"] if h["id"] == record), None)
            if entry is None:
                raise ValueError("WORKBENCH_NOT_FOUND")
            entry["status"] = "dismissed"
            self._store.write(document)
            return {"dismissed": record}

    @staticmethod
    def _find(document, ident):
        item = next((i for i in document["items"] if i["id"] == ident), None)
        if item is None:
            raise ValueError("WORKBENCH_NOT_FOUND")
        return item

    # -- the clock ---------------------------------------------------------------------------------

    def _deliver(self, frame, text):
        try:
            self._send(frame, text)
            return "sent", ""
        except ValueError as error:
            code = str(error)
            return "failed", code if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", code) else "SEND_FAILED"
        except Exception:
            self._logger.exception("scheduled message could not be sent")
            return "failed", "SEND_FAILED"

    def tick(self) -> list[dict]:
        """Settle every due schedule once. Returns the history entries it wrote."""
        now = self._now().replace(second=0, microsecond=0)
        due = []
        with self._store.lock:
            document = self._store.read()
            for item in document["items"]:
                when = _parse(item.get("nextRun"))
                if not item.get("enabled") or when is None or when > now:
                    continue
                # Several occurrences may have passed while Leo was closed: record the latest once.
                latest, probe = when, occurrence_after(item, when)
                while probe is not None and probe <= now:
                    latest, probe = probe, occurrence_after(item, probe)
                entry = {"id": "run_" + uuid.uuid4().hex[:16], "scheduleId": item["id"], "frameId": item["frameId"],
                         "frameName": item["frameName"], "text": item["text"], "due": _stamp(latest),
                         "status": "sending" if now - latest <= GRACE else "missed", "at": _stamp(now), "detail": ""}
                document["history"].append(entry)
                due.append(entry)
                item["nextRun"] = _stamp(probe)
                if probe is None:
                    item["enabled"] = False
            if due:
                self._store.write(document)
        for entry in due:
            if entry["status"] == "sending":
                entry["status"], entry["detail"] = self._deliver(entry["frameId"], entry["text"])
        if any(e["status"] != "missed" for e in due):
            with self._store.lock:
                document = self._store.read()
                results = {e["id"]: e for e in due}
                for h in document["history"]:
                    if h["id"] in results:
                        h.update({k: results[h["id"]][k] for k in ("status", "detail")})
                self._store.write(document)
        return due

    def _run(self):
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:
                self._logger.exception("scheduler tick failed")
            self._stop.wait(TICK_SECONDS)

    def close(self):
        self._stop.set()
