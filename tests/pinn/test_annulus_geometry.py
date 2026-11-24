"""The annulus geometry contract (Geometry Lift 1): membership, boundaries, normals, quadrature.

These are the checks that a lift from a rectangle to a curved, multiply connected
domain can silently fail. Everything here is pure Python, so it runs in the
governance virtualenv as well as under the training interpreter.
"""

import math

import pytest

from pinn.geometry import annulus as geo
from pinn.governance import annulus_contract as contract
from pinn.reference import analytic_annulus as ref

A = geo.INNER_RADIUS
R = geo.OUTER_RADIUS


def polar(r, theta):
    return geo.to_cartesian(r, theta)


# ------------------------------------------------------------------ membership

def test_the_geometry_contract_states_both_components_and_the_hole():
    assert geo.GEOMETRY["geometryType"] == "annulus"
    assert geo.GEOMETRY["multiplyConnected"] is True
    assert geo.GEOMETRY["outerBoundary"]["radius"] == 1.0
    assert geo.GEOMETRY["innerBoundary"]["radius"] == 0.35
    assert geo.GEOMETRY["boundaryComponents"] == ["outer", "inner"]


@pytest.mark.parametrize(
    ("point", "expected"),
    [
        ((0.6, 0.0), geo.INTERIOR),
        ((0.0, -0.6), geo.INTERIOR),
        ((0.9, 0.3), geo.OUTSIDE),          # r = 0.948 -- inside the disk but let the radius decide
        ((1.4, 0.0), geo.OUTSIDE),
        ((0.0, 0.0), geo.IN_HOLE),
        ((0.2, 0.1), geo.IN_HOLE),
        ((1.0, 0.0), geo.ON_OUTER),
        ((0.0, A), geo.ON_INNER),
    ],
)
def test_points_are_classified_by_the_contract(point, expected):
    kind = geo.classify(point)
    if expected == geo.OUTSIDE and geo.radius(point) < 1.0:
        assert kind == geo.INTERIOR          # (0.9, 0.3) really is inside; keep the arithmetic honest
    else:
        assert kind == expected


def test_the_hole_is_not_part_of_the_domain():
    for r in (0.0, 0.1, 0.2, 0.34, A - 1e-12):
        for theta in (0.0, 1.0, 2.5, 6.0):
            assert not geo.contains(polar(r, theta)), f"r = {r} is inside the hole"


def test_the_exterior_is_not_part_of_the_domain():
    for r in (1.0 + 1e-12, 1.01, 2.0):
        assert not geo.contains(polar(r, 0.3))


def test_the_boundaries_themselves_are_not_interior():
    assert not geo.contains(polar(R, 0.7))
    assert not geo.contains(polar(A, 0.7))
    assert geo.classify(polar(R, 0.7), tolerance=1e-9) == geo.ON_OUTER
    assert geo.classify(polar(A, 0.7), tolerance=1e-9) == geo.ON_INNER


def test_an_illegal_sample_set_is_refused_with_its_offenders():
    points = [polar(0.6, 0.0), (0.0, 0.0), polar(1.2, 1.0)]
    with pytest.raises(geo.GeometryError, match="not strictly inside"):
        geo.assert_interior(points, label="D_test")
    report = geo.membership_report(points)
    assert report["counts"][geo.IN_HOLE] == 1 and report["counts"][geo.OUTSIDE] == 1
    assert [item["class"] for item in report["illegal"]] == [geo.IN_HOLE, geo.OUTSIDE]


# --------------------------------------------------------------- polar mapping

@pytest.mark.parametrize("theta", [0.0, 0.3, math.pi / 2, math.pi, 4.0, 2 * math.pi - 1e-9])
def test_polar_roundtrip_and_angle_periodicity(theta):
    r = 0.7
    x, y = geo.to_cartesian(r, theta)
    back_r, back_theta = geo.to_polar((x, y))
    assert back_r == pytest.approx(r, abs=1e-15)
    assert back_theta == pytest.approx(theta, abs=1e-12)
    shifted = geo.to_cartesian(r, theta + 2 * math.pi)
    assert shifted[0] == pytest.approx(x, abs=1e-12) and shifted[1] == pytest.approx(y, abs=1e-12)
    assert 0.0 <= geo.to_polar(shifted)[1] < 2 * math.pi


def test_negative_angles_are_mapped_into_the_period():
    _r, theta = geo.to_polar(geo.to_cartesian(0.5, -0.4))
    assert 0.0 <= theta < 2 * math.pi
    assert theta == pytest.approx(2 * math.pi - 0.4, abs=1e-12)


# ------------------------------------------------- the area-uniform transform

def test_the_area_fraction_transform_is_the_inverse_of_the_radius_map():
    for t in (0.0, 0.25, 0.5, 0.9, 1.0):
        r = geo.radius_of_area_fraction(t)
        assert geo.area_fraction(r) == pytest.approx(t, abs=1e-15)
        assert A - 1e-15 <= r <= R + 1e-15


def test_uniform_radius_is_not_uniform_area():
    """The mistake this transform exists to prevent, stated as a number.

    Drawing r ~ U(a, 1) puts the median radius at (a + 1) / 2 = 0.675, whose area
    fraction is 0.38, not 0.5: the half of the points nearest the hole would cover
    only 38 % of the area. The area-uniform draw has t uniform by construction.
    """

    median_radius_uniform_r = 0.5 * (A + R)
    assert geo.area_fraction(median_radius_uniform_r) == pytest.approx(0.3796, abs=5e-4)
    assert geo.area_fraction(geo.radius_of_area_fraction(0.5)) == pytest.approx(0.5, abs=1e-15)


def test_the_radial_uniformity_check_separates_the_two_draws():
    """Deterministic stand-ins for the two sampling rules, so no RNG is needed here."""

    n = 4000
    area_uniform = [polar(geo.radius_of_area_fraction((i + 0.5) / n), 2 * math.pi * ((i * 0.618) % 1.0))
                    for i in range(n)]
    radius_uniform = [polar(A + (R - A) * (i + 0.5) / n, 2 * math.pi * ((i * 0.618) % 1.0)) for i in range(n)]
    good = geo.radial_uniformity(area_uniform)
    bad = geo.radial_uniformity(radius_uniform)
    assert good["meanAreaFraction"] == pytest.approx(0.5, abs=1e-3)
    assert good["kolmogorovStatistic"] < 0.01
    assert bad["meanAreaFraction"] < 0.47, "an r-uniform draw must be visibly biased towards the hole"
    assert bad["kolmogorovStatistic"] > 0.05


# ------------------------------------------------------------------ boundaries

@pytest.mark.parametrize("component", ["outer", "inner"])
def test_boundary_nodes_sit_on_their_own_circle(component):
    nodes, weights = geo.boundary_nodes(component, 64)
    radius = geo.boundary_radius(component)
    assert geo.assert_on_boundary(nodes, component) < 1e-15
    assert math.fsum(weights) == pytest.approx(2 * math.pi * radius, abs=1e-12)
    other = "inner" if component == "outer" else "outer"
    with pytest.raises(geo.GeometryError, match="expected"):
        geo.assert_on_boundary(nodes, other)


def test_the_outward_normals_of_the_two_components_point_in_opposite_directions():
    """The sign that a lift from a simply connected domain gets wrong."""

    for theta in (0.0, 0.9, 2.2, 5.5):
        outer_point = polar(R, theta)
        inner_point = polar(A, theta)
        nx, ny = geo.outward_normal(outer_point, "outer")
        assert (nx, ny) == pytest.approx((math.cos(theta), math.sin(theta)), abs=1e-15)
        mx, my = geo.outward_normal(inner_point, "inner")
        assert (mx, my) == pytest.approx((-math.cos(theta), -math.sin(theta)), abs=1e-15)
        # radially outward on the outer circle, towards the origin on the inner one
        assert nx * outer_point[0] + ny * outer_point[1] > 0
        assert mx * inner_point[0] + my * inner_point[1] < 0
        assert math.hypot(nx, ny) == pytest.approx(1.0, abs=1e-15)
        assert math.hypot(mx, my) == pytest.approx(1.0, abs=1e-15)


def test_an_unknown_boundary_component_is_refused():
    with pytest.raises(geo.GeometryError, match="unknown boundary component"):
        geo.outward_normal((1.0, 0.0), "left")


# ------------------------------------------------------------------ quadrature

def test_the_quadrature_integrates_the_annulus_area():
    points, weights = geo.quadrature(24, 96)
    assert math.fsum(weights) == pytest.approx(geo.area(), abs=1e-13)
    assert geo.area() == pytest.approx(math.pi * (1 - A * A), abs=1e-15)
    geo.assert_interior(points, label="quadrature")


def test_the_quadrature_jacobian_is_constant_in_t_and_theta():
    """dx dy = ((R^2 - a^2)/2) dt dtheta: no 1/r factor to get wrong."""

    points, weights = geo.quadrature(8, 12)
    assert len(set(round(w, 15) for w in weights)) <= 8, "weights may vary with the GL node in t, never with theta"
    for start in range(0, len(weights), 12):
        row = weights[start:start + 12]
        assert max(row) == pytest.approx(min(row), rel=1e-15), "the angular rule is uniform"


def test_the_quadrature_reproduces_the_exact_integral_of_the_solution():
    points, weights = geo.quadrature(40, 128)
    integral = geo.integrate([ref.solution(x, y) for x, y in points], weights)
    assert integral == pytest.approx(ref.exact_integral_of_solution(), rel=1e-12)
    assert ref.exact_integral_of_solution() == pytest.approx(math.pi * (1 - A * A) ** 3 / 6, rel=1e-15)


def test_the_non_radial_part_of_g_integrates_to_zero():
    """Section 18 asks for this to be verified, not assumed."""

    points, weights = geo.quadrature(40, 128)
    non_radial = geo.integrate(
        [ref.h(x, y) * (ref.g(x, y) - 1.0) for x, y in points], weights)
    assert abs(non_radial) < 1e-13 * abs(ref.exact_integral_of_solution())


def test_a_mismatched_quadrature_is_refused():
    points, weights = geo.quadrature(4, 8)
    with pytest.raises(geo.GeometryError, match="quadrature mismatch"):
        geo.integrate([1.0] * (len(points) - 1), weights)


# ------------------------------------------------- the manufactured solution

def test_the_hard_factor_vanishes_on_both_circles_and_is_positive_inside():
    for theta in (0.0, 1.1, 3.3, 5.9):
        assert abs(ref.h(*polar(R, theta))) < 1e-15
        assert abs(ref.h(*polar(A, theta))) < 1e-16
        for t in (0.1, 0.5, 0.9):
            assert ref.h(*polar(geo.radius_of_area_fraction(t), theta)) > 0
    assert ref.h(0.0, 0.0) < 0, "inside the hole the factor changes sign -- membership is not optional"


def test_the_solution_vanishes_on_both_boundary_components():
    for component in ("outer", "inner"):
        nodes, _weights = geo.boundary_nodes(component, 128)
        assert max(abs(ref.solution(x, y)) for x, y in nodes) < 1e-15


def test_the_modulation_is_positive_and_not_radial():
    """A radius-only implementation must not be able to reproduce u* by accident."""

    assert ref.g(0.3, 0.2) != pytest.approx(ref.g(0.2, 0.3), rel=1e-6)
    for t in (0.05, 0.5, 0.95):
        r = geo.radius_of_area_fraction(t)
        values = [ref.g(*polar(r, 2 * math.pi * k / 16)) for k in range(16)]
        assert min(values) > 0.0
        assert max(values) - min(values) > 0.1, "g must vary along a circle, or the problem is radial after all"


def test_the_analytic_laplacian_matches_a_finite_difference_of_the_solution():
    """An independent check of the closed-form source that needs no autograd."""

    step = 1e-4          # below this the second difference is dominated by float64 round-off
    for point in (polar(0.5, 0.4), polar(0.8, 2.0), polar(0.4, 5.0)):
        x, y = point
        numeric = ((ref.solution(x + step, y) - 2 * ref.solution(x, y) + ref.solution(x - step, y))
                   + (ref.solution(x, y + step) - 2 * ref.solution(x, y) + ref.solution(x, y - step))) / (step * step)
        assert ref.laplacian(x, y) == pytest.approx(numeric, rel=1e-5, abs=1e-6)
        assert ref.forcing(x, y) == pytest.approx(-ref.laplacian(x, y), rel=1e-15)


def test_the_normal_derivative_uses_each_components_own_normal():
    for theta in (0.2, 1.7, 4.4):
        outer = ref.normal_derivative(*polar(R, theta), "outer")
        inner = ref.normal_derivative(*polar(A, theta), "inner")
        assert outer < 0, "the solution decreases towards the outer wall"
        assert inner < 0, "and towards the hole, once the inner normal points into it"
        flipped = -inner
        assert flipped != pytest.approx(inner, rel=1e-9)


def test_the_flux_identity_holds_for_the_manufactured_solution():
    """int_dOmega du/dn ds + int_Omega f dA = 0 over BOTH components."""

    flux = 0.0
    per_component = {}
    for component in ("outer", "inner"):
        nodes, weights = geo.boundary_nodes(component, 512)
        per_component[component] = geo.integrate(
            [ref.normal_derivative(x, y, component) for x, y in nodes], weights)
        flux += per_component[component]
    points, weights = geo.quadrature(40, 128)
    forcing_integral = geo.integrate([ref.forcing(x, y) for x, y in points], weights)
    assert abs(flux + forcing_integral) / abs(forcing_integral) < 1e-12
    assert flux == pytest.approx(ref.exact_flux_integral(), rel=1e-12)
    # and the identity must NOT survive the wrong inner normal
    wrong = per_component["outer"] - per_component["inner"]
    assert abs(wrong + forcing_integral) / abs(forcing_integral) > 0.1


# ------------------------------------------------------- geometry-native cells

def test_the_localized_partition_is_equal_area_and_covers_the_domain():
    bins, sectors = contract.RADIAL_BINS, contract.ANGULAR_SECTORS
    assert bins * sectors == contract.LOCALIZED_CELLS == 64
    assert geo.cell_area(bins, sectors) == pytest.approx(geo.area() / 64, rel=1e-15)
    seen = set()
    for i in range(bins):
        for j in range(sectors):
            t = (i + 0.5) / bins
            theta = 2 * math.pi * (j + 0.5) / sectors
            point = polar(geo.radius_of_area_fraction(t), theta)
            assert geo.contains(point)
            seen.add(geo.cell_index(point, bins, sectors))
    assert len(seen) == 64, "every cell must be reachable"


def test_cells_follow_the_area_fraction_not_the_radius():
    bins, sectors = contract.RADIAL_BINS, contract.ANGULAR_SECTORS
    midpoint_by_radius = 0.5 * (A + R)
    i, _j = geo.cell_index(polar(midpoint_by_radius, 0.1), bins, sectors)
    assert i == 1, "the radial midpoint is in the second equal-area bin, not the third"
    assert geo.cell_index(polar(geo.radius_of_area_fraction(0.99), 0.1), bins, sectors)[0] == bins - 1


def test_the_localized_criterion_contract_is_geometry_native():
    criterion = contract.localized_criterion()
    assert criterion["criterionId"] == "ACA-9"
    assert criterion["partitionKind"] == "annulusEqualAreaCells"
    assert criterion["radialBins"] == 4 and criterion["angularSectors"] == 16
    assert criterion["operator"] == "<=" and criterion["seedPolicy"] == "every-seed"
    assert criterion["threshold"] == contract.thresholds()["ACA-9"]
    assert criterion["geometryId"] == geo.GEOMETRY["geometryId"]
    with pytest.raises(ValueError, match="not the localized-error criterion"):
        contract.localized_criterion("ACA-1")
    with pytest.raises(ValueError, match="not an acceptance criterion"):
        contract.localized_criterion("ACA-42")


def test_the_contract_registers_a_geometry_verdict_for_every_criterion():
    for criterion_id, _limit, _level in contract.CRITERIA:
        source = contract.THRESHOLD_SOURCES[criterion_id]
        assert source["geometryVerdict"].startswith(("GEOMETRY-INVARIANT", "GEOMETRY-SENSITIVE", "NEW-GEOMETRY"))
        assert source["source"].strip()
        assert criterion_id in contract.METRICS


def test_the_x_y_swap_symmetry_is_registered_not_applicable_with_a_reason():
    check = contract.PHYSICS_CHECKS["PH-A8"]
    assert "NOT_APPLICABLE" in check["statement"]
    assert "asymmetric" in check["geometryRisk"]
