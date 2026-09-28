"""Executable mathematical contract for the existing Poisson-1D v1 candidate.

This is an implementation check of MVP plan sections 9--11, not a new spec.
Changing the problem or metrics requires a reviewed spec version and adapter;
an arbitrary string in a generic applicability wrapper is not verification.
"""

from __future__ import annotations

import math
from typing import Any, Mapping


SEEDS = [20260904, 20260905, 20260906, 20260907, 20260908]
CRITERIA = [(f"AC-{i}", limit, "SHOULD" if i == 8 else "MUST")
            for i, limit in enumerate((.001, .005, .0001, .01, .001, .005, .01, .005), 1)]
METRICS = [
    ("sqrt( int (u_theta - u*)^2 dx / (int (u*)^2 dx + eps) )", "GL512"),
    ("max_j |u_theta - u*| / (max_j |u*| + eps)", "CGL2000"),
    ("max over x in {0,1} of |u_theta(x) - g(x)|", "boundarySet"),
    ("sqrt(int R^2 dx) / ||f||_rms", "GL512"),
    ("|int u_theta dx - 2/pi| / (2/pi)", "GL512"),
    ("|u_theta'(0) - pi| / pi", "boundarySet"),
    ("|int (u_theta')^2 dx - int f*u_theta dx| / (pi^2/2)", "GL512"),
    ("sqrt( int (u_theta' - u*')^2 dx / (int (u*')^2 dx + eps) )", "GL512"),
]


def _same(actual: Any, expected: Any) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, (int, float)):
        return math.isfinite(actual) and actual == expected
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            _same(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _same(a, b) for a, b in zip(actual, expected))
    return actual == expected


def check_paths(document: Mapping[str, Any], expectations: Mapping[str, Any], label: str) -> list[str]:
    errors = []
    for path, expected in expectations.items():
        actual: Any = document
        for key in path.split("."):
            actual = actual.get(key) if isinstance(actual, Mapping) else None
        if not _same(actual, expected):
            errors.append(f"{label}.{path} differs from the Poisson-1D v1 contract")
    return errors


def check_spec_contract(spec: Mapping[str, Any]) -> list[str]:
    expectations = {
        "specId": "poisson-1d-dirichlet", "version": "1.0", "evidenceLevel": "A",
        "equations.value.governing": "-u''(x) = f(x),  x in (0,1)",
        "equations.value.forcing": "f(x) = pi^2 * sin(pi*x)",
        "equations.value.equationCount": 1, "equations.value.unknownCount": 1,
        "domain.value": {"interior": "(0, 1)", "closure": "[0, 1]", "boundary": [0., 1.], "dimension": 1},
        "boundaryConditions.value": [
            {"location": "x = 0", "type": "Dirichlet", "operator": "u", "g": 0.},
            {"location": "x = 1", "type": "Dirichlet", "operator": "u", "g": 0.}],
        "parameters.value.free": [],
        "parameters.value.fixed": {"forcing_wavenumber_k": 1, "forcing_amplitude": "pi^2"},
        "dependentVariables.value": [{"symbol": "u", "meaning": "scalar field", "range": "real", "networkOutputIndex": 0}],
        "independentVariables.value": [{"symbol": "x", "meaning": "spatial coordinate", "networkInputIndex": 0}],
        "units.value": "Dimensionless throughout. x, u and f are pure numbers by construction. Dimensional consistency (Article 6-3) is trivially satisfied: every term of -u'' - f carries the same (null) dimension.",
        "nondimensionalForm.value": "-u''(x) = pi^2*sin(pi*x), x in (0,1), u(0)=u(1)=0. This coincides with the as-posed form, because no nondimensionalisation step was performed.",
        "trainingDomain.value.collocation": "interior samples in (0,1)",
        "trainingDomain.value.adaptivePool": "interior samples in (0,1)",
        "trainingDomain.value.diagnostic": "interior samples in (0,1), diagnostics only — must not trigger early stopping",
        "trainingDomain.value.boundary": [0., 1.], "validationDomain.value.boundarySet": [0., 1.],
        "validationDomain.value.quadratureNodes": "512 Gauss-Legendre nodes mapped to [0,1] — AC-1, AC-4, AC-5, AC-7, AC-8, and the holdout residual set",
        "validationDomain.value.pointwiseGrid": "2000 Chebyshev-Gauss-Lobatto nodes, x_j = (1 - cos(j*pi/1999))/2 — AC-2",
        "targetQuantities.value": [
            {"id": "QoI-1", "definition": "integral of u over [0,1]", "exactValue": "2/pi", "exactValueDecimal": 0.6366197723675814, "boundTo": "AC-5"},
            {"id": "QoI-2", "definition": "u'(0)", "exactValue": "pi", "exactValueDecimal": 3.141592653589793, "boundTo": "AC-6"}],
        "validationMetrics.referenceConstants": {"f_rms": 6.978864199639, "integral_u_star": 0.6366197723675814,
                                                  "u_star_prime_at_0": 3.141592653589793, "energy_both_sides": 4.934802200545},
        "initialConditions.applicability": "NOT_APPLICABLE",
        "dimensionalForm.applicability": "NOT_APPLICABLE",
        "referenceScales.applicability": "NOT_APPLICABLE",
        "referenceSolution.value.primary.form": "u*(x) = sin(pi*x)",
        "referenceSolution.value.primary.derivative": "u*'(x) = pi*cos(pi*x)",
        "referenceSolution.value.primary.provenance.equationBinding": "-u''(x)=pi^2*sin(pi*x);x in (0,1);u(0)=u(1)=0",
        "referenceSolution.value.primary.provenance.specBinding": "poisson-1d-dirichlet@1.0",
        "referenceSolution.value.primary.provenance.evaluatorSourcePath": "pinn/reference/analytic_poisson.py",
        "referenceSolution.value.primary.provenance.registeredBy": "pinn.reference.analytic_poisson",
        "referenceSolution.value.primary.provenance.transformation": "IDENTITY",
    }
    errors = check_paths(spec, expectations, "spec")
    try:
        metrics = spec["validationMetrics"]["value"]
        criteria = spec["acceptanceCriteria"]["value"]
        expected_criteria = [dict(id=i, metricRef=i, comparator="<", threshold=t, level=l) for i, t, l in CRITERIA]
        if not _same(criteria, expected_criteria):
            errors.append("spec acceptance criteria must retain all AC-1..AC-8, comparators, thresholds and MUST/SHOULD levels")
        if not isinstance(metrics, list) or len(metrics) != 8:
            errors.append("spec requires exactly eight registered validation metrics")
        else:
            for i, (item, (formula, grid)) in enumerate(zip(metrics, METRICS), 1):
                errors.extend(check_paths(item, {"id": f"AC-{i}", "definition": formula, "grid": grid}, "metric"))
    except (KeyError, TypeError):
        errors.append("spec metric/acceptance structure is malformed")
    return errors


def check_protocol_contract(protocol: Mapping[str, Any]) -> list[str]:
    return check_paths(protocol, {
        "protocolId": "poisson-1d-eval-protocol", "version": "1.0",
        "specRef": "spec.json", "manifestRef": "adversarial/core_manifest.json",
        "canonicalExecutor.device": "cpu", "canonicalExecutor.dtype": "float64",
        "canonicalExecutor.mixedPrecision": False, "canonicalExecutor.dtypeWidenUsed": False,
        "canonicalExecutor.determinism.torchUseDeterministicAlgorithms": True,
        "quadrature.id": "GL512", "quadrature.nodeCount": 512,
        # These are already frozen NPY assets under plan 9.3/14, not caller-
        # chosen weights. Self-consistent replacement hashes prove no identity.
        "quadrature.combinedDataSha256": "f0a29f490f7ebd79979e91ab23eea870791f9b7e1578154d7e3b6ce432adf2eb",
        "quadrature.artifacts.nodes.artifactSha256": "1d50c2db39cdfa8d741e23e9152a3cb8665991a8885c2e3ea5a505eae4e993db",
        "quadrature.artifacts.weights.artifactSha256": "f1fc34beda32cf34e6a0e7b6b9f98486d4833b2aed94a04a189bda203deb8ebd",
        "pointwiseGrid.artifact.artifactSha256": "81e98be345a69e0859097557533defa0b533b57f930b60db9fd9200482d23773",
        "pointwiseGrid.id": "CGL2000", "pointwiseGrid.nodeCount": 2000,
        "pointwiseGrid.includesEndpoints": True,
        "boundarySet.points": [0., 1.], "boundarySet.id": "BOUNDARY",
        "antiCollision.dMax": 64, "antiCollision.tolerance": 1e-12,
        "aliasingResolution.minResolvedMode": 64,
        "numerics.epsilon": 1e-30, "evaluationSeed.applicability": "NOT_APPLICABLE",
        "derivativeEvaluation.method": "AUTOGRAD_FIRST_ORDER",
        "fdmProtocol.nSequence": [32, 64, 128, 256, 512, 1024, 2048],
        "fdmProtocol.K": 4, "fdmProtocol.orderInterval": [1.8, 2.2],
        "fdmProtocol.neverEntersAcceptanceCriteria": True,
        "seeds.values": SEEDS, "seeds.preregistered": True,
        "acceptanceCriteriaBinding.must": [f"AC-{i}" for i in range(1, 8)],
        "acceptanceCriteriaBinding.should": ["AC-8"],
        "gate2a.checks": [
            {"id": "res", "quantity": "max |-u*'' - f| over GL512", "tolerance": 1e-12, "toleranceId": "tol_residual"},
            {"id": "bc", "quantity": "max(|u*(0)|, |u*(1)|)", "tolerance": 1e-14, "toleranceId": "tol_bc"}],
    }, "protocol")


def check_manifest_contract(manifest: Mapping[str, Any]) -> list[str]:
    """Expected verdicts are preregistered facts, not merely well-typed strings."""
    components = {
        "B1a": ("G3", "IMPLEMENTATION", "REJECT_IMPLEMENTATION", False),
        "B1b": ("G5", "VALIDATION", "REFUTE_PREDICTION", False),
        "B2": ("G3", "IMPLEMENTATION", "REJECT_CODE_CONFIG_MISMATCH", False),
        "B3": ("G5", "LOSS_BALANCE", "REJECT_AC_3", False),
        "B4": ("G5", "SAMPLING", "REJECT_AC_1_AND_AC_4", False),
        "B5": ("G3", "SCALING", "REJECT_SCALING", False),
        "B6": ("G5", "SAMPLING", "REJECT_AC_1_AND_AC_4", False),
        "B7": ("G5", "VALIDATION", "DETECT_VALIDATION_LEAKAGE", True),
        "B9a": ("G5", "PROVENANCE", "REJECT_PROVENANCE", True),
        "B9b": ("G5", "PROVENANCE", "REJECT_PROVENANCE", True),
        "B9c": ("G5", "PROVENANCE", "REJECT_MANUAL_SELF_PROMOTION", True),
        "B10": ("G4", "NUMERICAL", "TERMINATE_NONFINITE", True),
        "B11": ("G2", "BASELINE", "REJECT_MISSING_REFINEMENT_EVIDENCE", False),
    }
    errors = check_paths(manifest, {
        "conceptualCaseCount": 15, "executableScenarioCount": 18,
        "expectedVerdictRegistration.declaredBeforeFirstExecution": True,
        "expectedVerdictRegistration.resultIndependent": True,
        "expectedVerdictRegistration.lockBindingField": "adversarialManifestSha256",
    }, "manifest")
    scenarios = {s["subcaseId"]: s for c in manifest["cases"] for s in c["subcases"]}
    if set(scenarios) != set(components) | {"G1", "B8", "U1", "U2", "U3"}:
        errors.append("manifest atomic scenario identities differ from the registered suite")
    for key, (gate, taxonomy, decision, stop) in components.items():
        scenario = scenarios.get(key, {})
        errors.extend(check_paths(scenario, {
            "testMode": "VALIDATOR_COMPONENT", "expected.gateStatus": {gate: "FAIL"},
            "expected.componentDecision": decision, "expected.failureRecord.required": True,
            "expected.failureRecord.taxonomy": taxonomy, "expected.stopTheLine": stop,
        }, key))
    errors.extend(check_paths(scenarios.get("G1", {}), {
        "testMode": "TRAINING_E2E", "trainingApplicable": True,
        "construction.frozenParameters.seeds": SEEDS,
        "construction.frozenParameters.device": "cpu", "construction.frozenParameters.dtype": "float64",
        "expected.gateStatus": {f"G{i}": "PASS" for i in range(1, 8)},
        "expected.claimStatus": {f"C{i}": "SUPPORTED" for i in range(4)},
        "expected.workflowStatus": "ACCEPTED", "expected.failureRecord.required": False,
        "expected.stopTheLine": False,
    }, "G1"))
    for key in ("B8", "U1", "U2", "U3"):
        errors.extend(check_paths(scenarios.get(key, {}), {
            "testMode": "WORKFLOW_E2E", "expected.claimStatus.C2": "BLOCKED",
            "expected.failureRecord.required": True,
            "expected.stopTheLine": key != "U1",
        }, key))
    errors.extend(check_paths(scenarios.get("B8", {}), {
        "expected.gateStatus": {f"G{i}": "FAIL" if i == 1 else "BLOCKED" for i in range(1, 8)},
        "expected.workflowStatus": "STOPPED_THE_LINE", "expected.failureRecord.taxonomy": "SPEC",
    }, "B8"))
    errors.extend(check_paths(scenarios.get("U1", {}), {
        "construction.frozenParameters.evidenceLevel": "D",
        "construction.frozenParameters.exploratory": True,
        "expected.gateStatus": {"G1": "PASS", "G2": "FAIL", "G3": "PASS", "G4": "PASS", "G5": "BLOCKED", "G6": "PASS"},
        "expected.claimStatus": {"C0": "SUPPORTED", "C1": "SUPPORTED", "C2": "BLOCKED"},
    }, "U1"))
    for key in ("U2", "U3"):
        errors.extend(check_paths(scenarios.get(key, {}), {
            "expected.gateStatus": {**{f"G{i}": "PASS" for i in range(1, 6)}, "G6": "FAIL", "G7": "BLOCKED"},
            "expected.claimStatus": {"C1": "SUPPORTED", "C2": "BLOCKED"},
            "expected.workflowStatus": "FAILURE_RECORDED", "expected.failureRecord.taxonomy": "INFRASTRUCTURE",
        }, key))
    return errors
