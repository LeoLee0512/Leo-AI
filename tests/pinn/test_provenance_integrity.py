import copy

import pytest

from pinn.governance.provenance import derive_eligibility

RAW = dict(artifactId="raw1", artifactRole="RAW_MODEL_PREDICTION", producerType="TRUSTED_RUNNER",
           producerRunId="run1", checkpointHash="a" * 64, hash="b" * 64,
           evaluatorSourcePath="runner.py", evaluatorCodeSha256="c" * 64,
           captureMethod="DIRECT_FORWARD_EVAL", registeredBy="runner", parentArtifactIds=[], transformation="IDENTITY")


def derive(artifact, *, registry=None, parents=()):
    return derive_eligibility(artifact, trusted_registrars={"runner"},
                             registered_code_hashes={"runner.py": "c" * 64}, parents=parents,
                             registered_artifacts=registry)


def test_self_declaration_does_not_create_trust():
    assert not derive(RAW).claim_evidence_eligible
    assert derive(RAW, registry={"raw1": RAW}).validation_input_eligible


@pytest.mark.parametrize("field,value", [
    ("parentArtifactIds", ["missing"]), ("checkpointHash", "x"), ("hash", "x"),
    ("evaluatorCodeSha256", "x"), ("producerRunId", ""),
    ("transformation", "NAN_FILL"), ("transformation", "BOUNDARY_OVERWRITE"),
    ("producerType", "MANUAL_IMPORT"), ("artifactRole", "DISPLAY_ONLY"),
])
def test_invalid_or_destructive_artifact_rejected(field, value):
    artifact = copy.deepcopy(RAW)
    artifact[field] = value
    result = derive(artifact, registry={"raw1": artifact})
    assert not result.claim_evidence_eligible
    assert not result.validation_input_eligible


def test_relabeling_registered_artifact_rejected():
    imported = dict(RAW, artifactRole="UNTRUSTED_IMPORT", producerType="MANUAL_IMPORT")
    assert not derive(RAW, registry={"raw1": imported}).trusted


def test_parent_identity_must_match_not_just_count():
    parent = derive(RAW, registry={"raw1": RAW})
    child = dict(RAW, artifactId="child", parentArtifactIds=["some-other-parent"])
    assert not derive(child, registry={"child": child}, parents=(parent,)).lineage_clean


def test_destroyed_parent_cannot_be_laundered():
    damaged = dict(RAW, transformation="ISOTONIC_PROJECTION")
    parent = derive(damaged, registry={"raw1": damaged})
    child = dict(RAW, artifactId="child", parentArtifactIds=["raw1"])
    assert not derive(child, registry={"child": child}, parents=(parent,)).claim_evidence_eligible


def test_handwritten_flags_ignored_and_recorded():
    forged = dict(RAW, validationInputEligible=True, claimEvidenceEligible=True)
    result = derive(forged)
    assert not result.claim_evidence_eligible
    assert any("tampering" in error for error in result.errors)


def test_changed_checkpoint_hash_does_not_match_recorded_evidence():
    corrupted = dict(RAW, checkpointHash="d" * 64)
    assert not derive(corrupted, registry={"raw1": RAW}).claim_evidence_eligible


def test_seed_metadata_mismatch_is_rejected():
    recorded = dict(RAW, seed=20260904)
    altered = dict(recorded, seed=20260905)
    assert not derive(altered, registry={"raw1": recorded}).claim_evidence_eligible
