"""Filesystem layout resolution for the Leo AI Studio shell.

The shell ships as a portable package: every asset it needs lives under one
install root (the directory that contains the executable when frozen).  This
module resolves that root plus the well-known sub-directories, locates the
fixed-version WebView2 runtime, and rejects roots that cannot work reliably
(UNC paths and mapped network drives).
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["AppPaths"]

_ROOT_ENV_VAR = "LEO_STUDIO_ROOT"
_MAX_MANIFEST_BYTES = 1024 * 1024
_DRIVE_REMOTE = 4  # GetDriveTypeW result for network drives.


def _default_root() -> Path:
    """Resolve the install root for the current process.

    Frozen builds anchor at the executable's directory.  Development builds
    honour ``LEO_STUDIO_ROOT`` first and otherwise fall back to the parent of
    the repository checkout (the directory that contains ``LeoAIStudio-build``).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    override = os.environ.get(_ROOT_ENV_VAR, "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2]


def _read_manifest(path: Path) -> Any | None:
    """Best-effort read of a small JSON manifest; ``None`` on any failure."""
    try:
        if not path.is_file():
            return None
        if path.stat().st_size > _MAX_MANIFEST_BYTES:
            return None
        return json.loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _dig(mapping: Any, *keys: str) -> Any | None:
    """Walk nested dicts; ``None`` when any step is missing or not a dict."""
    node = mapping
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _drive_type(anchor: str) -> int | None:
    """Return ``GetDriveTypeW`` for *anchor*, or ``None`` when undeterminable.

    The ctypes call is deferred to first use so importing this module stays
    safe on non-Windows platforms.
    """
    if sys.platform != "win32" or not anchor:
        return None
    try:
        get_drive_type = ctypes.windll.kernel32.GetDriveTypeW  # type: ignore[attr-defined]
        get_drive_type.argtypes = [ctypes.c_wchar_p]
        get_drive_type.restype = ctypes.c_uint
        return int(get_drive_type(anchor))
    except (AttributeError, OSError, ValueError):
        return None


@dataclass(frozen=True)
class AppPaths:
    """Resolved directory layout of the portable package."""

    root: Path
    user: Path = field(init=False)
    theme: Path = field(init=False)
    bridge_script: Path = field(init=False)
    runtime_dir: Path = field(init=False)
    logs: Path = field(init=False)
    credentials: Path = field(init=False)

    def __post_init__(self) -> None:
        root = Path(self.root)
        user = root / "user"
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "user", user)
        object.__setattr__(self, "theme", root / "theme")
        object.__setattr__(self, "bridge_script", root / "bridge" / "leo_bridge.sh")
        object.__setattr__(self, "runtime_dir", root / "runtime")
        object.__setattr__(self, "logs", user / "logs")
        object.__setattr__(self, "credentials", user / "credentials")

    @classmethod
    def from_root(cls, root: Path | str | None = None) -> "AppPaths":
        """Build the layout for *root*, or resolve the default root."""
        if root is None:
            root = _default_root()
        return cls(Path(root))

    def reject_unsupported_root(self) -> None:
        """Raise ``ValueError`` for UNC roots and mapped network drives."""
        text = str(self.root)
        if text.startswith(("\\\\", "//")) or self.root.drive.startswith("\\\\"):
            raise ValueError(f"unsupported install root (UNC path): {text!r}")
        anchor = self.root.anchor
        if anchor and not anchor.startswith("\\\\"):
            if _drive_type(anchor) == _DRIVE_REMOTE:
                raise ValueError(f"unsupported install root (network drive): {text!r}")

    def webview2_dir(self) -> Path:
        """Locate the bundled fixed-version WebView2 runtime directory.

        Manifests ``runtime/dependencies.json`` and ``runtime/runtime-manifest.json``
        are consulted first (``dependencies.webview2.path``, relative to the
        install root).  Without a usable manifest entry, fall back to the single
        subdirectory of ``runtime/webview2``.  Raises ``FileNotFoundError`` when
        no unambiguous runtime can be found.
        """
        for manifest in (
            self.runtime_dir / "dependencies.json",
            self.runtime_dir / "runtime-manifest.json",
        ):
            candidate = self._webview2_from_manifest(manifest)
            if candidate is not None:
                return candidate
        return self._webview2_fallback()

    def _webview2_from_manifest(self, manifest: Path) -> Path | None:
        data = _read_manifest(manifest)
        if not isinstance(data, dict):
            return None
        relative = _dig(data, "dependencies", "webview2", "path")
        if isinstance(relative, str) and relative.strip():
            return self._resolve_dir_within_root(relative.strip())
        # ``dependencies.json`` records only the extracted directory name;
        # it lives one version level below ``runtime/webview2``.
        extracted = _dig(data, "webview2", "extracted_directory")
        if isinstance(extracted, str) and extracted:
            return self._webview2_from_extracted_name(extracted)
        return None

    def _resolve_dir_within_root(self, relative: str) -> Path | None:
        """Resolve a manifest-relative path; reject absolute or escaping paths."""
        try:
            rel = Path(relative)
        except (TypeError, ValueError):
            return None
        if rel.is_absolute() or rel.drive or rel.anchor:
            return None
        try:
            root = self.root.resolve()
            candidate = (root / rel).resolve()
        except OSError:
            return None
        if candidate == root or not candidate.is_relative_to(root):
            return None
        if not candidate.is_dir():
            return None
        return candidate

    def _webview2_from_extracted_name(self, name: str) -> Path | None:
        if Path(name).name != name:  # must be a bare directory name
            return None
        base = self.runtime_dir / "webview2"
        try:
            if not base.is_dir():
                return None
            version_dirs = sorted(base.iterdir())
        except OSError:
            return None
        for version_dir in version_dirs:
            candidate = version_dir / name
            try:
                if version_dir.is_dir() and candidate.is_dir():
                    return candidate
            except OSError:
                continue
        return None

    def _webview2_fallback(self) -> Path:
        base = self.runtime_dir / "webview2"
        subdirs: list[Path] = []
        try:
            if base.is_dir():
                subdirs = sorted(p for p in base.iterdir() if p.is_dir())
        except OSError:
            subdirs = []
        if len(subdirs) == 1:
            return subdirs[0]
        raise FileNotFoundError(
            "WebView2 fixed runtime not found: no usable manifest entry and "
            f"{str(base)!r} does not contain exactly one subdirectory"
        )
