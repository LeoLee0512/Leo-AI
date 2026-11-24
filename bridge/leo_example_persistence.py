"""Byte-checked persistence for deletion of the single bundled Example project.

The lifecycle repository writes a tombstone inside its existing deletion
transaction. Startup reads the same database setting before considering seed.
No existing project, conversation, connector or credential is removed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile

VERSION = 1
SETTING_KEY = "leo_example_project_deleted_v1"
PROJECT_ID = "proj_example"
SEED_MARKER = "# LEO_EXAMPLE_SEED_PERSISTENCE_VERSION = 1"
DELETE_MARKER = "# LEO_EXAMPLE_DELETE_PERSISTENCE_VERSION = 1"
SEED_ANCHOR = '''def _seed_example_project(cfg: Config) -> None:
    """Create an Example project (empty) on first boot so the dashboard isn't bare."""
    store = get_store(cfg.db_path)
'''
SEED_GUARD = '''    # LEO_EXAMPLE_SEED_PERSISTENCE_VERSION = 1
    _leo_example_absent = object()
    _leo_example_deleted = store.get_setting("leo_example_project_deleted_v1", _leo_example_absent)
    if _leo_example_deleted is not _leo_example_absent:
        if _leo_example_deleted != "1":
            raise RuntimeError("LEO_EXAMPLE_PERSISTENCE_MARKER_INVALID")
        return
'''
DELETE_ANCHOR = '''                self._delete_counted(
                    result["deleted_rows"],
                    "projects",
                    "project_id=?",
                    (project_id,),
                )
'''
DELETE_GUARD = '''                # LEO_EXAMPLE_DELETE_PERSISTENCE_VERSION = 1
                if project_id == "proj_example" and project is not None:
                    if result["deleted_rows"].get("projects") != 1:
                        raise RuntimeError("LEO_EXAMPLE_DELETE_NOT_CONFIRMED")
                    _leo_existing_marker = self._connection.execute(
                        "SELECT value FROM settings WHERE key=?",
                        ("leo_example_project_deleted_v1",),
                    ).fetchone()
                    if _leo_existing_marker is not None and _leo_existing_marker[0] != "1":
                        raise RuntimeError("LEO_EXAMPLE_PERSISTENCE_MARKER_INVALID")
                    self._connection.execute(
                        "INSERT INTO settings(key,value,updated_at) VALUES(?,?,CAST(strftime('%s','now') AS INTEGER)*1000) "
                        "ON CONFLICT(key) DO NOTHING",
                        ("leo_example_project_deleted_v1", "1"),
                    )
'''
TARGETS = {
    "openai4s/server/gateway.py": {
        "hashes": frozenset({
            "db33c3e3e7b4d618881e7899646d8de55c9c1794b47f57c5b97c7d2a2227a192",
            "ba955144415690db973211df4d5329b1420eb6eb369ed91cd13cb61e02ce4c67",
        }),
        "marker": SEED_MARKER, "anchor": SEED_ANCHOR, "guard": SEED_GUARD,
    },
    "openai4s/storage/deletion.py": {
        "hashes": frozenset({
            "e0e87e317d166218bf971e28a506c9cba627a00569d5da2b5734c1746b6b1cf8",
            "95c7d1be38e932f0378f2837f9ca5527fd4a2cc83cb22d56a7221d26cb9abe9e",
        }),
        "marker": DELETE_MARKER, "anchor": DELETE_ANCHOR, "guard": DELETE_GUARD,
    },
}


class PersistenceError(ValueError):
    pass


def persistent_source(relative: str, original: bytes) -> bytes:
    """Accept only exact audited originals or their exact resulting overlays."""
    if relative not in TARGETS:
        raise PersistenceError("EXAMPLE_PERSISTENCE_TARGET_INVALID")
    contract = TARGETS[relative]
    source = original.decode("utf-8")
    newline = "\r\n" if "\r\n" in source else "\n"
    guard = contract["guard"].replace("\n", newline).encode("utf-8")
    if contract["marker"] in source:
        if original.count(guard) != 1:
            raise PersistenceError("EXAMPLE_PERSISTENCE_OVERLAY_CONFLICT")
        candidate = original.replace(guard, b"", 1)
        if hashlib.sha256(candidate).hexdigest() not in contract["hashes"]:
            raise PersistenceError("EXAMPLE_PERSISTENCE_SOURCE_UNKNOWN")
        if persistent_source(relative, candidate) != original:
            raise PersistenceError("EXAMPLE_PERSISTENCE_OVERLAY_CONFLICT")
        return original
    if hashlib.sha256(original).hexdigest() not in contract["hashes"]:
        raise PersistenceError("EXAMPLE_PERSISTENCE_SOURCE_UNKNOWN")
    anchor = contract["anchor"].replace("\n", newline).encode("utf-8")
    if original.count(anchor) != 1:
        raise PersistenceError("EXAMPLE_PERSISTENCE_LAYOUT_CHANGED")
    updated = original.replace(anchor, anchor + guard, 1)
    compile(updated, "leo-example-persistence-overlay", "exec")
    return updated


def _replace(base: Path, target: Path, original: bytes, updated: bytes) -> None:
    backup_root = base / "example-persistence-originals"
    backup_root.mkdir(mode=0o700, exist_ok=True)
    if backup_root.is_symlink() or backup_root.resolve(strict=True) != backup_root:
        raise PersistenceError("EXAMPLE_PERSISTENCE_BACKUP_PATH_INVALID")
    backup = backup_root / (hashlib.sha256(original).hexdigest() + ".py")
    if backup.exists():
        if backup.is_symlink() or backup.read_bytes() != original:
            raise PersistenceError("EXAMPLE_PERSISTENCE_BACKUP_CONFLICT")
    else:
        with backup.open("xb") as handle:
            handle.write(original)
            handle.flush()
            os.fsync(handle.fileno())
    descriptor, temporary = tempfile.mkstemp(prefix=".leo-example-persistence-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, target.stat().st_mode & 0o777)
        if target.is_symlink() or target.resolve(strict=True) != target or target.read_bytes() != original:
            raise PersistenceError("EXAMPLE_PERSISTENCE_SOURCE_CHANGED")
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_persistence(base: Path, *, check: bool = False) -> dict:
    base = base.resolve(strict=True)
    sources = (base / "sources").resolve(strict=True)
    source_root = (base / "active-source").resolve(strict=True)
    if source_root == sources or sources not in source_root.parents:
        raise PersistenceError("EXAMPLE_PERSISTENCE_SOURCE_PATH_INVALID")
    prepared = []
    # A future/altered source is rejected before writing either target.
    for relative in TARGETS:
        target = source_root / relative
        if target.is_symlink() or target.resolve(strict=True) != target:
            raise PersistenceError("EXAMPLE_PERSISTENCE_SOURCE_PATH_INVALID")
        original = target.read_bytes()
        prepared.append((relative, target, original, persistent_source(relative, original)))
    files = []
    for relative, target, original, updated in prepared:
        changed = original != updated
        if changed and not check:
            _replace(base, target, original, updated)
        files.append({"source_file": relative,
            "previous_sha256": hashlib.sha256(original).hexdigest(),
            "sha256": hashlib.sha256(updated).hexdigest(),
            "applied": not check or not changed, "changed": changed and not check,
            "needs_update": changed if check else False})
    applied = all(item["applied"] for item in files)
    return {"version": VERSION, "example_persistence": applied, "applied": applied,
        "source_revision": source_root.name, "files": files,
        "setting_key": SETTING_KEY, "project_id": PROJECT_ID}


def persistence_status(database: Path) -> dict:
    """Read exactly the marker and target ID; never mutate or inspect secrets."""
    database = database.absolute()
    for candidate in (database, *database.parents):
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise PersistenceError("EXAMPLE_PERSISTENCE_DATABASE_PATH_INVALID")
    if not database.is_file():
        raise PersistenceError("EXAMPLE_PERSISTENCE_DATABASE_MISSING")
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        marker = connection.execute("SELECT value FROM settings WHERE key=?", (SETTING_KEY,)).fetchone()
        project = connection.execute("SELECT project_id FROM projects WHERE project_id=?", (PROJECT_ID,)).fetchone()
    finally:
        connection.close()
    if marker is not None and marker[0] != "1":
        raise PersistenceError("EXAMPLE_PERSISTENCE_MARKER_INVALID")
    return {"version": VERSION, "setting_key": SETTING_KEY, "project_id": PROJECT_ID,
        "marker_present": marker is not None, "marker_valid": marker is not None,
        "project_exists": project is not None, "read_only": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("apply", "check", "status"))
    parser.add_argument("--base", type=Path, default=Path.home() / ".local/share/leo-ai-studio")
    parser.add_argument("--database", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "status":
            result = persistence_status(args.database or args.base / "data/openai4s.db")
        else:
            if args.database is not None:
                raise PersistenceError("EXAMPLE_PERSISTENCE_ARGUMENT_INVALID")
            result = apply_persistence(args.base, check=args.action == "check")
        print(json.dumps({"ok": True, "data": result}, separators=(",", ":")))
        return 0
    except (OSError, ValueError, SyntaxError, sqlite3.Error) as exc:
        code = str(exc) if isinstance(exc, PersistenceError) else "EXAMPLE_PERSISTENCE_FAILED"
        print(json.dumps({"ok": False, "error": {"code": code,
            "message": "Example project deletion persistence could not be verified."}}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
