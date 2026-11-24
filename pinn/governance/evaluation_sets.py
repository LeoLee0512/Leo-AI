"""Evaluation-set manifests and sample-level disjointness (Amendment A-0001, draft 3).

Review finding (2026-09-15, issue 2): ``H(A) != H(B)`` does not imply
``A and B are disjoint``.  Three distinct artifact hashes only prove three
different files.  The isolation the Constitution's chapter 9 demands is
between the *samples* the model can see during training and the samples it
is judged on.  This module gives every evaluation sample a canonical identity
and checks the sets pairwise.

An evaluation set is a manifest document (``evaluation-set.schema.json``):

* ``inputNames``: the network-input coordinates in order (``["x"]``,
  ``["x", "t"]``, ``["x", "t", "mu"]`` for a parametric problem -- a
  parametric input is an input, so ``(x, t, mu1)`` and ``(x, t, mu2)`` are
  different samples by identity; their closeness is a *separation* question);
* ``samples[]``: ``{"inputs": [...], "kind": interior|boundary|initial|observation,
  "quantity"?: name}`` -- ``kind`` is metadata (a boundary point is still a
  location the model saw), ``quantity`` is part of the identity only for
  observations (inverse problems: an observation of ``u`` at ``x`` and of
  ``p`` at the same ``x`` are different observations; their shared location
  is again caught by separation).

Sample identity = canonical hash of ``{"inputs": [float64...], "quantity": ...}``.
Floats are compared at full float64 precision through the canonical JSON
serializer (shortest round-trip repr, so identity is exact bit identity with
``-0.0`` folded into ``0.0``); NaN and infinities are rejected.  "Almost the
same coordinates" is deliberately *not* identity: it is handled by the
optional preregistered ``minSeparation`` of the ProblemDefinition, which
requires every dev / claim sample to lie at least that far (Euclidean, in
the nondimensional input space) from every training-visible sample.  The
separation check is O(N*M) pure Python; that is acceptable for the MVP set
sizes and is run once per frozen spec.

The manifest's canonical hash is the artifact hash the ProblemDefinition
references, so the disjointness proof is tied to exactly the sets the spec
names.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256
from .jsonschema_lite import validate as validate_schema

SCHEMA_DIR = Path(__file__).with_name("schemas")
EVALUATION_SET_SCHEMA = "evaluation-set.schema.json"
EVALUATION_SET_VERSION = "pinn.evaluationSet/1.0"

#: Named sets of a ProblemDefinition and whether the model may see them while training.
TRAINING_VISIBLE_ROLES: tuple[str, ...] = ("train",)
HELD_OUT_ROLES: tuple[str, ...] = ("dev", "claim")
#: Physics-check nodes (Kimi R2 section 1.1, D_phys) are public and
#: deterministic but must not coincide with training points either: a residual
#: evaluated on trained-on points is not evidence.
AUXILIARY_ROLES: tuple[str, ...] = ("phys",)
SET_ROLES: tuple[str, ...] = TRAINING_VISIBLE_ROLES + HELD_OUT_ROLES + AUXILIARY_ROLES
SAMPLE_KINDS: tuple[str, ...] = ("interior", "boundary", "initial", "observation")


def _load_schema() -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / EVALUATION_SET_SCHEMA).read_text(encoding="utf-8"))


def _canonical_inputs(inputs: Sequence[object], path: str, errors: list[str]) -> tuple[float, ...] | None:
    values: list[float] = []
    for index, raw in enumerate(inputs):
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            errors.append(f"{path}.inputs[{index}]: {raw!r} is not a number")
            return None
        number = float(raw)
        if not math.isfinite(number):
            errors.append(f"{path}.inputs[{index}]: coordinates must be finite")
            return None
        values.append(0.0 if number == 0.0 else number)   # fold -0.0 into 0.0
    return tuple(values)


def sample_identity(inputs: Sequence[float], quantity: str | None = None) -> str:
    """The canonical identity of one evaluation sample."""

    errors: list[str] = []
    canonical = _canonical_inputs(inputs, "sample", errors)
    if canonical is None:
        raise ValueError(errors[0])
    if quantity is not None and (not isinstance(quantity, str) or not quantity.strip()):
        raise ValueError("quantity must be a non-empty string or None")
    return canonical_sha256({"inputs": list(canonical), "quantity": quantity})


@dataclass(frozen=True)
class EvaluationSet:
    artifact_id: str
    role: str
    input_names: tuple[str, ...]
    identities: tuple[str, ...]
    points: tuple[tuple[float, ...], ...]
    sha256: str


def validate_evaluation_set(document: Any) -> list[str]:
    """Structure, finite coordinates, consistent dimension, no duplicate samples inside one set."""

    errors = validate_schema(document, _load_schema())
    if errors:
        return errors
    width = len(document["inputNames"])
    if len(set(document["inputNames"])) != width:
        errors.append("inputNames: must be distinct")
    seen: set[str] = set()
    for index, sample in enumerate(document["samples"]):
        path = f"samples[{index}]"
        if len(sample["inputs"]) != width:
            errors.append(f"{path}.inputs: expected {width} coordinate(s) for inputNames {document['inputNames']}")
            continue
        canonical = _canonical_inputs(sample["inputs"], path, errors)
        if canonical is None:
            continue
        quantity = sample.get("quantity")
        if sample["kind"] == "observation" and quantity is None:
            errors.append(f"{path}.quantity: an observation must name the observed quantity")
        identity = canonical_sha256({"inputs": list(canonical), "quantity": quantity})
        if identity in seen:
            errors.append(f"{path}: duplicate sample inside the set")
        seen.add(identity)
    return errors


def load_evaluation_set(document: Mapping[str, Any]) -> EvaluationSet:
    """A validated manifest as an ``EvaluationSet`` (raises on the first validation error)."""

    errors = validate_evaluation_set(document)
    if errors:
        raise ValueError(errors[0])
    identities: list[str] = []
    points: list[tuple[float, ...]] = []
    for sample in document["samples"]:
        canonical = _canonical_inputs(sample["inputs"], "sample", errors)
        assert canonical is not None
        identities.append(canonical_sha256({"inputs": list(canonical), "quantity": sample.get("quantity")}))
        points.append(canonical)
    return EvaluationSet(
        artifact_id=document["artifactId"],
        role=document["role"],
        input_names=tuple(document["inputNames"]),
        identities=tuple(identities),
        points=tuple(points),
        sha256=canonical_sha256(document),
    )


def sample_set_hash(document: Mapping[str, Any]) -> str:
    """Identity of the *samples* of an evaluation set: canonical hash of the sorted sample identities.

    Two manifests with the same samples in any order, under any artifactId,
    generator metadata or role, have the same sample-set hash; the artifact
    hash (``canonical_sha256(document)``) does not.  Constitution 9.1 burns the
    claim set that was looked at -- this is the identity that burn follows.
    """

    return canonical_sha256(sorted(load_evaluation_set(document).identities))


def _min_separation(a: Sequence[tuple[float, ...]], b: Sequence[tuple[float, ...]]) -> float:
    best = math.inf
    for p in a:
        for q in b:
            distance = math.sqrt(sum((x - y) ** 2 for x, y in zip(p, q)))
            if distance < best:
                best = distance
                if best == 0.0:
                    return 0.0
    return best


def disjointness_errors(
    sets: Mapping[str, EvaluationSet],
    *,
    min_separation: float | None = None,
) -> list[str]:
    """Pairwise sample-level isolation between the named sets.

    Rules:
    * every training-visible set must share no sample identity with any
      held-out or auxiliary set;
    * the held-out sets (dev, claim) must share no sample identity with each
      other;
    * all sets must have the same input names (otherwise their samples are not
      comparable and the spec is inconsistent);
    * with ``min_separation`` (preregistered, > 0): every dev / claim / phys
      sample must be at least that far from every training-visible sample,
      and dev from claim.
    """

    errors: list[str] = []
    for role, item in sets.items():
        if not isinstance(item, EvaluationSet):
            raise TypeError(f"{role}: {item!r} is not an EvaluationSet")
        if role not in SET_ROLES:
            raise ValueError(f"{role!r} is not an evaluation-set role")
        if item.role != role:
            errors.append(f"{role}: manifest declares role {item.role!r}")
    if min_separation is not None:
        if isinstance(min_separation, bool) or not isinstance(min_separation, (int, float)) \
                or not math.isfinite(min_separation) or min_separation <= 0:
            raise ValueError("min_separation must be a finite positive number")
    names = {item.input_names for item in sets.values()}
    if len(names) > 1:
        errors.append(f"evaluation sets disagree on inputNames: {sorted(names)}")
        return errors

    def check_pair(left: str, right: str) -> None:
        a, b = sets[left], sets[right]
        shared = set(a.identities) & set(b.identities)
        if shared:
            errors.append(f"{left} and {right} share {len(shared)} sample(s); the sets must be disjoint")
        elif min_separation is not None and a.points and b.points:
            distance = _min_separation(a.points, b.points)
            if distance < min_separation:
                errors.append(
                    f"{left} and {right}: closest samples are {distance:.6g} apart, below the preregistered "
                    f"minimum separation {min_separation:.6g}"
                )

    for visible in TRAINING_VISIBLE_ROLES:
        if visible not in sets:
            continue
        for other in HELD_OUT_ROLES + AUXILIARY_ROLES:
            if other in sets:
                check_pair(visible, other)
    if "dev" in sets and "claim" in sets:
        check_pair("dev", "claim")
    return errors
