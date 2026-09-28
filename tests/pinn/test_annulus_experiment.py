"""Datasets, claim pool, gate registry and runner discipline of the annulus experiment.

Pure Python where possible so the governance virtualenv runs it; the pieces that
need numpy (the area-uniform draw) are skipped there and executed under the
training interpreter by ``experiments/annulus/verify_tests_under_torch.py``.
"""

import ast
import math
from pathlib import Path

import pytest

from pinn.experiments_annulus import datasets_annulus as ds
from pinn.experiments_annulus import gates_annulus as gates
from pinn.geometry import annulus as geo
from pinn.governance import annulus_contract as contract
from pinn.governance.evaluation_sets import sample_set_hash, validate_evaluation_set

ROOT = Path(__file__).resolve().parents[2]

#: The four blind claim members: pairwise coprime angular counts and distinct
#: angular offsets, so no two members (and no member and D_phys) can share a node.
POOL = {
    "DAC-M0": {"quadratureRadialOrder": 34, "quadratureAngularCount": 125, "angularOffset": 0.011,
               "pointwiseCglCount": 50, "pointwiseAngularCount": 33, "pointwiseAngularOffset": 0.007},
    "DAC-M1": {"quadratureRadialOrder": 36, "quadratureAngularCount": 127, "angularOffset": 0.013,
               "pointwiseCglCount": 54, "pointwiseAngularCount": 35, "pointwiseAngularOffset": 0.009},
    "DAC-M2": {"quadratureRadialOrder": 38, "quadratureAngularCount": 129, "angularOffset": 0.017,
               "pointwiseCglCount": 56, "pointwiseAngularCount": 37, "pointwiseAngularOffset": 0.011},
    "DAC-M3": {"quadratureRadialOrder": 42, "quadratureAngularCount": 131, "angularOffset": 0.019,
               "pointwiseCglCount": 60, "pointwiseAngularCount": 39, "pointwiseAngularOffset": 0.013},
}


# ------------------------------------------------------------------ datasets

def test_the_physics_grid_is_on_the_domain_and_integrates_it():
    points, weights = ds.phys_grid(40, 128)
    geo.assert_interior(points, label="D_phys")
    assert math.fsum(weights) == pytest.approx(geo.area(), abs=1e-12)
    assert len(points) == 40 * 128


def test_the_boundary_sets_carry_their_component_and_its_own_normal():
    boundary = ds.boundary_sets(64)
    assert set(boundary) == {"outer", "inner"}
    for component, block in boundary.items():
        assert block["component"] == component
        assert block["boundaryIdentityExempt"] is True
        assert len(block["points"]) == len(block["weights"]) == len(block["normals"]) == 64
        geo.assert_on_boundary(block["points"], component)
        assert math.fsum(block["weights"]) == pytest.approx(2 * math.pi * block["radius"], abs=1e-12)
    outer_first = boundary["outer"]["normals"][0]
    inner_first = boundary["inner"]["normals"][0]
    assert outer_first[0] > 0 > inner_first[0], "the two components' normals point in opposite directions"


def test_a_claim_member_covers_every_localized_cell():
    """ACA-9 cannot be evaluated on a grid that leaves a cell empty."""

    member = POOL["DAC-M0"]
    pointwise = ds.claim_pointwise(member["pointwiseCglCount"], member["pointwiseAngularCount"],
                                   member["pointwiseAngularOffset"])
    geo.assert_interior(pointwise, label="claim pointwise")
    cells = {geo.cell_index(point, contract.RADIAL_BINS, contract.ANGULAR_SECTORS) for point in pointwise}
    assert len(cells) == contract.LOCALIZED_CELLS


def test_the_claim_pool_members_are_pairwise_disjoint():
    manifests = ds.claim_pool_manifests(POOL, label="pdef-annulus-test")
    points = {name: set(ds.points_of(document)) for name, document in manifests.items()}
    names = list(points)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            assert not points[first] & points[second], f"{first} and {second} share a sample"
    physics, _weights = ds.phys_grid(40, 128)
    for name, member_points in points.items():
        assert not member_points & set(physics), f"{name} shares a node with D_phys"
    for document in manifests.values():
        assert not validate_evaluation_set(document)
        assert document["role"] == "claim"
        assert sample_set_hash(document)


def test_the_claim_members_have_distinct_sample_identities():
    manifests = ds.claim_pool_manifests(POOL, label="pdef-annulus-test")
    hashes = {name: sample_set_hash(document) for name, document in manifests.items()}
    assert len(set(hashes.values())) == len(hashes)


def test_the_area_uniform_sets_are_disjoint_and_on_the_domain():
    pytest.importorskip("numpy")
    config = {"sampling": {"poolSize": 512, "poolSeed": 20261301},
              "sets": {"devSize": 256, "devSeed": 20261302, "physRadialOrder": 20, "physAngularCount": 64,
                       "minSeparation": 1e-9}}
    member = POOL["DAC-M0"]
    claim_points = ds.claim_member_points(member)
    sets = ds.build_sets(config, claim_points=claim_points, claim_artifact_id="set-claim-test",
                         claim_generator={"generatorId": "DAC-M0",
                                          "generatorVersion": ds.member_generator_version(member)})
    report = ds.isolation_report(sets, min_separation=1e-9)
    assert report["errors"] == []
    assert all(entry["illegal"] == 0 for entry in report["membership"].values())
    assert set(report["sampleSetHashes"]) == {"train", "dev", "phys", "claim"}


def test_a_set_with_a_point_in_the_hole_is_refused():
    with pytest.raises(geo.GeometryError, match="not strictly inside"):
        ds.manifest("bad.json", "dev", [(0.6, 0.0), (0.1, 0.05)],
                    generator={"generatorId": "x", "generatorVersion": "y"}) if False else geo.assert_interior(
            [(0.6, 0.0), (0.1, 0.05)], label="dev")


# ------------------------------------------------------------ gate registry

def test_no_new_gate_and_no_new_trust_status_is_introduced():
    dimensions = {entry["dimension"] for entry in gates.REGISTRY}
    assert dimensions == {"math", "impl", "train", "physics", "external", "repro"}
    ids = [entry["checkId"] for entry in gates.REGISTRY]
    assert len(ids) == len(set(ids))
    assert {"G5b-acceptanceCriteriaMust", "G6-independentReproduction"} <= set(ids)


def test_every_not_applicable_check_carries_its_reason():
    for entry in gates.REGISTRY:
        if entry["applicability"] == "NOT_APPLICABLE":
            assert entry.get("reason", "").strip(), entry["checkId"]


def test_the_geometry_checks_exist_and_are_applicable():
    registry = {entry["checkId"]: entry for entry in gates.REGISTRY}
    for check_id in ("T11-geometryMembership", "T12-boundaryNormalOrientation", "T13-quadratureJacobian",
                     "PH8-geometryMembership", "T4-hardBoundaryBothComponents"):
        assert registry[check_id]["applicability"] == "APPLICABLE"


def test_the_symmetry_check_is_registered_not_applicable_with_the_honest_reason():
    registry = {entry["checkId"]: entry for entry in gates.REGISTRY}
    reason = registry["PH4-symmetry"]["reason"]
    assert "asymmetric" in reason and "faked" in reason
    assert registry["PH5-monotonicity"]["applicability"] == "NOT_APPLICABLE"


# ------------------------------------------------------------ runner discipline

def runner_source():
    return (ROOT / "pinn/experiments_annulus/runner_annulus.py").read_text(encoding="utf-8")


def test_the_identity_completeness_check_precedes_prelock_and_the_code_hash():
    source = runner_source()
    identity = source.split("def phase_identity", 1)[1].split("\n    def ", 1)[0]
    assert identity.index("assert_code_identity_complete(") < identity.index("code_hash_from_manifest(")
    assert identity.index("assert_code_identity_complete(") < identity.index("run_prelock(")
    assert "codeIdentityExtraFiles" in identity


def test_the_claim_guard_reads_the_ledger_before_any_training():
    source = runner_source()
    problem = source.split("def phase_problem", 1)[1].split("\n    def ", 1)[0]
    assert "derived_claim_status(" in problem
    assert problem.index("derived_claim_status(") < problem.index("isolation_report(")
    assert "is not consulted" in problem
    run = source.split("def run(", 1)[1]
    assert run.index("phase_problem()") < run.index("phase_training()")


def test_the_failure_path_measures_on_dev_only():
    source = runner_source()
    failure = source.split("def phase_failure", 1)[1].split("\n    def ", 1)[0]
    assert "self.dev_points" in failure
    assert "claim_points" not in failure and "claimPoints" not in failure
    assert "apply_localized_signature" in failure


def test_the_runner_never_imports_the_square_experiment_modules():
    """Parallel package, not a fork: the square runner must not be dragged in."""

    imported = set()
    for node in ast.walk(ast.parse(runner_source())):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not [name for name in imported if name.startswith("pinn.experiments2d")]
    assert "pinn.experiments.diagnosis" in imported, "the symptom rules are reused, not reimplemented"


def test_the_square_experiment_modules_are_untouched_by_this_round():
    """The CLOSED experiment's runner must not have been edited to fit the annulus."""

    square_runner = (ROOT / "pinn/experiments2d/runner2d.py").read_text(encoding="utf-8")
    for token in ("annulus", "Annulus", "ACA-"):
        assert token not in square_runner


def test_the_anti_collision_rule_runs_on_annulus_nodes():
    """A regression for an API mismatch that only surfaced inside a formal attempt.

    The governance rule takes its denominator limit positionally; calling it with a
    keyword raised TypeError in phase_problem -- after PRELOCK, after the identity was
    written, and only because a long run had been started. It is asserted here, in a
    test that costs milliseconds.
    """

    member = POOL["DAC-M0"]
    points = ds.claim_pointwise(member["pointwiseCglCount"], member["pointwiseAngularCount"],
                                member["pointwiseAngularOffset"])
    report = ds.component_anti_collision(points)
    assert set(report) == {"x", "y", "radius", "minDistance", "ok", "denominatorLimit"}
    assert report["ok"] is True
    assert report["minDistance"] > 1e-12
    assert report["radius"]["minDistance"] > 0.0
