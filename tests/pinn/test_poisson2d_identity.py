"""2D sample identity, dataset disjointness and the 2D claim pool (PART 22)."""

import math

import pytest

from pinn.governance.evaluation_sets import (
    disjointness_errors,
    load_evaluation_set,
    sample_identity,
    sample_set_hash,
    validate_evaluation_set,
)


def manifest(points, role="claim", artifact_id="set-test-2d"):
    return {"schemaVersion": "pinn.evaluationSet/1.0", "artifactId": artifact_id, "role": role,
            "inputNames": ["x", "y"], "generator": {"generatorId": "test", "generatorVersion": "1"},
            "samples": [{"inputs": [float(x), float(y)], "kind": "interior"} for x, y in points]}


def test_two_dimensional_points_have_distinct_identities_and_order_matters():
    a = sample_identity([0.25, 0.75])
    b = sample_identity([0.75, 0.25])
    c = sample_identity([0.25, 0.7500000000000001])
    assert a != b, "(x, y) and (y, x) must not collapse to the same sample id"
    assert a != c, "float64 neighbours are different samples"
    assert a == sample_identity([0.25, 0.75])
    assert sample_identity([-0.0, 0.5]) == sample_identity([0.0, 0.5])
    # a 2D identity must not equal the 1D identity of either component
    assert a != sample_identity([0.25]) and a != sample_identity([0.75])


def test_coordinate_count_must_match_input_names():
    document = manifest([(0.1, 0.2)])
    document["samples"].append({"inputs": [0.3], "kind": "interior"})
    errors = validate_evaluation_set(document)
    assert any("expected 2 coordinate" in e for e in errors)


def test_duplicate_and_non_finite_two_dimensional_samples_are_rejected():
    duplicate = manifest([(0.1, 0.2), (0.1, 0.2)])
    assert any("duplicate" in e for e in validate_evaluation_set(duplicate))
    non_finite = manifest([(0.1, float("nan"))])
    assert any("finite" in e for e in validate_evaluation_set(non_finite))


def test_sample_set_hash_ignores_order_and_artifact_id():
    left = manifest([(0.1, 0.2), (0.3, 0.4)], artifact_id="set-a")
    right = manifest([(0.3, 0.4), (0.1, 0.2)], artifact_id="set-b")
    assert sample_set_hash(left) == sample_set_hash(right)


def test_two_dimensional_sets_are_checked_sample_wise_and_by_separation():
    train = load_evaluation_set(manifest([(0.1, 0.1), (0.2, 0.2)], role="train", artifact_id="set-train"))
    claim_shared = load_evaluation_set(manifest([(0.2, 0.2), (0.9, 0.9)], role="claim", artifact_id="set-claim"))
    errors = disjointness_errors({"train": train, "claim": claim_shared})
    assert any("share 1 sample" in e for e in errors)
    claim_close = load_evaluation_set(manifest([(0.2 + 1e-12, 0.2), (0.9, 0.9)], role="claim", artifact_id="set-claim2"))
    assert not disjointness_errors({"train": train, "claim": claim_close})
    near = disjointness_errors({"train": train, "claim": claim_close}, min_separation=1e-9)
    assert any("minimum separation" in e for e in near)


def test_claim_pool_members_are_mutually_disjoint_and_anti_collision_clean():
    pytest.importorskip("numpy")
    from pinn.experiments2d import datasets2d as ds

    pool = {"D2C-GL32-CGL50": (32, 50), "D2C-GL34-CGL54": (34, 54)}
    manifests = ds.claim_pool_manifests(pool, label="pdef-test")
    loaded = {name: load_evaluation_set(doc) for name, doc in manifests.items()}
    names = list(loaded)
    shared = set(loaded[names[0]].identities) & set(loaded[names[1]].identities)
    assert not shared, "preregistered pool members must not share a sample"
    for name, doc in manifests.items():
        points = ds.points_of(doc)
        assert len(set(points)) == len(points)
        assert all(0.0 < x < 1.0 and 0.0 < y < 1.0 for x, y in points)
        report = ds.component_anti_collision(points)
        assert report["ok"], f"{name} collides with a rational lattice point: {report}"


def test_tensor_grids_have_the_expected_sizes_and_weights():
    pytest.importorskip("numpy")
    from pinn.experiments2d import datasets2d as ds

    points, weights = ds.gauss_legendre_square(8)
    assert len(points) == 64 and len(weights) == 64
    assert abs(math.fsum(weights) - 1.0) < 1e-14
    interior = ds.cgl_interior_square(10)
    assert len(interior) == 64
    assert all(0.0 < x < 1.0 and 0.0 < y < 1.0 for x, y in interior)
    boundary, boundary_weights = ds.boundary_nodes(8)
    assert len(boundary) == 32
    assert abs(math.fsum(boundary_weights) - 4.0) < 1e-14
    assert all(x in (0.0, 1.0) or y in (0.0, 1.0) for x, y in boundary)
