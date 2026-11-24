"""Per-seed dev diagnostics of the annulus experiment, feeding the preregistered symptom criteria.

The signature *rules* are geometry-independent and are reused unchanged from
``pinn.experiments.diagnosis.observed_signatures``; this module only produces the
measurements they read, on D_dev / D_phys / the two boundary components (never on
D_claim):

    relL2, normalizedResidualRms, maxBoundaryAbs, localizedRatio, fluxBalance

plus the geometry-native localized statistic ``maxCellRmsErrorOverReferenceRms``
that the d >= 2 trigger reads, and the spatial fields the plots need (per-cell RMS
error, hotspot with its radius and angle, pointwise error and residual fields).

``maxBoundaryAbs`` is the maximum over BOTH components, and the flux balance sums
the two components with each one's own outward normal: on a multiply connected
domain neither is a single number by accident.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.experiments.pinn_torch import rel_l2
from pinn.geometry import annulus as geo
from pinn.governance import annulus_contract as contract
from pinn.reference import analytic_annulus as reference

from . import pinn_torch_annulus as pinn
from .localized_error_annulus import LOCALIZED_STATISTIC


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def dev_diagnostics(model, dev_points: Sequence[Sequence[float]], phys_points: Sequence[Sequence[float]],
                    phys_weights: Sequence[float], boundary_sets: Mapping[str, Mapping[str, Any]],
                    radial_bins: int, angular_sectors: int, *, threads: int = 1) -> dict[str, Any]:
    fld = pinn.fields(model, dev_points, threads=threads)
    exact = [reference.solution(x, y) for x, y in dev_points]
    errors = [abs(a - b) for a, b in zip(fld["u"], exact)]
    residuals = [-(xx + yy) - reference.forcing(x, y)
                 for xx, yy, (x, y) in zip(fld["uxx"], fld["uyy"], dev_points)]
    residual_rms = math.sqrt(math.fsum(r * r for r in residuals) / len(residuals)) / reference.F_RMS

    boundary_abs = {}
    flux_components = {}
    for component, block in boundary_sets.items():
        values = pinn.values(model, block["points"], threads=threads)
        boundary_abs[component] = max(abs(v) for v in values)
        dn = pinn.normal_derivatives(model, block["points"], component, threads=threads)
        flux_components[component] = math.fsum(w * value for w, value in zip(block["weights"], dn))
    forcing_integral = math.fsum(w * reference.forcing(x, y) for w, (x, y) in zip(phys_weights, phys_points))
    flux_balance = abs(math.fsum(flux_components.values()) + forcing_integral) / abs(forcing_integral)

    cells: dict[tuple[int, int], list[float]] = {}
    for point, error in zip(dev_points, errors):
        cells.setdefault(geo.cell_index(point, radial_bins, angular_sectors), []).append(error * error)
    cell_rms = {key: math.sqrt(math.fsum(values) / len(values)) for key, values in cells.items()}
    values = list(cell_rms.values())
    median_cell = _median(values) if values else 0.0
    localized_ratio = (max(values) / median_cell) if median_cell > 0 else float("inf")
    reference_rms = math.sqrt(math.fsum(e * e for e in exact) / len(exact))
    localized_acceptance = (max(values) / reference_rms) if values and reference_rms > 0 else float("inf")
    hotspot_index = max(range(len(dev_points)), key=lambda i: errors[i]) if dev_points else 0
    hotspot_r, hotspot_theta = geo.to_polar(dev_points[hotspot_index])
    return {
        "relL2": rel_l2(fld["u"], exact),
        "normalizedResidualRms": residual_rms,
        "maxBoundaryAbs": max(boundary_abs.values()),
        "maxBoundaryAbsPerComponent": boundary_abs,
        "localizedRatio": localized_ratio,
        LOCALIZED_STATISTIC: localized_acceptance,
        "referenceRms": reference_rms,
        "fluxBalance": flux_balance,
        "fluxPerComponent": flux_components,
        "cellRms": {f"{i},{j}": value for (i, j), value in sorted(cell_rms.items())},
        "cellsCovered": len(cell_rms),
        "cellsExpected": radial_bins * angular_sectors,
        "partition": {"kind": contract.LOCALIZED_ERROR_CRITERION["partitionKind"],
                      "radialBins": radial_bins, "angularSectors": angular_sectors},
        "hotspot": {"x": dev_points[hotspot_index][0], "y": dev_points[hotspot_index][1],
                    "radius": hotspot_r, "theta": hotspot_theta, "absError": errors[hotspot_index]},
        "u": fld["u"],
        "residuals": residuals,
        "pointwiseAbsError": errors,
    }
