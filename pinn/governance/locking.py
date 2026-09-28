"""Non-self-referential lock construction and independent verification.

The public pre-lock command never calls :func:`write_lock`.  That function is
provided for the future, explicitly approved P2 operation and is testable only
against temporary fixtures in the v1.3 draft.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .canonical import canonical_bytes, validate_canonical_json
from .jsonschema_lite import SchemaError, validate as validate_schema


LOCK_FIELD_ORDER = (
    "specSha256",
    "protocolSha256",
    "adversarialManifestSha256",
    "constitutionSha256",
    "constitutionVersion",
    "lockVersion",
    "lockedAt",
)
#: Constitution versions a lock may bind.  1.1 = 1.0 + amendment A-0001
#: (ACCEPTED 2026-09-15).  A lock always binds one exact version and the exact
#: bytes of that version's canonical file; the pre-lock run additionally
#: requires the bound version to equal the version the Constitution declares.
SUPPORTED_CONSTITUTION_VERSIONS: tuple[str, ...] = ("1.0", "1.1", "1.2")
DRY_RUN_LOCKED_AT_SENTINEL = "DRY-RUN-ONLY--LOCKED-AT-NOT-SET"
_LOCK_LOCATION = Path("specs/poisson-1d/v1.0/lock.json")
_PRECONDITIONS = (
    "PRELOCK_VALIDATION passes without requiring a final lock.json",
    "spec.json, protocol.json and adversarial/core_manifest.json each equal the one canonical JSON serializer output",
    "none of the three hash inputs contains a self digest",
    "spec.json has lockedAt == null",
    "spec, protocol, lock draft and adversarial manifest schemas and semantic constraints pass",
    "the antiCollision check in protocol.json passes",
    "all core-suite expected verdicts exist in adversarial/core_manifest.json before the suite is first executed",
    "human approval to enter P2 has been recorded",
)
_PAYLOAD_INPUT = "UTF-8 bytes of the seven content fields, in the registered order, each followed by a single newline"
_PAYLOAD_FORMULA = "lockSha256 = SHA256(specSha256 + LF + protocolSha256 + LF + adversarialManifestSha256 + LF + constitutionSha256 + LF + constitutionVersion + LF + lockVersion + LF + lockedAt + LF)"


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value
    ) is None:
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() == timezone.utc.utcoffset(None)
    except ValueError:
        return False


def build_lock_payload(fields: Mapping[str, Any], *, dry_run: bool = False) -> bytes:
    values: list[str] = []
    for name in LOCK_FIELD_ORDER:
        value = fields.get(name)
        if dry_run and name == "lockedAt" and value is None:
            value = DRY_RUN_LOCKED_AT_SENTINEL
        if not isinstance(value, str) or not value:
            raise ValueError(f"lock payload field {name!r} must be a non-empty string")
        if name.endswith("Sha256") and re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"lock payload field {name!r} must be a lowercase SHA-256 digest")
        if name == "constitutionVersion" and value not in SUPPORTED_CONSTITUTION_VERSIONS:
            raise ValueError("unsupported Constitution version")
        if name == "lockVersion" and value != "1":
            raise ValueError("unsupported lock version")
        if name == "lockedAt" and not (
            (dry_run and value == DRY_RUN_LOCKED_AT_SENTINEL) or _valid_timestamp(value)
        ):
            raise ValueError("lockedAt must be an actual UTC ISO-8601 timestamp")
        values.append(value)
    return ("\n".join(values) + "\n").encode("utf-8")


def candidate_payload_sha256(fields: Mapping[str, Any]) -> str:
    """Hash a dry-run-only payload with a conspicuous timestamp sentinel."""

    return hashlib.sha256(build_lock_payload(fields, dry_run=True)).hexdigest()


def build_locked_document(
    draft: Mapping[str, Any],
    *,
    spec_sha256: str,
    protocol_sha256: str,
    adversarial_manifest_sha256: str,
    locked_at: str,
) -> dict[str, Any]:
    """Return final lock content without writing any file."""

    if draft.get("lockState") != "DRAFT" or any(
        draft.get(key) is not None
        for key in ("specSha256", "protocolSha256", "adversarialManifestSha256", "lockedAt", "lockSha256")
    ):
        raise ValueError("lock construction requires an unfilled DRAFT, not an existing lock")
    result = deepcopy(dict(draft))
    result["lockState"] = "LOCKED"
    result["specSha256"] = spec_sha256
    result["protocolSha256"] = protocol_sha256
    result["adversarialManifestSha256"] = adversarial_manifest_sha256
    result["lockedAt"] = locked_at
    result["lockSha256"] = hashlib.sha256(build_lock_payload(result)).hexdigest()
    errors = _metadata_errors(result)
    if errors:
        raise ValueError("invalid lock document: " + "; ".join(errors))
    return result


def write_lock(
    destination: str | Path,
    *,
    draft: Mapping[str, Any],
    spec_sha256: str,
    protocol_sha256: str,
    adversarial_manifest_sha256: str,
    locked_at: str,
    prelock_validator: Callable[[], bool],
    repo_root: str | Path | None = None,
) -> None:
    """Future P2 writer: validate final bytes, then exclusively create a lock.

    It refuses to overwrite.  This function is intentionally not exposed by
    the pre-lock CLI and must not be called without human approval.
    Any failed or interrupted write remains visible and must not be overwritten.
    """

    if prelock_validator() is not True:
        raise ValueError("PRELOCK_VALIDATION did not PASS; lock creation refused")
    target = Path(destination)
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"lock already exists and will not be overwritten: {target}")
    document = build_locked_document(
        draft,
        spec_sha256=spec_sha256,
        protocol_sha256=protocol_sha256,
        adversarial_manifest_sha256=adversarial_manifest_sha256,
        locked_at=locked_at,
    )
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root(target.resolve())
    errors = _binding_errors(target, document, root)
    if errors:
        raise ValueError("lock inputs are not valid: " + "; ".join(errors))
    target.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL inside 'xb' closes the previous exists()/write_bytes() overwrite race.
    with target.open("xb") as stream:
        stream.write(canonical_bytes(document))
        stream.flush()
        os.fsync(stream.fileno())
    errors = verify_lock_details(target, repo_root=root)
    if errors:
        raise ValueError("created lock failed read-back verification; retained for evidence: " + "; ".join(errors))


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ValueError(f"cannot locate repository root from {start}")


def _resolve(lock_path: Path, value: str, *, repo_root: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or candidate.drive or ".." in candidate.parts:
        raise ValueError("lock bindings must be repository-relative paths without traversal")
    source = lock_path.parent / candidate if "/" not in value and "\\" not in value else repo_root / candidate
    resolved = source.resolve()
    if not resolved.is_relative_to(repo_root.resolve()):
        raise ValueError("lock binding escapes the repository")
    return resolved


def _metadata_errors(lock: Mapping[str, Any]) -> list[str]:
    schema_path = Path(__file__).with_name("schemas") / "lock.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = validate_schema(lock, schema)
    if lock.get("lockState") != "LOCKED":
        errors.append("a formal lock must have lockState=LOCKED")
    if not _valid_timestamp(lock.get("lockedAt")):
        errors.append("lockedAt must be an actual UTC ISO-8601 timestamp")
    definition = lock.get("lockSha256Definition")
    if not isinstance(definition, dict) or definition.get("fieldOrder") != list(LOCK_FIELD_ORDER):
        errors.append("lock payload field order differs from the registered seven-field contract")
    if isinstance(definition, dict) and (
        definition.get("input") != _PAYLOAD_INPUT or definition.get("formula") != _PAYLOAD_FORMULA
    ):
        errors.append("lock payload definition differs from the registered seven-field contract")
    if lock.get("preconditions") != list(_PRECONDITIONS):
        errors.append("lock preconditions differ from the registered prelock and approval requirements")
    return errors


def _binding_errors(path: Path, lock: Mapping[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if path.resolve() != (root / _LOCK_LOCATION).resolve() or not path.resolve().is_relative_to(root):
        errors.append("lock must occupy specs/poisson-1d/v1.0/lock.json inside its repository")
        return errors
    bindings = (
        ("specPath", "specSha256"),
        ("protocolPath", "protocolSha256"),
        ("adversarialManifestPath", "adversarialManifestSha256"),
        ("constitutionPath", "constitutionSha256"),
    )
    for path_key, digest_key in bindings:
        relative, expected = lock.get(path_key), lock.get(digest_key)
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append(f"lock binding {path_key}/{digest_key} is incomplete")
            continue
        try:
            source = _resolve(path, relative, repo_root=root)
            raw = source.read_bytes()
            actual = hashlib.sha256(raw).hexdigest()
            if path_key != "constitutionPath":
                checked = validate_canonical_json(source)
                if not checked.passed or not isinstance(checked.obj, dict):
                    errors.append(f"{path_key} target is not a canonical JSON object")
                # Use the digest of the same read whose canonical form was checked.
                actual = checked.sha256
            elif raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
                errors.append("Constitution bytes violate UTF-8 without BOM / LF encoding")
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(f"cannot validate {path_key} target: {exc}")
            continue
        if actual != expected:
            errors.append(f"{digest_key} mismatch for {source}")
    return errors


def verify_lock_details(lock_path: str | Path, *, repo_root: str | Path | None = None) -> list[str]:
    errors: list[str] = []
    try:
        path = Path(lock_path)
        checked = validate_canonical_json(path)
        if not checked.passed or not isinstance(checked.obj, dict):
            return list(checked.errors or ("lock root must be an object",))
        lock = checked.obj
        root = Path(repo_root).resolve() if repo_root is not None else _repo_root(path.resolve())
        errors.extend(_metadata_errors(lock))
        # Do not follow paths until fixed-path schema checks have succeeded.
        if errors:
            return errors
        errors.extend(_binding_errors(path, lock, root))
        actual_lock_sha = hashlib.sha256(build_lock_payload(lock)).hexdigest()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, SchemaError) as exc:
        errors.append(str(exc))
    else:
        if actual_lock_sha != lock.get("lockSha256"):
            errors.append("lockSha256 payload mismatch")
    return errors


def verify_lock(lock_path: str | Path, *, repo_root: str | Path | None = None) -> bool:
    return not verify_lock_details(lock_path, repo_root=repo_root)
