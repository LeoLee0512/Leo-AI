"""Code-identity completeness audit (2026-09-16), asserted as executable invariants.

A codeHash is only worth recording if it covers every module whose bytes can change a
decision: how a ScientificSpec is read, what a Gate returns, which FailureSignature is
generated, what a DiagnosisRecord says, a TrustVector status, a ClaimGateDecision, a
Red-Team verdict, a reproducibility verdict.

The audit found the boundary sound for executed code (everything under ``pinn/``,
``scientific_reference/`` and ``specs/``) -- ``pinn/experiments2d/localized_error.py``
included -- and two non-code inputs outside it that carry the same power: the protocol
compilation (it decides which Tier-1 perturbations are mandatory) and the adversarial
core manifest (an input of PRELOCK, which gates whether a formal attempt starts). Both
are now named files of the identity, prospectively, for the next revision.

These tests are the regression evidence: what must be inside, what must stay outside,
and that an incomplete manifest stops the run before PRELOCK.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from pinn.experiments.common import (
    CODE_IDENTITY_FILES,
    CODE_IDENTITY_PREFIXES,
    CodeIdentityError,
    assert_code_identity_complete,
    code_manifest,
    required_identity_paths,
)
from pinn.governance.trust_loop import code_hash_from_manifest

ROOT = Path(__file__).resolve().parents[2]
CONFIG = "experiments/poisson2d/configs/exp2d_baseline.json"
ATTEMPT = ROOT / "experiments/poisson2d/runs/exp2d-poisson-calibration-r1"

#: One module per decision surface, named rather than globbed: if any of these ever falls
#: outside the identity, a decision could change without the codeHash changing.
DECISION_RELEVANT_MODULES = (
    # ScientificSpec interpretation
    "specs/poisson-2d/v1.0/POISSON_2D_V1.0_spec.json",
    "pinn/governance/poisson2d_contract.py",
    # Gate results
    "pinn/experiments2d/gates2d.py",
    "pinn/experiments2d/datasets2d.py",
    "pinn/experiments2d/pinn_torch2d.py",
    "pinn/validation/poisson2d.py",
    "pinn/reference/analytic_poisson2d.py",
    "scientific_reference/poisson2d_fdm.py",
    # FailureSignature generation and DiagnosisRecord content
    "pinn/experiments/diagnosis.py",
    "pinn/experiments2d/diagnostics2d.py",
    "pinn/experiments2d/localized_error.py",
    "pinn/governance/state_machine.py",
    # TrustVector status and ClaimGateDecision
    "pinn/governance/trust_vector.py",
    "pinn/governance/trust_loop.py",
    "pinn/governance/claim_set_ledger.py",
    # Red-Team verdict
    "pinn/experiments2d/redteam2d.py",
    "governance/PINN_TRUST_PROTOCOLS_R1.md",
    # reproducibility verdict
    "pinn/experiments2d/runner2d.py",
    "pinn/experiments2d/repro_package2d.py",
    # PRELOCK, which gates whether the attempt starts
    "pinn/governance/prelock.py",
    "adversarial/core_manifest.draft.json",
    "governance/PINN_RESEARCH_CONSTITUTION.md",
)

#: Files that must NOT move the codeHash: reports, evidence records and the driver scripts
#: that wrote them. Evidence changes every run by construction; folding it into the method
#: identity would make every run a different method.
IDENTITY_EXCLUDED = (
    "docs/TRUSTED_RESEARCH_V1.md",
    "experiments/poisson2d/runs/exp2d-poisson-calibration-r1/gate5b_external.json",
    "experiments/poisson2d/LOCALIZED_ERROR_CALIBRATION.json",
    "CHANGELOG.md",
)


@pytest.fixture(scope="module")
def manifest():
    return code_manifest(ROOT, [CONFIG])


def with_one_byte_changed(manifest, path):
    """The manifest as it would read after appending one byte to *path*."""

    changed = []
    for entry in manifest:
        if entry["path"] == path:
            entry = dict(entry, sha256=hashlib.sha256((ROOT / path).read_bytes() + b"#").hexdigest())
        changed.append(entry)
    return changed


# --------------------------------------------------------------- 1 & 2: sensitivity

def test_the_localized_error_module_is_inside_the_identity(manifest):
    """The module the next experiment's symptom rule runs on cannot sit outside the hash."""

    paths = {entry["path"] for entry in manifest}
    assert "pinn/experiments2d/localized_error.py" in paths
    assert "pinn/experiments2d/localized_error.py".startswith(CODE_IDENTITY_PREFIXES)


def test_one_byte_in_the_localized_error_module_changes_the_code_hash(manifest):
    before = code_hash_from_manifest(manifest)
    after = code_hash_from_manifest(with_one_byte_changed(manifest, "pinn/experiments2d/localized_error.py"))
    assert before != after


@pytest.mark.parametrize("path", DECISION_RELEVANT_MODULES)
def test_every_decision_relevant_module_is_covered_and_sensitive(path, manifest):
    paths = {entry["path"] for entry in manifest}
    assert path in paths, f"{path} can change a decision but is outside the code identity"
    assert (ROOT / path).is_file()
    assert code_hash_from_manifest(with_one_byte_changed(manifest, path)) != code_hash_from_manifest(manifest)


def test_the_run_config_is_part_of_the_identity(manifest):
    assert CONFIG in {entry["path"] for entry in manifest}
    assert code_hash_from_manifest(with_one_byte_changed(manifest, CONFIG)) != code_hash_from_manifest(manifest)


def test_the_two_audit_additions_are_registered():
    assert "governance/PINN_TRUST_PROTOCOLS_R1.md" in CODE_IDENTITY_FILES
    assert "adversarial/core_manifest.draft.json" in CODE_IDENTITY_FILES


# --------------------------------------------------- 3: evidence and docs stay outside

@pytest.mark.parametrize("path", IDENTITY_EXCLUDED)
def test_documentation_and_evidence_are_outside_the_identity(path, manifest):
    assert (ROOT / path).is_file()
    assert path not in {entry["path"] for entry in manifest}, (
        f"{path} is evidence or prose; folding it into the method identity would make every run a new method")


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _synthetic_repo(tmp_path):
    """A miniature repository with one file of each kind, tracked by git."""

    repo = tmp_path / "repo"
    files = {
        "pinn/experiments2d/module.py": "VALUE = 1\n",
        "scientific_reference/ref.py": "def f():\n    return 1\n",
        "specs/problem/v1.0/spec.json": '{"specId": "p"}\n',
        "governance/PINN_RESEARCH_CONSTITUTION.md": "# constitution\n",
        "governance/PINN_TRUST_PROTOCOLS_R1.md": "# protocols\n",
        "adversarial/core_manifest.draft.json": '{"entries": []}\n',
        "docs/report.md": "# a report about the run\n",
        "experiments/problem/runs/r1/gate5b_external.json": '{"checks": []}\n',
        "experiments/problem/driver.py": "print('drives a run')\n",
        "CHANGELOG.md": "# changes\n",
    }
    for name, text in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(repo.parent, "init", "--quiet", str(repo))
    _git(repo, "add", "-A")
    return repo


def test_a_documentation_or_evidence_edit_does_not_move_the_code_hash(tmp_path):
    """End to end, through git: only method bytes move the identity."""

    repo = _synthetic_repo(tmp_path)
    before = code_hash_from_manifest(code_manifest(repo))

    for untouchable in ("docs/report.md", "experiments/problem/runs/r1/gate5b_external.json", "CHANGELOG.md"):
        (repo / untouchable).write_text("changed evidence or prose\n", encoding="utf-8")
    _git(repo, "add", "-A")
    assert code_hash_from_manifest(code_manifest(repo)) == before, (
        "evidence and documentation must not be part of the method identity")

    (repo / "pinn/experiments2d/module.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    assert code_hash_from_manifest(code_manifest(repo)) != before, "one byte of method code must move the hash"


def test_a_declared_driver_outside_the_prefixes_enters_the_identity(tmp_path):
    """The escape hatch for a formal run driven from experiments/: declare it, and it is hashed."""

    repo = _synthetic_repo(tmp_path)
    driver = "experiments/problem/driver.py"
    plain = code_hash_from_manifest(code_manifest(repo))
    declared_manifest = code_manifest(repo, [driver])
    assert driver in {entry["path"] for entry in declared_manifest}
    declared = code_hash_from_manifest(declared_manifest)
    assert declared != plain

    (repo / driver).write_text("print('drives a run differently')\n", encoding="utf-8")
    _git(repo, "add", "-A")
    assert code_hash_from_manifest(code_manifest(repo, [driver])) != declared
    assert code_hash_from_manifest(code_manifest(repo)) == plain, (
        "an undeclared driver still stays outside -- which is exactly why the run must declare it")


# ------------------------------------------- 4: an incomplete manifest stops the run

@pytest.mark.parametrize("omitted", [
    "pinn/experiments2d/localized_error.py",
    "pinn/experiments2d/gates2d.py",
    "pinn/governance/poisson2d_contract.py",
    "governance/PINN_TRUST_PROTOCOLS_R1.md",
    "adversarial/core_manifest.draft.json",
])
def test_omitting_a_registered_module_is_rejected(omitted, manifest):
    incomplete = [entry for entry in manifest if entry["path"] != omitted]
    with pytest.raises(CodeIdentityError, match="code identity is incomplete"):
        assert_code_identity_complete(incomplete, ROOT, extra_required=[CONFIG])


def test_omitting_the_declared_config_is_rejected(manifest):
    incomplete = [entry for entry in manifest if entry["path"] != CONFIG]
    with pytest.raises(CodeIdentityError, match="code identity is incomplete"):
        assert_code_identity_complete(incomplete, ROOT, extra_required=[CONFIG])


def test_a_manifest_that_no_longer_matches_disk_is_rejected(manifest):
    stale = with_one_byte_changed(manifest, "pinn/experiments2d/localized_error.py")
    with pytest.raises(CodeIdentityError, match="no longer matches the files on disk"):
        assert_code_identity_complete(stale, ROOT, extra_required=[CONFIG])


def test_declaring_a_file_that_does_not_exist_is_rejected(manifest):
    with pytest.raises(CodeIdentityError):
        assert_code_identity_complete(manifest, ROOT, extra_required=[CONFIG, "experiments/poisson2d/no_such_driver.py"])


def test_the_complete_manifest_is_accepted(manifest):
    assert_code_identity_complete(manifest, ROOT, extra_required=[CONFIG])
    assert set(required_identity_paths(ROOT, [CONFIG])) <= {entry["path"] for entry in manifest}


def test_the_check_runs_before_prelock_and_before_any_gate():
    """Ordering is the point: an incomplete identity must stop the attempt, not annotate it."""

    source = (ROOT / "pinn/experiments2d/runner2d.py").read_text(encoding="utf-8")
    identity = source.split("def phase_identity", 1)[1].split("\n    def ", 1)[0]
    assert "assert_code_identity_complete(" in identity
    assert identity.index("assert_code_identity_complete(") < identity.index("run_prelock("), (
        "the completeness check must precede PRELOCK")
    assert identity.index("assert_code_identity_complete(") < identity.index("code_hash_from_manifest("), (
        "an incomplete manifest must never reach the codeHash")
    assert "codeIdentityExtraFiles" in identity, "a run must be able to declare its own driver"
    assert source.index("self.phase_identity()") < source.index("self.phase_problem("), (
        "identity is established before the problem definition, the gates and the training")


# ----------------------------------------------------- the historical run is untouched

def test_the_accepted_runs_recorded_identity_is_not_rewritten():
    identity = json.loads((ATTEMPT / "identity.json").read_text(encoding="utf-8"))
    assert identity["codeHash"].startswith("a39aa07e23d0")
    recorded = {entry["path"] for entry in identity["codeManifest"]}
    assert "governance/PINN_TRUST_PROTOCOLS_R1.md" not in recorded
    assert "adversarial/core_manifest.draft.json" not in recorded
    assert code_hash_from_manifest(identity["codeManifest"]) == identity["codeHash"], (
        "the recorded manifest must still hash to the recorded codeHash")


def test_the_boundary_change_applies_to_the_next_revision_only(manifest):
    """The new boundary necessarily differs from the accepted run's -- that is the revision rule."""

    identity = json.loads((ATTEMPT / "identity.json").read_text(encoding="utf-8"))
    assert code_hash_from_manifest(manifest) != identity["codeHash"]
    assert len({entry["path"] for entry in manifest}) > len({entry["path"] for entry in identity["codeManifest"]})
