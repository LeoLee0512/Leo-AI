"""CLI entry and assembly for the rewritten Leo AI Studio shell.

This module must stay importable without pywebview: every sibling import that
could pull in the GUI stack happens lazily inside :class:`Application`, so
``--diagnostics`` works on headless machines.  Exit codes:

- ``0`` — normal run (or the request was forwarded to a running instance)
- ``1`` — startup/diagnostics failure
- ``2`` — a reserved phase-two action (``--update`` / ``--export-data`` /
  ``--import-data``) was requested
"""

from __future__ import annotations

import argparse
import logging
import sys
from . import DISPLAY_NAME, __version__
from typing import Any, Sequence

__all__ = ["Application", "build_parser", "main"]


EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_UNSUPPORTED = 2

_LEGACY_CREDENTIAL_FILE = "credential.dpapi"


class _LateBoundUiSink:
    """UiSink placeholder resolved to the real DesktopUI after assembly.

    ``ConnectionCoordinator`` and ``DesktopUI`` reference each other, so the
    coordinator is constructed first with this proxy; nothing is submitted to
    the coordinator before the window exists, making the brief unbound window
    unreachable in practice.
    """

    def __init__(self) -> None:
        self._target: Any | None = None

    def bind(self, target: Any) -> None:
        self._target = target

    def publish_status(self, message: str, *, error: bool = False) -> None:
        target = self._target
        if target is not None:
            target.publish_status(message, error=error)

    def navigate(self, url: str) -> Any:
        target = self._target
        if target is not None:
            return target.navigate(url)
        return False

    def open_settings(self) -> None:
        target = self._target
        if target is not None:
            target.open_settings()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="leo-ai-studio",
        description=f"{DISPLAY_NAME} desktop shell",
    )
    parser.add_argument(
        "--version", action="version", version=f"{DISPLAY_NAME} ({__version__})",
    )
    parser.add_argument(
        "--settings",
        action="store_true",
        help="open the settings drawer right after launch; do not auto-connect",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="write a redacted diagnostics report to user/logs and exit",
    )
    for action in ("--update", "--export-data", "--import-data"):
        parser.add_argument(
            action,
            action="store_true",
            help="reserved for a future release (currently exits with code 2)",
        )
    return parser


class Application:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self._logger = logging.getLogger("leo_shell.app")

    def run(self) -> int:
        args = self._args

        from .paths import AppPaths

        try:
            paths = AppPaths.from_root()
            paths.reject_unsupported_root()
        except Exception as exc:
            print(f"Leo AI Studio cannot start from this location: {exc}", file=sys.stderr)
            return EXIT_FAILURE

        from .logging_setup import setup_logging

        logger = setup_logging(paths)
        self._logger = logger

        unsupported = [
            flag
            for flag, requested in (
                ("--update", args.update),
                ("--export-data", args.export_data),
                ("--import-data", args.import_data),
            )
            if requested
        ]
        if unsupported:
            logger.info(
                "unsupported CLI action(s) %s requested; exiting with code %d",
                ", ".join(unsupported),
                EXIT_UNSUPPORTED,
            )
            return EXIT_UNSUPPORTED

        if args.diagnostics:
            from .bridge_client import WslBridge

            try:
                bridge = WslBridge(paths, logger=logger)
            except Exception:
                logger.exception("bridge initialization failed")
                return EXIT_FAILURE
            return self._run_diagnostics(paths, bridge, logger)

        return self._run_windowed(paths, logger)

    # -- CLI modes -------------------------------------------------------------

    def _run_diagnostics(self, paths: Any, bridge: Any, logger: logging.Logger) -> int:
        from .diagnostics import run_diagnostics

        try:
            report_path = run_diagnostics(paths, bridge, logger)
        except Exception:
            logger.exception("diagnostics run failed")
            return EXIT_FAILURE
        print(f"Diagnostics written to {report_path}")
        return EXIT_OK

    def _run_windowed(self, paths: Any, logger: logging.Logger) -> int:
        from .bridge_client import WslBridge
        from .connection import ConnectionCoordinator
        from .secrets_store import SecretsStore
        from .settings_store import SettingsStore
        from .single_instance import SingleInstance

        secrets = SecretsStore(paths.credentials)
        settings = SettingsStore(paths, secrets)
        try:
            # Best-effort by contract: any failure is silently abandoned.  The
            # migration needs the active profile id, so it runs after the store
            # exists rather than before it.
            active = settings.active_profile()
            if (active is not None and getattr(active, "requires_key", True) is not False
                    and not secrets.load_key(active.id)):
                secrets.migrate_legacy(paths.user / _LEGACY_CREDENTIAL_FILE, active.id)
        except Exception:
            logger.debug("legacy credential migration skipped")
        bridge = WslBridge(paths, logger=logger)
        sink = _LateBoundUiSink()
        coordinator = ConnectionCoordinator(bridge, sink, logger)
        instance = SingleInstance(paths)

        try:
            claimed = instance.claim()
        except Exception:
            # Degraded mode per contract: being unable to claim must not
            # prevent the primary instance from running.
            logger.exception("single-instance claim failed; continuing as primary")
            claimed = True

        if not claimed:
            action = "settings" if self._args.settings else "activate"
            try:
                instance.forward(action)
            except Exception:
                logger.exception("failed to forward %s to the running instance", action)
            return EXIT_OK

        try:
            try:
                from .webview2_runtime import configure_fixed_runtime

                configure_fixed_runtime(paths, logger)
            except Exception:
                logger.exception(
                    "fixed WebView2 runtime setup failed; falling back to system runtime"
                )

            from .theme_runtime import ThemeRuntime

            theme = ThemeRuntime(paths.theme)

            # Lazy: importing ui pulls in pywebview.
            from . import ui as ui_module

            window_ui = ui_module.DesktopUI(paths, settings, theme, coordinator, logger)
            sink.bind(window_ui)
            if self._args.settings:
                window_ui.request_open_settings()

            instance.listen(lambda action: self._on_instance_action(window_ui, action))

            window_ui.run(lambda: self._on_window_ready(window_ui, settings, coordinator))
            return EXIT_OK
        finally:
            try:
                coordinator.close()
            except Exception:
                logger.exception("coordinator close failed")
            try:
                instance.close()
            except Exception:
                logger.exception("single-instance close failed")

    # -- callbacks ---------------------------------------------------------------

    def _on_instance_action(self, window_ui: Any, action: str) -> None:
        try:
            window_ui.handle_instance_action(action)
        except Exception:
            self._logger.exception("forwarded instance action failed")

    def _on_window_ready(self, window_ui: Any, settings: Any, coordinator: Any) -> None:
        """Keep startup passive; only an explicit shell action may connect.

        The page reads its configuration through ``ShellApi.get_state``. A
        stored credential or a local preset is not a request to start a daemon
        or load a model. Keep the callback signature for the assembly seam.
        """
        logger = self._logger
        if not self._args.settings:
            logger.info("startup stays on the start page; waiting for explicit entry")
            return
        try:
            # --settings is an explicit drawer request, never a connection.
            window_ui.open_settings()
        except Exception:
            from .connection import PUBLIC_SETTINGS_UNAVAILABLE

            logger.exception("startup settings drawer failed")
            try:
                window_ui.publish_status(PUBLIC_SETTINGS_UNAVAILABLE, error=True)
            except Exception:
                logger.debug("startup status publish failed", exc_info=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return Application(args).run()
    except Exception as exc:
        # Last-resort guard: startup failures before logging is ready must
        # still surface on stderr instead of dying with a raw traceback.
        print(f"Leo AI Studio failed to start: {exc}", file=sys.stderr)
        return EXIT_FAILURE
