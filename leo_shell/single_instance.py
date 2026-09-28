"""Per-user single-instance coordination over a mutex plus a named pipe.

The first process claims a ``Local\\`` mutex and serves ``\\\\.\\pipe\\`` IPC;
later processes forward their CLI intent (settings/activate/update) to the
primary and exit.  The pipe is authenticated with a per-install authkey stored
DPAPI-protected at ``user/ipc.dpapi`` so only the same Windows user can drive
the primary instance.

Degradation rules: a successful :meth:`SingleInstance.claim` is enough to run
the app; listener setup or authkey failures are logged and never fatal.  All
Win32/DPAPI access is lazy, so importing this module is safe everywhere.
"""

from __future__ import annotations

import base64
import ctypes
import getpass
import hashlib
import logging
import secrets
import threading
import time
from ctypes import wintypes
from multiprocessing import AuthenticationError
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .paths import AppPaths

__all__ = ["ALLOWED_ACTIONS", "SingleInstance"]

ALLOWED_ACTIONS = frozenset({"settings", "activate", "update"})

_ERROR_ALREADY_EXISTS = 183
_IPC_ENTROPY = b"LeoAIStudio/IPC/v1"
_IPC_FILE_MAGIC = b"LEOIPC1\n"
_AUTHKEY_BYTES = 32
_RETRY_INTERVAL_SECONDS = 0.5
_FORWARD_TIMEOUT_SECONDS = 3.0
_LISTEN_BIND_TIMEOUT_SECONDS = 3.0


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


class SingleInstance:
    """Owns the per-user instance mutex and the authenticated IPC pipe."""

    def __init__(self, paths: AppPaths, logger: logging.Logger | None = None) -> None:
        self._paths = paths
        self._logger = (
            logger if logger is not None else logging.getLogger(__name__)
        )
        digest = hashlib.sha256(
            f"{Path(paths.root).resolve()}".casefold().encode("utf-8")
            + b"\x00"
            + getpass.getuser().casefold().encode("utf-8")
        ).hexdigest()[:24]
        self._mutex_name = f"Local\\LeoAIStudio-{digest}"
        self._pipe_address = rf"\\.\pipe\LeoAIStudio-{digest}"
        self._authkey_file = Path(paths.user) / "ipc.dpapi"
        self._mutex_handle: int | None = None
        self._listener: Listener | None = None
        self._thread: threading.Thread | None = None
        self._closed = threading.Event()

    def claim(self) -> bool:
        """Acquire the per-user mutex; False means another instance owns it."""

        if self._mutex_handle is not None:
            return True
        try:
            kernel32 = ctypes.windll.kernel32  # Windows-only, resolved lazily
            kernel32.CreateMutexW.argtypes = (wintypes.LPCWSTR, wintypes.BOOL, wintypes.LPCWSTR)
        except (AttributeError, OSError) as exc:
            self._logger.warning(
                "single-instance mutex unavailable, continuing without it: %s",
                type(exc).__name__,
            )
            return True
        handle = kernel32.CreateMutexW(None, False, self._mutex_name)
        if not handle:
            self._logger.warning(
                "single-instance mutex creation failed, continuing without it"
            )
            return True
        if ctypes.GetLastError() == _ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._mutex_handle = handle
        return True

    def forward(self, action: str) -> bool:
        """Send ``action`` to the primary instance; False when unreachable.

        The pipe can lag the mutex by a moment (primary still starting up, or
        the previous owner's pipe name lingering after close), so a brief
        retry window turns those races into a delivered activation instead of
        a silently lost double-click.
        """

        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"unsupported single-instance action: {action!r}")
        authkey = self._load_authkey()
        if authkey is None:
            return False
        deadline = time.monotonic() + _FORWARD_TIMEOUT_SECONDS
        attempt = 0
        while True:
            attempt += 1
            try:
                with Client(
                    self._pipe_address, family="AF_PIPE", authkey=authkey
                ) as connection:
                    connection.send({"action": action})
                return True
            except (AuthenticationError, ValueError) as exc:
                # Auth/contract problems will not heal with time.
                self._logger.warning(
                    "single-instance forward failed: %s", type(exc).__name__
                )
                return False
            except OSError as exc:
                if time.monotonic() >= deadline:
                    self._logger.warning(
                        "single-instance forward failed after %d attempts: %s",
                        attempt,
                        type(exc).__name__,
                    )
                    return False
                time.sleep(_RETRY_INTERVAL_SECONDS)

    def listen(self, handler: Callable[[str], None]) -> None:
        """Serve forwarded actions on a background thread (best effort)."""

        if self._listener is not None or self._thread is not None:
            return
        authkey = self._ensure_authkey()
        if authkey is None:
            self._logger.warning(
                "single-instance listener disabled: no IPC authkey available"
            )
            return
        try:
            self._listener = self._bind_listener(authkey)
        except OSError as exc:
            self._logger.warning(
                "single-instance listener unavailable: %s", type(exc).__name__
            )
            self._listener = None
            return
        self._thread = threading.Thread(
            target=self._serve,
            args=(handler,),
            name="leo-shell-ipc",
            daemon=True,
        )
        self._thread.start()

    def _bind_listener(self, authkey: bytes) -> Listener:
        """Create the pipe listener, tolerating a lingering previous pipe.

        Right after the previous instance closes, the same pipe name can still
        be tearing down; ``CreateNamedPipe`` then fails with ``PermissionError``
        for a short window.  Retry briefly before giving up.
        """

        deadline = time.monotonic() + _LISTEN_BIND_TIMEOUT_SECONDS
        while True:
            try:
                return Listener(self._pipe_address, family="AF_PIPE", authkey=authkey)
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(_RETRY_INTERVAL_SECONDS)

    def close(self) -> None:
        self._closed.set()
        listener, self._listener = self._listener, None
        if listener is not None:
            try:
                listener.close()
            except OSError:
                pass
        handle, self._mutex_handle = self._mutex_handle, None
        if handle is not None:
            try:
                ctypes.windll.kernel32.CloseHandle(handle)
            except (AttributeError, OSError):
                pass

    def _serve(self, handler: Callable[[str], None]) -> None:
        while not self._closed.is_set():
            try:
                connection = self._listener.accept() if self._listener else None
            except OSError:
                if self._closed.is_set():
                    return
                continue
            if connection is None:
                return
            try:
                with connection:
                    try:
                        message = connection.recv()
                    except (EOFError, OSError):
                        continue
            except OSError:
                continue
            action = message.get("action") if isinstance(message, dict) else None
            if not isinstance(action, str) or action not in ALLOWED_ACTIONS:
                self._logger.warning("single-instance request rejected")
                continue
            try:
                handler(action)
            except Exception:  # noqa: BLE001 - the IPC thread must not die
                self._logger.exception("single-instance handler failed")

    def _ensure_authkey(self) -> bytes | None:
        authkey = self._load_authkey()
        if authkey is not None:
            return authkey
        authkey = secrets.token_bytes(_AUTHKEY_BYTES)
        try:
            self._authkey_file.parent.mkdir(parents=True, exist_ok=True)
            blob = _dpapi_protect(authkey, _IPC_ENTROPY)
            if not blob:
                # DPAPI unavailable (e.g. non-Windows dev box): the ephemeral
                # key still protects this process' listener; secondary
                # instances simply cannot forward and will log it.
                self._logger.warning(
                    "single-instance authkey could not be protected"
                )
                return authkey
            payload = _IPC_FILE_MAGIC + base64.urlsafe_b64encode(blob)
            self._authkey_file.write_bytes(payload)
        except OSError:
            self._logger.warning("single-instance authkey could not be persisted")
        return authkey

    def _load_authkey(self) -> bytes | None:
        try:
            payload = self._authkey_file.read_bytes()
        except OSError:
            return None
        if not payload.startswith(_IPC_FILE_MAGIC):
            return None
        try:
            blob = base64.urlsafe_b64decode(payload[len(_IPC_FILE_MAGIC):])
        except (ValueError, TypeError):
            return None
        authkey = _dpapi_unprotect(blob, _IPC_ENTROPY)
        if not authkey or len(authkey) != _AUTHKEY_BYTES:
            return None
        return authkey


def _dpapi_protect(data: bytes, entropy: bytes) -> bytes:
    """Encrypt ``data`` for the current Windows user; empty bytes on failure."""

    buffer_in = ctypes.create_string_buffer(data, len(data))
    blob_in = _DataBlob(len(data), ctypes.cast(buffer_in, ctypes.POINTER(ctypes.c_char)))
    entropy_buffer = ctypes.create_string_buffer(entropy, len(entropy))
    entropy_blob = _DataBlob(
        len(entropy), ctypes.cast(entropy_buffer, ctypes.POINTER(ctypes.c_char))
    )
    blob_out = _DataBlob()
    try:
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in),
            None,
            ctypes.byref(entropy_blob),
            None,
            None,
            0,
            ctypes.byref(blob_out),
        )
        if not ok:
            return b""
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    except (AttributeError, OSError):
        return b""
    finally:
        if blob_out.pbData:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _dpapi_unprotect(blob: bytes, entropy: bytes) -> bytes | None:
    """Decrypt a DPAPI blob; None when the blob is not ours to read."""

    buffer_in = ctypes.create_string_buffer(blob, len(blob))
    blob_in = _DataBlob(len(blob), ctypes.cast(buffer_in, ctypes.POINTER(ctypes.c_char)))
    entropy_buffer = ctypes.create_string_buffer(entropy, len(entropy))
    entropy_blob = _DataBlob(
        len(entropy), ctypes.cast(entropy_buffer, ctypes.POINTER(ctypes.c_char))
    )
    blob_out = _DataBlob()
    try:
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in),
            None,
            ctypes.byref(entropy_blob),
            None,
            None,
            0,
            ctypes.byref(blob_out),
        )
        if not ok:
            return None
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    except (AttributeError, OSError):
        return None
    finally:
        if blob_out.pbData:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
