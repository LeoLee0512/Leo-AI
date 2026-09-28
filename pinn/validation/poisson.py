"""AC-1..AC-8 arithmetic for the Poisson-1D candidate, isolated from any model.

This API accepts raw field samples, including separately evaluated derivatives.
It has no optimizer, checkpoint loader, Gate transition or Accuracy Claim API.
Until authorized formal locking and execution exist, all outputs are explicitly
VALIDATOR_COMPONENT diagnostics. Callers must not treat fixture success as a
validated scientific run. Formal provenance/leakage admission remains separate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
from typing import Callable, Mapping, Sequence

from pinn.governance.canonical import canonical_bytes, strict_json_loads
from pinn.governance.nodes import combined_data_sha256, data_sha256, read_npy_f64
from pinn.governance.poisson_contract import CRITERIA, METRICS, check_protocol_contract, check_spec_contract
from pinn.reference import analytic_poisson as reference


EPSILON = 1e-30
THRESHOLDS = tuple(criterion[1] for criterion in CRITERIA)
REFERENCE_SHA256 = "d792fd0ec91827bb6fcf38039893839024517c603bb4e5efcd0f7fe54b30a06d"
ASSET_SHA256 = {
    "GL512_nodes.npy": "1d50c2db39cdfa8d741e23e9152a3cb8665991a8885c2e3ea5a505eae4e993db",
    "GL512_weights.npy": "f1fc34beda32cf34e6a0e7b6b9f98486d4833b2aed94a04a189bda203deb8ebd",
    "CGL2000.npy": "81e98be345a69e0859097557533defa0b533b57f930b60db9fd9200482d23773",
}


class ValidationInputError(ValueError):
    """Invalid evidence must never be coerced into a finite, accepted result."""


def _float64(value: object, label: str) -> float:
    # Reject integers, strings, booleans, complex values, float32 and nested arrays.
    # Native Python float and NumPy float64 are binary64. No dtype widening.
    if not isinstance(value, float):
        raise ValidationInputError(f"{label} must be a float64 scalar")
    value = float(value)
    if not math.isfinite(value):
        raise ValidationInputError(f"{label} must be finite")
    return value


def _vector(values: Sequence[float], size: int, label: str) -> tuple[float, ...]:
    try:
        if len(values) != size:
            raise ValidationInputError(f"{label} shape must be ({size},)")
        return tuple(_float64(value, f"{label}[{i}]") for i, value in enumerate(values))
    except TypeError as exc:
        raise ValidationInputError(f"{label} must be a one-dimensional float64 sequence") from exc


@dataclass(frozen=True)
class PoissonProtocol:
    quadrature_nodes: tuple[float, ...]
    quadrature_weights: tuple[float, ...]
    pointwise_nodes: tuple[float, ...]
    spec_sha256: str
    protocol_sha256: str
    reference_sha256: str
    spec_bytes: bytes = field(repr=False)
    protocol_bytes: bytes = field(repr=False)


def _candidate_documents(spec_bytes: bytes, protocol_bytes: bytes) -> tuple[dict, dict]:
    documents = []
    for label, raw in (("spec", spec_bytes), ("protocol", protocol_bytes)):
        try:
            document = strict_json_loads(raw.decode("utf-8"))
            if raw != canonical_bytes(document):
                raise ValidationInputError(f"candidate {label} bytes are not canonical")
        except (UnicodeDecodeError, ValueError, TypeError, AttributeError) as exc:
            raise ValidationInputError(f"invalid candidate {label}: {exc}") from exc
        documents.append(document)
    spec, protocol = documents
    contract_errors = check_spec_contract(spec) + check_protocol_contract(protocol)
    if contract_errors:
        raise ValidationInputError("; ".join(contract_errors))
    return spec, protocol


def load_candidate_protocol(repository_root: str | Path) -> PoissonProtocol:
    """Read exact candidate assets; never regenerate, lock, or alter any input."""
    root = Path(repository_root).resolve()
    spec_path = root / "governance/POISSON_1D_V1.0_spec.draft.json"
    protocol_path = root / "governance/POISSON_1D_V1.0_protocol.draft.json"
    try:
        spec_bytes, protocol_bytes = spec_path.read_bytes(), protocol_path.read_bytes()
        spec, protocol = _candidate_documents(spec_bytes, protocol_bytes)
        criteria = spec["acceptanceCriteria"]["value"]
        expected = [
            {"id": f"AC-{i}", "metricRef": f"AC-{i}", "comparator": "<", "threshold": threshold,
             "level": "SHOULD" if i == 8 else "MUST"}
            for i, threshold in enumerate(THRESHOLDS, 1)
        ]
        if criteria != expected:
            raise ValidationInputError("candidate acceptance contract differs from implemented AC-1..AC-8")
        if protocol["numerics"]["epsilon"] != EPSILON:
            raise ValidationInputError("candidate epsilon differs from 1e-30")
        if protocol["canonicalExecutor"]["dtype"] != "float64" or protocol["canonicalExecutor"]["device"] != "cpu":
            raise ValidationInputError("candidate executor must be CPU float64")
        reference_path = root / "pinn/reference/analytic_poisson.py"
        reference_hash = hashlib.sha256(reference_path.read_bytes()).hexdigest()
        if reference_hash != REFERENCE_SHA256:
            raise ValidationInputError("registered analytic reference source hash mismatch")
        records = (
            protocol["quadrature"]["artifacts"]["nodes"],
            protocol["quadrature"]["artifacts"]["weights"],
            protocol["pointwiseGrid"]["artifact"],
        )
        arrays = []
        for record, filename, size in zip(records, ASSET_SHA256, (512, 512, 2000)):
            relative_path = Path("specs/poisson-1d/v1.0/assets") / filename
            if record["path"] != relative_path.as_posix():
                raise ValidationInputError(f"unexpected asset path for {filename}")
            path = root / relative_path
            raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if raw_hash != record["artifactSha256"] or raw_hash != ASSET_SHA256[filename]:
                raise ValidationInputError(f"asset hash mismatch: {filename}")
            values = _vector(read_npy_f64(path), size, filename)
            if data_sha256(values) != record["dataSha256"]:
                raise ValidationInputError(f"asset payload hash mismatch: {filename}")
            arrays.append(values)
        if combined_data_sha256(*arrays[:2]) != protocol["quadrature"]["combinedDataSha256"]:
            raise ValidationInputError("GL512 combined data hash mismatch")
        result = PoissonProtocol(*arrays, hashlib.sha256(spec_bytes).hexdigest(),
                                 hashlib.sha256(protocol_bytes).hexdigest(), reference_hash,
                                 spec_bytes, protocol_bytes)
        _verify_protocol_arrays(result)
        return result
    except (KeyError, TypeError, OSError, json.JSONDecodeError, IndexError) as exc:
        raise ValidationInputError(f"candidate protocol is incomplete or malformed: {exc}") from exc


def _verify_protocol_arrays(protocol: PoissonProtocol) -> None:
    _candidate_documents(protocol.spec_bytes, protocol.protocol_bytes)
    if (hashlib.sha256(protocol.spec_bytes).hexdigest() != protocol.spec_sha256
            or hashlib.sha256(protocol.protocol_bytes).hexdigest() != protocol.protocol_sha256
            or protocol.reference_sha256 != REFERENCE_SHA256):
        raise ValidationInputError("candidate metadata hash mismatch")
    gl = _vector(protocol.quadrature_nodes, 512, "GL512 coordinates")
    weights = _vector(protocol.quadrature_weights, 512, "GL512 weights")
    cgl = _vector(protocol.pointwise_nodes, 2000, "CGL2000 coordinates")
    if any(not 0.0 < x < 1.0 for x in gl):
        raise ValidationInputError("GL512 must be in the open unit interval")
    if cgl[0] != 0.0 or cgl[-1] != 1.0 or any(not 0.0 <= x <= 1.0 for x in cgl):
        raise ValidationInputError("CGL2000 must span the exact closed unit interval")
    if any(a >= b for nodes in (gl, cgl) for a, b in zip(nodes, nodes[1:])):
        raise ValidationInputError("validation coordinates must be strictly increasing")
    if any(w <= 0.0 for w in weights) or abs(math.fsum(weights) - 1.0) > 1e-14:
        raise ValidationInputError("GL512 weights must be positive and sum to one")
    # Payload hashes also prevent an in-memory dataclass replacement bypassing load.
    expected = ("803f12cb60359b02e14e57b4676a04baab5dd27042e259265d5b3c476b13a6c3",
                "d37cccc49beb2db5e27532b82796ca2424efc3908e94db1bc82431579d1f7048",
                "59d84b0eaf599b81d9add5fcb99fcd105d5922ae5c044a2ee589ef9971f5b6ff")
    if any(data_sha256(values) != digest for values, digest in zip((gl, weights, cgl), expected)):
        raise ValidationInputError("validation protocol payload differs from the candidate assets")


@dataclass(frozen=True)
class FieldSamples:
    """Raw field arrays; derivatives must already be evaluated independently.

    Array positions are bound to exact coordinates, not inferred from their size.
    A future adapter may populate this structure without importing a PINN class.
    Derivative/provenance assertions here are component metadata, not runner trust.
    """

    quadrature_coordinates: Sequence[float]
    pointwise_coordinates: Sequence[float]
    boundary_coordinates: Sequence[float]
    u_quadrature: Sequence[float]
    du_quadrature: Sequence[float]
    d2u_quadrature: Sequence[float]
    u_pointwise: Sequence[float]
    u_boundary: Sequence[float]
    du_boundary: Sequence[float]
    forcing_quadrature: Sequence[float]
    domain: tuple[float, float] = (0.0, 1.0)
    boundary_values: tuple[float, float] = (0.0, 0.0)
    equation_binding: str = reference.EQUATION_BINDING
    derivative_method: str = "CLOSED_FORM_SYMBOLIC"
    device: str = "cpu"


def sample_callable_fixture(
    protocol: PoissonProtocol,
    solution: Callable[[float], float],
    first_derivative: Callable[[float], float],
    second_derivative: Callable[[float], float],
    *,
    forcing: Callable[[float], float] = reference.forcing,
) -> FieldSamples:
    """Sample a closed-form fixture. This never impersonates a trained run."""
    gl, cgl, boundary = protocol.quadrature_nodes, protocol.pointwise_nodes, (0.0, 1.0)
    return FieldSamples(
        gl, cgl, boundary,
        tuple(solution(x) for x in gl), tuple(first_derivative(x) for x in gl),
        tuple(second_derivative(x) for x in gl), tuple(solution(x) for x in cgl),
        tuple(solution(x) for x in boundary), tuple(first_derivative(x) for x in boundary),
        tuple(forcing(x) for x in gl),
    )


def _ratio(numerator: float, denominator: float, label: str, *, epsilon: bool = False) -> float:
    if not math.isfinite(numerator) or numerator < 0.0:
        raise ValidationInputError(f"{label} has an invalid numerator")
    if not math.isfinite(denominator) or denominator <= 1e6 * EPSILON:
        raise ValidationInputError(f"{label} denominator is not above 1e6 * epsilon")
    value = numerator / (denominator + EPSILON if epsilon else denominator)
    if not math.isfinite(value):
        raise ValidationInputError(f"{label} produced a non-finite metric")
    return value


def check_metric_values(values: Mapping[str, float]) -> dict[str, bool]:
    """Strict metric shape/value checking; missing, extra and NaN are errors."""
    if set(values) != {f"AC-{i}" for i in range(1, 9)}:
        raise ValidationInputError("metrics must contain exactly AC-1 through AC-8")
    result = {}
    for i, threshold in enumerate(THRESHOLDS, 1):
        key = f"AC-{i}"
        value = _float64(values[key], key)
        if value < 0.0:
            raise ValidationInputError(f"{key} must not be negative")
        result[key] = value < threshold
    return result


def evaluate_samples(protocol: PoissonProtocol, samples: FieldSamples) -> dict:
    """Compute independent analytic errors and criteria, never a formal verdict."""
    _verify_protocol_arrays(protocol)
    if _vector(samples.domain, 2, "domain") != (0.0, 1.0):
        raise ValidationInputError("domain must equal [0,1]")
    if _vector(samples.boundary_values, 2, "boundary values") != (0.0, 0.0):
        raise ValidationInputError("candidate Dirichlet boundary values must both be zero")
    if samples.equation_binding != reference.EQUATION_BINDING:
        raise ValidationInputError("equation binding differs from the candidate Poisson problem")
    if samples.device != "cpu":
        raise ValidationInputError("candidate executor requires CPU")
    if samples.derivative_method not in {"CLOSED_FORM_SYMBOLIC", "AUTOGRAD_FIRST_AND_SECOND_ORDER"}:
        raise ValidationInputError("derivative method must be closed-form or first/second-order autograd")
    for given, expected, label in (
        (samples.quadrature_coordinates, protocol.quadrature_nodes, "GL512 coordinates"),
        (samples.pointwise_coordinates, protocol.pointwise_nodes, "CGL2000 coordinates"),
        (samples.boundary_coordinates, (0.0, 1.0), "boundary coordinates"),
    ):
        if _vector(given, len(expected), label) != expected:
            raise ValidationInputError(f"{label} do not match the exact protocol")
    u, du, d2u, f = (
        _vector(values, 512, name)
        for name, values in (("u quadrature", samples.u_quadrature), ("du quadrature", samples.du_quadrature),
                             ("d2u quadrature", samples.d2u_quadrature), ("forcing", samples.forcing_quadrature))
    )
    uc = _vector(samples.u_pointwise, 2000, "u pointwise")
    ub = _vector(samples.u_boundary, 2, "u boundary")
    dub = _vector(samples.du_boundary, 2, "du boundary")
    if (uc[0], uc[-1]) != ub:
        raise ValidationInputError("pointwise and boundary outputs disagree at the same exact endpoints")
    x, w = protocol.quadrature_nodes, protocol.quadrature_weights
    exact_u = tuple(reference.solution(point) for point in x)
    exact_du = tuple(reference.first_derivative(point) for point in x)
    exact_cgl = tuple(reference.solution(point) for point in protocol.pointwise_nodes)
    exact_f = tuple(reference.forcing(point) for point in x)
    # Declared forcing is audited, but the residual always uses the reference f.
    if any(abs(given - exact) > 1e-12 for given, exact in zip(f, exact_f)):
        raise ValidationInputError("declared forcing does not match pi^2*sin(pi*x)")
    try:
        integral = lambda values: math.fsum(weight * value for weight, value in zip(w, values))
        l2_squared = integral((value - exact) ** 2 for value, exact in zip(u, exact_u))
        derivative_l2_squared = integral((value - exact) ** 2 for value, exact in zip(du, exact_du))
        absolute_linf = max(abs(value - exact) for value, exact in zip(uc, exact_cgl))
        residuals = tuple(-second - forcing_value for second, forcing_value in zip(d2u, exact_f))
        residual_rms = math.sqrt(integral(value * value for value in residuals))
        integral_u = integral(u)
        derivative_energy = integral(value * value for value in du)
        forcing_energy = integral(force * value for force, value in zip(exact_f, u))
        values = {
            "AC-1": math.sqrt(_ratio(l2_squared, integral(value * value for value in exact_u), "AC-1", epsilon=True)),
            "AC-2": _ratio(absolute_linf, max(abs(value) for value in exact_cgl), "AC-2", epsilon=True),
            "AC-3": max(abs(value) for value in ub),
            "AC-4": _ratio(residual_rms, math.pi**2 / math.sqrt(2.0), "AC-4"),
            "AC-5": _ratio(abs(integral_u - 2.0 / math.pi), 2.0 / math.pi, "AC-5"),
            "AC-6": _ratio(abs(dub[0] - math.pi), math.pi, "AC-6"),
            "AC-7": _ratio(abs(derivative_energy - forcing_energy), math.pi**2 / 2.0, "AC-7"),
            "AC-8": math.sqrt(_ratio(derivative_l2_squared, integral(value * value for value in exact_du), "AC-8", epsilon=True)),
        }
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValidationInputError("metric computation overflowed; result rejected") from exc
    satisfied = check_metric_values(values)
    metrics = {
        key: {"value": value, "threshold": THRESHOLDS[i - 1], "comparator": "<",
              "level": "SHOULD" if i == 8 else "MUST", "units": "dimensionless",
              "formula": METRICS[i - 1][0], "sampleSet": METRICS[i - 1][1],
              "aggregation": ("weighted L2 norm", "maximum absolute difference",
                              "maximum absolute boundary difference", "weighted residual RMS",
                              "absolute integral difference", "absolute derivative difference at zero",
                              "absolute energy-integral difference", "weighted derivative L2 norm")[i - 1],
              "normalization": ("GL512 weighted reference L2 with epsilon",
                                "maximum absolute reference value on CGL2000 with epsilon",
                                "none", "pi^2/sqrt(2)", "2/pi", "pi", "pi^2/2",
                                "GL512 weighted reference derivative L2 with epsilon")[i - 1],
              "criterionSatisfied": satisfied[key]}
        for i, (key, value) in enumerate(values.items(), 1)
    }
    diagnostics = {
        "absoluteL2": math.sqrt(l2_squared), "absoluteLinf": absolute_linf,
        "pdeResidualRms": residual_rms, "pdeResidualMax": max(abs(v) for v in residuals),
        "integralU": integral_u, "unweightedBoundaryMeanSquare": math.fsum(v * v for v in ub) / 2.0,
        "derivativeAtZero": dub[0], "derivativeEnergy": derivative_energy,
        "forcingEnergy": forcing_energy, "referencePointwiseMaximum": max(abs(v) for v in exact_cgl),
    }
    for key, value in diagnostics.items():
        _float64(value, key)
    diagnostics["boundaryResiduals"] = list(ub)
    return {
        "evaluationScope": "VALIDATOR_COMPONENT",
        "workflowStatus": "NOT_APPLICABLE",
        "claimStatus": "NOT_APPLICABLE",
        "trainingApplicable": False,
        "lockStatus": "NOT_EXECUTED",
        "specCandidateSha256": protocol.spec_sha256,
        "protocolCandidateSha256": protocol.protocol_sha256,
        "referenceSourceSha256": protocol.reference_sha256,
        "derivativeMethod": samples.derivative_method,
        "device": samples.device,
        "dtype": "float64",
        "componentCriteriaSatisfied": all(satisfied[f"AC-{i}"] for i in range(1, 8)),
        "failedMustCriteria": [f"AC-{i}" for i in range(1, 8) if not satisfied[f"AC-{i}"]],
        "failedShouldCriteria": [] if satisfied["AC-8"] else ["AC-8"],
        "metrics": metrics,
        "diagnostics": diagnostics,
        "diagnosticDefinitions": {
            "absoluteL2": {"formula": "sqrt(sum_GL512 w*(u-u*)^2)", "sampleSet": "GL512", "units": "dimensionless"},
            "absoluteLinf": {"formula": "max_CGL2000 |u-u*|", "sampleSet": "CGL2000", "units": "dimensionless"},
            "pdeResidualRms": {"formula": "sqrt(sum_GL512 w*(-u''-f)^2)", "sampleSet": "GL512", "units": "dimensionless"},
            "pdeResidualMax": {"formula": "max_GL512 |-u''-f|", "sampleSet": "GL512", "units": "dimensionless"},
            "unweightedBoundaryMeanSquare": {"formula": "(u(0)^2+u(1)^2)/2", "sampleSet": "BOUNDARY", "units": "dimensionless"},
            "acceptanceThresholds": "Only AC-1..AC-8 define acceptance criteria; these auxiliary diagnostics add no threshold.",
            "trainingLoss": "NOT_APPLICABLE: fixture diagnostics are not training loss histories.",
        },
        "sampling": {"quadrature": "GL512", "quadratureCount": 512,
                     "pointwise": "CGL2000", "pointwiseCount": 2000, "boundary": [0.0, 1.0],
                     "evaluationSeed": "NOT_APPLICABLE", "epsilon": EPSILON},
        "limitations": ["Component evidence is not an ExperimentRun or a formal Gate.",
                        "Training provenance, leakage admission and repeatability are separate obligations.",
                        "Sampled arrays cannot establish that their derivative metadata is truthful."],
    }
