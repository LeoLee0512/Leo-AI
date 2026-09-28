"""AC-1..AC-8 on an arbitrary (GL quadrature, CGL pointwise) claim grid pair.

The frozen v1.0 protocol names one instance of the grid family (GL512 /
CGL2000) and the trusted validator ``pinn.validation.poisson.evaluate_samples``
is hard-wired to it.  Constitution 9.1 burns a claim set once opened, so a
revision after a Gate 5 FAIL needs a *fresh* blind set from the same family
(protocol clarification 2026-09-16, `EXPERIMENT3_PREREGISTRATION_20260916.md`
section 2).  This module evaluates the identical metric definitions
(``pinn.governance.poisson_contract.METRICS``, same epsilon, same fsum
quadrature, same thresholds) on any GL_n / CGL_m pair; ``test_claim_metrics``
proves bit-for-bit agreement with ``evaluate_samples`` on the frozen grids.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.governance.poisson_contract import CRITERIA, METRICS
from pinn.reference import analytic_poisson as reference
from pinn.validation.poisson import EPSILON, ValidationInputError, check_metric_values

THRESHOLDS = {cid: limit for cid, limit, _ in CRITERIA}
LEVELS = {cid: level for cid, _, level in CRITERIA}


def _ratio(numerator: float, denominator: float, label: str, *, epsilon: bool = False) -> float:
    if not math.isfinite(numerator) or numerator < 0.0:
        raise ValidationInputError(f"{label} has an invalid numerator")
    if not math.isfinite(denominator) or denominator <= 1e6 * EPSILON:
        raise ValidationInputError(f"{label} denominator is not above 1e6 * epsilon")
    value = numerator / (denominator + EPSILON if epsilon else denominator)
    if not math.isfinite(value):
        raise ValidationInputError(f"{label} produced a non-finite metric")
    return value


def evaluate_on_grids(*, gl_nodes: Sequence[float], gl_weights: Sequence[float], cgl_nodes: Sequence[float],
                      u_gl: Sequence[float], du_gl: Sequence[float], d2u_gl: Sequence[float],
                      u_cgl: Sequence[float], u_boundary: Sequence[float], du_boundary: Sequence[float],
                      grid_label: str) -> dict[str, Any]:
    """The AC-1..AC-8 values, thresholds and verdicts of one model on the given grid pair."""

    if len(u_gl) != len(gl_nodes) or len(du_gl) != len(gl_nodes) or len(d2u_gl) != len(gl_nodes):
        raise ValidationInputError("quadrature field arrays must match the quadrature nodes")
    if len(u_cgl) != len(cgl_nodes) or len(u_boundary) != 2 or len(du_boundary) != 2:
        raise ValidationInputError("pointwise / boundary arrays have the wrong length")
    if abs(math.fsum(gl_weights) - 1.0) > 1e-12:
        raise ValidationInputError("quadrature weights must sum to one on [0, 1]")
    if (cgl_nodes[0], cgl_nodes[-1]) != (0.0, 1.0):
        raise ValidationInputError("the pointwise grid must include the exact endpoints 0 and 1")
    if (u_cgl[0], u_cgl[-1]) != tuple(u_boundary):
        raise ValidationInputError("pointwise and boundary outputs disagree at the same exact endpoints")
    for value in (*u_gl, *du_gl, *d2u_gl, *u_cgl, *u_boundary, *du_boundary):
        if not math.isfinite(value):
            raise ValidationInputError("non-finite field value; the run is divergent, not evaluable")
    x, w = gl_nodes, gl_weights
    exact_u = [reference.solution(p) for p in x]
    exact_du = [reference.first_derivative(p) for p in x]
    exact_cgl = [reference.solution(p) for p in cgl_nodes]
    exact_f = [reference.forcing(p) for p in x]
    integral = lambda values: math.fsum(weight * value for weight, value in zip(w, values))
    l2_squared = integral((value - exact) ** 2 for value, exact in zip(u_gl, exact_u))
    derivative_l2_squared = integral((value - exact) ** 2 for value, exact in zip(du_gl, exact_du))
    absolute_linf = max(abs(value - exact) for value, exact in zip(u_cgl, exact_cgl))
    residuals = [-second - forcing_value for second, forcing_value in zip(d2u_gl, exact_f)]
    residual_rms = math.sqrt(integral(value * value for value in residuals))
    integral_u = integral(u_gl)
    derivative_energy = integral(value * value for value in du_gl)
    forcing_energy = integral(force * value for force, value in zip(exact_f, u_gl))
    values = {
        "AC-1": math.sqrt(_ratio(l2_squared, integral(value * value for value in exact_u), "AC-1", epsilon=True)),
        "AC-2": _ratio(absolute_linf, max(abs(value) for value in exact_cgl), "AC-2", epsilon=True),
        "AC-3": max(abs(value) for value in u_boundary),
        "AC-4": _ratio(residual_rms, math.pi ** 2 / math.sqrt(2.0), "AC-4"),
        "AC-5": _ratio(abs(integral_u - 2.0 / math.pi), 2.0 / math.pi, "AC-5"),
        "AC-6": _ratio(abs(du_boundary[0] - math.pi), math.pi, "AC-6"),
        "AC-7": _ratio(abs(derivative_energy - forcing_energy), math.pi ** 2 / 2.0, "AC-7"),
        "AC-8": math.sqrt(_ratio(derivative_l2_squared, integral(value * value for value in exact_du), "AC-8", epsilon=True)),
    }
    satisfied = check_metric_values(values)
    metrics = {
        key: {"value": value, "threshold": THRESHOLDS[key], "comparator": "<", "level": LEVELS[key],
              "formula": METRICS[i][0], "grid": grid_label, "criterionSatisfied": satisfied[key]}
        for i, (key, value) in enumerate(values.items())
    }
    return {
        "evaluationScope": "CLAIM_GRID_EVALUATION",
        "grid": grid_label,
        "quadratureCount": len(gl_nodes),
        "pointwiseCount": len(cgl_nodes),
        "componentCriteriaSatisfied": all(satisfied[f"AC-{i}"] for i in range(1, 8)),
        "failedMustCriteria": [f"AC-{i}" for i in range(1, 8) if not satisfied[f"AC-{i}"]],
        "failedShouldCriteria": [] if satisfied["AC-8"] else ["AC-8"],
        "metrics": metrics,
        "diagnostics": {"absoluteL2": math.sqrt(l2_squared), "absoluteLinf": absolute_linf, "pdeResidualRms": residual_rms,
                        "pdeResidualMax": max(abs(v) for v in residuals), "integralU": integral_u, "derivativeAtZero": du_boundary[0],
                        "derivativeEnergy": derivative_energy, "forcingEnergy": forcing_energy},
    }
