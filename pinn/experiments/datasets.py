"""Evaluation sets of the Poisson 1D calibration experiment (Constitution 9.1).

D_train  = a fixed, preregistered pool of interior collocation points (uniform
           random in (0,1) from ``poolSeed``) plus the two boundary points.  A
           run's *sampling seed* chooses which ``collocationCount`` pool points it
           trains on; the pool itself is the training-visible set the spec names.
D_dev    = uniform random interior points from ``devSeed`` (diagnostics, tuning,
           seed statistics, failure analysis, discriminating experiments).
D_phys   = Gauss-Legendre nodes of order ``physOrder`` (public, deterministic;
           physics checks G5a, Gate 2a reference verification).
D_claim  = the frozen protocol grids GL512 (quadrature) and CGL2000 (pointwise)
           without the two endpoints -- {0, 1} are spec-known boundary
           coordinates that also sit in D_train (protocol L1
           ``boundaryIdentityExempt``); they are evaluated as boundary values,
           never as claim samples.

Disjointness is proven sample-wise with ``pinn.governance.evaluation_sets``;
NumPy is needed only to generate the Gauss-Legendre nodes.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from pinn.governance.canonical import canonical_sha256
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set, validate_evaluation_set

SCHEMA_VERSION = "pinn.evaluationSet/1.0"


def gauss_legendre_unit(order: int) -> tuple[list[float], list[float]]:
    """GL nodes / weights of ``order`` mapped from [-1, 1] to [0, 1] (float64, NumPy generator)."""

    import numpy as np

    nodes, weights = np.polynomial.legendre.leggauss(int(order))
    return [float(v) for v in 0.5 * (nodes + 1.0)], [float(v) for v in 0.5 * weights]


def cgl_unit(count: int) -> list[float]:
    return [0.5 * (1.0 - math.cos(j * math.pi / (count - 1))) for j in range(count)]


def uniform_interior(size: int, seed: int) -> list[float]:
    """Uniform random points strictly inside (0, 1); deterministic in ``seed``."""

    import numpy as np

    rng = np.random.default_rng(int(seed))
    points = rng.random(int(size), dtype=np.float64)
    values = [float(v) for v in points]
    if any(v <= 0.0 or v >= 1.0 for v in values):
        raise ValueError("generator produced a boundary value; choose another seed")
    if len(set(values)) != len(values):
        raise ValueError("generator produced a duplicate coordinate; choose another seed")
    return values


def manifest(artifact_id: str, role: str, samples: Sequence[dict[str, Any]], *, generator: dict[str, str]) -> dict[str, Any]:
    document = {
        "schemaVersion": SCHEMA_VERSION,
        "artifactId": artifact_id,
        "role": role,
        "inputNames": ["x"],
        "generator": generator,
        "samples": list(samples),
    }
    errors = validate_evaluation_set(document)
    if errors:
        raise ValueError(f"{artifact_id}: {errors[0]}")
    return document


def interior(points: Sequence[float]) -> list[dict[str, Any]]:
    return [{"inputs": [float(x)], "kind": "interior"} for x in points]


def build_sets(config: dict[str, Any], *, claim_nodes: Sequence[float], claim_pointwise: Sequence[float],
               claim_label: str) -> dict[str, dict[str, Any]]:
    """The four manifests of one ProblemDefinition revision.

    ``claim_nodes`` / ``claim_pointwise`` are the frozen protocol grids (or, for a
    later revision whose first claim set was burnt, a fresh preregistered pair).
    """

    sets = config["sets"]
    pool = uniform_interior(config["sampling"]["poolSize"], config["sampling"]["poolSeed"])
    train = manifest(
        f"set-train-{claim_label}", "train",
        interior(pool) + [{"inputs": [0.0], "kind": "boundary"}, {"inputs": [1.0], "kind": "boundary"}],
        generator={"generatorId": "numpy.default_rng.random", "generatorVersion": "numpy-2.4",
                   "seedRef": f"poolSeed={config['sampling']['poolSeed']}"},
    )
    dev = manifest(
        f"set-dev-{claim_label}", "dev", interior(uniform_interior(sets["devSize"], sets["devSeed"])),
        generator={"generatorId": "numpy.default_rng.random", "generatorVersion": "numpy-2.4",
                   "seedRef": f"devSeed={sets['devSeed']}"},
    )
    phys_nodes, _ = gauss_legendre_unit(sets["physOrder"])
    phys = manifest(
        f"set-phys-{claim_label}", "phys", interior(phys_nodes),
        generator={"generatorId": f"gauss-legendre-{sets['physOrder']}", "generatorVersion": "numpy.polynomial.legendre.leggauss"},
    )
    claim_points = [x for x in list(claim_nodes) + list(claim_pointwise) if x != 0.0 and x != 1.0]
    claim = manifest(
        f"set-claim-{claim_label}", "claim", interior(claim_points),
        generator={"generatorId": claim_label, "generatorVersion": "frozen protocol grids without spec-known boundary coordinates"},
    )
    return {"train": train, "dev": dev, "phys": phys, "claim": claim}


def isolation_report(sets: dict[str, dict[str, Any]], *, min_separation: float | None) -> dict[str, Any]:
    loaded = {role: load_evaluation_set(doc) for role, doc in sets.items()}
    errors = disjointness_errors(loaded, min_separation=min_separation)
    pairs = {}
    roles = list(loaded)
    for i, a in enumerate(roles):
        for b in roles[i + 1:]:
            shared = len(set(loaded[a].identities) & set(loaded[b].identities))
            pairs[f"{a}|{b}"] = {"sharedSamples": shared}
    return {
        "sampleIdentityRule": "canonical_sha256({inputs: [float64 x], quantity: null}); -0.0 folded into 0.0; NaN/Inf rejected; kind is metadata",
        "minSeparation": min_separation,
        "sizes": {role: len(doc["samples"]) for role, doc in sets.items()},
        "hashes": {role: canonical_sha256(doc) for role, doc in sets.items()},
        "pairwise": pairs,
        "errors": errors,
        "disjoint": not errors,
    }


def points_of(document: dict[str, Any], kind: str | None = None) -> list[float]:
    return [s["inputs"][0] for s in document["samples"] if kind is None or s["kind"] == kind]


def claim_pool_manifests(pool: "dict[str, tuple[int, int]]", *, label: str) -> dict[str, dict[str, Any]]:
    """Fresh claim sets of the grid family {GL_n} U {CGL_m without endpoints} (Experiment 3 preregistration, section 2)."""

    manifests: dict[str, dict[str, Any]] = {}
    for name, (gl_order, cgl_count) in pool.items():
        nodes, _ = gauss_legendre_unit(gl_order)
        points = [x for x in nodes + cgl_unit(cgl_count) if x != 0.0 and x != 1.0]
        manifests[name] = manifest(
            f"set-claim-{label}-{name}", "claim", interior(points),
            generator={"generatorId": name, "generatorVersion": f"gauss-legendre-{gl_order} + chebyshev-gauss-lobatto-{cgl_count} without spec-known boundary coordinates"},
        )
    return manifests


def claim_grid(gl_order: int, cgl_count: int) -> tuple[list[float], list[float], list[float]]:
    nodes, weights = gauss_legendre_unit(gl_order)
    return nodes, weights, cgl_unit(cgl_count)
