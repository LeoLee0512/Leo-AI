"""Checkpoints must carry the whole optimizer, and a resume must be the same trajectory.

The r1 ensemble saved model weights and nothing else, which is precisely why its ten seeds
could not be continued after the fact. These tests pin the replacement: what a checkpoint
contains, and that reloading one produces the run that would have happened anyway.

They need torch, so the governance virtualenv skips them; they are executed under the
training interpreter by ``experiments/annulus/verify_tests_under_torch.py``.
"""

from __future__ import annotations

import json

import pytest

torch = pytest.importorskip("torch")

from pinn.experiments_annulus import checkpoint_annulus as ckpt          # noqa: E402
from pinn.experiments_annulus import datasets_annulus as ds              # noqa: E402
from pinn.experiments_annulus import pinn_torch_annulus as pinn          # noqa: E402

TOTAL = 120
CUT = 40
PREFIX = 80            # between CUT and TOTAL: a resume must cross the point where the LR is held
SEEDS = {"init": 20261200, "sample": 20261210, "batch": 20261220}

CONFIG = {
    "configId": "annulus-checkpoint-test",
    "network": {"hiddenLayers": 2, "width": 16, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "(R^2-s)(s-a^2)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": TOTAL, "batchSize": 16,
                  "threads": 1, "lrPrefixSteps": PREFIX},
    "lossWeights": {"pde": 1.0},
}


def _config(steps: int) -> dict:
    config = json.loads(json.dumps(CONFIG))
    config["optimizer"]["steps"] = steps
    return config


_CACHE: dict[str, object] = {}


def data():
    """Memoised, not a pytest fixture: this module must also run under the minimal harness in
    ``experiments/annulus/verify_tests_under_torch.py``, which calls each test with no arguments."""

    if "data" not in _CACHE:
        _CACHE["data"] = (ds.area_uniform_interior(64, 20261230), ds.area_uniform_interior(48, 20261240))
    return _CACHE["data"]


def _train(steps, *, checkpoints=(), resume_from=None):
    pool, dev = data()
    captured: dict[int, dict] = {}
    run = pinn.train_run(_config(steps), pool, dev, SEEDS, collocation_count=32, log_every=20,
                         checkpoint_steps=checkpoints,
                         checkpoint_sink=lambda step, state: captured.__setitem__(step, state),
                         resume_from=resume_from)
    return run, captured


def continuous():
    if "continuous" not in _CACHE:
        _CACHE["continuous"] = _train(TOTAL, checkpoints=(CUT, PREFIX, TOTAL))
    return _CACHE["continuous"]


def resumed():
    if "resumed" not in _CACHE:
        _, captured = continuous()
        carried = json.loads(json.dumps(captured[CUT]))      # exactly what a file would give back
        _CACHE["resumed"] = _train(TOTAL, checkpoints=(TOTAL,), resume_from=carried)
    return _CACHE["resumed"]


# ------------------------------------------------------------------ what a checkpoint holds

def test_the_checkpoint_carries_the_adam_moments_and_step_counter():
    _, captured = continuous()
    state = captured[CUT]["optimizerState"]["state"]
    assert state, "Adam must have per-parameter state by step 40"
    for entry in state.values():
        assert "exp_avg" in entry and "exp_avg_sq" in entry, "m_t and v_t are part of the optimizer"
        assert "step" in entry
        assert entry["exp_avg"]["__tensor__"]["data"], "the moments must be stored, not elided"


def test_the_checkpoint_carries_the_schedule_position():
    _, captured = continuous()
    scheduler = captured[CUT]["scheduler"]
    assert scheduler["lastEpoch"] == CUT
    assert scheduler["prefixSteps"] == PREFIX
    assert scheduler["gamma"] == pinn.schedule_of(CONFIG["optimizer"], TOTAL)[0]
    assert scheduler["currentLr"] and all(lr > 0 for lr in scheduler["currentLr"])


def test_the_checkpoint_carries_the_batch_generator_and_the_cursor():
    _, captured = continuous()
    state = captured[CUT]
    assert state["batchGeneratorState"]["__tensor__"]["data"], "the shuffle generator state must be stored"
    assert isinstance(state["cursor"], int)
    assert len(state["order"]) == 32
    assert sorted(state["order"]) == list(range(32)), "the order is a permutation of the collocation indices"


def test_the_checkpoint_carries_the_global_rng_states():
    _, captured = continuous()
    assert "cpu" in captured[CUT]["rngStates"]


def test_the_checkpoint_survives_a_json_round_trip():
    _, captured = continuous()
    restored = json.loads(json.dumps(captured[CUT]))
    assert restored == captured[CUT], "a checkpoint that only survives in memory is not a checkpoint"


def test_the_checkpoint_names_the_trajectory_it_belongs_to():
    _, captured = continuous()
    for step, state in captured.items():
        assert state["seeds"] == SEEDS
        assert state["currentStep"] == step
        assert state["schemaVersion"] == ckpt.CHECKPOINT_SCHEMA


def test_the_three_checkpoints_are_one_trajectory():
    """Nested, not three separate runs: each is the later state of the same optimization."""

    _, captured = continuous()
    steps = sorted(captured)
    assert steps == [CUT, PREFIX, TOTAL]
    assert [captured[s]["scheduler"]["lastEpoch"] for s in steps] == [CUT, PREFIX, PREFIX]
    assert len({json.dumps(captured[s]["seeds"], sort_keys=True) for s in steps}) == 1
    assert [captured[s]["optimizerState"]["state"]["0"]["step"]["__tensor__"]["data"][0] for s in steps] == \
        [float(CUT), float(PREFIX), float(TOTAL)]


# ------------------------------------------------------------------ resume fidelity

def test_resume_reproduces_the_uninterrupted_parameters_bitwise():
    _, straight = continuous()
    _, split = resumed()
    assert split[TOTAL]["modelState"] == straight[TOTAL]["modelState"]


def test_resume_reproduces_the_uninterrupted_optimizer_state_bitwise():
    _, straight = continuous()
    _, split = resumed()
    assert split[TOTAL]["optimizerState"] == straight[TOTAL]["optimizerState"]


def test_resume_reproduces_the_uninterrupted_schedule_and_batch_state():
    _, straight = continuous()
    _, split = resumed()
    assert split[TOTAL]["scheduler"] == straight[TOTAL]["scheduler"]
    assert split[TOTAL]["batchGeneratorState"] == straight[TOTAL]["batchGeneratorState"]
    assert split[TOTAL]["cursor"] == straight[TOTAL]["cursor"]
    assert split[TOTAL]["order"] == straight[TOTAL]["order"]


def test_resume_reproduces_the_uninterrupted_dev_metric_bitwise():
    straight_run, _ = continuous()
    split_run, _ = resumed()
    assert split_run["devRelL2"] == straight_run["devRelL2"]
    assert split_run["resumedFromStep"] == CUT


def test_resume_refuses_a_checkpoint_from_other_seeds():
    _, captured = continuous()
    foreign = json.loads(json.dumps(captured[CUT]))
    foreign["seeds"] = {"init": 1, "sample": 2, "batch": 3}
    with pytest.raises(ValueError, match="belongs to seeds"):
        _train(TOTAL, resume_from=foreign)


def test_resume_refuses_a_checkpoint_with_a_different_lr_prefix():
    """A different prefix is a different schedule, so it is a different trajectory."""

    _, captured = continuous()
    foreign = json.loads(json.dumps(captured[CUT]))
    foreign["scheduler"]["prefixSteps"] = PREFIX + 1
    with pytest.raises(ValueError, match="LR prefix"):
        _train(TOTAL, resume_from=foreign)


def test_resume_refuses_an_unknown_checkpoint_schema():
    _, captured = continuous()
    foreign = json.loads(json.dumps(captured[CUT]))
    foreign["schemaVersion"] = "something/0.1"
    with pytest.raises(ValueError, match="schema"):
        _train(TOTAL, resume_from=foreign)


# ------------------------------------------------------------------ the schedule, under training

def test_the_logged_learning_rate_matches_the_schedule_helper():
    run, _ = continuous()
    logged = {entry["step"]: entry["lr"] for entry in run["lossHistory"] if "lr" in entry}
    steps = sorted(logged)
    expected = pinn.learning_rates(CONFIG["optimizer"], TOTAL, steps, logged=True)
    assert [logged[s] for s in steps] == expected


def test_the_training_loop_holds_the_learning_rate_after_the_prefix():
    run, captured = continuous()
    logged = {entry["step"]: entry["lr"] for entry in run["lossHistory"] if "lr" in entry}
    past = [step for step in logged if step > PREFIX]
    assert past, "the fixture must train past the prefix"
    terminal = captured[PREFIX]["scheduler"]["currentLr"][0]
    assert all(logged[step] == terminal for step in past)


def test_the_record_reports_whether_the_schedule_was_budget_coupled():
    run, _ = continuous()
    assert run["lrSchedule"]["budgetCoupled"] is False
    assert run["lrSchedule"]["prefixSteps"] == PREFIX
    assert run["checkpointSteps"] == [CUT, PREFIX, TOTAL]


# --------------------------------------------------------------------- the corrupted control must converge

def test_the_corrupted_control_converges_and_loses_its_order():
    """The positive control has to RUN before it can detect anything.

    The first version updated ``u = u + residual / diagonal`` while residual is A u - b, so it
    ascended and diverged to NaN whatever the operator was -- and the criterion read NaN as
    "outside the band", i.e. as a pass. Repaired, the corrupted operator converges and stalls:
    dropping the 1/r term makes the scheme inconsistent, so refinement buys almost nothing.
    """

    from pinn.experiments_annulus import exclusion_annulus as ex

    result = ex.corrupted_polar_refinement([(16, 64), (32, 128)])
    for level in result["levels"]:
        assert level["finalMaxResidual"] < 1e-6, "the control must actually solve its own system"
        assert level["iterations"] < 200000
        assert level["relL2"] == level["relL2"], "no NaN"
    orders = result["observedOrders"]
    assert all(o == o for o in orders), "a control that produced NaN did not execute"
    assert any(not (1.8 <= o <= 2.2) for o in orders), "the corruption must be detectable"


def test_the_true_operator_still_converges_at_second_order():
    """The bench itself is faithful: the uncorrupted reference keeps its order."""

    from scientific_reference import annulus_polar_fdm as fdm
    from pinn.reference import analytic_annulus as reference

    diagnostic = fdm.refinement_diagnostic(reference.forcing, reference.solution,
                                           levels=((16, 64), (32, 128)))
    assert all(1.8 <= o <= 2.2 for o in diagnostic["observedOrders"])


def test_the_frozen_g3_field_cannot_satisfy_its_own_frozen_condition():
    """The preregistration froze r^(2/3) and a 'hotspot in bin 0' condition. They contradict.

    A d^(2/3) field vanishes at its anchor and grows with distance, so its hotspot lands against
    the OUTER circle; the frozen pass condition demands the inner one. The implementation used
    d^(-1/3), which does land in bin 0 -- the satisfiable reading of a self-contradictory spec.
    """

    from pinn.experiments_annulus import exclusion_annulus as ex
    from pinn.experiments_annulus import datasets_annulus as ds
    from pinn.reference import analytic_annulus as reference

    dev = ds.area_uniform_interior(512, 20261340)
    exact = [reference.solution(x, y) for x, y in dev]

    literal = ex.singular_error_field(dev, exponent=2.0 / 3.0)
    literal_stat = ex.independent_localized_statistic(dev, literal["errors"], exact)
    assert not literal_stat["worstCell"].startswith("0,"), (
        "the literally frozen field does not land in bin 0, which is what the frozen condition demands")

    executed = ex.singular_error_field(dev)
    executed_stat = ex.independent_localized_statistic(dev, executed["errors"], exact)
    assert executed_stat["worstCell"].startswith("0,"), "what was actually run does land in bin 0"
