"""Lock regressions use temporary repositories, never the candidate lock path."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from pinn.governance import locking
from pinn.governance.canonical import canonical_bytes


REPOSITORY = Path(__file__).resolve().parents[2]


@pytest.fixture
def lock_case(tmp_path):
    (tmp_path / ".git").mkdir()
    source_paths = {
        "spec": "governance/POISSON_1D_V1.0_spec.draft.json",
        "protocol": "governance/POISSON_1D_V1.0_protocol.draft.json",
        "adversarial_manifest": "adversarial/core_manifest.draft.json",
        "constitution": "governance/PINN_RESEARCH_CONSTITUTION.md",
    }
    destinations = {
        "spec": "specs/poisson-1d/v1.0/spec.json",
        "protocol": "specs/poisson-1d/v1.0/protocol.json",
        "adversarial_manifest": "adversarial/core_manifest.json",
        "constitution": "governance/PINN_RESEARCH_CONSTITUTION.md",
    }
    for key, source in source_paths.items():
        target = tmp_path / destinations[key]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPOSITORY / source).read_bytes())
    draft = json.loads((REPOSITORY / "governance/POISSON_1D_V1.0_lock.draft.json").read_text(encoding="utf-8"))
    arguments = {
        "draft": draft,
        "spec_sha256": hashlib.sha256((tmp_path / destinations["spec"]).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256((tmp_path / destinations["protocol"]).read_bytes()).hexdigest(),
        "adversarial_manifest_sha256": hashlib.sha256((tmp_path / destinations["adversarial_manifest"]).read_bytes()).hexdigest(),
        "locked_at": "2026-09-08T12:00:00Z",
    }
    return tmp_path, tmp_path / "specs/poisson-1d/v1.0/lock.json", arguments


def put_lock(case, document=None):
    root, path, arguments = case
    document = locking.build_locked_document(**arguments) if document is None else document
    path.write_bytes(canonical_bytes(document))
    return root, path, document


def test_registered_seven_field_payload_remains_exact(lock_case):
    _, _, arguments = lock_case
    doc = locking.build_locked_document(**arguments)
    expected = ("\n".join(doc[key] for key in locking.LOCK_FIELD_ORDER) + "\n").encode("utf-8")
    assert locking.build_lock_payload(doc) == expected
    assert hashlib.sha256(expected).hexdigest() == doc["lockSha256"]


def test_valid_temporary_lock_verifies_and_detects_spec_tamper(lock_case):
    root, path, _ = put_lock(lock_case)
    assert locking.verify_lock(path, repo_root=root)
    source = path.with_name("spec.json")
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc["domain"]["value"]["boundary"] = [0.0, 2.0]
    source.write_bytes(canonical_bytes(doc))
    assert any("specSha256 mismatch" in item for item in locking.verify_lock_details(path, repo_root=root))


@pytest.mark.parametrize(("field", "value"), [
    ("lockState", "DRAFT"), ("digestAlgorithm", "MD5"),
    ("constitutionVersion", "9.0"), ("lockVersion", "2"),
    ("specVersion", "2.0"), ("specPath", "../../wrong.json"),
    ("specPath", "C:/outside/spec.json"), ("protocolPath", "elsewhere/protocol.json"),
    ("adversarialManifestPath", "adversarial/core_manifest.draft.json"),
    ("constitutionPath", "another-constitution.md"), ("preconditions", []),
    ("lockedAt", "DRY-RUN-ONLY--LOCKED-AT-NOT-SET"),
    ("lockedAt", "2026-02-30T12:00:00Z"), ("lockedAt", "2026-09-08T12:00:00-07:00"),
    ("lockedAt", "2026-09-08T12:00:00Z\n"), ("specSha256", None),
    ("constitutionSha256", "x"), ("lockSha256", "0" * 64),
])
def test_lock_tamper_rejected_even_when_not_covered_by_payload(lock_case, field, value):
    _, _, args = lock_case
    doc = locking.build_locked_document(**args)
    doc[field] = value
    root, path, _ = put_lock(lock_case, doc)
    assert not locking.verify_lock(path, repo_root=root)


def test_reordered_payload_declaration_rejected(lock_case):
    _, _, args = lock_case
    doc = locking.build_locked_document(**args)
    doc["lockSha256Definition"]["fieldOrder"].reverse()
    root, path, _ = put_lock(lock_case, doc)
    assert not locking.verify_lock(path, repo_root=root)


def test_changed_payload_formula_rejected(lock_case):
    _, _, args = lock_case
    doc = locking.build_locked_document(**args)
    doc["lockSha256Definition"]["formula"] = "Always return PASS"
    root, path, _ = put_lock(lock_case, doc)
    assert not locking.verify_lock(path, repo_root=root)


def test_existing_lock_cannot_be_relabelled_as_fresh_draft(lock_case):
    _, _, args = lock_case
    doc = locking.build_locked_document(**args)
    with pytest.raises(ValueError, match="unfilled DRAFT"):
        locking.build_locked_document(**{**args, "draft": doc})


@pytest.mark.parametrize("which", ["spec.json", "protocol.json"])
def test_missing_bound_input_is_failure(lock_case, which):
    root, path, _ = put_lock(lock_case)
    # Temporary fixtures only; the real candidate/evidence is never removed.
    path.with_name(which).unlink()
    assert not locking.verify_lock(path, repo_root=root)


def test_wrong_lock_location_is_failure(lock_case):
    root, path, doc = put_lock(lock_case)
    other = path.with_name("another-lock.json")
    other.write_bytes(canonical_bytes(doc))
    assert not locking.verify_lock(other, repo_root=root)


def test_noncanonical_spec_fails_even_with_updated_digests(lock_case):
    root, path, args = lock_case
    spec = path.with_name("spec.json")
    spec.write_bytes(spec.read_bytes().replace(b"\n", b"\r\n"))
    args["spec_sha256"] = hashlib.sha256(spec.read_bytes()).hexdigest()
    _, path, _ = put_lock(lock_case)
    assert not locking.verify_lock(path, repo_root=root)


@pytest.mark.parametrize("value", [False, None, "PASS", "FAIL", 1, {}])
def test_writer_requires_literal_prelock_pass(lock_case, value):
    _, path, args = lock_case
    with pytest.raises(ValueError, match="PRELOCK_VALIDATION"):
        locking.write_lock(path, **args, prelock_validator=lambda: value)
    assert not path.exists()


def test_writer_rechecks_current_input_bytes(lock_case):
    _, path, args = lock_case
    path.with_name("spec.json").write_bytes(canonical_bytes({"wrong": "spec"}))
    with pytest.raises(ValueError, match="specSha256 mismatch"):
        locking.write_lock(path, **args, prelock_validator=lambda: True)
    assert not path.exists()


def test_writer_success_and_existing_failure_preserved(lock_case):
    root, path, args = lock_case
    locking.write_lock(path, **args, prelock_validator=lambda: True)
    assert locking.verify_lock(path, repo_root=root)
    initial = path.read_bytes()
    with pytest.raises(FileExistsError):
        locking.write_lock(path, **args, prelock_validator=lambda: True)
    assert path.read_bytes() == initial


def test_writer_closes_concurrent_create_overwrite_race(lock_case, monkeypatch):
    _, path, args = lock_case
    original_mkdir = Path.mkdir

    def competing_mkdir(self, *positional, **keyword):
        result = original_mkdir(self, *positional, **keyword)
        if self == path.parent:
            path.write_bytes(b"competing writer evidence\n")
        return result

    monkeypatch.setattr(Path, "mkdir", competing_mkdir)
    with pytest.raises(FileExistsError):
        locking.write_lock(path, **args, prelock_validator=lambda: True)
    assert path.read_bytes() == b"competing writer evidence\n"


def test_failed_readback_is_visible_and_not_reported_success(lock_case, monkeypatch):
    root, path, args = lock_case
    original_fsync = locking.os.fsync

    def corrupt_bound_input(descriptor):
        original_fsync(descriptor)
        path.with_name("spec.json").write_bytes(canonical_bytes({"changed": "during write"}))

    monkeypatch.setattr(locking.os, "fsync", corrupt_bound_input)
    with pytest.raises(ValueError, match="retained for evidence"):
        locking.write_lock(path, **args, prelock_validator=lambda: True)
    assert path.is_file()
    assert not locking.verify_lock(path, repo_root=root)


def test_malformed_lock_and_missing_repository_fail_closed(tmp_path):
    path = tmp_path / "lock.json"
    path.write_bytes(b"not JSON\n")
    assert not locking.verify_lock(path)
    path.write_bytes(canonical_bytes({}))
    assert not locking.verify_lock(path)


def test_dry_run_sentinel_never_becomes_formal_timestamp(lock_case):
    _, _, args = lock_case
    draft = copy.deepcopy(args["draft"])
    draft.update(specSha256=args["spec_sha256"], protocolSha256=args["protocol_sha256"],
                 adversarialManifestSha256=args["adversarial_manifest_sha256"])
    assert len(locking.candidate_payload_sha256(draft)) == 64
    with pytest.raises(ValueError, match="timestamp"):
        locking.build_locked_document(**{**args, "locked_at": locking.DRY_RUN_LOCKED_AT_SENTINEL})


def test_resolver_rejects_traversal_and_escape(tmp_path):
    path = tmp_path / "specs/poisson-1d/v1.0/lock.json"
    for value in ("../../outside.json", str(tmp_path.parent / "outside.json")):
        with pytest.raises(ValueError):
            locking._resolve(path, value, repo_root=tmp_path)
