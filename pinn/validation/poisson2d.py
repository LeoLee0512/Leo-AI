"""AC2D-1..AC2D-9 arithmetic for the Poisson-2D candidate, isolated from any model.

The API accepts raw field samples (values and separately evaluated first and
second derivatives) on the grids the ProblemDefinition names; it has no
optimizer, no checkpoint loader and no Gate transition.  Invalid evidence is
rejected (``ValidationInputError``) instead of being coerced into a finite
number.  The control fixtures at the bottom are the T10 evidence that this
validator accepts the analytic solution and rejects corrupted fields.

Grids (all supplied by the caller, all frozen in the ProblemDefinition):

* quadrature: tensor Gauss-Legendre nodes with product weights summing to 1;
* pointwise:  tensor Chebyshev-Gauss-Lobatto interior nodes (no boundary line);
* boundary:   Gauss-Legendre nodes along the four edges with arc-length weights
  summing to the perimeter 4, plus the outward normal derivative at each node.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from pinn.governance.poisson2d_contract import CRITERIA, METRICS, THRESHOLD_SOURCES, TILES_PER_AXIS
from pinn.reference import analytic_poisson2d as reference

EPSILON = 1e-30
THRESHOLDS = {cid: limit for cid, limit, _ in CRITERIA}
LEVELS = {cid: level for cid, _, level in CRITERIA}
MUST_IDS = tuple(cid for cid, _, level in CRITERIA if level == "MUST")
SHOULD_IDS = tuple(cid for cid, _, level in CRITERIA if level == "SHOULD")


class ValidationInputError(ValueError):
    """Invalid evidence must never be coerced into a finite, accepted result."""


def _float64(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, float):
        raise ValidationInputError(f"{label} must be a float64 scalar")
    if not math.isfinite(value):
        raise ValidationInputError(f"{label} must be finite")
    return float(value)


def _vector(values: Sequence[float], size: int, label: str) -> tuple[float, ...]:
    if len(values) != size:
        raise ValidationInputError(f"{label} must have {size} entries, got {len(values)}")
    return tuple(_float64(v, f"{label}[{i}]") for i, v in enumerate(values))


def _points(points: Sequence[Sequence[float]], label: str) -> tuple[tuple[float, float], ...]:
    out: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        if len(point) != 2:
            raise ValidationInputError(f"{label}[{index}] must be a 2-dimensional coordinate")
        out.append((_float64(float(point[0]), f"{label}[{index}].x"), _float64(float(point[1]), f"{label}[{index}].y")))
    return tuple(out)


@dataclass(frozen=True)
class Fields2D:
    """Everything the acceptance criteria read, evaluated by the caller."""

    quadrature_points: Sequence[Sequence[float]]
    quadrature_weights: Sequence[float]
    u_quadrature: Sequence[float]
    ux_quadrature: Sequence[float]
    uy_quadrature: Sequence[float]
    uxx_quadrature: Sequence[float]
    uyy_quadrature: Sequence[float]
    pointwise_points: Sequence[Sequence[float]]
    u_pointwise: Sequence[float]
    boundary_points: Sequence[Sequence[float]]
    boundary_weights: Sequence[float]
    u_boundary: Sequence[float]
    dn_boundary: Sequence[float]
    derivative_method: str = "AUTOGRAD_FIRST_AND_SECOND_ORDER"
    device: str = "cpu"


def _tile_index(value: float) -> int:
    index = int(value * TILES_PER_AXIS)
    return min(max(index, 0), TILES_PER_AXIS - 1)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def evaluate_fields(fields: Fields2D, *, grid_label: str) -> dict[str, Any]:
    """AC2D values, thresholds and verdicts for one model's fields."""

    q = _points(fields.quadrature_points, "quadrature_points")
    n_q = len(q)
    if n_q == 0:
        raise ValidationInputError("the quadrature grid is empty")
    w = _vector(fields.quadrature_weights, n_q, "quadrature_weights")
    if abs(math.fsum(w) - 1.0) > 1e-12:
        raise ValidationInputError("quadrature weights must sum to one on the unit square")
    if any(weight <= 0.0 for weight in w):
        raise ValidationInputError("quadrature weights must be positive")
    u_q = _vector(fields.u_quadrature, n_q, "u_quadrature")
    ux_q = _vector(fields.ux_quadrature, n_q, "ux_quadrature")
    uy_q = _vector(fields.uy_quadrature, n_q, "uy_quadrature")
    uxx_q = _vector(fields.uxx_quadrature, n_q, "uxx_quadrature")
    uyy_q = _vector(fields.uyy_quadrature, n_q, "uyy_quadrature")
    p = _points(fields.pointwise_points, "pointwise_points")
    n_p = len(p)
    if n_p == 0:
        raise ValidationInputError("the pointwise grid is empty")
    u_p = _vector(fields.u_pointwise, n_p, "u_pointwise")
    b = _points(fields.boundary_points, "boundary_points")
    n_b = len(b)
    if n_b == 0:
        raise ValidationInputError("the boundary set is empty")
    bw = _vector(fields.boundary_weights, n_b, "boundary_weights")
    if abs(math.fsum(bw) - 4.0) > 1e-12:
        raise ValidationInputError("boundary weights must sum to the perimeter 4")
    u_b = _vector(fields.u_boundary, n_b, "u_boundary")
    dn_b = _vector(fields.dn_boundary, n_b, "dn_boundary")
    for point in b:
        if not (point[0] in (0.0, 1.0) or point[1] in (0.0, 1.0)):
            raise ValidationInputError("a boundary node is not on an edge of the unit square")

    integral = lambda values: math.fsum(weight * value for weight, value in zip(w, values))
    exact_q = [reference.solution(x, y) for x, y in q]
    exact_ux = [reference.dx(x, y) for x, y in q]
    exact_uy = [reference.dy(x, y) for x, y in q]
    exact_f = [reference.forcing(x, y) for x, y in q]
    exact_p = [reference.solution(x, y) for x, y in p]
    exact_dn = [reference.normal_derivative(x, y) for x, y in b]

    l2_squared = integral((a - e) ** 2 for a, e in zip(u_q, exact_q))
    reference_l2_squared = integral(e * e for e in exact_q)
    grad_l2_squared = integral((a - e) ** 2 + (c - g) ** 2 for a, e, c, g in zip(ux_q, exact_ux, uy_q, exact_uy))
    reference_grad_squared = integral(e * e + g * g for e, g in zip(exact_ux, exact_uy))
    residuals = [-(xx + yy) - f for xx, yy, f in zip(uxx_q, uyy_q, exact_f)]
    residual_rms = math.sqrt(integral(r * r for r in residuals))
    integral_u = integral(u_q)
    dirichlet_energy = integral(a * a + c * c for a, c in zip(ux_q, uy_q))
    forcing_energy = integral(f * value for f, value in zip(exact_f, u_q))
    pointwise_errors = [abs(a - e) for a, e in zip(u_p, exact_p)]
    max_exact_p = max(abs(e) for e in exact_p)
    if max_exact_p <= 1e6 * EPSILON:
        raise ValidationInputError("the pointwise reference field is degenerate")
    if reference_l2_squared <= 1e6 * EPSILON:
        raise ValidationInputError("the quadrature reference field is degenerate")

    tiles: dict[tuple[int, int], list[float]] = {}
    for (x, y), error in zip(p, pointwise_errors):
        tiles.setdefault((_tile_index(x), _tile_index(y)), []).append(error * error)
    if len(tiles) < TILES_PER_AXIS * TILES_PER_AXIS:
        raise ValidationInputError("the pointwise grid does not cover every tile of the localized-error partition")
    reference_rms_p = math.sqrt(math.fsum(e * e for e in exact_p) / n_p)
    tile_rms = {key: math.sqrt(math.fsum(values) / len(values)) for key, values in tiles.items()}
    worst_tile = max(tile_rms, key=lambda key: tile_rms[key])
    tile_values = list(tile_rms.values())
    median_tile = _median(tile_values)
    hotspot_index = max(range(n_p), key=lambda i: pointwise_errors[i])

    values = {
        "AC2D-1": math.sqrt(l2_squared / (reference_l2_squared + EPSILON)),
        "AC2D-2": max(pointwise_errors) / (max_exact_p + EPSILON),
        "AC2D-3": max(abs(value) for value in u_b),
        "AC2D-4": residual_rms / reference.F_RMS,
        "AC2D-5": abs(integral_u - reference.INTEGRAL_U) / reference.INTEGRAL_U,
        "AC2D-6": max(abs(a - e) for a, e in zip(dn_b, exact_dn)) / reference.PI,
        "AC2D-7": abs(dirichlet_energy - forcing_energy) / reference.DIRICHLET_ENERGY,
        "AC2D-9": tile_rms[worst_tile] / reference_rms_p,
        "AC2D-8": math.sqrt(grad_l2_squared / (reference_grad_squared + EPSILON)),
    }
    for key, value in values.items():
        if not math.isfinite(value) or value < 0.0:
            raise ValidationInputError(f"{key} produced a non-finite metric")
    satisfied = {key: value < THRESHOLDS[key] for key, value in values.items()}
    metrics = {
        key: {"value": value, "threshold": THRESHOLDS[key], "comparator": "<", "level": LEVELS[key],
              "formula": METRICS[key][0], "grid": METRICS[key][1], "criterionSatisfied": satisfied[key],
              "dimensionVerdict": THRESHOLD_SOURCES[key]["dimensionVerdict"]}
        for key, value in values.items()
    }
    flux = math.fsum(weight * value for weight, value in zip(bw, dn_b))
    return {
        "evaluationScope": "CLAIM_GRID_EVALUATION_2D",
        "grid": grid_label,
        "quadratureCount": n_q,
        "pointwiseCount": n_p,
        "boundaryCount": n_b,
        "componentCriteriaSatisfied": all(satisfied[key] for key in MUST_IDS),
        "failedMustCriteria": [key for key in MUST_IDS if not satisfied[key]],
        "failedShouldCriteria": [key for key in SHOULD_IDS if not satisfied[key]],
        "metrics": metrics,
        "diagnostics": {
            "absoluteL2": math.sqrt(l2_squared),
            "absoluteLinf": max(pointwise_errors),
            "pdeResidualRms": residual_rms,
            "pdeResidualMax": max(abs(r) for r in residuals),
            "integralU": integral_u,
            "dirichletEnergy": dirichlet_energy,
            "forcingEnergy": forcing_energy,
            "boundaryFlux": flux,
            "fluxIdentityDefect": abs(flux + reference.INTEGRAL_F) / reference.INTEGRAL_F,
            "maxBoundaryAbsU": max(abs(value) for value in u_b),
            "worstTile": {"ix": worst_tile[0], "iy": worst_tile[1], "rms": tile_rms[worst_tile],
                          "xRange": [worst_tile[0] / TILES_PER_AXIS, (worst_tile[0] + 1) / TILES_PER_AXIS],
                          "yRange": [worst_tile[1] / TILES_PER_AXIS, (worst_tile[1] + 1) / TILES_PER_AXIS]},
            "tileRatioMaxOverMedian": (tile_rms[worst_tile] / median_tile) if median_tile > 0 else float("inf"),
            "hotspot": {"x": p[hotspot_index][0], "y": p[hotspot_index][1], "absError": pointwise_errors[hotspot_index]},
            "referenceRmsPointwise": reference_rms_p,
        },
    }


# ------------------------------------------------------------------ control fixtures (T10)

@dataclass(frozen=True)
class Fixture2D:
    """u(x, y) = offset + sum_k a_k sin(kx pi x) sin(ky pi y), with an optional reported-derivative defect."""

    fixture_id: str
    modes: tuple[tuple[int, int, float], ...] = ((1, 1, 1.0),)
    offset: float = 0.0
    second_derivative_factor: float = 1.0

    def u(self, x: float, y: float) -> float:
        return self.offset + math.fsum(a * math.sin(kx * math.pi * x) * math.sin(ky * math.pi * y) for kx, ky, a in self.modes)

    def ux(self, x: float, y: float) -> float:
        return math.fsum(a * kx * math.pi * math.cos(kx * math.pi * x) * math.sin(ky * math.pi * y) for kx, ky, a in self.modes)

    def uy(self, x: float, y: float) -> float:
        return math.fsum(a * ky * math.pi * math.sin(kx * math.pi * x) * math.cos(ky * math.pi * y) for kx, ky, a in self.modes)

    def uxx(self, x: float, y: float) -> float:
        return self.second_derivative_factor * math.fsum(
            -a * (kx * math.pi) ** 2 * math.sin(kx * math.pi * x) * math.sin(ky * math.pi * y) for kx, ky, a in self.modes)

    def uyy(self, x: float, y: float) -> float:
        return self.second_derivative_factor * math.fsum(
            -a * (ky * math.pi) ** 2 * math.sin(kx * math.pi * x) * math.sin(ky * math.pi * y) for kx, ky, a in self.modes)

    def dn(self, x: float, y: float) -> float:
        if x == 0.0:
            return -self.ux(0.0, y)
        if x == 1.0:
            return self.ux(1.0, y)
        if y == 0.0:
            return -self.uy(x, 0.0)
        if y == 1.0:
            return self.uy(x, 1.0)
        raise ValueError("dn is defined on the boundary only")


FIXTURES: tuple[Fixture2D, ...] = (
    Fixture2D("ANALYTIC_CONTROL"),
    Fixture2D("B1b_SIGN_FLIP", modes=((1, 1, -1.0),)),
    Fixture2D("B3_OFFSET", offset=0.3),
    Fixture2D("B4_SMALL_HIGH_MODE", modes=((1, 1, 1.0), (4, 4, 0.002))),
    Fixture2D("B6_LARGE_MODE", modes=((1, 1, 1.0), (5, 1, 0.2))),
    Fixture2D("ZERO_FIELD_CONTROL", modes=((1, 1, 0.0),)),
    Fixture2D("DERIVATIVE_INCONSISTENCY", second_derivative_factor=0.5),
)


def sample_fixture(fixture: Fixture2D, *, quadrature_points: Sequence[Sequence[float]], quadrature_weights: Sequence[float],
                   pointwise_points: Sequence[Sequence[float]], boundary_points: Sequence[Sequence[float]],
                   boundary_weights: Sequence[float]) -> Fields2D:
    return Fields2D(
        quadrature_points=list(quadrature_points), quadrature_weights=list(quadrature_weights),
        u_quadrature=[fixture.u(x, y) for x, y in quadrature_points],
        ux_quadrature=[fixture.ux(x, y) for x, y in quadrature_points],
        uy_quadrature=[fixture.uy(x, y) for x, y in quadrature_points],
        uxx_quadrature=[fixture.uxx(x, y) for x, y in quadrature_points],
        uyy_quadrature=[fixture.uyy(x, y) for x, y in quadrature_points],
        pointwise_points=list(pointwise_points), u_pointwise=[fixture.u(x, y) for x, y in pointwise_points],
        boundary_points=list(boundary_points), boundary_weights=list(boundary_weights),
        u_boundary=[fixture.u(x, y) for x, y in boundary_points],
        dn_boundary=[fixture.dn(x, y) for x, y in boundary_points],
        derivative_method="ANALYTIC_FIXTURE", device="cpu",
    )


def fixture_verdicts(*, quadrature_points: Sequence[Sequence[float]], quadrature_weights: Sequence[float],
                     pointwise_points: Sequence[Sequence[float]], boundary_points: Sequence[Sequence[float]],
                     boundary_weights: Sequence[float]) -> dict[str, Any]:
    """T10: the validator must accept ANALYTIC_CONTROL and reject every corrupted fixture."""

    verdicts: dict[str, Any] = {}
    for fixture in FIXTURES:
        try:
            samples = sample_fixture(fixture, quadrature_points=quadrature_points, quadrature_weights=quadrature_weights,
                                     pointwise_points=pointwise_points, boundary_points=boundary_points, boundary_weights=boundary_weights)
            verdicts[fixture.fixture_id] = bool(evaluate_fields(samples, grid_label="T10-fixture")["componentCriteriaSatisfied"])
        except Exception:                      # a rejected input is a rejection
            verdicts[fixture.fixture_id] = False
    return verdicts
