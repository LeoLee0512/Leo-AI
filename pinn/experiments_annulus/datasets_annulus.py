"""Evaluation sets of the annular Poisson experiment (Constitution 9.1, Geometry Lift 1).

D_train  = a preregistered pool of AREA-uniform random interior points of the
           annulus; a run's sampling seed chooses the ``collocationCount`` pool
           points it trains on. The hard parameterization removes the boundary
           loss, so the training set is interior-only.
D_dev    = area-uniform random interior points from ``devSeed`` (diagnostics,
           seed statistics, failure analysis, Red Team, reproduction comparison).
D_phys   = the geometry-native quadrature (Gauss-Legendre in the area fraction t,
           trapezoid in theta) -- deterministic and public.
D_claim  = a preregistered member of the blind claim pool: its own quadrature
           grid (integral criteria) together with its own pointwise grid
           (ACA-2 and the localized ACA-9). Claim identity follows the samples
           (``sampleSetHash``), never the artifact bytes.

The boundary nodes of the two components are spec-known coordinates (protocol L1
``boundaryIdentityExempt``), stored as their own artifact per component, because
a node's component decides which outward normal measures it.

Every constructor here refuses a point that is not strictly inside the annulus:
in a multiply connected domain "inside" is no longer implied by the bounding box.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.experiments.datasets import cgl_unit
from pinn.geometry import annulus as geo
from pinn.governance.canonical import canonical_sha256
from pinn.governance.evaluation_sets import (
    disjointness_errors,
    load_evaluation_set,
    sample_set_hash,
    validate_evaluation_set,
)
from pinn.governance.nodes import anti_collision

SCHEMA_VERSION = "pinn.evaluationSet/1.0"
INPUT_NAMES = ["x", "y"]


def area_uniform_interior(size: int, seed: int) -> list[tuple[float, float]]:
    """Area-uniform interior points; the draw is checked, not trusted."""

    points = geo.uniform_area_points(size, seed)
    geo.assert_interior(points, label=f"area-uniform draw seed={seed}")
    return points


def phys_grid(radial_order: int, angular_count: int) -> tuple[list[tuple[float, float]], list[float]]:
    points, weights = geo.quadrature(radial_order, angular_count)
    geo.assert_interior(points, label="D_phys")
    return points, weights


def claim_quadrature(radial_order: int, angular_count: int, angular_offset: float
                     ) -> tuple[list[tuple[float, float]], list[float]]:
    """A claim member's own quadrature: a different GL order and a rotated angular rule."""

    points, weights = geo.quadrature(radial_order, angular_count)
    rotated = [geo.to_cartesian(*_rotate(point, angular_offset)) for point in points]
    geo.assert_interior(rotated, label="claim quadrature")
    return rotated, weights


def _rotate(point: Sequence[float], angle: float) -> tuple[float, float]:
    r, theta = geo.to_polar(point)
    return r, (theta + angle) % (2.0 * math.pi)


def claim_pointwise(cgl_count: int, angular_count: int, angular_offset: float) -> list[tuple[float, float]]:
    """A claim member's pointwise grid: interior CGL nodes in the area fraction x rotated angles.

    CGL in ``t`` rather than in ``r`` keeps the nodes equidistributed by area, and
    dropping t = 0 and t = 1 keeps every node off both circles.
    """

    t_nodes = [t for t in cgl_unit(cgl_count) if 0.0 < t < 1.0]
    step = 2.0 * math.pi / angular_count
    points = [geo.to_cartesian(geo.radius_of_area_fraction(t), angular_offset + k * step)
              for t in t_nodes for k in range(angular_count)]
    geo.assert_interior(points, label="claim pointwise grid")
    return points


def boundary_sets(node_count: int) -> dict[str, dict[str, Any]]:
    """Both boundary components, each with its own nodes, weights and outward normals."""

    out: dict[str, dict[str, Any]] = {}
    for component in geo.BOUNDARY_COMPONENTS:
        nodes, weights = geo.boundary_nodes(component, node_count)
        geo.assert_on_boundary(nodes, component)
        out[component] = {
            "component": component,
            "radius": geo.boundary_radius(component),
            "points": nodes,
            "weights": weights,
            "normals": [geo.outward_normal(node, component) for node in nodes],
            "nodeCount": node_count,
            "rule": "equally spaced angles with weight r * 2 pi / count (periodic trapezoid)",
            "boundaryIdentityExempt": True,
        }
    return out


def samples(points, kind: str = "interior") -> list[dict[str, Any]]:
    return [{"inputs": [float(x), float(y)], "kind": kind} for x, y in points]


def manifest(artifact_id: str, role: str, points, *, generator: Mapping[str, str]) -> dict[str, Any]:
    """An evaluation-set artifact, in the schema the governance layer already fixes.

    The manifest shape is deliberately NOT extended for the annulus: the geometry
    belongs to the ProblemDefinition and to the geometry report, and a set whose
    schema drifted would no longer be comparable with the sets of the closed
    experiments. Every constructor above has already refused points off the domain.
    """

    document = {
        "schemaVersion": SCHEMA_VERSION,
        "artifactId": artifact_id,
        "role": role,
        "inputNames": list(INPUT_NAMES),
        "generator": dict(generator),
        "samples": samples(points),
    }
    errors = validate_evaluation_set(document)
    if errors:
        raise ValueError(f"{artifact_id}: {errors[0]}")
    return document


def points_of(document: Mapping[str, Any]) -> list[tuple[float, float]]:
    return [(float(sample["inputs"][0]), float(sample["inputs"][1])) for sample in document["samples"]]


def claim_member_points(member: Mapping[str, Any]) -> list[tuple[float, float]]:
    """The full sample list of a claim member: its quadrature grid then its pointwise grid."""

    quadrature, _weights = claim_quadrature(int(member["quadratureRadialOrder"]),
                                            int(member["quadratureAngularCount"]),
                                            float(member["angularOffset"]))
    pointwise = claim_pointwise(int(member["pointwiseCglCount"]), int(member["pointwiseAngularCount"]),
                                float(member["pointwiseAngularOffset"]))
    return list(quadrature) + list(pointwise)


def member_generator_version(member: Mapping[str, Any]) -> str:
    return ("annulus-claim: quadrature GL{quadratureRadialOrder} x {quadratureAngularCount} rotated by "
            "{angularOffset}; pointwise CGL{pointwiseCglCount} in t x {pointwiseAngularCount} angles from "
            "{pointwiseAngularOffset}").format(**member)


def claim_pool_manifests(pool: Mapping[str, Mapping[str, Any]], *, label: str) -> dict[str, dict[str, Any]]:
    """One evaluation-set artifact per sealed claim member."""

    out: dict[str, dict[str, Any]] = {}
    for member_id, member in pool.items():
        points = claim_member_points(member)
        if len(set(points)) != len(points):
            raise ValueError(f"{member_id}: the quadrature and pointwise grids of this member share a point")
        out[member_id] = manifest(f"set-claim-{label}-{member_id}", "claim", points,
                                  generator={"generatorId": member_id,
                                             "generatorVersion": member_generator_version(member)})
    return out


def build_sets(config: Mapping[str, Any], *, claim_points, claim_artifact_id: str,
               claim_generator: Mapping[str, str]) -> dict[str, dict[str, Any]]:
    """The three public sets plus the opened claim member, as artifacts."""

    sets_config = config["sets"]
    sampling = config["sampling"]
    train = area_uniform_interior(int(sampling["poolSize"]), int(sampling["poolSeed"]))
    dev = area_uniform_interior(int(sets_config["devSize"]), int(sets_config["devSeed"]))
    phys, _weights = phys_grid(int(sets_config["physRadialOrder"]), int(sets_config["physAngularCount"]))
    pool_version = ("r = sqrt(a^2 + (R^2 - a^2) U), theta = 2 pi V, numpy default_rng({seed}), size {size}")
    return {
        "train": manifest("train_pool.json", "train", train,
                          generator={"generatorId": "annulus-area-uniform-pool",
                                     "generatorVersion": pool_version.format(seed=int(sampling["poolSeed"]),
                                                                             size=int(sampling["poolSize"]))}),
        "dev": manifest("dev_set.json", "dev", dev,
                        generator={"generatorId": "annulus-area-uniform-dev",
                                   "generatorVersion": pool_version.format(seed=int(sets_config["devSeed"]),
                                                                           size=int(sets_config["devSize"]))}),
        "phys": manifest("phys_set.json", "phys", phys,
                         generator={"generatorId": "annulus-quadrature",
                                    "generatorVersion": "Gauss-Legendre order {order} in the area fraction t x {count} "
                                                        "trapezoid angles; Jacobian (R^2 - a^2)/2".format(
                                                            order=int(sets_config["physRadialOrder"]),
                                                            count=int(sets_config["physAngularCount"]))}),
        "claim": manifest(claim_artifact_id, "claim", claim_points, generator=dict(claim_generator)),
    }


def component_anti_collision(points: Sequence[Sequence[float]], denominator_limit: int = 64) -> dict[str, Any]:
    """Anti-collision of both coordinate components against rationals i/d, d <= limit.

    ``pinn.governance.nodes.anti_collision`` is the trusted 1D rule and takes its
    limit positionally; a 2D node collides with a rational lattice point exactly
    when one of its components does, so the rule is applied per component rather
    than rewritten. The annulus adds a third quantity worth reporting -- the radial
    coordinate -- because its nodes are built in (t, theta) and a collision there
    would not show up in x or y alone.
    """

    xs = sorted({float(p[0]) for p in points})
    ys = sorted({float(p[1]) for p in points})
    radii = sorted({geo.radius(p) for p in points})
    ax = anti_collision(xs, denominator_limit)
    ay = anti_collision(ys, denominator_limit)
    ar = anti_collision(radii, denominator_limit)
    smallest = min(ax.min_distance, ay.min_distance, ar.min_distance)
    return {"x": {"minDistance": ax.min_distance}, "y": {"minDistance": ay.min_distance},
            "radius": {"minDistance": ar.min_distance}, "minDistance": smallest,
            "ok": smallest > 1e-12, "denominatorLimit": denominator_limit}


def isolation_report(sets: Mapping[str, Mapping[str, Any]], *, min_separation: float | None) -> dict[str, Any]:
    """Sample-level mutual exclusion, plus the geometry membership of every set.

    Two things must hold before a formal run: no sample is shared between the
    training pool, the dev set, the physics grid and the opened claim member, and
    no set holds a point that is not strictly inside the annulus. In a multiply
    connected domain the second half is not implied by the first.
    """

    loaded = {name: load_evaluation_set(document) for name, document in sets.items()}
    errors = list(disjointness_errors(loaded, min_separation=min_separation))
    membership = {}
    for name, document in sets.items():
        points = points_of(document)
        report = geo.membership_report(points)
        membership[name] = {"counts": report["counts"], "illegal": len(report["illegal"]),
                            "sampleCount": len(points),
                            "radialRange": [min(geo.radius(p) for p in points), max(geo.radius(p) for p in points)]}
        if report["illegal"]:
            errors.append(f"{name}: {len(report['illegal'])} points are not strictly inside the annulus")
    return {"errors": errors, "minSeparation": min_separation, "membership": membership,
            "geometryId": geo.GEOMETRY["geometryId"],
            "sampleSetHashes": {name: sample_set_hash(document) for name, document in sets.items()},
            "artifactHashes": {name: canonical_sha256(document) for name, document in sets.items()}}
