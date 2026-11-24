"""The trusted annulus validator and its negative controls (Geometry Lift 1, Gate 3 material).

The validator is the thing that decides whether a candidate field passes the
acceptance criteria, so it is itself under test: the manufactured solution must be
accepted, and every geometry defect a lift from the square could plausibly produce
must be rejected. Pure Python -- no torch, no numpy.
"""

import math

import pytest

from pinn.experiments.datasets import cgl_unit
from pinn.geometry import annulus as geo
from pinn.governance import annulus_contract as contract
from pinn.reference import analytic_annulus as ref
from pinn.validation import annulus as val
from pinn.validation.poisson2d import ValidationInputError


def evaluation_sets(radial_order=20, angular=64, cgl=14, pointwise_angles=32, boundary_nodes=96):
    quadrature_points, quadrature_weights = geo.quadrature(radial_order, angular)
    t_nodes = [t for t in cgl_unit(cgl) if 0.0 < t < 1.0]
    pointwise = [geo.to_cartesian(geo.radius_of_area_fraction(t), 2 * math.pi * k / pointwise_angles + 0.017)
                 for t in t_nodes for k in range(pointwise_angles)]
    boundary = {}
    for component in (geo.OUTER, geo.INNER):
        nodes, weights = geo.boundary_nodes(component, boundary_nodes)
        boundary[component] = {"points": nodes, "weights": weights,
                               "u": [0.0] * len(nodes), "dn": [0.0] * len(nodes)}
    return quadrature_points, quadrature_weights, pointwise, boundary


@pytest.fixture(scope="module")
def sets():
    return evaluation_sets()


def exact_fields(sets):
    quadrature_points, quadrature_weights, pointwise, boundary = sets
    return val.sample_fixture(val.FIXTURES[0], quadrature_points=quadrature_points,
                              quadrature_weights=quadrature_weights, pointwise_points=pointwise, boundary=boundary)


# ------------------------------------------------------------- positive control

def test_the_manufactured_solution_satisfies_every_criterion(sets):
    result = val.evaluate_fields(exact_fields(sets), grid_label="control")
    assert result["failedMustCriteria"] == []
    assert result["failedShouldCriteria"] == []
    metrics = {cid: entry["value"] for cid, entry in result["metrics"].items()}
    assert metrics["ACA-1"] < 1e-9 and metrics["ACA-3"] < 1e-12
    assert result["diagnostics"]["geometryId"] == geo.GEOMETRY["geometryId"]
    assert result["diagnostics"]["worstCell"]["radialBin"] in range(contract.RADIAL_BINS)
    assert len(result["diagnostics"]["cells"]) == contract.LOCALIZED_CELLS


def test_the_localized_value_is_the_quotient_of_its_own_components(sets):
    """ACA-9's label must name what it divides by: the RMS of the REFERENCE solution."""

    fixture = next(f for f in val.FIXTURES if f.name == "localizedHotspot")
    quadrature_points, quadrature_weights, pointwise, boundary = sets
    fields = val.sample_fixture(fixture, quadrature_points=quadrature_points,
                                quadrature_weights=quadrature_weights, pointwise_points=pointwise, boundary=boundary)
    result = val.evaluate_fields(fields, grid_label="hotspot")
    diagnostics = result["diagnostics"]
    quotient = diagnostics["worstCell"]["rms"] / diagnostics["referenceRmsPointwise"]
    assert result["metrics"]["ACA-9"]["value"] == pytest.approx(quotient, rel=1e-15)
    assert diagnostics["referenceRmsPointwise"] == pytest.approx(
        math.sqrt(math.fsum(ref.solution(x, y) ** 2 for x, y in pointwise) / len(pointwise)), rel=1e-15)


# ------------------------------------------------------------ negative controls

def test_every_geometry_defect_is_rejected_and_the_control_accepted(sets):
    quadrature_points, quadrature_weights, pointwise, boundary = sets
    verdicts = val.fixture_verdicts(quadrature_points=quadrature_points, quadrature_weights=quadrature_weights,
                                    pointwise_points=pointwise, boundary=boundary)
    assert {v["fixture"] for v in verdicts} == {f.name for f in val.FIXTURES}
    wrong = [v for v in verdicts if not v["verdictCorrect"]]
    assert not wrong, f"the validator disagreed with the ground truth on: {wrong}"
    assert len([v for v in verdicts if not v["mustBeAccepted"]]) == 9


@pytest.mark.parametrize(
    ("fixture_name", "expected_criterion"),
    [
        ("holeFilled", "ACA-3"),              # does not vanish on the inner circle
        ("wrongInnerRadius", "ACA-3"),
        ("wrongOuterRadius", "ACA-3"),
        ("wrongSourceSign", "ACA-4"),
        ("wrongInnerNormal", "ACA-6"),
        ("boundaryComponentSwap", "ACA-6"),
        ("derivativeSwap", "ACA-6"),
        ("localizedHotspot", "ACA-9"),
        ("radialOnly", "ACA-1"),
    ],
)
def test_each_defect_fails_the_criterion_that_is_supposed_to_see_it(fixture_name, expected_criterion, sets):
    quadrature_points, quadrature_weights, pointwise, boundary = sets
    fixture = next(f for f in val.FIXTURES if f.name == fixture_name)
    fields = val.sample_fixture(fixture, quadrature_points=quadrature_points,
                                quadrature_weights=quadrature_weights, pointwise_points=pointwise, boundary=boundary)
    result = val.evaluate_fields(fields, grid_label=fixture_name)
    assert expected_criterion in result["failedMustCriteria"], result["metrics"][expected_criterion]


def test_the_wrong_inner_normal_shows_up_in_the_flux_terms(sets):
    """The defect the flux identity exists for: the two components' contributions have opposite signs."""

    quadrature_points, quadrature_weights, pointwise, boundary = sets
    correct = val.evaluate_fields(exact_fields(sets), grid_label="control")["diagnostics"]
    fixture = next(f for f in val.FIXTURES if f.name == "wrongInnerNormal")
    flipped = val.evaluate_fields(
        val.sample_fixture(fixture, quadrature_points=quadrature_points, quadrature_weights=quadrature_weights,
                           pointwise_points=pointwise, boundary=boundary), grid_label="flipped")["diagnostics"]
    assert correct["boundary"]["inner"]["flux"] == pytest.approx(-flipped["boundary"]["inner"]["flux"], rel=1e-12)
    assert correct["boundary"]["outer"]["flux"] == pytest.approx(flipped["boundary"]["outer"]["flux"], rel=1e-12)
    forcing_integral = geo.integrate([ref.forcing(x, y) for x, y in quadrature_points], quadrature_weights)
    assert abs(correct["integrals"]["fluxTotal"] + forcing_integral) / abs(forcing_integral) < 1e-9
    assert abs(flipped["integrals"]["fluxTotal"] + forcing_integral) / abs(forcing_integral) > 0.1


# --------------------------------------------------------- evidence validation

def test_a_node_in_the_hole_is_refused_before_any_arithmetic(sets):
    quadrature_points, quadrature_weights, pointwise, boundary = sets
    fields = exact_fields(sets)
    polluted = list(fields.pointwise_points)
    polluted[3] = (0.05, 0.02)                      # inside the hole
    broken = val.FieldsAnnulus(
        quadrature_points=fields.quadrature_points, quadrature_weights=fields.quadrature_weights,
        u_quadrature=fields.u_quadrature, ux_quadrature=fields.ux_quadrature, uy_quadrature=fields.uy_quadrature,
        uxx_quadrature=fields.uxx_quadrature, uyy_quadrature=fields.uyy_quadrature,
        pointwise_points=polluted, u_pointwise=fields.u_pointwise, boundary=fields.boundary)
    with pytest.raises(ValidationInputError, match="inHole"):
        val.evaluate_fields(broken, grid_label="polluted")


def test_boundary_nodes_handed_to_the_wrong_component_are_refused(sets):
    quadrature_points, quadrature_weights, pointwise, boundary = sets
    fields = exact_fields(sets)
    swapped = {geo.OUTER: fields.boundary[geo.INNER], geo.INNER: fields.boundary[geo.OUTER]}
    broken = val.FieldsAnnulus(
        quadrature_points=fields.quadrature_points, quadrature_weights=fields.quadrature_weights,
        u_quadrature=fields.u_quadrature, ux_quadrature=fields.ux_quadrature, uy_quadrature=fields.uy_quadrature,
        uxx_quadrature=fields.uxx_quadrature, uyy_quadrature=fields.uyy_quadrature,
        pointwise_points=fields.pointwise_points, u_pointwise=fields.u_pointwise, boundary=swapped)
    with pytest.raises(ValidationInputError, match="expected"):
        val.evaluate_fields(broken, grid_label="swapped")


def test_a_quadrature_that_does_not_integrate_the_annulus_is_refused(sets):
    fields = exact_fields(sets)
    broken = val.FieldsAnnulus(
        quadrature_points=fields.quadrature_points,
        quadrature_weights=[w * 1.01 for w in fields.quadrature_weights],
        u_quadrature=fields.u_quadrature, ux_quadrature=fields.ux_quadrature, uy_quadrature=fields.uy_quadrature,
        uxx_quadrature=fields.uxx_quadrature, uyy_quadrature=fields.uyy_quadrature,
        pointwise_points=fields.pointwise_points, u_pointwise=fields.u_pointwise, boundary=fields.boundary)
    with pytest.raises(ValidationInputError, match="annulus area"):
        val.evaluate_fields(broken, grid_label="rescaled")


def test_a_partition_with_empty_cells_is_refused(sets):
    """A pointwise grid too coarse for the 64 equal-area cells cannot judge the localized criterion."""

    quadrature_points, quadrature_weights, _pointwise, boundary = sets
    coarse = [geo.to_cartesian(geo.radius_of_area_fraction(t), theta)
              for t in (0.2, 0.8) for theta in (0.1, 2.0, 4.0)]
    fields = val.sample_fixture(val.FIXTURES[0], quadrature_points=quadrature_points,
                                quadrature_weights=quadrature_weights, pointwise_points=coarse, boundary=boundary)
    with pytest.raises(ValidationInputError, match="equal-area cells"):
        val.evaluate_fields(fields, grid_label="coarse")


def test_non_finite_evidence_is_refused(sets):
    fields = exact_fields(sets)
    values = list(fields.u_quadrature)
    values[0] = float("nan")
    broken = val.FieldsAnnulus(
        quadrature_points=fields.quadrature_points, quadrature_weights=fields.quadrature_weights,
        u_quadrature=values, ux_quadrature=fields.ux_quadrature, uy_quadrature=fields.uy_quadrature,
        uxx_quadrature=fields.uxx_quadrature, uyy_quadrature=fields.uyy_quadrature,
        pointwise_points=fields.pointwise_points, u_pointwise=fields.u_pointwise, boundary=fields.boundary)
    with pytest.raises(ValidationInputError, match="finite"):
        val.evaluate_fields(broken, grid_label="nan")
