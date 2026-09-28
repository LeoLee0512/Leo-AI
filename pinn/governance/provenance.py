"""Artifact provenance trust-boundary rules for the v1.3 draft."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from .canonical import canonical_bytes


TRUSTED_PRODUCERS = frozenset(
    {
        "TRUSTED_RUNNER",
        "TRUSTED_VALIDATOR",
        "TRUSTED_BASELINE_SOLVER",
        "TRUSTED_ANALYTIC_REFERENCE",
    }
)
PRESERVING_TRANSFORMATIONS = frozenset(
    {"IDENTITY", "LOSSLESS_SERIALISE", "DTYPE_WIDEN"}
)
VALIDATION_INPUT_ROLES = frozenset({"RAW_MODEL_PREDICTION", "REFERENCE"})
CLAIM_EVIDENCE_ROLES = frozenset(
    {"RAW_MODEL_PREDICTION", "REFERENCE", "VALIDATION_METRIC"}
)


@dataclass(frozen=True)
class Eligibility:
    trusted: bool
    lineage_clean: bool
    validation_input_eligible: bool
    claim_evidence_eligible: bool
    errors: tuple[str, ...]
    artifact_id: str | None = None


def derive_eligibility(
    artifact: Mapping[str, Any],
    *,
    trusted_registrars: set[str] | frozenset[str],
    registered_code_hashes: Mapping[str, str],
    parents: tuple[Eligibility, ...] = (),
    registered_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
) -> Eligibility:
    """Derive eligibility from registrar records, never self-declared metadata.

    ``registered_artifacts`` is supplied by the trusted recorder after verifying
    artifact bytes. It must not be built from an imported artifact's sidecar.
    This policy function is not a signature verifier or an evidence recorder.
    """

    errors: list[str] = []
    producer = artifact.get("producerType")
    role = artifact.get("artifactRole")
    capture = artifact.get("captureMethod")
    registrar = artifact.get("registeredBy")
    source_path = artifact.get("evaluatorSourcePath")
    source_hash = artifact.get("evaluatorCodeSha256")

    if not all(isinstance(value, str) for value in (producer, role, capture, registrar, source_path, source_hash)):
        return Eligibility(False, False, False, False, ("malformed artifact provenance fields",))
    trusted = producer in TRUSTED_PRODUCERS
    artifact_id = artifact.get("artifactId")
    if not isinstance(artifact_id, str) or not artifact_id:
        trusted = False
        errors.append("artifactId is missing")
    authoritative = (registered_artifacts or {}).get(artifact_id) if isinstance(artifact_id, str) else None
    derived_fields = {"validationInputEligible", "claimEvidenceEligible"}
    supplied = {k: v for k, v in artifact.items() if k not in derived_fields}
    try:
        matches = authoritative is not None and canonical_bytes(supplied) == canonical_bytes(
            {k: v for k, v in authoritative.items() if k not in derived_fields})
    except (ValueError, TypeError, OverflowError):
        matches = False
    if not matches:
        trusted = False
        errors.append("artifact metadata is not bound to a trusted recorder entry")
    if any(key in artifact for key in derived_fields):
        errors.append("self-declared eligibility ignored; possible tampering attempt")
    def digest(value: Any) -> bool:
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    if not digest(artifact.get("hash")) or not digest(source_hash):
        trusted = False
        errors.append("artifact/evaluator hash is not a SHA-256 digest")
    if registrar not in trusted_registrars:
        trusted = False
        errors.append("registrar is not trusted")
    if not source_path or registered_code_hashes.get(str(source_path)) != source_hash:
        trusted = False
        errors.append("evaluator source hash is absent or not registered")

    declared_parents = artifact.get("parentArtifactIds")
    parent_ids = [parent.artifact_id for parent in parents]
    complete_lineage = (
        isinstance(declared_parents, list)
        and all(isinstance(value, str) and value for value in declared_parents)
        and len(set(declared_parents)) == len(declared_parents)
        and declared_parents == parent_ids
        and artifact_id not in declared_parents
    )
    lineage_clean = (
        complete_lineage
        and
        artifact.get("transformation") in PRESERVING_TRANSFORMATIONS
        and all(parent.trusted and parent.lineage_clean for parent in parents)
    )
    if not lineage_clean:
        errors.append("artifact lineage is not evidence preserving")

    if role == "RAW_MODEL_PREDICTION":
        if producer != "TRUSTED_RUNNER" or capture != "DIRECT_FORWARD_EVAL":
            trusted = False
            errors.append("raw prediction must be a direct trusted-runner evaluation")
        if not digest(artifact.get("checkpointHash")):
            trusted = False
            errors.append("raw prediction is missing a valid checkpointHash")
        if not isinstance(artifact.get("producerRunId"), str) or not artifact.get("producerRunId"):
            trusted = False
            errors.append("raw prediction is missing producerRunId")
    elif role == "REFERENCE":
        numerical = producer == "TRUSTED_BASELINE_SOLVER" and capture == "SOLVER_OUTPUT"
        analytic = (
            producer == "TRUSTED_ANALYTIC_REFERENCE"
            and capture == "ANALYTIC_EVALUATION"
            and bool(artifact.get("equationBinding"))
            and bool(artifact.get("specBinding"))
        )
        if not (numerical or analytic):
            trusted = False
            errors.append("reference lacks a valid numerical or analytic provenance type")
    elif role == "VALIDATION_METRIC":
        if producer != "TRUSTED_VALIDATOR" or capture != "METRIC_COMPUTATION":
            trusted = False
            errors.append("validation metric must be computed by the trusted validator")
        if not parents or not all(parent.validation_input_eligible for parent in parents):
            trusted = False
            errors.append("validation metric parents are not validation-input eligible")

    validation_input = trusted and lineage_clean and role in VALIDATION_INPUT_ROLES
    claim_evidence = trusted and lineage_clean and role in CLAIM_EVIDENCE_ROLES
    return Eligibility(trusted, lineage_clean, validation_input, claim_evidence, tuple(errors), artifact_id)
