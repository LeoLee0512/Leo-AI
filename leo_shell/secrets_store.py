"""DPAPI-backed API key storage for the Leo AI Studio shell.

Keys are protected with the current user's DPAPI scope
(``crypt32.CryptProtectData``) and stored as one file per profile under
``user/credentials``.  The file layout is::

    b"LEOCRED1\\n" + base64url(dpapi(json.dumps({"v": 1, "api_key": key})))

All Windows-specific ctypes calls are deferred to first use, so importing
this module is safe on any platform.  Secret values are never logged and
never appear in exceptions; :meth:`SecretsStore.migrate_legacy` in particular
fails silently on every error path.
"""

from __future__ import annotations

import base64
import binascii
import ctypes
import json
import os
import re
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Any

from .logging_setup import register_redaction

__all__ = ["SecretsStore"]

_FILE_MAGIC = b"LEOCRED1\n"
_PROFILE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_MAX_KEY_FILE_BYTES = 1024 * 1024
_MAX_LEGACY_BYTES = 1024 * 1024
_CREATE_NO_WINDOW = 0x08000000
# Best-effort entropy candidates for legacy ``user/credential.dpapi`` blobs.
_LEGACY_ENTROPY_CANDIDATES: tuple[bytes | None, ...] = (
    None,
    b"LeoAIStudio",
    b"LeoAIStudio/Credential/v1",
    b"OpenAI4S",
    b"leo_ai_studio",
    b"credential",
)


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.c_void_p),
    ]


def _dpapi_available() -> bool:
    return sys.platform == "win32" and hasattr(ctypes, "windll")


def _blob_from_bytes(data: bytes) -> _DataBlob:
    buffer = ctypes.create_string_buffer(data, len(data))
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.c_void_p))
    blob._buffer = buffer  # type: ignore[attr-defined]  # keep the buffer alive
    return blob


def _local_free(pointer: int | None) -> None:
    """``LocalFree`` with an explicit 64-bit-safe prototype."""
    if not pointer:
        return
    local_free = ctypes.windll.kernel32.LocalFree  # type: ignore[attr-defined]
    local_free.argtypes = [ctypes.c_void_p]
    local_free.restype = ctypes.c_void_p
    local_free(ctypes.c_void_p(pointer))


def _protect(data: bytes, entropy: bytes | None = None) -> bytes:
    """Wrap ``CryptProtectData``; raises ``OSError`` on failure."""
    if not _dpapi_available():
        raise OSError("DPAPI is only available on Windows")
    crypt32 = ctypes.windll.crypt32  # type: ignore[attr-defined]
    blob_in = _blob_from_bytes(data)
    entropy_blob = _blob_from_bytes(entropy) if entropy else None
    blob_out = _DataBlob()
    ok = crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        None,
        ctypes.byref(entropy_blob) if entropy_blob is not None else None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    )
    if not ok:
        raise ctypes.WinError()  # type: ignore[attr-defined]
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _local_free(blob_out.pbData)


def _unprotect(blob: bytes, entropy: bytes | None = None) -> bytes:
    """Wrap ``CryptUnprotectData``; raises ``OSError`` on failure."""
    if not _dpapi_available():
        raise OSError("DPAPI is only available on Windows")
    crypt32 = ctypes.windll.crypt32  # type: ignore[attr-defined]
    blob_in = _blob_from_bytes(blob)
    entropy_blob = _blob_from_bytes(entropy) if entropy else None
    blob_out = _DataBlob()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        ctypes.byref(entropy_blob) if entropy_blob is not None else None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    )
    if not ok:
        raise ctypes.WinError()  # type: ignore[attr-defined]
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _local_free(blob_out.pbData)


def _restrict_to_current_user(path: Path) -> None:
    """Best-effort ACL tightening so only the current user can read *path*.

    Never fatal: DPAPI already binds the content to the user, this is just
    defence in depth for the file itself.
    """
    if sys.platform != "win32":
        return
    try:
        import getpass

        user = getpass.getuser()
        if not user:
            return
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        icacls = os.path.join(system_root, "System32", "icacls.exe")
        subprocess.run(
            [icacls, str(path), "/inheritance:r", "/grant:r", f"{user}:(F)"],
            creationflags=_CREATE_NO_WINDOW,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except Exception:
        pass


def _extract_key_from_plaintext(plain: bytes) -> str | None:
    """Interpret a decrypted legacy payload as an API key, or ``None``."""
    try:
        text = plain.decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        return None
    if not text or "\x00" in text:
        return None
    parsed: Any = None
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        lowered = {str(key).lower(): value for key, value in parsed.items()}
        for name in ("api_key", "apikey", "key", "token"):
            value = lowered.get(name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
    if isinstance(parsed, str) and parsed.strip():
        return parsed.strip()
    if parsed is None and len(text) <= 4096 and "\n" not in text and "\r" not in text:
        # A bare string payload is treated as the key itself.
        return text
    return None


def _legacy_blob_candidates(raw: bytes) -> list[bytes]:
    """Raw bytes plus plausible base64 wrappings of the DPAPI blob."""
    candidates = [raw]
    compact = re.sub(rb"\s+", b"", raw)
    if compact and compact != raw:
        candidates.append(compact)
    for source in (compact,):
        try:
            decoded = base64.b64decode(source, validate=True)
            if decoded:
                candidates.append(decoded)
        except (binascii.Error, ValueError):
            pass
        try:
            decoded = base64.urlsafe_b64decode(source)
            if decoded:
                candidates.append(decoded)
        except (binascii.Error, ValueError):
            pass
    return candidates


class SecretsStore:
    """One DPAPI-protected key file per profile under *directory*."""

    def __init__(self, directory: Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    @property
    def directory(self) -> Path:
        return self._directory

    def _key_file(self, profile_id: str) -> Path:
        if not isinstance(profile_id, str) or not _PROFILE_ID_PATTERN.match(profile_id):
            raise ValueError("invalid profile id for secrets storage")
        return self._directory / f"{profile_id}.dpapi"

    def save_key(
        self,
        profile_id: str,
        api_key: str,
        *,
        entropy: bytes | None = None,
        overwrite: bool = True,
    ) -> None:
        """Protect *api_key* with DPAPI and store it for *profile_id*."""
        if not isinstance(api_key, str) or not api_key:
            raise ValueError("api_key must be a non-empty string")
        target = self._key_file(profile_id)
        payload = json.dumps({"v": 1, "api_key": api_key}, separators=(",", ":")).encode("utf-8")
        blob = _protect(payload, entropy)
        content = _FILE_MAGIC + base64.urlsafe_b64encode(blob)
        if overwrite:
            tmp = target.with_name(target.name + ".tmp")
            with open(tmp, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, target)
        else:
            # Exclusive creation closes the race between migration's existence
            # check and a user saving a new profile credential.
            with open(target, "xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        _restrict_to_current_user(target)
        register_redaction(api_key)

    def load_key(self, profile_id: str, *, entropy: bytes | None = None) -> str | None:
        """Return the stored key, or ``None`` when missing or unreadable."""
        try:
            target = self._key_file(profile_id)
        except ValueError:
            return None
        try:
            if not target.is_file() or target.stat().st_size > _MAX_KEY_FILE_BYTES:
                return None
            raw = target.read_bytes()
        except OSError:
            return None
        if not raw.startswith(_FILE_MAGIC):
            return None
        encoded = raw[len(_FILE_MAGIC):].strip()
        try:
            blob = base64.urlsafe_b64decode(encoded)
            payload = _unprotect(blob, entropy)
            data = json.loads(payload.decode("utf-8"))
        except (binascii.Error, OSError, UnicodeDecodeError, ValueError):
            return None
        if not isinstance(data, dict) or data.get("v") != 1:
            return None
        key = data.get("api_key")
        if not isinstance(key, str) or not key:
            return None
        return key

    def delete_key(self, profile_id: str) -> None:
        """Remove the stored key; missing files are ignored."""
        try:
            target = self._key_file(profile_id)
        except ValueError:
            return
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass

    def migrate_legacy(self, legacy_file: Path, profile_id: str | None) -> None:
        """Best-effort import of the old shell's ``credential.dpapi``.

        Every failure path returns ``None`` silently: no exception escapes, no
        secret value is logged, and the legacy file is never modified or
        deleted. An existing destination, including an unreadable/corrupt file
        or a link, is preserved for explicit recovery rather than overwritten.
        """
        try:
            if not profile_id or not _dpapi_available():
                return None
            target = self._key_file(profile_id)
            try:
                target.lstat()
            except FileNotFoundError:
                pass
            else:
                return None
            source = Path(legacy_file)
            if not source.is_file() or source.stat().st_size > _MAX_LEGACY_BYTES:
                return None
            raw = source.read_bytes()
            if not raw:
                return None
            for blob in _legacy_blob_candidates(raw):
                for entropy in _LEGACY_ENTROPY_CANDIDATES:
                    try:
                        plain = _unprotect(blob, entropy)
                    except Exception:
                        continue
                    key = _extract_key_from_plaintext(plain)
                    if not key:
                        continue
                    try:
                        self.save_key(profile_id, key, overwrite=False)
                    except Exception:
                        pass
                    return None
        except Exception:
            return None
        return None
