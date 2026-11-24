"""Amendment register invariants (Constitution chapter 60; A-0002 second review, item 6).

An amendment file starts with a frontmatter block::

    ---
    amendmentId: A-0002
    oldVersion: 1.1
    newVersion: 1.2
    status: PROPOSED
    effectiveDate: PENDING
    dependsOn:
      - amendmentId: A-0001
        requiredStatus: ACCEPTED
        requiredConstitutionVersion: "1.1"
    ---

``validate_amendment_register`` enforces, over every file in
``governance/AMENDMENTS/``:

* R1 ids unique, status in {PROPOSED, ACCEPTED, REJECTED}, versions ``x.y``;
* R2 ACCEPTED needs a real effectiveDate, PROPOSED needs PENDING;
* R3 the ACCEPTED amendments form one chain ``1.0 -> ... -> constitution.version``:
  each ACCEPTED oldVersion equals the previous ACCEPTED newVersion (1.0 for
  the first), and the Constitution's declared version equals the last
  ACCEPTED newVersion (1.0 when none) -- so ``A-0002 ACCEPTED`` while
  ``A-0001 PROPOSED`` or while the Constitution says 1.0 is rejected;
* R4 every dependsOn target exists; for an ACCEPTED amendment each target
  must have the required status and, when given, the required Constitution
  version must equal the target's newVersion;
* R5 (final closure review, Issue 1) when ``effective_versions`` is given --
  the runtime's ``SUPPORTED_CONSTITUTION_VERSIONS`` -- every ACCEPTED
  newVersion is in it and no PROPOSED / REJECTED newVersion is: a PROPOSED
  amendment's semantics must be unreachable at runtime, and an ACCEPTED one's
  must be reachable.

The generic ``dependsOn`` costs one parser and one loop; a special case for
A-0002 would have to be re-invented for every later amendment.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

STATUSES = ("PROPOSED", "ACCEPTED", "REJECTED")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+$")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_ID = re.compile(r"^A-[0-9]{4}$")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> dict[str, Any]:
    """The minimal YAML subset the register uses: ``key: value`` lines and a ``dependsOn`` list of mappings."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("amendment file does not start with a frontmatter block")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("frontmatter block is not closed") from exc
    result: dict[str, Any] = {}
    depends: list[dict[str, str]] | None = None
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if raw.startswith("  ") and depends is not None:
            item = raw.strip()
            if item.startswith("- "):
                depends.append({})
                item = item[2:].strip()
            if not depends:
                raise ValueError("dependsOn entry must start with '- '")
            key, _, value = item.partition(":")
            if not _:
                raise ValueError(f"malformed dependsOn line: {raw!r}")
            depends[-1][key.strip()] = _unquote(value)
            continue
        depends = None
        key, sep, value = raw.partition(":")
        if not sep or raw.startswith(" "):
            raise ValueError(f"malformed frontmatter line: {raw!r}")
        key = key.strip()
        if key == "dependsOn":
            depends = []
            result[key] = depends
        else:
            result[key] = _unquote(value)
    return result


def load_amendment_register(directory: str | Path) -> list[dict[str, Any]]:
    folder = Path(directory)
    if not folder.is_dir():
        raise OSError(f"amendment register directory not found: {folder}")
    register: list[dict[str, Any]] = []
    for path in sorted(folder.glob("A-*.md")):
        entry = parse_frontmatter(path.read_text(encoding="utf-8"))
        entry["_file"] = path.name
        register.append(entry)
    return register


def _version_key(value: str) -> tuple[int, int]:
    major, minor = value.split(".")
    return int(major), int(minor)


def validate_amendment_register(
    amendments: Sequence[Mapping[str, Any]],
    *,
    constitution_version: str,
    effective_versions: Sequence[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    by_id: dict[str, Mapping[str, Any]] = {}
    for entry in amendments:
        label = entry.get("amendmentId") or entry.get("_file", "?")
        for key in ("amendmentId", "oldVersion", "newVersion", "status", "effectiveDate"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                errors.append(f"{label}: frontmatter field {key!r} missing")
        if errors:
            return errors
        if not _ID.fullmatch(entry["amendmentId"]):
            errors.append(f"{label}: amendmentId must look like A-0001")
        if entry["amendmentId"] in by_id:
            errors.append(f"{label}: amendmentId registered twice")
        by_id[entry["amendmentId"]] = entry
        if entry["status"] not in STATUSES:
            errors.append(f"{label}: status {entry['status']!r} is not one of {STATUSES}")
        for key in ("oldVersion", "newVersion"):
            if not _VERSION.fullmatch(entry[key]):
                errors.append(f"{label}: {key} must be major.minor")
        if entry["status"] == "ACCEPTED" and not _DATE.fullmatch(entry["effectiveDate"]):
            errors.append(f"{label}: ACCEPTED needs an effectiveDate (YYYY-MM-DD)")
        if entry["status"] == "PROPOSED" and entry["effectiveDate"] != "PENDING":
            errors.append(f"{label}: PROPOSED must carry effectiveDate PENDING")
    if errors:
        return errors

    accepted = sorted((e for e in amendments if e["status"] == "ACCEPTED"), key=lambda e: _version_key(e["oldVersion"]))
    expected = "1.0"
    for entry in accepted:
        if entry["oldVersion"] != expected:
            errors.append(
                f"{entry['amendmentId']}: ACCEPTED against version {entry['oldVersion']} but the accepted chain is at {expected}"
            )
        expected = entry["newVersion"]
    if constitution_version != expected:
        errors.append(
            f"constitution declares version {constitution_version!r} but the accepted amendment chain ends at {expected}"
        )

    for entry in amendments:
        for index, dependency in enumerate(entry.get("dependsOn", []) or []):
            path = f"{entry['amendmentId']}.dependsOn[{index}]"
            target_id = dependency.get("amendmentId")
            target = by_id.get(target_id or "")
            if target is None:
                errors.append(f"{path}: depends on unknown amendment {target_id!r}")
                continue
            if entry["status"] != "ACCEPTED":
                continue
            required_status = dependency.get("requiredStatus", "ACCEPTED")
            if target["status"] != required_status:
                errors.append(f"{path}: {target_id} is {target['status']}, required {required_status}")
            required_version = dependency.get("requiredConstitutionVersion")
            if required_version is not None and target["newVersion"] != required_version:
                errors.append(f"{path}: {target_id} yields version {target['newVersion']}, required {required_version}")

    if effective_versions is not None:
        effective = set(effective_versions)
        for entry in amendments:
            if entry["status"] == "ACCEPTED" and entry["newVersion"] not in effective:
                errors.append(
                    f"{entry['amendmentId']}: ACCEPTED but Constitution {entry['newVersion']} is not an effective runtime version"
                )
            if entry["status"] != "ACCEPTED" and entry["newVersion"] in effective:
                errors.append(
                    f"{entry['amendmentId']}: {entry['status']} but Constitution {entry['newVersion']} is already an effective "
                    "runtime version -- a proposed amendment's semantics leaked into the runtime"
                )
    return errors
