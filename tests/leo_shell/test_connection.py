"""Tests for leo_shell.connection using a fake bridge and a fake UI sink.

Worker threads run for real; every synchronization point is a
``threading.Event`` so the tests never depend on sleep timing.
"""

from __future__ import annotations

import logging
import threading
import time
from types import SimpleNamespace

import pytest

from leo_shell.bridge_client import BridgeError
from leo_shell.connection import (
    PUBLIC_APP_CLOSING,
    PUBLIC_CONNECTION_FAILED,
    ConnectionCoordinator,
)

PROFILE = SimpleNamespace(provider="chatgpt", model="deepseek-chat", base_url="https://api.deepseek.com")
URL = "http://127.0.0.1:8760/?token=test-token"


class FakeBridge:
    """Programmable stand-in for WslBridge; every call is recorded."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.calls: list[str] = []
        self.started_keys: list[str | None] = []
        self.status_responses: list[dict] = [{"state": "stopped", "running": False}]
        self._status_index = 0
        self.errors: dict[str, Exception] = {}
        self.url = URL
        self.preflight_gate: tuple[threading.Event, threading.Event] | None = None
        self.preflight_entered = threading.Event()
        self.url_called = threading.Event()
        self.stop_called = threading.Event()
        self.stop_count = 0

    def _record(self, name: str) -> None:
        with self._lock:
            self.calls.append(name)

    def _maybe_raise(self, name: str) -> None:
        error = self.errors.get(name)
        if error is not None:
            raise error

    def preflight(self) -> dict:
        self._record("preflight")
        self.preflight_entered.set()
        if self.preflight_gate is not None:
            entered, release = self.preflight_gate
            entered.set()
            release.wait(timeout=10)
        self._maybe_raise("preflight")
        return {}

    def status(self) -> dict:
        self._record("status")
        self._maybe_raise("status")
        with self._lock:
            index = min(self._status_index, len(self.status_responses) - 1)
            self._status_index += 1
            return dict(self.status_responses[index])

    def install(self) -> dict:
        self._record("install")
        self._maybe_raise("install")
        return {}

    def start(self, *, provider: str, model: str, base_url: str, api_key: str | None) -> dict:
        self._record("start")
        with self._lock:
            self.started_keys.append(api_key)
        self._maybe_raise("start")
        return {"state": "running", "running": True}

    def client_url(self) -> str:
        self._record("url")
        self.url_called.set()
        self._maybe_raise("url")
        return self.url

    def stop(self) -> dict:
        with self._lock:
            self.stop_count += 1
        self._record("stop")
        self.stop_called.set()
        self._maybe_raise("stop")
        return {"state": "stopped"}


class FakeSink:
    """Records every UiSink call and exposes events for synchronization."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.status_calls: list[tuple[str, bool]] = []
        self.navigate_calls: list[str] = []
        self.settings_calls = 0
        self.status_published = threading.Event()
        self.navigated = threading.Event()
        self.settings_opened = threading.Event()

    def publish_status(self, message: str, *, error: bool = False) -> None:
        with self._lock:
            self.status_calls.append((message, error))
        self.status_published.set()

    def navigate(self, url: str) -> None:
        with self._lock:
            self.navigate_calls.append(url)
        self.navigated.set()

    def open_settings(self) -> None:
        with self._lock:
            self.settings_calls += 1
        self.settings_opened.set()


class ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


@pytest.fixture
def harness():
    coordinators: list[ConnectionCoordinator] = []
    handler = ListHandler()
    logger = logging.getLogger("test-leo-shell-connection")
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    def factory(bridge: FakeBridge, sink: FakeSink, **kwargs) -> ConnectionCoordinator:
        coordinator = ConnectionCoordinator(bridge, sink, logger, **kwargs)
        coordinators.append(coordinator)
        return coordinator

    yield factory, handler
    for coordinator in coordinators:
        coordinator.close(stop_daemon=False)


# ------------------------------------------------------------------ happy path


def test_happy_path_navigates_without_ack(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    coordinator = factory(bridge, sink)

    reply = coordinator.submit(PROFILE, "sk-key-1", requires_ack=False)
    assert reply == {"ok": True, "pending": True, "request_id": 1}
    assert sink.navigated.wait(5)
    assert sink.navigate_calls == [URL]
    assert bridge.calls == ["preflight", "status", "start", "url"]
    assert sink.status_calls == []


def test_same_fingerprint_skips_restart(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    bridge.status_responses = [{"state": "running", "running": True}]
    coordinator = factory(bridge, sink)

    coordinator.submit(PROFILE, "sk-key-1", requires_ack=False)
    assert sink.navigated.wait(5)
    coordinator.submit(PROFILE, "sk-key-1", requires_ack=False)
    deadline = time.monotonic() + 5
    while True:
        with sink._lock:
            if len(sink.navigate_calls) >= 2:
                break
        assert time.monotonic() < deadline, "second navigation never happened"
        threading.Event().wait(0.01)
    assert sink.navigate_calls == [URL, URL]
    # The second connect reused the fingerprint: no new start, and the only
    # stop is the first connect's restart of the already-running daemon.
    assert bridge.calls.count("start") == 1
    assert bridge.calls.count("stop") == 1


def test_key_change_forces_restart(harness):
    """A new credential on an otherwise identical profile must restart the daemon.

    Regression: the fingerprint used to be provider|model|base_url only, so
    saving a key onto an existing keyless profile changed nothing it compared.
    The START stage was skipped as "same-fingerprint" and the daemon kept
    running without the credential -- the key was stored but never took effect.
    """

    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    bridge.status_responses = [{"state": "running", "running": True}]
    coordinator = factory(bridge, sink)

    coordinator.submit(PROFILE, None, requires_ack=False)  # keyless browse
    assert sink.navigated.wait(5)
    coordinator.submit(PROFILE, "sk-key-1", requires_ack=False)  # key added
    deadline = time.monotonic() + 5
    while True:
        with sink._lock:
            if len(sink.navigate_calls) >= 2:
                break
        assert time.monotonic() < deadline, "second navigation never happened"
        threading.Event().wait(0.01)
    # Two starts: the keyless one, then a real restart carrying the credential.
    assert bridge.calls.count("start") == 2
    assert bridge.started_keys == [None, "sk-key-1"]


# -------------------------------------------------------------- generations


def test_stale_generation_never_navigates(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    entered, release = threading.Event(), threading.Event()
    bridge.preflight_gate = (entered, release)
    coordinator = factory(bridge, sink)

    first = coordinator.submit(PROFILE, None, requires_ack=False)
    assert entered.wait(5)  # generation 1 is blocked inside PREFLIGHT.
    second = coordinator.submit(PROFILE, None, requires_ack=False)
    assert second["request_id"] == first["request_id"] + 1
    release.set()

    assert sink.navigated.wait(5)
    # Exactly one navigation total: the stale generation must have bailed out.
    assert sink.navigate_calls == [URL]


def test_ack_timeout_still_navigates(harness):
    factory, handler = harness
    bridge, sink = FakeBridge(), FakeSink()
    coordinator = factory(bridge, sink, ack_timeout=0.1)

    coordinator.submit(PROFILE, None, requires_ack=True)
    assert sink.navigated.wait(5)
    assert sink.navigate_calls == [URL]
    assert any("ACK_TIMEOUT" in message for message in handler.messages)


def test_ack_received_before_timeout_navigates_without_timeout(harness):
    factory, handler = harness
    bridge, sink = FakeBridge(), FakeSink()
    coordinator = factory(bridge, sink, ack_timeout=30.0)

    reply = coordinator.submit(PROFILE, None, requires_ack=True)
    assert bridge.url_called.wait(5)
    # The worker is parked in the ack wait, so navigation cannot have happened.
    assert not sink.navigated.is_set()
    coordinator.acknowledge(reply["request_id"])
    assert sink.navigated.wait(5)
    assert sink.navigate_calls == [URL]
    assert not any("ACK_TIMEOUT" in message for message in handler.messages)


# ------------------------------------------------------------------- failures


def test_bridge_error_publishes_public_code_and_opens_settings(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    bridge.errors["start"] = BridgeError("DAEMON_START_FAILED", "daemon exploded")
    coordinator = factory(bridge, sink)

    coordinator.submit(PROFILE, "sk-key-1", requires_ack=False)
    assert sink.settings_opened.wait(5)
    assert (PUBLIC_CONNECTION_FAILED, True) in sink.status_calls
    # The precise bridge code must never leak to the front end.
    assert all("DAEMON_START_FAILED" not in message for message, _ in sink.status_calls)
    assert sink.settings_calls == 1
    assert not sink.navigated.is_set()
    # A failed attempt triggers one best-effort cleanup stop.
    assert bridge.stop_called.wait(5)


# ---------------------------------------------------------------------- close


def test_close_stops_daemon_exactly_once(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    coordinator = factory(bridge, sink)

    coordinator.close()
    coordinator.close()
    assert bridge.stop_called.wait(5)
    assert bridge.stop_count == 1


def test_close_without_stop_daemon_skips_physical_stop(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    coordinator = factory(bridge, sink)

    coordinator.close(stop_daemon=False)
    assert not bridge.stop_called.is_set()


def test_submit_after_close_is_refused(harness):
    factory, _ = harness
    bridge, sink = FakeBridge(), FakeSink()
    coordinator = factory(bridge, sink)

    coordinator.close(stop_daemon=False)
    reply = coordinator.submit(PROFILE, None, requires_ack=False)
    assert reply["ok"] is False
    assert reply["pending"] is False
    assert reply["message"] == PUBLIC_APP_CLOSING
    assert not sink.navigated.is_set()
