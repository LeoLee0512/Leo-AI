"""Measurements for the diagnosis-only discriminating experiments (external review ruling item 4).

A root cause is what is left, so every alternative has to be ruled out by something that
would have spoken if the cause were present. "No defect observed" is not that. Each routine
here is therefore one of two kinds, and says which it is:

* **interventional** -- change the variable the cause depends on; if the cause were real the
  result would move;
* **positive-controlled** -- inject the cause first and show the measurement finds it, then
  measure the real thing and show it is not there.

Nothing here reads D_claim, writes a ledger event, or produces a claim. The criteria and
thresholds are frozen in
``experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md``.
"""

from __future__ import annotations

import importlib
import math
from typing import Any, Callable, Mapping, Sequence

from pinn.geometry import annulus as geo
from pinn.reference import analytic_annulus as reference

#: The partition the localized criterion is defined on.
RADIAL_BINS = 4
ANGULAR_SECTORS = 16


# --------------------------------------------------------------------- the solution, in torch

def solution_module(torch, *, dtype, bump: Mapping[str, Any] | None = None):
    """``u*`` as a differentiable torch module, optionally with a known local bump added.

    Built independently of ``pinn.reference`` -- the closed forms are written out again here
    rather than imported -- so that pushing it through the production pipeline exercises the
    autodiff path, the cell partition, the normalisation and the boundary code against an
    answer that is known exactly. ``bump`` adds ``amplitude * exp(-d^2 / (2 sigma^2))`` at a
    chosen point, which is how the positive control injects an implementation-style defect
    whose location is known in advance.
    """

    a2 = geo.INNER_RADIUS ** 2
    r2 = geo.OUTER_RADIUS ** 2
    pi = math.pi
    spec = dict(bump or {})

    class ExactSolution(torch.nn.Module):
        def forward(self, xy):
            x = xy[:, 0:1]
            y = xy[:, 1:2]
            s = x * x + y * y
            h = (r2 - s) * (s - a2)
            g = (1.0
                 + reference.G_SIN_AMPLITUDE * torch.sin(pi * x) * torch.cos(2.0 * pi * y)
                 + reference.G_X_SLOPE * x
                 - reference.G_Y_SLOPE * y)
            u = h * g
            if spec:
                dx = x - spec["x"]
                dy = y - spec["y"]
                u = u + spec["amplitude"] * torch.exp(-(dx * dx + dy * dy) / (2.0 * spec["sigma"] ** 2))
            return u

    return ExactSolution().to(dtype=dtype)


# --------------------------------------------------------------------- an independent statistic

def independent_cell_index(point: Sequence[float], radial_bins: int = RADIAL_BINS,
                           angular_sectors: int = ANGULAR_SECTORS) -> str:
    """The equal-area cell of a point, derived from the definition rather than imported.

    Deliberately does not call ``pinn.geometry.annulus.cell_index``: an independent
    recomputation that reuses the partition under test would check nothing.
    """

    x, y = float(point[0]), float(point[1])
    a2 = geo.INNER_RADIUS ** 2
    r2 = geo.OUTER_RADIUS ** 2
    fraction = (x * x + y * y - a2) / (r2 - a2)
    radial = min(radial_bins - 1, max(0, int(fraction * radial_bins)))
    theta = math.atan2(y, x) % (2.0 * math.pi)
    sector = min(angular_sectors - 1, max(0, int(theta / (2.0 * math.pi / angular_sectors))))
    return f"{radial},{sector}"


def independent_localized_statistic(points: Sequence[Sequence[float]], errors: Sequence[float],
                                    reference_values: Sequence[float], *, radial_bins: int = RADIAL_BINS,
                                    angular_sectors: int = ANGULAR_SECTORS) -> dict[str, Any]:
    """max over equal-area cells of the cell RMS error, over the RMS of the reference. Written out here.

    Same definition as the production statistic, none of the same code. If the two disagree,
    one of them is wrong and the localized signal cannot be trusted either way.
    """

    if not (len(points) == len(errors) == len(reference_values)):
        raise ValueError("points, errors and reference values must have the same length")
    if not points:
        raise ValueError("an empty evaluation set has no localized statistic")
    buckets: dict[str, list[float]] = {}
    for point, error in zip(points, errors):
        buckets.setdefault(independent_cell_index(point, radial_bins, angular_sectors), []).append(float(error) ** 2)
    cell_rms = {cell: math.sqrt(math.fsum(values) / len(values)) for cell, values in buckets.items()}
    reference_rms = math.sqrt(math.fsum(float(v) ** 2 for v in reference_values) / len(reference_values))
    if reference_rms <= 0.0:
        raise ValueError("the reference RMS is not positive; the normalisation is undefined")
    worst_cell = max(cell_rms, key=lambda cell: cell_rms[cell])
    return {
        "statistic": cell_rms[worst_cell] / reference_rms,
        "worstCell": worst_cell,
        "worstCellRms": cell_rms[worst_cell],
        "referenceRms": reference_rms,
        "cellRms": dict(sorted(cell_rms.items())),
        "cellsCovered": len(cell_rms),
        "cellsExpected": radial_bins * angular_sectors,
    }


# --------------------------------------------------------------------- spec consistency

def spec_residual_analytic(points: Sequence[Sequence[float]], *,
                           forcing: Callable[[float, float], float] | None = None) -> dict[str, Any]:
    """``max |-Lap u* - f|`` through the closed-form Laplacian. No autodiff, no model."""

    f = forcing or reference.forcing
    residuals = [abs(-reference.laplacian(x, y) - f(x, y)) for x, y in points]
    return {"route": "closed-form Laplacian", "maxAbsResidual": max(residuals) if residuals else float("inf"),
            "points": len(points)}


def spec_residual_autodiff(torch, points: Sequence[Sequence[float]], *, dtype,
                           forcing: Callable[[float, float], float] | None = None) -> dict[str, Any]:
    """``max |-Lap u* - f|`` through autodiff on the torch-expressed solution. Independent of the above."""

    f = forcing or reference.forcing
    model = solution_module(torch, dtype=dtype)
    xy = torch.tensor([[float(x), float(y)] for x, y in points], dtype=dtype).requires_grad_(True)
    u = model(xy)
    (grad,) = torch.autograd.grad(u, xy, grad_outputs=torch.ones_like(u), create_graph=True)
    (gx,) = torch.autograd.grad(grad[:, 0:1], xy, grad_outputs=torch.ones_like(grad[:, 0:1]), create_graph=True)
    (gy,) = torch.autograd.grad(grad[:, 1:2], xy, grad_outputs=torch.ones_like(grad[:, 1:2]), create_graph=True)
    laplacian = (gx[:, 0:1] + gy[:, 1:2]).detach().flatten().tolist()
    residuals = [abs(-value - f(x, y)) for value, (x, y) in zip(laplacian, points)]
    return {"route": "autodiff on the torch-expressed solution",
            "maxAbsResidual": max(residuals) if residuals else float("inf"), "points": len(points)}


def boundary_values(node_count: int = 64) -> dict[str, float]:
    """``max |u*|`` on each boundary component, computed on spec-known nodes."""

    out: dict[str, float] = {}
    for component in (geo.OUTER, geo.INNER):
        nodes, _weights = geo.boundary_nodes(component, node_count)
        out[component] = max(abs(reference.solution(x, y)) for x, y in nodes)
    return out


# --------------------------------------------------------------------- the numerical reference

def localized_reference_error(result: Mapping[str, Any]) -> dict[str, Any]:
    """Per-cell error of the independent FDM against the analytic solution.

    The question is not whether the reference is good on average but whether it could be the
    source of a localized signal, so the comparison is made cell by cell. ``result`` is what
    ``scientific_reference.annulus_polar_fdm.solve`` returns: x, y and u as 2-D arrays over the
    interior polar grid.
    """

    xs, ys, u = result["x"], result["y"], result["u"]
    buckets: dict[str, list[float]] = {}
    nodes = 0
    for i in range(u.shape[0]):
        for j in range(u.shape[1]):
            x, y = float(xs[i, j]), float(ys[i, j])
            error = abs(float(u[i, j]) - reference.solution(x, y))
            buckets.setdefault(independent_cell_index((x, y)), []).append(error * error)
            nodes += 1
    cell_rms = {cell: math.sqrt(math.fsum(v) / len(v)) for cell, v in buckets.items()}
    return {"cellRms": dict(sorted(cell_rms.items())), "maxCellRms": max(cell_rms.values()),
            "cellsCovered": len(cell_rms), "nodes": nodes}


def corrupted_polar_refinement(levels: Sequence[tuple[int, int]]) -> dict[str, Any]:
    """A deliberately wrong polar operator, refined the same way: the positive control for R2.

    The 1/r first-derivative term of the polar Laplacian is dropped. The scheme stays stable
    and still converges to *something*; what it loses is second order. If the refinement study
    cannot see that, it cannot see a reference defect either.
    """

    import numpy as np                                                    # noqa: PLC0415

    a, b = geo.INNER_RADIUS, geo.OUTER_RADIUS
    out = []
    for radial_cells, angular_cells in levels:
        dr = (b - a) / radial_cells
        dtheta = 2.0 * math.pi / angular_cells
        r = a + dr * np.arange(1, radial_cells)
        theta = dtheta * np.arange(angular_cells)
        rr, tt = np.meshgrid(r, theta, indexing="ij")
        xx, yy = rr * np.cos(tt), rr * np.sin(tt)
        rhs = np.vectorize(reference.forcing)(xx, yy)
        exact = np.vectorize(reference.solution)(xx, yy)
        u = np.zeros_like(rhs)
        diagonal = 2.0 / (dr * dr) + 2.0 / (dtheta * dtheta) / (rr * rr)
        # Damped Jacobi, iterated to a residual tolerance rather than a fixed sweep count.
        # Both details were wrong in the first version of this control and both mattered:
        #   * the update read ``u = u + residual / diagonal`` while ``residual`` is A u - b,
        #     so it ascended instead of descending and diverged whatever the operator was --
        #     the control never tested the corruption at all;
        #   * a fixed 4000 sweeps left the true operator at max|residual| ~ 1e-1, so iteration
        #     error would have contaminated the discretisation error it was meant to measure.
        iterations = 0
        for iterations in range(1, 200001):
            up = np.pad(u, ((1, 1), (0, 0)), mode="constant")
            up = np.concatenate([up[:, -1:], up, up[:, :1]], axis=1)
            urr = (up[2:, 1:-1] - 2.0 * u + up[:-2, 1:-1]) / (dr * dr)
            utt = (up[1:-1, 2:] - 2.0 * u + up[1:-1, :-2]) / (dtheta * dtheta) / (rr * rr)
            # the 1/r du/dr term is MISSING on purpose: that is the corruption under test
            residual = -(urr + utt) - rhs
            if float(np.max(np.abs(residual))) <= 1e-10 * max(1.0, float(np.max(np.abs(rhs)))):
                break
            u = u - residual / diagonal
        error = float(np.sqrt(np.mean((u - exact) ** 2)) / np.sqrt(np.mean(exact ** 2)))
        out.append({"radialCells": radial_cells, "angularCells": angular_cells, "relL2": error,
                    "iterations": iterations,
                    "finalMaxResidual": float(np.max(np.abs(residual)))})
    orders = [math.log(out[i]["relL2"] / out[i + 1]["relL2"], 2.0) for i in range(len(out) - 1)]
    return {"levels": out, "observedOrders": orders}


def observed_orders(levels: Sequence[Mapping[str, Any]], key: str = "relL2") -> list[float]:
    return [math.log(float(levels[i][key]) / float(levels[i + 1][key]), 2.0) for i in range(len(levels) - 1)]


def statistic_call_path_modules() -> dict[str, Any]:
    """Every module the localized statistic is built from, and whether any of them reaches the FDM.

    The claim is narrow and mechanical: the number that failed Gate 5b is computed from the
    analytic solution, never from the independent numerical reference. If the FDM cannot enter
    the statistic, a defect in it cannot have produced the signal. The import graph is read
    from the sources with ``ast`` rather than from a running interpreter, so nothing that
    happens to be imported elsewhere in the process can mask the answer.
    """

    import ast                                                            # noqa: PLC0415
    from pathlib import Path as _Path                                     # noqa: PLC0415

    root = _Path(__file__).resolve().parents[2]
    # The root set must include every module that COMPUTES the statistic and every module that
    # ADJUDICATES it. The first version of this audit listed only the former and reported an
    # empty result -- which was a property of the root set, not a finding. gates_annulus is the
    # module whose external_checks renders the ACA-9 MUST verdict, and it does import the FDM
    # (for Gate 2 and PH7); leaving it out is what made the audit unsound.
    roots = ["pinn.experiments_annulus.diagnostics_annulus",
             "pinn.experiments_annulus.pinn_torch_annulus",
             "pinn.experiments_annulus.localized_error_annulus",
             "pinn.experiments_annulus.gates_annulus",
             "pinn.experiments_annulus.runner_annulus",
             "pinn.experiments_annulus.datasets_annulus",
             "pinn.geometry.annulus",
             "pinn.governance.annulus_contract",
             "pinn.reference.analytic_annulus"]
    graph: dict[str, list[str]] = {}
    frontier = list(roots)
    while frontier:
        name = frontier.pop()
        if name in graph:
            continue
        source = root / (name.replace(".", "/") + ".py")
        if not source.is_file():
            package_init = root / name.replace(".", "/") / "__init__.py"
            if package_init.is_file():
                source = package_init          # a package node is not a leaf; its __init__ imports too
            else:
                graph[name] = []
                continue
        tree = ast.parse(source.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:                                            # relative: same package
                    package = name.rsplit(".", 1)[0]
                    if node.module:
                        # ``from .localized_error_annulus import LOCALIZED_STATISTIC`` imports a
                        # MODULE named by node.module; the aliases are symbols inside it. The first
                        # version used the aliases, which put symbol names into the module graph.
                        imported.add(f"{package}.{node.module}")
                    else:
                        imported.update(f"{package}.{alias.name}" for alias in node.names)
                elif node.module:
                    imported.add(node.module)
        local = sorted(item for item in imported if item.startswith(("pinn.", "scientific_reference")))
        graph[name] = local
        frontier.extend(item for item in local if item.startswith("pinn.") and item not in graph)
    reaches_reference = sorted(name for name, imports in graph.items()
                               if any(item.startswith("scientific_reference") for item in imports))
    return {"roots": roots, "graph": dict(sorted(graph.items())),
            "modulesReachingTheNumericalReference": reaches_reference,
            "statisticCanReadTheNumericalReference": bool(reaches_reference)}


# --------------------------------------------------------------------- regularity and singularity

def regularity_by_cell(points: Sequence[Sequence[float]]) -> dict[str, Any]:
    """Per-cell maxima of ``|u*|``, ``|grad u*|`` and ``|Lap u*|``: a singular feature would show here."""

    buckets: dict[str, dict[str, float]] = {}
    for x, y in points:
        cell = independent_cell_index((x, y))
        gx, gy = reference.gradient(x, y)
        entry = buckets.setdefault(cell, {"u": 0.0, "grad": 0.0, "laplacian": 0.0})
        entry["u"] = max(entry["u"], abs(reference.solution(x, y)))
        entry["grad"] = max(entry["grad"], math.hypot(gx, gy))
        entry["laplacian"] = max(entry["laplacian"], abs(reference.laplacian(x, y)))
    laplacians = sorted(entry["laplacian"] for entry in buckets.values())
    median = (laplacians[len(laplacians) // 2] if len(laplacians) % 2
              else 0.5 * (laplacians[len(laplacians) // 2 - 1] + laplacians[len(laplacians) // 2]))
    return {"perCell": dict(sorted(buckets.items())), "medianCellMaxLaplacian": median,
            "maxCellMaxLaplacian": laplacians[-1],
            "ratioMaxOverMedian": (laplacians[-1] / median) if median > 0 else float("inf")}


def singular_error_field(points: Sequence[Sequence[float]], *, theta0: float = 0.4,
                         exponent: float = -1.0 / 3.0, cap: float = 50.0) -> dict[str, Any]:
    """A genuinely singular error field anchored on the inner circle: the positive control for G3.

    ``d ** (-1/3)`` is the gradient scaling of a re-entrant corner, capped so the array stays
    finite. If the localized machinery cannot put the hotspot against the boundary for this
    field, then its failure to do so on the real data says nothing.
    """

    x0, y0 = geo.to_cartesian(geo.INNER_RADIUS, theta0)
    errors = []
    for x, y in points:
        distance = math.hypot(float(x) - x0, float(y) - y0)
        errors.append(min(cap, distance ** exponent) if distance > 0 else cap)
    return {"anchor": {"x": x0, "y": y0, "theta": theta0, "component": geo.INNER},
            "exponent": exponent, "cap": cap, "errors": errors}


def boundary_adjacent(cell: str, radial_bins: int = RADIAL_BINS) -> bool:
    """True when a cell touches either circle -- where a mishandled singularity would show."""

    return int(str(cell).split(",")[0]) in (0, radial_bins - 1)
