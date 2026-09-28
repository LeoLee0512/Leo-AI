"""Validation-leakage audit based on information flow, not proximity."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


HOLDOUT_SET_IDS = ("GL512", "CGL2000")
SPEC_KNOWN_BOUNDARY_SET_ID = "BOUNDARY"
FORBIDDEN_CONSUMERS = frozenset(
    {
        "optimizer",
        "adaptive sampler",
        "early-stopping controller",
        "loss-weight scheduler",
        "architecture selector",
        "hyperparameter tuner",
    }
)


def _ordered_int(value: float) -> int:
    bits = struct.unpack("<q", struct.pack("<d", float(value)))[0]
    return 0x8000_0000_0000_0000 - bits if bits < 0 else bits


def ulp_distance(left: float, right: float) -> int:
    if math.isnan(left) or math.isnan(right):
        return 2**64 - 1
    return abs(_ordered_int(left) - _ordered_int(right))


def coordinate_identity(left: float, right: float, *, max_ulps: int = 8) -> bool:
    if not math.isfinite(left) or not math.isfinite(right):
        return False
    if left == right:  # includes the two IEEE representations of zero
        return True
    return struct.pack("<d", float(left)) == struct.pack("<d", float(right)) or (
        ulp_distance(float(left), float(right)) <= max_ulps
    )


def _is_spec_known_boundary(value: float, boundary: Sequence[float]) -> bool:
    return any(coordinate_identity(value, point) for point in boundary)


@dataclass(frozen=True)
class LeakageFinding:
    check_id: str
    message: str


def audit_leakage(
    *,
    training_sets: Mapping[str, Iterable[float]],
    validation_sets: Mapping[str, Iterable[float]],
    boundary_coordinates: Sequence[float] = (0.0, 1.0),
    validation_consumers: Iterable[str] = (),
    validation_metric_consumers: Iterable[str] = (),
    validation_parent_is_training: bool = False,
    validation_generators: Mapping[str, str] | None = None,
) -> tuple[LeakageFinding, ...]:
    """Return machine findings for L1/L2/L3/L4, including absent metadata.

    L1 compares training coordinates only with *holdout* coordinates.  The
    spec-known boundary is removed from that comparison even though CGL2000
    contains the endpoints.  Consumer feedback remains forbidden for every
    validation metric, including boundary metrics.
    """

    findings: list[LeakageFinding] = []
    if tuple(boundary_coordinates) != (0.0, 1.0):
        findings.append(LeakageFinding("L2", "Poisson boundary coordinates must be (0,1)"))
    generators = validation_generators or {}
    required_sets = (*HOLDOUT_SET_IDS, SPEC_KNOWN_BOUNDARY_SET_ID)
    for set_id in required_sets:
        if set_id not in validation_sets or generators.get(set_id) != set_id:
            findings.append(LeakageFinding("L2", f"missing or invalid coordinate provenance for {set_id}"))
    # Materialize once so generator inputs are not consumed by the audit itself.
    validation_sets = {key: tuple(values) for key, values in validation_sets.items()}
    for key, values in validation_sets.items():
        if not values or any(not math.isfinite(float(x)) or not 0 <= float(x) <= 1 for x in values):
            findings.append(LeakageFinding("L2", f"empty/non-finite/out-of-domain validation set {key}"))
    if validation_sets.get("BOUNDARY") != (0.0, 1.0):
        findings.append(LeakageFinding("L2", "BOUNDARY must contain the exact public endpoints"))
    holdout: list[tuple[str, float]] = []
    for set_id in HOLDOUT_SET_IDS:
        for value in validation_sets.get(set_id, ()):  # missing sets are schema errors
            number = float(value)
            if not _is_spec_known_boundary(number, boundary_coordinates):
                holdout.append((set_id, number))

    for training_name, values in training_sets.items():
        for value in values:
            number = float(value)
            if not math.isfinite(number) or not 0 <= number <= 1:
                findings.append(LeakageFinding("L1", f"invalid training coordinate in {training_name}"))
                continue
            for set_id, validation_value in holdout:
                if coordinate_identity(number, validation_value):
                    findings.append(
                        LeakageFinding(
                            "L1",
                            f"training set {training_name!r} contains holdout coordinate "
                            f"from {set_id}: {validation_value!r}",
                        )
                    )
                    break

    if validation_parent_is_training:
        findings.append(
            LeakageFinding("L3", "validation artifact descends from a training artifact")
        )

    for source, consumers in (
        ("validation coordinates", validation_consumers),
        ("validation metrics", validation_metric_consumers),
    ):
        for consumer in consumers:
            if consumer in FORBIDDEN_CONSUMERS:
                findings.append(
                    LeakageFinding("L4", f"{source} were read by forbidden {consumer!r}")
                )
    return tuple(findings)
