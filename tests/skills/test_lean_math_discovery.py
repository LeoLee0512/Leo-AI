"""2D-A: lean-math must not be pinned to one machine.

Five absolute ``/home/leo/...`` paths and a hardcoded Lean release candidate
meant the skill could only work on the author's WSL user. On anyone else's
machine it failed with a subprocess error rather than saying Lean was not
installed, which is the difference between a bug report and an instruction.

These tests run on Windows where Lean is absent, so they exercise discovery and
the health states rather than Lean itself. Whether a real toolchain elaborates
correctly is a separate, manual acceptance item -- see
``docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]


def _skill_root() -> pathlib.Path:
    override = os.environ.get("LEO_SKILLS_ROOT")
    root = pathlib.Path(override) if override else REPO / "skills"
    return root / "lean-math"


class FakeHost:
    def __init__(self):
        self.files = {}

    def read_file(self, path):
        if path not in self.files:
            raise FileNotFoundError(path)
        return {"content": self.files[path]}

    def write_file(self, path, content):
        self.files[path] = content
        return {"path": path}


@pytest.fixture
def kernel(monkeypatch):
    path = _skill_root() / "kernel.py"
    assert path.is_file(), f"canonical lean-math kernel not found at {path}"
    sys.modules["host"] = FakeHost()
    spec = importlib.util.spec_from_file_location("leo_lean_kernel", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop("host", None)


def _clear_env(monkeypatch, kernel):
    for name in (kernel.LEAN_ENV_TOOLCHAIN, kernel.LEAN_ENV_PROJECT, kernel.LEAN_ENV_MATHLIB):
        monkeypatch.delenv(name, raising=False)
    kernel.LEAN_STATE.clear()


def test_no_personal_paths_remain_in_the_source():
    """The literal machine binding is gone from the shipped skill."""
    source = (_skill_root() / "kernel.py").read_text(encoding="utf-8")
    assert "/home/leo" not in source, "lean-math still hardcodes a personal home directory"
    assert "v4.34.0-rc2" not in source, "lean-math still pins a release-candidate toolchain"


def test_configuration_beats_discovery(kernel, monkeypatch, tmp_path):
    """An explicitly configured toolchain is used without searching."""
    _clear_env(monkeypatch, kernel)
    toolchain = tmp_path / "toolchain"
    (toolchain / "bin").mkdir(parents=True)
    (toolchain / "bin" / "lean").write_text("", encoding="utf-8")
    (toolchain / "bin" / "lake").write_text("", encoding="utf-8")
    monkeypatch.setenv(kernel.LEAN_ENV_TOOLCHAIN, str(toolchain))

    found, lean, lake = kernel.lean_discover_toolchain()
    assert found == str(toolchain)
    assert lean and lean.endswith("lean")
    assert lake and lake.endswith("lake")


def test_missing_toolchain_reports_not_installed(kernel, monkeypatch, tmp_path):
    """Absent Lean is NOT_INSTALLED with an actionable message, not a crash."""
    _clear_env(monkeypatch, kernel)
    monkeypatch.setenv(kernel.LEAN_ENV_TOOLCHAIN, str(tmp_path / "nothing-here"))
    monkeypatch.setattr(kernel.shutil, "which", lambda _name: None)

    status = kernel.lean_toolchain_status()
    assert status["state"] == kernel.LEAN_NOT_INSTALLED, status
    assert "elan" in status["summary"]
    # Never install several gigabytes on the user's behalf.
    assert "automatically" in status["summary"]


def test_toolchain_without_project_reports_project_not_ready(kernel, monkeypatch, tmp_path):
    """Lean present but no resolved Lake project is a distinct, fixable state."""
    _clear_env(monkeypatch, kernel)
    toolchain = tmp_path / "tc"
    (toolchain / "bin").mkdir(parents=True)
    for name in ("lean", "lake"):
        (toolchain / "bin" / name).write_text("", encoding="utf-8")
    monkeypatch.setenv(kernel.LEAN_ENV_TOOLCHAIN, str(toolchain))
    monkeypatch.setenv(kernel.LEAN_ENV_PROJECT, str(tmp_path / "no-project"))

    # `lean --version` is allowed: it is a cheap probe and the version is useful
    # in the report. What must not happen is any elaboration or install.
    calls = []

    class Probe:
        stdout, stderr, returncode = "Lean (version 4.20.0)", "", 0

    def fake_run(args, **kwargs):
        calls.append(args)
        return Probe()

    monkeypatch.setattr(kernel.subprocess, "run", fake_run)

    status = kernel.lean_toolchain_status()
    assert status["state"] == kernel.LEAN_PROJECT_NOT_READY, status
    assert kernel.LEAN_ENV_PROJECT in status["summary"]
    assert all(list(args)[1:] == ["--version"] for args in calls), calls


def test_a_directory_with_the_right_name_is_not_a_project(kernel, tmp_path):
    """An empty ~/lean_test must not be mistaken for a built project."""
    empty = tmp_path / "lean_test"
    empty.mkdir()
    assert kernel.lean_project_ready(str(empty)) is False

    (empty / "lakefile.lean").write_text("", encoding="utf-8")
    assert kernel.lean_project_ready(str(empty)) is False, "a lakefile alone is not resolved"

    (empty / "lake-manifest.json").write_text("{}", encoding="utf-8")
    assert kernel.lean_project_ready(str(empty)) is True


def test_toolchain_mismatch_is_reported_rather_than_used(kernel, monkeypatch, tmp_path):
    """A project pinned to another Lean must not be elaborated silently."""
    _clear_env(monkeypatch, kernel)
    toolchain = tmp_path / "leanprover--lean4---v4.20.0"
    (toolchain / "bin").mkdir(parents=True)
    for name in ("lean", "lake"):
        (toolchain / "bin" / name).write_text("", encoding="utf-8")
    project = tmp_path / "proj"
    project.mkdir()
    (project / "lakefile.lean").write_text("", encoding="utf-8")
    (project / "lake-manifest.json").write_text("{}", encoding="utf-8")
    (project / "lean-toolchain").write_text("leanprover/lean4:v4.99.0\n", encoding="utf-8")
    mathlib = tmp_path / "mathlib"
    (mathlib / ".lake/build/lib/lean/Mathlib").mkdir(parents=True)

    monkeypatch.setenv(kernel.LEAN_ENV_TOOLCHAIN, str(toolchain))
    monkeypatch.setenv(kernel.LEAN_ENV_PROJECT, str(project))
    monkeypatch.setenv(kernel.LEAN_ENV_MATHLIB, str(mathlib))

    class Probe:
        stdout, stderr, returncode = "Lean (version 4.20.0)", "", 0

    monkeypatch.setattr(kernel.subprocess, "run", lambda *a, **k: Probe())

    status = kernel.lean_toolchain_status()
    assert status["state"] == kernel.LEAN_VERSION_MISMATCH, status
    assert "v4.99.0" in status["summary"]


def test_require_ready_raises_with_the_state_in_the_message(kernel, monkeypatch, tmp_path):
    """Callers get a message naming the state, not a bare subprocess error."""
    _clear_env(monkeypatch, kernel)
    monkeypatch.setenv(kernel.LEAN_ENV_TOOLCHAIN, str(tmp_path / "absent"))
    monkeypatch.setattr(kernel.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match=kernel.LEAN_NOT_INSTALLED):
        kernel.lean_require_ready()


def test_status_names_the_configuration_variables(kernel, monkeypatch, tmp_path):
    """A user reading the status must learn how to fix it."""
    _clear_env(monkeypatch, kernel)
    monkeypatch.setenv(kernel.LEAN_ENV_TOOLCHAIN, str(tmp_path / "absent"))
    monkeypatch.setattr(kernel.shutil, "which", lambda _name: None)
    status = kernel.lean_toolchain_status()
    assert status["configure_with"] == {
        "toolchain": "LEO_LEAN_TOOLCHAIN",
        "project": "LEO_LEAN_PROJECT",
        "mathlib": "LEO_MATHLIB_DIR",
    }
