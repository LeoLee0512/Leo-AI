"""Executable acceptance contract for the annular Poisson problem (Geometry Lift 1).

Every criterion carries a **geometry verdict** as well as its threshold source,
because the question this round asks is not "is the PINN accurate" but "which
parts of the trust loop were assumptions about a rectangle":

    GEOMETRY-INVARIANT   the same dimensionless quantity, the same constant --
                         the domain's shape does not enter its definition;
    GEOMETRY-SENSITIVE   the definition survives but its attainability, its
                         normalisation or its evaluation grid changes;
    NEW-GEOMETRY METRIC  a criterion that has no square counterpart.

Thresholds are frozen here before the formal run and are never read from a
result (Constitution 9.1 / 10.1). Nothing may be relaxed after a number is seen.
"""

from __future__ import annotations

from pinn.geometry.annulus import INNER_RADIUS, OUTER_RADIUS

#: (criterionId, threshold, level)
CRITERIA: tuple[tuple[str, float, str], ...] = (
    ("ACA-1", 1e-3, "MUST"),
    ("ACA-2", 5e-3, "MUST"),
    ("ACA-3", 1e-4, "MUST"),
    ("ACA-4", 1e-2, "MUST"),
    ("ACA-5", 1e-3, "MUST"),
    ("ACA-6", 5e-3, "MUST"),
    ("ACA-7", 1e-2, "MUST"),
    ("ACA-9", 1e-3, "MUST"),
    ("ACA-8", 5e-3, "SHOULD"),
)

METRICS: dict[str, tuple[str, str]] = {
    "ACA-1": ("sqrt( int_Omega (u_theta - u*)^2 dA / (int_Omega (u*)^2 dA + eps) )",
              "annulus quadrature: Gauss-Legendre in the area fraction t, trapezoid in theta"),
    "ACA-2": ("max_j |u_theta - u*| / (max_j |u*| + eps)", "interior pointwise grid of the claim set"),
    "ACA-3": ("max over BOTH boundary components of |u_theta|", "outer and inner boundary nodes"),
    "ACA-4": ("sqrt( int_Omega ( -Lap u_theta - f )^2 dA / |Omega| ) / F_RMS", "annulus quadrature"),
    "ACA-5": ("| int_Omega u_theta dA - int_Omega u* dA | / | int_Omega u* dA |", "annulus quadrature"),
    "ACA-6": ("max over both components of |du_theta/dn - du*/dn| / max|du*/dn|",
              "outer and inner boundary nodes, each with ITS OWN outward normal"),
    "ACA-7": ("| int_Omega |grad u_theta|^2 dA - int_Omega f u_theta dA | / DIRICHLET_ENERGY", "annulus quadrature"),
    "ACA-9": ("max over equal-area cells of sqrt(mean_cell (u_theta - u*)^2) / sqrt(mean_grid (u*)^2)",
              "geometry-native partition: 4 equal-area radial bins x 16 angular sectors = 64 cells"),
    "ACA-8": ("sqrt( int_Omega |grad u_theta - grad u*|^2 dA / (int_Omega |grad u*|^2 dA + eps) )", "annulus quadrature"),
}

THRESHOLD_SOURCES: dict[str, dict[str, str]] = {
    "ACA-1": {
        "geometryVerdict": "GEOMETRY-INVARIANT (definition), GEOMETRY-SENSITIVE (attainability and quadrature)",
        "source": "2D square inherited (AC2D-1 = 1e-3). A relative L2 error is dimensionless and shape-free; what the "
                  "annulus changes is the quadrature that evaluates it (area-fraction Gauss-Legendre x trapezoid "
                  "instead of a tensor grid on the square) and the attainability, confirmed before the freeze by the "
                  "EXPLORATORY smoke run on D_dev only.",
    },
    "ACA-2": {
        "geometryVerdict": "GEOMETRY-INVARIANT (definition), GEOMETRY-SENSITIVE (grid)",
        "source": "2D square inherited (AC2D-2 = 5e-3). Same relative L-infinity; the pointwise grid is the annulus "
                  "claim grid, which has no nodes in the hole and none on either circle.",
    },
    "ACA-3": {
        "geometryVerdict": "GEOMETRY-SENSITIVE (two boundary components instead of four edges of one component)",
        "source": "2D square inherited (AC2D-3 = 1e-4). The hard parameterization u = h N with h = (1 - s)(s - a^2) "
                  "makes u vanish on BOTH circles by construction, so the criterion is satisfied at round-off; it is "
                  "kept because it is exactly the check that catches a hard factor written for one component only.",
    },
    "ACA-4": {
        "geometryVerdict": "GEOMETRY-SENSITIVE (normalisation: the forcing scale is the annulus one)",
        "source": "2D square inherited (AC2D-4 = 1e-2) as a dimensionless ratio, but the normaliser F_RMS is "
                  "recomputed for this problem from the frozen forcing on the annulus (6.2631...), not carried over "
                  "from the square. A residual is only meaningful against its own forcing scale.",
    },
    "ACA-5": {
        "geometryVerdict": "GEOMETRY-SENSITIVE (the exact integral is an annulus integral)",
        "source": "2D square inherited (AC2D-5 = 1e-3). The reference value is int_Omega u* dA = pi (1 - a^2)^3 / 6, "
                  "derived in closed form and verified numerically against the quadrature; the non-radial part of g "
                  "integrates to zero by symmetry, which is checked rather than assumed.",
    },
    "ACA-6": {
        "geometryVerdict": "NEW-GEOMETRY METRIC (the inner component's outward normal points towards the origin)",
        "source": "2D square inherited constant (AC2D-6 = 5e-3) on a normalised quantity. The new risk is not the "
                  "size of the constant but the SIGN of n on the inner circle: n_inner = -(x, y) / a. The criterion "
                  "is evaluated per component, and the flux identity (PH-A1) is the independent check on the sign.",
    },
    "ACA-7": {
        "geometryVerdict": "GEOMETRY-INVARIANT (definition), GEOMETRY-SENSITIVE (both integrals are annulus integrals)",
        "source": "2D square inherited (AC2D-7 = 1e-2). Green's identity has no boundary term because u vanishes on "
                  "the whole boundary -- which here means both components.",
    },
    "ACA-9": {
        "geometryVerdict": "NEW-GEOMETRY METRIC (a Cartesian tile grid straddles the hole)",
        "source": "protocol rule + 2D inherited constant. The localized requirement carries over from the square "
                  "(AC2D-9 = 1e-3 applied per cell) but the PARTITION cannot: 8x8 Cartesian tiles would cover the "
                  "hole, give cells of unequal domain area, and leave some cells empty. The annulus partition is "
                  "geometry-native and equal-area by construction: 4 bins uniform in the area fraction t x 16 "
                  "angular sectors. Same number of cells (64) as the square partition, so the constant transfers "
                  "without a change of statistical regime.",
    },
    "ACA-8": {
        "geometryVerdict": "GEOMETRY-INVARIANT (definition), GEOMETRY-SENSITIVE (quadrature)",
        "source": "2D square inherited (AC2D-8 = 5e-3, SHOULD). Relative H1 seminorm, same dimensionless form.",
    },
}

#: The localized-error partition: equal area by construction.
RADIAL_BINS = 4
ANGULAR_SECTORS = 16
LOCALIZED_CELLS = RADIAL_BINS * ANGULAR_SECTORS

#: The localized-error criterion as ONE binding (the hardening of 2026-09-16):
#: criterionId, statistic, normalisation, partition, operator, threshold, level and
#: seed policy travel together, so a localized measurement cannot be judged against
#: another criterion's bound.
LOCALIZED_ERROR_CRITERION: dict[str, object] = {
    "criterionId": "ACA-9",
    "statisticId": "maxCellRmsErrorOverReferenceRms",
    "normalization": "globalReferenceRms",
    "partitionKind": "annulusEqualAreaCells",
    "radialBins": RADIAL_BINS,
    "angularSectors": ANGULAR_SECTORS,
    "operator": "<=",
    "threshold": dict((cid, limit) for cid, limit, _ in CRITERIA)["ACA-9"],
    "level": dict((cid, level) for cid, _, level in CRITERIA)["ACA-9"],
    #: Gate 5b requires every MUST criterion of every seed model, so one failing seed
    #: is already an acceptance failure; the symptom reuses that policy.
    "seedPolicy": "every-seed",
    "dimensionScope": ">=2",
    "geometryId": "annulus-a035-R1-v1",
    "definition": METRICS["ACA-9"][0],
    "evaluationGrid": METRICS["ACA-9"][1],
}


def thresholds() -> dict[str, float]:
    return {cid: limit for cid, limit, _ in CRITERIA}


def levels() -> dict[str, str]:
    return {cid: level for cid, _, level in CRITERIA}


def must_ids() -> tuple[str, ...]:
    return tuple(cid for cid, _limit, level in CRITERIA if level == "MUST")


def should_ids() -> tuple[str, ...]:
    return tuple(cid for cid, _limit, level in CRITERIA if level == "SHOULD")


def localized_criterion(criterion_id: str = "ACA-9") -> dict[str, object]:
    """The localized-error criterion contract, or an error -- never a partial match."""

    if criterion_id != LOCALIZED_ERROR_CRITERION["criterionId"]:
        known = {cid for cid, _limit, _level in CRITERIA}
        if criterion_id in known:
            raise ValueError(
                f"{criterion_id} is an acceptance criterion of this contract but it is not the "
                f"localized-error criterion ({LOCALIZED_ERROR_CRITERION['criterionId']})")
        raise ValueError(f"{criterion_id} is not an acceptance criterion of this contract")
    return dict(LOCALIZED_ERROR_CRITERION)


#: Physics identities checked in Gate 5a, with the geometry risk each one carries.
PHYSICS_CHECKS: dict[str, dict[str, str]] = {
    "PH-A1": {"name": "flux identity",
              "statement": "int_{dOmega} du/dn ds + int_Omega f dA = 0 over BOTH components",
              "geometryRisk": "the inner component's outward normal points into the hole; a sign error here is "
                              "partly cancelled by the outer component, so the two contributions are also "
                              "reported separately"},
    "PH-A2": {"name": "energy identity", "statement": "int |grad u|^2 dA = int f u dA",
              "geometryRisk": "none beyond the quadrature being an annulus quadrature"},
    "PH-A3": {"name": "inner Dirichlet", "statement": "max |u| on r = a", "geometryRisk": "hard factor must vanish on BOTH circles"},
    "PH-A4": {"name": "outer Dirichlet", "statement": "max |u| on r = R", "geometryRisk": "same"},
    "PH-A5": {"name": "interior sign", "statement": "u* > 0 strictly inside, and u_theta must not change sign wholesale",
              "geometryRisk": "h > 0 only between the circles: a membership error puts h < 0 in the hole"},
    "PH-A6": {"name": "discrete maximum bound", "statement": "max |u_theta| <= (1 + tol) max |u*|",
              "geometryRisk": "none"},
    "PH-A7": {"name": "SPD witness", "statement": "Dirichlet energy of the model is positive",
              "geometryRisk": "none"},
    "PH-A8": {"name": "x/y swap symmetry", "statement": "NOT_APPLICABLE by construction",
              "geometryRisk": "the manufactured solution is deliberately asymmetric (g carries sin(pi x) cos(2 pi y) "
                              "and the slopes +0.1x, -0.1y), so no swap symmetry exists to test. Registered "
                              "NOT_APPLICABLE with this reason rather than faking a symmetry the problem does not have."},
}

GEOMETRY = {"innerRadius": INNER_RADIUS, "outerRadius": OUTER_RADIUS, "geometryId": "annulus-a035-R1-v1"}
