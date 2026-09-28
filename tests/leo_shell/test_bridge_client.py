"""Tests for leo_shell.bridge_client using an injected fake runner.

No real wsl.exe invocation ever happens here: the runner callable captures
argv/kwargs and returns a scripted CompletedProcess or raises on cue.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from leo_shell.bridge_client import BridgeError, WslBridge, windows_path_to_wsl

KEY = "sk-testsecret-1234567890"
REVISION = "a792c38d9984be428437b548db29baab3322f6dc"


def make_paths(root: Path | None = None) -> SimpleNamespace:
    base = root or Path(r"C:\pkg")
    return SimpleNamespace(
        bridge_script=base / "bridge" / "leo_bridge.sh",
        runtime_dir=base / "runtime",
        user=base / "user",
    )


def ok_line(data: dict | None = None, action: str = "x") -> str:
    return json.dumps({"schema": 1, "ok": True, "action": action, "data": data or {}})


def error_line(code: str, message: str = "boom", guidance: list[str] | None = None) -> str:
    return json.dumps(
        {
            "schema": 1,
            "ok": False,
            "action": "x",
            "error": {"code": code, "message": message, "guidance": guidance or [], "details": {}},
        }
    )


class FakeRunner:
    def __init__(self, handler=None):
        self.calls: list[tuple[list[str], dict]] = []
        self.handler = handler

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        if self.handler is not None:
            return self.handler(argv, **kwargs)
        # Script the real startup phases as separate protocol responses. The
        # security tests below inspect every argv and only the final start env.
        data = {}
        if any(str(part).endswith("leo_identity.py") for part in argv):
            data = {"identity": "Leo AI", "version": 1, "applied": True}
        elif any(str(part).endswith("leo_runtime_compat.py") for part in argv):
            data = {"compatibility": "submit-output", "version": 1, "applied": True, "browse_guard": True}
        elif any(str(part).endswith("leo_runtime_features.py") for part in argv):
            data = {"example_persistence": True, "conversation_runtime": True, "version": 1, "applied": True}
        elif any(str(part).endswith("leo_model_selection.py") for part in argv):
            data = {"global_key_override_empty": True, "restart_required": False,
                    "active_profile_empty": True}
        return subprocess.CompletedProcess(argv, 0, stdout=ok_line(data) + "\n", stderr="")


def make_bridge(runner: FakeRunner, *, root: Path | None = None, **kwargs) -> WslBridge:
    paths = make_paths(root)
    if root is not None:
        paths.bridge_script.parent.mkdir(parents=True, exist_ok=True)
        paths.bridge_script.write_text("#!/bin/sh\n", encoding="utf-8")
    return WslBridge(paths, runner=runner, **kwargs)


# --------------------------------------------------------------------- argv


def test_preflight_argv_path_conversion_and_hidden_window(tmp_path):
    runner = FakeRunner()
    bridge = make_bridge(runner, root=tmp_path)
    assert bridge.preflight() == {}
    argv, kwargs = runner.calls[0]
    assert argv == ["wsl.exe", "-e", "/bin/sh", windows_path_to_wsl(tmp_path / "bridge/leo_bridge.sh"), "preflight"]
    assert kwargs["timeout"] == 60
    assert kwargs["shell"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["creationflags"] & 0x08000000  # CREATE_NO_WINDOW
    info = kwargs.get("startupinfo")
    assert info is not None
    assert info.dwFlags & subprocess.STARTF_USESHOWWINDOW
    assert info.wShowWindow == 0  # SW_HIDE


def test_distro_flag_inserted_before_e():
    runner = FakeRunner()
    bridge = make_bridge(runner, distro="Ubuntu-24.04")
    bridge.status()
    argv, kwargs = runner.calls[0]
    assert argv[1:3] == ["-d", "Ubuntu-24.04"]
    assert kwargs["timeout"] == 30


def test_windows_path_to_wsl_conversion():
    assert windows_path_to_wsl(r"C:\x\y") == "/mnt/c/x/y"
    assert windows_path_to_wsl(r"d:\A B\c.tar") == "/mnt/d/A B/c.tar"
    assert windows_path_to_wsl("/already/posix") == "/already/posix"
    with pytest.raises(BridgeError) as excinfo:
        windows_path_to_wsl(r"\\server\share\leo_bridge.sh")
    assert excinfo.value.code == "INVALID_ARGUMENT"


# ------------------------------------------------------------------- secrets


def test_start_secret_only_in_env_never_in_argv(monkeypatch):
    monkeypatch.setenv("WSLENV", "PRESET")
    runner = FakeRunner()
    bridge = make_bridge(runner)
    bridge.start(provider="chatgpt", model="deepseek-chat", base_url="https://api.deepseek.com", api_key=KEY)
    assert len(runner.calls) == 6  # stop, identity, compatibility, deletion persistence, selection, start
    argv, kwargs = runner.calls[-1]
    assert argv[-4:] == ["start", "chatgpt", "deepseek-chat", "https://api.deepseek.com"]
    assert all(KEY not in str(part) for call, _ in runner.calls for part in call)
    assert all(KEY not in str(options.get("env", {})) for _, options in runner.calls[:-1])
    env = kwargs["env"]
    assert env["OPENAI4S_LLM_API_KEY"] == KEY
    assert env["OPENAI4S_CHATGPT_API_KEY"] == KEY
    advertised = env["WSLENV"].split(":")
    assert advertised[0] == "PRESET"
    assert "OPENAI4S_LLM_API_KEY" in advertised
    assert "OPENAI4S_CHATGPT_API_KEY" in advertised
    assert kwargs["timeout"] == 120


def test_start_without_key_explicitly_clears_inherited_keys_and_enables_browse(monkeypatch):
    monkeypatch.delenv("WSLENV", raising=False)
    runner = FakeRunner()
    bridge = make_bridge(runner)
    bridge.start(provider="ark", model="doubao", base_url="", api_key=None)
    assert len(runner.calls) == 6
    _, kwargs = runner.calls[-1]
    env = kwargs["env"]
    assert env.get("OPENAI4S_LLM_API_KEY") == ""
    assert env.get("LEO_STUDIO_BROWSE_ONLY") == "1"
    assert env.get("OPENAI4S_SKIP_DOTENV") == "1"
    assert "LEO_STUDIO_BROWSE_ONLY" in env["WSLENV"].split(":")
    assert "--browse" in runner.calls[-2][0]


def test_sensitive_argument_name_rejected_before_spawn():
    runner = FakeRunner()
    bridge = make_bridge(runner)
    with pytest.raises(BridgeError) as excinfo:
        bridge.start(provider="--api-key", model="m", base_url="", api_key=None)
    assert excinfo.value.code == "INVALID_ARGUMENT"
    assert runner.calls == []


def test_secret_redacted_from_error_output():
    def handler(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=f"garbage {KEY}\n", stderr="")

    runner = FakeRunner(handler)
    bridge = make_bridge(runner)
    with pytest.raises(BridgeError) as excinfo:
        bridge.start(provider="chatgpt", model="m", base_url="", api_key=KEY)
    assert excinfo.value.code == "BRIDGE_OUTPUT_INVALID"
    assert KEY not in str(excinfo.value)
    assert KEY not in excinfo.value.message


# -------------------------------------------------------------------- output


def test_json_is_last_non_empty_stdout_line_with_noise(tmp_path):
    payload = ok_line({"a": 1})
    stdout = f"wsl localhost proxy warning\n{payload}\n\n"

    runner = FakeRunner(lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="noise"))
    assert make_bridge(runner, root=tmp_path).preflight() == {"a": 1}


def test_json_recovered_when_trailing_noise_follows_payload():
    payload = ok_line({"b": 2})
    stdout = f"{payload}\ntrailing noise\n"

    runner = FakeRunner(lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr=""))
    assert make_bridge(runner).status() == {"b": 2}


def test_ok_false_raises_bridge_error_with_code_and_guidance():
    def handler(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv, 1, stdout=error_line("PROVIDER_INVALID", "bad provider", ["fix it"]) + "\n", stderr=""
        )

    runner = FakeRunner(handler)
    with pytest.raises(BridgeError) as excinfo:
        make_bridge(runner).start(provider="nope", model="m", base_url="", api_key=None)
    exc = excinfo.value
    assert exc.code == "PROVIDER_INVALID"
    assert exc.message == "bad provider"
    assert exc.guidance == ["fix it"]


def test_timeout_maps_to_wsl_timeout():
    def handler(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs["timeout"])

    with pytest.raises(BridgeError) as excinfo:
        make_bridge(FakeRunner(handler)).status()
    assert excinfo.value.code == "WSL_TIMEOUT"


def test_missing_wsl_exe_maps_to_wsl_unavailable(tmp_path):
    def handler(argv, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "wsl.exe")

    with pytest.raises(BridgeError) as excinfo:
        make_bridge(FakeRunner(handler), root=tmp_path).preflight()
    assert excinfo.value.code == "WSL_UNAVAILABLE"


def test_non_json_output_maps_to_bridge_output_invalid():
    runner = FakeRunner(lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout="garbage\n", stderr="junk"))
    with pytest.raises(BridgeError) as excinfo:
        make_bridge(runner).doctor()
    assert excinfo.value.code == "BRIDGE_OUTPUT_INVALID"


# ------------------------------------------------------------------ url action


def test_client_url_returns_validated_url():
    url = "http://127.0.0.1:8760/?token=abc123"
    runner = FakeRunner(lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout=ok_line({"client_url": url}, "url"), stderr=""))
    bridge = make_bridge(runner)
    assert bridge.client_url() == url
    argv, kwargs = runner.calls[0]
    assert argv[-1] == "url"
    assert kwargs["timeout"] == 30


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://127.0.0.1:9999/?token=abc",       # wrong port
        "https://127.0.0.1:8760/?token=abc",      # wrong scheme
        "http://evil.example.com:8760/?token=a",  # non-loopback host
        "http://user:pw@127.0.0.1:8760/?token=a",  # userinfo
        "http://127.0.0.1:8760/?token=a#frag",    # fragment
        "",                                        # empty
        None,                                      # missing
    ],
)
def test_client_url_rejects_untrusted_values(bad_url):
    payload = ok_line({"client_url": bad_url}, "url")
    runner = FakeRunner(lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout=payload, stderr=""))
    with pytest.raises(BridgeError) as excinfo:
        make_bridge(runner).client_url()
    assert excinfo.value.code == "CLIENT_URL_INVALID"


# ----------------------------------------------------------------- install


def write_manifest(runtime_dir: Path) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime-manifest.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "archive": "openai4s-linux-x86_64.tar.gz",
                "sha256": "a" * 64,
                "version": "0.2.0",
                "upstream": {"revision": REVISION},
            }
        ),
        encoding="utf-8",
    )
    (runtime_dir / "openai4s-linux-x86_64.tar.gz").write_bytes(b"runtime")


def test_install_runs_three_bridge_actions(tmp_path):
    write_manifest(tmp_path / "runtime")
    cache = tmp_path / "user" / "cache"
    cache.mkdir(parents=True)
    source = cache / f"source-{REVISION}.tar"
    source.write_bytes(b"source-bytes")
    expected_source_sha = hashlib.sha256(b"source-bytes").hexdigest()

    runner = FakeRunner()
    bridge = WslBridge(make_paths(tmp_path), runner=runner)
    result = bridge.install()

    assert [call[0][4] for call in runner.calls] == ["install-runtime", "stage-source", "activate-source"]
    argv0, kwargs0 = runner.calls[0]
    assert argv0[5].startswith("/mnt/") and argv0[5].endswith("openai4s-linux-x86_64.tar.gz")
    assert argv0[6] == "a" * 64
    assert argv0[7] == "0.2.0"
    assert kwargs0["timeout"] == 600
    argv1, _ = runner.calls[1]
    assert argv1[5].startswith("/mnt/") and argv1[5].endswith(f"source-{REVISION}.tar")
    assert argv1[6] == expected_source_sha
    assert argv1[7] == REVISION
    argv2, _ = runner.calls[2]
    assert argv2[5] == REVISION
    assert len(argv2) == 6
    assert set(result) == {"runtime", "source", "activate"}


def test_install_missing_source_archive_fails_before_spawn(tmp_path):
    write_manifest(tmp_path / "runtime")
    runner = FakeRunner()
    bridge = WslBridge(make_paths(tmp_path), runner=runner)
    with pytest.raises(BridgeError) as excinfo:
        bridge.install()
    assert excinfo.value.code == "SOURCE_ARCHIVE_UNAVAILABLE"
    assert runner.calls == []


@pytest.mark.parametrize("phase,code", [
    ("leo_identity.py", "IDENTITY_PREPARATION_FAILED"),
    ("leo_runtime_compat.py", "RUNTIME_COMPAT_PREPARATION_FAILED"),
    ("leo_runtime_features.py", "CONVERSATION_RUNTIME_PREPARATION_FAILED"),
    ("leo_model_selection.py", "LOCAL_SELECTION_FAILED"),
])
def test_cloud_start_preparation_failure_never_starts_daemon(phase, code):
    successful = FakeRunner()
    def handler(argv, **kwargs):
        if any(str(part).endswith(phase) for part in argv):
            return subprocess.CompletedProcess(argv, 0, stdout=ok_line({}) + "\n", stderr="")
        return successful(argv, **kwargs)
    runner = FakeRunner(handler)
    with pytest.raises(BridgeError) as caught:
        make_bridge(runner).start(provider="chatgpt", model="m", base_url="", api_key=KEY)
    assert caught.value.code == code
    assert not any("start" in call for call, _ in runner.calls)
    assert all(KEY not in str(part) for call, _ in runner.calls for part in call)
    assert KEY not in str(caught.value)
