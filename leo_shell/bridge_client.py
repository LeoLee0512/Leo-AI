"""WSL bridge client for Leo AI Studio's Windows shell.

The client shells out to ``wsl.exe`` running ``bridge/leo_bridge.sh`` and
speaks the bridge's single-line JSON protocol.  Secrets are only ever passed
through the child process environment (advertised via ``WSLENV``), never
through command line arguments, and registered secret values are scrubbed
from captured output before it is logged or re-raised.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a hard import cycle.
    from .paths import AppPaths

__all__ = ["BridgeError", "WslBridge", "windows_path_to_wsl"]


_CREATE_NO_WINDOW = 0x08000000
_SW_HIDE = 0
_MAX_MANIFEST_BYTES = 1024 * 1024
_DRIVE_PATTERN = re.compile(r"^([A-Za-z]):[\\/]")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{7,64}$")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SENSITIVE_ARGUMENT_NAMES = frozenset(
    {
        "--api-key",
        "--api_key",
        "--password",
        "--secret",
        "--token",
    }
)


class BridgeError(RuntimeError):
    """A failure reported by the WSL bridge or by the local WSL plumbing."""

    def __init__(self, code: str, message: str, guidance: list[str] | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.guidance = list(guidance) if guidance else []


def windows_path_to_wsl(path: object) -> str:
    """Convert an absolute Windows path to its ``/mnt/<drive>/...`` form.

    Paths that are already POSIX absolute are returned unchanged.  Anything
    that cannot be resolved to a drive-anchored absolute path (for example a
    UNC share) raises ``BridgeError("INVALID_ARGUMENT")``.
    """

    text = str(path)
    if text.startswith("/"):
        return text
    match = _DRIVE_PATTERN.match(text)
    if match is None:
        try:
            text = str(Path(text).resolve())
        except OSError as exc:
            raise BridgeError("INVALID_ARGUMENT", f"Cannot resolve the path {text!r} for WSL.") from exc
        match = _DRIVE_PATTERN.match(text)
    if match is None:
        raise BridgeError("INVALID_ARGUMENT", f"The path {str(path)!r} has no WSL /mnt equivalent.")
    drive = match.group(1).lower()
    rest = text[2:].lstrip("\\/").replace("\\", "/")
    return f"/mnt/{drive}/{rest}" if rest else f"/mnt/{drive}"


class WslBridge:
    """Thin, secret-safe client for the Linux-side ``leo_bridge.sh``."""

    def __init__(
        self,
        paths: "AppPaths",
        *,
        distro: str | None = None,
        runner: Callable[..., Any] = subprocess.run,
        logger: logging.Logger | None = None,
        local_session_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._paths = paths
        self._distro = distro
        self._runner = runner
        self._logger = logger or logging.getLogger("leo_shell.bridge")
        self._secret_values: list[str] = []
        self._local_session_factory = local_session_factory
        self._local_session: Any = None
        self._local_base_url: str | None = None
        self._local_configuration: tuple[str, str, int] | None = None

    # ------------------------------------------------------------------ API

    def preflight(self) -> dict:
        # Update/visual-preview payloads can omit the installed WSL launcher.
        # Detect this before spawning WSL; it is not a model or credential error.
        if not Path(self._paths.bridge_script).is_file():
            raise BridgeError(
                "APP_PACKAGE_INCOMPLETE",
                "The installed workbench launcher is missing.",
                ["Open the complete Leo AI installation, or restore its runtime files."],
            )
        return self._run("preflight", timeout=60)

    def status(self) -> dict:
        return self._run("status", timeout=30)

    def install(self, source_archive: Path | None = None) -> dict:
        """Run install-runtime + stage-source + activate-source in order."""

        manifest = self._load_runtime_manifest()
        archive = self._require_text(manifest, "archive", "RUNTIME_METADATA_INVALID")
        digest = self._require_text(manifest, "sha256", "RUNTIME_METADATA_INVALID")
        version = self._require_text(manifest, "version", "RUNTIME_METADATA_INVALID")
        if not _SHA256_PATTERN.match(digest):
            raise BridgeError("RUNTIME_METADATA_INVALID", "The runtime archive checksum is invalid.")
        if not _VERSION_PATTERN.match(version) or version.startswith("."):
            raise BridgeError("RUNTIME_METADATA_INVALID", "The runtime version identifier is invalid.")
        upstream = manifest.get("upstream")
        revision = upstream.get("revision") if isinstance(upstream, dict) else None
        if not isinstance(revision, str) or not _REVISION_PATTERN.match(revision):
            raise BridgeError("SOURCE_METADATA_INVALID", "The source revision is invalid.")

        runtime_tar = Path(self._paths.runtime_dir) / archive
        if source_archive is None:
            source_archive = Path(self._paths.user) / "cache" / f"source-{revision}.tar"
        source_archive = Path(source_archive)
        if not source_archive.is_file():
            raise BridgeError(
                "SOURCE_ARCHIVE_UNAVAILABLE",
                "The OpenAI4S source archive is missing from the user cache.",
                ["Restore the Leo AI Studio package cache and retry."],
            )
        source_digest = self._sha256_file(source_archive)

        runtime_result = self._run(
            "install-runtime",
            [windows_path_to_wsl(runtime_tar), digest, version],
            timeout=600,
        )
        source_result = self._run(
            "stage-source",
            [windows_path_to_wsl(source_archive), source_digest, revision],
            timeout=600,
        )
        activate_result = self._run("activate-source", [revision], timeout=600)
        return {"runtime": runtime_result, "source": source_result, "activate": activate_result}

    def start(self, *, provider: str, model: str, base_url: str, api_key: str | None) -> dict:
        provider = self._require_value("provider", provider)
        model = self._require_value("model", model)
        base_url = self._require_value("base_url", base_url, allow_empty=True)
        self._reject_sensitive_argv(["start", provider, model, base_url])
        if provider == "local-llama":
            return self._start_local(model=model, base_url=base_url, api_key=api_key)
        extra_env = self._connection_env(browse=not bool(api_key))
        if api_key:
            self._register_secret(api_key)
            provider_env = "OPENAI4S_" + re.sub(r"[^A-Z0-9]+", "_", provider.upper()) + "_API_KEY"
            extra_env["OPENAI4S_LLM_API_KEY"] = api_key
            extra_env[provider_env] = api_key
        # The coordinator already skips identical cloud fingerprints. Every
        # actual start here must apply this call's environment, including a new
        # key or an explicit keyless connection to the same model and endpoint.
        self.stop()
        self._prepare_identity()
        self._prepare_runtime_compatibility()
        self._prepare_example_persistence()
        self._select_native_model(
            provider=provider, model=model, base_url=base_url, explicit_key=bool(api_key),
            browse=not bool(api_key),
        )
        return self._run("start", [provider, model, base_url], timeout=120, extra_env=extra_env)

    def _start_local(self, *, model: str, base_url: str, api_key: str | None) -> dict:
        from .local_model import LOCAL_BASE_URL, LOCAL_MODEL, LocalModelSession

        if model != LOCAL_MODEL or base_url != LOCAL_BASE_URL or api_key:
            raise BridgeError(
                "LOCAL_MODEL_CONFIG_INVALID",
                "本地模型使用固定的本机地址与模型名称，无需 API Key。",
            )
        if self._local_session is None:
            factory = self._local_session_factory or LocalModelSession
            self._local_session = factory(self._paths, self._distro)
        try:
            relay_url, relay_token = self._local_session.start()
            self._register_secret(relay_token)
            # A new relay receives a new loopback port.  The detached daemon
            # must not retain an earlier endpoint (including an old cloud one).
            configuration = (relay_url, relay_token, self._local_session.context_size)
            restarting = self._local_configuration != configuration
            if restarting:
                self._run("stop", timeout=60)
                self._prepare_identity()
                self._prepare_runtime_compatibility()
                self._prepare_example_persistence()
            selection = self._select_native_model(
                provider="chatgpt", model=LOCAL_MODEL, base_url=relay_url, local=True,
            )
            if selection.get("restart_required") and not restarting:
                self._run("stop", timeout=60)
                self._prepare_identity()
                self._prepare_runtime_compatibility()
                self._prepare_example_persistence()
            extra_env = {
                "LEO_STUDIO_BROWSE_ONLY": "0",
                "OPENAI4S_LLM_API_KEY": relay_token,
                "OPENAI4S_CHATGPT_API_KEY": relay_token,
                "OPENAI4S_LLM_PROVIDER": "chatgpt",
                "OPENAI4S_LLM_BASE_URL": relay_url,
                "OPENAI4S_CHATGPT_BASE_URL": relay_url,
                "OPENAI4S_LLM_MODEL": LOCAL_MODEL,
                "OPENAI4S_CHATGPT_MODEL": LOCAL_MODEL,
                "OPENAI4S_LLM_MAX_TOKENS": "512",
                "OPENAI4S_LLM_REASONING_EFFORT": "none",
                "OPENAI4S_CONTEXT_WINDOW": str(self._local_session.context_size),
            }
            result = self._run("start", ["chatgpt", LOCAL_MODEL, relay_url], timeout=120, extra_env=extra_env)
            self._local_base_url = relay_url
            self._local_configuration = configuration
            return result
        except Exception:
            self._local_base_url = None
            self._local_configuration = None
            try:
                self._run("stop", timeout=60)
            except Exception:
                self._logger.warning("local model daemon cleanup failed")
            try:
                self._local_session.stop()
            except Exception:
                self._logger.warning("local model session cleanup failed")
            raise

    def _prepare_identity(self) -> dict:
        # The daemon imports this prompt once. Apply the bounded overlay after
        # stop and before start so new and resumed sessions see Leo's identity.
        resource = Path(self._paths.bridge_script).with_name("leo_identity.py")
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        argv += ["-e", "/usr/bin/python3", "-I", windows_path_to_wsl(resource), "apply"]
        result = self._execute("identity", argv, timeout=30)
        if result.get("identity") != "Leo AI" or result.get("version") != 1 or result.get("applied") is not True:
            raise BridgeError("IDENTITY_PREPARATION_FAILED", "Leo AI identity could not be prepared.")
        return result

    def _prepare_runtime_compatibility(self) -> dict:
        resource = Path(self._paths.bridge_script).with_name("leo_runtime_compat.py")
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        argv += ["-e", "/usr/bin/python3", "-I", windows_path_to_wsl(resource), "apply"]
        result = self._execute("runtime-compatibility", argv, timeout=30)
        if (result.get("compatibility") != "submit-output" or result.get("version") != 1
                or result.get("applied") is not True or result.get("browse_guard") is not True):
            raise BridgeError("RUNTIME_COMPAT_PREPARATION_FAILED", "Leo AI runtime compatibility could not be prepared.")
        return result

    def _prepare_example_persistence(self) -> dict:
        # Gateway changes must be verified as one composed source, including
        # Example deletion, immutable model binding and thought projections.
        resource = Path(self._paths.bridge_script).with_name("leo_runtime_features.py")
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        argv += ["-e", "/usr/bin/python3", "-I", windows_path_to_wsl(resource), "apply"]
        result = self._execute("example-persistence", argv, timeout=30)
        if (result.get("version") != 1 or result.get("example_persistence") is not True
                or result.get("conversation_runtime") is not True or result.get("applied") is not True):
            raise BridgeError("CONVERSATION_RUNTIME_PREPARATION_FAILED", "Leo AI conversation runtime and deletion persistence could not be verified.")
        return result

    def _select_native_model(
        self, *, provider: str, model: str, base_url: str,
        local: bool = False, explicit_key: bool = False, browse: bool = False,
    ) -> dict:
        # This helper never receives a credential. It preserves the original
        # global override in the same protected settings table, then lets the
        # daemon environment carry this connection's key or private relay token.
        resource = Path(self._paths.bridge_script).with_name("leo_model_selection.py")
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        argv += ["-e", "/usr/bin/python3", "-I", windows_path_to_wsl(resource), "select",
                 "--provider", provider, "--model", model]
        if base_url:
            argv += ["--base-url", base_url]
        if local:
            argv.append("--local")
        if explicit_key:
            argv.append("--explicit-key")
        if browse:
            argv.append("--browse")
        result = self._execute("model-selection", argv, timeout=30)
        if (result.get("global_key_override_empty") is not True
                or type(result.get("restart_required")) is not bool
                or type(result.get("active_profile_empty")) is not bool
                or ((local or explicit_key or browse) and result.get("active_profile_empty") is not True)):
            raise BridgeError("LOCAL_SELECTION_FAILED", "本机模型选择未能安全同步，原始设置已保留。")
        return result

    def client_url(self) -> str:
        data = self._run("url", timeout=30)
        url = data.get("client_url")
        if not self._is_valid_client_url(url):
            raise BridgeError("CLIENT_URL_INVALID", "OpenAI4S returned an untrusted local sign-in URL.")
        return url

    def stop(self) -> dict:
        try:
            return self._run("stop", timeout=60)
        finally:
            self._local_base_url = None
            self._local_configuration = None
            if self._local_session is not None:
                self._local_session.stop()

    def doctor(self) -> dict:
        return self._run("doctor", timeout=120)

    # ------------------------------------------------------------- plumbing

    def _run(
        self,
        action: str,
        args: list[str] | tuple[str, ...] = (),
        *,
        timeout: float,
        extra_env: dict[str, str] | None = None,
    ) -> dict:
        argv = self._build_argv(action, args)
        return self._execute(action, argv, timeout=timeout, extra_env=extra_env)

    def _execute(
        self, action: str, argv: list[str], *, timeout: float,
        extra_env: dict[str, str] | None = None,
    ) -> dict:
        self._reject_sensitive_argv(argv)
        kwargs: dict[str, Any] = {
            "shell": False,
            "capture_output": True,
            "timeout": timeout,
            "env": self._build_env(extra_env),
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "creationflags": self._creationflags(),
        }
        startupinfo = self._startupinfo()
        if startupinfo is not None:
            kwargs["startupinfo"] = startupinfo

        started = time.monotonic()
        try:
            completed = self._runner(argv, **kwargs)
        except FileNotFoundError as exc:
            raise BridgeError(
                "WSL_UNAVAILABLE",
                "wsl.exe was not found; WSL2 is required to run Leo AI Studio.",
                ["Install WSL2 with an Ubuntu 24.04 distribution, then retry."],
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise BridgeError(
                "WSL_TIMEOUT",
                f"The WSL bridge action '{action}' did not finish within {int(timeout)} seconds.",
            ) from exc
        elapsed_ms = int((time.monotonic() - started) * 1000)

        try:
            data = self._parse_output(completed, action)
        except BridgeError as exc:
            self._logger.warning(
                "bridge action=%s failed code=%s elapsed_ms=%d", action, exc.code, elapsed_ms
            )
            raise
        self._logger.info("bridge action=%s ok elapsed_ms=%d", action, elapsed_ms)
        return data

    def _build_argv(self, action: str, args: list[str] | tuple[str, ...]) -> list[str]:
        argv = ["wsl.exe"]
        if self._distro:
            argv += ["-d", self._distro]
        argv += ["-e", "/bin/sh", windows_path_to_wsl(self._paths.bridge_script), action]
        argv += [str(arg) for arg in args]
        return argv

    @staticmethod
    def _reject_sensitive_argv(argv: list[str]) -> None:
        for argument in argv[1:]:
            name = argument.split("=", 1)[0].casefold()
            if name in _SENSITIVE_ARGUMENT_NAMES:
                raise BridgeError(
                    "INVALID_ARGUMENT",
                    "Refusing to pass a sensitive option name on the WSL command line.",
                )

    @staticmethod
    def _connection_env(*, browse: bool) -> dict[str, str]:
        env = {"LEO_STUDIO_BROWSE_ONLY": "1" if browse else "0"}
        if browse:
            # These empty values override both Windows inheritance and WSLENV.
            # The runtime guard is still required: old sessions may carry keys.
            names = {
                "OPENAI4S_LLM_API_KEY", "OPENAI4S_CHATGPT_API_KEY",
                "OPENAI4S_ARK_API_KEY", "OPENAI4S_CLAUDE_API_KEY",
                "OPENAI4S_GEMINI_API_KEY", "ARK_API_KEY", "DOUBAO_API_KEY",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_API_KEY",
                "GEMINI_API_KEY", "GOOGLE_API_KEY",
            }
            names.update(name for name in os.environ if name.startswith("OPENAI4S_") and name.endswith("API_KEY"))
            env.update({name: "" for name in sorted(names)})
            env["OPENAI4S_SKIP_DOTENV"] = "1"
        return env

    @staticmethod
    def _build_env(extra_env: dict[str, str] | None) -> dict[str, str]:
        env = dict(os.environ)
        if extra_env:
            env.update(extra_env)
            advertised = [part for part in env.get("WSLENV", "").split(":")
                          if part and part.split("/", 1)[0] not in extra_env]
            for name in extra_env:
                if name not in advertised:
                    advertised.append(name)
            env["WSLENV"] = ":".join(advertised)
        return env

    @staticmethod
    def _creationflags() -> int:
        return getattr(subprocess, "CREATE_NO_WINDOW", _CREATE_NO_WINDOW)

    @staticmethod
    def _startupinfo() -> Any:
        startupinfo_type = getattr(subprocess, "STARTUPINFO", None)
        if startupinfo_type is None:  # non-Windows host; only reachable from tests.
            return None
        info = startupinfo_type()
        info.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
        info.wShowWindow = _SW_HIDE
        return info

    # ---------------------------------------------------------------- output

    def _parse_output(self, completed: Any, action: str) -> dict:
        stdout = self._coerce_text(getattr(completed, "stdout", ""))
        stderr = self._coerce_text(getattr(completed, "stderr", ""))
        payload = self._extract_json(stdout, stderr, action)
        if payload.get("ok") is True:
            data = payload.get("data")
            if data is None:
                return {}
            if not isinstance(data, dict):
                raise BridgeError(
                    "BRIDGE_OUTPUT_INVALID",
                    f"The WSL bridge action '{action}' returned a non-object data payload.",
                )
            return data
        error = payload.get("error")
        if not isinstance(error, dict):
            error = {}
        code = str(error.get("code") or "BRIDGE_UNKNOWN")
        message = self._redact(str(error.get("message") or "The WSL bridge reported a failure."))
        raw_guidance = error.get("guidance")
        guidance = (
            [self._redact(str(item)) for item in raw_guidance] if isinstance(raw_guidance, list) else []
        )
        raise BridgeError(code, message, guidance)

    def _extract_json(self, stdout: str, stderr: str, action: str) -> dict:
        """The payload is the last non-empty stdout line; tolerate noise lines."""

        stdout_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        stderr_lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        candidates: list[str] = []
        if stdout_lines:
            candidates.append(stdout_lines[-1])
            candidates.extend(reversed(stdout_lines[:-1]))
        candidates.extend(reversed(stderr_lines))
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except ValueError:
                continue
            if isinstance(parsed, dict) and "ok" in parsed:
                return parsed
        snippet = self._redact((stdout_lines[-1] if stdout_lines else stderr_lines[-1] if stderr_lines else "")[:200])
        raise BridgeError(
            "BRIDGE_OUTPUT_INVALID",
            f"The WSL bridge action '{action}' did not return a JSON payload: {snippet!r}",
        )

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    # --------------------------------------------------------------- secrets

    def _register_secret(self, value: str) -> None:
        if value and value not in self._secret_values:
            self._secret_values.append(value)

    def _redact(self, text: str) -> str:
        for secret in self._secret_values:
            if secret:
                text = text.replace(secret, "<redacted>")
        return text

    # ---------------------------------------------------------------- files

    def _load_runtime_manifest(self) -> dict:
        manifest_path = Path(self._paths.runtime_dir) / "runtime-manifest.json"
        try:
            if manifest_path.stat().st_size > _MAX_MANIFEST_BYTES:
                raise BridgeError("RUNTIME_METADATA_INVALID", "The runtime manifest is too large.")
            raw = manifest_path.read_text(encoding="utf-8-sig")
            manifest = json.loads(raw)
        except BridgeError:
            raise
        except (OSError, ValueError) as exc:
            raise BridgeError(
                "RUNTIME_METADATA_INVALID", "The runtime manifest is missing or unreadable."
            ) from exc
        if not isinstance(manifest, dict):
            raise BridgeError("RUNTIME_METADATA_INVALID", "The runtime manifest is not a JSON object.")
        return manifest

    @staticmethod
    def _require_text(manifest: dict, key: str, code: str) -> str:
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            raise BridgeError(code, f"The runtime manifest is missing '{key}'.")
        return value

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        try:
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError as exc:
            raise BridgeError("SOURCE_ARCHIVE_UNAVAILABLE", f"The source archive {path} is unreadable.") from exc
        return digest.hexdigest()

    # -------------------------------------------------------------- helpers

    @staticmethod
    def _require_value(name: str, value: object, *, allow_empty: bool = False) -> str:
        if not isinstance(value, str) or (not allow_empty and not value):
            raise BridgeError("INVALID_ARGUMENT", f"The bridge argument '{name}' must be a non-empty string.")
        if any(ord(char) < 32 for char in value):
            raise BridgeError("INVALID_ARGUMENT", f"The bridge argument '{name}' contains control characters.")
        return value

    @staticmethod
    def _is_valid_client_url(url: object) -> bool:
        if not isinstance(url, str) or not url or any(ord(char) < 32 for char in url):
            return False
        try:
            from urllib.parse import urlsplit

            parts = urlsplit(url)
            return (
                parts.scheme == "http"
                and parts.hostname in {"127.0.0.1", "::1", "localhost"}
                and parts.port == 8760
                and parts.username is None
                and parts.password is None
                and not parts.fragment
            )
        except ValueError:
            return False
