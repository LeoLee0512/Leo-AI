"""Regression tests for the fixed WebView2 runtime pin.

The black-screen incident: pinning the exe *file* instead of its parent
*directory* made CoreWebView2Environment.CreateAsync fail with 0x80070002.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from leo_shell import webview2_runtime
from leo_shell.webview2_runtime import WebView2RuntimeError, configure_fixed_runtime


class _FakePaths:
    def __init__(self, root: Path):
        self._root = root

    def webview2_dir(self) -> Path:
        return self._root


def _make_runtime(root: Path, *, nested: bool = False) -> Path:
    exe_dir = root / "inner" if nested else root
    exe_dir.mkdir(parents=True, exist_ok=True)
    (exe_dir / "msedgewebview2.exe").write_bytes(b"MZ")
    return exe_dir


def _fake_webview(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    module = types.ModuleType("webview")
    module.settings = {}
    monkeypatch.setitem(sys.modules, "webview", module)
    return module


def test_pin_points_at_directory_containing_exe(tmp_path, monkeypatch):
    exe_dir = _make_runtime(tmp_path / "wv2")
    webview = _fake_webview(monkeypatch)
    monkeypatch.setattr(webview2_runtime, "_grant_acl", lambda *a, **k: None)

    configure_fixed_runtime(_FakePaths(tmp_path / "wv2"))

    pinned = Path(webview.settings["WEBVIEW2_RUNTIME_PATH"])
    assert pinned == exe_dir
    assert pinned.is_dir()
    assert (pinned / "msedgewebview2.exe").is_file()


def test_nested_exe_pins_its_parent_directory(tmp_path, monkeypatch):
    exe_dir = _make_runtime(tmp_path / "wv2", nested=True)
    webview = _fake_webview(monkeypatch)
    monkeypatch.setattr(webview2_runtime, "_grant_acl", lambda *a, **k: None)

    configure_fixed_runtime(_FakePaths(tmp_path / "wv2"))

    assert Path(webview.settings["WEBVIEW2_RUNTIME_PATH"]) == exe_dir


def test_missing_exe_raises(tmp_path, monkeypatch):
    (tmp_path / "wv2").mkdir()
    _fake_webview(monkeypatch)
    monkeypatch.setattr(webview2_runtime, "_grant_acl", lambda *a, **k: None)

    with pytest.raises(WebView2RuntimeError):
        configure_fixed_runtime(_FakePaths(tmp_path / "wv2"))


def test_two_candidates_raise(tmp_path, monkeypatch):
    # No direct child exe: two nested candidates must be rejected as ambiguous.
    _make_runtime(tmp_path / "wv2" / "first", nested=True)
    _make_runtime(tmp_path / "wv2" / "second", nested=True)
    _fake_webview(monkeypatch)
    monkeypatch.setattr(webview2_runtime, "_grant_acl", lambda *a, **k: None)

    with pytest.raises(WebView2RuntimeError):
        configure_fixed_runtime(_FakePaths(tmp_path / "wv2"))
