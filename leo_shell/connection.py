"""Serial connection coordinator for Leo AI Studio's Windows shell.

All WSL connection work (preflight, install, start, URL retrieval, navigation)
runs on a single daemon worker thread.  Every submit bumps a generation
counter; a stale generation checks ``is_current`` before each stage and exits
quietly, so a newer save always supersedes an in-flight connection attempt.
Navigation can be gated on a front-end acknowledgement, but an ack timeout
never deadlocks the shell: the worker navigates anyway and logs ACK_TIMEOUT.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Any, Protocol

from .bridge_client import BridgeError

try:  # settings_store ships in a parallel work stream; tolerate its absence.
    from .settings_store import SettingsInvalid
except Exception:  # pragma: no cover - exercised only when the module is absent.
    SettingsInvalid = None  # type: ignore[assignment]

__all__ = [
    "PUBLIC_APP_CLOSING",
    "PUBLIC_SETTINGS_INVALID",
    "PUBLIC_SETTINGS_UNAVAILABLE",
    "PUBLIC_CONNECTION_FAILED",
    "PUBLIC_RECOVERY_REQUIRED",
    "UiSink",
    "ConnectionCoordinator",
]


PUBLIC_APP_CLOSING = "APP_CLOSING"
PUBLIC_SETTINGS_INVALID = "MODEL_SETTINGS_INVALID"
PUBLIC_SETTINGS_UNAVAILABLE = "MODEL_SETTINGS_UNAVAILABLE"
PUBLIC_CONNECTION_FAILED = "MODEL_CONNECTION_FAILED"
PUBLIC_RECOVERY_REQUIRED = "MODEL_SETTINGS_RECOVERY_REQUIRED"


class UiSink(Protocol):
    """The UI surface the coordinator reports to."""

    def publish_status(self, message: str, *, error: bool = False) -> Any: ...

    def navigate(self, url: str) -> Any: ...

    def open_settings(self) -> Any: ...


def _key_marker(api_key: str | None) -> str:
    """Return a stable, non-reversible marker for *api_key*.

    Used only to tell one credential from another inside the restart
    fingerprint.  The key itself must never be stored on the coordinator, and a
    digest keeps the comparison working without holding the secret: ``""`` for
    keyless, otherwise a truncated SHA-256 of the key.
    """

    if not api_key:
        return "nokey"
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    return digest[:16]


class _GenerationStale(Exception):
    """Internal marker: this generation was superseded while working."""


class ConnectionCoordinator:
    """One serial worker plus a single pending slot, guarded by a Condition."""

    def __init__(
        self,
        bridge: Any,
        sink: UiSink,
        logger: logging.Logger | None = None,
        *,
        ack_timeout: float = 15.0,
    ) -> None:
        self._bridge = bridge
        self._sink = sink
        self._logger = logger or logging.getLogger("leo_shell.connection")
        self._ack_timeout = max(0.0, float(ack_timeout))
        self._cond = threading.Condition()
        self._navigation_lock = threading.Lock()
        self._io_lock = threading.Lock()  # serializes physical start/stop calls.
        self._generation = 0
        self._pending: tuple[int, Any, str | None, bool] | None = None
        self._acked: set[int] = set()
        self._closing = False
        self._fingerprint: str | None = None
        self._runtime_state = {
            "mode": "unconfigured", "status": "idle", "has_key": False,
            "local_ready": False,
        }
        self._physical_stop_requested = False
        self._stop_thread: threading.Thread | None = None
        self._worker = threading.Thread(
            target=self._worker_loop, name="leo-shell-connect", daemon=True
        )
        self._worker.start()

    # ------------------------------------------------------------------ API

    def submit(self, profile: Any, api_key: str | None, *, requires_ack: bool) -> dict:
        """Queue a connection attempt; returns immediately with a request id."""

        with self._cond:
            if self._closing:
                return {"ok": False, "pending": False, "message": PUBLIC_APP_CLOSING}
            self._generation += 1
            request_id = self._generation
            mode = getattr(profile, "entry_mode", None)
            if mode not in {"unconfigured", "keyless"}:
                mode = "local" if getattr(profile, "provider", None) == "local-llama" else ("cloud" if api_key else "keyless")
            self._runtime_state = {
                "mode": mode, "status": "connecting", "has_key": bool(api_key),
                "local_ready": False,
            }
            self._pending = (request_id, profile, api_key, bool(requires_ack))
            self._cond.notify_all()
        self._logger.info("submit request=%d requires_ack=%s", request_id, bool(requires_ack))
        return {"ok": True, "pending": True, "request_id": request_id}

    def runtime_state(self) -> dict:
        """Report this process's connection receipt, never stored credentials."""
        with self._cond:
            return dict(self._runtime_state)

    def cancel_pending(self) -> None:
        """Cancel late navigation without closing the worker or the daemon."""
        with self._navigation_lock:
            with self._cond:
                self._generation += 1
                self._pending = None
                self._acked.clear()
                if self._runtime_state["status"] == "connecting":
                    self._runtime_state.update(status="idle", has_key=False, local_ready=False)
                self._cond.notify_all()

    def acknowledge(self, request_id: int) -> None:
        """Record a front-end acknowledgement; safe to call early or late."""

        if not isinstance(request_id, int) or isinstance(request_id, bool) or request_id <= 0:
            return
        with self._cond:
            self._acked.add(request_id)
            self._cond.notify_all()

    def close(self, *, wait_timeout: float = 1.0, stop_daemon: bool = True) -> None:
        """Invalidate in-flight work, then arrange exactly one physical stop."""

        with self._cond:
            self._closing = True
            self._generation += 1  # invalidate the current generation.
            self._pending = None
            self._cond.notify_all()
        if threading.current_thread() is not self._worker and self._worker.is_alive():
            self._worker.join(timeout=max(0.0, float(wait_timeout)))
        if stop_daemon:
            self._request_physical_stop()

    # --------------------------------------------------------------- worker

    def _worker_loop(self) -> None:
        while True:
            with self._cond:
                while self._pending is None and not self._closing:
                    self._cond.wait()
                if self._closing:
                    self._pending = None
                    return
                generation, profile, api_key, requires_ack = self._pending
                self._pending = None
            try:
                self._connect(generation, profile, api_key, requires_ack)
            except _GenerationStale:
                self._logger.info("request=%d superseded; abandoning quietly", generation)
            except BridgeError as exc:
                code = "APP_PACKAGE_INCOMPLETE" if exc.code == "APP_PACKAGE_INCOMPLETE" else PUBLIC_CONNECTION_FAILED
                self._fail(generation, code, exc)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a public code.
                code = PUBLIC_CONNECTION_FAILED
                if SettingsInvalid is not None and isinstance(exc, SettingsInvalid):
                    code = PUBLIC_SETTINGS_INVALID
                self._fail(generation, code, exc)
            finally:
                # The API key must not outlive the start attempt that used it.
                api_key = None
                profile = None

    def _connect(self, generation: int, profile: Any, api_key: str | None, requires_ack: bool) -> None:
        self._stage_call(generation, "PREFLIGHT", self._bridge.preflight)
        status = self._stage_call(generation, "STATUS", self._bridge.status) or {}
        if status.get("state") == "not-installed":
            self._stage_call(generation, "INSTALL", self._bridge.install)
            status = self._stage_call(generation, "STATUS", self._bridge.status) or {}

        provider = str(getattr(profile, "provider", "") or "")
        model = str(getattr(profile, "model", "") or "")
        base_url = str(getattr(profile, "base_url", "") or "")
        # The credential is part of what the daemon was started with, so it has to
        # be part of the identity that decides whether a restart is needed.  Adding
        # a key to an existing profile changes nothing else, so without this the
        # START stage is skipped as "same-fingerprint" and the daemon keeps running
        # with the old credential -- the key is saved but never takes effect.
        # Only a digest is kept: enough to notice a change, useless if it leaks.
        fingerprint = f"{provider}|{model}|{base_url}|{_key_marker(api_key)}"
        running = bool(status.get("running")) or status.get("state") == "running"

        key = api_key
        try:
            if running and self._fingerprint == fingerprint and provider != "local-llama":
                self._logger.info("stage=START request=%d skipped reason=same-fingerprint", generation)
            else:
                # A local model can be stopped outside Leo AI while its WSL
                # daemon stays alive.  Revalidate it on every reconnect; the
                # bridge keeps a healthy existing relay and model in place.
                if running and self._fingerprint != fingerprint:
                    self._stage_call(generation, "STOP", self._locked_stop)
                def _start() -> Any:
                    with self._io_lock:
                        # Closing may win this lock after the stage checkpoint.
                        # A completed shutdown must never be followed by a start.
                        if not self._is_current(generation):
                            raise _GenerationStale()
                        return self._bridge.start(
                            provider=provider, model=model, base_url=base_url, api_key=key
                        )
                self._stage_call(generation, "START", _start)
                self._fingerprint = fingerprint
        finally:
            key = None
            api_key = None

        url = self._stage_call(generation, "URL", self._bridge.client_url)
        self._checkpoint(generation, "NAVIGATE")
        if requires_ack:
            self._wait_for_ack(generation)
        # Serialize cancellation with navigation, but release the condition
        # before calling UI code: injection may read runtime_state while holding
        # its own window lock. No condition/window lock inversion is allowed.
        with self._navigation_lock:
            with self._cond:
                if not self._is_current_locked(generation):
                    raise _GenerationStale()
                self._runtime_state.update(
                    status="ready", local_ready=provider == "local-llama",
                )
            if self._sink.navigate(url) is False:
                raise RuntimeError("BACKEND_NAVIGATION_FAILED")
        self._logger.info("stage=NAVIGATE request=%d done", generation)

    def _wait_for_ack(self, generation: int) -> None:
        with self._cond:
            self._cond.wait_for(
                lambda: generation in self._acked or not self._is_current_locked(generation),
                timeout=self._ack_timeout,
            )
            acknowledged = generation in self._acked
            current = self._is_current_locked(generation)
        if acknowledged:
            self._logger.info("stage=ACK request=%d received", generation)
        elif current:
            # Never deadlock the shell: navigate anyway after the grace period.
            self._logger.warning(
                "ACK_TIMEOUT request=%d timeout=%.3fs; navigating without ack",
                generation,
                self._ack_timeout,
            )

    # -------------------------------------------------------------- failures

    def _fail(self, generation: int, public_code: str, exc: BaseException) -> None:
        with self._cond:
            if not self._is_current_locked(generation):
                return  # Includes APP_CLOSING: stay silent while shutting down.
            self._runtime_state.update(status="failed", local_ready=False)
        precise = exc.code if isinstance(exc, BridgeError) else type(exc).__name__
        self._logger.warning(
            "request=%d failed public=%s precise=%s", generation, public_code, precise
        )
        try:
            self._sink.publish_status(public_code, error=True)
        except Exception:  # noqa: BLE001 - the sink must never break the worker.
            self._logger.exception("publish_status failed request=%d", generation)
        if public_code == "APP_PACKAGE_INCOMPLETE":
            # Preflight did not touch a daemon. Do not send the user to model
            # settings or try to stop a runtime through the missing launcher.
            return
        try:
            self._sink.open_settings()
        except Exception:  # noqa: BLE001
            self._logger.exception("open_settings failed request=%d", generation)
        try:
            with self._io_lock:
                self._bridge.stop()
        except Exception:  # noqa: BLE001 - best-effort cleanup only.
            self._logger.warning("cleanup stop failed request=%d", generation, exc_info=True)

    # --------------------------------------------------------------- helpers

    def _stage_call(self, generation: int, stage: str, call: Any) -> Any:
        self._checkpoint(generation, stage)
        started = time.monotonic()
        result = call()
        self._logger.info(
            "stage=%s request=%d elapsed_ms=%d",
            stage,
            generation,
            int((time.monotonic() - started) * 1000),
        )
        return result

    def _checkpoint(self, generation: int, stage: str) -> None:
        if not self._is_current(generation):
            raise _GenerationStale()
        self._logger.info("stage=%s request=%d begin", stage, generation)

    def _locked_stop(self) -> Any:
        with self._io_lock:
            return self._bridge.stop()

    def _is_current_locked(self, generation: int) -> bool:
        return not self._closing and generation == self._generation

    def _is_current(self, generation: int) -> bool:
        with self._cond:
            return self._is_current_locked(generation)

    def _request_physical_stop(self) -> None:
        with self._cond:
            if self._physical_stop_requested:
                return
            self._physical_stop_requested = True
        thread = threading.Thread(
            target=self._physical_stop, name="leo-shell-stop", daemon=False
        )
        self._stop_thread = thread
        thread.start()

    def _physical_stop(self) -> None:
        # _io_lock queues this stop behind any in-flight start call.
        with self._io_lock:
            try:
                self._bridge.stop()
                self._logger.info("physical daemon stop completed")
            except Exception:  # noqa: BLE001 - shutdown must not raise.
                self._logger.warning("physical daemon stop failed", exc_info=True)
