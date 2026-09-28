"""Single-instance IPC retry-hardening tests (no real pipe needed)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import leo_shell.single_instance as si
from leo_shell.single_instance import SingleInstance


class _FakePaths:
    def __init__(self, root: Path):
        self.root = root
        self.user = root / "user"


def _instance(tmp_path, monkeypatch):
    monkeypatch.setattr(si, "_RETRY_INTERVAL_SECONDS", 0.02)
    monkeypatch.setattr(si, "_FORWARD_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(si, "_LISTEN_BIND_TIMEOUT_SECONDS", 0.2)
    inst = SingleInstance(_FakePaths(tmp_path))
    monkeypatch.setattr(inst, "_load_authkey", lambda: b"k" * 32)
    return inst


class _FakeConnection:
    def __init__(self):
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def send(self, message):
        self.sent.append(message)


def test_forward_recovers_from_transient_pipe_race(tmp_path, monkeypatch):
    inst = _instance(tmp_path, monkeypatch)
    connection = _FakeConnection()
    calls = {"count": 0}

    def flaky_client(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise FileNotFoundError("pipe not up yet")
        return connection

    monkeypatch.setattr(si, "Client", flaky_client)
    assert inst.forward("activate") is True
    assert calls["count"] == 3
    assert connection.sent == [{"action": "activate"}]


def test_forward_gives_up_after_deadline(tmp_path, monkeypatch):
    inst = _instance(tmp_path, monkeypatch)

    def always_missing(*args, **kwargs):
        raise FileNotFoundError("no pipe")

    monkeypatch.setattr(si, "Client", always_missing)
    started = time.monotonic()
    assert inst.forward("activate") is False
    assert time.monotonic() - started < 2.0  # bounded by the monkeypatched timeout


def test_forward_rejects_unknown_action(tmp_path, monkeypatch):
    inst = _instance(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        inst.forward("restart")


def test_bind_listener_retries_until_name_is_free(tmp_path, monkeypatch):
    inst = _instance(tmp_path, monkeypatch)
    sentinel = object()
    calls = {"count": 0}

    def flaky_listener(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise PermissionError("previous pipe still tearing down")
        return sentinel

    monkeypatch.setattr(si, "Listener", flaky_listener)
    assert inst._bind_listener(b"k" * 32) is sentinel
    assert calls["count"] == 2


def test_bind_listener_reports_persistent_failure(tmp_path, monkeypatch):
    inst = _instance(tmp_path, monkeypatch)

    def always_denied(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(si, "Listener", always_denied)
    with pytest.raises(PermissionError):
        inst._bind_listener(b"k" * 32)
