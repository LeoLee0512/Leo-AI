"""Tests for leo_shell.settings_store (profiles, settings mirror, appearance)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from leo_shell.paths import AppPaths
from leo_shell.secrets_store import SecretsStore
from leo_shell.settings_store import (
    PRESETS,
    Profile,
    SettingsInvalid,
    SettingsStore,
)

_TEST_KEY = "sk-test-fixture-key-0000000000000001"


@pytest.fixture()
def paths(tmp_path: Path) -> AppPaths:
    return AppPaths.from_root(tmp_path)


@pytest.fixture()
def secrets(paths: AppPaths) -> SecretsStore:
    return SecretsStore(paths.credentials)


@pytest.fixture()
def store(paths: AppPaths, secrets: SecretsStore) -> SettingsStore:
    return SettingsStore(paths, secrets)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# defaults and presets


def test_presets_contract() -> None:
    ids = [preset["id"] for preset in PRESETS]
    assert "deepseek" in ids  # the shell's default selection when no profile exists
    assert len(ids) == len(set(ids))
    for preset in PRESETS:
        for key in ("id", "label", "provider", "model", "base_url", "editable_base_url"):
            assert key in preset


def test_state_defaults(store: SettingsStore) -> None:
    state = store.state_for_shell()
    assert state["profiles"] == []
    assert state["active_profile_id"] is None
    assert state["has_key"] is False
    assert state["settings"] == {
        "preset": "deepseek",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
    }
    assert state["appearance"] == {"theme": "deep-sea-molten-orange", "locale": "zh"}
    preset_keys = {"id", "label", "model", "base_url", "editable_base_url"}
    # Cloud presets retain the original exact public shape. The inherited local
    # preset explicitly advertises its keyless contract; no arbitrary keys leak.
    for preset in state["presets"]:
        if preset["id"] == "local-qwen":
            assert set(preset) == preset_keys | {"requires_key"}
            assert preset["requires_key"] is False
            assert preset["editable_base_url"] is False
            assert preset["model"] == "local-qwen3-4b"
            assert preset["base_url"] == "http://127.0.0.1:8080/v1"
        else:
            assert set(preset) == preset_keys
    assert state["presets"][0]["id"] == "deepseek"


# ---------------------------------------------------------------------------
# save_profile


def test_save_profile_creates_and_activates(store: SettingsStore, paths: AppPaths) -> None:
    profile = store.save_profile(
        {
            "profile_id": None,
            "name": "Work",
            "preset": "deepseek",
            "model": "deepseek-chat",
            "base_url": "",
            "api_key": _TEST_KEY,
            "activate": True,
        }
    )
    assert profile.id.startswith("profile-") and len(profile.id) == len("profile-") + 32
    assert profile.provider == "chatgpt"
    assert profile.base_url == "https://api.deepseek.com"  # preset default filled in

    doc = _read_json(paths.user / "model-profiles.json")
    assert doc["schema_version"] == 1
    assert doc["active_profile_id"] == profile.id
    assert [p["id"] for p in doc["profiles"]] == [profile.id]
    assert set(doc["profiles"][0]) == {"base_url", "id", "model", "name", "preset", "provider"}

    mirror = _read_json(paths.user / "settings.json")
    assert mirror == {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "preset": "deepseek",
        "provider": "chatgpt",
        "schema_version": 1,
    }
    assert store.api_key_for(profile.id) == _TEST_KEY


def test_save_profile_empty_id_is_create_sentinel(store: SettingsStore) -> None:
    profile = store.save_profile(
        {"profile_id": "", "preset": "qwen", "model": "qwen-plus", "activate": True}
    )
    assert profile.id != ""
    assert profile.id.startswith("profile-")


def test_save_profile_updates_existing(store: SettingsStore) -> None:
    profile = store.save_profile(
        {"profile_id": None, "preset": "deepseek", "model": "deepseek-chat", "activate": True}
    )
    updated = store.save_profile(
        {
            "profile_id": profile.id,
            "preset": "kimi",
            "model": "moonshot-v1-8k",
            "base_url": "https://api.moonshot.cn/v1",
            "activate": True,
        }
    )
    assert updated.id == profile.id
    assert updated.preset == "kimi"
    assert store.active_profile().preset == "kimi"  # type: ignore[union-attr]
    assert len(store.state_for_shell()["profiles"]) == 1


def test_save_profile_without_activate_keeps_previous_active(store: SettingsStore) -> None:
    first = store.save_profile(
        {"profile_id": None, "preset": "deepseek", "model": "deepseek-chat", "activate": True}
    )
    store.save_profile(
        {"profile_id": None, "preset": "qwen", "model": "qwen-plus", "activate": False}
    )
    assert store.active_profile().id == first.id  # type: ignore[union-attr]


def test_save_profile_first_save_auto_activates(store: SettingsStore) -> None:
    profile = store.save_profile(
        {"profile_id": None, "preset": "qwen", "model": "qwen-plus", "activate": False}
    )
    assert store.active_profile().id == profile.id  # type: ignore[union-attr]


def test_state_never_contains_api_key(store: SettingsStore) -> None:
    store.save_profile(
        {
            "profile_id": None,
            "preset": "deepseek",
            "model": "deepseek-chat",
            "api_key": _TEST_KEY,
            "activate": True,
        }
    )
    state = store.state_for_shell()
    assert state["has_key"] is True
    assert state["profiles"][0]["has_key"] is True
    assert _TEST_KEY not in json.dumps(state, ensure_ascii=False)


def test_profiles_file_never_contains_api_key(store: SettingsStore, paths: AppPaths) -> None:
    store.save_profile(
        {
            "profile_id": None,
            "preset": "deepseek",
            "model": "deepseek-chat",
            "api_key": _TEST_KEY,
            "activate": True,
        }
    )
    assert _TEST_KEY not in (paths.user / "model-profiles.json").read_text(encoding="utf-8")
    assert _TEST_KEY not in (paths.user / "settings.json").read_text(encoding="utf-8")


def test_save_profile_custom_preset(store: SettingsStore) -> None:
    profile = store.save_profile(
        {
            "profile_id": None,
            "preset": "custom",
            "model": "my-model",
            "base_url": "https://llm.example.com/v1",
            "activate": True,
        }
    )
    assert profile.provider == "chatgpt"
    assert profile.base_url == "https://llm.example.com/v1"


# ---------------------------------------------------------------------------
# validation


@pytest.mark.parametrize(
    "payload",
    [
        {"preset": "no-such-preset", "model": "m"},
        {"preset": "deepseek", "model": ""},
        {"preset": "deepseek", "model": "   "},
        {"preset": "deepseek", "model": "m" * 201},
        {"preset": "deepseek", "model": "m", "base_url": "ftp://example.com"},
        {"preset": "deepseek", "model": "m", "base_url": "example.com"},
        {"preset": "deepseek", "model": "m", "base_url": "http://user:pass@example.com"},
        {"preset": "deepseek", "model": "m", "base_url": "https://example.com/#frag"},
        {"preset": "deepseek", "model": "m", "name": "n" * 81},
        {"preset": "custom", "model": "m", "base_url": ""},
        {"profile_id": "profile-does-not-exist", "preset": "deepseek", "model": "m"},
    ],
)
def test_save_profile_validation_errors(store: SettingsStore, payload: dict) -> None:
    with pytest.raises(SettingsInvalid):
        store.save_profile(payload)
    assert store.state_for_shell()["profiles"] == []


def test_settings_invalid_is_value_error() -> None:
    assert issubclass(SettingsInvalid, ValueError)


def test_corrupt_profiles_file_raises(store: SettingsStore, paths: AppPaths) -> None:
    paths.user.mkdir(parents=True, exist_ok=True)
    (paths.user / "model-profiles.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(SettingsInvalid):
        store.state_for_shell()


# ---------------------------------------------------------------------------
# legacy format compatibility (structure of the existing user/*.json files)


def test_reads_legacy_profile_format(store: SettingsStore, paths: AppPaths) -> None:
    paths.user.mkdir(parents=True, exist_ok=True)
    legacy_id = "profile-73c0f0438a84cc93214f6a868fd3a479"
    (paths.user / "model-profiles.json").write_text(
        json.dumps(
            {
                "active_profile_id": legacy_id,
                "profiles": [
                    {
                        "base_url": "https://api.deepseek.com",
                        "id": legacy_id,
                        "model": "deepseek",
                        "name": "deepseek",
                        "preset": "deepseek",
                        "provider": "chatgpt",
                    }
                ],
                "schema_version": 1,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    active = store.active_profile()
    assert isinstance(active, Profile)
    assert active.id == legacy_id
    assert active.provider == "chatgpt"
    state = store.state_for_shell()
    assert state["settings"]["model"] == "deepseek"
    assert state["profiles"][0]["has_key"] is False


def test_stale_active_id_is_dropped(store: SettingsStore, paths: AppPaths) -> None:
    paths.user.mkdir(parents=True, exist_ok=True)
    (paths.user / "model-profiles.json").write_text(
        json.dumps({"schema_version": 1, "active_profile_id": "profile-gone", "profiles": []}),
        encoding="utf-8",
    )
    assert store.active_profile() is None
    assert store.state_for_shell()["active_profile_id"] is None


# ---------------------------------------------------------------------------
# delete_profile


def test_delete_profile(store: SettingsStore, paths: AppPaths) -> None:
    profile = store.save_profile(
        {
            "profile_id": None,
            "preset": "deepseek",
            "model": "deepseek-chat",
            "api_key": _TEST_KEY,
            "activate": True,
        }
    )
    store.delete_profile(profile.id)
    assert store.state_for_shell()["profiles"] == []
    assert store.active_profile() is None
    assert store.api_key_for(profile.id) is None
    # settings.json falls back to the default preset mirror
    mirror = _read_json(paths.user / "settings.json")
    assert mirror["preset"] == "deepseek"
    assert mirror["provider"] == "chatgpt"


def test_delete_unknown_profile_raises(store: SettingsStore) -> None:
    with pytest.raises(SettingsInvalid):
        store.delete_profile("profile-missing")


# ---------------------------------------------------------------------------
# atomic writes


def test_writes_are_compact_sorted_and_leave_no_tmp(
    store: SettingsStore, paths: AppPaths
) -> None:
    store.save_profile(
        {"profile_id": None, "preset": "deepseek", "model": "deepseek-chat", "activate": True}
    )
    raw = (paths.user / "model-profiles.json").read_text(encoding="utf-8")
    assert "\n" not in raw and '": ' not in raw  # compact separators
    assert raw == json.dumps(json.loads(raw), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert list(paths.user.glob("*.tmp")) == []


def test_leftover_tmp_file_is_ignored(store: SettingsStore, paths: AppPaths) -> None:
    paths.user.mkdir(parents=True, exist_ok=True)
    (paths.user / "model-profiles.json.tmp").write_text("{garbage", encoding="utf-8")
    assert store.state_for_shell()["profiles"] == []


# ---------------------------------------------------------------------------
# appearance


def test_appearance_roundtrip(store: SettingsStore, paths: AppPaths) -> None:
    result = store.save_appearance("amethyst-teal", "en")
    assert result == {"theme": "amethyst-teal", "locale": "en"}
    assert store.load_appearance() == {"theme": "amethyst-teal", "locale": "en"}
    payload = _read_json(paths.user / "appearance.json")
    assert set(payload) == {"schema_version", "theme", "locale"}
    assert payload["schema_version"] == 1


def test_appearance_rejects_unknown_values(store: SettingsStore) -> None:
    with pytest.raises(SettingsInvalid):
        store.save_appearance("no-such-theme", "zh")
    with pytest.raises(SettingsInvalid):
        store.save_appearance("deep-sea-molten-orange", "fr")
    assert store.load_appearance() == {"theme": "deep-sea-molten-orange", "locale": "zh"}


def test_appearance_corrupt_file_falls_back_to_defaults(
    store: SettingsStore, paths: AppPaths
) -> None:
    paths.user.mkdir(parents=True, exist_ok=True)
    (paths.user / "appearance.json").write_text("{broken", encoding="utf-8")
    assert store.load_appearance() == {"theme": "deep-sea-molten-orange", "locale": "zh"}


def test_appearance_unknown_stored_theme_falls_back(
    store: SettingsStore, paths: AppPaths
) -> None:
    paths.user.mkdir(parents=True, exist_ok=True)
    (paths.user / "appearance.json").write_text(
        json.dumps({"schema_version": 1, "theme": "retired-theme", "locale": "en"}),
        encoding="utf-8",
    )
    assert store.load_appearance() == {"theme": "deep-sea-molten-orange", "locale": "en"}


def _write_themes(paths: AppPaths, document: dict) -> None:
    paths.theme.mkdir(parents=True, exist_ok=True)
    (paths.theme / "themes.json").write_text(json.dumps(document), encoding="utf-8")


def test_first_run_default_comes_from_themes_json(
    store: SettingsStore, paths: AppPaths
) -> None:
    """Shipping a different default must not require a rebuild."""
    _write_themes(
        paths,
        {
            "default_theme": "ink-autumn",
            "themes": [{"id": "ink-autumn"}, {"id": "deep-sea-molten-orange"}],
        },
    )
    assert store.load_appearance() == {"theme": "ink-autumn", "locale": "zh"}


def test_first_run_default_ignores_unregistered_declaration(
    store: SettingsStore, paths: AppPaths
) -> None:
    """A typo in ``default_theme`` degrades; it never persists an unusable id."""
    _write_themes(paths, {"default_theme": "ink-autum", "themes": [{"id": "ink-autumn"}]})
    assert store.load_appearance()["theme"] == "deep-sea-molten-orange"


def test_stored_choice_survives_a_new_shipped_default(
    store: SettingsStore, paths: AppPaths
) -> None:
    """Changing the shipped default must not move anyone off their own theme."""
    _write_themes(
        paths,
        {
            "default_theme": "ink-autumn",
            "themes": [{"id": "ink-autumn"}, {"id": "amethyst-teal"}],
        },
    )
    store.save_appearance("amethyst-teal", "en")
    assert store.load_appearance() == {"theme": "amethyst-teal", "locale": "en"}


def test_appearance_reads_themes_json(store: SettingsStore, paths: AppPaths) -> None:
    themes_dir = paths.theme
    themes_dir.mkdir(parents=True)
    (themes_dir / "themes.json").write_text(
        json.dumps({"themes": [{"id": "custom-theme-x"}]}),
        encoding="utf-8",
    )
    assert store.save_appearance("custom-theme-x", "zh") == {
        "theme": "custom-theme-x",
        "locale": "zh",
    }


@pytest.mark.parametrize("locale", ["zh", "en"])
def test_shipped_theme_catalog_and_ink_autumn_restart(
    store: SettingsStore, paths: AppPaths, secrets: SecretsStore, locale: str
) -> None:
    registry = _read_json(Path(__file__).resolve().parents[2] / "stage" / "themes.json")
    _write_themes(paths, registry)
    initial = store.state_for_shell()
    assert initial["themes"] == registry["themes"]
    assert initial["appearance"] == {"theme": "ink-autumn", "locale": "zh"}
    ink_autumn = next(item for item in initial["themes"] if item["id"] == "ink-autumn")
    assert ink_autumn["name"] == {"zh": "淡墨浓秋", "en": "Ink Autumn"}

    store.save_appearance("ink-autumn", locale)
    reopened = SettingsStore(paths, secrets)
    assert reopened.load_appearance() == {"theme": "ink-autumn", "locale": locale}
    assert reopened.state_for_shell()["themes"] == registry["themes"]


def test_theme_catalog_contains_only_display_metadata(
    store: SettingsStore, paths: AppPaths
) -> None:
    _write_themes(paths, {"themes": [
        {"id": "theme-x", "name": {"zh": "主题", "en": {"api_key": "hidden"},
                                   "api_key": "hidden"},
         "primary": "#123456", "accent": {"api_key": "hidden"},
         "builtin": True, "api_key": "hidden"},
        {"id": None}, "theme-y",
    ]})
    assert store.state_for_shell()["themes"] == [
        {"id": "theme-x", "name": {"zh": "主题"}, "primary": "#123456", "builtin": True}
    ]


@pytest.mark.parametrize("registry", [None, {}, {"themes": "invalid"}])
def test_unavailable_theme_catalog_is_empty(
    store: SettingsStore, paths: AppPaths, registry: dict | None
) -> None:
    if registry is not None:
        _write_themes(paths, registry)
    assert store.state_for_shell()["themes"] == []
