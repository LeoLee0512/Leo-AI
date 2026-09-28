"""Independent three-point Poisson reference, with explicit refinement evidence.

This module contains no model, training, governance or PINN imports. Its results
are baseline-component diagnostics, never a scientific Gate or accuracy claim.
The FDM values must not replace the analytic reference in AC-1 through AC-8.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable, Sequence


REFINEMENT_SEQUENCE = (32, 64, 128, 256, 512, 1024, 2048)


def exact_solution(x: float) -> float:
    return math.sin(math.pi * x)


def source_term(x: float) -> float:
    return math.pi * math.pi * math.sin(math.pi * x)


@dataclass(frozen=True)
class FdmSolution:
    intervals: int
    spacing: float
    coordinates: tuple[float, ...]
    values: tuple[float, ...]
    interior_max_error: float
    discrete_residual_max: float


def solve_poisson(
    intervals: int,
    *,
    forcing: Callable[[float], float] = source_term,
    boundary: tuple[float, float] = (0.0, 0.0),
) -> FdmSolution:
    """Solve (-u[i-1]+2*u[i]-u[i+1])/h**2=f[i] by Thomas elimination.

Boundary and forcing overrides exist for rejection diagnostics. Error remains
relative to the candidate problem's sin(pi*x), even for a deliberately bad BVP.
"""
    if type(intervals) is not int or intervals < 2:
        raise ValueError("intervals must be an integer >= 2")
    if len(boundary) != 2 or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in boundary
    ):
        raise ValueError("boundary must contain two finite real values")
    h = 1.0 / intervals
    points = tuple(i / intervals for i in range(intervals + 1))
    source = tuple(forcing(x) for x in points[1:-1])
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in source
    ):
        raise ValueError("forcing returned a non-finite or non-real value")
    diagonal = [2.0] * (intervals - 1)
    rhs = [h * h * float(value) for value in source]
    rhs[0] += boundary[0]
    rhs[-1] += boundary[1]
    # The off-diagonals are both -1; eliminate without using an analytic inverse.
    for i in range(1, intervals - 1):
        factor = -1.0 / diagonal[i - 1]
        diagonal[i] += factor
        rhs[i] -= factor * rhs[i - 1]
    interior = [0.0] * (intervals - 1)
    interior[-1] = rhs[-1] / diagonal[-1]
    for i in range(intervals - 3, -1, -1):
        interior[i] = (rhs[i] + interior[i + 1]) / diagonal[i]
    values = (float(boundary[0]), *interior, float(boundary[1]))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("finite-difference solution contains non-finite values")
    error = max(abs(value - exact_solution(x)) for x, value in zip(points[1:-1], interior))
    residual = max(
        abs((-values[i - 1] + 2.0 * values[i] - values[i + 1]) / (h * h) - source[i - 1])
        for i in range(1, intervals)
    )
    if not math.isfinite(error) or not math.isfinite(residual):
        raise ValueError("finite-difference diagnostics contain non-finite values")
    return FdmSolution(intervals, h, points, values, error, residual)


def refinement_diagnostic(sequence: Sequence[int] = REFINEMENT_SEQUENCE) -> dict:
    """Measure errors/orders and preserve absent evidence instead of inventing p.

The exact candidate sequence is required to satisfy the component contract.
This is not formal Gate 2 execution and cannot change workflow state.
"""
    sequence = tuple(sequence)
    if not sequence or len(set(sequence)) != len(sequence):
        raise ValueError("refinement sequence must be nonempty and unique")
    solutions = tuple(solve_poisson(n) for n in sequence)
    errors = tuple(solution.interior_max_error for solution in solutions)
    orders = tuple(
        {
            "pair": [left.intervals, right.intervals],
            "order": math.log2(left.interior_max_error / right.interior_max_error),
        }
        for left, right in zip(solutions, solutions[1:])
        if right.intervals == 2 * left.intervals
        and left.interior_max_error > 0.0
        and right.interior_max_error > 0.0
    )
    missing_sequence = sequence != REFINEMENT_SEQUENCE
    decreasing = len(errors) > 1 and all(right < left for left, right in zip(errors, errors[1:]))
    final_pairs = list(zip(REFINEMENT_SEQUENCE[-5:-1], REFINEMENT_SEQUENCE[-4:]))
    measured = {tuple(item["pair"]): item["order"] for item in orders}
    final_orders_present = all(pair in measured for pair in final_pairs)
    final_orders_in_range = final_orders_present and all(
        1.8 <= measured[pair] <= 2.2 for pair in final_pairs
    )
    reasons = []
    if missing_sequence:
        reasons.append("required refinement sequence absent; convergence evidence incomplete")
    if len(sequence) == 1:
        reasons.append("a single grid has no observed convergence order")
    elif not decreasing:
        reasons.append("errors are not strictly decreasing across the sequence")
    if final_orders_present and not final_orders_in_range:
        reasons.append("measured final four orders are outside [1.8, 2.2]")
    return {
        "evaluationScope": "VALIDATOR_COMPONENT",
        "component": "independent_fdm_refinement",
        "workflowStatus": "NOT_APPLICABLE",
        "claimStatus": "NOT_APPLICABLE",
        "trainingApplicable": False,
        "acceptanceReference": False,
        "errorDefinition": "max_{i=1..N-1} |u_i - sin(pi*i/N)|",
        "orderDefinition": "log2(E(N)/E(2N))",
        "requiredSequence": list(REFINEMENT_SEQUENCE),
        "observedSequence": list(sequence),
        "orders": list(orders),
        "orderInterval": [1.8, 2.2],
        "finalPairCount": 4,
        "componentCriteriaSatisfied": not reasons and final_orders_in_range,
        "findings": reasons,
        "solutions": [asdict(solution) for solution in solutions],
    }
