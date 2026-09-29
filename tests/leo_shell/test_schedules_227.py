"""2.2.7: scheduled messages — minute precision, only while Leo is open, missed times never sent on their own."""
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from leo_shell import workbench
from leo_shell.extensions import APPROVAL_OPERATIONS, SCHEDULE_OPERATIONS, Extensions
from leo_shell.schedules import Scheduler, occurrence_after


class Clock:
    def __init__(self, text):
        self.now = datetime.strptime(text, "%Y-%m-%d %H:%M")

    def __call__(self):
        return self.now

    def set(self, text):
        self.now = datetime.strptime(text, "%Y-%m-%d %H:%M")


def make(tmp_path, when="2026-09-29 08:00", fail=None):
    sent = []

    def send(frame, text):
        if fail:
            raise ValueError(fail)
        sent.append((frame, text))

    clock = Clock(when)
    return Scheduler(tmp_path, send, now=clock, start=False), clock, sent


def item(**extra):
    return {"frameId": "f1", "frameName": "每日文献速览", "text": "检索新论文", "date": "2026-09-29", "time": "08:30",
            "repeat": "once", **extra}


# -- the calendar ---------------------------------------------------------------------------------

@pytest.mark.parametrize("repeat,after,expected", [
    ("once", "2026-09-29 08:00", "2026-09-29 08:30"),
    ("once", "2026-09-29 08:30", None),
    ("daily", "2026-09-29 08:30", "2026-09-30 08:30"),
    ("daily", "2026-09-28 23:00", "2026-09-29 08:30"),          # never before the start date
    ("weekdays", "2026-10-02 09:00", "2026-10-05 08:30"),       # Friday after the time -> Monday
    ("weekly", "2026-09-29 08:30", "2026-10-06 08:30"),         # same weekday as the start date (Tuesday)
])
def test_the_next_occurrence(repeat, after, expected):
    got = occurrence_after(item(repeat=repeat), datetime.strptime(after, "%Y-%m-%d %H:%M"))
    assert got == (datetime.strptime(expected, "%Y-%m-%d %H:%M") if expected else None)


@pytest.mark.parametrize("change,code", [
    ({"time": "8:30"}, "WORKBENCH_SCHEDULE_TIME_INVALID"),
    ({"date": "2026-02-30"}, "WORKBENCH_SCHEDULE_TIME_INVALID"),
    ({"text": "  "}, "WORKBENCH_SCHEDULE_TEXT_INVALID"),
    ({"repeat": "hourly"}, "WORKBENCH_INVALID_REQUEST"),
    ({"frameId": "../x"}, "WORKBENCH_INVALID_REQUEST"),
    ({"time": "07:00"}, "WORKBENCH_SCHEDULE_TIME_PASSED"),
])
def test_invalid_schedules_are_refused(tmp_path, change, code):
    scheduler, _, _ = make(tmp_path)
    with pytest.raises(ValueError, match=code):
        scheduler.save(item(**change))


# -- the clock ------------------------------------------------------------------------------------

def test_an_on_time_schedule_is_sent_once_and_a_one_off_then_ends(tmp_path):
    scheduler, clock, sent = make(tmp_path)
    scheduler.save(item())
    clock.set("2026-09-29 08:29")
    assert scheduler.tick() == [] and sent == []
    clock.set("2026-09-29 08:30")
    scheduler.tick()
    scheduler.tick()
    assert sent == [("f1", "检索新论文")]
    listing = scheduler.list()
    assert listing["items"][0]["enabled"] is False and listing["history"][0]["status"] == "sent"


def test_a_time_missed_while_leo_was_closed_is_recorded_not_sent(tmp_path):
    scheduler, clock, sent = make(tmp_path)
    scheduler.save(item(repeat="daily"))
    clock.set("2026-10-02 12:00")                 # Leo was closed for three days
    entries = scheduler.tick()
    assert sent == [] and [e["status"] for e in entries] == ["missed"]
    assert entries[0]["due"] == "2026-10-02T08:30", "the latest missed occurrence, recorded once"
    assert scheduler.list()["items"][0]["nextRun"] == "2026-10-03T08:30"


def test_a_missed_time_is_sent_only_when_the_person_asks(tmp_path):
    scheduler, clock, sent = make(tmp_path)
    scheduler.save(item())
    clock.set("2026-09-29 11:00")
    record = scheduler.tick()[0]["id"]
    scheduler.send_now(record)
    assert sent == [("f1", "检索新论文")] and scheduler.list()["history"][0]["status"] == "sent_late"
    with pytest.raises(ValueError, match="WORKBENCH_NOT_FOUND"):
        scheduler.send_now(record)


def test_a_failed_send_keeps_its_reason_and_can_be_dismissed(tmp_path):
    scheduler, clock, _ = make(tmp_path, fail="MODEL_SELECTION_REQUIRED")
    scheduler.save(item())
    clock.set("2026-09-29 08:30")
    entry = scheduler.tick()[0]
    assert entry["status"] == "failed" and entry["detail"] == "MODEL_SELECTION_REQUIRED"
    scheduler.dismiss(entry["id"])
    assert scheduler.list()["history"][0]["status"] == "dismissed"


def test_pause_resume_edit_and_delete(tmp_path):
    scheduler, clock, sent = make(tmp_path)
    ident = scheduler.save(item(repeat="daily"))["item"]["id"]
    scheduler.toggle(ident, False)
    clock.set("2026-09-29 08:30")
    assert scheduler.tick() == [] and sent == []
    assert scheduler.toggle(ident, True)["item"]["nextRun"] == "2026-09-30T08:30"
    edited = scheduler.save({**item(repeat="daily", time="09:15"), "id": ident})["item"]
    assert edited["id"] == ident and edited["nextRun"] == "2026-09-29T09:15"
    scheduler.delete(ident)
    assert scheduler.list()["items"] == []


def test_a_corrupt_file_reads_as_empty_rather_than_crashing(tmp_path):
    (tmp_path / "schedules.json").write_text("{not json", encoding="utf-8")
    scheduler, _, _ = make(tmp_path)
    assert scheduler.list()["items"] == []


# -- sending as the page would --------------------------------------------------------------------

class FakeApi:
    def __init__(self, ready=True, bound=True):
        self.calls, self.ready, self.bound = [], ready, bound

    def list_session_models(self, payload):
        self.calls.append(("list", payload))
        binding = {"profile_id": "mp-1", "revision": 2, "native_profile_id": "m1", "credential_ready": self.ready,
                   "reasoning": {"revision": "cap-1"}} if self.bound else {"profile_id": None}
        return {"ok": True, "binding": binding}

    def select_session_model(self, payload):
        self.calls.append(("select", payload))
        self.ready = True
        return {"ok": True}

    def workbench_request(self, payload):
        self.calls.append(("workbench", payload))
        return {"ok": True, "data": {}}


def extensions(tmp_path, api):
    ext = Extensions(api, SimpleNamespace(user=tmp_path), lambda: "http://127.0.0.1:8760/?token=t", start=False)
    ext.approvals.mode = lambda frame: {"mode": "smart"}
    return ext


def test_a_scheduled_message_uses_the_conversations_own_model_and_default_reasoning(tmp_path):
    api = FakeApi(ready=False)
    ext = extensions(tmp_path, api)
    try:
        ext.send("f1", "你好")
        kinds = [c[0] for c in api.calls]
        assert kinds == ["list", "select", "list", "workbench"]
        payload = api.calls[-1][1]
        assert payload["modelBinding"] == {"profile_id": "mp-1", "revision": 2}
        assert payload["reasoningSelection"] == {"choice": "default", "capability_revision": "cap-1"}
    finally:
        ext.close()


def test_a_conversation_without_a_model_is_reported_not_guessed(tmp_path):
    ext = extensions(tmp_path, FakeApi(bound=False))
    try:
        with pytest.raises(ValueError, match="MODEL_SELECTION_REQUIRED"):
            ext.send("f1", "你好")
    finally:
        ext.close()


def test_the_page_reaches_schedules_through_workbench_request_only(tmp_path):
    ext = extensions(tmp_path, FakeApi())
    try:
        gateway = workbench.WorkbenchGateway(lambda: pytest.fail("no daemon call expected"))
        assert gateway.request({"operation": "schedules"})["data"]["items"] == []
    finally:
        ext.close()
    for op in APPROVAL_OPERATIONS + SCHEDULE_OPERATIONS:
        assert op not in workbench._LOCAL_HANDLERS
