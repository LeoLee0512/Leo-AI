"""The opening animation played once per launch on the start page.

The start page is an in-memory document (``NavigateToString``, 1.5 MiB budget), so a
21 MB video cannot be inlined. Instead the folder that holds ONLY the video is mapped
to a virtual host with WebView2's ``SetVirtualHostNameToFolderMapping``: no port is
opened, nothing leaves the machine, and no other file of the installation becomes
reachable. ``DenyCors`` lets a ``<video>`` element read it but refuses scripted
cross-origin reads.

The animation was generated with the Seedance 2.5 model (owner-supplied, 2026-09-26);
that is stated in Settings -> About, next to the OpenAI4S attribution, and recorded in
``manifests/runtime-asset-origins.json``.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

__all__ = ["INTRO_DIRECTORY", "INTRO_FILE", "INTRO_HOST", "IntroGate", "intro_url", "map_intro_folder"]

INTRO_DIRECTORY = "intro"
INTRO_FILE = "leo-intro.mp4"
# ``.example`` is reserved (RFC 2606) and can never resolve to a real site.
INTRO_HOST = "intro.leo-studio.example"


def intro_url() -> str:
    return f"https://{INTRO_HOST}/{INTRO_FILE}"


class IntroGate:
    """Hands the intro out at most once per process: launch plays it, returning to the start page does not."""

    def __init__(self, folder: Path, *, enabled: bool = True) -> None:
        self._folder = Path(folder)
        self._pending = bool(enabled)
        self._lock = threading.Lock()

    @property
    def folder(self) -> Path:
        return self._folder

    def pending(self) -> bool:
        with self._lock:
            return self._pending and (self._folder / INTRO_FILE).is_file()

    def cancel(self) -> None:
        with self._lock:
            self._pending = False

    def claim(self) -> bool:
        """True exactly once, and only when the video file is present."""
        with self._lock:
            if not self._pending:
                return False
            self._pending = False
        return (self._folder / INTRO_FILE).is_file()


def map_intro_folder(native_form: Any, folder: Path) -> None:
    """Map ``folder`` to :data:`INTRO_HOST` on the WebView2 UI thread (pywebview EdgeChromium)."""

    from System import Action  # type: ignore[import-not-found]  # pythonnet, loaded by pywebview

    def apply() -> None:
        from Microsoft.Web.WebView2.Core import CoreWebView2HostResourceAccessKind  # type: ignore[import-not-found]

        native_form.webview.CoreWebView2.SetVirtualHostNameToFolderMapping(
            INTRO_HOST, str(Path(folder).resolve()), CoreWebView2HostResourceAccessKind.DenyCors)

    native_form.Invoke(Action(apply))
