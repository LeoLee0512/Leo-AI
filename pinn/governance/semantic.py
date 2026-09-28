"""Cross-document semantic validation not expressible in plain JSON Schema."""

from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path
from typing import Any, Iterable, Mapping

from .nodes import anti_collision, combined_data_sha256, data_sha256, read_npy_f64
from .poisson_contract import check_spec_contract, check_protocol_contract, check_manifest_contract


CONTENT_FIELDS = (
    "title",
    "scientificQuestion",
    "equations",
    "dependentVariables",
    "independentVariables",
    "domain",
    "geometry",
    "initialConditions",
    "boundaryConditions",
    "parameters",
    "units",
    "dimensionalForm",
    "nondimensionalForm",
    "referenceScales",
    "assumptions",
    "targetQuantities",
    "referenceSolution",
    "trainingDomain",
    "validationDomain",
    "validationMetrics",
    "acceptanceCriteria",
    "knownSingularities",
    "knownNumericalRisks",
)
NEVER_NOT_APPLICABLE = frozenset(
    {
        "scientificQuestion",
        "equations",
        "dependentVariables",
        "independentVariables",
        "domain",
        "boundaryConditions",
        "parameters",
        "targetQuantities",
        "validationMetrics",
        "acceptanceCriteria",
        "trainingDomain",
        "validationDomain",
    }
)
PLACEHOLDERS = frozenset({"", "n/a", "na", "none", "-", "tbd", "not applicable"})


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        if value in seen:
            duplicate.add(value)
        seen.add(value)
    return duplicate


def validate_spec(spec: Mapping[str, Any]) -> list[str]:
    errors: list[str] = check_spec_contract(spec)
    for field in CONTENT_FIELDS:
        wrapper = spec.get(field)
        if not isinstance(wrapper, dict):
            errors.append(f"spec.{field} must be an applicability object")
            continue
        applicability = wrapper.get("applicability")
        if applicability not in {"APPLICABLE", "NOT_APPLICABLE"}:
            errors.append(f"spec.{field}.applicability is invalid")
        elif applicability == "APPLICABLE" and "value" not in wrapper:
            errors.append(f"spec.{field} is APPLICABLE but has no value")
        elif applicability == "NOT_APPLICABLE":
            reason = wrapper.get("reason")
            if not isinstance(reason, str) or reason.strip().lower() in PLACEHOLDERS:
                errors.append(f"spec.{field} has an invalid NOT_APPLICABLE reason")
            if field in NEVER_NOT_APPLICABLE:
                errors.append(f"spec.{field} may never be NOT_APPLICABLE")

    if spec.get("lockedAt") is not None:
        errors.append("spec.lockedAt must remain null; lock.json is the authority")
    if any(key in spec for key in ("specSha256", "protocolSha256", "lockSha256")):
        errors.append("spec must not contain digest fields")

    metrics = spec.get("validationMetrics", {}).get("value", [])
    acceptances = spec.get("acceptanceCriteria", {}).get("value", [])
    metric_ids = [item.get("id") for item in metrics if isinstance(item, dict)]
    acceptance_ids = [item.get("id") for item in acceptances if isinstance(item, dict)]
    for duplicate in sorted(_duplicates(str(value) for value in metric_ids)):
        errors.append(f"duplicate validation metric id: {duplicate}")
    for duplicate in sorted(_duplicates(str(value) for value in acceptance_ids)):
        errors.append(f"duplicate acceptance id: {duplicate}")
    metric_id_set = set(metric_ids)
    for index, item in enumerate(acceptances):
        if not isinstance(item, dict):
            continue
        metric_ref = item.get("metricRef")
        if metric_ref not in metric_id_set:
            errors.append(
                f"acceptanceCriteria[{index}].metricRef {metric_ref!r} does not uniquely reference a metric"
            )

    primary = spec.get("referenceSolution", {}).get("value", {}).get("primary", {})
    provenance = primary.get("provenance", {}) if isinstance(primary, dict) else {}
    expected = {
        "artifactRole": "REFERENCE",
        "producerType": "TRUSTED_ANALYTIC_REFERENCE",
        "captureMethod": "ANALYTIC_EVALUATION",
    }
    for key, value in expected.items():
        if provenance.get(key) != value:
            errors.append(f"analytic primary reference requires {key}={value}")
    for key in (
        "evaluatorSourcePath",
        "evaluatorCodeSha256",
        "equationBinding",
        "specBinding",
        "registeredBy",
    ):
        if not provenance.get(key):
            errors.append(f"analytic primary reference is missing {key}")
    return errors


def _recursive_digest_keys(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"specSha256", "protocolSha256", "lockSha256"}:
                errors.append(f"{path}.{key} is a forbidden self/cross digest")
            errors.extend(_recursive_digest_keys(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_recursive_digest_keys(item, f"{path}[{index}]"))
    return errors


def _check_source_hash(record: Mapping[str, Any], repo_root: Path, label: str) -> list[str]:
    path_value = record.get("generatorSourcePath") or record.get("evaluatorSourcePath")
    digest_value = record.get("generatorImplementationSha256") or record.get("evaluatorCodeSha256")
    if not isinstance(path_value, str) or not isinstance(digest_value, str):
        return [f"{label} source path/hash is missing"]
    source = (repo_root / path_value).resolve()
    if Path(path_value).is_absolute() or not source.is_relative_to(repo_root.resolve()):
        return [f"{label} source path escapes repository"]
    try:
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
    except OSError as exc:
        return [f"{label} source cannot be read: {exc}"]
    return [] if actual == digest_value else [f"{label} source hash mismatch"]


def _asset_path(repo_root: Path, record: Mapping[str, Any]) -> Path:
    value = record["path"]
    if not isinstance(value, str):
        raise ValueError("asset path must be a string")
    path = (repo_root / value).resolve()
    if Path(value).is_absolute() or not path.is_relative_to(repo_root.resolve()):
        raise ValueError("asset path escapes repository")
    return path


def validate_protocol(protocol: Mapping[str, Any], *, repo_root: Path) -> list[str]:
    errors = _recursive_digest_keys(protocol) + check_protocol_contract(protocol)

    pointwise = protocol.get("pointwiseGrid", {})
    cgl_artifact = pointwise.get("artifact", {}) if isinstance(pointwise, dict) else {}
    try:
        cgl_path = _asset_path(repo_root, cgl_artifact)
        cgl = read_npy_f64(cgl_path)
        artifact_sha = hashlib.sha256(cgl_path.read_bytes()).hexdigest()
        if artifact_sha != cgl_artifact.get("artifactSha256"):
            errors.append("CGL2000 artifact SHA-256 mismatch")
        if data_sha256(cgl) != cgl_artifact.get("dataSha256"):
            errors.append("CGL2000 data-byte SHA-256 mismatch")
        if len(cgl) != pointwise.get("nodeCount"):
            errors.append("CGL2000 artifact shape/nodeCount mismatch")
        if not cgl or cgl[0] != 0 or cgl[-1] != 1 or any(not math.isfinite(x) for x in cgl) or any(a >= b for a, b in zip(cgl, cgl[1:])):
            errors.append("CGL2000 nodes must be finite, strictly ordered and span [0,1]")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, struct.error, SyntaxError, UnicodeError) as exc:
        cgl = ()
        errors.append(f"CGL2000 artifact invalid: {exc}")

    quadrature = protocol.get("quadrature", {})
    assets = quadrature.get("artifacts", {}) if isinstance(quadrature, dict) else {}
    try:
        nodes_record = assets["nodes"]
        weights_record = assets["weights"]
        gl_nodes_path = _asset_path(repo_root, nodes_record)
        gl_weights_path = _asset_path(repo_root, weights_record)
        gl_nodes = read_npy_f64(gl_nodes_path)
        gl_weights = read_npy_f64(gl_weights_path)
        for label, record, path in (
            ("GL512 nodes", nodes_record, gl_nodes_path),
            ("GL512 weights", weights_record, gl_weights_path),
        ):
            if hashlib.sha256(path.read_bytes()).hexdigest() != record.get("artifactSha256"):
                errors.append(f"{label} artifact SHA-256 mismatch")
        if data_sha256(gl_nodes) != nodes_record.get("dataSha256"):
            errors.append("GL512 nodes data-byte SHA-256 mismatch")
        if data_sha256(gl_weights) != weights_record.get("dataSha256"):
            errors.append("GL512 weights data-byte SHA-256 mismatch")
        if combined_data_sha256(gl_nodes, gl_weights) != quadrature.get("combinedDataSha256"):
            errors.append("GL512 combined data-byte SHA-256 mismatch")
        if len(gl_nodes) != 512 or len(gl_weights) != 512:
            errors.append("GL512 artifact shape mismatch")
        if any(not math.isfinite(x) or not 0 < x < 1 for x in gl_nodes) or any(a >= b for a,b in zip(gl_nodes, gl_nodes[1:])):
            errors.append("GL512 nodes must be finite, unique, ordered interior coordinates")
        if any(not math.isfinite(w) or w <= 0 for w in gl_weights) or abs(math.fsum(gl_weights) - 1.0) > 1e-12:
            errors.append("GL512 weights must be finite, positive and integrate unity")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, struct.error, SyntaxError, UnicodeError) as exc:
        gl_nodes = ()
        errors.append(f"GL512 artifacts invalid: {exc}")

    errors.extend(_check_source_hash(pointwise.get("generatorProvenance", {}), repo_root, "CGL2000 generator"))
    errors.extend(_check_source_hash(quadrature.get("generatorProvenance", {}), repo_root, "GL512 generator"))

    measured = protocol.get("antiCollision", {}).get("measured", {})
    tolerance = protocol.get("antiCollision", {}).get("tolerance")
    for name, values in (("CGL2000", cgl), ("GL512", gl_nodes)):
        if not values:
            continue
        for d_max, key in ((12, "dLe12"), (64, "dLe64")):
            result = anti_collision(values, d_max)
            if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or result.min_distance <= tolerance:
                errors.append(f"{name} antiCollision d<={d_max} FAIL")
            record = measured.get(name, {}).get(key, {})
            if record.get("worstDenominator") != result.denominator:
                errors.append(f"{name} antiCollision {key} denominator mismatch")
            stored_distance = record.get("minDistance")
            if not isinstance(stored_distance, (int, float)) or not math.isfinite(stored_distance) or abs(stored_distance - result.min_distance) > 1e-18:
                errors.append(f"{name} antiCollision {key} distance mismatch")

    leakage = protocol.get("leakageProtocol", {})
    checks = {item.get("id"): item for item in leakage.get("checks", []) if isinstance(item, dict)}
    l1 = checks.get("L1", {})
    if l1.get("holdoutValidationSets") != ["GL512", "CGL2000"]:
        errors.append("L1 must name exactly GL512 and CGL2000 as holdout sets")
    if l1.get("specKnownBoundarySet") != "BOUNDARY" or not l1.get("boundaryIdentityExempt"):
        errors.append("L1 must exempt the spec-known BOUNDARY coordinates")
    if "boundary" in l1.get("trainingSideSets", []):
        errors.append("L1 training-side identity sets must not treat the BC set as holdout leakage")
    l4 = checks.get("L4", {})
    required_consumers = {
        "optimizer",
        "adaptive sampler",
        "early-stopping controller",
        "loss-weight scheduler",
        "architecture selector",
        "hyperparameter tuner",
    }
    if set(l4.get("forbiddenConsumers", [])) != required_consumers:
        errors.append("L4 forbidden-consumer set is incomplete")

    policy = protocol.get("provenancePolicy", {})
    if "TRUSTED_ANALYTIC_REFERENCE" not in policy.get("producerTypes", []):
        errors.append("provenance producerTypes lacks TRUSTED_ANALYTIC_REFERENCE")
    analytic = policy.get("analyticReference", {})
    if analytic.get("captureMethod") != "ANALYTIC_EVALUATION":
        errors.append("analytic reference captureMethod is not machine typed")
    return errors


def validate_manifest(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = check_manifest_contract(manifest)
    cases = manifest.get("cases", [])
    case_ids = [case.get("caseId") for case in cases if isinstance(case, dict)]
    if len(case_ids) != manifest.get("conceptualCaseCount"):
        errors.append("conceptualCaseCount does not equal the number of case IDs")
    if len(set(case_ids)) != len(case_ids):
        errors.append("duplicate conceptual caseId")
    expected_ids = {"G1", *(f"B{i}" for i in range(1, 12)), "U1", "U2", "U3"}
    if set(case_ids) != expected_ids:
        errors.append("core manifest must contain exactly G1, B1-B11 and U1-U3")

    scenario_ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        for scenario in case.get("subcases", []):
            scenario_id = scenario.get("subcaseId")
            scenario_ids.append(scenario_id)
            if scenario.get("category") == "EMPIRICAL_CHALLENGE":
                errors.append(f"{scenario_id}: EMPIRICAL_CHALLENGE is forbidden in core")
            expected = scenario.get("expected", {})
            required_expected = {
                "gateStatus",
                "workflowStatus",
                "claimStatus",
                "failureRecord",
                "stopTheLine",
            }
            missing = required_expected - set(expected)
            if missing:
                errors.append(f"{scenario_id}: expected verdict missing {sorted(missing)}")
            mode = scenario.get("testMode")
            if mode == "VALIDATOR_COMPONENT":
                if expected.get("workflowStatus") != "NOT_APPLICABLE":
                    errors.append(f"{scenario_id}: component test must not fabricate workflow state")
                if any(value != "NOT_APPLICABLE" for value in expected.get("claimStatus", {}).values()):
                    errors.append(f"{scenario_id}: component test must not fabricate ClaimStatus")
            elif expected.get("workflowStatus") == "NOT_APPLICABLE":
                errors.append(f"{scenario_id}: E2E test requires a formal workflow state")

    if len(scenario_ids) != manifest.get("executableScenarioCount"):
        errors.append("executableScenarioCount does not equal atomic subcase count")
    if len(set(scenario_ids)) != len(scenario_ids):
        errors.append("duplicate subcaseId")
    by_case = {case.get("caseId"): case for case in cases if isinstance(case, dict)}
    if [item.get("subcaseId") for item in by_case.get("B1", {}).get("subcases", [])] != ["B1a", "B1b"]:
        errors.append("B1 must define atomic subcases B1a and B1b")
    if [item.get("subcaseId") for item in by_case.get("B9", {}).get("subcases", [])] != ["B9a", "B9b", "B9c"]:
        errors.append("B9 must define atomic subcases B9a, B9b and B9c")
    return errors


def validate_lock_draft(lock: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "specSha256",
        "protocolSha256",
        "adversarialManifestSha256",
        "lockedAt",
        "lockSha256",
    ):
        if lock.get(key) is not None:
            errors.append(f"lock draft {key} must be null")
    if lock.get("lockState") != "DRAFT":
        errors.append("lock draft lockState must be DRAFT")
    expected_order = [
        "specSha256",
        "protocolSha256",
        "adversarialManifestSha256",
        "constitutionSha256",
        "constitutionVersion",
        "lockVersion",
        "lockedAt",
    ]
    definition = lock.get("lockSha256Definition", {})
    if definition.get("fieldOrder") != expected_order:
        errors.append("lock payload field order is not the registered seven-field order")
    return errors
