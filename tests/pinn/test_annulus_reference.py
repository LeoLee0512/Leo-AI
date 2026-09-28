"""The independent numerical reference and the sampler (Geometry Lift 1).

These need numpy (the polar finite-difference solver, the area-uniform sampler) or
torch (autograd against the frozen analytic source), so the governance virtualenv
skips them; ``experiments/annulus/verify_tests_under_torch.py`` runs the same
functions under the training interpreter and records the result.
"""

import math

import pytest

from pinn.geometry import annulus as geo
from pinn.reference import analytic_annulus as ref


def test_the_area_uniform_sampler_draws_inside_the_annulus_only():
    pytest.importorskip("numpy")
    points = geo.uniform_area_points(20000, 20260917)
    geo.assert_interior(points, label="sampler")
    assert len(points) == 20000


def test_the_sampler_is_uniform_in_area_not_in_radius():
    """Implementation validation, never a scientific claim (Geometry Lift 1 section 8)."""

    numpy = pytest.importorskip("numpy")
    points = geo.uniform_area_points(40000, 20260918)
    report = geo.radial_uniformity(points, bins=10)
    assert report["meanAreaFraction"] == pytest.approx(0.5, abs=0.01)
    # Kolmogorov: the 99.9 % band for n = 40000 is about 1.95/sqrt(n) = 0.0098
    assert report["kolmogorovStatistic"] < 0.0098
    expected = report["expectedPerBin"]
    assert max(abs(count - expected) for count in report["bins"]) < 5.0 * math.sqrt(expected)

    radii = [geo.radius(p) for p in points]
    assert min(radii) > geo.INNER_RADIUS and max(radii) < geo.OUTER_RADIUS
    # the same sample drawn r-uniformly would fail the check above
    rng = numpy.random.default_rng(7)
    r_uniform = [geo.to_cartesian(geo.INNER_RADIUS + (geo.OUTER_RADIUS - geo.INNER_RADIUS) * float(u),
                                  2 * math.pi * float(v)) for u, v in rng.random((40000, 2))]
    assert geo.radial_uniformity(r_uniform)["kolmogorovStatistic"] > 0.05


def test_the_sampler_is_reproducible_from_its_seed():
    pytest.importorskip("numpy")
    first = geo.uniform_area_points(500, 4242)
    second = geo.uniform_area_points(500, 4242)
    other = geo.uniform_area_points(500, 4243)
    assert first == second
    assert first != other


def test_autograd_reproduces_the_frozen_analytic_source():
    """Verification B: -Lap u* - f must vanish to machine tolerance on independent points.

    The forcing is written out analytically and the derivatives are taken by
    torch: a single wrong helper cannot certify itself.
    """

    torch = pytest.importorskip("torch")
    pytest.importorskip("numpy")
    torch.set_default_dtype(torch.float64)
    points = geo.uniform_area_points(2000, 909090)
    xy = torch.tensor(points, dtype=torch.float64, requires_grad=True)
    x, y = xy[:, 0], xy[:, 1]
    s = x * x + y * y
    u = (1.0 - s) * (s - ref.A ** 2) * (1.0 + 0.2 * torch.sin(math.pi * x) * torch.cos(2 * math.pi * y)
                                        + 0.1 * x - 0.1 * y)
    grad, = torch.autograd.grad(u.sum(), xy, create_graph=True)
    uxx, = torch.autograd.grad(grad[:, 0].sum(), xy, create_graph=True)
    uyy, = torch.autograd.grad(grad[:, 1].sum(), xy, create_graph=True)
    laplacian = (uxx[:, 0] + uyy[:, 1]).detach()
    forcing = torch.tensor([ref.forcing(px, py) for px, py in points], dtype=torch.float64)
    residual = (-laplacian - forcing).abs().max().item()
    assert residual < 1e-12, residual

    analytic_gradient = torch.tensor([ref.gradient(px, py) for px, py in points], dtype=torch.float64)
    assert (grad.detach() - analytic_gradient).abs().max().item() < 1e-12


def test_the_polar_finite_difference_reference_is_second_order():
    """Gate 2b: an independent solver, three refinements, observed order near 2."""

    pytest.importorskip("numpy")
    from scientific_reference import annulus_polar_fdm as fdm

    diagnostic = fdm.refinement_diagnostic(ref.forcing, ref.solution)
    assert [level["converged"] for level in diagnostic["levels"]] == [True, True, True]
    errors = [level["relL2"] for level in diagnostic["levels"]]
    assert errors == sorted(errors, reverse=True), "refinement must reduce the error"
    for order in diagnostic["observedOrders"]:
        assert 1.8 <= order <= 2.2, diagnostic["observedOrders"]
    assert diagnostic["dependencies"] == ["numpy"], "the reference must not pull in a new dependency"


def test_the_finite_difference_solver_shares_no_code_with_the_model():
    """Independence is a property of what the module IMPORTS, so the imports are read.

    Checking the raw text would be fooled by the docstring, which legitimately says
    the words "autograd" and "PINN" while explaining that it uses neither.
    """

    import ast
    from pathlib import Path

    source = (Path(__file__).resolve().parents[2] / "scientific_reference/annulus_polar_fdm.py").read_text(
        encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    for forbidden in ("torch", "pinn.experiments", "pinn.experiments2d", "pinn.experiments_annulus",
                      "pinn.validation", "pinn.reference.analytic_annulus"):
        assert not any(name == forbidden or name.startswith(forbidden + ".") for name in imported), (
            f"the independent reference must not import {forbidden}: {sorted(imported)}")
    assert "numpy" in imported
    # the repository rule is stricter than "no model code": scientific_reference/ imports
    # nothing from pinn at all, so the radii are restated there and pinned equal here
    assert not [name for name in imported if name.startswith("pinn")], sorted(imported)
    # the radii are restated in the reference; read them from its syntax tree rather than
    # importing it, so this check needs no numpy and stays in the governance suite
    literals = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, float):
                literals[node.targets[0].id] = node.value.value
    assert literals.get("INNER_RADIUS") == geo.INNER_RADIUS
    assert literals.get("OUTER_RADIUS") == geo.OUTER_RADIUS


def test_the_finite_difference_solution_satisfies_the_boundary_conditions():
    pytest.importorskip("numpy")
    from scientific_reference import annulus_polar_fdm as fdm

    result = fdm.solve(ref.forcing, 24, 96)
    assert result["converged"]
    radii = result["grid"]["r"]
    assert radii[0] == pytest.approx(geo.INNER_RADIUS) and radii[-1] == pytest.approx(geo.OUTER_RADIUS)
    # the unknowns are the interior radial nodes only: the Dirichlet values are structural
    assert result["u"].shape == (len(radii) - 2, result["grid"]["angularCells"])
    error = fdm.error_against(ref.solution, result)
    assert error["relL2"] < 2e-3
