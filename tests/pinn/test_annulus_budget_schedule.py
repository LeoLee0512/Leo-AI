"""The budget-decoupled LR schedule, the B* rule, and the firewalls around the diagnosis.

None of these need torch: they are properties of the schedule arithmetic, of the archived
r1 evidence, and of the diagnostic driver's structure. The checkpoint and resume behaviour
lives in ``test_annulus_checkpoint_resume.py``, which does need torch.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from pinn.experiments_annulus.localized_error_annulus import LOCALIZED_STATISTIC
from pinn.experiments_annulus.pinn_torch_annulus import learning_rates, schedule_of

REPO = Path(__file__).resolve().parents[2]
R1_ATTEMPT = REPO / "experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu"
BASELINE_CONFIG = REPO / "experiments/annulus/configs/exp_annulus_baseline.json"
DRIVER = REPO / "experiments/annulus/run_nested_budget_diagnosis.py"
EXCLUSION_DRIVER = REPO / "experiments/annulus/run_exclusion_experiments.py"

R1_STEPS = 120000
DIAGNOSTIC_BUDGETS = (120000, 180000, 240000)


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _driver():
    return _load(DRIVER)


def _exclusion_driver():
    return _load(EXCLUSION_DRIVER)


def _baseline_optimizer() -> dict:
    return json.loads(BASELINE_CONFIG.read_text(encoding="utf-8"))["optimizer"]


def _diagnostic_optimizer() -> dict:
    cfg = _baseline_optimizer()
    cfg["lrPrefixSteps"] = R1_STEPS
    return cfg


def _archived_learning_rates() -> dict[int, float]:
    run = json.loads((R1_ATTEMPT / "runs/run-00.json").read_text(encoding="utf-8"))
    return {entry["step"]: entry["lr"] for entry in run["lossHistory"] if "lr" in entry}


# --------------------------------------------------------------------- the schedule

def test_the_fixed_prefix_schedule_reproduces_the_archived_120k_trajectory_bitwise():
    """Every learning rate the r1 ensemble recorded, reproduced exactly.

    The comparison is against what the run actually logged, not against the closed form:
    ``ExponentialLR`` multiplies the current rate by gamma step after step, and after tens of
    thousands of multiplications that is one or two ULP away from ``lr0 * gamma ** t``.
    """

    archived = _archived_learning_rates()
    assert archived, "the r1 attempt must carry its learning-rate history"
    steps = sorted(archived)
    reproduced = learning_rates(_diagnostic_optimizer(), max(DIAGNOSTIC_BUDGETS), steps, logged=True)
    mismatches = [(s, archived[s], got) for s, got in zip(steps, reproduced) if archived[s] != got]
    assert mismatches == [], f"{len(mismatches)} of {len(steps)} learning rates differ from the archived run"


@pytest.mark.parametrize("step", [1, 30000, 60000, 90000, 120000])
def test_the_representative_prefix_steps_match_the_archived_run(step):
    archived = _archived_learning_rates()
    assert step in archived, f"the archived history must log step {step}"
    got = learning_rates(_diagnostic_optimizer(), max(DIAGNOSTIC_BUDGETS), [step], logged=True)[0]
    assert got == archived[step]


def test_the_learning_rate_is_held_exactly_at_the_terminal_value_after_the_prefix():
    opt = _diagnostic_optimizer()
    terminal = learning_rates(opt, max(DIAGNOSTIC_BUDGETS), [R1_STEPS], logged=True)[0]
    held = learning_rates(opt, max(DIAGNOSTIC_BUDGETS), [R1_STEPS + 1, 180000, 240000], logged=True)
    assert held == [terminal, terminal, terminal]
    # and the applied rate one step past the prefix is that same held value
    assert learning_rates(opt, 240000, [R1_STEPS + 1])[0] == terminal


def test_the_schedule_does_not_depend_on_the_requested_budget():
    """The defect that made the retrospective continuation impossible must not come back."""

    opt = _diagnostic_optimizer()
    probes = [1, 30000, 60000, 90000, 120000, 120001, 180000]
    rates = [learning_rates(opt, budget, probes) for budget in DIAGNOSTIC_BUDGETS]
    assert rates[0] == rates[1] == rates[2]
    gammas = {schedule_of(opt, budget) for budget in DIAGNOSTIC_BUDGETS}
    assert gammas == {schedule_of(opt, R1_STEPS)}


def test_without_the_prefix_field_the_schedule_is_still_budget_coupled():
    """The old behaviour is preserved for anything that has not opted in, byte for byte."""

    opt = _baseline_optimizer()
    assert "lrPrefixSteps" not in opt
    assert schedule_of(opt, R1_STEPS) != schedule_of(opt, 240000)
    # and with the budget it was actually run at, it is the r1 schedule
    assert schedule_of(opt, R1_STEPS) == schedule_of(_diagnostic_optimizer(), 240000)


def test_a_non_positive_prefix_is_refused():
    opt = _diagnostic_optimizer()
    opt["lrPrefixSteps"] = 0
    with pytest.raises(ValueError):
        schedule_of(opt, 240000)


# --------------------------------------------------------------------- the B* rule

def _verdict(budget: int, *, all_pass: bool) -> dict:
    return {"budget": budget, "allPass": all_pass}


def test_b_star_is_the_smallest_passing_budget_above_the_baseline():
    select = _driver().select_b_star
    verdicts = [_verdict(120000, all_pass=False), _verdict(180000, all_pass=True), _verdict(240000, all_pass=True)]
    assert select(verdicts, 120000) == 180000


def test_b_star_falls_through_to_the_larger_budget_only_when_the_smaller_one_fails():
    select = _driver().select_b_star
    verdicts = [_verdict(120000, all_pass=False), _verdict(180000, all_pass=False), _verdict(240000, all_pass=True)]
    assert select(verdicts, 120000) == 240000


def test_no_b_star_when_the_maximum_budget_still_fails():
    select = _driver().select_b_star
    verdicts = [_verdict(b, all_pass=False) for b in DIAGNOSTIC_BUDGETS]
    assert select(verdicts, 120000) is None


def test_the_baseline_budget_can_never_be_b_star():
    """B* answers "does continuing help"; the budget that already failed cannot answer it."""

    select = _driver().select_b_star
    assert select([_verdict(120000, all_pass=True)], 120000) is None


def test_the_driver_carries_no_escalation_beyond_the_preregistered_maximum():
    module = _driver()
    assert module.BUDGETS == DIAGNOSTIC_BUDGETS
    assert max(module.BUDGETS) == 240000
    source = DRIVER.read_text(encoding="utf-8")
    for forbidden in ("300000", "360000", "480000", "while ", "budget *= ", "budget +="):
        assert forbidden not in source, f"the driver must not contain {forbidden!r}: no automatic escalation"


# --------------------------------------------------------------------- the firewalls

def test_the_diagnosis_reads_only_dev_and_never_a_claim_set():
    module = _driver()
    config = module.diagnostic_config(json.loads(BASELINE_CONFIG.read_text(encoding="utf-8")),
                                      max(DIAGNOSTIC_BUDGETS))
    assert config["diagnostic"]["claimSetsRead"] == []
    assert config["signatureCriteria"]["sLocalizedError"]["evaluationSet"] == "dev"
    source = DRIVER.read_text(encoding="utf-8")
    for forbidden in ("claim_grids", "claim_quadrature", "claim_pointwise", "make_event", "write_ledger",
                      "OPENED", "SEALED\"", "claim_evaluation"):
        assert forbidden not in source, f"the diagnostic driver must not reference {forbidden!r}"


def test_the_localized_contract_is_carried_over_unchanged():
    """A diagnosis that invents its own local standard measures nothing about the failure."""

    module = _driver()
    baseline = json.loads(BASELINE_CONFIG.read_text(encoding="utf-8"))
    config = module.diagnostic_config(baseline, max(DIAGNOSTIC_BUDGETS))
    assert config["signatureCriteria"]["sLocalizedError"] == baseline["signatureCriteria"]["sLocalizedError"]
    assert config["signatureCriteria"]["sLocalizedError"]["statistic"] == LOCALIZED_STATISTIC
    assert config["physicsThresholds"] == baseline["physicsThresholds"]
    assert config["preregistration"] == baseline["preregistration"]


def test_the_diagnostic_config_changes_only_the_budget_and_the_schedule_representation():
    module = _driver()
    baseline = json.loads(BASELINE_CONFIG.read_text(encoding="utf-8"))
    config = module.diagnostic_config(baseline, max(DIAGNOSTIC_BUDGETS))
    assert config["optimizer"]["steps"] == 240000
    assert config["optimizer"]["lrPrefixSteps"] == R1_STEPS
    for field in ("name", "lr", "finalLr", "batchSize", "threads"):
        assert config["optimizer"][field] == baseline["optimizer"][field]
    for section in ("network", "geometry", "sampling", "sets", "claimPool", "lossWeights"):
        assert config[section] == baseline[section], f"{section} must be carried over unchanged"


def test_the_paired_cohort_is_the_r1_seed_identities():
    module = _driver()
    baseline = json.loads(BASELINE_CONFIG.read_text(encoding="utf-8"))
    triplets = module.paired_seed_triplets(baseline, 10)
    assert len(triplets) == 10
    for index in range(10):
        recorded = json.loads((R1_ATTEMPT / f"runs/run-{index:02d}.json").read_text(encoding="utf-8"))["seeds"]
        assert {k: triplets[index][k] for k in ("init", "sample", "batch")} == recorded


def test_the_diagnosis_is_not_a_claim_revision():
    module = _driver()
    baseline = json.loads(BASELINE_CONFIG.read_text(encoding="utf-8"))
    config = module.diagnostic_config(baseline, max(DIAGNOSTIC_BUDGETS))
    assert config["diagnostic"]["formalEvidence"] is False
    assert config["diagnostic"]["marking"] == "DIAGNOSTIC"
    assert config["configId"] != baseline["configId"]


# --------------------------------------------------------------------- the history stays put

def test_the_r1_evidence_is_untouched_by_the_diagnosis():
    identity = json.loads((R1_ATTEMPT / "identity.json").read_text(encoding="utf-8"))
    summary = json.loads((R1_ATTEMPT / "RUN_SUMMARY.json").read_text(encoding="utf-8"))
    assert identity["codeHash"] == "8ee9b9236199996fe95684b42bb6a247717f07bb5845437ac7c85ff7978b550e"
    assert summary["finalState"] == "FAILURE_RECORDED"
    assert summary["trustVector"]["external"] == "FAIL"
    assert summary["failure"]["observedSignatures"] == ["sLocalizedError"]
    # r1 saved weights and nothing else: this is the fact that made the retrospective
    # continuation impossible, and it must stay visible in the record
    run = json.loads((R1_ATTEMPT / "runs/run-00.json").read_text(encoding="utf-8"))
    assert "weights" in run
    assert "optimizerState" not in run and "schedulerState" not in run


def test_the_burnt_claim_member_stays_burnt_and_the_others_stay_sealed_shut():
    events = json.loads((REPO / "experiments/annulus/ledger/pdef-annulus-poisson-v1.json")
                        .read_text(encoding="utf-8"))
    # Revision 2 (owner's ruling 2026-09-26) appends DAC-M1 events; r1's two events are
    # an immutable prefix and DAC-M0 may never appear again after them.
    assert [e["eventId"][:8] for e in events[:2]] == ["7152b353", "df1b1c50"]
    assert [e["event"] for e in events[:2]] == ["SEALED", "OPENED"]
    burnt = events[0]["sampleSetHash"]
    assert events[1]["sampleSetHash"] == burnt
    assert all(e["sampleSetHash"] != burnt and e["revision"] in (2, 3) for e in events[2:]), (
        "after r1 only events of revisions 2 and 3 (other members) may follow")


def test_the_r1_dev_metric_at_120k_is_available_for_the_prefix_comparison():
    """PART 10 needs the archived value; if it is missing the comparison cannot be made."""

    for index in range(10):
        run = json.loads((R1_ATTEMPT / f"runs/run-{index:02d}.json").read_text(encoding="utf-8"))
        history = {entry["step"]: entry for entry in run["lossHistory"]}
        assert 120000 in history
        assert history[120000]["devRelL2"] == run["devRelL2"]


# --------------------------------------------------------------------- positive controls fail closed

def test_a_positive_control_that_diverged_is_not_a_positive_control():
    """NaN is not "outside the band", it is the absence of a measurement.

    The corrupted-operator control of exp-annulus-dx-reference diverged instead of losing an
    order of convergence, and the first version of the check read that as a pass because
    ``1.8 <= nan`` is False. That is the defect the localized-error trigger was hardened
    against on 2026-09-16, reappearing in this round's own code.
    """

    verdict = _exclusion_driver().control_verdict
    assert verdict([float("nan")]) == (False, False)
    assert verdict([float("inf")]) == (False, False)
    assert verdict([2.0, float("nan")]) == (False, False)
    assert verdict([]) == (False, False), "no measurement is not a detection either"


def test_a_positive_control_detects_a_lost_order():
    verdict = _exclusion_driver().control_verdict
    assert verdict([1.02, 0.98]) == (True, True), "first order instead of second: detected"
    assert verdict([2.0016, 2.0004]) == (True, False), "still second order: the control saw nothing"
    assert verdict([2.0, 1.0]) == (True, True), "one level outside the band is enough"
