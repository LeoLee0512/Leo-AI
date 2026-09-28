"""Settings, model profile and appearance persistence.

Three JSON documents under ``user/``:

- ``model-profiles.json``: source of truth for profiles and the active
  selection (``{"schema_version": 1, "active_profile_id", "profiles": [...]}``).
- ``settings.json``: mirror of the effective connection settings for the
  daemon side (active profile, or the default preset when none is active).
- ``appearance.json``: ``{"schema_version": 1, "theme", "locale"}`` only.

All writes are atomic (tmp file + ``os.replace``), UTF-8, compact and with
sorted keys.  Reads of the profile document are lenient about individual
fields but raise :class:`SettingsInvalid` for unparseable files, so corrupt
user data is never silently overwritten.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from secrets import token_hex
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from .paths import AppPaths

if TYPE_CHECKING:  # avoid a hard import cycle; secrets_store never imports us
    from .secrets_store import SecretsStore

__all__ = ["PRESETS", "Profile", "SettingsInvalid", "SettingsStore"]

_SCHEMA_VERSION = 1
_DEFAULT_PRESET_ID = "deepseek"
_LOCAL_PRESET_ID = "local-qwen"
# Last-resort theme id, used only when ``theme/themes.json`` is missing or
# unreadable.  The shipped default lives in that file's ``default_theme`` and is
# resolved by ``_default_theme_id()`` -- a theme is a theme-layer fact, and the
# settings store has no business naming the one that happens to ship first.
_FALLBACK_THEME = "deep-sea-molten-orange"
_BUILTIN_THEME_IDS = frozenset({"deep-sea-molten-orange", "amethyst-teal"})
_LOCALES = frozenset({"zh", "en"})
_DEFAULT_LOCALE = "zh"
_MAX_MODEL_LENGTH = 200
_MAX_NAME_LENGTH = 80
_MAX_FILE_BYTES = 1024 * 1024

PRESETS: tuple[dict, ...] = (
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "provider": "chatgpt",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "editable_base_url": True,
    },
    {
        "id": "qwen",
        "label": "Qwen",
        "provider": "chatgpt",
        "model": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "editable_base_url": True,
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "provider": "chatgpt",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "editable_base_url": True,
    },
    {
        "id": "zhipu",
        "label": "智谱 GLM",
        "provider": "chatgpt",
        "model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "editable_base_url": True,
    },
    {
        "id": "kimi",
        "label": "Kimi",
        "provider": "chatgpt",
        "model": "moonshot-v1-8k",
        "base_url": "https://api.moonshot.cn/v1",
        "editable_base_url": True,
    },
    {
        "id": "ark",
        "label": "火山方舟 Ark",
        "provider": "ark",
        "model": "doubao-seed-1-6-250615",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "editable_base_url": True,
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "provider": "claude",
        "model": "claude-3-5-haiku-20241022",
        "base_url": "https://api.anthropic.com",
        "editable_base_url": True,
    },
    {
        "id": "gemini",
        "label": "Google Gemini",
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "base_url": "https://generativelanguage.googleapis.com",
        "editable_base_url": True,
    },
    {
        "id": _LOCAL_PRESET_ID,
        "label": "本地 Qwen3 · 无需密钥",
        "provider": "local-llama",
        "model": "local-qwen3-4b",
        "base_url": "http://127.0.0.1:8080/v1",
        "editable_base_url": False,
        "requires_key": False,
    },
    {
        "id": "custom",
        "label": "自定义（OpenAI 兼容）",
        "provider": "chatgpt",
        "model": "",
        "base_url": "",
        "editable_base_url": True,
    },
)

_PRESETS_BY_ID = {preset["id"]: preset for preset in PRESETS}
_PROFILE_ID_PREFIX = "profile-"


class SettingsInvalid(ValueError):
    """Raised when a settings payload or document fails validation."""


@dataclass
class Profile:
    id: str
    name: str
    preset: str
    provider: str
    model: str
    base_url: str

    @property
    def requires_key(self) -> bool:
        """Credential policy comes from the built-in preset, never stored input."""
        return self.preset != _LOCAL_PRESET_ID


def _write_json_atomic(path: Path, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _read_json_strict(path: Path) -> Any | None:
    """Parse *path*; ``None`` when missing, ``SettingsInvalid`` when corrupt."""
    try:
        if not path.is_file():
            return None
        if path.stat().st_size > _MAX_FILE_BYTES:
            raise SettingsInvalid(f"settings file too large: {path.name}")
        raw = path.read_bytes()
    except OSError as exc:
        raise SettingsInvalid(f"settings file unreadable: {path.name}") from exc
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise SettingsInvalid(f"settings file corrupt: {path.name}") from exc


def _read_json_lenient(path: Path) -> Any | None:
    """Parse *path*; ``None`` on any failure (for non-critical documents)."""
    try:
        if not path.is_file() or path.stat().st_size > _MAX_FILE_BYTES:
            return None
        return json.loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _validate_base_url(value: str) -> None:
    try:
        parts = urlsplit(value)
        hostname = parts.hostname
    except ValueError as exc:
        raise SettingsInvalid("base_url is not a valid URL") from exc
    if parts.scheme.lower() not in ("http", "https") or not hostname:
        raise SettingsInvalid("base_url must be an http(s):// URL")
    if parts.username is not None or parts.password is not None:
        raise SettingsInvalid("base_url must not contain userinfo")
    if parts.fragment:
        raise SettingsInvalid("base_url must not contain a fragment")


def _profile_from_raw(item: Any) -> Profile | None:
    """Leniently coerce one stored profile; ``None`` when it has no id."""
    if not isinstance(item, dict):
        return None
    profile_id = item.get("id")
    if not isinstance(profile_id, str) or not profile_id:
        return None
    preset = item.get("preset")
    preset = preset if isinstance(preset, str) and preset else "custom"
    provider = item.get("provider")
    if not isinstance(provider, str) or not provider:
        provider = _PRESETS_BY_ID.get(preset, _PRESETS_BY_ID["custom"])["provider"]
    name = item.get("name")
    model = item.get("model")
    base_url = item.get("base_url")
    if preset == _LOCAL_PRESET_ID:
        local = _PRESETS_BY_ID[_LOCAL_PRESET_ID]
        if (provider, model, base_url) != (local["provider"], local["model"], local["base_url"]):
            raise SettingsInvalid("the built-in local profile has invalid connection settings")
    return Profile(
        id=profile_id,
        name=name if isinstance(name, str) else "",
        preset=preset,
        provider=provider,
        model=model if isinstance(model, str) else "",
        base_url=base_url if isinstance(base_url, str) else "",
    )


def _profile_to_raw(profile: Profile) -> dict:
    return {
        "base_url": profile.base_url,
        "id": profile.id,
        "model": profile.model,
        "name": profile.name,
        "preset": profile.preset,
        "provider": profile.provider,
    }


class SettingsStore:
    """Thread-safe persistence for profiles, settings mirror and appearance."""

    def __init__(self, paths: AppPaths, secrets: "SecretsStore") -> None:
        self._paths = paths
        self._secrets = secrets
        self._lock = threading.RLock()
        self._profiles_file = paths.user / "model-profiles.json"
        self._settings_file = paths.user / "settings.json"
        self._appearance_file = paths.user / "appearance.json"

    # ------------------------------------------------------------------
    # profile document helpers

    def _load_profiles_doc(self) -> dict:
        data = _read_json_strict(self._profiles_file)
        if data is None:
            return {
                "schema_version": _SCHEMA_VERSION,
                "active_profile_id": None,
                "profiles": [],
            }
        if not isinstance(data, dict):
            raise SettingsInvalid("model-profiles.json must contain an object")
        raw_profiles = data.get("profiles", [])
        if not isinstance(raw_profiles, list):
            raise SettingsInvalid("model-profiles.json: profiles must be a list")
        profiles = []
        for item in raw_profiles:
            profile = _profile_from_raw(item)
            if profile is not None:
                profiles.append(profile)
        active = data.get("active_profile_id")
        if not isinstance(active, str) or not active:
            active = None
        if active is not None and all(p.id != active for p in profiles):
            active = None
        return {
            "schema_version": _SCHEMA_VERSION,
            "active_profile_id": active,
            "profiles": profiles,
        }

    def _write_profiles_doc(self, doc: dict) -> None:
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "active_profile_id": doc["active_profile_id"],
            "profiles": [_profile_to_raw(p) for p in doc["profiles"]],
        }
        _write_json_atomic(self._profiles_file, payload)
        self._write_settings_mirror(doc)

    def _write_settings_mirror(self, doc: dict) -> None:
        active = self._active_from_doc(doc)
        if active is not None:
            mirror = {
                "base_url": active.base_url,
                "model": active.model,
                "preset": active.preset,
                "provider": active.provider,
            }
        else:
            preset = _PRESETS_BY_ID[_DEFAULT_PRESET_ID]
            mirror = {
                "base_url": preset["base_url"],
                "model": preset["model"],
                "preset": preset["id"],
                "provider": preset["provider"],
            }
        mirror["schema_version"] = _SCHEMA_VERSION
        _write_json_atomic(self._settings_file, mirror)

    @staticmethod
    def _active_from_doc(doc: dict) -> Profile | None:
        active_id = doc.get("active_profile_id")
        if not active_id:
            return None
        for profile in doc["profiles"]:
            if profile.id == active_id:
                return profile
        return None

    # ------------------------------------------------------------------
    # public API

    def state_for_shell(self) -> dict:
        """Return the ``get_state`` payload; never includes any API key."""
        with self._lock:
            doc = self._load_profiles_doc()
            appearance = self.load_appearance()
            active = self._active_from_doc(doc)
            presets = [
                {
                    "id": preset["id"],
                    "label": preset["label"],
                    "model": preset["model"],
                    "base_url": preset["base_url"],
                    "editable_base_url": bool(preset["editable_base_url"]),
                    **({"requires_key": False} if preset.get("requires_key") is False else {}),
                }
                for preset in PRESETS
            ]
            profiles = [
                {
                    "id": profile.id,
                    "name": profile.name,
                    "preset": profile.preset,
                    "model": profile.model,
                    "base_url": profile.base_url,
                    "has_key": self.api_key_for(profile.id) is not None,
                    **({"requires_key": False} if not profile.requires_key else {}),
                }
                for profile in doc["profiles"]
            ]
            if active is not None:
                settings = {
                    "preset": active.preset,
                    "model": active.model,
                    "base_url": active.base_url,
                    **({"requires_key": False} if not active.requires_key else {}),
                }
                has_key = self.api_key_for(active.id) is not None
            else:
                preset = _PRESETS_BY_ID[_DEFAULT_PRESET_ID]
                settings = {
                    "preset": preset["id"],
                    "model": preset["model"],
                    "base_url": preset["base_url"],
                }
                has_key = False
            return {
                "appearance": appearance,
                "themes": self._theme_catalog(),
                "presets": presets,
                "profiles": profiles,
                "active_profile_id": active.id if active is not None else None,
                "settings": settings,
                "has_key": has_key,
            }

    def save_profile(self, payload: dict) -> Profile:
        """Create or update a profile; raises ``SettingsInvalid`` on bad input."""
        if not isinstance(payload, dict):
            raise SettingsInvalid("payload must be an object")
        with self._lock:
            doc = self._load_profiles_doc()
            profile_id = payload.get("profile_id")
            if profile_id is not None and not isinstance(profile_id, str):
                raise SettingsInvalid("profile_id must be a string or null")
            # An empty profile_id is the shell's "create new" sentinel.
            existing: Profile | None = None
            if profile_id:
                for profile in doc["profiles"]:
                    if profile.id == profile_id:
                        existing = profile
                        break
                if existing is None:
                    raise SettingsInvalid("unknown profile_id")

            preset_id = payload.get("preset", existing.preset if existing else None)
            if not isinstance(preset_id, str) or preset_id not in _PRESETS_BY_ID:
                raise SettingsInvalid(f"unknown preset: {preset_id!r}")
            preset = _PRESETS_BY_ID[preset_id]

            api_key = payload.get("api_key")
            if preset_id == _LOCAL_PRESET_ID:
                if api_key is not None and (not isinstance(api_key, str) or api_key.strip()):
                    raise SettingsInvalid("the built-in local model does not accept an API key")

            model = payload.get("model", existing.model if existing else preset["model"])
            if not isinstance(model, str):
                raise SettingsInvalid("model must be a string")
            model = model.strip()
            if not model:
                raise SettingsInvalid("model must not be empty")
            if len(model) > _MAX_MODEL_LENGTH:
                raise SettingsInvalid("model is too long")

            base_url = payload.get(
                "base_url", existing.base_url if existing else preset["base_url"]
            )
            if not isinstance(base_url, str):
                raise SettingsInvalid("base_url must be a string")
            base_url = base_url.strip()
            if base_url:
                _validate_base_url(base_url)
            else:
                base_url = preset["base_url"]
                if not base_url:
                    raise SettingsInvalid("base_url must not be empty for this preset")

            if preset_id == _LOCAL_PRESET_ID and (model != preset["model"] or base_url != preset["base_url"]):
                raise SettingsInvalid("the built-in local model and endpoint are fixed")

            name = payload.get("name", existing.name if existing else preset["label"])
            if not isinstance(name, str):
                raise SettingsInvalid("name must be a string")
            name = name.strip()
            if not name:
                name = preset["label"]
            if len(name) > _MAX_NAME_LENGTH:
                raise SettingsInvalid("name is too long")

            if existing is None:
                profile = Profile(
                    id=_PROFILE_ID_PREFIX + token_hex(16),
                    name=name,
                    preset=preset_id,
                    provider=preset["provider"],
                    model=model,
                    base_url=base_url,
                )
                doc["profiles"].append(profile)
            else:
                existing.name = name
                existing.preset = preset_id
                existing.provider = preset["provider"]
                existing.model = model
                existing.base_url = base_url
                profile = existing

            if isinstance(api_key, str) and api_key.strip():
                self._secrets.save_key(profile.id, api_key.strip())

            activate = bool(payload.get("activate"))
            if activate or doc.get("active_profile_id") is None:
                doc["active_profile_id"] = profile.id
            self._write_profiles_doc(doc)
            return profile

    def delete_profile(self, profile_id: str) -> None:
        """Remove a profile and its stored key; unknown ids raise."""
        if not isinstance(profile_id, str) or not profile_id:
            raise SettingsInvalid("profile_id must be a non-empty string")
        with self._lock:
            doc = self._load_profiles_doc()
            remaining = [p for p in doc["profiles"] if p.id != profile_id]
            if len(remaining) == len(doc["profiles"]):
                raise SettingsInvalid("unknown profile_id")
            doc["profiles"] = remaining
            if doc.get("active_profile_id") == profile_id:
                doc["active_profile_id"] = None
            self._secrets.delete_key(profile_id)
            self._write_profiles_doc(doc)

    def active_profile(self) -> Profile | None:
        with self._lock:
            return self._active_from_doc(self._load_profiles_doc())

    def api_key_for(self, profile_id: str) -> str | None:
        """Return the stored API key for *profile_id*, or ``None``."""
        if not isinstance(profile_id, str) or not profile_id:
            return None
        with self._lock:
            profile = next((p for p in self._load_profiles_doc()["profiles"] if p.id == profile_id), None)
            if profile is not None and not profile.requires_key:
                return None
            return self._secrets.load_key(profile_id)

    # ------------------------------------------------------------------
    # appearance

    def _theme_catalog(self) -> list[dict]:
        """Return display metadata for the installed theme registry."""
        data = _read_json_lenient(self._paths.theme / "themes.json")
        entries = data.get("themes") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            return []
        catalog = []
        for item in entries:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                continue
            entry = {"id": item["id"]}
            name = item.get("name")
            if isinstance(name, str):
                entry["name"] = name
            elif isinstance(name, dict):
                entry["name"] = {
                    locale: name[locale]
                    for locale in ("zh", "en")
                    if isinstance(name.get(locale), str)
                }
            for key in ("primary", "accent", "dark_primary", "dark_accent"):
                if isinstance(item.get(key), str):
                    entry[key] = item[key]
            if isinstance(item.get("builtin"), bool):
                entry["builtin"] = item["builtin"]
            catalog.append(entry)
        return catalog

    def _known_theme_ids(self) -> frozenset[str]:
        ids = set(_BUILTIN_THEME_IDS)
        data = _read_json_lenient(self._paths.theme / "themes.json")
        if isinstance(data, dict):
            themes = data.get("themes")
            if isinstance(themes, list):
                for item in themes:
                    if isinstance(item, dict) and isinstance(item.get("id"), str):
                        ids.add(item["id"])
                    elif isinstance(item, str):
                        ids.add(item)
            default = data.get("default_theme")
            if isinstance(default, str) and default:
                ids.add(default)
        return frozenset(ids)

    def _default_theme_id(self) -> str:
        """Return the theme a user with no stored preference should get.

        ``themes.json`` names it; that is what makes the shipped default a
        theme-layer decision rather than a rebuild.

        The declared id is checked against the ``themes`` array specifically,
        NOT against :meth:`_known_theme_ids` -- that set deliberately contains
        ``default_theme`` itself, so validating against it would accept any
        string, and a typo would become an id the injection layer then rejects.
        Registered-or-fallback is the only check that can fail.
        """
        data = _read_json_lenient(self._paths.theme / "themes.json")
        if not isinstance(data, dict):
            return _FALLBACK_THEME
        declared = data.get("default_theme")
        if not isinstance(declared, str) or not declared:
            return _FALLBACK_THEME
        entries = data.get("themes")
        registered = set()
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    registered.add(item["id"])
                elif isinstance(item, str):
                    registered.add(item)
        if declared in registered or declared in _BUILTIN_THEME_IDS:
            return declared
        return _FALLBACK_THEME

    def load_appearance(self) -> dict:
        """Return ``{"theme", "locale"}``; any stored problem falls back to defaults."""
        with self._lock:
            data = _read_json_lenient(self._appearance_file)
            theme = self._default_theme_id()
            locale = _DEFAULT_LOCALE
            if isinstance(data, dict):
                stored_theme = data.get("theme")
                if isinstance(stored_theme, str) and stored_theme in self._known_theme_ids():
                    theme = stored_theme
                stored_locale = data.get("locale")
                if isinstance(stored_locale, str) and stored_locale in _LOCALES:
                    locale = stored_locale
            return {"theme": theme, "locale": locale}

    def save_appearance(self, theme: str, locale: str) -> dict:
        """Persist appearance; raises ``SettingsInvalid`` for unknown values."""
        with self._lock:
            if not isinstance(theme, str) or theme not in self._known_theme_ids():
                raise SettingsInvalid(f"unknown theme: {theme!r}")
            if not isinstance(locale, str) or locale not in _LOCALES:
                raise SettingsInvalid(f"unknown locale: {locale!r}")
            _write_json_atomic(
                self._appearance_file,
                {"schema_version": _SCHEMA_VERSION, "theme": theme, "locale": locale},
            )
            return {"theme": theme, "locale": locale}
