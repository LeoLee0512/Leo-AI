"""The localized-error trigger on a geometry-native partition (Geometry Lift 1 section 15).

The rule itself is the hardened one of 2026-09-16 and is not re-litigated here:

    for d >= 2, sLocalizedError fires exactly when the localized-error acceptance
    criterion the experiment preregistered FAILS, under that criterion's own seed
    policy, with every per-seed value kept in the record and invalid evidence
    failing closed.

What the annulus changes is the *partition*, and only that. A Cartesian 8 x 8 tile
grid would straddle the hole, give cells of unequal domain area and leave some cells
with no domain in them at all, so the criterion ACA-9 is defined on 4 equal-area
radial bins (uniform in the area fraction t) x 16 angular sectors.

This module deliberately does NOT generalise ``pinn/experiments2d/localized_error.py``
into a partition framework: that module belongs to a CLOSED experiment, and
rewriting it would move the code identity its results are bound to. The shared
semantics are imported where they are public (``criterion_failed``,
``ValidationInputError``), and ``tests/pinn/test_annulus_localized_error.py`` pins
the two implementations to the same verdict for every k of N failing seeds.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping, Sequence

from pinn.experiments2d.localized_error import criterion_failed
from pinn.governance import annulus_contract as contract
from pinn.validation.poisson2d import ValidationInputError

LOCALIZED_SIGNATURE = "sLocalizedError"

#: The statistic name the annulus contract binds; a different name is a different
#: criterion and must be preregistered under its own contract entry.
LOCALIZED_STATISTIC = "maxCellRmsErrorOverReferenceRms"

#: The diagnosis never reads D_claim: the claim set is opened once, for acceptance.
LOCALIZED_EVALUATION_SETS: tuple[str, ...] = ("dev",)

#: Everything a preregistration must state for this partition kind.
REQUIRED_FIELDS: tuple[str, ...] = (
    "criterion", "statistic", "normalization", "partitionKind", "radialBins", "angularSectors",
    "operator", "threshold", "evaluationSet", "preregisteredIn",
)

SEED_POLICIES: tuple[str, ...] = ("every-seed",)


def _number(value: Any, label: str, *, non_negative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationInputError(f"{label} must be a real number, got {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationInputError(
            f"{label} is {number}: invalid evidence is not evidence of no localized failure")
    if non_negative and number < 0.0:
        raise ValidationInputError(f"{label} must be non-negative, got {number}")
    return number


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def ensemble_fired(failure_count: int, seed_count: int, seed_policy: str) -> bool:
    """Gate 5b requires every MUST criterion of every seed, so one failing seed already fails acceptance."""

    if seed_policy == "every-seed":
        return failure_count >= 1
    raise ValidationInputError(f"unknown seed policy {seed_policy!r}")


def preregistered_localized_criterion(criteria: Mapping[str, Any], *, dimension: int,
                                      contract_resolver: Callable[[str], Mapping[str, Any]] | None = None
                                      ) -> dict[str, Any]:
    """The localized criterion this experiment registered, checked field by field against the contract."""

    if dimension < 2:
        raise ValidationInputError("the annulus problem is two-dimensional; there is no 1D path here")
    entry = dict(criteria.get(LOCALIZED_SIGNATURE) or {})
    missing = [field for field in REQUIRED_FIELDS if entry.get(field) in (None, "")]
    if missing:
        raise ValidationInputError(
            f"no preregistered localized-error acceptance criterion for d = {dimension}: missing {missing}. "
            "For d >= 2 the localized-error requirement is carried by an acceptance criterion, which must be "
            "registered in signatureCriteria before the formal run (external review ruling 2026-09-16).")
    resolver = contract_resolver or contract.localized_criterion
    resolved = resolver(str(entry["criterion"]))
    for declared, contracted in (("statistic", "statisticId"), ("normalization", "normalization"),
                                 ("partitionKind", "partitionKind"), ("operator", "operator")):
        if entry[declared] != resolved[contracted]:
            raise ValidationInputError(
                f"the preregistered {declared} {entry[declared]!r} does not match criterion "
                f"{resolved['criterionId']}'s {contracted} {resolved[contracted]!r}")
    if entry["statistic"] != LOCALIZED_STATISTIC:
        raise ValidationInputError(
            f"the localized criterion must use the {LOCALIZED_STATISTIC} statistic, not {entry['statistic']!r}")
    for field in ("radialBins", "angularSectors"):
        if int(entry[field]) != int(resolved[field]):
            raise ValidationInputError(
                f"the preregistered {field} {entry[field]} does not match criterion {resolved['criterionId']}'s "
                f"{resolved[field]}: a different partition is a different criterion")
    if float(entry["threshold"]) != float(resolved["threshold"]):
        raise ValidationInputError(
            f"the localized symptom threshold {entry['threshold']} does not equal the acceptance threshold "
            f"{resolved['threshold']} of {resolved['criterionId']}: the symptom may not carry a bound of its own")
    if entry["evaluationSet"] not in LOCALIZED_EVALUATION_SETS:
        raise ValidationInputError(
            f"the localized-error diagnosis may only read {LOCALIZED_EVALUATION_SETS}, not "
            f"{entry['evaluationSet']!r}: D_claim is opened once for acceptance and is never used for diagnosis")
    seed_policy = str(resolved["seedPolicy"])
    if seed_policy not in SEED_POLICIES:
        raise ValidationInputError(f"unknown seed policy {seed_policy!r} for {resolved['criterionId']}")
    return {"dimension": dimension, "kind": "acceptance-criterion", **entry,
            "criterionId": resolved["criterionId"], "statisticId": resolved["statisticId"],
            "normalization": resolved["normalization"], "partitionKind": resolved["partitionKind"],
            "level": resolved["level"], "seedPolicy": seed_policy, "geometryId": resolved["geometryId"],
            "definition": resolved["definition"]}


def localized_signature(per_seed: Sequence[Mapping[str, Any]], criteria: Mapping[str, Any], *, dimension: int = 2,
                        contract_resolver: Callable[[str], Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """The ``sLocalizedError`` rule entry, with the per-seed evidence kept, not summarised away."""

    criterion = preregistered_localized_criterion(criteria, dimension=dimension, contract_resolver=contract_resolver)
    if not per_seed:
        raise ValidationInputError("no per-seed localized evidence: an empty ensemble is not a passing ensemble")
    values: list[float] = []
    for index, record in enumerate(per_seed):
        if LOCALIZED_STATISTIC not in record:
            raise ValidationInputError(f"seed {index}: the dev diagnostics do not carry {LOCALIZED_STATISTIC}")
        values.append(_number(record[LOCALIZED_STATISTIC], f"seed {index} {LOCALIZED_STATISTIC}", non_negative=True))
    threshold = float(criterion["threshold"])
    operator = str(criterion["operator"])
    failing = [index for index, value in enumerate(values) if criterion_failed(value, threshold, operator)]
    seed_policy = str(criterion["seedPolicy"])
    fired = ensemble_fired(len(failing), len(values), seed_policy)
    worst, median = max(values), _median(values)
    return {
        "value": worst, "threshold": threshold, "fired": bool(fired),
        "rule": (f"the preregistered localized acceptance criterion {criterion['criterionId']} "
                 f"({LOCALIZED_STATISTIC} {operator} {threshold:g} on {criterion['radialBins']} equal-area radial "
                 f"bins x {criterion['angularSectors']} angular sectors, normalized by "
                 f"{criterion['normalization']}) evaluated on D_{criterion['evaluationSet']}, aggregated by the "
                 f"'{seed_policy}' policy Gate 5b applies to {criterion['level']} criteria"),
        "criterion": criterion["criterionId"], "criterionId": criterion["criterionId"],
        "statistic": LOCALIZED_STATISTIC, "statisticId": criterion["statisticId"],
        "normalization": criterion["normalization"], "partitionKind": criterion["partitionKind"],
        "radialBins": int(criterion["radialBins"]), "angularSectors": int(criterion["angularSectors"]),
        "operator": operator, "level": criterion["level"], "evaluationSet": criterion["evaluationSet"],
        "preregisteredIn": criterion["preregisteredIn"], "seedPolicy": seed_policy,
        "geometryId": criterion["geometryId"],
        "perSeedValues": values, "failingSeedIndices": failing, "failureCount": len(failing),
        "failureFraction": len(failing) / len(values), "seedCount": len(values),
        "ensembleStatistic": {"median": median, "worst": worst, "best": min(values)},
        "firedBy": (f"{len(failing)}/{len(values)} seed(s) fail {criterion['criterionId']}" if fired
                    else f"no seed fails {criterion['criterionId']}"),
        "medianStatistic": median,
    }


def apply_localized_signature(observed: Mapping[str, Any], per_seed: Sequence[Mapping[str, Any]],
                              criteria: Mapping[str, Any], *, dimension: int = 2,
                              contract_resolver: Callable[[str], Mapping[str, Any]] | None = None
                              ) -> dict[str, Any]:
    """Replace the inherited symptom rule with the preregistered geometry-native trigger."""

    rule = localized_signature(per_seed, criteria, dimension=dimension, contract_resolver=contract_resolver)
    retired = [_number(record["localizedRatio"], f"seed {index} localizedRatio")
               for index, record in enumerate(per_seed)
               if "localizedRatio" in record and math.isfinite(float(record["localizedRatio"]))]
    if retired:
        rule["retiredStatistic"] = {
            "maxOverMedianRatioMedian": _median(retired), "retiredThreshold": 3.0,
            "note": ("the inherited 1D statistic on the annulus cells, reported for continuity only: NOT CALIBRATED "
                     "for d >= 2 and no part of this decision"),
        }
    out = dict(observed)
    rules = dict(out.get("rules", {}))
    rules[LOCALIZED_SIGNATURE] = rule
    out["rules"] = rules
    fired = [name for name in out.get("observedSignatures", []) if name != LOCALIZED_SIGNATURE]
    if rule["fired"]:
        fired.append(LOCALIZED_SIGNATURE)
        order = list(rules)
        fired.sort(key=lambda name: order.index(name) if name in order else len(order))
    out["observedSignatures"] = fired
    medians = dict(out.get("medians", {}))
    medians[LOCALIZED_STATISTIC] = rule["medianStatistic"]
    out["medians"] = medians
    out["localizedErrorTrigger"] = {
        "dimension": dimension, "criterionId": rule["criterionId"], "statisticId": rule["statisticId"],
        "normalization": rule["normalization"], "partitionKind": rule["partitionKind"],
        "radialBins": rule["radialBins"], "angularSectors": rule["angularSectors"],
        "operator": rule["operator"], "threshold": rule["threshold"], "evaluationSet": rule["evaluationSet"],
        "preregisteredIn": rule["preregisteredIn"], "seedPolicy": rule["seedPolicy"],
        "geometryId": rule["geometryId"], "perSeedValues": rule["perSeedValues"],
        "failingSeedIndices": rule["failingSeedIndices"], "failureCount": rule["failureCount"],
        "failureFraction": rule["failureFraction"], "ensembleStatistic": rule["ensembleStatistic"],
        "fired": rule["fired"], "firedBy": rule["firedBy"],
        "ruling": ("external review ruling 2026-09-16 item 4 as hardened the same day: the symptom fires exactly when "
                   "the preregistered localized acceptance criterion fails, under that criterion's seed policy. "
                   "Geometry Lift 1 changes only the partition, which is equal-area and geometry-native because a "
                   "Cartesian tile grid would straddle the hole."),
    }
    return out
