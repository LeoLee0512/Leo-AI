"""ACA-1..ACA-9 arithmetic for the annular Poisson candidate, isolated from any model.

The validator is handed *numbers* -- fields already evaluated by the caller -- and
never touches a network, an optimiser or autograd. What it adds for Geometry Lift 1
is that it also refuses evidence that is geometrically wrong before it computes
anything:

  * a quadrature or pointwise node in the hole, outside the disk, or on a circle;
  * boundary nodes that are not on the component they claim to be on;
  * quadrature weights that do not integrate the annulus area, or boundary weights
    that do not integrate that component's circumference;
  * a boundary component whose nodes were handed over with the other component's
    normals (the flux terms are reported per component so a sign swap cannot hide
    inside a sum).

Invalid evidence raises ``ValidationInputError``; it is never coerced into a finite,
accepted number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pinn.geometry import annulus as geo
from pinn.governance.annulus_contract import (
    ANGULAR_SECTORS,
    CRITERIA,
    LOCALIZED_ERROR_CRITERION,
    RADIAL_BINS,
)
from pinn.reference import analytic_annulus as reference
from pinn.validation.poisson2d import ValidationInputError

EPSILON = 1e-30
THRESHOLDS = {cid: limit for cid, limit, _ in CRITERIA}
LEVELS = {cid: level for cid, _, level in CRITERIA}
MUST_IDS = tuple(cid for cid, _, level in CRITERIA if level == "MUST")
SHOULD_IDS = tuple(cid for cid, _, level in CRITERIA if level == "SHOULD")

#: How closely a node must sit on its circle, and how closely the quadrature must
#: integrate the domain it claims to cover.
BOUNDARY_TOLERANCE = 1e-12
QUADRATURE_TOLERANCE = 1e-9


def _float64(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationInputError(f"{label} must be a real scalar")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationInputError(f"{label} must be finite, got {number}")
    return number


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


def _require_interior(points: Sequence[Sequence[float]], label: str) -> None:
    for index, point in enumerate(points):
        kind = geo.classify(point)
        if kind != geo.INTERIOR:
            raise ValidationInputError(
                f"{label}[{index}] = {tuple(point)} is {kind}, not strictly inside the annulus "
                f"(a^2 < x^2 + y^2 < 1): evidence off the domain is not evidence")


@dataclass(frozen=True)
class FieldsAnnulus:
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
    boundary: Mapping[str, Mapping[str, Sequence[Any]]]
    derivative_method: str = "AUTOGRAD_FIRST_AND_SECOND_ORDER"
    device: str = "cpu"


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def _boundary_component(boundary: Mapping[str, Mapping[str, Sequence[Any]]], component: str) -> dict[str, Any]:
    if component not in boundary:
        raise ValidationInputError(f"the boundary evidence has no '{component}' component")
    block = boundary[component]
    points = _points(block["points"], f"{component}.points")
    n = len(points)
    if n == 0:
        raise ValidationInputError(f"the {component} boundary set is empty")
    weights = _vector(block["weights"], n, f"{component}.weights")
    u = _vector(block["u"], n, f"{component}.u")
    dn = _vector(block["dn"], n, f"{component}.dn")
    radius = geo.boundary_radius(component)
    for index, point in enumerate(points):
        if abs(geo.radius(point) - radius) > BOUNDARY_TOLERANCE:
            raise ValidationInputError(
                f"{component} boundary node {index} is at radius {geo.radius(point)}, expected {radius}: "
                "a node handed to the wrong component would be measured with the wrong outward normal")
    circumference = 2.0 * math.pi * radius
    if abs(math.fsum(weights) - circumference) > QUADRATURE_TOLERANCE:
        raise ValidationInputError(
            f"{component} boundary weights sum to {math.fsum(weights)}, expected the circumference {circumference}")
    if any(weight <= 0.0 for weight in weights):
        raise ValidationInputError(f"{component} boundary weights must be positive")
    return {"points": points, "weights": weights, "u": u, "dn": dn, "radius": radius}


def evaluate_fields(fields: FieldsAnnulus, *, grid_label: str) -> dict[str, Any]:
    """ACA values, thresholds and verdicts for one model's fields on the annulus."""

    q = _points(fields.quadrature_points, "quadrature_points")
    n_q = len(q)
    if n_q == 0:
        raise ValidationInputError("the quadrature grid is empty")
    _require_interior(q, "quadrature_points")
    w = _vector(fields.quadrature_weights, n_q, "quadrature_weights")
    if any(weight <= 0.0 for weight in w):
        raise ValidationInputError("quadrature weights must be positive")
    if abs(math.fsum(w) - reference.AREA) > QUADRATURE_TOLERANCE:
        raise ValidationInputError(
            f"quadrature weights sum to {math.fsum(w)}, expected the annulus area {reference.AREA}")
    u_q = _vector(fields.u_quadrature, n_q, "u_quadrature")
    ux_q = _vector(fields.ux_quadrature, n_q, "ux_quadrature")
    uy_q = _vector(fields.uy_quadrature, n_q, "uy_quadrature")
    uxx_q = _vector(fields.uxx_quadrature, n_q, "uxx_quadrature")
    uyy_q = _vector(fields.uyy_quadrature, n_q, "uyy_quadrature")

    p = _points(fields.pointwise_points, "pointwise_points")
    n_p = len(p)
    if n_p == 0:
        raise ValidationInputError("the pointwise grid is empty")
    _require_interior(p, "pointwise_points")
    u_p = _vector(fields.u_pointwise, n_p, "u_pointwise")

    outer = _boundary_component(fields.boundary, geo.OUTER)
    inner = _boundary_component(fields.boundary, geo.INNER)

    integral = lambda values: math.fsum(weight * value for weight, value in zip(w, values))
    exact_q = [reference.solution(x, y) for x, y in q]
    exact_ux = [reference.gradient(x, y)[0] for x, y in q]
    exact_uy = [reference.gradient(x, y)[1] for x, y in q]
    exact_f = [reference.forcing(x, y) for x, y in q]
    exact_p = [reference.solution(x, y) for x, y in p]

    l2_squared = integral((a - e) ** 2 for a, e in zip(u_q, exact_q))
    reference_l2_squared = integral(e * e for e in exact_q)
    if reference_l2_squared <= 1e6 * EPSILON:
        raise ValidationInputError("the quadrature reference field is degenerate")
    grad_l2_squared = integral((a - e) ** 2 + (c - g) ** 2 for a, e, c, g in zip(ux_q, exact_ux, uy_q, exact_uy))
    reference_grad_squared = integral(e * e + g * g for e, g in zip(exact_ux, exact_uy))
    residuals = [-(xx + yy) - f for xx, yy, f in zip(uxx_q, uyy_q, exact_f)]
    residual_rms = math.sqrt(integral(r * r for r in residuals) / reference.AREA)
    integral_u = integral(u_q)
    dirichlet_energy = integral(a * a + c * c for a, c in zip(ux_q, uy_q))
    forcing_energy = integral(f * value for f, value in zip(exact_f, u_q))

    pointwise_errors = [abs(a - e) for a, e in zip(u_p, exact_p)]
    max_exact_p = max(abs(e) for e in exact_p)
    if max_exact_p <= 1e6 * EPSILON:
        raise ValidationInputError("the pointwise reference field is degenerate")

    boundary_abs = max(max(abs(v) for v in outer["u"]), max(abs(v) for v in inner["u"]))
    normal_errors = {}
    flux = {}
    for name, block in ((geo.OUTER, outer), (geo.INNER, inner)):
        exact_dn = [reference.normal_derivative(x, y, name) for x, y in block["points"]]
        normal_errors[name] = max(abs(a - e) for a, e in zip(block["dn"], exact_dn))
        flux[name] = math.fsum(weight * value for weight, value in zip(block["weights"], block["dn"]))
    normal_error = max(normal_errors.values()) / (reference.MAX_ABS_NORMAL_DERIVATIVE + EPSILON)

    # geometry-native equal-area cells (4 radial x 16 angular)
    cells: dict[tuple[int, int], list[float]] = {}
    for point, error in zip(p, pointwise_errors):
        cells.setdefault(geo.cell_index(point, RADIAL_BINS, ANGULAR_SECTORS), []).append(error * error)
    if len(cells) < RADIAL_BINS * ANGULAR_SECTORS:
        raise ValidationInputError(
            f"the pointwise grid covers {len(cells)} of {RADIAL_BINS * ANGULAR_SECTORS} equal-area cells; "
            "the localized criterion cannot be evaluated on a partition with empty cells")
    reference_rms_p = math.sqrt(math.fsum(e * e for e in exact_p) / n_p)
    cell_rms = {key: math.sqrt(math.fsum(values) / len(values)) for key, values in cells.items()}
    worst_cell = max(cell_rms, key=lambda key: cell_rms[key])
    hotspot_index = max(range(n_p), key=lambda i: pointwise_errors[i])

    values = {
        "ACA-1": math.sqrt(l2_squared / (reference_l2_squared + EPSILON)),
        "ACA-2": max(pointwise_errors) / (max_exact_p + EPSILON),
        "ACA-3": boundary_abs,
        "ACA-4": residual_rms / reference.F_RMS,
        "ACA-5": abs(integral_u - reference.INTEGRAL_U) / abs(reference.INTEGRAL_U),
        "ACA-6": normal_error,
        "ACA-7": abs(dirichlet_energy - forcing_energy) / reference.DIRICHLET_ENERGY,
        "ACA-9": cell_rms[worst_cell] / reference_rms_p,
        "ACA-8": math.sqrt(grad_l2_squared / (reference_grad_squared + EPSILON)),
    }
    metrics = {cid: {"value": values[cid], "threshold": THRESHOLDS[cid], "level": LEVELS[cid],
                     "criterionSatisfied": values[cid] <= THRESHOLDS[cid]} for cid, _limit, _level in CRITERIA}
    diagnostics = {
        "gridLabel": grid_label,
        "geometryId": geo.GEOMETRY["geometryId"],
        "quadratureNodes": n_q,
        "pointwiseNodes": n_p,
        "quadratureArea": math.fsum(w),
        "referenceRmsPointwise": reference_rms_p,
        "worstCell": {"radialBin": worst_cell[0], "angularSector": worst_cell[1], "rms": cell_rms[worst_cell],
                      "members": len(cells[worst_cell])},
        "medianCellRms": _median(list(cell_rms.values())),
        "cells": {f"{i},{j}": value for (i, j), value in sorted(cell_rms.items())},
        "hotspot": {"x": p[hotspot_index][0], "y": p[hotspot_index][1], "absError": pointwise_errors[hotspot_index],
                    "radius": geo.radius(p[hotspot_index])},
        "boundary": {
            geo.OUTER: {"maxAbsU": max(abs(v) for v in outer["u"]), "maxNormalError": normal_errors[geo.OUTER],
                        "flux": flux[geo.OUTER], "nodes": len(outer["points"])},
            geo.INNER: {"maxAbsU": max(abs(v) for v in inner["u"]), "maxNormalError": normal_errors[geo.INNER],
                        "flux": flux[geo.INNER], "nodes": len(inner["points"])},
        },
        "integrals": {"u": integral_u, "dirichletEnergy": dirichlet_energy, "forcingEnergy": forcing_energy,
                      "fluxTotal": flux[geo.OUTER] + flux[geo.INNER]},
        "localizedCriterion": dict(LOCALIZED_ERROR_CRITERION),
        "derivativeMethod": fields.derivative_method,
        "device": fields.device,
    }
    return {"metrics": metrics, "diagnostics": diagnostics,
            "failedMustCriteria": [cid for cid in MUST_IDS if not metrics[cid]["criterionSatisfied"]],
            "failedShouldCriteria": [cid for cid in SHOULD_IDS if not metrics[cid]["criterionSatisfied"]]}


# ------------------------------------------------------------------ fixtures
#
# Negative controls for Gate 3: each fixture is a field the validator must REJECT,
# built from a defect that a lift from the square could plausibly produce. The
# positive control is the analytic solution itself, which must be accepted.

@dataclass(frozen=True)
class FixtureAnnulus:
    name: str
    description: str
    must_be_accepted: bool
    #: how the candidate field is built from the reference at a point
    mode: str


FIXTURES: tuple[FixtureAnnulus, ...] = (
    FixtureAnnulus("analyticControl", "the manufactured solution itself", True, "exact"),
    FixtureAnnulus("holeFilled", "the hard factor written as if the domain were the full disk: (1 - s) only, so the "
                                 "field does not vanish on the inner circle", False, "holeFilled"),
    FixtureAnnulus("wrongInnerRadius", "the hard factor built with a = 0.3 instead of 0.35", False, "wrongInnerRadius"),
    FixtureAnnulus("wrongOuterRadius", "the hard factor built with R = 1.05 instead of 1", False, "wrongOuterRadius"),
    FixtureAnnulus("wrongSourceSign", "the residual evaluated against -f", False, "wrongSourceSign"),
    FixtureAnnulus("derivativeSwap",
                   "u_x and u_y exchanged everywhere the model reports a derivative, including the boundary normal "
                   "derivative -- the acceptance MUST set alone does not see a swap that stays inside the domain "
                   "integrals (the energy is swap-invariant and the H1 seminorm is a SHOULD), which is why Gate 3 "
                   "checks the AD components separately",
                   False, "derivativeSwap"),
    FixtureAnnulus("wrongInnerNormal", "the inner boundary measured with +(x, y)/a instead of -(x, y)/a", False,
                   "wrongInnerNormal"),
    FixtureAnnulus("boundaryComponentSwap", "the two components' normals exchanged", False, "boundaryComponentSwap"),
    FixtureAnnulus("localizedHotspot", "the exact solution plus a narrow bump in one equal-area cell", False,
                   "localizedHotspot"),
    FixtureAnnulus("radialOnly", "the radial part h only, dropping the non-radial modulation g", False, "radialOnly"),
)


def _hard_factor(x: float, y: float, inner: float, outer: float) -> float:
    s = x * x + y * y
    return (outer * outer - s) * (s - inner * inner)


def sample_fixture(fixture: FixtureAnnulus, *, quadrature_points: Sequence[Sequence[float]],
                   quadrature_weights: Sequence[float], pointwise_points: Sequence[Sequence[float]],
                   boundary: Mapping[str, Mapping[str, Sequence[Any]]]) -> FieldsAnnulus:
    """Build the candidate fields of one fixture on the given evaluation sets."""

    mode = fixture.mode
    scale = reference.A * reference.A

    def value(x: float, y: float) -> float:
        if mode == "holeFilled":
            return (1.0 - (x * x + y * y)) * reference.g(x, y) * (1.0 - scale)
        if mode == "wrongInnerRadius":
            return _hard_factor(x, y, 0.30, reference.R) * reference.g(x, y)
        if mode == "wrongOuterRadius":
            return _hard_factor(x, y, reference.A, 1.05) * reference.g(x, y)
        if mode == "radialOnly":
            return reference.h(x, y)
        if mode == "localizedHotspot":
            dx, dy = x - 0.5, y - 0.45
            return reference.solution(x, y) + 0.02 * math.exp(-(dx * dx + dy * dy) / (2.0 * 0.03 * 0.03))
        return reference.solution(x, y)

    def gradient(x: float, y: float) -> tuple[float, float]:
        gx, gy = reference.gradient(x, y)
        if mode == "derivativeSwap":
            return gy, gx
        if mode in ("holeFilled", "wrongInnerRadius", "wrongOuterRadius", "radialOnly", "localizedHotspot"):
            step = 1e-6
            return ((value(x + step, y) - value(x - step, y)) / (2.0 * step),
                    (value(x, y + step) - value(x, y - step)) / (2.0 * step))
        return gx, gy

    def second(x: float, y: float) -> tuple[float, float]:
        step = 1e-4
        uxx = (value(x + step, y) - 2.0 * value(x, y) + value(x - step, y)) / (step * step)
        uyy = (value(x, y + step) - 2.0 * value(x, y) + value(x, y - step)) / (step * step)
        if mode == "wrongSourceSign":
            return -uxx, -uyy
        return uxx, uyy

    u_q, ux_q, uy_q, uxx_q, uyy_q = [], [], [], [], []
    for x, y in quadrature_points:
        u_q.append(value(x, y))
        gx, gy = gradient(x, y)
        ux_q.append(gx)
        uy_q.append(gy)
        xx, yy = second(x, y)
        uxx_q.append(xx)
        uyy_q.append(yy)

    blocks: dict[str, dict[str, list[float]]] = {}
    for component, block in boundary.items():
        points = list(block["points"])
        us = [value(x, y) for x, y in points]
        normals_component = component
        if mode == "wrongInnerNormal" and component == geo.INNER:
            dns = [-reference.normal_derivative(x, y, geo.INNER) for x, y in points]
        elif mode == "boundaryComponentSwap":
            other = geo.INNER if component == geo.OUTER else geo.OUTER
            dns = [reference.gradient(x, y)[0] * geo.outward_normal((x, y), other)[0]
                   + reference.gradient(x, y)[1] * geo.outward_normal((x, y), other)[1] for x, y in points]
            normals_component = other
        elif mode == "derivativeSwap":
            # a genuine x/y swap in the derivative wiring corrupts the normal derivative
            # too: dn = (u_y, u_x) . n instead of (u_x, u_y) . n
            dns = []
            for x, y in points:
                gx, gy = reference.gradient(x, y)
                nx, ny = geo.outward_normal((x, y), component)
                dns.append(gy * nx + gx * ny)
        else:
            dns = [reference.normal_derivative(x, y, component) for x, y in points]
        blocks[component] = {"points": points, "weights": list(block["weights"]), "u": us, "dn": dns,
                             "normalsFrom": normals_component}

    return FieldsAnnulus(
        quadrature_points=list(quadrature_points), quadrature_weights=list(quadrature_weights),
        u_quadrature=u_q, ux_quadrature=ux_q, uy_quadrature=uy_q, uxx_quadrature=uxx_q, uyy_quadrature=uyy_q,
        pointwise_points=list(pointwise_points), u_pointwise=[value(x, y) for x, y in pointwise_points],
        boundary=blocks, derivative_method="ANALYTIC_OR_FINITE_DIFFERENCE_FIXTURE", device="cpu")


def fixture_verdicts(*, quadrature_points: Sequence[Sequence[float]], quadrature_weights: Sequence[float],
                     pointwise_points: Sequence[Sequence[float]],
                     boundary: Mapping[str, Mapping[str, Sequence[Any]]],
                     tolerance_for_control: Mapping[str, float] | None = None) -> list[dict[str, Any]]:
    """Run every fixture through the validator and report accepted/rejected against its ground truth."""

    verdicts = []
    for fixture in FIXTURES:
        try:
            fields = sample_fixture(fixture, quadrature_points=quadrature_points,
                                    quadrature_weights=quadrature_weights,
                                    pointwise_points=pointwise_points, boundary=boundary)
            result = evaluate_fields(fields, grid_label=f"fixture:{fixture.name}")
            accepted = not result["failedMustCriteria"]
            failed = result["failedMustCriteria"]
            error = None
        except ValidationInputError as exc:               # a fixture the validator refuses outright
            accepted, failed, error = False, ["<rejected by input validation>"], str(exc)
        verdicts.append({"fixture": fixture.name, "description": fixture.description,
                         "mustBeAccepted": fixture.must_be_accepted, "accepted": accepted,
                         "failedMust": failed, "validationError": error,
                         "verdictCorrect": accepted == fixture.must_be_accepted})
    return verdicts
