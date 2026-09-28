"""Small dependency-free validator for the checked-in JSON Schema subset.

The build virtualenv intentionally has no runtime dependency on ``jsonschema``.
This module implements only keywords used by the four governance schemas and
fails closed on unsupported keywords in those schemas.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any


class SchemaError(ValueError):
    pass


_SUPPORTED = {
    "$schema",
    "$id",
    "$ref",
    "$defs",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "minItems",
    "maxItems",
    "uniqueItems",
    "enum",
    "const",
    "pattern",
    "minLength",
    "minimum",
    "maximum",
    "anyOf",
    "allOf",
}


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaError(f"only local JSON pointers are supported, got {ref!r}")
    current: Any = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise SchemaError(f"unresolved schema reference {ref!r}")
        current = current[token]
    if not isinstance(current, dict):
        raise SchemaError(f"schema reference {ref!r} does not name an object")
    return current


def _json_equal(left: Any, right: Any) -> bool:
    """JSON booleans are not numbers; Python's True == 1 is not this contract."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) or isinstance(right, dict):
        return isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys() and all(
            _json_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) or isinstance(right, list):
        return isinstance(left, list) and isinstance(right, list) and len(left) == len(right) and all(
            _json_equal(a, b) for a, b in zip(left, right))
    return left == right


def validate(instance: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def walk(value: Any, rule: dict[str, Any], path: str) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{path}: non-finite number is not JSON")
            return
        unknown = set(rule) - _SUPPORTED
        if unknown:
            raise SchemaError(f"unsupported schema keyword(s): {sorted(unknown)}")

        if "$ref" in rule:
            walk(value, _resolve_ref(schema, rule["$ref"]), path)
            return

        if "allOf" in rule:
            for sub in rule["allOf"]:
                walk(value, sub, path)

        if "anyOf" in rule:
            alternatives: list[list[str]] = []
            for sub in rule["anyOf"]:
                before = len(errors)
                walk(value, sub, path)
                alternatives.append(errors[before:])
                del errors[before:]
            if all(alternatives):
                errors.append(f"{path}: does not match any allowed schema")

        expected = rule.get("type")
        if expected is not None:
            allowed = [expected] if isinstance(expected, str) else list(expected)
            if not any(_type_matches(value, item) for item in allowed):
                errors.append(f"{path}: expected type {allowed}, got {type(value).__name__}")
                return

        if "const" in rule and not _json_equal(value, rule["const"]):
            errors.append(f"{path}: expected constant {rule['const']!r}")
        if "enum" in rule and not any(_json_equal(value, choice) for choice in rule["enum"]):
            errors.append(f"{path}: {value!r} is not in {rule['enum']!r}")

        if isinstance(value, str):
            if "minLength" in rule and len(value) < rule["minLength"]:
                errors.append(f"{path}: string is shorter than {rule['minLength']}")
            if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
                errors.append(f"{path}: string does not match {rule['pattern']!r}")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in rule and value < rule["minimum"]:
                errors.append(f"{path}: value is below {rule['minimum']}")
            if "maximum" in rule and value > rule["maximum"]:
                errors.append(f"{path}: value is above {rule['maximum']}")

        if isinstance(value, dict):
            for key in rule.get("required", []):
                if key not in value:
                    errors.append(f"{path}: missing required property {key!r}")
            properties = rule.get("properties", {})
            for key, item in value.items():
                if key in properties:
                    walk(item, properties[key], f"{path}.{key}")
                elif rule.get("additionalProperties") is False:
                    errors.append(f"{path}: unexpected property {key!r}")

        if isinstance(value, list):
            if "minItems" in rule and len(value) < rule["minItems"]:
                errors.append(f"{path}: expected at least {rule['minItems']} items")
            if "maxItems" in rule and len(value) > rule["maxItems"]:
                errors.append(f"{path}: expected at most {rule['maxItems']} items")
            if rule.get("uniqueItems"):
                if any(_json_equal(item, earlier) for i, item in enumerate(value) for earlier in value[:i]):
                    errors.append(f"{path}: array items are not unique")
            if "items" in rule:
                for index, item in enumerate(value):
                    walk(item, rule["items"], f"{path}[{index}]")

    walk(instance, schema, "$")
    return errors
