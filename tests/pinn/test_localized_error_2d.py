"""Dimension-aware localized-error signature (Final Closure Audit issue 5).

The inherited 1D rule (max block / median block > 3.0) fires on a *correct* 2D
solution.  These tests pin down what the replacement machinery must do, and they
pin down the honest verdict: the best calibrated candidate still misfires on a
validated run, so the symptom rule is registered NOT CALIBRATED for d >= 2 rather
than shipped with a threshold fitted to that run.
"""

import json
import math
from pathlib import Path

import pytest

from pinn.experiments2d import localized_error as le

ROOT = Path(__file__).resolve().parents[2]
CALIBRATION = ROOT / "experiments/poisson2d/LOCALIZED_ERROR_CALIBRATION.json"


def statistics_for(fixture: str, points, blocks_per_axis: int = 8, amplitude: float = 1e-5):
    exact = le.reference_field(points)
    errors = le.fixture_fields(points, amplitude)[fixture]
    return le.block_statistics(points, errors, exact, blocks_per_axis)


def chosen_rule():
    document = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    return document, document["chosen"]["candidate"], document["chosen"]["threshold"]


def test_ordinary_2d_heterogeneity_does_not_fire_the_calibrated_rule():
    _document, candidate, threshold = chosen_rule()
    for points in (le.uniform_grid(48), le.pseudo_random_grid(1024)):
        for fixture in le.NON_LOCALIZED_FIXTURES:
            stats = statistics_for(fixture, points)
            assert not le.signature_fired(stats, candidate=candidate, threshold=threshold), (
                f"{fixture} is a correct, non-localized field and must not fire the signature")


def test_synthetic_hotspots_fire_the_calibrated_rule():
    _document, candidate, threshold = chosen_rule()
    for points in (le.uniform_grid(48), le.pseudo_random_grid(1024)):
        for fixture in le.LOCALIZED_FIXTURES:
            stats = statistics_for(fixture, points)
            assert le.signature_fired(stats, candidate=candidate, threshold=threshold), (
                f"{fixture} carries a genuine hotspot and must fire the signature")


def test_a_global_increase_is_not_reported_as_localized():
    """Ten times worse everywhere is a different failure than a hotspot, and must not be confused with one."""

    _document, candidate, threshold = chosen_rule()
    points = le.uniform_grid(48)
    heterogeneous = statistics_for("heterogeneous", points)
    global_increase = statistics_for("globalIncrease", points)
    assert global_increase["domainErrorRms"] > 5 * heterogeneous["domainErrorRms"], "the fixture must be globally worse"
    for stats in (heterogeneous, global_increase):
        assert not le.signature_fired(stats, candidate=candidate, threshold=threshold)
    # the localization statistic barely moves, while the global error norm moves by an order of magnitude:
    # that is exactly the separation between a localized signature and a global one.
    a, b = le.CANDIDATES[candidate](heterogeneous), le.CANDIDATES[candidate](global_increase)
    assert abs(a - b) <= 0.25 * max(a, b, 1e-12)


def test_the_inherited_1d_rule_is_retired_because_it_misfires_on_a_validated_run():
    document, _candidate, _threshold = chosen_rule()
    check = document["completedRunCheck"]
    assert check["seedsFiringUnderOld1DRule"] >= 1, "the record must keep the measured false-positive count"
    assert document["oldRule"]["threshold"] == 3.0 and document["oldRule"]["bins"] == 10
    assert document["deploymentVerdict"]["falsePositiveSeedsOld1DRule"] == check["seedsFiringUnderOld1DRule"]


def test_the_calibrated_candidate_is_not_shipped_while_it_still_misfires():
    document, _candidate, _threshold = chosen_rule()
    verdict = document["deploymentVerdict"]
    if verdict["falsePositiveSeedsChosenRule"] > 0:
        assert verdict["decision"] == "NOT CALIBRATED FOR DEPLOYMENT"
        assert verdict["deployable"] is False
        assert any("empirical null" in line.lower() or "EMPIRICAL null" in line
                   for line in [verdict["reasoning"]] + verdict["prospectiveProtocol"])
    else:
        assert verdict["decision"] == "CALIBRATED" and verdict["deployable"] is True


def test_calibration_never_used_the_completed_run():
    document, _candidate, _threshold = chosen_rule()
    assert document["prospective"] is True
    assert "the completed run's value never enters the calibration" in document["decisionRule"][-1]
    assert document["completedRunCheck"]["note"].startswith("check only")


def test_robust_z_degeneracies_are_decided_explicitly():
    assert le._robust_z([2.0, 2.0, 2.0, 2.0]) == 0.0                  # a perfectly flat bulk is not an outlier
    assert le._robust_z([1.0, 1.0, 1.0, 9.0]) == math.inf             # an isolated spike over a flat bulk is
    assert le._robust_z([1.0, 2.0, 3.0, 4.0]) > 0.0
    assert le._robust_z([1.0, 1.0 + 1e-15, 1.0, 1.0]) == 0.0          # float64 noise is not a signal


def test_reference_conditioning_excludes_blocks_where_the_solution_vanishes():
    points = le.uniform_grid(32)
    stats = statistics_for("heterogeneous", points)
    floor = le.REFERENCE_FLOOR_FRACTION * stats["domainReferenceRms"]
    kept = le.relative_block_errors(stats)
    assert len(kept) == sum(1 for value in stats["referenceRms"] if value > floor)
    # at this partition every block still carries solution mass, so nothing is excluded; raising the floor
    # exercises the safeguard itself -- blocks whose reference magnitude is negligible are dropped, not floored.
    raised = le.relative_block_errors(stats, floor_fraction=0.6)
    assert len(raised) < len(stats["referenceRms"])
    assert all(math.isfinite(value) for value in raised)


def test_governance_classification_is_protocol_not_constitutional():
    document, _candidate, _threshold = chosen_rule()
    classification = document["governanceClassification"]
    assert classification["amendmentNeeded"] is False
    assert "PROTOCOL CALIBRATION" in classification["verdict"]
