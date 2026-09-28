"""Preregistered, machine-decidable criterion for a controlled single-factor intervention (Experiment 3 onward).

Constitution 1.2 (3.2) requires >= 3 levels x >= 3 seeds and a strictly
decreasing per-level median; Experiment 2 showed that this can be met by a
5.89e-4 -> 5.09e-4 step with overlapping seeds (report N2 / N3).  The protocol
therefore adds a stricter test, frozen on 2026-09-16 *before* the boundary
intervention ran and not applied retroactively to Experiment 2:

* **paired seeds**: every level uses the same N seed triplets (N >= 10), so the
  comparison between adjacent levels is paired, not two independent samples;
* **effect size**: ``median(E_high) / median(E_low) < rho`` with ``rho = 0.5``
  -- the factor-of-two rule the protocol compilation already uses for the
  capacity scan (P23: ratio < 0.5), i.e. a factor that matters must at least
  halve the error over one preregistered decade of its control;
* **consistency**: the fraction of paired seeds whose error improves,
  ``#{E_i(high) < E_i(low)} / N >= q`` with ``q = 0.8`` -- the same 0.8 line
  Constitution 10.1 uses for k/N (for N = 10 under H0 p = 0.5 the one-sided
  binomial probability of >= 8 improvements is 0.055).

Both tests are required between *every* pair of adjacent levels.  "high" is
the level expected to reduce the error (more of the factor); the direction is
declared in the plan before the runs.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

RHO = 0.5
Q = 0.8
MIN_PAIRED_SEEDS = 10


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])


def paired_intervention_errors(levels: Sequence[Mapping[str, Any]], *, rho: float = RHO, q: float = Q,
                               min_seeds: int = MIN_PAIRED_SEEDS, metric: str = "errors") -> list[str]:
    """Errors (empty = criterion met) for ``levels = [{level, seedTriplets, errors}]`` ordered low -> high factor.

    ``errors[i]`` of every level must belong to the same seed triplet ``seedTriplets[i]``.
    """

    errors: list[str] = []
    if len(levels) < 3:
        return ["at least three levels are required"]
    triplets = None
    for index, level in enumerate(levels):
        values = level.get(metric)
        seeds = level.get("seedTriplets")
        if not isinstance(values, list) or len(values) < min_seeds:
            errors.append(f"levels[{index}]: at least {min_seeds} paired seeds are required")
            continue
        if not isinstance(seeds, list) or len(seeds) != len(values):
            errors.append(f"levels[{index}]: every error needs its seed triplet")
            continue
        if triplets is None:
            triplets = seeds
        elif seeds != triplets:
            errors.append(f"levels[{index}]: seed triplets differ from the first level; the comparison must be paired")
        if any((not isinstance(v, (int, float))) or isinstance(v, bool) or v != v or v < 0 for v in values):
            errors.append(f"levels[{index}]: errors must be finite non-negative numbers (a divergent run is an error, report it separately)")
    if errors:
        return errors
    for index in range(len(levels) - 1):
        low, high = levels[index], levels[index + 1]
        med_low, med_high = _median(low[metric]), _median(high[metric])
        if med_low <= 0:
            errors.append(f"levels[{index}]: median error is zero; the ratio test is undefined")
            continue
        ratio = med_high / med_low
        if not ratio < rho:
            errors.append(f"levels[{index}]->[{index + 1}]: median ratio {ratio:.3f} is not below rho = {rho} (effect too small)")
        improved = sum(1 for a, b in zip(low[metric], high[metric]) if b < a)
        fraction = improved / len(low[metric])
        if fraction < q:
            errors.append(f"levels[{index}]->[{index + 1}]: only {improved}/{len(low[metric])} paired seeds improved; q = {q} required")
    return errors


def paired_intervention_summary(levels: Sequence[Mapping[str, Any]], metric: str = "errors") -> dict[str, Any]:
    out = []
    for index, level in enumerate(levels):
        entry = {"level": level.get("level"), "median": _median(level[metric]), "n": len(level[metric])}
        if index:
            prev = levels[index - 1]
            entry["ratioToPrevious"] = entry["median"] / _median(prev[metric]) if _median(prev[metric]) > 0 else math.inf
            entry["pairedImproved"] = sum(1 for a, b in zip(prev[metric], level[metric]) if b < a)
        out.append(entry)
    return {"rho": RHO, "q": Q, "minPairedSeeds": MIN_PAIRED_SEEDS, "levels": out}
