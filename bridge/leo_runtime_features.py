"""Compose audited runtime overlays; never migrate databases or start a daemon.

The packaged build receipt binds these installer components to a clean commit.
Historical installation receipts never authorize unknown source/module bytes.
Only active-source is allowed to be a link, to the one pinned sources directory.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import types
import uuid

VERSION = 1
UPSTREAM_REVISION = "a792c38d9984be428437b548db29baab3322f6dc"
COMPONENTS = (
    "leo_runtime_features.py", "leo_example_persistence.py", "leo_turn_binding.py",
    "leo_turn_binding_runtime.py", "leo_thought_runtime.py", "leo_reasoning.py",
)
MAX_SOURCE = 4 * 1024 * 1024

# Audited whole-file LF/CRLF identities for UPSTREAM_REVISION. Windows checkout
# bytes are transported unchanged to WSL by the existing source installer.
# These literal pairs extend only a component that declares the matching LF
# identity; input bytes are never normalized to manufacture a hash match.
# storage/deletion.py already declares both identities in its Example contract.
AUDITED_CRLF_SOURCE_PAIRS = {
    "openai4s/agent/engine.py": (
        "eb087db2144d9d7d0040968376e3208d8891c60844dc552980825556350c2d1c",
        "a89ef311c7d6cb05b7d2296ffbe6f9afa81bd4e646edadde8c1e4a5e27692322",
    ),
    "openai4s/agent/events.py": (
        "d0bc5b4ae08cfc4efca3a841fedbede25fc3e35b1ae218e6d915b440ee828b63",
        "b9438749fdd49d402df2747d0aa62c7acc3cc435a663a9f0fa5046ed6df9b827",
    ),
    "openai4s/config.py": (
        "8e50e9fa301993340f79a30a8072a41b535d6e618af8c7efece547e3cab5b33b",
        "5591f1225b60897bbe21f1097549e3600d6602d02bbaa148fc764d565948dd82",
    ),
    "openai4s/llm/messages.py": (
        "b61f50acb576c7e9dda65b0aa207a5eecaf7e6c328043f000ed7c3ad451e5690",
        "efdc633e182942898e206426ca36e66221c4bab6dcfccdacf00b6adfd575020a",
    ),
    "openai4s/llm/providers/openai.py": (
        "2a8e28801717493dd9bd26cff691978e31930aa957c6d0a4e52fed2af6ab6447",
        "51b7df5d4c8765412fa16650c9b73e23015598d71426f9e660d692555ad771e7",
    ),
    "openai4s/server/agent_run.py": (
        "cc52e2abd7f0ba287b41e34f14cdf518e15b2f774ea61cde5c568bc60d0659ed",
        "f9aa579e0efbfd75c2257163b3d3e0ab96acb74613dc533b435df594f8d1078a",
    ),
    "openai4s/server/completions.py": (
        "d917d69948778424b6c5ca772fe766c7386e321755e948d5903ca0a5179fecca",
        "fe566d90cc88f8ff6e8fb44280c54d74c3ac57e5ea5fc782055407641964dea6",
    ),
    "openai4s/server/gateway.py": (
        "db33c3e3e7b4d618881e7899646d8de55c9c1794b47f57c5b97c7d2a2227a192",
        "ba955144415690db973211df4d5329b1420eb6eb369ed91cd13cb61e02ce4c67",
    ),
    "openai4s/storage/frames.py": (
        "75c4bc0ab72c187008edb9898778072e7265eb6000c3a20b9d4db55c0a79f7f0",
        "2aa165ffc4d343569c2a20ce237442a5836cd914398cba27bde59d63b03a9c05",
    ),
    "openai4s/store.py": (
        "ebb2ca6ad7ae0b4084f63bbf3b388c23f09a189e614d46b182e54b4583492224",
        "1bd906bb6c45823b2eca9ff517a24a827291971616f810ed936f30ad3b208ec6",
    ),
}


class FeaturesError(ValueError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise FeaturesError("RUNTIME_FEATURES_RECEIPT_INVALID")
            result[key] = value
        return result
    def invalid(_):
        raise FeaturesError("RUNTIME_FEATURES_RECEIPT_INVALID")
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if type(value) is not dict:
        raise FeaturesError("RUNTIME_FEATURES_RECEIPT_INVALID")
    return value


def _encode(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _safe(path: Path, *, missing: bool = False) -> None:
    """Reject links/reparse points in every component, not just the final name."""
    if not path.is_absolute() or ".." in path.parts:
        raise FeaturesError("RUNTIME_FEATURES_PATH_INVALID")
    for item in reversed((path, *path.parents)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            if missing and item == path:
                return
            raise FeaturesError("RUNTIME_FEATURES_PATH_MISSING") from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise FeaturesError("RUNTIME_FEATURES_PATH_LINK")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise FeaturesError("RUNTIME_FEATURES_PATH_INVALID")
        if item == path and not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise FeaturesError("RUNTIME_FEATURES_PATH_INVALID")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise FeaturesError("RUNTIME_FEATURES_PATH_HARDLINK")


def _read(path: Path, *, missing: bool = False) -> bytes | None:
    _safe(path, missing=missing)
    try:
        with path.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise FeaturesError("RUNTIME_FEATURES_PATH_INVALID")
            raw = stream.read(MAX_SOURCE + 1)
    except FileNotFoundError:
        if missing:
            return None
        raise
    if len(raw) > MAX_SOURCE:
        raise FeaturesError("RUNTIME_FEATURES_SOURCE_TOO_LARGE")
    _safe(path)
    return raw


def _relative(name: str) -> str:
    if (type(name) is not str or "\\" in name or ":" in name
            or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            or not name.startswith("openai4s/") or not name.endswith(".py")
            or PurePosixPath(name).as_posix() != name):
        raise FeaturesError("RUNTIME_FEATURES_TARGET_INVALID")
    return name


def _source(base: Path) -> Path:
    _safe(base)
    _safe(base / "sources")
    expected = base / "sources" / UPSTREAM_REVISION
    _safe(expected)
    pointer = base / "active-source"
    # This one existing link is intentional. Its destination still passes the
    # complete no-link walk, and a link to any other revision is rejected.
    if pointer.resolve(strict=True) != expected:
        raise FeaturesError("RUNTIME_FEATURES_SOURCE_REVISION_MISMATCH")
    return expected


def _load_bundle(directory: Path) -> tuple[dict, dict, dict]:
    directory = Path(os.path.abspath(directory))
    _safe(directory)
    receipt_raw = _read(directory.parent / "build-receipt.json")
    receipt = _json(receipt_raw)
    source = receipt.get("source", {})
    if (type(receipt.get("schema_version")) is not int or receipt["schema_version"] != 1
            or receipt.get("mode") != "hermetic"
            or type(source) is not dict or source.get("dirty") is not False
            or type(source.get("files")) is not dict or type(receipt.get("artifacts")) is not dict
            or type(source.get("commit")) is not str
            or not re.fullmatch(r"[0-9a-f]{40}", source["commit"])):
        raise FeaturesError("RUNTIME_FEATURES_BUILD_RECEIPT_INVALID")
    raw = {}
    for name in COMPONENTS:
        value = _read(directory / name)
        key = "bridge/" + name
        artifact = receipt.get("artifacts", {}).get(key)
        if (type(artifact) is not dict or artifact.get("sha256") != digest(value)
                or type(artifact.get("size")) is not int or artifact["size"] != len(value)
                or source.get("files", {}).get(key) != digest(value)):
            raise FeaturesError("RUNTIME_FEATURES_COMPONENT_MISMATCH")
        compile(value, name, "exec")
        raw[name] = value
    if raw["leo_runtime_features.py"] != _read(Path(__file__).absolute()):
        raise FeaturesError("RUNTIME_FEATURES_INSTALLER_MISMATCH")
    modules = {}
    # Compile the verified bytes directly, never execute an unchecked pyc or
    # import a same-named component from another directory on sys.path.
    for name in ("leo_example_persistence.py", "leo_turn_binding.py", "leo_thought_runtime.py"):
        module = types.ModuleType("_leo_features_" + name[:-3])
        module.__file__ = str(directory / name)
        exec(compile(raw[name], name, "exec"), module.__dict__)
        modules[name] = module
    identity = {"package_source_commit": source["commit"],
                "build_receipt_sha256": digest(receipt_raw),
                "components": {name: digest(value) for name, value in raw.items()}}
    return identity, modules, raw


def _contracts(modules: dict, raw: dict) -> tuple[dict, dict]:
    example = modules["leo_example_persistence.py"]
    binding = modules["leo_turn_binding.py"]
    thought = modules["leo_thought_runtime.py"]
    contracts = {}
    def add(relative, hashes, edits):
        _relative(relative)
        if (not hashes or any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes)
                or not edits or any(type(a) is not str or type(b) is not str or not a or a == b for a,b in edits)):
            raise FeaturesError("RUNTIME_FEATURES_CONTRACT_INVALID")
        hashes = set(hashes)
        pair = AUDITED_CRLF_SOURCE_PAIRS.get(relative)
        if pair is not None and pair[0] in hashes:
            hashes.add(pair[1])
        entry = contracts.setdefault(relative, {"hashes": set(hashes), "layers": []})
        entry["hashes"].intersection_update(hashes)
        if not entry["hashes"]:
            raise FeaturesError("RUNTIME_FEATURES_BASE_CONFLICT")
        entry["layers"].append(edits)
    for relative, spec in example.TARGETS.items():
        add(relative, spec["hashes"], [(spec["anchor"], spec["anchor"] + spec["guard"])])
    for relative, source_sha in binding.BASE_SHA256.items():
        add(relative, {source_sha}, binding.edits(relative))
    for relative, spec in thought.patches().items():
        add(relative, {spec["source_sha256"]}, spec["replacements"])
    runtime = thought.runtime_modules()
    expected = {"openai4s/leo_reasoning.py": raw["leo_reasoning.py"],
                "openai4s/leo_thought.py": raw["leo_thought_runtime.py"]}
    if runtime != expected:
        raise FeaturesError("RUNTIME_FEATURES_RUNTIME_MODULE_MISMATCH")
    runtime["openai4s/server/leo_turn_binding.py"] = raw["leo_turn_binding_runtime.py"]
    if set(runtime) & set(contracts):
        raise FeaturesError("RUNTIME_FEATURES_TARGET_CONFLICT")
    for relative, value in runtime.items():
        _relative(relative)
        compile(value, relative, "exec")
    return contracts, runtime


def _edit(raw: bytes, edits: list, *, reverse: bool = False) -> bytes:
    newline = "\r\n" if b"\r\n" in raw else "\n"
    for before, after in reversed(edits) if reverse else edits:
        before, after = (text.replace("\n", newline).encode("utf-8") for text in (before, after))
        old, new = (after, before) if reverse else (before, after)
        if raw.count(old) != 1:
            raise FeaturesError("RUNTIME_FEATURES_LAYER_CONFLICT")
        raw = raw.replace(old, new, 1)
    return raw


def compose(relative: str, original: bytes, contract: dict) -> tuple[bytes, bytes]:
    """Reverse whole registered layers, verify the entire base, then rebuild.

    A marker or a receipt is never a trust decision. Every accepted current
    byte must also exactly equal a reconstruction from a fixed known base.
    """
    layers = contract["layers"]
    base = None
    for count in range(len(layers) + 1):
        for order in itertools.permutations(range(len(layers)), count):
            try:
                candidate = original
                for i in reversed(order):
                    candidate = _edit(candidate, layers[i], reverse=True)
                if digest(candidate) not in contract["hashes"]:
                    continue
                rebuilt = candidate
                for i in order:
                    rebuilt = _edit(rebuilt, layers[i])
                if rebuilt == original:
                    base = candidate
                    break
            except FeaturesError:
                continue
        if base is not None:
            break
    if base is None:
        raise FeaturesError("RUNTIME_FEATURES_SOURCE_UNKNOWN")
    updated = base
    for layer in layers:
        updated = _edit(updated, layer)
    reverse = updated
    for layer in reversed(layers):
        reverse = _edit(reverse, layer, reverse=True)
    if reverse != base or digest(reverse) not in contract["hashes"]:
        raise FeaturesError("RUNTIME_FEATURES_COMPOSITION_INVALID")
    compile(updated, relative, "exec")
    return base, updated


def _prepare(base: Path, contracts: dict, runtime: dict) -> tuple[Path, list]:
    source = _source(base)
    prepared = []
    for relative in sorted(set(contracts) | set(runtime)):
        target = source / relative
        original = _read(target, missing=relative in runtime)
        if relative in contracts:
            canonical, updated = compose(relative, original, contracts[relative])
        else:
            canonical, updated = None, runtime[relative]
            # There is no previously released full-features module version in
            # v1. Future upgrades must register audited old hashes in code;
            # a historical receipt alone cannot bless arbitrary old bytes.
            if original is not None and original != updated:
                raise FeaturesError("RUNTIME_FEATURES_RUNTIME_MODULE_UNKNOWN")
        prepared.append({"relative": relative, "path": target, "original": original,
                         "canonical": canonical, "updated": updated})
    return source, prepared


def _mkdir(path: Path) -> None:
    _safe(path, missing=True)
    path.mkdir(mode=0o700, exist_ok=True)
    _safe(path)


def _exclusive(path: Path, raw: bytes, *, existing: bool = False) -> None:
    _safe(path, missing=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError:
        if existing and _read(path) == raw:
            return
        raise FeaturesError("RUNTIME_FEATURES_EVIDENCE_CONFLICT") from None
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _replace(path: Path, expected: bytes | None, updated: bytes) -> None:
    if _read(path, missing=True) != expected:
        raise FeaturesError("RUNTIME_FEATURES_SOURCE_CHANGED")
    mode = path.stat().st_mode & 0o777 if expected is not None else 0o644
    fd, temporary = tempfile.mkstemp(prefix=".leo-features-", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        if _read(path, missing=True) != expected:
            raise FeaturesError("RUNTIME_FEATURES_SOURCE_CHANGED")
        if expected is None:
            # Atomic creation must never replace a file that appeared after
            # preflight. Link is exclusive on both NTFS and the Linux runtime.
            os.link(temporary, path)
            temporary.unlink()
        else:
            os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _receipt(identity: dict, prepared: list) -> dict:
    return {"version": VERSION, "source_revision": UPSTREAM_REVISION, **identity,
            "example_persistence": True, "conversation_runtime": True,
            "targets": {p["relative"]: {"sha256": digest(p["updated"]),
                "canonical_sha256": digest(p["canonical"]) if p["canonical"] is not None else None}
                for p in prepared}}


def apply_features(base: Path, *, check: bool = False, bundle: Path | None = None) -> dict:
    base = Path(os.path.abspath(base))
    identity, modules, raw = _load_bundle(bundle or Path(__file__).absolute().parent)
    contracts, runtime = _contracts(modules, raw)
    source, prepared = _prepare(base, contracts, runtime)
    receipt = _receipt(identity, prepared)
    receipt_raw = _encode(receipt)
    receipt_id = digest(receipt_raw)
    evidence = base / "runtime-features"
    receipt_path = evidence / (receipt_id + ".json")
    if evidence.exists() or evidence.is_symlink():
        _safe(evidence)
        existing = _read(receipt_path, missing=True)
        if existing is not None and existing != receipt_raw:
            raise FeaturesError("RUNTIME_FEATURES_RECEIPT_CONFLICT")
    else:
        existing = None
    changed = any(p["original"] != p["updated"] for p in prepared)
    applied = not changed and existing == receipt_raw
    result = {**receipt, "applied": applied, "changed": False,
              "needs_update": not applied, "receipt_sha256": receipt_id}
    if check or applied:
        return result

    lock = base / "runtime-features.lock"
    lock_raw = _encode({"attempt": uuid.uuid4().hex, "pid": os.getpid()})
    _exclusive(lock, lock_raw)
    replaced = []
    attempt = uuid.uuid4().hex
    try:
        # Recheck every file and the active pointer after acquiring the lock.
        source_again, current = _prepare(base, contracts, runtime)
        if source_again != source or any(a["original"] != b["original"] for a,b in zip(prepared,current)):
            raise FeaturesError("RUNTIME_FEATURES_SOURCE_CHANGED")
        _mkdir(evidence)
        originals = evidence / "originals"
        _mkdir(originals)
        for item in prepared:
            if item["original"] is not None:
                _exclusive(originals / (digest(item["original"]) + ".py"), item["original"], existing=True)
        _exclusive(evidence / (attempt + ".started.json"), _encode({
            "version": VERSION, "receipt_sha256": receipt_id,
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_revision": UPSTREAM_REVISION,
            "previous": {p["relative"]: digest(p["original"]) if p["original"] is not None else None for p in prepared}}))
        for item in prepared:
            if _source(base) != source:
                raise FeaturesError("RUNTIME_FEATURES_SOURCE_CHANGED")
            if item["original"] != item["updated"]:
                replaced.append(item)
                _replace(item["path"], item["original"], item["updated"])
        # A success receipt is the last operation after all runtime bytes have
        # been read back, including new helper modules and unchanged targets.
        if _source(base) != source or any(_read(p["path"]) != p["updated"] for p in prepared):
            raise FeaturesError("RUNTIME_FEATURES_POSTCHECK_FAILED")
        if _load_bundle(bundle or Path(__file__).absolute().parent)[0] != identity:
            raise FeaturesError("RUNTIME_FEATURES_COMPONENTS_CHANGED")
        _exclusive(receipt_path, receipt_raw, existing=True)
        if _read(receipt_path) != receipt_raw:
            raise FeaturesError("RUNTIME_FEATURES_RECEIPT_CONFLICT")
        return {**result, "applied": True, "changed": changed, "needs_update": False}
    except Exception:
        rollback_ok = True
        for item in reversed(replaced):
            try:
                current_bytes = _read(item["path"], missing=True)
                if current_bytes == item["original"]:
                    continue
                if current_bytes != item["updated"]:
                    raise FeaturesError("RUNTIME_FEATURES_ROLLBACK_CONFLICT")
                if item["original"] is None:
                    item["path"].unlink()
                else:
                    _replace(item["path"], item["updated"], item["original"])
            except Exception:
                rollback_ok = False
        if evidence.exists():
            _exclusive(evidence / (attempt + ".failed.json"), _encode({
                "version": VERSION, "receipt_sha256": receipt_id,
                "failed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "rollback_ok": rollback_ok, "success": False}))
        if not rollback_ok:
            raise FeaturesError("RUNTIME_FEATURES_ROLLBACK_INCOMPLETE") from None
        raise
    finally:
        # Never remove another process's replacement lock.
        if _read(lock, missing=True) == lock_raw:
            lock.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("apply", "check"))
    parser.add_argument("--base", type=Path, default=Path.home() / ".local/share/leo-ai-studio")
    args = parser.parse_args(argv)
    try:
        result = apply_features(args.base, check=args.action == "check")
        print(json.dumps({"ok": True, "data": result}, separators=(",", ":")))
        return 0
    except Exception as exc:
        # Do not print source snippets, arbitrary exceptions, paths or keys.
        code = str(exc) if isinstance(exc, FeaturesError) else "RUNTIME_FEATURES_FAILED"
        print(json.dumps({"ok": False, "error": {"code": code,
            "message": "Runtime features could not be verified; daemon startup is blocked."}}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
