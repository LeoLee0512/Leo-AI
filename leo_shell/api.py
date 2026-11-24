"""pywebview ``js_api`` facade for the rewritten Leo AI Studio shell.

The front end in ``theme/shell.html`` calls these methods through
``pywebview.api.*`` on a pywebview-managed thread.  Every public method is
therefore thread-safe and never raises: failures collapse into the small
``{"ok": False, "message": <public code>}`` shape the page already knows how
to render.  API keys never leave this object; the page only ever sees
``has_key``.

This module deliberately avoids importing the sibling runtime modules so it
stays importable in headless test environments.  It only relies on the public
interfaces fixed by ``DESIGN.md``: ``SettingsStore``, ``ConnectionCoordinator``
and (optionally) ``DesktopUI``.
"""

from __future__ import annotations

import hashlib
import logging
import re
import os
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .connection import ConnectionCoordinator
    from .paths import AppPaths
    from .settings_store import SettingsStore
    from .ui import DesktopUI

__all__ = ["ShellApi"]


# Public codes mirrored by the front end's publicMessage table in shell.html
# and by the PUBLIC_* constants in connection.py.
MODEL_SETTINGS_INVALID = "MODEL_SETTINGS_INVALID"
MODEL_SETTINGS_UNAVAILABLE = "MODEL_SETTINGS_UNAVAILABLE"
MODEL_CONNECTION_FAILED = "MODEL_CONNECTION_FAILED"

_LOCAL_SKILLS_UNAVAILABLE = "LOCAL_SKILLS_UNAVAILABLE"

_VALID_LOCALES = frozenset({"zh", "en"})
_DEFAULT_LOCALE = "zh"

_MAX_SKILL_FILE_BYTES = 1024 * 1024
_MAX_SKILL_NAME_LENGTH = 120

_UNIMPLEMENTED_MESSAGE = "此功能暂未在新版壳中提供。"
_UNIMPLEMENTED_EXTENSIONS = frozenset(
    {
        "choose_theme_file",
        "stage_theme_preview",
        "confirm_theme_preview",
        "discard_theme_preview",
        "delete_custom_theme",
        "get_project_persona",
        "save_project_persona",
    }
)

# Exact key sets of the get_state contract; anything else (notably any secret
# material a buggy store might have attached) is dropped before responding.
_STATE_PRESET_KEYS = ("id", "label", "model", "base_url", "editable_base_url")
_STATE_PROFILE_KEYS = ("id", "name", "preset", "model", "base_url")
_STATE_SETTINGS_KEYS = ("preset", "model", "base_url")


_APPEARANCE_INTENTS = frozenset({"upload", "chat"})


def _failure(message: str) -> dict:
    return {"ok": False, "message": message}


def _is_within(candidate: Path, base: Path) -> bool:
    try:
        candidate.relative_to(base)
    except ValueError:
        return False
    return True


def _skill_name(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return heading[:_MAX_SKILL_NAME_LENGTH]
    return fallback


def _scan_skills(root: Path) -> dict:
    """Read ``root/<id>/SKILL.md`` entries and say what was refused and why.

    Returns the shape the removed upstream injection consumed (kept for a future
    Leo-owned skills view): ``skills`` carries
    ``folder``/``byte_size``/``sha256``/``content`` (the sync step filters on
    all four and posts ``content`` to the daemon's skills import endpoint),
    ``rejected`` names what was skipped with a machine code, and
    ``hidden_count`` reports dot-entries that were never read at all.  ``id``
    and ``name`` stay in each entry so any older caller keeps working.
    """

    skills: list[dict] = []
    rejected: list[dict] = []
    hidden = 0
    if not root.is_dir():
        return {"skills": skills, "rejected": rejected, "hidden_count": hidden}
    try:
        base = root.resolve()
    except OSError:
        return {"skills": skills, "rejected": rejected, "hidden_count": hidden}
    for child in sorted(root.iterdir(), key=lambda path: path.name):
        if child.name.startswith("."):
            # Not even read: a dot-entry is deliberately out of scope, and
            # naming it in `rejected` would leak the directory listing.
            hidden += 1
            continue
        code = None
        content = ""
        try:
            if child.is_symlink():
                code = "symlink"
            elif not child.is_dir():
                code = "not_a_directory"
            elif not _is_within(child.resolve(), base):
                code = "escapes_root"
            else:
                skill_file = child / "SKILL.md"
                if skill_file.is_symlink():
                    code = "symlink"
                elif not skill_file.is_file():
                    code = "no_skill_md"
                elif not _is_within(skill_file.resolve(), base):
                    code = "escapes_root"
                elif skill_file.stat().st_size > _MAX_SKILL_FILE_BYTES:
                    code = "too_large"
                else:
                    content = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            # A single broken skill must not break the whole scan.
            code = "unreadable"
        if code is not None:
            if code != "not_a_directory":
                rejected.append({"folder": child.name, "code": code})
            continue
        encoded = content.encode("utf-8")
        skills.append(
            {
                "id": child.name,
                "folder": child.name,
                "name": _skill_name(content, child.name),
                "byte_size": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "content": content,
            }
        )
    return {"skills": skills, "rejected": rejected, "hidden_count": hidden}


class ShellApi:
    """Thread-safe implementation of the front-end contract (see DESIGN.md).

    ``ui`` is the owning :class:`~leo_shell.ui.DesktopUI` (or a test double),
    used for navigation and native dialogs.  ``paths`` is needed for the
    local-skills helpers and the research and entity stores.
    """

    def __init__(
        self,
        settings: SettingsStore,
        coordinator: ConnectionCoordinator,
        ui: DesktopUI | None = None,
        *,
        paths: AppPaths | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._coordinator = coordinator
        self._ui = ui
        self._paths = paths
        self._logger = logger if logger is not None else logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._entity_store = None
        self._session_model_service = None
        self._research_service = None
        self._workbench_gateway = None
        self._appearance_intent: str | None = None

    def workbench_request(self, payload: Any) -> dict:
        try:
            from .workbench import WorkbenchGateway
            with self._lock:
                if self._workbench_gateway is None:
                    self._workbench_gateway = WorkbenchGateway(self._coordinator._bridge.client_url)
            return self._workbench_gateway.request(payload)
        except ValueError as exc:
            code = str(exc)
            return _failure(code if re.fullmatch(r"WORKBENCH_[A-Z_]+", code) else "WORKBENCH_REQUEST_FAILED")
        except Exception:
            return _failure("WORKBENCH_UNAVAILABLE")

    def account_request(self, payload: Any) -> dict:
        """Local adapter seam for a later server-backed account service."""
        with self._lock:
            try:
                from .local_accounts import LocalAccounts
                if self._paths is None:
                    return _failure("ACCOUNT_UNAVAILABLE")
                return LocalAccounts(self._paths.user).request(payload)
            except ValueError as exc:
                code = str(exc)
                return _failure(code if code.startswith("ACCOUNT_") else "ACCOUNT_UNAVAILABLE")
            except Exception:
                return _failure("ACCOUNT_UNAVAILABLE")

    def workspace_preferences(self, payload: Any) -> dict:
        with self._lock:
            try:
                from .workspace_preferences import WorkspacePreferences
                if self._paths is None: return _failure("THEME_UNAVAILABLE")
                return WorkspacePreferences(self._paths.user).request(payload)
            except ValueError as exc:
                code = str(exc)
                return _failure(code if code in {"THEME_INVALID", "THEME_CONTRAST_LOW", "THEME_UNAVAILABLE"} else "THEME_UNAVAILABLE")
            except Exception:
                return _failure("THEME_UNAVAILABLE")

    def paste_text(self) -> dict:
        """Read text only in response to the user's explicit Edit > Paste action."""
        from .clipboard import ClipboardError, get_text
        with self._lock:
            try:
                return {"ok": True, "text": get_text()}
            except ClipboardError as exc:
                return _failure(str(exc))
            except Exception:
                self._logger.exception("paste_text failed")
                return _failure("CLIPBOARD_UNAVAILABLE")

    def appearance_intent(self, payload: Any) -> dict:
        """One-shot hand-off from the start page to the workbench appearance tab.

        The two pages replace each other through ``load_html``, so browser
        storage is not a dependable channel between them; the intent lives in
        this process instead and is consumed exactly once.
        """
        with self._lock:
            op = payload.get("operation") if isinstance(payload, dict) else None
            if op == "set":
                intent = payload.get("intent")
                if intent not in _APPEARANCE_INTENTS:
                    return _failure("APPEARANCE_INTENT_INVALID")
                self._appearance_intent = intent
                return {"ok": True}
            if op == "take":
                intent, self._appearance_intent = self._appearance_intent, None
                return {"ok": True, "intent": intent}
            return _failure("APPEARANCE_INTENT_INVALID")

    def purge_entity(self, payload: Any) -> dict:
        """Delete only an explicitly confirmed, revision-matched recycled item."""
        with self._lock:
            try:
                from .entity_store import EntityStore
                from .workbench import WorkbenchGateway, identifier
                if not isinstance(payload, dict) or self._paths is None:
                    return _failure("ENTITY_INVALID")
                kind, ident = payload.get("entity_type"), identifier(payload.get("entity_id"))
                if kind not in {"session", "project"} or payload.get("confirm_id") != ident:
                    return _failure("ENTITY_INVALID")
                store = self._entity_store
                if store is None:
                    store = self._entity_store = EntityStore(self._paths.user)
                with store.lock:
                    data = store._read()
                    record = next((r for r in data["entities"] if r["entity_type"] == kind and r["entity_id"] == ident), None)
                    if not record or record["state"] != "trashed" or type(payload.get("expected_revision")) is not int or record["revision"] != payload["expected_revision"]:
                        return _failure("ENTITY_REVISION_CONFLICT")
                    if self._workbench_gateway is None:
                        self._workbench_gateway = WorkbenchGateway(self._coordinator._bridge.client_url)
                    self._workbench_gateway.purge(kind, ident)
                    members = set(record.get("snapshot", {}).get("member_session_ids", []))
                    data["entities"] = [r for r in data["entities"] if r != record and not (kind == "project" and r["entity_type"] == "session" and r["entity_id"] in members)]
                    data["revision"] += 1
                    store._write(data)
                    return {"ok": True}
            except ValueError as exc:
                code = str(exc)
                return _failure(code if code.startswith(("ENTITY_", "WORKBENCH_")) else "ENTITY_INVALID")
            except Exception:
                return _failure("WORKBENCH_UNAVAILABLE")

    def research_request(self, payload: Any) -> dict:
        """Task operations are validated by the service; payloads cannot supply approval."""
        if not isinstance(payload, dict):
            return _failure("RESEARCH_REQUEST_INVALID")
        try:
            service = self._research()
            if service is None:
                return _failure("RESEARCH_RUNTIME_UNAVAILABLE")
            return service.dispatch(payload.get("operation"), payload)
        except ValueError as exc:
            code = str(exc)
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,100}", code):
                code = "RESEARCH_VALIDATION_FAILED"
            return _failure(code)
        except Exception:
            return _failure("RESEARCH_UNAVAILABLE")

    def _research(self):
        from .research import ResearchService
        from .research_draft import generate
        with self._lock:
            if self._paths is None:
                return None
            if self._research_service is None:
                def confirm(title, text):
                    window = getattr(self._ui, "_window", None)
                    return bool(window and window.create_confirmation_dialog(title, text))
                self._research_service = ResearchService(self._paths, confirm=confirm,
                    draft_provider=lambda frame, prompt: generate(self._session_models(), frame, prompt))
            return self._research_service

    # Window lifecycle only; underscored so the page cannot call them.
    def _research_busy_tasks(self) -> list:
        service = self._research()
        return service.busy_tasks() if service is not None else []

    def _research_stop_for_close(self) -> None:
        service = self._research()
        if service is not None:
            service.stop_for_close()

    def _session_models(self):
        if self._paths is None:
            from .session_models import SessionModelError
            raise SessionModelError("MODEL_RUNTIME_UNAVAILABLE", 503)
        if self._session_model_service is None:
            from .session_models import SessionModelService
            self._session_model_service = SessionModelService(self._settings, self._paths, self._coordinator)
        return self._session_model_service

    def _model_selection(self, operation: str, payload: Any) -> dict:
        from .session_models import SessionModelError
        with self._lock:
            try:
                return getattr(self._session_models(), operation)(payload)
            except SessionModelError as error:
                return error.response()
            except Exception:
                # The transport and DPAPI path can hold secrets in exception
                # arguments. Never log or expose the exception representation.
                return {"ok": False, "message": "MODEL_SELECTION_UNAVAILABLE",
                        "code": "MODEL_SELECTION_UNAVAILABLE", "status": 503}

    def list_session_models(self, payload: Any) -> dict:
        return self._model_selection("list", payload)

    def select_session_model(self, payload: Any) -> dict:
        return self._model_selection("select", payload)

    def _entities(self, operation: str, payload: Any) -> dict:
        with self._lock:
            try:
                if self._paths is None:
                    return _failure("ENTITY_STORE_UNAVAILABLE")
                if self._entity_store is None:
                    from .entity_store import EntityStore
                    self._entity_store = EntityStore(self._paths.user)
                return getattr(self._entity_store, operation)(payload)
            except ValueError as exc:
                code = str(exc)
                return _failure(code if code in {"ENTITY_INVALID", "ENTITY_REVISION_CONFLICT"} else "ENTITY_STORE_UNAVAILABLE")
            except Exception:
                return _failure("ENTITY_STORE_UNAVAILABLE")

    def list_entity_states(self, payload: Any = None) -> dict:
        return self._entities("list", {} if payload is None else payload)

    def mark_entity(self, payload: Any) -> dict:
        return self._entities("mark", payload)

    def restore_entity(self, payload: Any) -> dict:
        return self._entities("remove", payload)

    def forget_entity(self, payload: Any) -> dict:
        return self._entities("remove", payload)

    # -- front-end contract ------------------------------------------------

    def get_state(self) -> dict:
        """Return the shell state; secrets are never part of the payload."""

        with self._lock:
            try:
                state = self._settings.state_for_shell()
                if not isinstance(state, dict):
                    raise TypeError("state_for_shell did not return a dict")
                return self._sanitize_state(state)
            except Exception:
                self._logger.exception("get_state failed")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)

    def save_profile(self, payload: Any) -> dict:
        with self._lock:
            if not isinstance(payload, dict):
                return _failure(MODEL_SETTINGS_INVALID)
            try:
                profile = self._settings.save_profile(payload)
            except ValueError:
                # SettingsInvalid is a ValueError subclass by contract.
                self._logger.info("save_profile rejected invalid model settings")
                return _failure(MODEL_SETTINGS_INVALID)
            except Exception:
                self._logger.exception("save_profile failed")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)

            if not bool(payload.get("activate")):
                return {"ok": True, "pending": False}

            api_key: str | None = None
            try:
                api_key = self._settings.api_key_for(profile.id)
            except Exception:
                self._logger.exception("failed to resolve the saved profile's API key")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)
            try:
                result = self._coordinator.submit(profile, api_key, requires_ack=True)
            except Exception:
                self._logger.exception("connection submit failed after save_profile")
                return _failure(MODEL_CONNECTION_FAILED)
            finally:
                api_key = None
            return self._submission_response(result)

    def save_settings(self, payload: Any) -> dict:
        """Alias kept for the legacy front end; identical to save_profile."""

        return self.save_profile(payload)

    def delete_profile(self, payload: Any) -> dict:
        with self._lock:
            profile_id = payload.get("profile_id") if isinstance(payload, dict) else None
            if not isinstance(profile_id, str) or not profile_id:
                return _failure(MODEL_SETTINGS_INVALID)
            try:
                # No mapping means this profile never created managed runtime
                # copies. Preserve the legacy offline-delete behavior then.
                mapping = Path(self._paths.user) / "session-model-bindings.dpapi" if self._paths else None
                if self._session_model_service is not None or (mapping is not None and mapping.exists()):
                    from .session_models import SessionModelError
                    try:
                        self._session_models().revoke(profile_id)
                    except SessionModelError as error:
                        return error.response()
                self._settings.delete_profile(profile_id)
            except ValueError:
                return _failure(MODEL_SETTINGS_INVALID)
            except Exception:
                self._logger.exception("delete_profile failed")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)
            return {"ok": True}

    def save_appearance(self, payload: Any) -> dict:
        with self._lock:
            if not isinstance(payload, dict):
                return _failure(MODEL_SETTINGS_INVALID)
            try:
                appearance = self._settings.save_appearance(
                    payload.get("theme"), payload.get("locale")
                )
            except ValueError:
                return _failure(MODEL_SETTINGS_INVALID)
            except Exception:
                self._logger.exception("save_appearance failed")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)
            return {"ok": True, "appearance": appearance}

    def connect_keyless(self) -> dict:
        """Enter the workbench without a key, because the user asked for it.

        The startup path no longer navigates on its own when no key is stored
        (see ``app._on_window_ready``); this is the explicit opt-in behind the
        page's "browse without a model" button.  The stored key is never read
        here: keyless means keyless, even for a profile that has one.
        """

        with self._lock:
            try:
                profile = self._settings.active_profile()
            except Exception:
                self._logger.exception("connect_keyless could not read the active profile")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)
            # A transient bootstrap is enough to open the daemon's workbench.
            # It is never persisted as a user profile. Explicit browsing must
            # also avoid launching the configured local model.
            if profile is None or getattr(profile, "provider", None) == "local-llama":
                profile = self._browse_profile(unconfigured=profile is None)
            try:
                result = self._coordinator.submit(profile, None, requires_ack=False)
            except Exception:
                self._logger.exception("connect_keyless submit failed")
                return _failure(MODEL_CONNECTION_FAILED)
            return self._submission_response(result)

    def enter_studio(self) -> dict:
        """Use the selected model, or explicitly enter unconfigured browsing."""
        with self._lock:
            api_key = None
            try:
                profile = self._settings.active_profile()
                if profile is None:
                    profile = self._browse_profile(unconfigured=True)
                elif getattr(profile, "provider", None) != "local-llama":
                    api_key = self._settings.api_key_for(profile.id)
            except Exception:
                self._logger.exception("enter_studio could not resolve model settings")
                return _failure(MODEL_SETTINGS_UNAVAILABLE)
            try:
                return self._submission_response(
                    self._coordinator.submit(profile, api_key, requires_ack=False)
                )
            except Exception:
                self._logger.exception("enter_studio submit failed")
                return _failure(MODEL_CONNECTION_FAILED)
            finally:
                api_key = None

    @staticmethod
    def _browse_profile(*, unconfigured: bool) -> Any:
        from .settings_store import PRESETS
        preset = next(item for item in PRESETS if item["id"] == "deepseek")
        return SimpleNamespace(
            id="", name="", preset=preset["id"], provider=preset["provider"],
            model=preset["model"], base_url=preset["base_url"],
            entry_mode="unconfigured" if unconfigured else "keyless",
        )

    @staticmethod
    def _submission_response(result: Any) -> dict:
        if not isinstance(result, dict) or result.get("ok") is not True:
            code = "APP_CLOSING" if isinstance(result, dict) and result.get("message") == "APP_CLOSING" else MODEL_CONNECTION_FAILED
            return _failure(code)
        return {"ok": True, "pending": True, "request_id": result.get("request_id")}

    def get_runtime_state(self) -> dict:
        """Keep runtime readiness separate from the persisted get_state contract."""
        try:
            value = self._coordinator.runtime_state()
            mode, status = value.get("mode"), value.get("status")
            if mode not in {"unconfigured", "keyless", "cloud", "local"} or status not in {"idle", "connecting", "ready", "failed"}:
                raise ValueError("invalid runtime state")
            return {
                "mode": mode, "status": status,
                "has_key": mode == "cloud" and value.get("has_key") is True,
                "local_ready": mode == "local" and status == "ready" and value.get("local_ready") is True,
            }
        except Exception:
            return _failure("RUNTIME_STATE_UNAVAILABLE")

    def return_to_start(self) -> dict:
        with self._lock:
            try:
                if self._ui is None or self._ui.return_to_start() is not True:
                    return _failure("START_PAGE_UNAVAILABLE")
                return {"ok": True}
            except Exception:
                self._logger.exception("return_to_start failed")
                return _failure("START_PAGE_UNAVAILABLE")

    def intro_video(self) -> dict:
        """URL of the opening animation on launch, else null (the page then skips it)."""
        try:
            getter = getattr(self._ui, "intro_video_url", None)
            return {"ok": True, "url": getter() if callable(getter) else None}
        except Exception:
            self._logger.debug("intro_video failed", exc_info=True)
            return {"ok": True, "url": None}

    def copy_text(self, payload: Any) -> dict:
        """Clipboard fallback for the workbench's copy and share-text actions (write-only)."""
        from .clipboard import ClipboardError, set_text
        text = payload.get("text") if isinstance(payload, dict) else None
        try:
            set_text(text)
            return {"ok": True}
        except ClipboardError as exc:
            return _failure(str(exc))
        except Exception:
            self._logger.exception("copy_text failed")
            return _failure("CLIPBOARD_UNAVAILABLE")

    def open_model_settings(self) -> dict:
        """Model profiles live on the start page; arrive with its drawer open."""
        with self._lock:
            try:
                if self._ui is None or self._ui.return_to_start(open_settings=True) is not True:
                    return _failure("START_PAGE_UNAVAILABLE")
                return {"ok": True}
            except Exception:
                self._logger.exception("open_model_settings failed")
                return _failure("START_PAGE_UNAVAILABLE")

    def acknowledge_connection(self, payload: Any) -> dict:
        """Release a pending navigation; always reports success."""

        try:
            request_id = self._request_id_from(payload)
            if request_id is not None:
                self._coordinator.acknowledge(request_id)
        except Exception:
            self._logger.debug("acknowledge_connection failed", exc_info=True)
        return {"ok": True}

    def open_local_skills_folder(self) -> dict:
        with self._lock:
            try:
                root = self._skills_root()
                startfile = getattr(os, "startfile", None)
                if root is None or startfile is None:
                    return _failure(_LOCAL_SKILLS_UNAVAILABLE)
                root.mkdir(parents=True, exist_ok=True)
                startfile(str(root))
                return {"ok": True}
            except Exception:
                self._logger.exception("open_local_skills_folder failed")
                return _failure(_LOCAL_SKILLS_UNAVAILABLE)

    def scan_local_skills(self, payload: Any = None) -> dict:
        """Scan ``user/user-skills`` for syncable SKILL.md documents.

        ``payload`` is accepted and ignored: the workbench overlay calls this
        as ``scan_local_skills({})``, and a zero-argument signature made every
        press of "scan and sync" fail before it reached the scan.
        """

        with self._lock:
            root = self._skills_root()
            if root is None:
                return _failure(_LOCAL_SKILLS_UNAVAILABLE)
            try:
                return {"ok": True, **_scan_skills(root)}
            except Exception:
                self._logger.exception("scan_local_skills failed")
                return _failure(_LOCAL_SKILLS_UNAVAILABLE)

    # -- extension-method fallback ------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # Phase-two extension methods must not explode the front end with an
        # AttributeError; answer with the contracted "not available" payload.
        if name in _UNIMPLEMENTED_EXTENSIONS:

            def _unavailable(*args: Any, **kwargs: Any) -> dict:
                return _failure(_UNIMPLEMENTED_MESSAGE)

            _unavailable.__name__ = name
            return _unavailable
        raise AttributeError(f"{type(self).__name__} has no attribute {name!r}")

    # -- internals -----------------------------------------------------------

    @staticmethod
    def _sanitize_themes(value: Any) -> list[dict]:
        """Keep only typed display fields, including within localized names."""
        if not isinstance(value, list):
            return []
        themes = []
        for item in value:
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
            themes.append(entry)
        return themes

    @staticmethod
    def _sanitize_state(state: dict) -> dict:
        appearance = state.get("appearance")
        appearance = dict(appearance) if isinstance(appearance, dict) else {}
        locale = appearance.get("locale")
        settings = state.get("settings")
        active = state.get("active_profile_id")
        presets = []
        for item in state.get("presets") or []:
            if isinstance(item, dict):
                entry = {key: item.get(key) for key in _STATE_PRESET_KEYS}
                if isinstance(item.get("requires_key"), bool):
                    entry["requires_key"] = item["requires_key"]
                presets.append(entry)
        profiles = []
        for item in state.get("profiles") or []:
            if not isinstance(item, dict):
                continue
            entry = {key: item.get(key) for key in _STATE_PROFILE_KEYS}
            entry["has_key"] = bool(item.get("has_key"))
            if isinstance(item.get("requires_key"), bool):
                entry["requires_key"] = item["requires_key"]
            profiles.append(entry)
        safe_settings = {key: settings.get(key) for key in _STATE_SETTINGS_KEYS} if isinstance(settings, dict) else None
        if isinstance(settings, dict) and isinstance(settings.get("requires_key"), bool):
            safe_settings["requires_key"] = settings["requires_key"]
        return {
            "appearance": {
                "locale": locale if locale in _VALID_LOCALES else _DEFAULT_LOCALE,
                "theme": appearance.get("theme"),
            },
            "themes": ShellApi._sanitize_themes(state.get("themes")),
            "presets": presets,
            "profiles": profiles,
            "active_profile_id": active if isinstance(active, str) else None,
            "settings": safe_settings,
            "has_key": bool(state.get("has_key")),
        }

    @staticmethod
    def _request_id_from(payload: Any) -> int | None:
        if not isinstance(payload, dict):
            return None
        value = payload.get("request_id")
        if isinstance(value, bool):
            return None
        if isinstance(value, float) and not value.is_integer():
            return None
        try:
            request_id = int(value)
        except (TypeError, ValueError):
            return None
        return request_id if request_id > 0 else None

    def _skills_root(self) -> Path | None:
        user = getattr(self._paths, "user", None)
        if user is None:
            return None
        return Path(user) / "user-skills"
