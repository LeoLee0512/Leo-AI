"""Desktop window layer for the rewritten Leo AI Studio shell.

This is the only shell module allowed to import pywebview at module import
time.  ``app.py`` therefore imports this module lazily, right before the
window is assembled, so ``--diagnostics`` keeps working on machines where the
GUI stack cannot load.

:class:`DesktopUI` owns the pywebview window and implements the
``UiSink`` protocol consumed by ``connection.ConnectionCoordinator``:

- ``publish_status`` forwards status codes to ``window.setStatus``; the front
  end replays them once the shell has revealed itself, so any timing is safe.
- ``navigate`` checks the daemon URL is the trusted loopback backend, then
  loads Leo's own workbench document; the upstream page is never navigated.
- ``open_settings`` opens the settings drawer through ``LeoShell``.
"""

from __future__ import annotations

import json
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import webview

from .api import ShellApi
from .intro import INTRO_DIRECTORY, IntroGate, intro_url, map_intro_folder
from .theme_runtime import trusted_backend_url
from .windows_branding import apply_window_branding, clear_window_branding, set_process_app_id

if TYPE_CHECKING:
    from .connection import ConnectionCoordinator
    from .paths import AppPaths
    from .settings_store import SettingsStore
    from .theme_runtime import ThemeRuntime

__all__ = ["DesktopUI"]


from . import DISPLAY_NAME

_WINDOW_TITLE = DISPLAY_NAME
# Must stay in sync with the splash page background in theme/shell.html
# (--bg): the window paints this before the document renders, so a
# mismatch shows as a one-frame flash of the previous palette.
_WINDOW_BACKGROUND = "#FBF7F2"
_STARTUP_GUARD_SECONDS = 10.0
# WebView2 applies a virtual-host mapping only to documents navigated AFTER it is set
# (measured 2026-09-26: an in-memory page loaded earlier cannot reach the host at all).
# So a launch that plays the opening animation first shows this blank page -- the
# window's own colour, nothing to see -- maps the intro folder, then loads the start page.
_BOOT_HTML = ('<!doctype html><html><head><meta charset="utf-8"></head>'
              '<body style="margin:0;background:' + "#FBF7F2" + '"></body></html>')
_BOOT_FALLBACK_SECONDS = 6.0

_OPEN_SETTINGS_JS = (
    "window.LeoShell && window.LeoShell.openSettings "
    "&& window.LeoShell.openSettings();"
)


class DesktopUI:
    """Owns the pywebview window; implements the coordinator's UiSink."""

    def __init__(
        self,
        paths: AppPaths,
        settings: SettingsStore,
        theme: ThemeRuntime,
        coordinator: ConnectionCoordinator,
        logger: logging.Logger | None = None,
    ) -> None:
        self._paths = paths
        self._settings = settings
        self._theme = theme
        self._coordinator = coordinator
        self._logger = logger if logger is not None else logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._window: Any | None = None
        self._open_settings = False
        self._closed = False
        self._guard_deadline = 0.0
        self._minimized_recovered = False
        self._owned_workbench = False
        # The opening animation plays once, on launch; --settings and every later
        # return to the start page skip it.
        theme_root = getattr(paths, "theme", None)
        self._intro = IntroGate(theme_root / INTRO_DIRECTORY if theme_root is not None else Path(INTRO_DIRECTORY),
                                enabled=theme_root is not None)
        self._intro_mapped = False
        self._boot: tuple[str, str] | None = None

    # -- lifecycle -----------------------------------------------------------

    def request_open_settings(self) -> None:
        """Open the settings drawer once the shell is up (used by --settings)."""

        with self._lock:
            self._open_settings = True
        self._intro.cancel()
        self.open_settings()

    def run(self, on_ready: Callable[[], None]) -> None:
        """Create the window and block in the pywebview event loop."""

        try:
            set_process_app_id(self._paths.theme / "logos" / "leo-lion.ico")
        except Exception:
            self._logger.warning("taskbar process identity could not be set", exc_info=True)
        html = self._theme.render_shell(open_settings=self._open_settings)
        first_document = html
        if self._intro.pending():
            self._boot = (self._theme.render_shell(open_settings=False, intro=True), html)
            first_document = _BOOT_HTML
        api = ShellApi(
            self._settings,
            self._coordinator,
            self,
            paths=self._paths,
            logger=self._logger,
        )
        self._api = api
        # Approval modes and scheduled messages run beside the window for as long as it is open.
        self._extensions = None
        try:
            from .extensions import Extensions
            self._extensions = Extensions(api, self._paths, self._coordinator._bridge.client_url, logger=self._logger)
        except Exception:
            self._logger.exception("approval and schedule services could not start")
        # WebView2 otherwise silently cancels the user-requested knowledge-tree
        # export. pywebview presents its native Save dialog for every download.
        webview.settings["ALLOW_DOWNLOADS"] = True
        window = webview.create_window(
            _WINDOW_TITLE,
            html=first_document,
            js_api=api,
            width=1280,
            height=800,
            min_size=(840, 600),
            confirm_close=False,
            background_color=_WINDOW_BACKGROUND,
        )
        self._window = window
        self._guard_deadline = time.monotonic() + _STARTUP_GUARD_SECONDS
        window.events.shown += self._on_shown
        window.events.minimized += self._on_minimized
        window.events.closing += self._on_closing
        if self._boot is not None:
            window.events.loaded += self._on_boot_loaded
            threading.Thread(target=self._boot_fallback, name="leo-boot-fallback", daemon=True).start()
        # The native window, executable and desktop shortcut share one icon.
        icon_path = self._paths.theme / "logos" / "leo-lion.ico"
        webview.start(func=on_ready, gui="edgechromium", private_mode=True, debug=False,
                      icon=str(icon_path) if icon_path.is_file() else None)

    # -- UiSink (called from the coordinator worker thread) -------------------

    def publish_status(self, message: str, *, error: bool = False) -> None:
        window = self._window
        if window is None:
            return
        script = (
            "window.setStatus && window.setStatus("
            + json.dumps(str(message), ensure_ascii=False)
            + (", true);" if error else ", false);")
        )
        try:
            window.evaluate_js(script)
        except Exception:
            self._logger.debug("status publish failed", exc_info=True)

    def navigate(self, url: str) -> bool:
        window = self._window
        if window is None:
            return False
        if not trusted_backend_url(url):
            # Never log the URL itself: it carries the daemon token.
            self._logger.error("refusing to navigate to an untrusted backend URL")
            return False
        with self._lock:
            try:
                html = self._theme.render_workbench()
                window.load_html(html)
                self._owned_workbench = True
                self._logger.info("Leo workbench document loaded; upstream page not navigated")
                return True
            except Exception as exc:
                # Native exceptions may include the navigation URI and token.
                self._logger.error("backend navigation failed (%s)", type(exc).__name__)
                return False

    def return_to_start(self, open_settings: bool = False) -> bool:
        """Reload the original shell while preserving the running workbench."""
        window = self._window
        if window is None:
            return False
        try:
            # Render first: a missing asset leaves the current page usable.
            html = self._theme.render_shell(open_settings=bool(open_settings))
            self._coordinator.cancel_pending()
            with self._lock:
                window.load_html(html)
                self._owned_workbench = False
            return True
        except Exception:
            self._logger.exception("start page navigation failed")
            return False

    def intro_video_url(self) -> str | None:
        """The intro URL once per launch, only after the boot step mapped its folder; None means skip it."""
        if not self._intro_mapped or not self._intro.claim():
            return None
        return intro_url()

    def _take_boot(self) -> tuple[str, str] | None:
        with self._lock:
            boot, self._boot = self._boot, None
        return boot

    def _on_boot_loaded(self) -> None:
        """First document is the blank boot page: map the intro folder, then load the start page."""
        boot = self._take_boot()
        window = self._window
        if boot is None or window is None:
            return
        with_intro, plain = boot
        try:
            map_intro_folder(window.native, self._intro.folder)
            self._intro_mapped = True
        except Exception:
            self._intro.cancel()
            self._logger.warning("opening animation unavailable; start page shown directly", exc_info=True)
        try:
            window.load_html(with_intro if self._intro_mapped else plain)
        except Exception:
            self._logger.exception("start page load after boot failed")

    def _boot_fallback(self) -> None:
        """Never leave the blank boot page up: without a load event, show the start page plainly."""
        time.sleep(_BOOT_FALLBACK_SECONDS)
        boot = self._take_boot()
        window = self._window
        if boot is None or window is None:
            return
        self._intro.cancel()
        self._logger.warning("boot page did not report loaded; start page shown without the opening animation")
        try:
            window.load_html(boot[1])
        except Exception:
            self._logger.exception("start page fallback load failed")

    def open_settings(self) -> None:
        window = self._window
        if window is None:
            return
        try:
            window.evaluate_js(_OPEN_SETTINGS_JS)
        except Exception:
            self._logger.debug("open_settings evaluation failed", exc_info=True)

    # -- hooks used by app.py / api.py ----------------------------------------

    def handle_instance_action(self, action: str) -> None:
        """Handle an action forwarded by a second process instance."""

        if action == "update":
            self._logger.info("ignoring forwarded update action (unsupported)")
            return
        if action not in ("settings", "activate"):
            self._logger.warning("ignoring unknown forwarded action")
            return
        window = self._window
        if window is not None:
            try:
                window.restore()
                window.show()
            except Exception:
                self._logger.debug("window restore/show failed", exc_info=True)
        self.open_settings()

    # -- window events ---------------------------------------------------------

    def _on_shown(self) -> None:
        try:
            if self._window is not None:
                apply_window_branding(
                    self._window.native.Handle.ToInt64(),
                    self._paths.theme / "logos" / "leo-lion.ico",
                    subprocess.list2cmdline([str(self._paths.root / "LeoAIStudio.exe")]),
                )
        except Exception:
            self._logger.warning("taskbar window branding could not be set", exc_info=True)
        self._startup_guard_recover()

    def _on_minimized(self) -> None:
        with self._lock:
            if self._minimized_recovered:
                return
            self._minimized_recovered = True
        self._startup_guard_recover()

    def _on_closing(self):
        with self._lock:
            if self._closed:
                return None
        if not self._research_close_allowed():
            return False  # pywebview cancels the close
        with self._lock:
            if self._closed:
                return None
            self._closed = True
        try:
            if getattr(self, "_extensions", None) is not None:
                self._extensions.close()
        except Exception:
            self._logger.exception("approval and schedule services did not stop cleanly")
        try:
            if self._window is not None:
                clear_window_branding(self._window.native.Handle.ToInt64())
        except Exception:
            self._logger.debug("taskbar window branding cleanup failed", exc_info=True)
        try:
            self._coordinator.close()
        except Exception:
            self._logger.exception("coordinator close failed during window closing")

    def _research_close_allowed(self) -> bool:
        """A running research task is never left computing behind a closed window.

        Runs on the UI thread inside the closing event, where a native message box is safe.
        """
        api = getattr(self, "_api", None)
        try:
            busy = api._research_busy_tasks() if api is not None else []
        except Exception:
            self._logger.exception("research state could not be read while closing")
            busy = []
        if not busy:
            return True
        text = ("有科研任务正在进行。\n\n关闭 Leo AI 会停止计算：正在运行的任务记为「已取消」，"
                "已经产生的证据会保留；正在准备的确认包下次打开时会标为「准备中断」。\n\n确定关闭吗？")
        if not _confirm_native(self._window, _WINDOW_TITLE, text):
            return False
        try:
            api._research_stop_for_close()
        except Exception:
            self._logger.exception("research runs could not be stopped while closing")
        return True

    # -- internals --------------------------------------------------------------

    def _startup_guard_recover(self) -> None:
        """Force the window visible during the startup grace period."""

        if time.monotonic() > self._guard_deadline:
            return
        window = self._window
        if window is None:
            return
        try:
            window.restore()
            window.show()
        except Exception:
            self._logger.debug("startup guard recovery failed", exc_info=True)


def _confirm_native(window, title: str, text: str) -> bool:
    """OK/Cancel message box owned by the Leo window (Windows only; elsewhere, allow)."""
    try:
        import ctypes
        owner = window.native.Handle.ToInt64() if window is not None else 0
        # MB_OKCANCEL | MB_ICONWARNING | MB_DEFBUTTON2: cancelling is the default.
        return ctypes.WinDLL("user32").MessageBoxW(owner, text, title, 0x1 | 0x30 | 0x100) == 1
    except Exception:
        return True
