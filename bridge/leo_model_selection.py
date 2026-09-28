"""Align native model selection without editing profiles or conversation pins.

The upstream resolver prefers a stored global key to the process environment.
Keep that original row, including its timestamp, in the same protected settings
table and leave the live override empty while the native shell owns selection.
Only the daemon environment receives the current key or private relay token.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import stat
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

STATE_KEY = "leo_shell_native_selection_v1"
SAVED_PREFIX = "leo_shell_native_saved_"
MANAGED_KEYS = ("active_model_profile", "llm_api_key")
LOCAL_MODEL = "local-qwen3-4b"


class SelectionError(ValueError):
    pass


def _setting(connection, key):
    return connection.execute("SELECT value,updated_at FROM settings WHERE key=?", (key,)).fetchone()


def _write(connection, key, value, updated_at=None):
    connection.execute(
        "INSERT INTO settings(key,value,updated_at) VALUES(?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
        (key, value, updated_at if updated_at is not None else int(time.time() * 1000)),
    )


def _text(row):
    return str(row[0] or "") if row else ""


def _saved_row(connection, state, key):
    slot = state["saved"].get(key)
    if slot is None:
        return None
    if not isinstance(slot, str) or not slot.startswith(SAVED_PREFIX) or not slot.endswith("_" + key):
        raise SelectionError("LOCAL_SELECTION_STATE_INVALID")
    row = _setting(connection, slot)
    if row is None:
        raise SelectionError("LOCAL_SELECTION_STATE_INVALID")
    return row


def _load_state(connection):
    row = _setting(connection, STATE_KEY)
    if row is None:
        return None
    try:
        state = json.loads(row[0])
        if state.get("version") != 1 or set(state["saved"]) != set(MANAGED_KEYS) or set(state["expected"]) != set(MANAGED_KEYS):
            raise ValueError()
        if not all(isinstance(state["expected"][key], str) for key in MANAGED_KEYS):
            raise ValueError()
        for key in MANAGED_KEYS:
            _saved_row(connection, state, key)
        return state
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise SelectionError("LOCAL_SELECTION_STATE_INVALID") from exc


def _save_original(connection, state, key):
    row = _setting(connection, key)
    if row is None:
        state["saved"][key] = None
        return
    slot = SAVED_PREFIX + uuid.uuid4().hex + "_" + key
    _write(connection, slot, row[0], row[1])
    state["saved"][key] = slot


def _matching_saved_profile(connection, state, provider, model, base_url):
    previous = _text(_saved_row(connection, state, "active_model_profile"))
    if not previous:
        return ""
    try:
        profiles = json.loads(_text(_setting(connection, "model_profiles")) or "[]")
        if not isinstance(profiles, list):
            return ""
        for profile in profiles:
            if not isinstance(profile, dict) or profile.get("id") != previous or profile.get("deleted_at"):
                continue
            if (profile.get("provider") == provider and profile.get("model") == model
                    and str(profile.get("base_url") or "").rstrip("/") == base_url.rstrip("/")):
                return previous
    except (ValueError, TypeError):
        pass
    return ""


def select(connection, *, provider, model, base_url, local=False, explicit_key=False, browse=False):
    """One transaction; callers must already have opened the intended database."""
    if (any(type(flag) is not bool for flag in (local, explicit_key, browse))
            or (browse and (local or explicit_key))):
        raise SelectionError("LOCAL_SELECTION_ARGUMENT_INVALID")
    if provider not in {"chatgpt", "claude", "ark", "gemini", "openai_responses"}:
        raise SelectionError("LOCAL_SELECTION_ARGUMENT_INVALID")
    if not isinstance(model, str) or not model or len(model) > 200 or any(ord(c) < 32 for c in model):
        raise SelectionError("LOCAL_SELECTION_ARGUMENT_INVALID")
    endpoint = urlsplit(base_url)
    if base_url and (endpoint.scheme not in {"http", "https"} or not endpoint.hostname or endpoint.username
                     or endpoint.password or endpoint.query or endpoint.fragment or any(ord(c) < 32 for c in base_url)):
        raise SelectionError("LOCAL_SELECTION_ARGUMENT_INVALID")
    if local and (provider != "chatgpt" or model != LOCAL_MODEL or endpoint.hostname != "127.0.0.1"):
        raise SelectionError("LOCAL_SELECTION_ARGUMENT_INVALID")
    connection.execute("BEGIN IMMEDIATE")
    try:
        state = _load_state(connection)
        if state is None:
            state = {"version": 1, "saved": {}, "expected": {}}
            for key in MANAGED_KEYS:
                _save_original(connection, state, key)
        else:
            # A deliberate change through the upstream settings UI gets its own
            # recoverable row. Never overwrite the previously saved credential.
            for key in MANAGED_KEYS:
                if _text(_setting(connection, key)) != state["expected"][key]:
                    _save_original(connection, state, key)
        # Browsing must not reactivate a saved profile's credential. Keep its
        # original row recoverable; pinned conversations and profiles are intact.
        # The daemon's separate browse guard blocks their model calls as well.
        chosen_active = "" if local or explicit_key or browse else _matching_saved_profile(
            connection, state, provider, model, base_url
        )
        desired = {"active_model_profile": chosen_active, "llm_api_key": ""}
        changed = any(_text(_setting(connection, key)) != value for key, value in desired.items())
        for key, value in desired.items():
            if _setting(connection, key) is None or _text(_setting(connection, key)) != value:
                _write(connection, key, value)
        state["expected"] = desired
        _write(connection, STATE_KEY, json.dumps(state, separators=(",", ":")))
        config_changed = (
            _text(_setting(connection, "llm_provider")) != provider
            or _text(_setting(connection, "llm_model")) != model
            or (bool(base_url) and _text(_setting(connection, "llm_base_url")).rstrip("/") != base_url.rstrip("/"))
        )
        connection.commit()
        return {"changed": changed, "restart_required": bool(changed or config_changed),
                "active_profile_empty": not bool(chosen_active), "global_key_override_empty": True,
                "browse": browse}
    except BaseException:
        connection.rollback()
        raise


def restore(connection):
    """Restore saved rows only while the shell's expected values still own them."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        state = _load_state(connection)
        if state is None:
            connection.commit()
            return {"restored": False, "conflict": False}
        if any(_text(_setting(connection, key)) != state["expected"][key] for key in MANAGED_KEYS):
            connection.rollback()
            return {"restored": False, "conflict": True}
        for key in MANAGED_KEYS:
            row = _saved_row(connection, state, key)
            if row is None:
                connection.execute("DELETE FROM settings WHERE key=?", (key,))
            else:
                _write(connection, key, row[0], row[1])
        connection.execute("DELETE FROM settings WHERE key=?", (STATE_KEY,))
        connection.commit()
        return {"restored": True, "conflict": False}
    except BaseException:
        connection.rollback()
        raise


def open_database(path):
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise SelectionError("LOCAL_SELECTION_PATH_INVALID")
    if not path.is_file():
        raise SelectionError("LOCAL_SELECTION_DATABASE_MISSING")
    connection = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=5)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(settings)")}
    if not {"key", "value", "updated_at"} <= columns:
        connection.close()
        raise SelectionError("LOCAL_SELECTION_SCHEMA_INVALID")
    return connection


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("select", "restore"))
    parser.add_argument("--database", type=Path, default=Path.home() / ".local/share/leo-ai-studio/data/openai4s.db")
    parser.add_argument("--provider", default="chatgpt")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--explicit-key", action="store_true")
    parser.add_argument("--browse", action="store_true")
    args = parser.parse_args(argv)
    try:
        connection = open_database(args.database)
        try:
            result = restore(connection) if args.action == "restore" else select(
                connection, provider=args.provider, model=args.model, base_url=args.base_url,
                local=args.local, explicit_key=args.explicit_key, browse=args.browse,
            )
        finally:
            connection.close()
        print(json.dumps({"ok": True, "data": result}, separators=(",", ":")))
        return 0
    except (OSError, ValueError, sqlite3.Error) as exc:
        code = str(exc) if isinstance(exc, SelectionError) else "LOCAL_SELECTION_FAILED"
        print(json.dumps({"ok": False, "error": {"code": code, "message": "本机模型选择未能安全同步，原始设置已保留。"}}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
