"""Tier-1 P11 applicability and the portability closure (Final Closure Audit issues 2 and 3)."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "experiments/poisson2d/runs/exp2d-poisson-calibration-r1"
PROTOCOL = ROOT / "governance/PINN_TRUST_PROTOCOLS_R1.md"
POLICY = ROOT / "manifests/portability-historical-evidence.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def scanner():
    spec = importlib.util.spec_from_file_location("leo_portability_check", ROOT / "tools/portability_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------- P11 applicability

def test_every_tier1_perturbation_the_protocol_mandates_was_executed():
    """The protocol's Tier-1 set must be covered; NOT_APPLICABLE needs a registered reason, not silence."""

    text = PROTOCOL.read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if "Tier-1" in l and "C2" in l and "P11" in l)
    mandated = {token for token in ("P1", "P4", "P6", "P7", "P8", "P9", "P11", "P16") if token in line}
    assert mandated == {"P1", "P4", "P6", "P7", "P8", "P9", "P11", "P16"}, line
    executed = {r["id"] for r in load(ATTEMPT / "tier1_redteam.json")["results"]
                if r.get("applicability") == "APPLICABLE"}
    not_applicable = {r["id"]: r for r in load(ATTEMPT / "tier1_redteam.json")["results"]
                      if r.get("applicability") == "NOT_APPLICABLE"}
    supplement = ATTEMPT / "tier1_p11_supplement.json"
    assert supplement.exists(), "P11 is mandatory before C2 and must have been executed"
    executed |= {load(supplement)["perturbation"]}
    assert mandated <= executed, f"missing Tier-1 perturbations: {sorted(mandated - executed)}"
    for entry in not_applicable.values():
        assert entry.get("reason"), "a NOT_APPLICABLE perturbation must carry its registered reason"


def test_the_supplemental_p11_stayed_on_dev_and_never_touched_the_claim_set():
    record = load(ATTEMPT / "tier1_p11_supplement.json")
    assert record["evaluationSet"] == "dev"
    assert record["claimSetTouched"] is False
    assert record["perturbation"] == "P11" and record["supplemental"] is True
    assert record["codeHash"] == load(ATTEMPT / "identity.json")["codeHash"], (
        "the supplemental perturbation must run under the formal run's code identity")
    assert record["preregistration"].endswith("P11_SUPPLEMENT_PREREGISTRATION_20260916.md")
    assert record["region"]["densificationFactor"] == 2.0
    assert record["status"] in ("PASS", "PARTIAL", "FAIL")
    assert record["thresholds"]["maintain"] == 0.01 and record["thresholds"]["fail"] == 0.05


def test_the_trust_vector_after_p11_supersedes_the_gate6_one():
    vector = load(ATTEMPT / "trust_vector_g6_p11.json")
    assert vector["supersedesRecordId"] == load(ATTEMPT / "trust_vector_g6.json")["recordId"]
    train = vector["dimensions"]["train"]
    assert "P11" in train.get("perturbationsRun", []), "the train dimension must record that P11 ran"
    decision = load(ATTEMPT / "claim_gate_decision_g6_p11.json")
    assert decision["trustVectorRef"]["artifactId"] == vector["recordId"]


# ---------------------------------------------------------------- portability closure

def test_source_files_carry_no_absolute_user_path():
    module = scanner()
    for relative in ("experiments/poisson2d/qualify_environment_b.py",
                     "experiments/poisson2d/verify_tests_under_torch.py"):
        findings = [f for f in module.scan() if f["file"] == relative]
        assert not findings, f"{relative} must not bind a user path: {findings}"


def test_future_environment_evidence_is_path_neutral():
    record = load(ROOT / "experiments/poisson2d/TEST_VERIFICATION_UNDER_TORCH.json")
    assert "executable" not in record, "the absolute interpreter path must not be recorded any more"
    assert record["interpreterInstallationId"].startswith("prefix-")
    assert "pathRecordingRule" in record
    module = scanner()
    assert not [f for f in module.scan() if f["file"].endswith("TEST_VERIFICATION_UNDER_TORCH.json")]


def write_policy(tmp_path, monkeypatch, **overrides):
    module = scanner()
    monkeypatch.setattr(module, "REPO", tmp_path)
    policy = tmp_path / "manifests" / "portability-historical-evidence.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    entry = {"file": "experiments/poisson2d/environment_b_qualification.json", "sha256": "0" * 64,
             "classification": "immutable-historical-evidence", "finding_type": "windows-user-home",
             "expected_occurrences": 1, "ruling": "test", "constraint": "test"}
    entry.update(overrides)
    policy.write_text(json.dumps({"schema_version": 1, "entries": [entry]}), encoding="utf-8")
    return module


def test_the_exemption_mechanism_reaches_immutable_evidence_but_nothing_executable(tmp_path, monkeypatch):
    """The approved scope extension (external review ruling 2026-09-16), asserted both ways.

    Issue 3A's blocker was that the loader only accepted ``governance/**.md``, so the
    evidence under ``experiments/`` could not be classified at all. The extension lets an
    approved *record* be named; what it must never let through is a file that is executed.
    """

    module = write_policy(tmp_path, monkeypatch)
    assert [e["file"] for e in module.historical_evidence_policy()] == [
        "experiments/poisson2d/environment_b_qualification.json"]

    for rejected, message in (
            ("experiments/poisson2d/qualify_environment_b.py", "non-evidence file"),
            ("pinn/experiments2d/runner2d.py", "non-evidence file"),
            ("tools/portability_check.py", "non-evidence file"),
            ("manifests/dependency-lock.json", "non-evidence file"),
            ("experiments/poisson2d/*.json", "wildcard or pattern"),
            ("experiments/poisson2d/", "directory"),
    ):
        module = write_policy(tmp_path, monkeypatch, file=rejected)
        with pytest.raises(RuntimeError, match=message):
            module.historical_evidence_policy()

    module = write_policy(tmp_path, monkeypatch)
    module.historical_evidence_policy()
    document = json.loads((tmp_path / "manifests/portability-historical-evidence.json").read_text(encoding="utf-8"))
    document["entries"][0].pop("constraint")
    (tmp_path / "manifests/portability-historical-evidence.json").write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(RuntimeError, match="has no constraint"):
        module.historical_evidence_policy()


def test_one_byte_mutation_invalidates_an_exemption(tmp_path, monkeypatch):
    module = scanner()
    monkeypatch.setattr(module, "REPO", tmp_path)
    document = tmp_path / "governance" / "EVIDENCE.md"
    document.parent.mkdir(parents=True)
    document.write_text("a path C:\\Users\\someone\\thing\n", encoding="utf-8")
    digest = module._sha256(document)
    policy = tmp_path / "manifests" / "portability-historical-evidence.json"
    policy.parent.mkdir(parents=True)
    entry = {"file": "governance/EVIDENCE.md", "sha256": digest, "classification": "immutable-historical-evidence",
             "finding_type": "windows-user-home", "expected_occurrences": 1, "ruling": "test", "constraint": "test"}
    policy.write_text(json.dumps({"schema_version": 1, "entries": [entry]}), encoding="utf-8")
    finding = {"file": "governance/EVIDENCE.md", "rule": "windows-user-home", "line": 1, "text": "x",
               "configurable_default": False}
    classified = module.classify_historical_evidence([dict(finding)])
    assert classified[0].get("audit_marker") == module.HISTORICAL_MARKER
    document.write_text("a path C:\\Users\\someone\\thing!\n", encoding="utf-8")   # one byte more
    classified = module.classify_historical_evidence([dict(finding)])
    assert classified[0].get("audit_marker") is None, "a changed byte must invalidate the exemption"


def test_the_committed_policy_holds_exactly_the_approved_entries():
    """Every classification in the repository is one a human approved, named file by file."""

    policy = load(POLICY)
    assert policy["schema_version"] == 1
    assert [(entry["file"], entry["finding_type"]) for entry in policy["entries"]] == [
        ("governance/PINN_CONSTITUTION_COMPLIANCE_AUDIT.md", "windows-user-home"),
        ("experiments/poisson1d/environment_b_qualification.json", "windows-user-home"),
        ("experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json", "windows-user-home"),
        ("experiments/poisson1d/runs/repro-envb-frozen-r2/PROVENANCE_MANIFEST.json", "desktop-path"),
        ("experiments/poisson1d/runs/repro-envb-r2/POST_AUDIT_ANNOTATION.md", "windows-user-home"),
        ("experiments/poisson2d/environment_b_qualification.json", "windows-user-home"),
    ]
    module = scanner()
    for entry in policy["entries"]:
        assert entry["classification"] == "immutable-historical-evidence"
        assert entry["ruling"].strip() and entry["constraint"].strip()
        assert entry["expected_occurrences"] >= 1
        assert not entry["file"].endswith(module.EVIDENCE_POLICY_FORBIDDEN_SUFFIXES), (
            "no script or executable may ever carry the classification")
        assert module._sha256(ROOT / entry["file"]) == entry["sha256"], (
            "the approved bytes must still be the bytes on disk")


def test_the_approved_findings_stay_visible_and_nothing_else_remains():
    """Closure: zero unexpected findings, and every approved one is still reported."""

    module = scanner()
    hard, _configurable, historical = module.partition_findings(module.scan())
    assert not hard, hard
    approved = {(entry["file"], entry["finding_type"]) for entry in load(POLICY)["entries"]}
    assert {(f["file"], f["rule"]) for f in historical} == approved
    assert all(f["audit_marker"] == module.HISTORICAL_MARKER for f in historical)
