"""Independent second-order finite-difference baseline for Poisson-2D v1.0.

    -(u_xx + u_yy) = f  on (0,1)^2,  u = 0 on the boundary

Five-point stencil on a uniform (n x n) interval grid, solved matrix-free with
conjugate gradients (the discrete operator is symmetric positive definite, so
CG converges to the discrete solution; no dense factorisation and no external
linear-algebra package beyond NumPy).  This module knows nothing about neural
networks and does not import the PINN code: it is the Evidence-Level-B
reference of Gate 2b, checked against the analytic solution's observed order of
convergence p ~ 2.  It never replaces the analytic reference.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

REFINEMENT_SEQUENCE: tuple[int, ...] = (8, 16, 32, 64)
CG_TOLERANCE = 1e-13
CG_MAX_ITERATIONS = 20000


@dataclass(frozen=True)
class FdmSolution:
    intervals: int
    h: float
    iterations: int
    residual: float
    interior_max_error: float
    interior_rms_error: float


def _forcing_grid(n: int):
    import numpy as np

    h = 1.0 / n
    idx = np.arange(1, n, dtype=np.float64) * h
    xx, yy = np.meshgrid(idx, idx, indexing="ij")
    return xx, yy, 2.0 * (math.pi ** 2) * np.sin(math.pi * xx) * np.sin(math.pi * yy), h


def _apply_operator(u, h: float):
    """(4 u_ij - u_{i-1,j} - u_{i+1,j} - u_{i,j-1} - u_{i,j+1}) / h^2 with zero Dirichlet data."""

    import numpy as np

    padded = np.zeros((u.shape[0] + 2, u.shape[1] + 2), dtype=np.float64)
    padded[1:-1, 1:-1] = u
    return (4.0 * u - padded[:-2, 1:-1] - padded[2:, 1:-1] - padded[1:-1, :-2] - padded[1:-1, 2:]) / (h * h)


def solve_poisson(n: int) -> FdmSolution:
    """Solve the discrete system on ``n`` intervals per axis and compare with u*."""

    import numpy as np

    if n < 2:
        raise ValueError("at least two intervals per axis are required")
    xx, yy, f, h = _forcing_grid(n)
    u = np.zeros_like(f)
    r = f - _apply_operator(u, h)
    p = r.copy()
    rs = float(np.sum(r * r))
    norm_b = math.sqrt(float(np.sum(f * f)))
    iterations = 0
    for iterations in range(1, CG_MAX_ITERATIONS + 1):
        ap = _apply_operator(p, h)
        denominator = float(np.sum(p * ap))
        if denominator <= 0.0:
            raise ArithmeticError("the five-point operator is not positive definite on this grid")
        alpha = rs / denominator
        u += alpha * p
        r -= alpha * ap
        rs_new = float(np.sum(r * r))
        if math.sqrt(rs_new) <= CG_TOLERANCE * norm_b:
            rs = rs_new
            break
        p = r + (rs_new / rs) * p
        rs = rs_new
    exact = np.sin(math.pi * xx) * np.sin(math.pi * yy)
    error = np.abs(u - exact)
    return FdmSolution(
        intervals=n, h=h, iterations=iterations, residual=math.sqrt(rs) / norm_b,
        interior_max_error=float(np.max(error)),
        interior_rms_error=float(math.sqrt(float(np.mean(error * error)))),
    )


def stiffness_min_eigenvalue(n: int) -> float:
    """Smallest eigenvalue of the five-point operator on ``n`` intervals (closed form, SPD witness)."""

    h = 1.0 / n
    return 8.0 / (h * h) * math.sin(math.pi * h / 2.0) ** 2


def refinement_diagnostic(sequence: Sequence[int] = REFINEMENT_SEQUENCE) -> dict:
    """Errors, observed orders and the component verdict; absent evidence stays absent."""

    sequence = tuple(sequence)
    if not sequence or len(set(sequence)) != len(sequence):
        raise ValueError("refinement sequence must be nonempty and unique")
    solutions = tuple(solve_poisson(n) for n in sequence)
    errors = tuple(s.interior_max_error for s in solutions)
    orders = tuple(
        {"pair": [left.intervals, right.intervals], "order": math.log2(left.interior_max_error / right.interior_max_error)}
        for left, right in zip(solutions, solutions[1:])
        if right.intervals == 2 * left.intervals and left.interior_max_error > 0.0 and right.interior_max_error > 0.0
    )
    decreasing = len(errors) > 1 and all(right < left for left, right in zip(errors, errors[1:]))
    measured = [item["order"] for item in orders]
    orders_in_range = bool(measured) and all(1.8 <= value <= 2.2 for value in measured)
    converged = all(s.residual <= 1e-10 for s in solutions)
    reasons = []
    if not decreasing:
        reasons.append("interior max errors are not strictly decreasing under refinement")
    if not orders_in_range:
        reasons.append("observed orders are not all inside [1.8, 2.2]")
    if not converged:
        reasons.append("a linear solve did not reach the CG tolerance")
    return {
        "scheme": "five-point second-order finite differences, matrix-free conjugate gradients",
        "equationBinding": "-(u_xx+u_yy)=2*pi^2*sin(pi*x)*sin(pi*y); u=0 on the boundary of (0,1)^2",
        "sequence": list(sequence),
        "solutions": [
            {"intervals": s.intervals, "h": s.h, "iterations": s.iterations, "linearResidual": s.residual,
             "interior_max_error": s.interior_max_error, "interior_rms_error": s.interior_rms_error}
            for s in solutions
        ],
        "orders": [dict(item) for item in orders],
        "errorsStrictlyDecreasing": decreasing,
        "ordersInRange": orders_in_range,
        "linearSolvesConverged": converged,
        "componentCriteriaSatisfied": bool(decreasing and orders_in_range and converged),
        "reasons": reasons,
        "stiffnessMinEigenvalue": {str(n): stiffness_min_eigenvalue(n) for n in sequence},
    }
