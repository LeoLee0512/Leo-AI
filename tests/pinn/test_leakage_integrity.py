import pytest

from pinn.governance.leakage import audit_leakage, coordinate_identity


SETS = {"GL512": [.123, .456], "CGL2000": [0., .333, .666, 1.], "BOUNDARY": [0., 1.]}
GENERATORS = {name: name for name in SETS}


def audit(**kwargs):
    options = dict(training_sets={"collocation": [.1, .2], "boundary": [0, 1]},
                   validation_sets=SETS, validation_generators=GENERATORS)
    options.update(kwargs)
    return audit_leakage(**options)


def test_public_boundary_reuse_is_legal():
    assert audit() == ()
    assert coordinate_identity(-0., 0.)


def test_training_holdout_collision_is_rejected():
    assert any(f.check_id == "L1" for f in audit(training_sets={"collocation": [.123]}))


@pytest.mark.parametrize("consumer", ["optimizer", "adaptive sampler", "early-stopping controller",
                                     "loss-weight scheduler", "architecture selector", "hyperparameter tuner"])
def test_validation_feedback_including_boundary_is_rejected(consumer):
    assert any(f.check_id == "L4" for f in audit(validation_metric_consumers=[consumer]))


def test_generation_parent_is_not_hidden():
    assert any(f.check_id == "L3" for f in audit(validation_parent_is_training=True))


@pytest.mark.parametrize("generators", [None, {}, {"GL512": "training", "CGL2000": "CGL2000", "BOUNDARY": "BOUNDARY"}])
def test_missing_or_wrong_generator_provenance_fails(generators):
    assert any(f.check_id == "L2" for f in audit(validation_generators=generators))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1., 2.])
def test_invalid_coordinates_rejected(value):
    assert audit(training_sets={"collocation": [value]})
    assert audit(validation_sets=dict(SETS, GL512=[value]))


def test_absent_validation_sets_are_not_a_clean_audit():
    assert audit(validation_sets={})


def test_arbitrary_boundary_exemption_not_allowed():
    assert audit(boundary_coordinates=(.123, .456))
