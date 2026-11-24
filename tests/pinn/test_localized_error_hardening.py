"""Hardening of the d >= 2 localized-error trigger (external review of commit 33dc22b).

Three findings were reproduced against the shipped implementation and are fixed here:

1. **Seed-level failures vanished under the ensemble median.** 1/10 and 4/10 seeds
   failing the criterion both left the signature silent, while Gate 5b fails a MUST
   criterion as soon as *one* seed fails it. Aggregation may summarise evidence; it
   may not delete it.
2. **Invalid evidence read as "no failure".** All-NaN, -Inf and negative statistics
   returned ``fired=False``, and unequal array lengths were silently truncated by
   ``zip`` -- a hotspot in the discarded tail simply disappeared.
3. **The criterion id was bound to a threshold, not to a measurement.** A localized
   statistic could be judged against AC2D-2's looser bound and pass.

The tests below are the regression evidence for each, plus the invariant that ties
the ensemble rule to the Gate's own policy rather than to a freshly invented ratio.
"""

import copy
import hashlib
import json
import math
from pathlib import Path

import pytest

from pinn.experiments2d import gates2d
from pinn.experiments2d import localized_error as le
from pinn.governance import poisson2d_contract as contract
from pinn.governance.trust_loop import code_hash_from_manifest
from pinn.validation.poisson2d import ValidationInputError

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "experiments/poisson2d/runs/exp2d-poisson-calibration-r1"
CONTRACT = contract.localized_criterion()
THRESHOLD = float(CONTRACT["threshold"])

CRITERIA = {
    "sLocalizedError": {
        "criterion": CONTRACT["criterionId"],
        "statistic": CONTRACT["statisticId"],
        "normalization": CONTRACT["normalization"],
        "partitionKind": CONTRACT["partitionKind"],
        "tilesPerAxis": CONTRACT["tilesPerAxis"],
        "operator": CONTRACT["operator"],
        "threshold": THRESHOLD,
        "evaluationSet": "dev",
        "preregisteredIn": "experiments/poisson2d/<preregistration>.md",
    }
}

PASSING = 0.1 * THRESHOLD
FAILING = 5.0 * THRESHOLD


def per_seed(values, ratio=2.5):
    return [{"relL2": 1e-5, "localizedRatio": ratio, le.LOCALIZED_STATISTIC: value} for value in values]


def ensemble(failing_count, total=10):
    return per_seed([PASSING] * (total - failing_count) + [FAILING] * failing_count)


def observed(signatures=()):
    return {"observedSignatures": list(signatures),
            "rules": {"sPinnCfd": {"value": 1e-5, "threshold": 1e-3, "fired": False},
                      "sLocalizedError": {"value": 2.5, "threshold": 3.0, "fired": False}},
            "medians": {"relL2": 1e-5, "localizedRatio": 2.5}}


# ------------------------------------------------------------- 1. seed aggregation

@pytest.mark.parametrize("failing_count", [0, 1, 2, 4, 5, 6, 9, 10])
def test_every_failing_seed_is_counted_named_and_visible(failing_count):
    """0/N, a minority, exactly half, a majority and N/N -- the record keeps them all."""

    rule = le.localized_signature(ensemble(failing_count), CRITERIA, dimension=2)
    assert rule["failureCount"] == failing_count
    assert rule["failingSeedIndices"] == list(range(10 - failing_count, 10))
    assert rule["failureFraction"] == pytest.approx(failing_count / 10)
    assert rule["seedCount"] == 10
    assert len(rule["perSeedValues"]) == 10
    assert rule["fired"] is (failing_count > 0), "one failing seed is already an acceptance failure"
    # value and fired must agree: the decisive statistic is reported, not a median that
    # contradicts the verdict
    assert rule["fired"] == le.criterion_failed(rule["value"], rule["threshold"], rule["operator"])


def test_the_reviewer_minority_probes_no_longer_go_silent():
    """The exact probes from the review: 1/10 and 4/10 used to leave fired=False."""

    for failing_count in (1, 4):
        rule = le.localized_signature(ensemble(failing_count), CRITERIA, dimension=2)
        assert rule["fired"] is True
        assert rule["medianStatistic"] < rule["threshold"], (
            "the median is still below the threshold; the verdict must not come from it")


def test_the_ensemble_rule_is_the_gate_policy_not_a_new_ratio():
    """THE invariant: Gate-failing evidence cannot disappear under aggregation.

    For every k, the signature fires exactly when Gate 5b's MUST verdict on the same
    per-seed outcomes is FAIL. The symptom is therefore neither weaker (silently losing
    a real failure) nor stricter (inventing a claim criterion of its own).
    """

    claim_ref = {"sha256": "0" * 64}
    for failing_count in range(11):
        evaluations = [{"failedMustCriteria": [], "failedShouldCriteria": []} for _ in range(10)]
        for index in range(10 - failing_count, 10):
            evaluations[index]["failedMustCriteria"] = [CONTRACT["criterionId"]]
        gate_must = next(c for c in gates2d.external_checks(evaluations, claim_ref, [])
                         if c["checkId"] == "G5b-acceptanceCriteriaMust")
        gate_failed = gate_must["status"] != "PASS"
        fired = le.localized_signature(ensemble(failing_count), CRITERIA, dimension=2)["fired"]
        assert fired == gate_failed, (
            f"{failing_count}/10 failing seeds: signature fired={fired} but Gate 5b MUST failed={gate_failed}")


def test_the_seed_policy_comes_from_the_acceptance_contract():
    assert CONTRACT["seedPolicy"] == "every-seed"
    assert CONTRACT["level"] == "MUST"
    rule = le.localized_signature(ensemble(1), CRITERIA, dimension=2)
    assert rule["seedPolicy"] == "every-seed" and rule["level"] == "MUST"
    source = (ROOT / "pinn/experiments2d/gates2d.py").read_text(encoding="utf-8")
    assert 'must_ok = all(not e["failedMustCriteria"] for e in evaluations)' in source, (
        "the contract's seed policy must keep describing what Gate 5b actually does")


def test_the_diagnosis_record_carries_the_per_seed_evidence():
    result = le.apply_localized_signature(observed(), ensemble(3), CRITERIA, dimension=2)
    trigger = result["localizedErrorTrigger"]
    assert result["observedSignatures"] == ["sLocalizedError"]
    assert trigger["failingSeedIndices"] == [7, 8, 9]
    assert trigger["failureCount"] == 3 and trigger["failureFraction"] == pytest.approx(0.3)
    assert len(trigger["perSeedValues"]) == 10
    assert set(trigger["ensembleStatistic"]) == {"median", "worst", "best"}
    assert trigger["criterionId"] == "AC2D-9" and trigger["seedPolicy"] == "every-seed"


# --------------------------------------------------------------- 2. numeric validity

@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -1.0, -1e-18])
def test_invalid_per_seed_statistics_fail_closed(value):
    """Invalid evidence is not evidence of no localized failure."""

    with pytest.raises(ValidationInputError):
        le.localized_signature(per_seed([value] * 10), CRITERIA, dimension=2)


def test_one_invalid_seed_among_valid_ones_still_fails_closed():
    values = [PASSING] * 9 + [float("nan")]
    with pytest.raises(ValidationInputError):
        le.localized_signature(per_seed(values), CRITERIA, dimension=2)


def test_an_empty_ensemble_is_not_a_passing_ensemble():
    with pytest.raises(ValidationInputError, match="empty ensemble"):
        le.localized_signature([], CRITERIA, dimension=2)


def test_a_missing_statistic_is_named_by_seed():
    with pytest.raises(ValidationInputError, match="seed 1"):
        le.localized_signature([{le.LOCALIZED_STATISTIC: PASSING}, {"relL2": 1e-5}], CRITERIA, dimension=2)


@pytest.mark.parametrize(
    ("label", "points", "errors", "reference", "blocks"),
    [
        ("empty", [], [], [], 8),
        ("zero reference", [(0.2, 0.2), (0.6, 0.6)], [1e-5, 1e-5], [0.0, 0.0], 2),
        ("nan error", [(0.2, 0.2)], [float("nan")], [1.0], 2),
        ("inf error", [(0.2, 0.2)], [float("inf")], [1.0], 2),
        ("nan reference", [(0.2, 0.2)], [1e-5], [float("nan")], 2),
        ("nan coordinate", [(float("nan"), 0.2)], [1e-5], [1.0], 2),
        ("coordinate outside the domain", [(1.4, 0.2)], [1e-5], [1.0], 2),
        ("one-dimensional points", [(0.2,), (0.6,)], [1e-5, 1e-5], [1.0, 1.0], 2),
        ("ragged points", [(0.2, 0.2), (0.6, 0.6, 0.6)], [1e-5, 1e-5], [1.0, 1.0], 2),
        ("zero blocks", [(0.2, 0.2)], [1e-5], [1.0], 0),
        ("negative blocks", [(0.2, 0.2)], [1e-5], [1.0], -8),
        ("fractional blocks", [(0.2, 0.2)], [1e-5], [1.0], 2.5),
        ("boolean blocks", [(0.2, 0.2)], [1e-5], [1.0], True),
    ],
)
def test_invalid_evidence_fields_fail_closed(label, points, errors, reference, blocks):
    with pytest.raises(ValidationInputError):
        le.localized_acceptance_ratio(points, errors, reference, blocks)
    if label == "zero reference":
        # the per-block statistics are still well defined; it is the RELATIVE criterion
        # that has no meaning, and that is where the refusal belongs
        assert le.block_statistics(points, errors, reference, blocks)["domainReferenceRms"] == 0.0
        return
    with pytest.raises(ValidationInputError):
        le.block_statistics(points, errors, reference, blocks)


# ------------------------------------------------------------------- 3. truncation

@pytest.mark.parametrize(
    ("label", "points", "errors", "reference"),
    [
        ("points shorter than errors", [(0.2, 0.2), (0.4, 0.4)], [1e-5, 1e-5, 1.0], [1.0, 1.0, 1.0]),
        ("errors shorter than reference", [(0.2, 0.2), (0.4, 0.4), (0.8, 0.8)], [1e-5, 1e-5], [1.0, 1.0, 1.0]),
        ("reference shorter than points", [(0.2, 0.2), (0.4, 0.4), (0.8, 0.8)], [1e-5, 1e-5, 1.0], [1.0, 1.0]),
    ],
)
def test_unequal_lengths_are_refused_instead_of_truncated(label, points, errors, reference):
    with pytest.raises(ValidationInputError, match="equal length"):
        le.localized_acceptance_ratio(points, errors, reference, 2)
    with pytest.raises(ValidationInputError, match="equal length"):
        le.block_statistics(points, errors, reference, 2)


def test_the_truncation_probe_from_the_review_changes_the_answer():
    """The reviewer's own numbers: dropping the tail turned 100 into 1e-5."""

    points = [(0.2, 0.2), (0.4, 0.4)]
    errors = [1e-5, 1e-5, 1.0]
    reference = [1e-2, 1e-2, 1e-2]
    with pytest.raises(ValidationInputError, match="equal length"):
        le.localized_acceptance_ratio(points, errors, reference, 2)
    aligned = le.localized_acceptance_ratio(points + [(0.8, 0.8)], errors, reference, 2)
    assert aligned > 1.0, "with the third point kept, the hotspot dominates"


# -------------------------------------------------------------- 4. contract binding

def test_the_correct_criterion_and_statistic_are_accepted():
    criterion = le.preregistered_localized_criterion(CRITERIA, dimension=2)
    assert criterion["criterionId"] == "AC2D-9"
    assert criterion["statisticId"] == le.LOCALIZED_STATISTIC
    assert criterion["normalization"] == "globalReferenceRms"
    assert criterion["partitionKind"] == "uniformTiles" and criterion["tilesPerAxis"] == 8
    assert criterion["operator"] == "<=" and float(criterion["threshold"]) == THRESHOLD


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("criterion", "AC2D-2", "not the localized-error criterion"),
        ("criterion", "AC2D-1", "not the localized-error criterion"),
        ("criterion", "AC2D-42", "not an acceptance criterion"),
        ("statistic", "D-referenceConditionedZ", "statisticId"),
        ("statistic", "maxBinToMedianBinRatio", "statisticId"),
        ("normalization", "perTileReference", "normalization"),
        ("normalization", "globalErrorRms", "normalization"),
        ("partitionKind", "quadtree", "partitionKind"),
        ("tilesPerAxis", 4, "partition"),
        ("tilesPerAxis", 16, "partition"),
        ("operator", "<", "operator"),
        ("threshold", 5e-3, "does not equal the acceptance threshold"),
        ("threshold", 1e-4, "does not equal the acceptance threshold"),
        ("evaluationSet", "claim", "D_claim is opened once"),
        ("evaluationSet", "train", "D_claim is opened once"),
    ],
)
def test_every_mismatched_field_is_refused(field, value, message):
    criteria = copy.deepcopy(CRITERIA)
    criteria["sLocalizedError"][field] = value
    with pytest.raises(ValueError, match=message):
        le.preregistered_localized_criterion(criteria, dimension=2)


def test_the_wrong_criterion_cannot_borrow_a_looser_threshold():
    """The review's exact construction: AC2D-2's 5e-3 must not judge a localized value of 2e-3."""

    borrowed = copy.deepcopy(CRITERIA)
    borrowed["sLocalizedError"]["criterion"] = "AC2D-2"
    borrowed["sLocalizedError"]["threshold"] = contract.thresholds()["AC2D-2"]
    with pytest.raises(ValueError, match="not the localized-error criterion"):
        le.localized_signature(per_seed([2e-3] * 10), borrowed, dimension=2)
    assert le.localized_signature(per_seed([2e-3] * 10), CRITERIA, dimension=2)["fired"] is True


@pytest.mark.parametrize("field", list(le._LOCALIZED_REQUIRED_FIELDS))
def test_every_required_field_must_be_present(field):
    criteria = copy.deepcopy(CRITERIA)
    criteria["sLocalizedError"].pop(field)
    with pytest.raises(ValidationInputError, match="no preregistered localized-error acceptance criterion"):
        le.preregistered_localized_criterion(criteria, dimension=2)


def test_the_contract_is_the_single_source_of_truth():
    """Statistic, normalization, partition, operator and threshold all resolve from the id."""

    assert contract.LOCALIZED_ERROR_CRITERION["threshold"] == contract.thresholds()["AC2D-9"]
    assert contract.LOCALIZED_ERROR_CRITERION["level"] == dict(
        (cid, level) for cid, _limit, level in contract.CRITERIA)["AC2D-9"]
    assert contract.LOCALIZED_ERROR_CRITERION["tilesPerAxis"] == contract.TILES_PER_AXIS
    assert contract.LOCALIZED_ERROR_CRITERION["definition"] == contract.METRICS["AC2D-9"][0]
    assert "8 x 8 tiles" in contract.LOCALIZED_ERROR_CRITERION["evaluationGrid"]
    with pytest.raises(ValueError):
        contract.localized_criterion("AC2D-1")


# ------------------------------------------- 5. the existing Poisson2D fixture still behaves

def test_the_validated_run_still_passes_and_a_hotspot_still_fails():
    per_seed_ac2d9 = [seed["metrics"]["AC2D-9"]
                      for seed in json.loads((ATTEMPT / "gate5b_external.json").read_text(encoding="utf-8"))["perSeed"]]
    assert len(per_seed_ac2d9) == 10 and max(per_seed_ac2d9) < THRESHOLD
    rule = le.localized_signature(per_seed(per_seed_ac2d9, ratio=3.94), CRITERIA, dimension=2)
    assert rule["fired"] is False and rule["failureCount"] == 0

    points = le.pseudo_random_grid(1024)
    reference = le.reference_field(points)
    fields = le.fixture_fields(points, amplitude=1e-5)
    quiet = le.localized_acceptance_ratio(points, fields["heterogeneousOscillatory"], reference, 8)
    hotspot = le.localized_acceptance_ratio(points, [10.0 * e for e in fields["singleHotspot"]], reference, 8)
    assert quiet < THRESHOLD < hotspot
    assert le.localized_signature(per_seed([hotspot] * 10), CRITERIA, dimension=2)["fired"] is True


# ------------------------------------------------------------ 6. revision / code identity

def test_the_hardened_implementation_cannot_claim_the_accepted_runs_code_identity():
    """PART 5: the next formal run must use a new revision; this proves the old one is gone."""

    identity = json.loads((ATTEMPT / "identity.json").read_text(encoding="utf-8"))
    manifest = identity["codeManifest"]
    recorded = {entry["path"]: entry["sha256"] for entry in manifest}
    # the localized-error module did not exist yet when the run was recorded: a file the
    # identity never covered cannot be part of it now either
    assert "pinn/experiments2d/localized_error.py" not in recorded
    assert (ROOT / "pinn/experiments2d/localized_error.py").is_file()
    for changed in ("pinn/governance/poisson2d_contract.py", "pinn/experiments2d/diagnostics2d.py",
                    "pinn/experiments2d/runner2d.py"):
        current = hashlib.sha256((ROOT / changed).read_bytes()).hexdigest()
        assert changed in recorded, f"{changed} must be inside the code identity"
        assert current != recorded[changed], (
            f"{changed} was changed since the accepted run; its bytes cannot still be that run's")
    rebuilt = [dict(entry) for entry in manifest]
    for entry in rebuilt:
        path = ROOT / entry["path"]
        if path.is_file():
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    rebuilt.append({"path": "pinn/experiments2d/localized_error.py",
                    "sha256": hashlib.sha256((ROOT / "pinn/experiments2d/localized_error.py").read_bytes()).hexdigest()})
    assert code_hash_from_manifest(rebuilt) != identity["codeHash"], (
        "the working tree must not be able to pose as the code identity that produced the existing C2")
    assert identity["codeHash"].startswith("a39aa07e23d0")


def test_a_criterion_added_after_the_accepted_run_still_cannot_reach_it(tmp_path):
    manifest = json.loads((ATTEMPT / "identity.json").read_text(encoding="utf-8"))["codeManifest"]
    config = ROOT / "experiments/poisson2d/configs/exp2d_baseline.json"
    assert le.assert_criterion_within_run_identity(config, manifest)
    retrofitted = json.loads(config.read_text(encoding="utf-8"))
    retrofitted["signatureCriteria"]["sLocalizedError"].update(CRITERIA["sLocalizedError"])
    forged = tmp_path / "experiments/poisson2d/configs/exp2d_baseline.json"
    forged.parent.mkdir(parents=True)
    forged.write_text(json.dumps(retrofitted, indent=2), encoding="utf-8")
    with pytest.raises(ValidationInputError, match="may not be used to trigger a signature on it"):
        le.assert_criterion_within_run_identity(forged, manifest)


def test_the_accepted_runs_recorded_evidence_is_untouched():
    """PART 4: the historical artifacts this round must not have moved."""

    gate5b = json.loads((ATTEMPT / "gate5b_external.json").read_text(encoding="utf-8"))
    assert gate5b["codeHash"].startswith("a39aa07e23d0")
    assert all(not seed["failedMust"] for seed in gate5b["perSeed"])
    assert gate5b["thresholds"]["AC2D-9"] == THRESHOLD, "the accepted run's threshold must be unchanged"
    decision = json.loads((ATTEMPT / "claim_gate_decision_g6_p11.json").read_text(encoding="utf-8"))
    assert [claim["level"] for claim in decision["allowedClaims"]] == ["C0", "C1", "C2"]
    assert [claim["level"] for claim in decision["blockedClaims"]] == ["C3"]
    assert decision["codeHash"].startswith("a39aa07e23d0"), (
        "the decision stays bound to the code identity that produced it")
    criteria = json.loads((ROOT / "experiments/poisson2d/configs/exp2d_baseline.json").read_text(
        encoding="utf-8"))["signatureCriteria"]["sLocalizedError"]
    assert "criterion" not in criteria, "the accepted run's frozen configuration must stay untouched"


def test_nan_cannot_enter_through_the_retired_statistic():
    result = le.apply_localized_signature(observed(), per_seed([PASSING] * 10, ratio=float("nan")),
                                          CRITERIA, dimension=2)
    assert "retiredStatistic" not in result["rules"]["sLocalizedError"], (
        "a non-finite retired statistic is dropped, never aggregated")
    assert math.isfinite(result["rules"]["sLocalizedError"]["value"])
