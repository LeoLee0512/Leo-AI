"""Tests for leo_shell.paths (AppPaths resolution, UNC rejection, webview2)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from leo_shell import paths as paths_module
from leo_shell.paths import AppPaths


# ---------------------------------------------------------------------------
# root resolution


def test_from_root_explicit(tmp_path: Path) -> None:
    paths = AppPaths.from_root(tmp_path)
    assert paths.root == tmp_path
    assert paths.user == tmp_path / "user"
    assert paths.theme == tmp_path / "theme"
    assert paths.bridge_script == tmp_path / "bridge" / "leo_bridge.sh"
    assert paths.runtime_dir == tmp_path / "runtime"
    assert paths.logs == tmp_path / "user" / "logs"
    assert paths.credentials == tmp_path / "user" / "credentials"


def test_from_root_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEO_STUDIO_ROOT", raising=False)
    monkeypatch.setenv("LEO_STUDIO_ROOT", str(tmp_path))
    assert AppPaths.from_root().root == tmp_path


def test_from_root_dev_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEO_STUDIO_ROOT", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    expected = Path(paths_module.__file__).resolve().parents[2]
    assert AppPaths.from_root().root == expected


def test_from_root_frozen_wins_over_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exe_dir = tmp_path / "bundle"
    exe_dir.mkdir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "LeoAIStudio.exe"))
    monkeypatch.setenv("LEO_STUDIO_ROOT", str(tmp_path / "elsewhere"))
    assert AppPaths.from_root().root == exe_dir


# ---------------------------------------------------------------------------
# unsupported roots


def test_reject_unsupported_root_accepts_local(tmp_path: Path) -> None:
    AppPaths.from_root(tmp_path).reject_unsupported_root()  # must not raise


def test_reject_unsupported_root_unc() -> None:
    paths = AppPaths(Path(r"\\server\share\leo"))
    with pytest.raises(ValueError):
        paths.reject_unsupported_root()


def test_reject_unsupported_root_unc_forward_slashes() -> None:
    paths = AppPaths(Path("//server/share/leo"))
    with pytest.raises(ValueError):
        paths.reject_unsupported_root()


def test_reject_unsupported_root_mapped_network_drive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths_module, "_drive_type", lambda anchor: 4)
    with pytest.raises(ValueError):
        AppPaths.from_root(tmp_path).reject_unsupported_root()


def test_reject_unsupported_root_drive_type_unknown_is_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths_module, "_drive_type", lambda anchor: None)
    AppPaths.from_root(tmp_path).reject_unsupported_root()  # must not raise


# ---------------------------------------------------------------------------
# webview2_dir


def _make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.from_root(tmp_path)


def _write_manifest(path: Path, payload: dict, *, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload)
    path.write_bytes(("\ufeff" + text).encode("utf-8") if bom else text.encode("utf-8"))


def test_webview2_dir_from_runtime_manifest(tmp_path: Path) -> None:
    target = tmp_path / "runtime" / "webview2" / "1.2.3" / "runtime-x64"
    target.mkdir(parents=True)
    _write_manifest(
        tmp_path / "runtime" / "runtime-manifest.json",
        {"dependencies": {"webview2": {"path": "runtime/webview2/1.2.3/runtime-x64"}}},
    )
    assert _make_paths(tmp_path).webview2_dir() == target.resolve()


def test_webview2_dir_from_dependencies_json_extracted_directory(tmp_path: Path) -> None:
    target = tmp_path / "runtime" / "webview2" / "1.2.3" / "FixedVersion.x64"
    target.mkdir(parents=True)
    _write_manifest(
        tmp_path / "runtime" / "dependencies.json",
        {"webview2": {"extracted_directory": "FixedVersion.x64"}},
    )
    assert _make_paths(tmp_path).webview2_dir() == target


def test_webview2_dir_manifest_with_bom(tmp_path: Path) -> None:
    target = tmp_path / "runtime" / "webview2" / "v" / "x"
    target.mkdir(parents=True)
    _write_manifest(
        tmp_path / "runtime" / "runtime-manifest.json",
        {"dependencies": {"webview2": {"path": "runtime/webview2/v/x"}}},
        bom=True,
    )
    assert _make_paths(tmp_path).webview2_dir() == target.resolve()


def test_webview2_dir_rejects_absolute_manifest_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / "webview2-outside"
    outside.mkdir(exist_ok=True)
    _write_manifest(
        tmp_path / "runtime" / "runtime-manifest.json",
        {"dependencies": {"webview2": {"path": str(outside)}}},
    )
    with pytest.raises(FileNotFoundError):
        _make_paths(tmp_path).webview2_dir()


def test_webview2_dir_rejects_escaping_manifest_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / "webview2-escape"
    outside.mkdir(exist_ok=True)
    _write_manifest(
        tmp_path / "runtime" / "runtime-manifest.json",
        {"dependencies": {"webview2": {"path": "../webview2-escape"}}},
    )
    with pytest.raises(FileNotFoundError):
        _make_paths(tmp_path).webview2_dir()


def test_webview2_dir_rejects_missing_manifest_target(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path / "runtime" / "runtime-manifest.json",
        {"dependencies": {"webview2": {"path": "runtime/webview2/v/x"}}},
    )
    with pytest.raises(FileNotFoundError):
        _make_paths(tmp_path).webview2_dir()


def test_webview2_dir_skips_oversized_manifest(tmp_path: Path) -> None:
    fallback = tmp_path / "runtime" / "webview2" / "only-one"
    fallback.mkdir(parents=True)
    manifest = tmp_path / "runtime" / "runtime-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_bytes(b'{"dependencies":' + b" " * (1024 * 1024) + b"}")
    assert _make_paths(tmp_path).webview2_dir() == fallback


def test_webview2_dir_fallback_unique_subdir(tmp_path: Path) -> None:
    only = tmp_path / "runtime" / "webview2" / "152.0.4191.53"
    only.mkdir(parents=True)
    assert _make_paths(tmp_path).webview2_dir() == only


def test_webview2_dir_fallback_ambiguous_subdirs(tmp_path: Path) -> None:
    (tmp_path / "runtime" / "webview2" / "a").mkdir(parents=True)
    (tmp_path / "runtime" / "webview2" / "b").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        _make_paths(tmp_path).webview2_dir()


def test_webview2_dir_missing_everything(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _make_paths(tmp_path).webview2_dir()
