"""Per-seed 2D diagnostics feeding the preregistered failure-signature criteria.

The signature *rules* are dimension-independent and are reused unchanged from
``pinn.experiments.diagnosis.observed_signatures``; this module only produces the
measurements they read, on D_dev / D_phys / the boundary set (never on D_claim):

    relL2, normalizedResidualRms, maxBoundaryAbs, localizedRatio, fluxBalance

plus the AC2D-9-form localized statistic (``maxTileRmsErrorOverReferenceRms``) that the
d >= 2 ``sLocalizedError`` trigger reads, and

plus the 2D-specific spatial fields (per-tile RMS error, hotspot coordinates,
pointwise error field, residual field) that PART 17 requires for the error maps.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from pinn.experiments.pinn_torch import rel_l2
from pinn.reference import analytic_poisson2d as reference

from . import pinn_torch2d as pinn2d
from .localized_error import LOCALIZED_STATISTIC


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def dev_diagnostics(model, dev_points: Sequence[Sequence[float]], phys_points: Sequence[Sequence[float]],
                    phys_weights: Sequence[float], boundary_points: Sequence[Sequence[float]],
                    boundary_weights: Sequence[float], tiles_per_axis: int, *, threads: int = 1) -> dict[str, Any]:
    fld = pinn2d.fields(model, dev_points, threads=threads)
    exact = [reference.solution(x, y) for x, y in dev_points]
    errors = [abs(a - b) for a, b in zip(fld["u"], exact)]
    residuals = [-(xx + yy) - reference.forcing(x, y) for xx, yy, (x, y) in zip(fld["uxx"], fld["uyy"], dev_points)]
    residual_rms = math.sqrt(math.fsum(r * r for r in residuals) / len(residuals)) / reference.F_RMS
    boundary_values = pinn2d.values(model, boundary_points, threads=threads)
    dn = pinn2d.normal_derivatives(model, boundary_points, threads=threads)
    flux = math.fsum(w * d for w, d in zip(boundary_weights, dn))
    forcing_integral = math.fsum(w * reference.forcing(x, y) for w, (x, y) in zip(phys_weights, phys_points))
    tiles: dict[tuple[int, int], list[float]] = {}
    for (x, y), error in zip(dev_points, errors):
        key = (min(int(x * tiles_per_axis), tiles_per_axis - 1), min(int(y * tiles_per_axis), tiles_per_axis - 1))
        tiles.setdefault(key, []).append(error * error)
    tile_rms = {f"{i},{j}": math.sqrt(math.fsum(v) / len(v)) for (i, j), v in tiles.items()}
    values = list(tile_rms.values())
    median_tile = _median(values) if values else 0.0
    localized = (max(values) / median_tile) if median_tile > 0 else float("inf")
    # The AC2D-9 form of the same partition: the worst tile's RMS error relative to the
    # scale of the reference solution. This is what the d >= 2 sLocalizedError trigger
    # reads (external review ruling 2026-09-16 item 4); the max/median ratio above is
    # kept only as a retired diagnostic.
    reference_rms = math.sqrt(math.fsum(v * v for v in exact) / len(exact))
    localized_acceptance = (max(values) / reference_rms) if values and reference_rms > 0 else float("inf")
    hotspot_index = max(range(len(dev_points)), key=lambda i: errors[i]) if dev_points else 0
    return {
        "relL2": rel_l2(fld["u"], exact),
        "normalizedResidualRms": residual_rms,
        "maxBoundaryAbs": max(abs(v) for v in boundary_values),
        "localizedRatio": localized,
        LOCALIZED_STATISTIC: localized_acceptance,
        "referenceRms": reference_rms,
        "fluxBalance": abs(flux + forcing_integral) / abs(forcing_integral),
        "tileRms": tile_rms,
        "tilesPerAxis": tiles_per_axis,
        "hotspot": {"x": dev_points[hotspot_index][0], "y": dev_points[hotspot_index][1], "absError": errors[hotspot_index]},
        "u": fld["u"],
        "residuals": residuals,
        "pointwiseAbsError": errors,
    }
