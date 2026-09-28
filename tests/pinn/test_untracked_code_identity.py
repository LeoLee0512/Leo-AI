"""An untracked module must not be able to hide from the code identity (external review ruling item 3).

The hole was real and it fired: the nested-budget preregistration first recorded a codeHash
computed before the commit, when ``pinn/experiments_annulus/checkpoint_annulus.py`` was still
untracked and therefore absent from ``git ls-files`` -- so absent from the manifest. Nothing
complained, because ``code_manifest`` only enumerates tracked files and ``workspace_dirty_paths``
passes ``--untracked-files=no``. The cause was confirmed by reproducing the wrong hash exactly
after dropping that one entry.

These tests pin the three parts of the fix: the boundary scan finds such a file, code identity
refuses to be computed while one exists, and PRELOCK refuses to let the attempt start.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from pinn.experiments.common import (
    CodeIdentityError,
    all_tracked_paths,
    assert_code_identity_complete,
    code_hash_from_manifest,
    code_manifest,
    untracked_identity_paths,
)
from pinn.governance.prelock import PrelockPaths, run_prelock

ROOT = Path(__file__).resolve().parents[2]


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repo_with_identity(tmp_path) -> Path:
    """A miniature repository whose tracked files include one module inside the boundary."""

    repo = tmp_path / "repo"
    (repo / "pinn/experiments").mkdir(parents=True)
    (repo / "pinn/experiments/tracked.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "docs").mkdir(parents=True)
    (repo / "docs/report.md").write_text("# report\n", encoding="utf-8")
    _git(repo.parent, "init", "--quiet", str(repo))
    _git(repo, "add", "-A")
    return repo


# --------------------------------------------------------------- the boundary scan

def test_an_untracked_module_inside_the_boundary_is_found(tmp_path):
    repo = _repo_with_identity(tmp_path)
    assert untracked_identity_paths(repo) == []
    (repo / "pinn/experiments/helper.py").write_text("def help():\n    return 2\n", encoding="utf-8")
    assert untracked_identity_paths(repo) == ["pinn/experiments/helper.py"]


def test_an_untracked_file_outside_the_boundary_is_not_the_identity_s_business(tmp_path):
    repo = _repo_with_identity(tmp_path)
    (repo / "docs/new_report.md").write_text("# another report\n", encoding="utf-8")
    (repo / "experiments").mkdir(parents=True, exist_ok=True)
    (repo / "experiments/evidence.json").write_text("{}\n", encoding="utf-8")
    assert untracked_identity_paths(repo) == []


def test_gitignoring_a_helper_does_not_remove_it_from_the_identity(tmp_path):
    """A module does not leave the method by being listed in .gitignore."""

    repo = _repo_with_identity(tmp_path)
    (repo / ".gitignore").write_text("pinn/experiments/hidden.py\n", encoding="utf-8")
    (repo / "pinn/experiments/hidden.py").write_text("SECRET = 3\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    assert untracked_identity_paths(repo) == ["pinn/experiments/hidden.py"]


def test_byte_code_caches_do_not_trip_the_scan(tmp_path):
    """Caches are outputs of the modules, not sources of behaviour."""

    repo = _repo_with_identity(tmp_path)
    (repo / "pinn/experiments/__pycache__").mkdir(parents=True)
    (repo / "pinn/experiments/__pycache__/tracked.cpython-312.pyc").write_bytes(b"\x00\x01")
    assert untracked_identity_paths(repo) == []


# --------------------------------------------------------------- code identity refuses

def test_code_identity_refuses_to_be_computed_while_a_module_is_untracked(tmp_path):
    repo = _repo_with_identity(tmp_path)
    manifest = code_manifest(repo)
    assert_code_identity_complete(manifest, repo)          # clean tree: fine

    (repo / "pinn/experiments/helper.py").write_text("def help():\n    return 2\n", encoding="utf-8")
    with pytest.raises(CodeIdentityError, match="untracked files inside the code-identity boundary"):
        assert_code_identity_complete(code_manifest(repo), repo)


def test_an_untracked_declared_extra_file_is_refused(tmp_path):
    """codeIdentityExtraFiles must be git-tracked: untracked bytes cannot identify a method."""

    repo = _repo_with_identity(tmp_path)
    (repo / "experiments").mkdir(parents=True, exist_ok=True)
    driver = "experiments/driver.py"
    (repo / driver).write_text("print('drives a run')\n", encoding="utf-8")
    manifest = code_manifest(repo, [driver])
    assert driver in {entry["path"] for entry in manifest}, "it does reach the manifest, which is the trap"
    with pytest.raises(CodeIdentityError, match="must be git-tracked"):
        assert_code_identity_complete(manifest, repo, extra_required=[driver])

    _git(repo, "add", driver)
    assert_code_identity_complete(code_manifest(repo, [driver]), repo, extra_required=[driver])


def test_a_declared_file_that_does_not_exist_is_still_refused(tmp_path):
    """Caught one step earlier: as a path the manifest is required to contain and does not."""

    repo = _repo_with_identity(tmp_path)
    with pytest.raises(CodeIdentityError, match="not in the manifest"):
        assert_code_identity_complete(code_manifest(repo), repo, extra_required=["experiments/absent.py"])


def test_tracking_the_module_moves_the_hash_which_is_the_incident_itself(tmp_path):
    """Reproduces what happened to the Phase II preregistration, in miniature."""

    repo = _repo_with_identity(tmp_path)
    before = code_hash_from_manifest(code_manifest(repo))
    (repo / "pinn/experiments/helper.py").write_text("def help():\n    return 2\n", encoding="utf-8")
    assert code_hash_from_manifest(code_manifest(repo)) == before, (
        "this is the defect: while the module is untracked the hash does not notice it at all")
    _git(repo, "add", "-A")
    assert code_hash_from_manifest(code_manifest(repo)) != before
    assert "pinn/experiments/helper.py" in all_tracked_paths(repo)


# --------------------------------------------------------------- PRELOCK refuses (adversarial)

def _prelock_fixture(tmp_path) -> Path:
    """A repository PRELOCK can actually run on: the real governance inputs, tracked."""

    repo = tmp_path / "prelock-repo"
    repo.mkdir()
    # A faithful copy of everything PRELOCK reads. Enumerating the individual files it
    # happens to open today would make this fixture break the next time PRELOCK reads one
    # more, and the test would then fail for a reason that has nothing to do with what it
    # is about, so the whole of pinn/ comes along.
    for relative in ("governance", "adversarial", "specs", "pinn"):
        shutil.copytree(ROOT / relative, repo / relative,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ROOT / ".gitattributes", repo / ".gitattributes")
    _git(repo.parent, "init", "--quiet", str(repo))
    _git(repo, "add", "-A")
    return repo


def test_prelock_rejects_a_tree_whose_imported_helper_is_untracked(tmp_path):
    """The adversarial case the ruling names: the helper is there, the manifest cannot see it.

    The control matters as much as the failure: the same tree must pass before the helper is
    written, so the refusal is attributable to this one fact and not to the fixture.
    """

    repo = _prelock_fixture(tmp_path)
    control = run_prelock(PrelockPaths.defaults(repo))
    assert control["checks"]["codeIdentityTracked"]["status"] == "PASS"
    assert control["prelockStatus"] == "PASS", "the fixture itself must be a tree PRELOCK accepts"

    # a helper the run would import, written but never added
    (repo / "pinn" / "secret_helper.py").write_text(
        "def contributes_to_a_result():\n    return 42\n", encoding="utf-8")

    adversarial = run_prelock(PrelockPaths.defaults(repo))
    assert adversarial["prelockStatus"] == "FAIL", "an attempt must not start on a tree with a hidden module"
    identity = adversarial["checks"]["codeIdentityTracked"]
    assert identity["status"] == "FAIL"
    assert "pinn/secret_helper.py" in identity["errors"][0]

    changed = [name for name, check in adversarial["checks"].items()
               if check["status"] != control["checks"][name]["status"]]
    assert changed == ["codeIdentityTracked"], f"the refusal must come from this check alone, not {changed}"

    # and committing it clears the refusal
    _git(repo, "add", "-A")
    assert run_prelock(PrelockPaths.defaults(repo))["prelockStatus"] == "PASS"


def test_prelock_reports_the_identity_check_on_the_real_repository():
    result = run_prelock(PrelockPaths.defaults(ROOT))
    assert "codeIdentityTracked" in result["checks"]
    assert result["checks"]["codeIdentityTracked"]["status"] == "PASS", (
        f"the working tree has untracked modules inside the identity boundary: "
        f"{untracked_identity_paths(ROOT)}")


# --------------------------------------------------------------------- the import audit must be sound

def test_the_import_audit_includes_the_module_that_adjudicates_the_criterion():
    """The first version hand-picked roots that happened to exclude the adjudicating module.

    ``gates_annulus.external_checks`` is where the ACA-9 MUST verdict is rendered, and
    ``gates_annulus`` imports the independent FDM at module level. An audit asking "can the
    statistic reach the reference?" that never looks at that module reports an empty answer
    which is a property of its root set, not a finding.
    """

    from pinn.experiments_annulus import exclusion_annulus as ex

    audit = ex.statistic_call_path_modules()
    assert "pinn.experiments_annulus.gates_annulus" in audit["roots"]
    assert "pinn.experiments_annulus.gates_annulus" in audit["graph"]
    assert audit["modulesReachingTheNumericalReference"], (
        "gates_annulus does import scientific_reference; an empty answer here means the audit "
        "stopped looking before it got there")


def test_the_import_audit_does_not_stop_at_a_package_node():
    """``pinn.governance`` is a package; its __init__ imports too, and they were being dropped."""

    from pinn.experiments_annulus import exclusion_annulus as ex

    audit = ex.statistic_call_path_modules()
    package_nodes = [name for name in audit["graph"] if (ROOT / name.replace(".", "/")).is_dir()]
    for name in package_nodes:
        init = ROOT / name.replace(".", "/") / "__init__.py"
        if init.is_file() and "import" in init.read_text(encoding="utf-8"):
            assert audit["graph"][name], f"{name} is a package whose __init__ imports; it must not read as a leaf"


def test_the_import_audit_records_modules_not_symbols():
    """``from .x import Y`` imports the module x; Y is a symbol inside it, not a node."""

    from pinn.experiments_annulus import exclusion_annulus as ex

    audit = ex.statistic_call_path_modules()
    for name, imports in audit["graph"].items():
        for item in imports:
            leaf = item.rsplit(".", 1)[-1]
            assert not leaf.isupper(), f"{name} -> {item}: an ALL_CAPS leaf is a constant, not a module"
