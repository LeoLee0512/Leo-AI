"""Evaluation sets of the Poisson 2D calibration experiment (Constitution 9.1).

D_train  = a preregistered pool of uniform random interior points of (0,1)^2
           (``numpy.default_rng(poolSeed)``); a run's sampling seed chooses the
           ``collocationCount`` pool points it trains on.  With the hard
           boundary parameterization there is no boundary loss term, so the
           training set contains interior points only.
D_dev    = uniform random interior points from ``devSeed`` (diagnostics, seed
           statistics, failure analysis, Red Team, reproduction comparison).
D_phys   = tensor Gauss-Legendre nodes of order ``physOrder`` with product
           weights (physics checks G5a; public and deterministic).
D_claim  = a preregistered member of the blind claim pool: the tensor GL grid of
           order n (quadrature metrics) together with the interior tensor
           Chebyshev-Gauss-Lobatto grid of count m (pointwise metrics).  Claim
           identity follows the samples (``sampleSetHash``), never the artifact
           bytes.

The boundary evaluation nodes (four edges, Gauss-Legendre in arc length) are
spec-known boundary coordinates: like the two endpoints in the 1D protocol they
are exempt from sample identity (protocol L1 ``boundaryIdentityExempt``) and are
stored as their own artifact, not as an evaluation set.

Dimension-independent helpers (``gauss_legendre_unit``, ``cgl_unit``) are reused
from the 1D module; everything else here is the 2D construction.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from pinn.experiments.datasets import cgl_unit, gauss_legendre_unit
from pinn.governance.canonical import canonical_sha256
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set, validate_evaluation_set
from pinn.governance.nodes import anti_collision

SCHEMA_VERSION = "pinn.evaluationSet/1.0"
INPUT_NAMES = ["x", "y"]


def tensor_grid(nodes_x: Sequence[float], nodes_y: Sequence[float]) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x in nodes_x for y in nodes_y]


def tensor_weights(weights_x: Sequence[float], weights_y: Sequence[float]) -> list[float]:
    return [float(wx) * float(wy) for wx in weights_x for wy in weights_y]


def gauss_legendre_square(order: int) -> tuple[list[tuple[float, float]], list[float]]:
    nodes, weights = gauss_legendre_unit(order)
    return tensor_grid(nodes, nodes), tensor_weights(weights, weights)


def cgl_interior_square(count: int) -> list[tuple[float, float]]:
    """Interior tensor CGL nodes: the boundary lines x, y in {0, 1} are removed."""

    nodes = [v for v in cgl_unit(count) if v != 0.0 and v != 1.0]
    return tensor_grid(nodes, nodes)


def uniform_interior(size: int, seed: int) -> list[tuple[float, float]]:
    """Uniform random points strictly inside (0,1)^2; deterministic in ``seed``."""

    import numpy as np

    rng = np.random.default_rng(int(seed))
    raw = rng.random((int(size), 2), dtype=np.float64)
    points = [(float(a), float(b)) for a, b in raw]
    for x, y in points:
        if x <= 0.0 or x >= 1.0 or y <= 0.0 or y >= 1.0:
            raise ValueError("generator produced a boundary coordinate; choose another seed")
    if len(set(points)) != len(points):
        raise ValueError("generator produced a duplicate point; choose another seed")
    return points


def boundary_nodes(order: int) -> tuple[list[tuple[float, float]], list[float]]:
    """Gauss-Legendre nodes along the four edges with arc-length weights summing to the perimeter 4."""

    nodes, weights = gauss_legendre_unit(order)
    points: list[tuple[float, float]] = []
    edge_weights: list[float] = []
    for t, weight in zip(nodes, weights):
        points.append((0.0, float(t)))
        edge_weights.append(float(weight))
    for t, weight in zip(nodes, weights):
        points.append((1.0, float(t)))
        edge_weights.append(float(weight))
    for t, weight in zip(nodes, weights):
        points.append((float(t), 0.0))
        edge_weights.append(float(weight))
    for t, weight in zip(nodes, weights):
        points.append((float(t), 1.0))
        edge_weights.append(float(weight))
    return points, edge_weights


def samples(points: Sequence[Sequence[float]], kind: str = "interior") -> list[dict[str, Any]]:
    return [{"inputs": [float(x), float(y)], "kind": kind} for x, y in points]


def manifest(artifact_id: str, role: str, points: Sequence[Sequence[float]], *, generator: Mapping[str, str]) -> dict[str, Any]:
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


def claim_member_points(gl_order: int, cgl_count: int) -> list[tuple[float, float]]:
    return gauss_legendre_square(gl_order)[0] + cgl_interior_square(cgl_count)


def claim_pool_manifests(pool: Mapping[str, tuple[int, int]], *, label: str) -> dict[str, dict[str, Any]]:
    """Blind claim sets of the 2D grid family {tensor GL_n} U {interior tensor CGL_m}."""

    manifests: dict[str, dict[str, Any]] = {}
    for name, (gl_order, cgl_count) in pool.items():
        points = claim_member_points(gl_order, cgl_count)
        if len(set(points)) != len(points):
            raise ValueError(f"{name}: the GL and CGL grids of this member share a point")
        manifests[name] = manifest(
            f"set-claim-{label}-{name}", "claim", points,
            generator={"generatorId": name,
                       "generatorVersion": f"tensor gauss-legendre-{gl_order} + interior tensor chebyshev-gauss-lobatto-{cgl_count}"},
        )
    return manifests


def build_sets(config: Mapping[str, Any], *, claim_points: Sequence[Sequence[float]], claim_artifact_id: str,
               claim_generator: Mapping[str, str], label: str) -> dict[str, dict[str, Any]]:
    sets_cfg = config["sets"]
    pool = uniform_interior(config["sampling"]["poolSize"], config["sampling"]["poolSeed"])
    train = manifest(
        f"set-train-{label}", "train", pool,
        generator={"generatorId": "numpy.default_rng.random((n,2))", "generatorVersion": "numpy-2.4",
                   "seedRef": f"poolSeed={config['sampling']['poolSeed']}"},
    )
    dev = manifest(
        f"set-dev-{label}", "dev", uniform_interior(sets_cfg["devSize"], sets_cfg["devSeed"]),
        generator={"generatorId": "numpy.default_rng.random((n,2))", "generatorVersion": "numpy-2.4",
                   "seedRef": f"devSeed={sets_cfg['devSeed']}"},
    )
    phys_points, _ = gauss_legendre_square(sets_cfg["physOrder"])
    phys = manifest(
        f"set-phys-{label}", "phys", phys_points,
        generator={"generatorId": f"tensor-gauss-legendre-{sets_cfg['physOrder']}",
                   "generatorVersion": "numpy.polynomial.legendre.leggauss (tensor product)"},
    )
    claim = manifest(claim_artifact_id, "claim", claim_points, generator=claim_generator)
    return {"train": train, "dev": dev, "phys": phys, "claim": claim}


def points_of(document: Mapping[str, Any]) -> list[tuple[float, float]]:
    return [(float(s["inputs"][0]), float(s["inputs"][1])) for s in document["samples"]]


def component_anti_collision(points: Sequence[Sequence[float]], denominator_limit: int = 64) -> dict[str, Any]:
    """Anti-collision of both coordinate components against rationals i/d, d <= limit.

    ``pinn.governance.nodes.anti_collision`` is the 1D rule; a 2D node collides
    with a rational lattice point exactly when one of its components does, so the
    existing (trusted) rule is applied per component instead of being rewritten.
    """

    xs = sorted({float(p[0]) for p in points})
    ys = sorted({float(p[1]) for p in points})
    ax = anti_collision(xs, denominator_limit)
    ay = anti_collision(ys, denominator_limit)
    return {"x": {"minDistance": ax.min_distance}, "y": {"minDistance": ay.min_distance},
            "minDistance": min(ax.min_distance, ay.min_distance),
            "ok": min(ax.min_distance, ay.min_distance) > 1e-12, "denominatorLimit": denominator_limit}


def isolation_report(sets: Mapping[str, Mapping[str, Any]], *, min_separation: float | None) -> dict[str, Any]:
    loaded = {role: load_evaluation_set(doc) for role, doc in sets.items()}
    errors = disjointness_errors(loaded, min_separation=min_separation)
    pairs = {}
    roles = list(loaded)
    for i, a in enumerate(roles):
        for b in roles[i + 1:]:
            pairs[f"{a}|{b}"] = {"sharedSamples": len(set(loaded[a].identities) & set(loaded[b].identities))}
    return {
        "sampleIdentityRule": "canonical_sha256({inputs: [float64 x, float64 y], quantity: null}); -0.0 folded into 0.0; NaN/Inf rejected; kind is metadata",
        "inputNames": list(INPUT_NAMES),
        "minSeparation": min_separation,
        "sizes": {role: len(doc["samples"]) for role, doc in sets.items()},
        "hashes": {role: canonical_sha256(doc) for role, doc in sets.items()},
        "pairwise": pairs,
        "errors": errors,
        "disjoint": not errors,
    }
