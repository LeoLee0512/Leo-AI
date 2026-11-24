"""The deployed d >= 2 localized-error trigger (external review ruling 2026-09-16, item 4/5).

The ruling replaced the question. Instead of fitting a heuristic threshold to a block
statistic -- which the calibration showed cannot be done honestly from synthetic nulls --
``sLocalizedError`` for d >= 2 fires exactly when the localized-error acceptance criterion
the experiment preregistered in its ScientificSpec fails. For Poisson-2D that is AC2D-9.

These tests pin the five properties the ruling names, plus the two that make it safe: the
criterion must exist before the run, and it can never be attached to a run afterwards.
"""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from pinn.experiments2d import localized_error as le
from pinn.governance import poisson2d_contract as contract
from pinn.governance.trust_loop import code_hash_from_manifest

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "experiments/poisson2d/runs/exp2d-poisson-calibration-r1"
PROTOCOL = ROOT / "experiments/poisson2d/LOCALIZED_ERROR_TRIGGER_PROTOCOL_20260916.json"
CONFIG = ROOT / "experiments/poisson2d/configs/exp2d_baseline.json"

THRESHOLD = contract.thresholds()["AC2D-9"]

CONTRACT = contract.localized_criterion()

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


def per_seed(localized_values, rel_l2=1e-5, ratio=2.5):
    """Dev diagnostics in the shape ``dev_diagnostics`` returns, one record per seed."""

    return [{"relL2": rel_l2, "localizedRatio": ratio, le.LOCALIZED_STATISTIC: value}
            for value in localized_values]


def observed(signatures=()):
    """What ``observed_signatures`` would hand over before the d >= 2 override."""

    return {"observedSignatures": list(signatures),
            "rules": {"sPinnCfd": {"value": 1e-5, "threshold": 1e-3, "fired": False},
                      "sLocalizedError": {"value": 2.5, "threshold": 3.0, "fired": False}},
            "medians": {"relL2": 1e-5, "localizedRatio": 2.5}}


# ----------------------------------------------------------------- the trigger itself

def test_a_passing_global_metric_with_a_failing_localized_criterion_fires_the_signature():
    """The case the signature exists for: accurate on average, wrong in one place."""

    result = le.apply_localized_signature(observed(), per_seed([5.0 * THRESHOLD] * 10), CRITERIA, dimension=2)
    assert result["observedSignatures"] == ["sLocalizedError"]
    rule = result["rules"]["sLocalizedError"]
    assert rule["fired"] is True
    assert rule["criterion"] == "AC2D-9" and rule["threshold"] == THRESHOLD
    assert rule["failureCount"] == 10 and rule["failingSeedIndices"] == list(range(10))
    # the global metric is untouched and still passing: the two are independent
    assert result["rules"]["sPinnCfd"]["fired"] is False
    assert result["medians"]["relL2"] == 1e-5


def test_a_satisfied_localized_criterion_does_not_fire_the_signature():
    result = le.apply_localized_signature(observed(), per_seed([0.1 * THRESHOLD] * 10), CRITERIA, dimension=2)
    assert result["observedSignatures"] == []
    assert result["rules"]["sLocalizedError"]["fired"] is False
    assert result["rules"]["sLocalizedError"]["failureCount"] == 0


def test_the_completed_run_would_not_fire_under_the_deployed_trigger():
    """The validated 2D run: AC2D-9 worst seed 1.568e-4 against 1e-3 -- no symptom.

    This is the whole point of the ruling: the retired 1D statistic called that same run
    localized on 9 of 10 seeds.
    """

    worst_seed_ac2d9 = max(seed["metrics"]["AC2D-9"]
                           for seed in json.loads((ATTEMPT / "gate5b_external.json").read_text(encoding="utf-8"))["perSeed"])
    assert worst_seed_ac2d9 < THRESHOLD
    result = le.apply_localized_signature(observed(), per_seed([worst_seed_ac2d9] * 10, ratio=3.94), CRITERIA, dimension=2)
    assert result["observedSignatures"] == []
    retired = result["rules"]["sLocalizedError"]["retiredStatistic"]
    assert retired["maxOverMedianRatioMedian"] > retired["retiredThreshold"], (
        "the retired 1D rule would have fired here; it must be reported and not acted on")


def test_the_signature_leaves_every_other_observed_signature_alone():
    result = le.apply_localized_signature(observed(["sPdeResidual", "sLocalizedError"]),
                                          per_seed([0.1 * THRESHOLD] * 10), CRITERIA, dimension=2)
    assert result["observedSignatures"] == ["sPdeResidual"], (
        "a signature the 1D rule fired must be withdrawn, and nothing else touched")


def test_the_statistic_is_the_ac2d9_quantity_and_sees_a_hotspot():
    """The dev-side statistic and the acceptance criterion are one measurement, two point sets."""

    points = le.pseudo_random_grid(1024)
    reference = le.reference_field(points)
    fields = le.fixture_fields(points, amplitude=1e-5)
    quiet = le.localized_acceptance_ratio(points, fields["heterogeneousOscillatory"], reference, 8)
    hotspot = le.localized_acceptance_ratio(points, [10.0 * e for e in fields["singleHotspot"]], reference, 8)
    assert quiet < THRESHOLD < hotspot
    stats = le.block_statistics(points, fields["singleHotspot"], reference, 8)
    assert le.localized_acceptance_ratio(points, fields["singleHotspot"], reference, 8) == pytest.approx(
        max(stats["errorRms"]) / stats["domainReferenceRms"])


# ------------------------------------------------------- preregistration discipline

def test_a_criterion_that_was_never_preregistered_is_refused():
    for criteria in ({}, {"sLocalizedError": {}},
                     {"sLocalizedError": {"tilesPerAxis": 8, "bins": 64, "maxBinToMedianBinRatio": 3.0}}):
        with pytest.raises(ValueError, match="no preregistered localized-error acceptance criterion"):
            le.preregistered_localized_criterion(criteria, dimension=2)


def test_the_symptom_may_not_invent_its_own_bound_or_its_own_statistic():
    loosened = copy.deepcopy(CRITERIA)
    loosened["sLocalizedError"]["threshold"] = 10.0 * THRESHOLD
    with pytest.raises(ValueError, match="does not equal the acceptance threshold"):
        le.preregistered_localized_criterion(loosened, dimension=2)

    unknown = copy.deepcopy(CRITERIA)
    unknown["sLocalizedError"]["criterion"] = "AC2D-42"
    with pytest.raises(ValueError, match="not an acceptance criterion"):
        le.preregistered_localized_criterion(unknown, dimension=2)

    other_criterion = copy.deepcopy(CRITERIA)
    other_criterion["sLocalizedError"]["criterion"] = "AC2D-2"
    other_criterion["sLocalizedError"]["threshold"] = contract.thresholds()["AC2D-2"]
    with pytest.raises(ValueError, match="not the localized-error criterion"):
        le.preregistered_localized_criterion(other_criterion, dimension=2)

    other_statistic = copy.deepcopy(CRITERIA)
    other_statistic["sLocalizedError"]["statistic"] = "D-referenceConditionedZ"
    with pytest.raises(ValueError, match="does not match criterion AC2D-9's statisticId"):
        le.preregistered_localized_criterion(other_statistic, dimension=2)


def test_the_diagnosis_may_only_read_the_dev_set():
    """D_claim is opened once, for acceptance; adaptive tuning on it is what the lifecycle prevents."""

    on_claim = copy.deepcopy(CRITERIA)
    on_claim["sLocalizedError"]["evaluationSet"] = "claim"
    with pytest.raises(ValueError, match="D_claim is opened once"):
        le.preregistered_localized_criterion(on_claim, dimension=2)
    assert le.LOCALIZED_EVALUATION_SETS == ("dev",)

    source = (ROOT / "pinn/experiments2d/runner2d.py").read_text(encoding="utf-8")
    failure = source.split("def phase_failure", 1)[1].split("\n    def ", 1)[0]
    assert "self.dev_points" in failure and "claim_points" not in failure, (
        "the failure path must measure on D_dev only")
    assert "apply_localized_signature" in failure and "assert_criterion_within_run_identity" in failure


def test_a_criterion_added_after_a_run_cannot_trigger_a_signature_on_it(tmp_path):
    """No retrofit: the config is inside the run's code identity, so a later edit is visible."""

    manifest = json.loads((ATTEMPT / "identity.json").read_text(encoding="utf-8"))["codeManifest"]
    # the configuration as the accepted run recorded it still matches, byte for byte
    assert le.assert_criterion_within_run_identity(CONFIG, manifest) == hashlib.sha256(CONFIG.read_bytes()).hexdigest()

    retrofitted = json.loads(CONFIG.read_text(encoding="utf-8"))
    retrofitted["signatureCriteria"]["sLocalizedError"].update(CRITERIA["sLocalizedError"])
    forged = tmp_path / "experiments/poisson2d/configs/exp2d_baseline.json"
    forged.parent.mkdir(parents=True)
    forged.write_text(json.dumps(retrofitted, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="may not be used to trigger a signature on it"):
        le.assert_criterion_within_run_identity(forged, manifest)

    mutated = [dict(entry) for entry in manifest]
    for entry in mutated:
        if entry["path"].endswith("configs/exp2d_baseline.json"):
            entry["sha256"] = hashlib.sha256(forged.read_bytes()).hexdigest()
    assert code_hash_from_manifest(mutated) != code_hash_from_manifest(manifest), (
        "adding a criterion changes the code identity; it cannot pose as the accepted run")


def test_the_accepted_run_is_not_retro_triggered():
    """The completed run keeps the criteria it preregistered; this round did not edit them."""

    criteria = json.loads(CONFIG.read_text(encoding="utf-8"))["signatureCriteria"]["sLocalizedError"]
    assert "criterion" not in criteria, "the accepted run's frozen configuration must stay untouched"
    with pytest.raises(ValueError, match="no preregistered localized-error acceptance criterion"):
        le.preregistered_localized_criterion({"sLocalizedError": criteria}, dimension=2)


def test_one_dimension_keeps_its_own_closed_rule():
    criterion = le.preregistered_localized_criterion(
        {"sLocalizedError": {"bins": 10, "maxBinToMedianBinRatio": 3.0}}, dimension=1)
    assert criterion["kind"] == "symptom-statistic" and criterion["threshold"] == 3.0
    assert le.apply_localized_signature(observed(["sLocalizedError"]), per_seed([5.0 * THRESHOLD]),
                                        CRITERIA, dimension=1)["observedSignatures"] == ["sLocalizedError"]


# ------------------------------------------------------------------ the record itself

def test_the_ruling_is_recorded_and_matches_the_implementation():
    record = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert record["trigger"]["statistic"] == le.LOCALIZED_STATISTIC
    assert record["trigger"]["evaluationSet"] == "dev"
    assert record["preregistrationRequirement"]["requiredFields"] == list(le._LOCALIZED_REQUIRED_FIELDS)
    assert record["trigger"]["seedPolicy"] == CONTRACT["seedPolicy"]
    assert record["preregistrationRequirement"]["exampleForPoisson2D"]["threshold"] == THRESHOLD
    assert record["governanceClassification"]["amendment"] == "none; no A-0003"
    assert set(record["governanceClassification"]["unchanged"]) >= {
        "FailureSignature names", "RootCause classes", "TrustStatus values", "Claim semantics"}
    assert record["notAppliedRetroactively"]["run"] == "exp2d-poisson-calibration-r1"
    calibration = json.loads((ROOT / "experiments/poisson2d/LOCALIZED_ERROR_CALIBRATION.json").read_text(encoding="utf-8"))
    assert calibration["deploymentVerdict"]["decision"] == "NOT CALIBRATED FOR DEPLOYMENT", (
        "the calibration record is evidence and stays as it was written")
