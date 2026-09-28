"""The geometry-native localized-error trigger (Geometry Lift 1 section 15).

The *semantics* are the hardened ones of 2026-09-16 and must not drift: a failing
seed is never averaged away, invalid evidence fails closed, and the criterion is
bound to one statistic, one normalisation, one partition, one operator and one
threshold. What the annulus changes is the partition, and these tests pin exactly
that -- including an equivalence test against the square implementation, so the two
cannot diverge silently.
"""

import copy
import math

import pytest

from pinn.experiments2d import localized_error as square
from pinn.experiments_annulus import localized_error_annulus as annulus
from pinn.geometry import annulus as geo
from pinn.governance import annulus_contract as contract
from pinn.governance import poisson2d_contract as square_contract
from pinn.validation.poisson2d import ValidationInputError

CONTRACT = contract.localized_criterion()
THRESHOLD = float(CONTRACT["threshold"])

CRITERIA = {
    "sLocalizedError": {
        "criterion": CONTRACT["criterionId"],
        "statistic": CONTRACT["statisticId"],
        "normalization": CONTRACT["normalization"],
        "partitionKind": CONTRACT["partitionKind"],
        "radialBins": CONTRACT["radialBins"],
        "angularSectors": CONTRACT["angularSectors"],
        "operator": CONTRACT["operator"],
        "threshold": THRESHOLD,
        "evaluationSet": "dev",
        "preregisteredIn": "experiments/annulus/<preregistration>.md",
    }
}

SQUARE_CONTRACT = square_contract.localized_criterion()
SQUARE_CRITERIA = {
    "sLocalizedError": {
        "criterion": SQUARE_CONTRACT["criterionId"], "statistic": SQUARE_CONTRACT["statisticId"],
        "normalization": SQUARE_CONTRACT["normalization"], "partitionKind": SQUARE_CONTRACT["partitionKind"],
        "tilesPerAxis": SQUARE_CONTRACT["tilesPerAxis"], "operator": SQUARE_CONTRACT["operator"],
        "threshold": float(SQUARE_CONTRACT["threshold"]), "evaluationSet": "dev", "preregisteredIn": "x",
    }
}

PASSING = 0.1 * THRESHOLD
FAILING = 5.0 * THRESHOLD


def per_seed(values, ratio=2.5):
    return [{annulus.LOCALIZED_STATISTIC: value, "localizedRatio": ratio, "relL2": 1e-5} for value in values]


def ensemble(failing_count, total=10):
    return per_seed([PASSING] * (total - failing_count) + [FAILING] * failing_count)


# ------------------------------------------------------- the partition is the change

def test_the_criterion_is_the_annulus_one_and_its_partition_is_geometry_native():
    criterion = annulus.preregistered_localized_criterion(CRITERIA, dimension=2)
    assert criterion["criterionId"] == "ACA-9"
    assert criterion["statisticId"] == "maxCellRmsErrorOverReferenceRms"
    assert criterion["partitionKind"] == "annulusEqualAreaCells"
    assert (criterion["radialBins"], criterion["angularSectors"]) == (4, 16)
    assert criterion["geometryId"] == geo.GEOMETRY["geometryId"]
    assert criterion["seedPolicy"] == "every-seed" and criterion["level"] == "MUST"


def test_the_square_partition_cannot_be_used_on_the_annulus():
    """A Cartesian tile grid would straddle the hole: it is not a valid partition here."""

    borrowed = copy.deepcopy(CRITERIA)
    borrowed["sLocalizedError"]["partitionKind"] = "uniformTiles"
    with pytest.raises(ValidationInputError, match="partitionKind"):
        annulus.preregistered_localized_criterion(borrowed, dimension=2)

    missing_partition = copy.deepcopy(CRITERIA)
    missing_partition["sLocalizedError"].pop("radialBins")
    with pytest.raises(ValidationInputError, match="no preregistered localized-error acceptance criterion"):
        annulus.preregistered_localized_criterion(missing_partition, dimension=2)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("criterion", "ACA-1", "not the localized-error criterion"),
        ("criterion", "ACA-2", "not the localized-error criterion"),
        ("criterion", "ACA-42", "not an acceptance criterion"),
        ("statistic", "maxTileRmsErrorOverReferenceRms", "statisticId"),
        ("normalization", "perCellReference", "normalization"),
        ("radialBins", 8, "radialBins"),
        ("angularSectors", 32, "angularSectors"),
        ("operator", "<", "operator"),
        ("threshold", 5e-3, "does not equal the acceptance threshold"),
        ("evaluationSet", "claim", "D_claim is opened once"),
    ],
)
def test_every_mismatched_field_is_refused(field, value, message):
    criteria = copy.deepcopy(CRITERIA)
    criteria["sLocalizedError"][field] = value
    with pytest.raises(ValueError, match=message):
        annulus.preregistered_localized_criterion(criteria, dimension=2)


# --------------------------------------------- the hardened semantics do not drift

@pytest.mark.parametrize("failing_count", [0, 1, 2, 5, 9, 10])
def test_the_annulus_and_square_triggers_agree_for_every_k_of_n(failing_count):
    """Same seed policy, same verdict: the geometry changed the partition, not the rule."""

    annulus_rule = annulus.localized_signature(ensemble(failing_count), CRITERIA)
    square_values = [PASSING] * (10 - failing_count) + [
        5.0 * float(SQUARE_CONTRACT["threshold"])] * failing_count
    square_rule = square.localized_signature(
        [{square.LOCALIZED_STATISTIC: value, "localizedRatio": 2.5} for value in square_values],
        SQUARE_CRITERIA, dimension=2)
    assert annulus_rule["fired"] == square_rule["fired"]
    assert annulus_rule["failureCount"] == square_rule["failureCount"] == failing_count
    assert annulus_rule["failingSeedIndices"] == square_rule["failingSeedIndices"]
    assert annulus_rule["seedPolicy"] == square_rule["seedPolicy"] == "every-seed"


def test_a_minority_of_failing_seeds_still_fires():
    for failing_count in (1, 4):
        rule = annulus.localized_signature(ensemble(failing_count), CRITERIA)
        assert rule["fired"] is True
        assert rule["medianStatistic"] < rule["threshold"], "the median must not be the decision"


def test_a_satisfied_criterion_does_not_fire():
    rule = annulus.localized_signature(ensemble(0), CRITERIA)
    assert rule["fired"] is False and rule["failureCount"] == 0
    assert rule["value"] == pytest.approx(PASSING)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -1.0])
def test_invalid_per_seed_evidence_fails_closed(value):
    with pytest.raises(ValidationInputError):
        annulus.localized_signature(per_seed([value] * 10), CRITERIA)


def test_an_empty_ensemble_is_not_a_passing_ensemble():
    with pytest.raises(ValidationInputError, match="empty ensemble"):
        annulus.localized_signature([], CRITERIA)


def test_the_applied_record_keeps_the_per_seed_evidence():
    observed = {"observedSignatures": [], "rules": {}, "medians": {}}
    result = annulus.apply_localized_signature(observed, ensemble(3), CRITERIA)
    trigger = result["localizedErrorTrigger"]
    assert result["observedSignatures"] == ["sLocalizedError"]
    assert trigger["failingSeedIndices"] == [7, 8, 9] and trigger["failureCount"] == 3
    assert trigger["failureFraction"] == pytest.approx(0.3)
    assert trigger["partitionKind"] == "annulusEqualAreaCells"
    assert trigger["geometryId"] == geo.GEOMETRY["geometryId"]
    assert set(trigger["ensembleStatistic"]) == {"median", "worst", "best"}
    assert "retiredStatistic" in result["rules"]["sLocalizedError"]


def test_a_non_finite_retired_statistic_is_dropped_not_aggregated():
    observed = {"observedSignatures": [], "rules": {}, "medians": {}}
    result = annulus.apply_localized_signature(observed, per_seed([PASSING] * 10, ratio=float("nan")), CRITERIA)
    assert "retiredStatistic" not in result["rules"]["sLocalizedError"]
    assert math.isfinite(result["rules"]["sLocalizedError"]["value"])


# ------------------------------------------------ the statistic is the ACA-9 quantity

def test_the_dev_statistic_and_the_acceptance_criterion_are_the_same_measurement():
    """Same numerator and denominator as ACA-9, evaluated on a different point set."""

    from pinn.reference import analytic_annulus as ref

    points = [geo.to_cartesian(geo.radius_of_area_fraction(((i * 0.6180339887) % 1.0) * 0.998 + 0.001),
                               2 * math.pi * ((i * 0.371) % 1.0))
              for i in range(4000)]
    exact = [ref.solution(x, y) for x, y in points]
    quiet = [1e-6 * value for value in exact]
    hotspot = list(quiet)
    for index, (x, y) in enumerate(points):
        radius, _theta = geo.to_polar((x, y))
        if 0.5 < radius < 0.6:
            hotspot[index] += 0.02

    def statistic(errors):
        cells = {}
        for point, error in zip(points, errors):
            cells.setdefault(geo.cell_index(point, 4, 16), []).append(error * error)
        cell_rms = [math.sqrt(math.fsum(values) / len(values)) for values in cells.values()]
        reference_rms = math.sqrt(math.fsum(e * e for e in exact) / len(exact))
        return max(cell_rms) / reference_rms

    assert statistic(quiet) < THRESHOLD < statistic(hotspot)
    assert annulus.localized_signature(per_seed([statistic(hotspot)] * 10), CRITERIA)["fired"] is True
    assert annulus.localized_signature(per_seed([statistic(quiet)] * 10), CRITERIA)["fired"] is False
