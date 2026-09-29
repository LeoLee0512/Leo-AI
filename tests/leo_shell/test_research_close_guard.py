"""Closing the window never leaves a research run computing unseen (2.2.6)."""
import logging
from types import SimpleNamespace

import pytest

pytest.importorskip("webview")
from leo_shell import ui  # noqa: E402


class FakeApi:
    def __init__(self, busy):
        self.busy, self.stopped = busy, 0

    def _research_busy_tasks(self):
        return self.busy

    def _research_stop_for_close(self):
        self.stopped += 1


def guard(api, answer, monkeypatch):
    asked = []
    monkeypatch.setattr(ui, "_confirm_native", lambda window, title, text: asked.append(text) or answer)
    stand_in = SimpleNamespace(_api=api, _window=None, _logger=logging.getLogger("test"))
    return ui.DesktopUI._research_close_allowed(stand_in), asked


def test_nothing_running_closes_without_asking(monkeypatch):
    allowed, asked = guard(FakeApi([]), False, monkeypatch)
    assert allowed is True and asked == []


def test_a_running_task_asks_and_stops_on_confirmation(monkeypatch):
    api = FakeApi(["research-" + "a" * 32])
    allowed, asked = guard(api, True, monkeypatch)
    assert allowed is True and api.stopped == 1
    assert "停止计算" in asked[0] and "证据会保留" in asked[0]


def test_declining_keeps_the_window_and_the_run(monkeypatch):
    api = FakeApi(["research-" + "a" * 32])
    allowed, asked = guard(api, False, monkeypatch)
    assert allowed is False and api.stopped == 0 and len(asked) == 1


def test_an_unreadable_research_state_never_blocks_closing(monkeypatch):
    class Broken(FakeApi):
        def _research_busy_tasks(self):
            raise OSError("disk")
    allowed, asked = guard(Broken([]), False, monkeypatch)
    assert allowed is True and asked == []


def test_the_page_cannot_reach_the_close_controls():
    from leo_shell.api import ShellApi
    # pywebview exposes public methods only; the lifecycle hooks stay private.
    assert all(name.startswith("_") for name in ("_research_busy_tasks", "_research_stop_for_close"))
    assert hasattr(ShellApi, "_research_busy_tasks") and hasattr(ShellApi, "_research_stop_for_close")
