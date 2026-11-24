"""Contract tests for leo_shell.api.ShellApi using fakes only.

These tests must stay importable in a headless CI environment: no ``webview``
and none of the sibling runtime modules are imported here.  The fakes model
the public interfaces fixed in DESIGN.md (SettingsStore /
ConnectionCoordinator / DesktopUI).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from leo_shell.api import ShellApi


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


@dataclass
class FakeProfile:
    id: str
    name: str
    preset: str
    provider: str
    model: str
    base_url: str


class FakeSettingsStore:
    def __init__(self) -> None:
        self.saved_payloads: list[dict] = []
        self.deleted: list[str] = []
        self.appearances: list[tuple[str, str]] = []
        self.keys: dict[str, str] = {}
        self.state_override: dict | None = None
        self.fail_with: Exception | None = None
        self.active: FakeProfile | None = None

    def _maybe_fail(self) -> None:
        if self.fail_with is not None:
            raise self.fail_with

    def state_for_shell(self) -> dict:
        self._maybe_fail()
        if self.state_override is not None:
            return self.state_override
        # Deliberately carries stray api_key fields: the API must strip them.
        return {
            "appearance": {"theme": "deep-sea-molten-orange", "locale": "zh"},
            "themes": [{
                "id": "ink-autumn",
                "name": {"zh": "淡墨浓秋", "en": "Ink Autumn", "api_key": "sk-mustnotleak123"},
                "primary": "#9C3A28", "accent": "#E0CFB2",
                "dark_primary": "#D2705A", "dark_accent": "#3A2E24",
                "builtin": True, "api_key": "sk-mustnotleak123",
            }],
            "presets": [
                {
                    "id": "deepseek",
                    "label": "DeepSeek",
                    "provider": "chatgpt",
                    "model": "deepseek-chat",
                    "base_url": "https://api.deepseek.com",
                    "editable_base_url": True,
                    "api_key": "sk-mustnotleak123",
                }
            ],
            "profiles": [
                {
                    "id": "profile-1",
                    "name": "DeepSeek research",
                    "preset": "deepseek",
                    "provider": "chatgpt",
                    "model": "deepseek-chat",
                    "base_url": "https://api.deepseek.com",
                    "has_key": True,
                    "api_key": "sk-mustnotleak123",
                }
            ],
            "active_profile_id": "profile-1",
            "settings": {
                "preset": "deepseek",
                "provider": "chatgpt",
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com",
                "api_key": "sk-mustnotleak123",
            },
            "has_key": True,
        }

    def save_profile(self, payload: dict) -> FakeProfile:
        self._maybe_fail()
        if not isinstance(payload.get("model"), str) or not payload["model"]:
            raise ValueError("model is required")
        if payload.get("preset") not in ("deepseek", "custom"):
            raise ValueError("unknown preset")
        profile = FakeProfile(
            id=payload.get("profile_id") or "profile-new",
            name=payload.get("name") or "profile",
            preset=payload["preset"],
            provider="chatgpt",
            model=payload["model"],
            base_url=payload.get("base_url") or "https://api.deepseek.com",
        )
        self.saved_payloads.append(dict(payload))
        key = payload.get("api_key")
        if isinstance(key, str) and key:
            self.keys[profile.id] = key
        return profile

    def delete_profile(self, profile_id: str) -> None:
        self._maybe_fail()
        self.deleted.append(profile_id)
        self.keys.pop(profile_id, None)

    def active_profile(self):
        self._maybe_fail()
        return self.active

    def api_key_for(self, profile_id: str):
        return self.keys.get(profile_id)

    def load_appearance(self) -> dict:
        return {"theme": "deep-sea-molten-orange", "locale": "zh"}

    def save_appearance(self, theme: str, locale: str) -> dict:
        self._maybe_fail()
        if locale not in ("zh", "en"):
            raise ValueError("unsupported locale")
        if not isinstance(theme, str) or not theme:
            raise ValueError("unsupported theme")
        self.appearances.append((theme, locale))
        return {"theme": theme, "locale": locale}


class FakeCoordinator:
    def __init__(self) -> None:
        self.submissions: list[tuple[object, object, bool]] = []
        self.acknowledged: list[int] = []
        self.next_request_id = 7
        self.fail_with: Exception | None = None

    def submit(self, profile, api_key, *, requires_ack: bool) -> dict:
        if self.fail_with is not None:
            raise self.fail_with
        self.submissions.append((profile, api_key, requires_ack))
        return {"ok": True, "pending": True, "request_id": self.next_request_id}

    def acknowledge(self, request_id: int) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.acknowledged.append(request_id)


class FakeUI:
    def __init__(self, *, backend_loaded: bool = False) -> None:
        self._backend_loaded = backend_loaded
        self.refresh_calls = 0

    def refresh_injection(self) -> bool:
        self.refresh_calls += 1
        return True


def make_api(*, store=None, coordinator=None, ui=None, paths=None):
    store = store if store is not None else FakeSettingsStore()
    coordinator = coordinator if coordinator is not None else FakeCoordinator()
    api = ShellApi(store, coordinator, ui, paths=paths)
    return api, store, coordinator


VALID_SAVE_PAYLOAD = {
    "profile_id": None,
    "name": "DeepSeek research",
    "preset": "deepseek",
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-live-key-123",
    "activate": True,
}


# ---------------------------------------------------------------------------
# get_state
# ---------------------------------------------------------------------------


def test_get_state_contract_shape_and_secret_scrubbing():
    api, _, _ = make_api()
    state = api.get_state()

    assert set(state) == {
        "appearance",
        "themes",
        "presets",
        "profiles",
        "active_profile_id",
        "settings",
        "has_key",
    }
    assert state["appearance"] == {"locale": "zh", "theme": "deep-sea-molten-orange"}
    assert state["themes"] == [{
        "id": "ink-autumn", "name": {"zh": "淡墨浓秋", "en": "Ink Autumn"},
        "primary": "#9C3A28", "accent": "#E0CFB2",
        "dark_primary": "#D2705A", "dark_accent": "#3A2E24", "builtin": True,
    }]
    assert set(state["presets"][0]) == {"id", "label", "model", "base_url", "editable_base_url"}
    assert set(state["profiles"][0]) == {"id", "name", "preset", "model", "base_url", "has_key"}
    assert state["profiles"][0]["has_key"] is True
    assert set(state["settings"]) == {"preset", "model", "base_url"}
    assert state["active_profile_id"] == "profile-1"
    assert state["has_key"] is True

    serialized = json.dumps(state, ensure_ascii=False)
    assert "sk-mustnotleak123" not in serialized
    assert "api_key" not in serialized


@pytest.mark.parametrize("themes", [None, {}, "invalid", 42])
def test_get_state_invalid_theme_catalog_is_empty(themes):
    store = FakeSettingsStore()
    store.state_override = {"themes": themes}
    api, _, _ = make_api(store=store)
    assert api.get_state()["themes"] == []


def test_get_state_theme_metadata_types_and_nested_secret_scrubbing():
    store = FakeSettingsStore()
    store.state_override = {"themes": [
        None, "invalid", {"id": 42}, {"id": ""},
        {"id": "theme-x", "name": {"zh": "主题", "en": {"api_key": "secret"},
                                   "api_key": "secret"},
         "primary": {"api_key": "secret"}, "accent": "#123456",
         "dark_primary": [], "dark_accent": False, "builtin": "false", "api_key": "secret"},
        {"id": "theme-y", "name": "Simple name", "builtin": False},
    ]}
    api, _, _ = make_api(store=store)
    assert api.get_state()["themes"] == [
        {"id": "theme-x", "name": {"zh": "主题"}, "accent": "#123456"},
        {"id": "theme-y", "name": "Simple name", "builtin": False},
    ]


@pytest.mark.parametrize("bad_locale", ["fr", "", None, 42])
def test_get_state_coerces_invalid_locale(bad_locale):
    store = FakeSettingsStore()
    store.state_override = {
        "appearance": {"theme": "deep-sea-molten-orange", "locale": bad_locale},
        "presets": [],
        "profiles": [],
        "active_profile_id": None,
        "settings": None,
        "has_key": False,
    }
    api, _, _ = make_api(store=store)
    assert api.get_state()["appearance"]["locale"] == "zh"


def test_get_state_store_failure_is_collapsed_to_dict():
    store = FakeSettingsStore()
    store.fail_with = RuntimeError("disk on fire")
    api, _, _ = make_api(store=store)
    assert api.get_state() == {"ok": False, "message": "MODEL_SETTINGS_UNAVAILABLE"}


def test_get_state_non_dict_state_is_collapsed_to_dict():
    store = FakeSettingsStore()
    store.state_override = "not-a-dict"
    api, _, _ = make_api(store=store)
    assert api.get_state() == {"ok": False, "message": "MODEL_SETTINGS_UNAVAILABLE"}


# ---------------------------------------------------------------------------
# save_profile / save_settings
# ---------------------------------------------------------------------------


def test_save_profile_activate_submits_and_returns_request_id():
    api, store, coordinator = make_api()
    result = api.save_profile(dict(VALID_SAVE_PAYLOAD))

    assert result == {"ok": True, "pending": True, "request_id": 7}
    assert len(coordinator.submissions) == 1
    profile, api_key, requires_ack = coordinator.submissions[0]
    assert profile.id == "profile-new"
    assert api_key == "sk-live-key-123"  # resolved from the store, not the payload
    assert requires_ack is True
    assert store.saved_payloads[0]["preset"] == "deepseek"


def test_save_profile_without_activate_does_not_submit():
    api, _, coordinator = make_api()
    payload = dict(VALID_SAVE_PAYLOAD, activate=False)
    result = api.save_profile(payload)

    assert result == {"ok": True, "pending": False}
    assert coordinator.submissions == []


def test_save_profile_without_stored_key_submits_none():
    api, _, coordinator = make_api()
    payload = dict(VALID_SAVE_PAYLOAD, api_key="")
    result = api.save_profile(payload)

    assert result == {"ok": True, "pending": True, "request_id": 7}
    assert coordinator.submissions[0][1] is None


@pytest.mark.parametrize("payload", [None, "nope", 42, ["not", "a", "dict"]])
def test_save_profile_rejects_non_dict_payload(payload):
    api, store, coordinator = make_api()
    result = api.save_profile(payload)

    assert result == {"ok": False, "message": "MODEL_SETTINGS_INVALID"}
    assert store.saved_payloads == []
    assert coordinator.submissions == []


def test_save_profile_validation_failure_maps_to_public_code():
    api, _, coordinator = make_api()
    payload = dict(VALID_SAVE_PAYLOAD, model="")
    result = api.save_profile(payload)

    assert result == {"ok": False, "message": "MODEL_SETTINGS_INVALID"}
    assert coordinator.submissions == []


def test_save_profile_unexpected_store_error_maps_to_unavailable():
    store = FakeSettingsStore()
    store.fail_with = RuntimeError("io error")
    api, _, coordinator = make_api(store=store)

    assert api.save_profile(dict(VALID_SAVE_PAYLOAD)) == {
        "ok": False,
        "message": "MODEL_SETTINGS_UNAVAILABLE",
    }
    assert coordinator.submissions == []


def test_save_profile_submit_failure_is_collapsed():
    coordinator = FakeCoordinator()
    coordinator.fail_with = RuntimeError("closing")
    api, _, _ = make_api(coordinator=coordinator)

    result = api.save_profile(dict(VALID_SAVE_PAYLOAD))
    assert result["ok"] is False
    assert result["message"] == "MODEL_CONNECTION_FAILED"


def test_save_settings_is_an_alias_of_save_profile():
    api, _, coordinator = make_api()
    result = api.save_settings(dict(VALID_SAVE_PAYLOAD))

    assert result == {"ok": True, "pending": True, "request_id": 7}
    assert len(coordinator.submissions) == 1


# ---------------------------------------------------------------------------
# delete_profile
# ---------------------------------------------------------------------------


def test_delete_profile_success():
    api, store, _ = make_api()
    assert api.delete_profile({"profile_id": "profile-1"}) == {"ok": True}
    assert store.deleted == ["profile-1"]


@pytest.mark.parametrize(
    "payload",
    [{}, {"profile_id": ""}, {"profile_id": None}, {"profile_id": 3}, None, "x"],
)
def test_delete_profile_rejects_bad_payload(payload):
    api, store, _ = make_api()
    result = api.delete_profile(payload)

    assert result == {"ok": False, "message": "MODEL_SETTINGS_INVALID"}
    assert store.deleted == []


def test_delete_profile_unexpected_error_maps_to_unavailable():
    store = FakeSettingsStore()
    store.fail_with = RuntimeError("io error")
    api, _, _ = make_api(store=store)
    assert api.delete_profile({"profile_id": "profile-1"}) == {
        "ok": False,
        "message": "MODEL_SETTINGS_UNAVAILABLE",
    }


# ---------------------------------------------------------------------------
# save_appearance
# ---------------------------------------------------------------------------


def test_save_appearance_success_without_ui():
    api, store, _ = make_api()
    result = api.save_appearance({"theme": "amethyst-teal", "locale": "en"})

    assert result == {"ok": True, "appearance": {"theme": "amethyst-teal", "locale": "en"}}
    assert store.appearances == [("amethyst-teal", "en")]


def test_save_appearance_does_not_reach_into_the_window():
    """Saving is storage only: the upstream page it used to re-inject was removed on 2026-09-26."""
    ui = FakeUI(backend_loaded=True)
    api, _, _ = make_api(ui=ui)
    assert api.save_appearance({"theme": "amethyst-teal", "locale": "zh"})["ok"] is True
    assert ui.refresh_calls == 0


@pytest.mark.parametrize(
    "payload",
    [{"theme": "amethyst-teal", "locale": "fr"}, {"theme": "", "locale": "zh"}, None, "x"],
)
def test_save_appearance_rejects_invalid_payload(payload):
    api, store, _ = make_api()
    result = api.save_appearance(payload)

    assert result == {"ok": False, "message": "MODEL_SETTINGS_INVALID"}
    assert store.appearances == []


# ---------------------------------------------------------------------------
# acknowledge_connection
# ---------------------------------------------------------------------------


def test_acknowledge_connection_forwards_valid_request_id():
    api, _, coordinator = make_api()
    assert api.acknowledge_connection({"request_id": 7}) == {"ok": True}
    assert coordinator.acknowledged == [7]


@pytest.mark.parametrize(
    "payload",
    [
        {"request_id": 0},
        {"request_id": -3},
        {"request_id": True},
        {"request_id": 2.5},
        {"request_id": "abc"},
        {"request_id": None},
        {},
        None,
        "x",
    ],
)
def test_acknowledge_connection_ignores_invalid_ids(payload):
    api, _, coordinator = make_api()
    assert api.acknowledge_connection(payload) == {"ok": True}
    assert coordinator.acknowledged == []


def test_acknowledge_connection_swallows_coordinator_errors():
    coordinator = FakeCoordinator()
    coordinator.fail_with = RuntimeError("gone")
    api, _, _ = make_api(coordinator=coordinator)
    assert api.acknowledge_connection({"request_id": 7}) == {"ok": True}


# ---------------------------------------------------------------------------
# connect_keyless
# ---------------------------------------------------------------------------


KEYLESS_PROFILE = FakeProfile(
    id="profile-1",
    name="DeepSeek research",
    preset="deepseek",
    provider="chatgpt",
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
)


def test_connect_keyless_submits_the_active_profile_without_a_key():
    store = FakeSettingsStore()
    store.active = KEYLESS_PROFILE
    store.keys[KEYLESS_PROFILE.id] = "sk-mustnotleak123"
    api, _, coordinator = make_api(store=store)

    result = api.connect_keyless()

    assert result == {"ok": True, "pending": True, "request_id": 7}
    assert len(coordinator.submissions) == 1
    profile, api_key, requires_ack = coordinator.submissions[0]
    assert profile is KEYLESS_PROFILE
    # Keyless means keyless even when the profile has a stored credential.
    assert api_key is None
    assert requires_ack is False


def test_connect_keyless_without_a_profile_uses_an_unpersisted_bootstrap():
    api, store, coordinator = make_api()
    def forbid_key_read(profile_id):
        raise AssertionError("browsing must not read a credential")
    store.api_key_for = forbid_key_read
    assert api.connect_keyless() == {"ok": True, "pending": True, "request_id": 7}
    assert len(coordinator.submissions) == 1
    profile, api_key, requires_ack = coordinator.submissions[0]
    assert profile.entry_mode == "unconfigured"
    assert profile.id == ""
    assert profile.provider == "chatgpt" and profile.model == "deepseek-v4-flash"
    assert api_key is None and requires_ack is False
    assert store.active is None and store.saved_payloads == [] and store.keys == {}


def test_connect_keyless_store_failure_maps_to_unavailable():
    store = FakeSettingsStore()
    store.fail_with = RuntimeError("disk on fire")
    api, _, coordinator = make_api(store=store)
    assert api.connect_keyless() == {
        "ok": False,
        "message": "MODEL_SETTINGS_UNAVAILABLE",
    }
    assert coordinator.submissions == []


def test_connect_keyless_submit_failure_maps_to_connection_failed():
    store = FakeSettingsStore()
    store.active = KEYLESS_PROFILE
    coordinator = FakeCoordinator()
    coordinator.fail_with = RuntimeError("bridge down")
    api, _, _ = make_api(store=store, coordinator=coordinator)
    assert api.connect_keyless() == {
        "ok": False,
        "message": "MODEL_CONNECTION_FAILED",
    }


def test_connect_keyless_tolerates_a_coordinator_without_a_request_id():
    class SilentCoordinator(FakeCoordinator):
        def submit(self, profile, api_key, *, requires_ack: bool) -> dict:
            super().submit(profile, api_key, requires_ack=requires_ack)
            return {"ok": True}

    store = FakeSettingsStore()
    store.active = KEYLESS_PROFILE
    api, _, _ = make_api(store=store, coordinator=SilentCoordinator())
    assert api.connect_keyless() == {"ok": True, "pending": True, "request_id": None}


# ---------------------------------------------------------------------------
# local skills
# ---------------------------------------------------------------------------


def _paths_for(tmp_path):
    return SimpleNamespace(user=tmp_path / "user")


def _write_skill(root, name, content: str):
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(content, encoding="utf-8")


def test_scan_local_skills_collects_valid_skills(tmp_path):
    root = tmp_path / "user" / "user-skills"
    _write_skill(root, "beta", "no heading here")
    _write_skill(root, "alpha", "# Alpha Skill\n\ndoes things")
    (root / "gamma").mkdir(parents=True)  # no SKILL.md -> skipped
    (root / "stray.txt").write_text("x", encoding="utf-8")  # not a dir -> skipped
    bad = root / "bad"
    bad.mkdir()
    (bad / "SKILL.md").write_bytes(b"\xff\xfe invalid utf-8")  # skipped
    big = root / "big"
    big.mkdir()
    (big / "SKILL.md").write_bytes(b"x" * (1024 * 1024 + 1))  # too large -> skipped

    (root / ".hidden").mkdir()  # dot entry -> counted, never read

    api, _, _ = make_api(paths=_paths_for(tmp_path))
    # The workbench overlay calls this as scan_local_skills({}); accepting the
    # argument is part of the contract.
    result = api.scan_local_skills({})

    assert result["ok"] is True
    assert [skill["id"] for skill in result["skills"]] == ["alpha", "beta"]
    alpha, beta = result["skills"]
    assert alpha["name"] == "Alpha Skill"
    assert alpha["content"].startswith("# Alpha Skill")
    assert beta["name"] == "beta"
    assert result["hidden_count"] == 1
    assert {entry["folder"]: entry["code"] for entry in result["rejected"]} == {
        "gamma": "no_skill_md",
        "bad": "unreadable",
        "big": "too_large",
    }


def test_scan_local_skills_entries_satisfy_the_sync_filter(tmp_path):
    """leo-inject.js drops any entry missing folder/content/sha256."""

    root = tmp_path / "user" / "user-skills"
    _write_skill(root, "alpha", "# Alpha Skill\n\ndoes things")

    api, _, _ = make_api(paths=_paths_for(tmp_path))
    (entry,) = api.scan_local_skills({})["skills"]

    payload = "# Alpha Skill\n\ndoes things".encode("utf-8")
    assert entry["folder"] == "alpha"
    assert entry["byte_size"] == len(payload)
    assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
    assert entry["content"] == payload.decode("utf-8")


def test_scan_local_skills_missing_root_returns_empty(tmp_path):
    api, _, _ = make_api(paths=_paths_for(tmp_path))
    assert api.scan_local_skills() == {
        "ok": True,
        "skills": [],
        "rejected": [],
        "hidden_count": 0,
    }


def test_scan_local_skills_rejects_symlink_escape(tmp_path):
    root = tmp_path / "user" / "user-skills"
    root.mkdir(parents=True)
    outside = tmp_path / "outside"
    _write_skill(outside, "hidden", "# Hidden\nsecret content")
    link = root / "escape"
    try:
        os.symlink(outside / "hidden", link, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation requires privileges on this host")

    api, _, _ = make_api(paths=_paths_for(tmp_path))
    result = api.scan_local_skills()

    assert result["ok"] is True
    assert result["skills"] == []
    assert result["rejected"] == [{"folder": "escape", "code": "symlink"}]


def test_scan_local_skills_without_paths_fails_closed():
    api, _, _ = make_api()
    result = api.scan_local_skills()
    assert result == {"ok": False, "message": "LOCAL_SKILLS_UNAVAILABLE"}


def test_open_local_skills_folder_creates_and_opens(tmp_path, monkeypatch):
    opened: list[str] = []
    monkeypatch.setattr(os, "startfile", opened.append, raising=False)

    api, _, _ = make_api(paths=_paths_for(tmp_path))
    result = api.open_local_skills_folder()

    root = tmp_path / "user" / "user-skills"
    assert result == {"ok": True}
    assert root.is_dir()
    assert opened == [str(root)]


def test_open_local_skills_folder_failure_is_collapsed(tmp_path, monkeypatch):
    def explode(path):
        raise OSError("no shell")

    monkeypatch.setattr(os, "startfile", explode, raising=False)
    api, _, _ = make_api(paths=_paths_for(tmp_path))
    assert api.open_local_skills_folder() == {
        "ok": False,
        "message": "LOCAL_SKILLS_UNAVAILABLE",
    }


# ---------------------------------------------------------------------------
# extension-method fallback
# ---------------------------------------------------------------------------


UNIMPLEMENTED = (
    "choose_theme_file",
    "stage_theme_preview",
    "confirm_theme_preview",
    "discard_theme_preview",
    "delete_custom_theme",
    "list_entity_states",
    "mark_entity",
    "restore_entity",
    "forget_entity",
    "get_project_persona",
    "save_project_persona",
)


@pytest.mark.parametrize("name", UNIMPLEMENTED)
def test_unimplemented_extensions_return_contract_payload(name):
    api, _, _ = make_api()
    method = getattr(api, name)
    assert callable(method)
    # Entity operations became real persisted APIs in the inherited snapshot.
    # With no storage root they must still fail closed, now with the typed code.
    if name in {"list_entity_states", "mark_entity", "restore_entity", "forget_entity"}:
        assert method({"anything": 1}) == {"ok": False, "message": "ENTITY_STORE_UNAVAILABLE"}
    else:
        assert method({"anything": 1}) == {"ok": False, "message": "此功能暂未在新版壳中提供。"}


def test_unknown_attribute_still_raises_attribute_error():
    api, _, _ = make_api()
    with pytest.raises(AttributeError):
        api.totally_made_up_method


# ---------------------------------------------------------------------------
# thread safety smoke test
# ---------------------------------------------------------------------------


def test_concurrent_calls_are_serialized_and_never_raise():
    api, _, coordinator = make_api()
    results: list[dict] = []

    def worker(index: int) -> None:
        payload = dict(VALID_SAVE_PAYLOAD, activate=index % 2 == 0)
        results.append(api.save_profile(payload))
        results.append(api.get_state())
        results.append(api.acknowledge_connection({"request_id": index}))

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(1, 9)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 24
    # get_state returns the state shape (no "ok" key); save/ack return ok=True.
    assert all(
        isinstance(item, dict) and (item.get("ok") or "appearance" in item)
        for item in results
    )
    assert len(coordinator.submissions) == 4


@pytest.mark.parametrize("operation", ["restore_entity", "forget_entity"])
def test_entity_api_roundtrip_and_revision_guard(tmp_path, operation):
    api, _, _ = make_api(paths=_paths_for(tmp_path))
    assert api.list_entity_states() == {"ok": True, "entities": [], "next_offset": None}
    result = api.mark_entity({"entity_type": "session", "entity_id": "session-1",
                              "state": "archived", "title": "Scientific diagnostic"})
    assert result["ok"] is True
    record = result["entity"]
    assert record["revision"] == 1
    stored = tmp_path / "user" / "entity-states.json"
    before = stored.read_bytes()
    fresh, _, _ = make_api(paths=_paths_for(tmp_path))
    assert fresh.list_entity_states()["entities"] == [record]
    assert getattr(fresh, operation)({"entity_type": "session", "entity_id": "session-1",
                                     "expected_revision": 0}) == {
        "ok": False, "message": "ENTITY_REVISION_CONFLICT"}
    assert stored.read_bytes() == before
    assert getattr(fresh, operation)({"entity_type": "session", "entity_id": "session-1",
                                     "expected_revision": 1}) == {"ok": True}
    assert fresh.list_entity_states()["entities"] == []


@pytest.mark.parametrize("operation", ["list_entity_states", "mark_entity", "restore_entity", "forget_entity"])
def test_entity_api_corrupt_evidence_is_preserved(tmp_path, operation):
    paths = _paths_for(tmp_path)
    stored = tmp_path / "user" / "entity-states.json"
    stored.parent.mkdir(parents=True, exist_ok=True)
    raw = b'{"version":1,"entities": [CORRUPT]}'
    stored.write_bytes(raw)
    api, _, _ = make_api(paths=paths)
    payload = {"entity_type": "session", "entity_id": "session-1", "state": "archived",
               "expected_revision": 1}
    assert getattr(api, operation)(payload) == {"ok": False, "message": "ENTITY_STORE_UNAVAILABLE"}
    assert stored.read_bytes() == raw
