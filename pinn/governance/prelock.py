"""Executable PRELOCK_VALIDATION pipeline.

This module is read-only: it validates candidate draft bytes and reports
candidate digests, but it has no code path that creates ``lock.json`` or starts
training.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable, Mapping

from .canonical import CanonicalJSONResult, validate_canonical_json
from .jsonschema_lite import SchemaError, validate as validate_schema
from .amendments import load_amendment_register, validate_amendment_register
from .locking import SUPPORTED_CONSTITUTION_VERSIONS, candidate_payload_sha256
from .state_machine import ADMISSIBLE_ROOT_CAUSES_BY_VERSION
from .semantic import (
    validate_lock_draft,
    validate_manifest,
    validate_protocol,
    validate_spec,
    _check_source_hash,
)


SCHEMA_DIR = Path(__file__).with_name("schemas")
REQUIRED_GITATTRIBUTES = (
    "specs/**/spec.json      text eol=lf",
    "specs/**/protocol.json  text eol=lf",
    "specs/**/lock.json      text eol=lf",
    "adversarial/**/core_manifest.json text eol=lf",
    "*.npy binary",
)


@dataclass(frozen=True)
class PrelockPaths:
    repo_root: Path
    constitution: Path
    spec: Path
    protocol: Path
    lock_draft: Path
    manifest: Path
    gitattributes: Path

    @classmethod
    def defaults(cls, repo_root: str | Path) -> "PrelockPaths":
        root = Path(repo_root).resolve()
        governance = root / "governance"
        return cls(
            repo_root=root,
            constitution=governance / "PINN_RESEARCH_CONSTITUTION.md",
            spec=governance / "POISSON_1D_V1.0_spec.draft.json",
            protocol=governance / "POISSON_1D_V1.0_protocol.draft.json",
            lock_draft=governance / "POISSON_1D_V1.0_lock.draft.json",
            manifest=root / "adversarial" / "core_manifest.draft.json",
            gitattributes=root / ".gitattributes",
        )


def _check(status_errors: list[str]) -> dict[str, Any]:
    return {"status": "PASS" if not status_errors else "FAIL", "errors": status_errors}


_VERSION_ROW = re.compile(rb"^\|\s*Version\s*\|\s*([0-9]+\.[0-9]+)\s*\|\s*$", re.MULTILINE)


def declared_constitution_version(constitution_bytes: bytes) -> str | None:
    """The version the Constitution's own metadata table declares (``| Version | 1.1 |``)."""

    match = _VERSION_ROW.search(constitution_bytes)
    return match.group(1).decode("ascii") if match else None


def _schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _document_check(
    result: CanonicalJSONResult,
    *,
    schema_name: str,
    semantic: Callable[[Mapping[str, Any]], list[str]],
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    errors = list(result.errors)
    obj = result.obj if isinstance(result.obj, dict) else None
    if obj is None:
        if result.obj is not None:
            errors.append("document root must be an object")
    else:
        try:
            errors.extend(validate_schema(obj, _schema(schema_name)))
        except (OSError, json.JSONDecodeError, SchemaError) as exc:
            errors.append(f"schema engine failure: {exc}")
        # Invalid schema shapes must not crash semantic traversal or bypass it.
        if not errors:
            try:
                errors.extend(semantic(obj))
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
                errors.append(f"semantic validation failed: {type(exc).__name__}: {exc}")
    report = _check(errors)
    report["sha256"] = result.sha256
    report["canonicalBytes"] = result.passed
    return report, obj


def run_prelock(paths: PrelockPaths) -> dict[str, Any]:
    """Run every pre-lock check without changing repository state."""

    checks: dict[str, dict[str, Any]] = {}

    try:
        constitution_bytes = paths.constitution.read_bytes()
        constitution_sha = hashlib.sha256(constitution_bytes).hexdigest()
        constitution_errors: list[str] = []
        if constitution_bytes.startswith(b"\xef\xbb\xbf"):
            constitution_errors.append("Constitution unexpectedly has a BOM")
        if b"\r" in constitution_bytes:
            constitution_errors.append("Constitution unexpectedly has CR bytes")
        declared_version = declared_constitution_version(constitution_bytes)
        if declared_version is None:
            constitution_errors.append("Constitution declares no version in its metadata table")
        elif declared_version not in SUPPORTED_CONSTITUTION_VERSIONS:
            constitution_errors.append(f"Constitution version {declared_version} is not supported by this validator")
    except OSError as exc:
        constitution_sha = ""
        declared_version = None
        constitution_errors = [f"cannot read Constitution: {exc}"]

    spec_result = validate_canonical_json(paths.spec)
    protocol_result = validate_canonical_json(paths.protocol)
    manifest_result = validate_canonical_json(paths.manifest)
    lock_result = validate_canonical_json(paths.lock_draft)

    spec_check, spec = _document_check(
        spec_result,
        schema_name="spec.schema.json",
        semantic=validate_spec,
    )
    protocol_check, protocol = _document_check(
        protocol_result,
        schema_name="protocol.schema.json",
        semantic=lambda obj: validate_protocol(obj, repo_root=paths.repo_root),
    )
    manifest_check, manifest = _document_check(
        manifest_result,
        schema_name="adversarial-manifest.schema.json",
        semantic=validate_manifest,
    )
    lock_check, lock = _document_check(
        lock_result,
        schema_name="lock.schema.json",
        semantic=validate_lock_draft,
    )

    if spec is not None and spec_check["status"] == "PASS":
        source_errors = _check_source_hash(
            spec["referenceSolution"]["value"]["primary"]["provenance"],
            paths.repo_root, "analytic primary reference")
        spec_check["errors"].extend(source_errors)
        if source_errors:
            spec_check["status"] = "FAIL"

    if lock is not None:
        if lock.get("constitutionSha256") != constitution_sha:
            constitution_errors.append("lock draft Constitution SHA does not match current bytes")
        if declared_version is not None and lock.get("constitutionVersion") != declared_version:
            constitution_errors.append(
                f"lock draft binds Constitution version {lock.get('constitutionVersion')!r} but the Constitution "
                f"declares {declared_version}"
            )
    for label, document in (("spec", spec), ("protocol", protocol)):
        if document is not None and declared_version is not None \
                and document.get("constitutionVersion") != declared_version:
            constitution_errors.append(
                f"{label} binds Constitution version {document.get('constitutionVersion')!r} but the Constitution "
                f"declares {declared_version}"
            )
    checks["constitutionBinding"] = _check(constitution_errors)
    checks["constitutionBinding"]["sha256"] = constitution_sha
    checks["spec"] = spec_check
    checks["protocol"] = protocol_check
    checks["adversarialManifest"] = manifest_check
    checks["lockDraft"] = lock_check

    repository_errors: list[str] = []
    try:
        attributes = paths.gitattributes.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        repository_errors.append(f"cannot read .gitattributes: {exc}")
        attributes = []
    for required in REQUIRED_GITATTRIBUTES:
        if required not in attributes:
            repository_errors.append(f"missing .gitattributes rule: {required}")
    checks["repository"] = _check(repository_errors)

    try:
        register = load_amendment_register(paths.repo_root / "governance" / "AMENDMENTS")
        register_errors = validate_amendment_register(
            register, constitution_version=declared_version or "", effective_versions=SUPPORTED_CONSTITUTION_VERSIONS)
        # The runtime matrix must know every version an amendment names (from 1.1 on),
        # and the declared version must have a matrix: PRELOCK's version and the
        # runtime matrix agree (final closure review, Issue 1).
        for version in sorted({entry["newVersion"] for entry in register} | ({declared_version} if declared_version else set())):
            if version != "1.0" and version not in ADMISSIBLE_ROOT_CAUSES_BY_VERSION:
                register_errors.append(f"Constitution {version} has no runtime admissible matrix (state_machine.ADMISSIBLE_ROOT_CAUSES_BY_VERSION)")
    except (OSError, ValueError) as exc:
        register_errors = [f"cannot read the amendment register: {exc}"]
    checks["amendmentRegister"] = _check(register_errors)

    # Ruling item 3 (external review, 2026-09-20): a repo-local module that a formal or
    # diagnostic run imports must be git-tracked, or the codeHash it records does not
    # identify the method. PRELOCK refuses to let such a tree start an attempt.
    try:
        from pinn.experiments.common import untracked_identity_paths     # local: avoids an import cycle

        hidden = untracked_identity_paths(paths.repo_root)
        identity_errors = ([f"untracked files inside the code-identity boundary: {hidden}"] if hidden else [])
    except Exception as exc:                                             # noqa: BLE001
        identity_errors = [f"cannot enumerate untracked code-identity files: {exc}"]
    checks["codeIdentityTracked"] = _check(identity_errors)

    passed = all(check["status"] == "PASS" for check in checks.values())
    candidate: dict[str, Any] = {
        "candidateSpecSha256": spec_result.sha256,
        "candidateProtocolSha256": protocol_result.sha256,
        "candidateManifestSha256": manifest_result.sha256,
        "candidateLockPayloadSha256": None,
        "label": "DRY-RUN ONLY - NOT A LOCK",
    }
    if lock is not None and spec_result.sha256 and protocol_result.sha256 and manifest_result.sha256:
        fields = dict(lock)
        fields.update(
            {
                "specSha256": spec_result.sha256,
                "protocolSha256": protocol_result.sha256,
                "adversarialManifestSha256": manifest_result.sha256,
            }
        )
        try:
            candidate["candidateLockPayloadSha256"] = candidate_payload_sha256(fields)
        except ValueError as exc:
            checks["lockDraft"]["status"] = "FAIL"
            checks["lockDraft"]["errors"].append(str(exc))
            passed = False

    return {
        "prelockStatus": "PASS" if passed else "FAIL",
        "hashLockExecuted": False,
        "trainingExecuted": False,
        "p2Entered": False,
        "checks": checks,
        "candidateDigests": candidate,
    }


def _discover_repo_root() -> Path:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return Path(__file__).resolve().parents[2]


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PINN v1.3 pre-lock dry run")
    parser.add_argument("--repo-root", type=Path, default=_discover_repo_root())
    parser.add_argument("--compact", action="store_true", help="emit one-line JSON")
    args = parser.parse_args(argv)
    report = run_prelock(PrelockPaths.defaults(args.repo_root))
    json.dump(report, sys.stdout, ensure_ascii=False, indent=None if args.compact else 2)
    sys.stdout.write("\n")
    return 0 if report["prelockStatus"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
