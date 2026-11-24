"""Sample-level isolation of the evaluation sets: distinct hashes are not disjoint sets (draft 3, issue 2)."""

import pytest

from pinn.governance.canonical import canonical_sha256
from pinn.governance.evaluation_sets import (
    disjointness_errors,
    load_evaluation_set,
    sample_identity,
    validate_evaluation_set,
)


def manifest(role, points, *, names=("x",), kind="interior", quantity=None, artifact=None):
    samples = []
    for point in points:
        sample = {"inputs": list(point) if isinstance(point, (list, tuple)) else [point], "kind": kind}
        if quantity is not None:
            sample["quantity"] = quantity
        samples.append(sample)
    return {"schemaVersion": "pinn.evaluationSet/1.0", "artifactId": artifact or f"set-{role}", "role": role,
            "inputNames": list(names), "samples": samples}


def sets(**manifests):
    return {role: load_evaluation_set(document) for role, document in manifests.items()}


def test_sample_identity_is_exact_float64_with_negative_zero_folded():
    assert sample_identity([0.5]) == sample_identity([0.5])
    assert sample_identity([0.5]) != sample_identity([0.5000000000000001])
    assert sample_identity([-0.0]) == sample_identity([0.0])
    assert sample_identity([1]) == sample_identity([1.0])
    assert sample_identity([0.5], "u") != sample_identity([0.5], "p") != sample_identity([0.5])
    with pytest.raises(ValueError):
        sample_identity([float("nan")])
    with pytest.raises(ValueError):
        sample_identity([float("inf")])
    with pytest.raises(ValueError):
        sample_identity([0.5], "  ")


def test_different_hashes_but_overlapping_samples_are_rejected():
    """The reviewer's example: {1,2,3,4,5} versus {1,2,3,4,6}."""

    dev = manifest("dev", [0.1, 0.2, 0.3, 0.4, 0.5])
    claim = manifest("claim", [0.1, 0.2, 0.3, 0.4, 0.6])
    assert canonical_sha256(dev) != canonical_sha256(claim)
    errors = disjointness_errors(sets(dev=dev, claim=claim))
    assert any("dev and claim share 4 sample(s)" in error for error in errors)


def test_identical_samples_serialized_differently_still_collide():
    train = manifest("train", [[1, 0]], names=("x", "t"))
    claim = manifest("claim", [[1.0, -0.0]], names=("x", "t"))
    assert any("share 1 sample" in error for error in disjointness_errors(sets(train=train, claim=claim)))


def test_parameterized_sample_identity_includes_the_parameter():
    train = manifest("train", [[0.5, 0.1, 1.0]], names=("x", "t", "mu"))
    claim = manifest("claim", [[0.5, 0.1, 2.0]], names=("x", "t", "mu"))
    assert disjointness_errors(sets(train=train, claim=claim)) == []
    assert any("minimum separation" in error for error in
               disjointness_errors(sets(train=train, claim=claim), min_separation=1.5))
    assert disjointness_errors(sets(train=train, claim=claim), min_separation=0.5) == []


def test_boundary_points_are_training_visible():
    train = manifest("train", [0.0, 1.0], kind="boundary")
    claim = manifest("claim", [0.0, 0.5], kind="interior")
    assert any("train and claim share 1 sample" in error for error in disjointness_errors(sets(train=train, claim=claim)))


def test_dev_versus_claim_and_train_versus_phys_are_checked_too():
    train = manifest("train", [0.25, 0.75])
    dev = manifest("dev", [0.3, 0.5])
    claim = manifest("claim", [0.5, 0.9])
    phys = manifest("phys", [0.25, 0.6])
    errors = disjointness_errors(sets(train=train, dev=dev, claim=claim, phys=phys))
    assert any("dev and claim share 1 sample" in error for error in errors)
    assert any("train and phys share 1 sample" in error for error in errors)
    assert not any("train and dev" in error for error in errors)


def test_minimum_separation_is_preregistered_and_positive():
    train = manifest("train", [0.5])
    claim = manifest("claim", [0.5 + 1e-9])
    assert disjointness_errors(sets(train=train, claim=claim)) == []
    assert any("below the preregistered minimum separation" in error for error in
               disjointness_errors(sets(train=train, claim=claim), min_separation=1e-6))
    with pytest.raises(ValueError):
        disjointness_errors(sets(train=train, claim=claim), min_separation=0)


def test_sets_must_agree_on_input_names_and_declare_their_role():
    train = manifest("train", [[0.5, 0.1]], names=("x", "t"))
    claim = manifest("claim", [0.5])
    assert any("disagree on inputNames" in error for error in disjointness_errors(sets(train=train, claim=claim)))
    mislabeled = {"dev": load_evaluation_set(manifest("claim", [0.5]))}
    assert any("declares role" in error for error in disjointness_errors(mislabeled))
    with pytest.raises(ValueError):
        disjointness_errors({"test": load_evaluation_set(manifest("dev", [0.5]))})
    with pytest.raises(TypeError):
        disjointness_errors({"dev": manifest("dev", [0.5])})


def test_manifest_validation_rejects_bad_samples():
    assert validate_evaluation_set(manifest("train", [0.1, 0.2])) == []
    duplicate = manifest("train", [0.1, 0.1])
    assert any("duplicate sample" in error for error in validate_evaluation_set(duplicate))
    width = manifest("train", [[0.1, 0.2]], names=("x",))
    assert any("expected 1 coordinate" in error for error in validate_evaluation_set(width))
    observation = manifest("train", [0.1], kind="observation")
    assert any("observed quantity" in error for error in validate_evaluation_set(observation))
    empty = manifest("train", [])
    assert any("at least 1" in error for error in validate_evaluation_set(empty))
    wrong_role = manifest("test", [0.1])
    assert validate_evaluation_set(wrong_role)
    with pytest.raises(ValueError):
        load_evaluation_set(duplicate)
