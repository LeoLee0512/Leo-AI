"""2D reference, trusted validator, component-separated AD, hard BC on four edges, symmetry (PART 22)."""

import math

import pytest

from pinn.governance.poisson2d_contract import CRITERIA, THRESHOLD_SOURCES
from pinn.reference import analytic_poisson2d as reference
from pinn.validation import poisson2d as validator


def test_manufactured_solution_satisfies_the_frozen_equation_and_boundary_data():
    for x, y in [(0.13, 0.71), (0.5, 0.5), (0.9, 0.02), (0.33, 0.33)]:
        assert abs(-(reference.dxx(x, y) + reference.dyy(x, y)) - reference.forcing(x, y)) < 1e-12
        assert abs(reference.laplacian(x, y) + reference.forcing(x, y)) < 1e-12
    for t in [0.0, 0.25, 0.5, 0.77, 1.0]:
        assert abs(reference.solution(0.0, t)) < 1e-15
        assert abs(reference.solution(1.0, t)) < 1e-15
        assert abs(reference.solution(t, 0.0)) < 1e-15
        assert abs(reference.solution(t, 1.0)) < 1e-15
    assert abs(reference.INTEGRAL_U - 4.0 / math.pi ** 2) < 1e-15
    assert abs(reference.INTEGRAL_F - 8.0) < 1e-12
    assert abs(reference.DIRICHLET_ENERGY - math.pi ** 2 / 2.0) < 1e-12
    assert reference.solution(0.3, 0.8) == pytest.approx(reference.solution(0.8, 0.3))


def test_every_criterion_declares_a_dimension_verdict_and_a_threshold_source():
    for criterion_id, threshold, level in CRITERIA:
        assert level in ("MUST", "SHOULD") and threshold > 0
        source = THRESHOLD_SOURCES[criterion_id]
        assert source["dimensionVerdict"] and source["source"]
        assert any(word in source["source"] for word in ("1D inherited", "numerical reference", "stability reasoning", "protocol rule"))


def grids():
    from pinn.experiments2d import datasets2d as ds

    quadrature, weights = ds.gauss_legendre_square(16)
    pointwise = ds.cgl_interior_square(26)
    boundary, boundary_weights = ds.boundary_nodes(16)
    return quadrature, weights, pointwise, boundary, boundary_weights


def test_validator_accepts_the_analytic_control_and_rejects_every_corrupted_fixture():
    pytest.importorskip("numpy")
    quadrature, weights, pointwise, boundary, boundary_weights = grids()
    verdicts = validator.fixture_verdicts(quadrature_points=quadrature, quadrature_weights=weights,
                                          pointwise_points=pointwise, boundary_points=boundary,
                                          boundary_weights=boundary_weights)
    assert verdicts["ANALYTIC_CONTROL"] is True
    assert all(value is False for key, value in verdicts.items() if key != "ANALYTIC_CONTROL")
    assert "DERIVATIVE_INCONSISTENCY" in verdicts, "the reported second derivatives must be wired into AC2D-4"


def test_validator_rejects_malformed_evidence_instead_of_coercing_it():
    pytest.importorskip("numpy")
    quadrature, weights, pointwise, boundary, boundary_weights = grids()
    fields = validator.sample_fixture(validator.FIXTURES[0], quadrature_points=quadrature, quadrature_weights=weights,
                                      pointwise_points=pointwise, boundary_points=boundary, boundary_weights=boundary_weights)
    broken = validator.Fields2D(**{**fields.__dict__, "quadrature_weights": [w * 2 for w in weights]})
    with pytest.raises(validator.ValidationInputError):
        validator.evaluate_fields(broken, grid_label="broken-weights")
    nan_fields = validator.Fields2D(**{**fields.__dict__, "u_pointwise": [float("nan")] * len(pointwise)})
    with pytest.raises(validator.ValidationInputError):
        validator.evaluate_fields(nan_fields, grid_label="nan")
    off_boundary = validator.Fields2D(**{**fields.__dict__, "boundary_points": [(0.5, 0.5)] * len(boundary)})
    with pytest.raises(validator.ValidationInputError):
        validator.evaluate_fields(off_boundary, grid_label="interior-boundary")


def test_localized_error_is_detected_when_the_global_norm_still_passes():
    pytest.importorskip("numpy")
    quadrature, weights, pointwise, boundary, boundary_weights = grids()
    base = validator.sample_fixture(validator.FIXTURES[0], quadrature_points=quadrature, quadrature_weights=weights,
                                    pointwise_points=pointwise, boundary_points=boundary, boundary_weights=boundary_weights)
    hotspot = list(base.u_pointwise)
    touched = 0
    for index, (x, y) in enumerate(pointwise):
        if 0.125 <= x < 0.25 and 0.125 <= y < 0.25:          # one 8 x 8 tile
            hotspot[index] += 5e-3
            touched += 1
    assert touched > 0
    spotted = validator.evaluate_fields(validator.Fields2D(**{**base.__dict__, "u_pointwise": hotspot}), grid_label="hotspot")
    assert "AC2D-9" in spotted["failedMustCriteria"], "a single-tile hotspot must fail the localized criterion"
    assert spotted["metrics"]["AC2D-1"]["criterionSatisfied"], "the quadrature norm is untouched by the pointwise hotspot"
    assert spotted["diagnostics"]["worstTile"]["xRange"] == [0.125, 0.25]
    assert spotted["diagnostics"]["tileRatioMaxOverMedian"] > 1.0


def test_autograd_gives_each_second_derivative_component_separately():
    torch = pytest.importorskip("torch")
    from pinn.experiments2d import pinn_torch2d as pinn2d

    class Probe(torch.nn.Module):
        """w(x, y) = sin(2 pi x) sin(pi y): w_xx = -4 pi^2 w, w_yy = -pi^2 w (they must not be exchanged)."""

        def forward(self, xy):
            return torch.sin(2 * math.pi * xy[:, 0:1]) * torch.sin(math.pi * xy[:, 1:2])

    points = [(0.21, 0.37), (0.55, 0.62), (0.81, 0.11)]
    fld = pinn2d.fields(Probe(), points)
    for (x, y), u, uxx, uyy in zip(points, fld["u"], fld["uxx"], fld["uyy"]):
        assert uxx == pytest.approx(-(2 * math.pi) ** 2 * u, abs=1e-9)
        assert uyy == pytest.approx(-(math.pi ** 2) * u, abs=1e-9)
        assert abs(uxx - uyy) > 1.0, "an x/y swap in the operator must be detectable on this probe"
    laplacian = [a + b for a, b in zip(fld["uxx"], fld["uyy"])]
    assert all(value == pytest.approx(-5 * math.pi ** 2 * u, abs=1e-9) for value, u in zip(laplacian, fld["u"]))


def test_residual_operator_vanishes_on_the_manufactured_solution():
    torch = pytest.importorskip("torch")
    from pinn.experiments2d import pinn_torch2d as pinn2d

    class Exact(torch.nn.Module):
        def forward(self, xy):
            return torch.sin(math.pi * xy[:, 0:1]) * torch.sin(math.pi * xy[:, 1:2])

    points = [(0.17, 0.44), (0.62, 0.29), (0.5, 0.5)]
    fld = pinn2d.fields(Exact(), points)
    for (x, y), uxx, uyy in zip(points, fld["uxx"], fld["uyy"]):
        assert abs(-(uxx + uyy) - reference.forcing(x, y)) < 1e-9


def test_hard_parameterization_vanishes_on_all_four_edges_and_rescales_with_the_domain():
    pytest.importorskip("torch")
    pytest.importorskip("numpy")
    from pinn.experiments2d import datasets2d as ds
    from pinn.experiments2d import pinn_torch2d as pinn2d

    config = {"configId": "unit", "network": {"hiddenLayers": 2, "width": 8, "activation": "tanh",
                                              "outputParameterization": "x(1-x)y(1-y)N"},
              "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": 1, "batchSize": 4, "threads": 1},
              "lossWeights": {"pde": 1.0}, "sampling": {"poolSize": 8, "poolSeed": 1, "collocationCount": 4}}
    model = pinn2d.build_model(config, 7)
    edge_points, _ = ds.boundary_nodes(8)
    assert max(abs(v) for v in pinn2d.values(model, edge_points)) == 0.0
    per_edge = {"x0": [], "x1": [], "y0": [], "y1": []}
    for (x, y), value in zip(edge_points, pinn2d.values(model, edge_points)):
        key = "x0" if x == 0.0 else "x1" if x == 1.0 else "y0" if y == 0.0 else "y1"
        per_edge[key].append(abs(value))
    assert all(edge and max(edge) == 0.0 for edge in per_edge.values())
    # P8: on the rescaled square (0, L)^2 the parameterization must vanish on the rescaled edges (1D Tier-1 harness defect)
    scaled = pinn2d.build_model(config, 7, domain_length=2.0)
    scaled_edges = [(0.0, 1.3), (2.0, 0.4), (0.7, 0.0), (1.1, 2.0)]
    values = pinn2d.values(scaled, scaled_edges)
    assert max(abs(v) for v in values) == 0.0


def test_swap_symmetry_metric_separates_a_symmetric_from_an_asymmetric_field():
    torch = pytest.importorskip("torch")
    from pinn.experiments2d import pinn_torch2d as pinn2d

    class Symmetric(torch.nn.Module):
        def forward(self, xy):
            return torch.sin(math.pi * xy[:, 0:1]) * torch.sin(math.pi * xy[:, 1:2])

    class Asymmetric(torch.nn.Module):
        def forward(self, xy):
            return torch.sin(2 * math.pi * xy[:, 0:1]) * torch.sin(math.pi * xy[:, 1:2])

    points = [(0.21, 0.37), (0.55, 0.62), (0.81, 0.11), (0.4, 0.9)]
    swapped = [(y, x) for x, y in points]
    for model, expect_symmetric in ((Symmetric(), True), (Asymmetric(), False)):
        direct = pinn2d.values(model, points)
        mirrored = pinn2d.values(model, swapped)
        defect = max(abs(a - b) for a, b in zip(direct, mirrored))
        assert (defect < 1e-15) is expect_symmetric


def test_five_point_fdm_reference_is_second_order():
    pytest.importorskip("numpy")
    from scientific_reference.poisson2d_fdm import refinement_diagnostic, stiffness_min_eigenvalue

    diagnostic = refinement_diagnostic((8, 16, 32))
    assert diagnostic["componentCriteriaSatisfied"] is True
    assert diagnostic["errorsStrictlyDecreasing"] and diagnostic["ordersInRange"]
    assert all(1.8 <= entry["order"] <= 2.2 for entry in diagnostic["orders"])
    assert stiffness_min_eigenvalue(64) > 0.0
