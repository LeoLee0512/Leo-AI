"""Startup-dispatch contract for leo_shell.app.Application._on_window_ready.

The shell always waits on the start page for an explicit entry/connection
action, including when a profile already has a key. The page owns read-only
configuration display; the window-ready callback must not read credentials or
start a model. ``--settings`` opens only the settings drawer.

Only fakes are used; pywebview is never imported.
"""

from __future__ import annotations

from dataclasses import dataclass

from leo_shell.app import Application, build_parser


@dataclass
class FakeProfile:
    id: str = "profile-1"
    provider: str = "chatgpt"
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"


class FakeSettings:
    def __init__(self, profile=None, key=None, *, key_error=None, profile_error=None):
        self._profile = profile
        self._key = key
        self._key_error = key_error
        self._profile_error = profile_error
        self.profile_reads = 0
        self.key_reads = 0

    def active_profile(self):
        self.profile_reads += 1
        if self._profile_error is not None:
            raise self._profile_error
        return self._profile

    def api_key_for(self, profile_id: str):
        self.key_reads += 1
        if self._key_error is not None:
            raise self._key_error
        return self._key


class FakeCoordinator:
    def __init__(self) -> None:
        self.submissions: list[tuple[object, object, bool]] = []

    def submit(self, profile, api_key, *, requires_ack: bool) -> dict:
        self.submissions.append((profile, api_key, requires_ack))
        return {"ok": True, "pending": True, "request_id": 1}


class FakeWindow:
    def __init__(self) -> None:
        self.statuses: list[tuple[str, bool]] = []
        self.settings_opened = 0
        self.navigations: list[str] = []

    def publish_status(self, message: str, *, error: bool = False) -> None:
        self.statuses.append((message, error))

    def open_settings(self) -> None:
        self.settings_opened += 1

    def navigate(self, url: str) -> None:
        self.navigations.append(url)


def make_app(argv=()):
    return Application(build_parser().parse_args(list(argv)))


def run_ready(app, settings, *, window=None, coordinator=None):
    window = window if window is not None else FakeWindow()
    coordinator = coordinator if coordinator is not None else FakeCoordinator()
    app._on_window_ready(window, settings, coordinator)
    assert settings.profile_reads == 0
    assert settings.key_reads == 0
    assert window.navigations == []
    return window, coordinator


def test_profile_with_key_waits_for_explicit_entry():
    profile = FakeProfile()
    window, coordinator = run_ready(
        make_app(), FakeSettings(profile, "sk-live-key-123")
    )

    assert coordinator.submissions == []
    assert window.settings_opened == 0
    assert window.statuses == []


def test_profile_without_key_stays_on_the_splash_page():
    window, coordinator = run_ready(make_app(), FakeSettings(FakeProfile(), None))

    assert coordinator.submissions == []
    assert window.settings_opened == 0
    # No status code: the page renders its own localized guidance from
    # get_state().has_key, and none of the five public codes fits "not
    # configured yet".
    assert window.statuses == []


def test_profile_with_empty_key_is_treated_as_no_key():
    window, coordinator = run_ready(make_app(), FakeSettings(FakeProfile(), ""))

    assert coordinator.submissions == []
    assert window.settings_opened == 0


def test_unreadable_key_does_not_fall_through_to_keyless_navigation():
    settings = FakeSettings(FakeProfile(), key_error=RuntimeError("dpapi refused"))
    window, coordinator = run_ready(make_app(), settings)

    assert coordinator.submissions == []
    assert window.settings_opened == 0


def test_no_profile_keeps_entry_choice_without_an_error_banner():
    window, coordinator = run_ready(make_app(), FakeSettings(None))

    assert coordinator.submissions == []
    assert window.settings_opened == 0
    assert window.statuses == []


def test_settings_flag_never_auto_connects_even_with_a_key():
    window, coordinator = run_ready(
        make_app(["--settings"]), FakeSettings(FakeProfile(), "sk-live-key-123")
    )

    assert coordinator.submissions == []
    assert window.settings_opened == 1


def test_settings_drawer_failure_still_reports_the_public_code():
    class FailingWindow(FakeWindow):
        def open_settings(self):
            super().open_settings()
            raise RuntimeError("drawer unavailable")

    settings = FakeSettings(profile_error=RuntimeError("must not read the store"))
    window, coordinator = run_ready(
        make_app(["--settings"]), settings, window=FailingWindow()
    )

    assert coordinator.submissions == []
    assert window.statuses == [("MODEL_SETTINGS_UNAVAILABLE", True)]
    assert window.settings_opened == 1
