"""Dimension-aware localized-error signature (Final Closure Audit issue 5).

The 1D failure-signature rule ``sLocalizedError`` fires when

    max_j E_j / median_j E_j > 3.0            (E_j = RMS error of bin j, 10 bins)

In 2D that rule fires on a *correct* solution: the 2D calibration run, which
passed every acceptance criterion with more than an order of magnitude of margin,
measured 3.94.  The reason is structural, not numerical: a PINN's error amplitude
follows the solution's own amplitude, so on a tensor partition of a 2D domain the
blocks legitimately differ by a factor of several -- and the more blocks a
partition has (64 instead of 10), the larger the max/median of any smooth field.
Using that rule in 2D would manufacture a false ``sLocalizedError`` and poison the
root-cause diagnosis of a genuinely failing run.

This module is the *prospective* replacement.  It is not used by, and does not
change, the completed 2D calibration; the next experiment preregisters it in its
``signatureCriteria``.  Nothing here touches the Constitution: a failure signature's
threshold and its dimension-specific implementation live in the protocol and in the
per-experiment preregistration (Constitution chapter 23 leaves the symptom criteria
to the protocol; the RootCause classes, TrustStatus values and Claim semantics are
untouched).

Four candidates are implemented and calibrated against synthetic fixtures whose
ground truth is known by construction; the calibration record is written by
``experiments/poisson2d/calibrate_localized_error.py``.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Iterable, Mapping, Sequence

from pinn.validation.poisson2d import ValidationInputError

#: The fraction of the domain-wide reference RMS used as a floor when a block's own
#: reference magnitude is tiny (near a homogeneous Dirichlet boundary the solution and
#: the error both vanish, and an unfloored ratio would be dominated by round-off).
REFERENCE_FLOOR_FRACTION = 0.1


def block_index(point: Sequence[float], blocks_per_axis: int) -> tuple[int, ...]:
    return tuple(min(int(value * blocks_per_axis), blocks_per_axis - 1) for value in point)


def block_statistics(points: Sequence[Sequence[float]], errors: Sequence[float], reference: Sequence[float],
                     blocks_per_axis: int) -> dict[str, Any]:
    """Per-block RMS of the error and of the reference field on a uniform block partition."""

    points, errors, reference, blocks_per_axis = validate_evidence_fields(points, errors, reference, blocks_per_axis)
    squares: dict[tuple[int, ...], list[float]] = {}
    reference_squares: dict[tuple[int, ...], list[float]] = {}
    for point, error, exact in zip(points, errors, reference):
        key = block_index(point, blocks_per_axis)
        squares.setdefault(key, []).append(error * error)
        reference_squares.setdefault(key, []).append(exact * exact)
    keys = sorted(squares)
    error_rms = [math.sqrt(math.fsum(squares[k]) / len(squares[k])) for k in keys]
    reference_rms = [math.sqrt(math.fsum(reference_squares[k]) / len(reference_squares[k])) for k in keys]
    counts = [len(squares[k]) for k in keys]
    domain_reference_rms = math.sqrt(math.fsum(e * e for e in reference) / len(reference))
    return {"keys": [list(k) for k in keys], "errorRms": error_rms, "referenceRms": reference_rms,
            "counts": counts, "domainReferenceRms": domain_reference_rms,
            "domainErrorRms": math.sqrt(math.fsum(e * e for e in errors) / len(errors)),
            "blocksPerAxis": blocks_per_axis, "dimension": len(points[0])}


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def _mad(values: Sequence[float]) -> float:
    centre = _median(values)
    return _median([abs(v - centre) for v in values])


def _robust_z(values: Sequence[float]) -> float:
    """(max - median) / MAD, with the degenerate cases decided explicitly.

    MAD = 0 means the bulk has no spread at all: then a strictly larger maximum is an
    infinitely strong outlier, while max == median (a perfectly flat field) is no
    outlier at all and must score 0 rather than inf.
    """

    centre = _median(values)
    spread = _mad(values)
    excess = max(values) - centre
    # float64 hygiene: a maximum that differs from the bulk only in the last bits is not an outlier.
    if excess <= 1e-12 * abs(centre):
        return 0.0
    if spread > 0:
        return excess / spread
    return math.inf


# ------------------------------------------------------------------ candidates

def candidate_a_max_over_median(stats: Mapping[str, Any]) -> float:
    """A: the 1D rule, max block error over median block error."""

    values = stats["errorRms"]
    centre = _median(values)
    return max(values) / centre if centre > 0 else math.inf


def candidate_b_robust_z(stats: Mapping[str, Any]) -> float:
    """B: robust z-score of the largest block error, (max - median) / MAD."""

    return _robust_z(stats["errorRms"])


def candidate_c_top_k_concentration(stats: Mapping[str, Any], k: int | None = None) -> float:
    """C: share of the total error energy carried by the k largest blocks (k = 1 % of blocks, at least 1)."""

    values = sorted((v * v for v in stats["errorRms"]), reverse=True)
    total = math.fsum(values)
    if total <= 0:
        return 0.0
    k = k or max(1, len(values) // 64)
    return math.fsum(values[:k]) / total


def relative_block_errors(stats: Mapping[str, Any], floor_fraction: float = REFERENCE_FLOOR_FRACTION) -> list[float]:
    """Each block's error normalised by the reference magnitude *of that block*.

    Blocks where the reference field itself is negligible (near a homogeneous Dirichlet
    boundary the solution vanishes) carry no information about relative accuracy and are
    *excluded* rather than floored: flooring them makes many blocks share one value, which
    collapses the robust dispersion to zero and turns the statistic degenerate.
    """

    floor = floor_fraction * stats["domainReferenceRms"]
    kept = [error / reference for error, reference in zip(stats["errorRms"], stats["referenceRms"]) if reference > floor]
    return kept or [error / max(reference, floor) for error, reference in zip(stats["errorRms"], stats["referenceRms"])]


def candidate_d_reference_conditioned_z(stats: Mapping[str, Any],
                                        floor_fraction: float = REFERENCE_FLOOR_FRACTION) -> float:
    """D: robust z-score of the *reference-conditioned* block error.

    Dividing by the block's own reference magnitude removes the heterogeneity every
    correct solution has (the error tracks the solution), so what is left is the part
    a hotspot actually produces.  The robust z-score then measures how far the worst
    block stands out from the bulk, in units of the bulk's own dispersion.
    """

    return _robust_z(relative_block_errors(stats, floor_fraction))


CANDIDATES: dict[str, Callable[[Mapping[str, Any]], float]] = {
    "A-maxOverMedian": candidate_a_max_over_median,
    "B-robustZ": candidate_b_robust_z,
    "C-topKConcentration": candidate_c_top_k_concentration,
    "D-referenceConditionedZ": candidate_d_reference_conditioned_z,
}


# ------------------------------------------------------------------ fixtures

def uniform_grid(n: int) -> list[tuple[float, float]]:
    """A deterministic interior grid of the unit square (no torch, no numpy)."""

    step = 1.0 / (n + 1)
    return [((i + 1) * step, (j + 1) * step) for i in range(n) for j in range(n)]


def pseudo_random_grid(count: int, seed: int = 20260916) -> list[tuple[float, float]]:
    """A deterministic pseudo-random interior point set (pure Python LCG).

    The signature is deployed on a *randomly sampled* dev set, where each block holds only
    a few dozen samples, so every block statistic carries estimation noise.  A null family
    evaluated only on dense deterministic grids has none of that noise and therefore
    understates the natural spread; the calibration must sample the same way the rule is
    used (Final Closure Audit issue 5, regime matching).
    """

    state = seed & 0xFFFFFFFF
    points: list[tuple[float, float]] = []

    def nxt() -> float:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return (state + 0.5) / 4294967296.0

    while len(points) < count:
        x, y = nxt(), nxt()
        if 0.0 < x < 1.0 and 0.0 < y < 1.0:
            points.append((x, y))
    return points


def oscillatory_component(points: Sequence[Sequence[float]], amplitude: float, modes: int = 9) -> list[float]:
    """A sign-oscillating high-frequency component: what a trained PINN's error field actually looks like.

    The residual of a converged PINN is not a smooth envelope; it oscillates on the scale of
    the collocation spacing and crosses zero repeatedly (visible as the contour lines in the
    2D error map).  Sampling such a field at a few dozen points per block is the dominant
    source of block-to-block spread in a *correct* solution.
    """

    return [amplitude * math.sin(modes * math.pi * x) * math.cos((modes + 2) * math.pi * y) for x, y in points]


def reference_field(points: Sequence[Sequence[float]]) -> list[float]:
    return [math.sin(math.pi * x) * math.sin(math.pi * y) for x, y in points]


def fixture_fields(points: Sequence[Sequence[float]], amplitude: float = 1e-5) -> dict[str, list[float]]:
    """The five preregistered calibration fixtures (issue 5.3), error fields on ``points``.

    * ``smoothUniform``          -- constant error, no structure at all;
    * ``heterogeneous``          -- error tracks the solution's own amplitude (the realistic correct case);
    * ``singleHotspot``          -- heterogeneous plus one narrow bump an order of magnitude above it;
    * ``multipleHotspots``       -- heterogeneous plus three such bumps;
    * ``globalIncrease``         -- the heterogeneous field scaled up ten times: worse everywhere, not localized.
    """

    exact = reference_field(points)
    heterogeneous = [amplitude * abs(value) for value in exact]

    def bump(centre: tuple[float, float], height: float, sigma: float = 0.04) -> list[float]:
        cx, cy = centre
        return [height * math.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * sigma * sigma))) for x, y in points]

    single = bump((0.31, 0.46), 10.0 * amplitude)
    triple = [a + b + c for a, b, c in zip(bump((0.31, 0.46), 10.0 * amplitude),
                                           bump((0.72, 0.19), 10.0 * amplitude),
                                           bump((0.55, 0.81), 10.0 * amplitude))]
    # A correct PINN error field is smooth-ish but genuinely uneven: its amplitude follows the
    # solution, it carries anisotropic modulation from the optimiser, and it has seed-scale
    # jitter. These two extra null fixtures are built from that description (first principles),
    # not from any observed value of the completed run.
    anisotropic = [amplitude * abs(value) ** 0.5 * (1.0 + 0.8 * math.sin(3 * math.pi * x) * math.cos(2 * math.pi * y))
                   for value, (x, y) in zip(exact, points)]
    jitter = [h * (1.0 + 0.5 * math.sin(97.0 * x + 61.0 * y) ** 2) for h, (x, y) in zip(heterogeneous, points)]
    # the realistic correct field: a smooth envelope times a sign-oscillating high-frequency component
    oscillatory = [e + o for e, o in zip(heterogeneous, oscillatory_component(points, 0.6 * amplitude))]
    return {
        "smoothUniform": [amplitude] * len(points),
        "heterogeneous": heterogeneous,
        "heterogeneousAnisotropic": anisotropic,
        "heterogeneousJitter": jitter,
        "heterogeneousOscillatory": oscillatory,
        "singleHotspot": [h + s for h, s in zip(heterogeneous, single)],
        "multipleHotspots": [h + s for h, s in zip(heterogeneous, triple)],
        "globalIncrease": [10.0 * h for h in heterogeneous],
    }


#: Which fixtures must fire the signature and which must not (ground truth by construction).
LOCALIZED_FIXTURES: tuple[str, ...] = ("singleHotspot", "multipleHotspots")
NON_LOCALIZED_FIXTURES: tuple[str, ...] = ("smoothUniform", "heterogeneous", "heterogeneousAnisotropic",
                                          "heterogeneousJitter", "heterogeneousOscillatory", "globalIncrease")


def evaluate_candidates(points: Sequence[Sequence[float]], blocks_per_axis: int,
                        amplitude: float = 1e-5) -> dict[str, dict[str, float]]:
    exact = reference_field(points)
    out: dict[str, dict[str, float]] = {}
    for name, errors in fixture_fields(points, amplitude).items():
        stats = block_statistics(points, errors, exact, blocks_per_axis)
        out[name] = {key: function(stats) for key, function in CANDIDATES.items()}
    return out


def separation(evaluated: Mapping[str, Mapping[str, float]], candidate: str) -> dict[str, float]:
    """How far the worst non-localized fixture is from the weakest localized one."""

    null_max = max(evaluated[name][candidate] for name in NON_LOCALIZED_FIXTURES)
    hot_min = min(evaluated[name][candidate] for name in LOCALIZED_FIXTURES)
    return {"nullMax": null_max, "hotspotMin": hot_min,
            "separationRatio": (hot_min / null_max) if null_max > 0 else math.inf}


def threshold_from_separation(null_max: float, hotspot_min: float) -> float:
    """The geometric mean of the two sides -- the scale-free midpoint, not a fitted value."""

    if not (null_max > 0 and hotspot_min > null_max):
        raise ValueError("the candidate does not separate the fixture families; it must not be used")
    return math.sqrt(null_max * hotspot_min)


def signature_fired(stats: Mapping[str, Any], *, candidate: str, threshold: float) -> bool:
    return CANDIDATES[candidate](stats) > threshold


# ------------------------------------------------ the deployed d >= 2 trigger
#
# External review ruling 2026-09-16, item 4. The calibration above answered the
# question it was given -- can a *statistic* of the block distribution separate a
# hotspot from ordinary 2D heterogeneity? -- and the honest answer was no, not from
# synthetic nulls alone (candidate D still misfires on 2/10 seeds of a validated
# run). The ruling does not ask for a fitted threshold. It replaces the trigger:
#
#     for d >= 2, sLocalizedError fires exactly when the localized-error acceptance
#     criterion preregistered for that problem in its ScientificSpec FAILS.
#
# For Poisson-2D that criterion is AC2D-9. This keeps a symptom that is already
# measured, already preregistered, already threshold-sourced and already known to
# behave correctly (worst seed 1.568e-4 against 1e-3), and it removes the only
# degree of freedom that could be tuned after seeing a result -- there is no second
# constant to choose. The candidate statistics above stay what they are: diagnostics
# and calibration research, never a gate.
#
# Nothing here changes a FailureSignature name, a RootCause class, a TrustStatus or
# a Claim semantics; the trigger of a symptom lives in the protocol and in each
# experiment's preregistered ``signatureCriteria``. Protocol clarification, not an
# amendment.

LOCALIZED_SIGNATURE = "sLocalizedError"

#: The only statistic the d >= 2 trigger accepts, and the name the acceptance
#: contract gives it. A different statistic is a different criterion and has to be
#: preregistered under its own contract entry.
LOCALIZED_STATISTIC = "maxTileRmsErrorOverReferenceRms"

#: The diagnosis never looks at D_claim (Constitution 10.1 / chapter 65): the claim
#: set is opened once, for acceptance, and adaptive tuning on it is what the whole
#: lifecycle exists to prevent.
LOCALIZED_EVALUATION_SETS: tuple[str, ...] = ("dev",)

#: Everything a preregistration must state. The criterion's *content* still comes
#: from the acceptance contract -- these fields are the run's declaration, and each
#: one is checked against the contract, so a mismatch is refused rather than
#: silently preferred (external review finding 3).
_LOCALIZED_REQUIRED_FIELDS: tuple[str, ...] = (
    "criterion", "statistic", "normalization", "partitionKind", "tilesPerAxis",
    "operator", "threshold", "evaluationSet", "preregisteredIn",
)

#: How a per-seed criterion outcome becomes an ensemble verdict. ``every-seed`` is
#: the policy Gate 5b already applies to every MUST criterion
#: (``gates2d.external_checks``: ``all(not failedMustCriteria)``), so one failing
#: seed is already an acceptance failure and must stay visible to the diagnosis.
#: No new proportion is invented here; `tests/pinn/test_localized_error_hardening.py`
#: ties this rule to the Gate's own behaviour for k = 0..N failing seeds.
_SEED_POLICIES: tuple[str, ...] = ("every-seed",)


def _number(value: Any, label: str, *, non_negative: bool = False) -> float:
    """A finite float, or an error -- never a silently propagated NaN / infinity."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationInputError(f"{label} must be a real number, got {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationInputError(
            f"{label} is {number}: invalid evidence is not evidence of no localized failure"
        )
    if non_negative and number < 0.0:
        raise ValidationInputError(f"{label} must be non-negative, got {number}")
    return number


def validate_evidence_fields(points: Sequence[Sequence[float]], errors: Sequence[float],
                             reference: Sequence[float], blocks_per_axis: int
                             ) -> tuple[list[tuple[float, ...]], list[float], list[float], int]:
    """Check the three arrays *before* anything zips them together.

    ``zip`` stops at the shortest input, so a shorter coordinate array silently
    discards the tail of the error field -- a hotspot in the discarded tail simply
    disappears (external review finding 2.2). Lengths are therefore asserted here,
    with no truncation, padding or ignoring, together with finiteness, the point
    dimension and the block count.
    """

    if not isinstance(blocks_per_axis, int) or isinstance(blocks_per_axis, bool) or blocks_per_axis < 1:
        raise ValidationInputError(f"blocksPerAxis must be an integer >= 1, got {blocks_per_axis!r}")
    lengths = {"points": len(points), "errors": len(errors), "reference": len(reference)}
    if len(set(lengths.values())) != 1:
        raise ValidationInputError(
            f"localized-error evidence arrays must have equal length, got {lengths}: "
            "a shorter array would silently truncate the rest of the field"
        )
    if lengths["points"] == 0:
        raise ValidationInputError("localized-error evidence is empty; there is nothing to judge")

    dimension = len(points[0])
    if dimension < 2:
        raise ValidationInputError(f"localized-error evidence needs points of dimension >= 2, got {dimension}")
    checked_points: list[tuple[float, ...]] = []
    for index, point in enumerate(points):
        if len(point) != dimension:
            raise ValidationInputError(
                f"points[{index}] has dimension {len(point)}, expected {dimension}: the point set is not homogeneous")
        coordinates = tuple(_number(value, f"points[{index}][{axis}]") for axis, value in enumerate(point))
        for axis, value in enumerate(coordinates):
            if not 0.0 <= value <= 1.0:
                raise ValidationInputError(
                    f"points[{index}][{axis}] = {value} is outside the unit domain; block assignment would clamp it")
        checked_points.append(coordinates)
    checked_errors = [_number(value, f"errors[{index}]") for index, value in enumerate(errors)]
    checked_reference = [_number(value, f"reference[{index}]") for index, value in enumerate(reference)]
    return checked_points, checked_errors, checked_reference, blocks_per_axis


def localized_acceptance_ratio(points: Sequence[Sequence[float]], errors: Sequence[float],
                               reference: Sequence[float], tiles_per_axis: int) -> float:
    """The AC2D-9 quantity: worst tile RMS error divided by the RMS of the reference solution.

    Numerator and denominator are exactly the ones ``pinn.validation.poisson2d`` uses on
    the claim grid (the denominator is the *reference* field, not the error field), so the
    dev-side symptom and the acceptance criterion are the same measurement on different
    point sets. Invalid evidence raises; it never returns a small, innocent-looking number.
    """

    points, errors, reference, tiles_per_axis = validate_evidence_fields(points, errors, reference, tiles_per_axis)
    stats = block_statistics(points, errors, reference, tiles_per_axis)
    domain_reference = stats["domainReferenceRms"]
    if not domain_reference > 0:
        raise ValidationInputError(
            "the reference field vanishes on this set; the relative criterion is undefined")
    return max(stats["errorRms"]) / domain_reference


def _contract_for(criterion_id: str, contract_resolver: Callable[[str], Mapping[str, Any]] | None
                  ) -> Mapping[str, Any]:
    if contract_resolver is None:
        from pinn.governance import poisson2d_contract

        contract_resolver = poisson2d_contract.localized_criterion
    return contract_resolver(criterion_id)


def preregistered_localized_criterion(criteria: Mapping[str, Any], *, dimension: int,
                                      contract_resolver: Callable[[str], Mapping[str, Any]] | None = None
                                      ) -> dict[str, Any]:
    """The localized-error acceptance criterion this experiment registered, or an error.

    Fail-closed on purpose: for d >= 2 a run whose ``signatureCriteria`` carry no
    localized acceptance criterion has no localized-error symptom at all, and that is a
    preregistration defect to be fixed before the run, not a detail to be filled in after
    one. Every declared field is then checked against the contract entry the criterion id
    resolves to -- statistic, normalization, partition, tiles, operator and threshold --
    so a localized measurement cannot be judged against a different criterion's bound.
    """

    entry = dict(criteria.get(LOCALIZED_SIGNATURE) or {})
    if dimension < 2:
        return {"dimension": dimension, "kind": "symptom-statistic", "statistic": "maxBinToMedianBinRatio",
                "threshold": entry.get("maxBinToMedianBinRatio"),
                "note": "the inherited 1D rule; retired for d >= 2 (machine-verified false positives)"}

    missing = [field for field in _LOCALIZED_REQUIRED_FIELDS if entry.get(field) in (None, "")]
    if missing:
        raise ValidationInputError(
            f"no preregistered localized-error acceptance criterion for d = {dimension}: missing {missing}. "
            "For d >= 2 the localized-error requirement is carried by an acceptance criterion of the AC2D-9 form, "
            "which must be registered in signatureCriteria before the formal run (external review ruling 2026-09-16)."
        )
    contract = _contract_for(str(entry["criterion"]), contract_resolver)
    for declared, contracted in (("statistic", "statisticId"), ("normalization", "normalization"),
                                 ("partitionKind", "partitionKind"), ("operator", "operator")):
        if entry[declared] != contract[contracted]:
            raise ValidationInputError(
                f"the preregistered {declared} {entry[declared]!r} does not match criterion "
                f"{contract['criterionId']}'s {contracted} {contract[contracted]!r}"
            )
    if entry["statistic"] != LOCALIZED_STATISTIC:
        raise ValidationInputError(
            f"the localized criterion must use the {LOCALIZED_STATISTIC} statistic, not {entry['statistic']!r}")
    if int(entry["tilesPerAxis"]) != int(contract["tilesPerAxis"]):
        raise ValidationInputError(
            f"the preregistered partition {entry['tilesPerAxis']}x{entry['tilesPerAxis']} does not match criterion "
            f"{contract['criterionId']}'s {contract['tilesPerAxis']}x{contract['tilesPerAxis']} tiles")
    if float(entry["threshold"]) != float(contract["threshold"]):
        raise ValidationInputError(
            f"the localized symptom threshold {entry['threshold']} does not equal the acceptance threshold "
            f"{contract['threshold']} of {contract['criterionId']}: the symptom may not carry a bound of its own")
    if entry["evaluationSet"] not in LOCALIZED_EVALUATION_SETS:
        raise ValidationInputError(
            f"the localized-error diagnosis may only read {LOCALIZED_EVALUATION_SETS}, not {entry['evaluationSet']!r}: "
            "D_claim is opened once for acceptance and is never used for diagnosis or adaptive tuning")
    seed_policy = str(contract["seedPolicy"])
    if seed_policy not in _SEED_POLICIES:
        raise ValidationInputError(f"unknown seed policy {seed_policy!r} for {contract['criterionId']}")
    return {"dimension": dimension, "kind": "acceptance-criterion", **entry,
            "criterionId": contract["criterionId"], "statisticId": contract["statisticId"],
            "normalization": contract["normalization"], "partitionKind": contract["partitionKind"],
            "operator": contract["operator"], "level": contract["level"], "seedPolicy": seed_policy,
            "definition": contract["definition"]}


def criterion_failed(value: float, threshold: float, operator: str) -> bool:
    """Whether one seed's statistic fails the criterion, under the contract's operator."""

    if operator == "<=":
        return value > threshold
    if operator == "<":
        return value >= threshold
    raise ValidationInputError(f"unsupported comparison operator {operator!r}")


def _ensemble_fired(failure_count: int, seed_count: int, seed_policy: str) -> bool:
    if seed_policy == "every-seed":
        # Gate 5b requires every seed to satisfy every MUST criterion, so a single
        # failing seed is already an acceptance failure of this criterion.
        return failure_count >= 1
    raise ValidationInputError(f"unknown seed policy {seed_policy!r}")


def localized_signature(per_seed: Sequence[Mapping[str, Any]], criteria: Mapping[str, Any], *, dimension: int,
                        contract_resolver: Callable[[str], Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """The ``sLocalizedError`` rule entry for d >= 2, with the per-seed evidence kept.

    The result is the full picture, not a boolean: which seeds failed, how many, what
    fraction, the ensemble statistics, and the verdict under the criterion's own seed
    policy. Aggregation may summarise the evidence; it may not delete it (external review
    finding 1).
    """

    criterion = preregistered_localized_criterion(criteria, dimension=dimension, contract_resolver=contract_resolver)
    if criterion["kind"] != "acceptance-criterion":
        raise ValidationInputError("localized_signature is the d >= 2 rule; 1D keeps its own inherited statistic")
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
    fired = _ensemble_fired(len(failing), len(values), seed_policy)
    worst = max(values)
    median = _median(values)
    return {
        # the decisive statistic under this seed policy, so value/threshold and fired agree
        "value": worst, "threshold": threshold, "fired": bool(fired),
        "rule": (f"the preregistered localized acceptance criterion {criterion['criterionId']} "
                 f"({LOCALIZED_STATISTIC} {operator} {threshold:g}, {criterion['tilesPerAxis']}x"
                 f"{criterion['tilesPerAxis']} tiles, normalized by {criterion['normalization']}) evaluated on "
                 f"D_{criterion['evaluationSet']}, aggregated by the '{seed_policy}' policy Gate 5b applies to "
                 f"{criterion['level']} criteria"),
        "criterion": criterion["criterionId"], "criterionId": criterion["criterionId"],
        "statistic": LOCALIZED_STATISTIC, "statisticId": criterion["statisticId"],
        "normalization": criterion["normalization"], "partitionKind": criterion["partitionKind"],
        "tilesPerAxis": criterion["tilesPerAxis"], "operator": operator, "level": criterion["level"],
        "evaluationSet": criterion["evaluationSet"], "preregisteredIn": criterion["preregisteredIn"],
        "seedPolicy": seed_policy,
        "perSeedValues": values, "failingSeedIndices": failing, "failureCount": len(failing),
        "failureFraction": len(failing) / len(values), "seedCount": len(values),
        "ensembleStatistic": {"median": median, "worst": worst, "best": min(values)},
        "firedBy": (f"{len(failing)}/{len(values)} seed(s) fail {criterion['criterionId']}" if fired
                    else f"no seed fails {criterion['criterionId']}"),
        # kept for continuity of the record; the median is NOT the decision rule, because
        # a minority of failing seeds leaves it below the threshold (reviewer probe:
        # 1/10 and 4/10 failing seeds both left the old median-based rule silent).
        "medianStatistic": median,
    }


def apply_localized_signature(observed: Mapping[str, Any], per_seed: Sequence[Mapping[str, Any]],
                              criteria: Mapping[str, Any], *, dimension: int,
                              contract_resolver: Callable[[str], Mapping[str, Any]] | None = None
                              ) -> dict[str, Any]:
    """Replace the inherited 1D symptom rule with the preregistered d >= 2 trigger.

    The retired statistic is kept beside it as a diagnostic so the record still shows what
    the old rule would have said -- it is reported, never acted on.
    """

    if dimension < 2:
        return dict(observed)
    rule = localized_signature(per_seed, criteria, dimension=dimension, contract_resolver=contract_resolver)
    retired = [_number(record["localizedRatio"], f"seed {index} localizedRatio")
               for index, record in enumerate(per_seed) if "localizedRatio" in record
               and math.isfinite(float(record["localizedRatio"]))]
    if retired:
        rule["retiredStatistic"] = {
            "maxOverMedianRatioMedian": _median(retired), "retiredThreshold": 3.0,
            "note": ("the inherited 1D statistic, reported for continuity only: it is NOT CALIBRATED for d >= 2 "
                     "(it fires on 9/10 seeds of a validated 2D run) and takes no part in this decision"),
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
        "tilesPerAxis": rule["tilesPerAxis"], "operator": rule["operator"], "threshold": rule["threshold"],
        "evaluationSet": rule["evaluationSet"], "preregisteredIn": rule["preregisteredIn"],
        "seedPolicy": rule["seedPolicy"], "perSeedValues": rule["perSeedValues"],
        "failingSeedIndices": rule["failingSeedIndices"], "failureCount": rule["failureCount"],
        "failureFraction": rule["failureFraction"], "ensembleStatistic": rule["ensembleStatistic"],
        "fired": rule["fired"], "firedBy": rule["firedBy"],
        "ruling": ("external review ruling 2026-09-16 item 4, hardened by the 2026-09-16 trigger review: for d >= 2 "
                   "the symptom fires exactly when the preregistered localized-error acceptance criterion fails, "
                   "under the same seed policy Gate 5b applies to that criterion's level; max/median, robust z and "
                   "top-k concentration remain diagnostics and calibration research, not a gate"),
    }
    return out


def assert_criterion_within_run_identity(config_path: str | Any, code_manifest: Sequence[Mapping[str, str]]) -> str:
    """Refuse a localized criterion that was added after the run it would judge.

    The frozen configuration is part of the run's code identity, so the criterion a run
    was judged under is exactly the one in the config whose SHA-256 the run recorded.
    Adding a criterion now and pointing it at a completed run changes those bytes, and
    this raises instead of letting the new trigger reach back in time.
    """

    import hashlib
    import pathlib

    path = pathlib.Path(config_path)
    relative = path.as_posix().replace("\\", "/")
    entry = next((item for item in code_manifest if relative.endswith(item["path"])), None)
    if entry is None:
        raise ValidationInputError(
            f"{relative} is not part of the recorded code identity; it cannot carry a preregistered criterion")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise ValidationInputError(
            f"{entry['path']} has changed since the run was recorded ({digest[:12]} != {entry['sha256'][:12]}): a "
            "localized-error criterion introduced after a run may not be used to trigger a signature on it"
        )
    return digest
