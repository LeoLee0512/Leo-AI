"""Independent second-order finite-difference solver for the annular Poisson problem.

Gate 2b needs a numerical reference that shares nothing with the model under
test: no autograd, no PINN residual helper, no PINN model, no shared derivative
code. Only the *mathematical* specification (the frozen forcing) is shared --
that is the point of comparison, not a shortcut.

The annulus is a product domain in polar coordinates, so the natural
discretisation is a uniform (r, theta) grid with Dirichlet data on both circles
and periodicity in theta:

    u(a, theta) = u(1, theta) = 0,        u(r, theta + 2 pi) = u(r, theta)

The Laplacian is discretised in conservative (flux) form,

    Lap u = (1/r) d/dr ( r du/dr ) + (1/r^2) d^2u/dtheta^2

    (Lap u)_{i,j} ~ [ r_{i+1/2} (u_{i+1,j} - u_{i,j}) - r_{i-1/2} (u_{i,j} - u_{i-1,j}) ] / (r_i dr^2)
                    + (u_{i,j+1} - 2 u_{i,j} + u_{i,j-1}) / (r_i^2 dtheta^2)

which is second order and, after multiplying the equation by r_i, symmetric
positive definite -- so the linear system is solved matrix-free by conjugate
gradients. Nothing but numpy is imported: the reproduction environment holds
torch and numpy only, and a solver is not a reason to contaminate it.
"""

from __future__ import annotations

import math
from typing import Any, Callable

#: The frozen radii of the problem, restated here ON PURPOSE.
#:
#: ``scientific_reference/`` may not import anything from ``pinn`` (the repository's
#: independence rule, asserted by tests/pinn/test_scientific_validation.py): an
#: independent reference that imports the model side is not independent. The two
#: definitions are kept equal by a test that compares them, which is the coupling
#: that belongs in a test rather than in an import.
INNER_RADIUS = 0.35
OUTER_RADIUS = 1.0


def _numpy():
    """numpy is imported lazily so the module can be read (and its independence checked)
    in the governance virtualenv, which has no numpy."""

    import numpy as np

    return np


def grid(radial_cells: int, angular_cells: int, *, inner: float = INNER_RADIUS,
         outer: float = OUTER_RADIUS) -> dict[str, Any]:
    """Nodes of the uniform polar grid; interior radial nodes carry the unknowns."""

    np = _numpy()

    if radial_cells < 2 or angular_cells < 4:
        raise ValueError("the polar grid needs at least 2 radial cells and 4 angular cells")
    dr = (outer - inner) / radial_cells
    dtheta = 2.0 * math.pi / angular_cells
    r = inner + dr * np.arange(radial_cells + 1)
    theta = dtheta * np.arange(angular_cells)
    return {"r": r, "theta": theta, "dr": dr, "dtheta": dtheta,
            "radialCells": radial_cells, "angularCells": angular_cells,
            "inner": inner, "outer": outer}


def _operator(u, g: dict[str, Any]):
    """(-Lap u) * r on the interior nodes, in conservative form (symmetric positive definite)."""

    np = _numpy()
    r = g["r"]
    dr, dtheta = g["dr"], g["dtheta"]
    interior = r[1:-1][:, None]                      # (nr-1, 1)
    padded = np.zeros((u.shape[0] + 2, u.shape[1]))  # Dirichlet zeros on both circles
    padded[1:-1] = u
    r_plus = (r[1:-1] + r[2:])[:, None] * 0.5
    r_minus = (r[1:-1] + r[:-2])[:, None] * 0.5
    radial = (r_plus * (padded[2:] - padded[1:-1]) - r_minus * (padded[1:-1] - padded[:-2])) / (dr * dr)
    angular = (np.roll(u, -1, axis=1) - 2.0 * u + np.roll(u, 1, axis=1)) / (interior * dtheta * dtheta)
    return -(radial + angular)


def solve(forcing: Callable[[float, float], float], radial_cells: int, angular_cells: int, *,
          inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS,
          tolerance: float = 1e-12, max_iterations: int = 20000) -> dict[str, Any]:
    """Solve -Lap u = f with zero Dirichlet data on both circles, matrix-free CG."""

    np = _numpy()
    g = grid(radial_cells, angular_cells, inner=inner, outer=outer)
    r, theta = g["r"], g["theta"]
    interior_r = r[1:-1]
    xs = interior_r[:, None] * np.cos(theta)[None, :]
    ys = interior_r[:, None] * np.sin(theta)[None, :]
    rhs = np.empty_like(xs)
    for i in range(xs.shape[0]):
        for j in range(xs.shape[1]):
            rhs[i, j] = forcing(float(xs[i, j]), float(ys[i, j]))
    rhs = rhs * interior_r[:, None]                  # the same r factor the operator carries

    u = np.zeros_like(rhs)
    residual = rhs - _operator(u, g)
    direction = residual.copy()
    rs_old = float(np.sum(residual * residual))
    scale = math.sqrt(float(np.sum(rhs * rhs))) or 1.0
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        a_direction = _operator(direction, g)
        denominator = float(np.sum(direction * a_direction))
        if denominator == 0.0:
            break
        alpha = rs_old / denominator
        u += alpha * direction
        residual -= alpha * a_direction
        rs_new = float(np.sum(residual * residual))
        if math.sqrt(rs_new) / scale < tolerance:
            break
        direction = residual + (rs_new / rs_old) * direction
        rs_old = rs_new
    final = math.sqrt(float(np.sum((rhs - _operator(u, g)) * (rhs - _operator(u, g))))) / scale
    return {"grid": g, "u": u, "x": xs, "y": ys, "iterations": iterations,
            "relativeResidual": final, "converged": final < max(tolerance * 10.0, 1e-10)}


def error_against(solution: Callable[[float, float], float], result: dict[str, Any]) -> dict[str, float]:
    """Relative L2 and L-infinity of the FD solution against a closed-form solution."""

    np = _numpy()
    xs, ys, u = result["x"], result["y"], result["u"]
    exact = np.empty_like(u)
    for i in range(u.shape[0]):
        for j in range(u.shape[1]):
            exact[i, j] = solution(float(xs[i, j]), float(ys[i, j]))
    difference = u - exact
    denominator = float(np.sqrt(np.mean(exact * exact)))
    return {"relL2": float(np.sqrt(np.mean(difference * difference))) / denominator,
            "maxAbs": float(np.max(np.abs(difference))),
            "referenceRms": denominator}


def refinement_diagnostic(forcing: Callable[[float, float], float], solution: Callable[[float, float], float],
                          levels: tuple[tuple[int, int], ...] = ((16, 64), (32, 128), (64, 256)),
                          *, inner: float = INNER_RADIUS, outer: float = OUTER_RADIUS) -> dict[str, Any]:
    """Three refinements and the observed order p ~ log2(e_coarse / e_fine).

    Each level halves both dr and dtheta, so a second-order scheme must quarter
    the error. A result that is not close to 2 is reported as it is: the point of
    an independent reference is to notice when it disagrees.
    """

    records = []
    for radial_cells, angular_cells in levels:
        result = solve(forcing, radial_cells, angular_cells, inner=inner, outer=outer)
        error = error_against(solution, result)
        records.append({"radialCells": radial_cells, "angularCells": angular_cells,
                        "relL2": error["relL2"], "maxAbs": error["maxAbs"],
                        "iterations": result["iterations"], "relativeResidual": result["relativeResidual"],
                        "converged": result["converged"]})
    orders = [math.log2(records[i]["relL2"] / records[i + 1]["relL2"]) for i in range(len(records) - 1)]
    return {"levels": records, "observedOrders": orders,
            "method": "second-order conservative finite differences in polar coordinates, matrix-free CG",
            "independence": "no autograd, no PINN model, no PINN residual helper; only the frozen forcing is shared",
            "dependencies": ["numpy"]}


def min_eigenvalue(radial_cells: int = 24, angular_cells: int = 96, *, inner: float = INNER_RADIUS,
                   outer: float = OUTER_RADIUS, iterations: int = 60) -> dict[str, Any]:
    """Smallest eigenvalue of the discrete operator, by inverse power iteration.

    The weighted operator ``B u = r (-Lap u)`` is symmetric positive definite on the
    interior nodes with zero Dirichlet data on both circles; a positive smallest
    eigenvalue is the SPD witness the physics gate asks for, computed here on the
    independent reference rather than on anything the model touched. The Rayleigh
    quotient uses the same r weight that makes B symmetric.
    """

    np = _numpy()
    g = grid(radial_cells, angular_cells, inner=inner, outer=outer)
    weight = g["r"][1:-1][:, None]
    rng = np.random.default_rng(20260917)
    v = rng.standard_normal((radial_cells - 1, angular_cells))
    value = float("nan")
    for _ in range(iterations):
        rhs = v * weight
        u = np.zeros_like(rhs)
        residual = rhs - _operator(u, g)
        direction = residual.copy()
        rs_old = float(np.sum(residual * residual))
        for _cg in range(5000):
            a_direction = _operator(direction, g)
            denominator = float(np.sum(direction * a_direction))
            if denominator == 0.0:
                break
            alpha = rs_old / denominator
            u += alpha * direction
            residual -= alpha * a_direction
            rs_new = float(np.sum(residual * residual))
            if math.sqrt(rs_new) <= 1e-12 * math.sqrt(float(np.sum(rhs * rhs)) + 1e-300):
                break
            direction = residual + (rs_new / rs_old) * direction
            rs_old = rs_new
        norm = math.sqrt(float(np.sum(u * u * weight)))
        if norm == 0.0:
            break
        v = u / norm
        value = float(np.sum(v * _operator(v, g))) / float(np.sum(v * v * weight))
    return {"lambdaMin": value, "radialCells": radial_cells, "angularCells": angular_cells,
            "method": "inverse power iteration on the weighted polar operator (CG inner solves)"}
