"""Fixed-version WebView2 runtime discovery and ACL hardening.

The portable bundle ships a fixed WebView2 runtime below ``runtime/``.  At
startup we locate the single ``msedgewebview2.exe``, grant read/execute to the
restricted app-container SIDs (some enterprise policies strip those), and pin
pywebview to the bundled runtime.  Every step except the final pin is
fail-soft: if ACL hardening fails, the system WebView2 remains as fallback.

``webview`` is imported lazily inside :func:`configure_fixed_runtime` so this
module stays importable on machines without pywebview (CI, diagnostics).
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .paths import AppPaths

__all__ = ["WebView2RuntimeError", "configure_fixed_runtime"]

_EXE_NAME = "msedgewebview2.exe"
_ICACLS_TIMEOUT_SECONDS = 30
_CREATE_NO_WINDOW = 0x08000000
_STARTF_USESHOWWINDOW = 0x00000001
_SW_HIDE = 0
# Read/execute for restricted app containers and all app containers.
_ACL_GRANTS = ("*S-1-15-2-2:(OI)(CI)(RX)", "*S-1-15-2-1:(OI)(CI)(RX)")


class WebView2RuntimeError(RuntimeError):
    """Raised when the bundled fixed WebView2 runtime cannot be used."""


def configure_fixed_runtime(paths: AppPaths, logger: logging.Logger | None = None) -> None:
    """Pin pywebview to the bundled runtime after best-effort ACL hardening."""

    log = logger if logger is not None else logging.getLogger(__name__)
    runtime_dir = paths.webview2_dir()
    if not runtime_dir.is_dir():
        raise WebView2RuntimeError(
            f"WebView2 runtime directory is missing: {runtime_dir}"
        )
    selected = _locate_runtime_exe(runtime_dir)
    _grant_acl(selected.parent, log)

    import webview  # deferred: pywebview is unavailable in test environments

    settings = getattr(webview, "settings", None)
    if settings is None:
        raise WebView2RuntimeError("pywebview settings surface is unavailable")
    # BrowserExecutableFolder is the *directory* that holds msedgewebview2.exe.
    # Passing the exe file itself makes CoreWebView2Environment.CreateAsync
    # fail with 0x80070002 and the window stays black.
    settings["WEBVIEW2_RUNTIME_PATH"] = str(selected.parent)
    log.info("webview2 runtime pinned to %s", selected.parent)


def _locate_runtime_exe(runtime_dir: Path) -> Path:
    direct = runtime_dir / _EXE_NAME
    if direct.is_file():
        return direct
    matches = sorted(path for path in runtime_dir.rglob(_EXE_NAME) if path.is_file())
    if len(matches) != 1:
        raise WebView2RuntimeError(
            f"expected exactly one {_EXE_NAME} below {runtime_dir}, "
            f"found {len(matches)}"
        )
    return matches[0]


def _grant_acl(runtime_dir: Path, log: logging.Logger) -> None:
    """Best-effort ``icacls`` grant; failures are logged, never raised."""

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    icacls = Path(system_root) / "System32" / "icacls.exe"
    argv = [str(icacls), str(runtime_dir), "/grant:r", *_ACL_GRANTS]
    try:
        result = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            timeout=_ICACLS_TIMEOUT_SECONDS,
            **_hidden_window_kwargs(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning("webview2 ACL grant failed to launch: %s", type(exc).__name__)
        return
    if result.returncode != 0:
        log.warning("webview2 ACL grant exited with code %s", result.returncode)


def _hidden_window_kwargs() -> dict[str, Any]:
    if sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= _STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = _SW_HIDE
    return {"creationflags": _CREATE_NO_WINDOW, "startupinfo": startupinfo}
