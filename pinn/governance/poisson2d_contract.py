"""Executable acceptance contract for Poisson-2D v1.0 (metric definitions + frozen thresholds).

PART 9 / PART 10 of the 2D preregistration.  Every criterion carries an
explicit dimension verdict and the source of its threshold; nothing here is
inherited from the 1D contract silently, and nothing may be relaxed after a
result is read (Constitution 9.1 / 10.1 and the preregistration document
``experiments/poisson2d/EXPERIMENT2D_PREREGISTRATION_20260916.md``).

Threshold-source vocabulary (PART 10): ``1D inherited`` (same dimensionless
quantity, same constant), ``numerical reference`` (fixed by the analytic
reference), ``stability reasoning``, ``protocol rule``.
"""

from __future__ import annotations

#: (criterionId, threshold, level)
CRITERIA: tuple[tuple[str, float, str], ...] = (
    ("AC2D-1", 1e-3, "MUST"),
    ("AC2D-2", 5e-3, "MUST"),
    ("AC2D-3", 1e-4, "MUST"),
    ("AC2D-4", 1e-2, "MUST"),
    ("AC2D-5", 1e-3, "MUST"),
    ("AC2D-6", 5e-3, "MUST"),
    ("AC2D-7", 1e-2, "MUST"),
    ("AC2D-9", 1e-3, "MUST"),
    ("AC2D-8", 5e-3, "SHOULD"),
)

METRICS: dict[str, tuple[str, str]] = {
    "AC2D-1": ("sqrt( int int (u_theta - u*)^2 dA / (int int (u*)^2 dA + eps) )", "GL tensor grid"),
    "AC2D-2": ("max_j |u_theta - u*| / (max_j |u*| + eps)", "CGL tensor grid (interior)"),
    "AC2D-3": ("max over the four edges of |u_theta - g|,  g = 0", "boundary set"),
    "AC2D-4": ("sqrt( int int R^2 dA ) / ||f||_rms,  R = -(u_xx + u_yy) - f", "GL tensor grid"),
    "AC2D-5": ("|int int u_theta dA - 4/pi^2| / (4/pi^2)", "GL tensor grid"),
    "AC2D-6": ("max over boundary nodes |du_theta/dn - du*/dn| / max|du*/dn|,  max|du*/dn| = pi", "boundary set"),
    "AC2D-7": ("|int int |grad u_theta|^2 dA - int int f u_theta dA| / (pi^2/2)", "GL tensor grid"),
    "AC2D-8": ("sqrt( int int |grad u_theta - grad u*|^2 dA / (int int |grad u*|^2 dA + eps) )", "GL tensor grid"),
    "AC2D-9": ("max over tiles of sqrt(mean_tile (u_theta - u*)^2) / sqrt(mean_grid (u*)^2)", "CGL tensor grid, 8 x 8 tiles"),
}

#: PART 10: per-criterion dimension verdict and threshold provenance.
THRESHOLD_SOURCES: dict[str, dict[str, str]] = {
    "AC2D-1": {
        "dimensionVerdict": "DIMENSION-SENSITIVE (attainability), DIMENSION-INVARIANT (definition)",
        "source": "1D inherited (AC-1 = 1e-3). The quantity is a dimensionless relative L2 norm, so the constant transfers; "
                  "what changes with the dimension is how hard it is to reach. Attainability was confirmed on D_dev only, in the "
                  "EXPLORATORY performance pilot, before the threshold was frozen and before any claim set was sealed; no claim data entered.",
    },
    "AC2D-2": {
        "dimensionVerdict": "DIMENSION-SENSITIVE",
        "source": "1D inherited (AC-2 = 5e-3 = 5 x AC-1). In 2D the pointwise maximum of a PINN error field is further above its RMS than "
                  "in 1D, so this criterion is the weaker one of the pair by construction; the localized criterion AC2D-9 carries the "
                  "spatial-structure requirement instead of a hand-tuned looser L-infinity constant.",
    },
    "AC2D-3": {
        "dimensionVerdict": "DIMENSION-INVARIANT",
        "source": "1D inherited (AC-3 = 1e-4). The Dirichlet data are exactly zero and the parameterization u = x(1-x)y(1-y)N enforces "
                  "them by construction on all four edges, so the criterion is satisfied at float64 round-off independently of the dimension.",
    },
    "AC2D-4": {
        "dimensionVerdict": "DIMENSION-INVARIANT",
        "source": "1D inherited (AC-4 = 1e-2). The residual RMS is normalised by ||f||_rms of the same problem (pi^2 in 2D, pi^2/sqrt(2) in 1D), "
                  "so the ratio is dimensionless and the constant carries over.",
    },
    "AC2D-5": {
        "dimensionVerdict": "DIMENSION-INVARIANT",
        "source": "1D inherited (AC-5 = 1e-3) with the 2D numerical reference int int u* = 4/pi^2 (numerical reference).",
    },
    "AC2D-6": {
        "dimensionVerdict": "DIMENSION-SENSITIVE (quantity redefined, constant inherited)",
        "source": "1D AC-6 compared one boundary derivative u'(0) with pi. In 2D the normal derivative varies along each edge, so the "
                  "criterion is the worst boundary node of |du/dn - du*/dn| normalised by max|du*/dn| = pi (numerical reference); the "
                  "constant 5e-3 is 1D inherited and the quantity is strictly stricter than the 1D single-point form (it is a maximum over "
                  "the whole boundary quadrature, not one node). The integrated flux identity is checked separately as the physics check PH1.",
    },
    "AC2D-7": {
        "dimensionVerdict": "DIMENSION-INVARIANT",
        "source": "1D inherited (AC-7 = 1e-2); the energy identity int|grad u|^2 = int f u holds in both dimensions and is normalised by its "
                  "own exact value pi^2/2 (numerical reference).",
    },
    "AC2D-8": {
        "dimensionVerdict": "DIMENSION-INVARIANT",
        "source": "1D inherited (AC-8 = 5e-3, SHOULD). The gradient now has two components; the relative H1 seminorm is still dimensionless.",
    },
    "AC2D-9": {
        "dimensionVerdict": "DIMENSION-SENSITIVE (new criterion, required by the dimension lift)",
        "source": "protocol rule + 1D inherited constant. A global L2 norm cannot see a spatial hotspot, which is a genuinely new failure mode "
                  "in 2D, so the AC2D-1 constant (1e-3) is applied per tile on an 8 x 8 partition of the pointwise grid: no tile may be worse "
                  "than the global acceptance level. This is strictly stronger than AC2D-1 and introduces no new numerical constant. "
                  "The 1D symptom rule sLocalizedError (max-bin / median-bin ratio 3.0) stays a *symptom* criterion for the failure path and is "
                  "not used as an acceptance threshold.",
    },
}

TILES_PER_AXIS = 8

#: The localized-error criterion, as ONE binding instead of three loose strings.
#:
#: External review finding 3 (2026-09-16): validating "the criterion id exists" and
#: "the threshold equals that criterion's threshold" is not enough -- AC2D-2 also
#: exists and also has a threshold, so a localized measurement could be checked
#: against the wrong criterion's (looser) bound and pass. What identifies a
#: criterion is the whole measurement: which statistic, normalized how, over which
#: partition, compared with which operator, against which threshold, at which
#: level, under which seed policy. Every field below is derived from, or asserted
#: against, the frozen tables above; nothing here introduces a new constant.
LOCALIZED_ERROR_CRITERION: dict[str, object] = {
    "criterionId": "AC2D-9",
    "statisticId": "maxTileRmsErrorOverReferenceRms",
    "normalization": "globalReferenceRms",
    "partitionKind": "uniformTiles",
    "tilesPerAxis": TILES_PER_AXIS,
    "operator": "<=",
    "threshold": dict((cid, limit) for cid, limit, _ in CRITERIA)["AC2D-9"],
    "level": dict((cid, level) for cid, _, level in CRITERIA)["AC2D-9"],
    #: Gate 5b enforces every MUST criterion on every seed model
    #: (``pinn.experiments2d.gates2d.external_checks``: ``all(not failedMustCriteria)``),
    #: so one seed failing this criterion is already an acceptance failure. The
    #: symptom rule reuses that policy; it does not invent a proportion of its own.
    "seedPolicy": "every-seed",
    "dimensionScope": ">=2",
    "definition": METRICS["AC2D-9"][0],
    "evaluationGrid": METRICS["AC2D-9"][1],
}


def localized_criterion(criterion_id: str = "AC2D-9") -> dict[str, object]:
    """The localized-error criterion contract, or an error -- never a partial match.

    A caller names only the criterion id; statistic, normalization, partition,
    operator and threshold all come from here, so they cannot be recombined.
    """

    if criterion_id != LOCALIZED_ERROR_CRITERION["criterionId"]:
        known = {cid for cid, _limit, _level in CRITERIA}
        if criterion_id in known:
            raise ValueError(
                f"{criterion_id} is an acceptance criterion of this contract but it is not the "
                f"localized-error criterion ({LOCALIZED_ERROR_CRITERION['criterionId']})"
            )
        raise ValueError(f"{criterion_id} is not an acceptance criterion of this contract")
    return dict(LOCALIZED_ERROR_CRITERION)


def thresholds() -> dict[str, float]:
    return {cid: limit for cid, limit, _ in CRITERIA}


def levels() -> dict[str, str]:
    return {cid: level for cid, _, level in CRITERIA}


def must_ids() -> tuple[str, ...]:
    return tuple(cid for cid, _, level in CRITERIA if level == "MUST")


def should_ids() -> tuple[str, ...]:
    return tuple(cid for cid, _, level in CRITERIA if level == "SHOULD")
