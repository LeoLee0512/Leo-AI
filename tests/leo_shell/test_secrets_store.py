"""Tests for leo_shell.secrets_store (DPAPI roundtrip and legacy migration).

Secret values used here are dummy fixtures; they must never appear in test
output or logs.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

from leo_shell import secrets_store
from leo_shell.secrets_store import SecretsStore

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="DPAPI is only available on Windows"
)

_TEST_KEY = "sk-test-fixture-key-0000000000000002"
_LEGACY_KEY = "sk-test-legacy-key-0000000000000003"


@pytest.fixture()
def store(tmp_path: Path) -> SecretsStore:
    return SecretsStore(tmp_path / "credentials")


# ---------------------------------------------------------------------------
# save / load / delete roundtrip


def test_roundtrip(store: SecretsStore, tmp_path: Path) -> None:
    store.save_key("profile-abc", _TEST_KEY)
    assert store.load_key("profile-abc") == _TEST_KEY

    raw = (tmp_path / "credentials" / "profile-abc.dpapi").read_bytes()
    assert raw.startswith(b"LEOCRED1\n")
    blob = base64.urlsafe_b64decode(raw[len(b"LEOCRED1\n"):])
    assert blob  # DPAPI blob decodes from base64url
    assert _TEST_KEY.encode() not in raw  # never stored in plaintext


def test_load_missing_returns_none(store: SecretsStore) -> None:
    assert store.load_key("profile-missing") is None


def test_overwrite(store: SecretsStore) -> None:
    store.save_key("profile-abc", _TEST_KEY)
    store.save_key("profile-abc", _LEGACY_KEY)
    assert store.load_key("profile-abc") == _LEGACY_KEY


def test_delete_key(store: SecretsStore) -> None:
    store.save_key("profile-abc", _TEST_KEY)
    store.delete_key("profile-abc")
    assert store.load_key("profile-abc") is None
    store.delete_key("profile-abc")  # idempotent


def test_entropy_roundtrip(store: SecretsStore) -> None:
    store.save_key("ipc", _TEST_KEY, entropy=b"LeoAIStudio/IPC/v1")
    assert store.load_key("ipc", entropy=b"LeoAIStudio/IPC/v1") == _TEST_KEY
    assert store.load_key("ipc") is None  # wrong entropy does not decrypt


def test_invalid_profile_id_rejected(store: SecretsStore) -> None:
    for bad in ("", "../escape", "a/b", "a\\b", "a b"):
        with pytest.raises(ValueError):
            store.save_key(bad, _TEST_KEY)
    assert store.load_key("../escape") is None  # load stays defensive
    store.delete_key("../escape")  # must not raise


def test_corrupt_file_returns_none(store: SecretsStore, tmp_path: Path) -> None:
    target = tmp_path / "credentials" / "profile-bad.dpapi"
    target.write_bytes(b"LEOCRED1\n!!!not-base64!!!")
    assert store.load_key("profile-bad") is None
    target.write_bytes(b"WRONGMAGIC\n" + base64.urlsafe_b64encode(b"garbage"))
    assert store.load_key("profile-bad") is None
    target.write_bytes(b"LEOCRED1\n" + base64.urlsafe_b64encode(b"not-a-dpapi-blob"))
    assert store.load_key("profile-bad") is None


def test_save_rejects_empty_key(store: SecretsStore) -> None:
    with pytest.raises(ValueError):
        store.save_key("profile-abc", "")


# ---------------------------------------------------------------------------
# legacy migration (best effort, always silent)


def _legacy_blob(payload: bytes, entropy: bytes | None = None) -> bytes:
    return secrets_store._protect(payload, entropy)


def test_migrate_legacy_json_payload(store: SecretsStore, tmp_path: Path) -> None:
    legacy = tmp_path / "credential.dpapi"
    legacy.write_bytes(_legacy_blob(json.dumps({"api_key": _LEGACY_KEY}).encode("utf-8")))
    assert store.migrate_legacy(legacy, "profile-abc") is None
    assert store.load_key("profile-abc") == _LEGACY_KEY
    assert legacy.is_file()  # legacy file is never deleted


def test_migrate_legacy_plain_string_payload(store: SecretsStore, tmp_path: Path) -> None:
    legacy = tmp_path / "credential.dpapi"
    legacy.write_bytes(_legacy_blob(_LEGACY_KEY.encode("utf-8")))
    store.migrate_legacy(legacy, "profile-abc")
    assert store.load_key("profile-abc") == _LEGACY_KEY


def test_migrate_legacy_json_string_payload(store: SecretsStore, tmp_path: Path) -> None:
    legacy = tmp_path / "credential.dpapi"
    legacy.write_bytes(_legacy_blob(json.dumps(_LEGACY_KEY).encode("utf-8")))
    store.migrate_legacy(legacy, "profile-abc")
    assert store.load_key("profile-abc") == _LEGACY_KEY


def test_migrate_legacy_base64_wrapped_blob(store: SecretsStore, tmp_path: Path) -> None:
    legacy = tmp_path / "credential.dpapi"
    legacy.write_bytes(base64.b64encode(_legacy_blob(json.dumps({"token": _LEGACY_KEY}).encode())))
    store.migrate_legacy(legacy, "profile-abc")
    assert store.load_key("profile-abc") == _LEGACY_KEY


def test_migrate_legacy_known_entropy_candidate(store: SecretsStore, tmp_path: Path) -> None:
    legacy = tmp_path / "credential.dpapi"
    legacy.write_bytes(
        _legacy_blob(json.dumps({"key": _LEGACY_KEY}).encode("utf-8"), entropy=b"LeoAIStudio")
    )
    store.migrate_legacy(legacy, "profile-abc")
    assert store.load_key("profile-abc") == _LEGACY_KEY


def test_migrate_legacy_failures_are_silent(store: SecretsStore, tmp_path: Path) -> None:
    # Missing file.
    assert store.migrate_legacy(tmp_path / "nope.dpapi", "profile-abc") is None
    # Garbage that is not a DPAPI blob.
    garbage = tmp_path / "credential.dpapi"
    garbage.write_bytes(b"\x00\x01\x02\x03 not dpapi")
    assert store.migrate_legacy(garbage, "profile-abc") is None
    # Valid DPAPI blob without any key-shaped field.
    no_key = tmp_path / "other.dpapi"
    no_key.write_bytes(_legacy_blob(json.dumps({"unrelated": 1}).encode("utf-8")))
    assert store.migrate_legacy(no_key, "profile-abc") is None
    # Valid blob but no profile to store into.
    valid = tmp_path / "valid.dpapi"
    valid.write_bytes(_legacy_blob(json.dumps({"api_key": _LEGACY_KEY}).encode("utf-8")))
    assert store.migrate_legacy(valid, None) is None

    assert store.load_key("profile-abc") is None
    assert garbage.is_file() and no_key.is_file() and valid.is_file()


def test_migrate_legacy_never_logs_secret(
    store: SecretsStore, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    legacy = tmp_path / "credential.dpapi"
    legacy.write_bytes(_legacy_blob(json.dumps({"api_key": _LEGACY_KEY}).encode("utf-8")))
    with caplog.at_level("DEBUG"):
        store.migrate_legacy(legacy, "profile-abc")
        store.migrate_legacy(tmp_path / "missing.dpapi", "profile-abc")
    assert store.load_key("profile-abc") == _LEGACY_KEY
    assert _LEGACY_KEY not in caplog.text
    assert _TEST_KEY not in caplog.text
