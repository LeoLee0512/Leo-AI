"""The one canonical JSON byte representation used by pre-lock and lock.

There is intentionally no "preserve the draft verbatim" path.  A JSON source
is canonical exactly when its bytes equal ``canonical_bytes(json.loads(...))``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CanonicalJSONResult:
    path: Path
    obj: Any | None
    errors: tuple[str, ...]
    sha256: str

    @property
    def passed(self) -> bool:
        return not self.errors


def canonical_bytes(obj: Any) -> bytes:
    """Return the protocol's sole canonical representation."""

    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def strict_json_loads(text: str) -> Any:
    """Reject ambiguous objects and non-JSON numeric constants before hashing."""
    def constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON property: {key}")
            result[key] = value
        return result

    obj = json.loads(text, parse_constant=constant, object_pairs_hook=pairs)
    # Also detects overflow such as 1e999 parsed as infinity.
    canonical_bytes(obj)
    return obj


def canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def validate_canonical_json(path: str | Path) -> CanonicalJSONResult:
    source = Path(path)
    errors: list[str] = []
    try:
        raw = source.read_bytes()
    except OSError as exc:
        return CanonicalJSONResult(source, None, (f"cannot read file: {exc}",), "")

    digest = hashlib.sha256(raw).hexdigest()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("UTF-8 BOM is forbidden")
    if b"\r" in raw:
        errors.append("CR bytes are forbidden; line endings must be LF")
    if not raw.endswith(b"\n"):
        errors.append("file must end with exactly one LF")
    elif raw.endswith(b"\n\n"):
        errors.append("file has more than one trailing LF")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"invalid UTF-8: {exc}")
        return CanonicalJSONResult(source, None, tuple(errors), digest)

    try:
        obj = strict_json_loads(text)
    except (ValueError, OverflowError) as exc:
        errors.append(f"invalid JSON: {exc}")
        return CanonicalJSONResult(source, None, tuple(errors), digest)

    if raw != canonical_bytes(obj):
        errors.append(
            "bytes are not canonical json.dumps(obj, ensure_ascii=False, indent=2) + LF"
        )
    return CanonicalJSONResult(source, obj, tuple(errors), digest)
