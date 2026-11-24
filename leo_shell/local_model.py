"""Own a Windows llama.cpp session and a private WSL loopback relay.

The model project keeps its own lifecycle scripts.  We reuse their identity
checks and mutex instead of killing by process name or by a listening port.
Only a model whose launcher is this session's PowerShell child is released.
"""

from __future__ import annotations

import base64
import json
import os
import queue
import secrets
import stat
import subprocess
import threading
from pathlib import Path
from typing import Any
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

from .bridge_client import BridgeError, WslBridge, windows_path_to_wsl

LOCAL_MODEL = "local-qwen3-4b"
LOCAL_BASE_URL = "http://127.0.0.1:8080/v1"
_MAX_JSON = 64 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _ps_string(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _read_json(path: Path) -> dict:
    try:
        with path.open("rb") as stream:
            raw = stream.read(_MAX_JSON + 1)
        if len(raw) > _MAX_JSON:
            raise ValueError("oversized config")
        value = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("not an object")
        return value
    except (OSError, UnicodeError, ValueError) as exc:
        raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型配置缺失或无法读取。") from exc


def _reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型路径不能包含符号链接或目录联接。")


def _within(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative or any(ord(c) < 32 for c in relative):
        raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型文件路径无效。")
    path = Path(relative)
    if path.is_absolute() or path.drive or path.anchor or ".." in path.parts:
        raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型文件必须位于项目目录内。")
    result = root / path
    _reject_links(result)
    if not result.is_file():
        raise BridgeError("LOCAL_MODEL_NOT_INSTALLED", "本地模型项目缺少必要文件，请先完成模型安装。")
    return result


class LocalModelSession:
    """Synchronous lifecycle used under the shell connection coordinator lock."""

    def __init__(self, paths: Any, distro: str | None = None) -> None:
        self._paths = paths
        self._distro = distro
        self._project: Path | None = None
        self._model_config: dict = {}
        self._owned_model: dict | None = None
        self._relay: Any = None
        self._relay_token: str | None = None
        self._base_url: str | None = None
        self.context_size = 4096

    def _load_config(self) -> None:
        root = Path(self._paths.root).absolute()
        setting = _read_json(Path(self._paths.user) / "local-model.json")
        location = setting.get("project_directory")
        if not isinstance(location, str) or not location.strip() or any(ord(c) < 32 for c in location):
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "请在本机 local-model.json 中配置模型项目目录。")
        candidate = Path(location)
        if location.startswith(("\\\\", "//")) or (candidate.drive and not candidate.is_absolute()):
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型项目必须位于本机磁盘。")
        project = Path(os.path.abspath(candidate if candidate.is_absolute() else root / candidate))
        _reject_links(project)
        from .paths import _drive_type
        if _drive_type(project.anchor) == 4:
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型项目不能位于网络驱动器。")
        config = _read_json(_within(project, "config/model.json"))
        if config.get("host") != "127.0.0.1" or config.get("port") != 8080 or config.get("alias") != LOCAL_MODEL:
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型必须使用 127.0.0.1:8080 和 local-qwen3-4b。")
        context_size = config.get("contextSize")
        if type(context_size) is not int or not 1024 <= context_size <= 32768:
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型上下文配置必须在 1024–32768 之间。")
        model_path = _within(project, config.get("modelFile"))
        executable = _within(project, config.get("executable"))
        if model_path.suffix.lower() != ".gguf" or executable.name.lower() != "llama-server.exe":
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型必须使用 GGUF 和 llama-server.exe。")
        models = list((project / "models").rglob("*.gguf"))
        if len(models) != 1 or models[0] != model_path:
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "本地模型项目必须仅包含配置指定的一个 GGUF 模型。")
        for script in ("scripts/common.ps1", "scripts/start.ps1", "scripts/stop.ps1"):
            _within(project, script)
        if self._project is not None and project != self._project and (self._relay or self._owned_model):
            raise BridgeError("LOCAL_MODEL_CONFIG_INVALID", "模型项目目录已变更，请先断开当前连接。")
        self._project = project
        self._model_config = config
        self.context_size = context_size

    @staticmethod
    def _powershell() -> str:
        return str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe")

    @staticmethod
    def _hidden() -> dict:
        options: dict[str, Any] = {"shell": False, "creationflags": WslBridge._creationflags(), "close_fds": True}
        info = WslBridge._startupinfo()
        if info is not None:
            options["startupinfo"] = info
        return options

    def _powershell_json(self, body: str) -> dict:
        assert self._project is not None
        script = (
            "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=New-Object Text.UTF8Encoding($false); "
            "try { . " + _ps_string(self._project / "scripts/common.ps1") + "; " + body +
            " } catch { [Console]::Out.WriteLine('{\"ok\":false}'); exit 1 }"
        )
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        try:
            result = subprocess.run(
                [self._powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, **self._hidden(),
            )
            payload = json.loads(result.stdout.strip())
            if result.returncode != 0 or not isinstance(payload, dict) or payload.get("ok") is not True:
                raise ValueError("identity check failed")
            return payload
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            raise BridgeError("LOCAL_MODEL_IDENTITY_INVALID", "无法核验本地模型进程身份，未更改其他进程。") from exc

    def _inspect_model(self) -> dict | None:
        result = self._powershell_json("""
            $c=Get-LocalLlmConfig; $s=Read-LocalLlmState;
            $p=$null; if ($null -ne $s) { $p=Get-LocalLlmTrackedProcess -State $s -Config $c };
            $listeners=@(Get-LocalLlmListeners -Port $c.port);
            if ($null -eq $p) {
                if ($listeners.Count -gt 0) { throw 'Port is owned by another process' };
                @{ok=$true; identity=$null} | ConvertTo-Json -Compress;
            } else {
                foreach ($listener in $listeners) {
                    if ($listener.OwningProcess -ne $p.Id -or $listener.LocalAddress -cne '127.0.0.1') { throw 'Listener owner mismatch' }
                };
                $parent=(Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $p.Id)).ParentProcessId;
                @{ok=$true; identity=@{processId=$s.processId; processStartTimeUtc=$s.processStartTimeUtc;
                  executablePath=$s.executablePath; parentProcessId=$parent; listening=($listeners.Count -gt 0)}} | ConvertTo-Json -Compress;
            }
        """)
        return result.get("identity")

    @staticmethod
    def _same_identity(first: dict | None, second: dict | None) -> bool:
        return bool(first and second and all(first.get(k) == second.get(k) for k in (
            "processId", "processStartTimeUtc", "executablePath"
        )))

    def _verify_health(self, identity: dict | None) -> None:
        if not identity or not identity.get("listening"):
            raise BridgeError("LOCAL_MODEL_NOT_READY", "本地模型尚未就绪，请重试连接。")
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        try:
            values = []
            for route in ("/health", "/v1/models"):
                with opener.open("http://127.0.0.1:8080" + route, timeout=5) as response:
                    raw = response.read(_MAX_JSON + 1)
                if len(raw) > _MAX_JSON:
                    raise ValueError("oversized response")
                values.append(json.loads(raw.decode("utf-8")))
            if values[0].get("status") != "ok" or [item.get("id") for item in values[1].get("data", [])] != [LOCAL_MODEL]:
                raise ValueError("wrong model")
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            raise BridgeError("LOCAL_MODEL_NOT_READY", "本地模型健康检查或模型身份检查失败。") from exc

    def _start_model(self) -> None:
        before = self._inspect_model()
        assert self._project is not None
        child = None
        try:
            # No stdio redirection here: the native server must not inherit a
            # Python capture pipe.  start.ps1 writes its bounded native log.
            child = subprocess.Popen(
                [self._powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(self._project / "scripts/start.ps1")],
                cwd=str(self._project), **self._hidden(),
            )
            returncode = child.wait(timeout=145)
        except subprocess.TimeoutExpired as exc:
            try:
                child.kill()
                child.wait(timeout=5)
            finally:
                self._claim_started_model(before, child.pid)
            raise BridgeError("LOCAL_MODEL_START_TIMEOUT", "本地模型启动超时，请查看模型项目的日志。") from exc
        except OSError as exc:
            if child is not None:
                self._claim_started_model(before, child.pid)
            raise BridgeError("LOCAL_MODEL_START_FAILED", "无法启动本地模型的 PowerShell 脚本。") from exc
        after = self._claim_started_model(before, child.pid)
        if returncode != 0:
            raise BridgeError("LOCAL_MODEL_START_FAILED", "本地模型启动失败，请查看模型项目的日志。")
        self._verify_health(after)

    def _claim_started_model(self, before: dict | None, launcher_pid: int) -> dict | None:
        after = self._inspect_model()
        if before is None and after and after.get("parentProcessId") == launcher_pid:
            self._owned_model = after
        elif self._owned_model and not self._same_identity(self._owned_model, after):
            self._owned_model = None
        return after

    def _start_relay(self) -> tuple[str, str]:
        relay_path = _within(Path(self._paths.root), "bridge/leo_local_relay.py")
        token = secrets.token_urlsafe(32)
        env = dict(os.environ)
        env["LEO_LOCAL_RELAY_TOKEN"] = token
        advertised = [part for part in env.get("WSLENV", "").split(":") if part and part.split("/")[0] != "LEO_LOCAL_RELAY_TOKEN"]
        env["WSLENV"] = ":".join(advertised + ["LEO_LOCAL_RELAY_TOKEN"])
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        argv += ["-e", "/usr/bin/python3", "-u", windows_path_to_wsl(relay_path), "--model-port", "8080", "--context-size", str(self.context_size)]
        try:
            self._relay = subprocess.Popen(
                argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=env, **self._hidden(),
            )
        except OSError as exc:
            raise BridgeError("LOCAL_RELAY_START_FAILED", "无法启动本机模型中继。") from exc
        received: queue.Queue = queue.Queue(maxsize=1)
        stream = self._relay.stdout

        def read_handshake() -> None:
            try:
                received.put(stream.readline(4097))
            except (OSError, ValueError):
                received.put(b"")

        threading.Thread(target=read_handshake, name="leo-local-relay-handshake", daemon=True).start()
        try:
            raw = received.get(timeout=40)
            payload = json.loads(raw.decode("utf-8"))
            port = payload.get("port")
            if len(raw) > 4096 or payload.get("ok") is not True or type(port) is not int or not 1024 <= port <= 65535 or self._relay.poll() is not None:
                raise ValueError("invalid handshake")
        except (queue.Empty, ValueError, UnicodeError, AttributeError) as exc:
            raise BridgeError("LOCAL_RELAY_START_FAILED", "本机模型中继未能完成启动握手。") from exc
        self._relay_token = token
        self._base_url = f"http://127.0.0.1:{port}/v1"
        return self._base_url, token

    def start(self) -> tuple[str, str]:
        try:
            previous_context = self.context_size
            self._load_config()
            self._start_model()
            if self._relay is not None and self._relay.poll() is None and previous_context == self.context_size:
                assert self._base_url and self._relay_token
                return self._base_url, self._relay_token
            self._stop_relay()
            return self._start_relay()
        except Exception:
            try:
                self.stop()
            except Exception:
                pass
            raise

    def _stop_relay(self) -> None:
        child, self._relay = self._relay, None
        self._relay_token = None
        self._base_url = None
        if child is None:
            return
        try:
            if child.stdin is not None:
                try:
                    child.stdin.close()
                except OSError:
                    pass  # An exited relay can already have broken its pipe.
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()  # Popen's own process handle, never a name/port lookup.
                child.wait(timeout=5)
        finally:
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass

    def _stop_owned_model(self) -> None:
        owned = self._owned_model
        if not owned:
            return
        assert self._project is not None
        expected = _ps_string(json.dumps({key: owned[key] for key in (
            "processId", "processStartTimeUtc", "executablePath"
        )}))
        # The .NET mutex is recursive on the same PowerShell thread.  Hold it
        # over the identity check and the existing stop script so a concurrent
        # restart cannot replace server-state.json between those operations.
        self._powershell_json("""
            $lock=Enter-LocalLlmLock;
            try {
                $expected=""" + expected + """ | ConvertFrom-Json;
                $c=Get-LocalLlmConfig -SkipFileChecks; $s=Read-LocalLlmState;
                if ($null -ne $s -and $s.processId -eq $expected.processId -and
                    $s.processStartTimeUtc -eq $expected.processStartTimeUtc -and
                    $s.executablePath -eq $expected.executablePath) {
                    $p=Get-LocalLlmTrackedProcess -State $s -Config $c;
                    if ($null -ne $p) {
                        & """ + _ps_string(self._project / "scripts/stop.ps1") + """ *> $null;
                        if ($LASTEXITCODE -ne 0) { throw 'Model stop failed' }
                    }
                };
                @{ok=$true} | ConvertTo-Json -Compress;
            } finally { $lock.ReleaseMutex(); $lock.Dispose() }
        """)
        self._owned_model = None

    def stop(self) -> None:
        try:
            self._stop_relay()
        finally:
            self._stop_owned_model()
