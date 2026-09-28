"""The annulus geometry contract (Geometry Lift 1).

    Omega = { (x, y) : a^2 < x^2 + y^2 < 1 },   a = 0.35

One frozen description answers every geometric question the experiment asks --
membership, which boundary component a point is on, the outward normal there,
how to sample the area uniformly, and how to integrate over it -- so the
sampler, the quadrature, the physics checks and the validator cannot disagree
about where the domain is.

Two facts drive most of the code below.

*Uniform area is not uniform radius.* Drawing ``r ~ U(a, 1)`` over-samples the
inner ring, because the area element is ``r dr dtheta``. The area-uniform draw
is ``r = sqrt(a^2 + (1 - a^2) U)``, i.e. the *area fraction*

    t(r) = (r^2 - a^2) / (1 - a^2)

is what must be uniform. The same substitution makes the quadrature Jacobian a
constant: ``dx dy = r dr dtheta = ((1 - a^2) / 2) dt dtheta``.

*The two boundary components have opposite normals.* The outward normal of the
domain points away from the origin on the outer circle and *into the hole* on
the inner one:

    n_outer(x, y) = (x, y) / R        n_inner(x, y) = -(x, y) / a

Getting the inner sign wrong still leaves a plausible-looking flux defect,
because the two contributions partly cancel, so the sign is asserted on its own
(``pinn/experiments_annulus`` tests) rather than only through the flux identity.

Pure Python and pure functions: no torch, no numpy, no global state.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

#: Frozen geometry parameters. These are part of the ScientificSpec: changing
#: either radius is a new problem, not a new run.
INNER_RADIUS = 0.35
OUTER_RADIUS = 1.0

OUTER = "outer"
INNER = "inner"
BOUNDARY_COMPONENTS: tuple[str, ...] = (OUTER, INNER)

#: The machine-readable contract every artifact of this experiment refers to.
GEOMETRY: dict[str, Any] = {
    "geometryId": "annulus-a035-R1-v1",
    "geometryType": "annulus",
    "dimension": 2,
    "coordinates": ["x", "y"],
    "outerBoundary": {"component": OUTER, "center": [0.0, 0.0], "radius": OUTER_RADIUS,
                      "identity": "x^2 + y^2 = 1",
                      "outwardNormal": "(x, y) / R -- away from the origin"},
    "innerBoundary": {"component": INNER, "center": [0.0, 0.0], "radius": INNER_RADIUS,
                      "identity": "x^2 + y^2 = a^2",
                      "outwardNormal": "-(x, y) / a -- into the hole, i.e. towards the origin"},
    "membership": "a^2 < x^2 + y^2 < 1",
    "multiplyConnected": True,
    "boundaryComponents": list(BOUNDARY_COMPONENTS),
    "areaUniformRadialTransform": "t = (r^2 - a^2) / (1 - a^2) ~ U(0, 1)",
    "quadratureJacobian": "dx dy = r dr dtheta = ((1 - a^2) / 2) dt dtheta (constant in t and theta)",
    "area": "pi * (R^2 - a^2)",
}

INTERIOR = "interior"
ON_OUTER = "onOuterBoundary"
ON_INNER = "onInnerBoundary"
IN_HOLE = "inHole"
OUTSIDE = "outsideOuterDisk"


class GeometryError(ValueError):
    """A point, a sample set or a boundary set that the geometry contract rejects."""


def _coordinates(point: Sequence[float]) -> tuple[float, float]:
    if len(point) != 2:
        raise GeometryError(f"an annulus point needs 2 coordinates, got {len(point)}")
    x, y = float(point[0]), float(point[1])
    if not (math.isfinite(x) and math.isfinite(y)):
        raise GeometryError(f"non-finite coordinate ({x}, {y})")
    return x, y


def radius_squared(point: Sequence[float]) -> float:
    x, y = _coordinates(point)
    return x * x + y * y


def radius(point: Sequence[float]) -> float:
    return math.sqrt(radius_squared(point))


def area(inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> float:
    return math.pi * (outer * outer - inner * inner)


def classify(point: Sequence[float], *, tolerance: float = 0.0,
             inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> str:
    """Which part of the plane this point belongs to, with an explicit boundary band.

    ``tolerance`` is a band *in radius*: a point within it of either circle is
    reported as being on that boundary component rather than inside or outside.
    With the default 0 the classification is the strict mathematical one.
    """

    if tolerance < 0:
        raise GeometryError("tolerance must be >= 0")
    r = radius(point)
    if abs(r - outer) <= tolerance:
        return ON_OUTER
    if abs(r - inner) <= tolerance:
        return ON_INNER
    if r > outer:
        return OUTSIDE
    if r < inner:
        return IN_HOLE
    return INTERIOR


def contains(point: Sequence[float], *, tolerance: float = 0.0) -> bool:
    """Strict interior membership: a^2 < x^2 + y^2 < 1, boundaries excluded."""

    return classify(point, tolerance=tolerance) == INTERIOR


def membership_report(points: Sequence[Sequence[float]], *, tolerance: float = 0.0) -> dict[str, Any]:
    """Counts per class plus the indices of everything that is not strictly interior."""

    counts = {INTERIOR: 0, ON_OUTER: 0, ON_INNER: 0, IN_HOLE: 0, OUTSIDE: 0}
    illegal: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        kind = classify(point, tolerance=tolerance)
        counts[kind] += 1
        if kind != INTERIOR:
            illegal.append({"index": index, "point": [float(point[0]), float(point[1])],
                            "class": kind, "radius": radius(point)})
    return {"counts": counts, "illegal": illegal, "total": len(points),
            "tolerance": tolerance, "geometryId": GEOMETRY["geometryId"]}


def assert_interior(points: Sequence[Sequence[float]], *, label: str, tolerance: float = 0.0) -> None:
    """Fail closed: no evaluation set may hold a point in the hole, outside, or on a boundary."""

    report = membership_report(points, tolerance=tolerance)
    if report["illegal"]:
        first = report["illegal"][:5]
        raise GeometryError(
            f"{label}: {len(report['illegal'])} of {report['total']} points are not strictly inside the annulus "
            f"(a^2 < x^2 + y^2 < 1); first offenders: {first}"
        )


# ------------------------------------------------------------------ polar map

def to_cartesian(r: float, theta: float) -> tuple[float, float]:
    return r * math.cos(theta), r * math.sin(theta)


def to_polar(point: Sequence[float]) -> tuple[float, float]:
    """(r, theta) with theta in [0, 2*pi)."""

    x, y = _coordinates(point)
    theta = math.atan2(y, x)
    if theta < 0.0:
        theta += 2.0 * math.pi
    if theta >= 2.0 * math.pi:          # atan2 can return exactly -0.0 -> 2*pi
        theta -= 2.0 * math.pi
    return math.hypot(x, y), theta


def area_fraction(r: float, *, inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> float:
    """t = (r^2 - a^2) / (R^2 - a^2): the fraction of the annulus area inside radius r."""

    return (r * r - inner * inner) / (outer * outer - inner * inner)


def radius_of_area_fraction(t: float, *, inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> float:
    if not 0.0 <= t <= 1.0:
        raise GeometryError(f"area fraction must lie in [0, 1], got {t}")
    return math.sqrt(inner * inner + (outer * outer - inner * inner) * t)


# ------------------------------------------------------------------ sampling

def uniform_area_points(count: int, seed: int, *, inner: float = INNER_RADIUS,
                        outer: float = OUTER_RADIUS) -> list[tuple[float, float]]:
    """``count`` points drawn uniformly by AREA, using numpy's Generator for reproducibility.

    r = sqrt(a^2 + (R^2 - a^2) U), theta = 2 pi V with U, V ~ U(0, 1). Drawing r
    uniformly instead would put too many points near the hole; the radial
    profile is checked by ``radial_uniformity`` and by a statistical test.
    """

    if count < 1:
        raise GeometryError("count must be >= 1")
    import numpy as np                                   # local: the governance venv has no numpy

    rng = np.random.default_rng(seed)
    draws = rng.random((count, 2))
    points: list[tuple[float, float]] = []
    for u, v in draws:
        r = math.sqrt(inner * inner + (outer * outer - inner * inner) * float(u))
        theta = 2.0 * math.pi * float(v)
        x, y = to_cartesian(r, theta)
        points.append((x, y))
    return points


def radial_uniformity(points: Sequence[Sequence[float]], bins: int = 10) -> dict[str, Any]:
    """Implementation check (never a scientific claim): is t = (r^2-a^2)/(R^2-a^2) ~ U(0,1)?

    Reports the per-bin counts, the largest deviation of the empirical CDF from
    the uniform one (a Kolmogorov statistic) and the mean of t, which is 1/2 for
    an area-uniform draw and about 0.46 for the r-uniform mistake at a = 0.35.
    """

    if bins < 2:
        raise GeometryError("bins must be >= 2")
    values = sorted(area_fraction(radius(p)) for p in points)
    n = len(values)
    if n == 0:
        raise GeometryError("no points")
    counts = [0] * bins
    for t in values:
        counts[min(int(t * bins), bins - 1)] += 1
    supremum = max(max(abs((i + 1) / n - t), abs(t - i / n)) for i, t in enumerate(values))
    return {"bins": counts, "expectedPerBin": n / bins, "meanAreaFraction": math.fsum(values) / n,
            "kolmogorovStatistic": supremum, "count": n}


# ------------------------------------------------------------------ boundaries

def boundary_radius(component: str, *, inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> float:
    if component == OUTER:
        return outer
    if component == INNER:
        return inner
    raise GeometryError(f"unknown boundary component {component!r}; expected one of {BOUNDARY_COMPONENTS}")


def boundary_nodes(component: str, count: int, *, inner: float = INNER_RADIUS,
                   outer: float = OUTER_RADIUS) -> tuple[list[tuple[float, float]], list[float]]:
    """Deterministic arc-length quadrature on one boundary component.

    Equally spaced angles with weight ``r * 2 pi / count`` is the periodic
    trapezoid rule, which is spectrally accurate for smooth periodic integrands
    -- the right rule for a circle, and the reason no Gauss nodes are needed here.
    """

    if count < 3:
        raise GeometryError("a boundary component needs at least 3 nodes")
    r = boundary_radius(component, inner=inner, outer=outer)
    step = 2.0 * math.pi / count
    nodes = [to_cartesian(r, i * step) for i in range(count)]
    weights = [r * step] * count
    return nodes, weights


def outward_normal(point: Sequence[float], component: str, *, inner: float = INNER_RADIUS,
                   outer: float = OUTER_RADIUS) -> tuple[float, float]:
    """The outward normal OF THE DOMAIN at a boundary point.

    Outer component: away from the origin. Inner component: towards the origin,
    because the hole is outside the domain. The second sign is the one a lift
    from a simply connected square gets wrong.
    """

    x, y = _coordinates(point)
    r = boundary_radius(component, inner=inner, outer=outer)
    if r <= 0:
        raise GeometryError("a boundary component needs a positive radius")
    if component == OUTER:
        return x / r, y / r
    return -x / r, -y / r


def assert_on_boundary(points: Sequence[Sequence[float]], component: str, *, tolerance: float = 1e-12,
                       inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> float:
    """Every node must sit on the named circle; returns the worst deviation in radius."""

    target = boundary_radius(component, inner=inner, outer=outer)
    worst = 0.0
    for index, point in enumerate(points):
        deviation = abs(radius(point) - target)
        worst = max(worst, deviation)
        if deviation > tolerance:
            raise GeometryError(
                f"{component} boundary node {index} is at radius {radius(point)!r}, expected {target} "
                f"(deviation {deviation:.3e} > {tolerance:.3e})")
    return worst


# ------------------------------------------------------------------ quadrature

def _gauss_legendre_unit(order: int) -> tuple[list[float], list[float]]:
    """Gauss-Legendre nodes and weights mapped to (0, 1), by Newton iteration on P_n."""

    if order < 1:
        raise GeometryError("quadrature order must be >= 1")
    nodes: list[float] = []
    weights: list[float] = []
    for i in range(1, order + 1):
        x = math.cos(math.pi * (i - 0.25) / (order + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, 0.0
            for j in range(1, order + 1):
                p0, p1 = ((2 * j - 1) * x * p0 - (j - 1) * p1) / j, p0
            derivative = order * (x * p0 - p1) / (x * x - 1.0)
            delta = p0 / derivative
            x -= delta
            if abs(delta) < 1e-15:
                break
        weight = 2.0 / ((1.0 - x * x) * derivative * derivative)
        nodes.append(0.5 * (1.0 - x))
        weights.append(0.5 * weight)
    order_index = sorted(range(order), key=lambda k: nodes[k])
    return [nodes[k] for k in order_index], [weights[k] for k in order_index]


def quadrature(radial_order: int, angular_count: int, *, inner: float = INNER_RADIUS,
               outer: float = OUTER_RADIUS) -> tuple[list[tuple[float, float]], list[float]]:
    """Geometry-native quadrature of the annulus: Gauss-Legendre in t, trapezoid in theta.

    With t = (r^2 - a^2) / (R^2 - a^2) the Jacobian is the constant
    ``(R^2 - a^2) / 2``, so the weights are a plain product -- no 1/r factors to
    get wrong, and no node sits on either boundary.
    """

    if angular_count < 3:
        raise GeometryError("the angular rule needs at least 3 nodes")
    t_nodes, t_weights = _gauss_legendre_unit(radial_order)
    jacobian = 0.5 * (outer * outer - inner * inner)
    step = 2.0 * math.pi / angular_count
    points: list[tuple[float, float]] = []
    weights: list[float] = []
    for t, wt in zip(t_nodes, t_weights):
        r = radius_of_area_fraction(t, inner=inner, outer=outer)
        for k in range(angular_count):
            points.append(to_cartesian(r, k * step))
            weights.append(jacobian * wt * step)
    return points, weights


def integrate(values: Iterable[float], weights: Sequence[float]) -> float:
    values = list(values)
    if len(values) != len(weights):
        raise GeometryError(f"quadrature mismatch: {len(values)} values against {len(weights)} weights")
    return math.fsum(v * w for v, w in zip(values, weights))


# ------------------------------------------------------- geometry-native cells

def cell_index(point: Sequence[float], radial_bins: int, angular_sectors: int, *,
               inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> tuple[int, int]:
    """Which equal-area cell a point falls in: (radial bin in t, angular sector).

    Equal area, because the bins are uniform in the area fraction t -- a
    Cartesian tile grid would straddle the hole and give cells of different area
    (and some with no domain in them at all).
    """

    if radial_bins < 1 or angular_sectors < 1:
        raise GeometryError("a partition needs at least one bin and one sector")
    r, theta = to_polar(point)
    t = area_fraction(r, inner=inner, outer=outer)
    i = min(max(int(t * radial_bins), 0), radial_bins - 1)
    j = min(max(int(theta / (2.0 * math.pi) * angular_sectors), 0), angular_sectors - 1)
    return i, j


def cell_area(radial_bins: int, angular_sectors: int, *, inner: float = INNER_RADIUS,
              outer: float = OUTER_RADIUS) -> float:
    return area(inner, outer) / (radial_bins * angular_sectors)
