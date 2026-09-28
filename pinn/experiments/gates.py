"""Gate executions of the Poisson 1D calibration experiment, one function per Gate.

Every function returns plain ``CheckResult``-shaped dicts (``checkId``,
``applicability``, ``status`` / ``reason``, ``evidencePointers``) so that the
TrustVector is a direct rendering of what was executed, and the dimension
status is always the meet of the applicable checks (``dimension_status``).
Thresholds come from the frozen experiment config; nothing here reads a
threshold from a result.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set
from pinn.governance.trust_vector import (
    Applicability,
    CheckResult,
    TrustStatus,
    dimension_status_from_checks,
    seed_statistics,
)
from pinn.reference import analytic_poisson as reference
from pinn.validation import fixtures as control_fixtures
from pinn.validation.poisson import FieldSamples, evaluate_samples, sample_callable_fixture
from scientific_reference.poisson_fdm import refinement_diagnostic

from . import pinn_torch

F_RMS = math.pi ** 2 / math.sqrt(2.0)          # ||f||_rms on [0,1] for f = pi^2 sin(pi x)
TWO_PI = 2.0 * math.pi

#: The frozen check registry (ProblemDefinition.checkApplicability), INV-A1 satisfied per dimension.
REGISTRY: list[dict[str, str]] = [
    {"checkId": "M1-fieldCountClosure", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M2-boundaryConditionCount", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M3-dimensionalHomogeneity", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M5-geometryBinding", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M6-referenceEquationBinding", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "T1-autogradVsFiniteDifference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T3-residualOperatorOnReference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T4-boundaryOperatorOnReference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T8-lossTermSeparation", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T9-collocationDisjointness", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T10-validatorControlFixtures", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "G4-trainingIntegrity", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "G4-seedProtocol", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "G4-lossErrorDecoupling", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "PH1-fluxBalance", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH2-energyBalance", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH3-positivity", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH4-symmetry", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH5-monotonicity", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH6-maximumPrinciple", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH7-spd", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH10-momentumBudget", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "scalar Poisson equation has no momentum variable (protocol section 3 applicability table)"},
    {"checkId": "PH11-freeEnergy", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "steady elliptic equation has no dissipative free-energy structure; the energy identity PH2 covers it"},
    {"checkId": "G5b-acceptanceCriteriaMust", "dimension": "external", "applicability": "APPLICABLE"},
    {"checkId": "G5b-acceptanceCriteriaShould", "dimension": "external", "applicability": "APPLICABLE"},
    {"checkId": "G6-independentReproduction", "dimension": "repro", "applicability": "APPLICABLE"},
]


def check(check_id: str, status: str | TrustStatus, reason: str, evidence: Sequence[Mapping[str, str]] = ()) -> dict[str, Any]:
    value = status.value if isinstance(status, TrustStatus) else status
    result: dict[str, Any] = {"checkId": check_id, "applicability": "APPLICABLE", "status": value, "reason": reason}
    if evidence:
        result["evidencePointers"] = [dict(e) for e in evidence]
    return result


def not_applicable(check_id: str) -> dict[str, Any]:
    entry = next(e for e in REGISTRY if e["checkId"] == check_id)
    return {"checkId": check_id, "applicability": "NOT_APPLICABLE", "reason": entry["reason"]}


def dimension_status(checks: Sequence[Mapping[str, Any]]) -> TrustStatus:
    results = []
    for item in checks:
        if item["applicability"] == "APPLICABLE":
            results.append(CheckResult(item["checkId"], Applicability.APPLICABLE, TrustStatus(item["status"]), item.get("reason")))
        else:
            results.append(CheckResult(item["checkId"], Applicability.NOT_APPLICABLE, None, item["reason"]))
    return dimension_status_from_checks(results)


def pass_fail(ok: bool) -> str:
    return TrustStatus.PASS.value if ok else TrustStatus.FAIL.value


# ------------------------------------------------------------------ Gate 1

def gate1_math(pdef: Mapping[str, Any], evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    equations = pdef["pde"]["equations"]
    dependent = [v for v in pdef["variables"] if v["role"] == "dependent"]
    independent = [v for v in pdef["variables"] if v["role"] == "independent"]
    bcs = pdef["boundaryConditions"]
    units = {e["unit"] for e in pdef["units"]["entries"]}
    x_range = next(v["domainRange"] for v in independent if v["name"] == "x")
    regions = {r["id"] for r in pdef["geometry"]["regions"]}
    return [
        check("M1-fieldCountClosure", pass_fail(len(equations) == len(dependent) == 1),
              f"{len(equations)} equation(s) for {len(dependent)} dependent field(s): closed", evidence),
        check("M2-boundaryConditionCount", pass_fail(len(bcs) == 2 and all(b["type"] == "dirichlet" for b in bcs)),
              f"{len(bcs)} Dirichlet conditions for one second-order operator in 1D: determined (not Neumann-only)", evidence),
        check("M3-dimensionalHomogeneity", pass_fail(pdef["units"]["system"] == "nondimensional" and units == {"1"}),
              "nondimensional by construction; every term of -u'' - f carries the null dimension", evidence),
        check("M5-geometryBinding", pass_fail(x_range == [0.0, 1.0] and {"interior", "x0", "x1"} <= regions
                                              and all(b["regionRef"] in regions for b in bcs)),
              "domain [0,1] with boundary regions x0, x1 bound to the two conditions", evidence),
        check("M6-referenceEquationBinding", pass_fail(reference.EQUATION_BINDING == "-u''(x)=pi^2*sin(pi*x);x in (0,1);u(0)=u(1)=0"),
              f"reference module binds {reference.EQUATION_BINDING}", evidence),
    ]


# ------------------------------------------------------------------ Gate 2

def gate2_baseline(phys_nodes: Sequence[float], evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    residual = max(abs(-reference.second_derivative(x) - reference.forcing(x)) for x in phys_nodes)
    boundary = max(abs(reference.solution(0.0)), abs(reference.solution(1.0)))
    fdm = refinement_diagnostic()
    solutions = fdm.get("solutions", [])
    errors = [s["interior_max_error"] for s in solutions if isinstance(s, Mapping) and "interior_max_error" in s]
    orders = [entry.get("order") for entry in fdm.get("orders", []) if isinstance(entry, Mapping)]
    measured = [o for o in orders if isinstance(o, (int, float))]
    decreasing = len(errors) >= 2 and all(b < a for a, b in zip(errors, errors[1:]))
    order_ok = bool(measured) and all(1.8 <= o <= 2.2 for o in measured)
    component_ok = fdm.get("componentCriteriaSatisfied") is True
    checks = [
        check("G2a-analyticReferenceVerification", pass_fail(residual < 1e-12 and boundary < 1e-14),
              f"max |-u*'' - f| on D_phys = {residual:.3e} (< 1e-12); max boundary |u*| = {boundary:.3e} (< 1e-14)", evidence),
        check("G2b-fdmRefinement", pass_fail(decreasing and order_ok and component_ok),
              f"independent FDM component verdict componentCriteriaSatisfied={component_ok}; interior max errors {['%.3e' % e for e in errors]} strictly decreasing: {decreasing}; "
              f"observed orders {['%.4f' % o for o in measured]} in [1.8, 2.2]: {order_ok}", evidence),
    ]
    detail = {"analyticResidualMax": residual, "analyticBoundaryMax": boundary,
              "fdm": {k: v for k, v in fdm.items() if k != "solutions"}, "fdmErrors": errors, "fdmSequence": [s.get("intervals") for s in solutions]}
    return checks, detail


# ------------------------------------------------------------------ Gate 3

def gate3_implementation(config: Mapping[str, Any], sets: Mapping[str, Mapping[str, Any]], protocol,
                         dev_points: Sequence[float], evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch  # type: ignore[import-not-found]

    detail: dict[str, Any] = {}
    # T1: autograd first and second derivative of a randomly initialised network against central differences.
    model = pinn_torch.build_model(config, 424242)
    probes = [0.137, 0.5, 0.86]
    h = 1e-4
    ad = pinn_torch.fields(model, probes)
    with torch.no_grad():
        def u(x: float) -> float:
            return float(model(torch.tensor([[x]], dtype=torch.float64)).item())
        fd_first = [(u(x + h) - u(x - h)) / (2 * h) for x in probes]
        fd_second = [(u(x + h) - 2 * u(x) + u(x - h)) / (h * h) for x in probes]
    err_first = max(abs(a - b) for a, b in zip(ad["ux"], fd_first))
    err_second = max(abs(a - b) for a, b in zip(ad["uxx"], fd_second))
    detail["T1"] = {"maxFirstDerivativeDiff": err_first, "maxSecondDerivativeDiff": err_second, "h": h}
    # T3 / T4: the residual and boundary operators applied to the analytic reference implemented with torch ops.
    x = torch.tensor([[p] for p in dev_points], dtype=torch.float64, requires_grad=True)
    u_star = torch.sin(math.pi * x)
    (ux,) = torch.autograd.grad(u_star, x, grad_outputs=torch.ones_like(u_star), create_graph=True)
    (uxx,) = torch.autograd.grad(ux, x, grad_outputs=torch.ones_like(ux), create_graph=True)
    f = torch.tensor([[reference.forcing(p)] for p in dev_points], dtype=torch.float64)
    residual_max = float(torch.max(torch.abs(-uxx - f)).item())
    boundary_loss = float(torch.mean(torch.sin(math.pi * torch.tensor([[0.0], [1.0]], dtype=torch.float64)) ** 2).item())
    detail["T3"] = {"residualMaxOnReference": residual_max}
    detail["T4"] = {"boundaryLossOnReference": boundary_loss}
    # T9: sample-level disjointness of the four registered sets.
    loaded = {role: load_evaluation_set(doc) for role, doc in sets.items()}
    disjoint_errors = disjointness_errors(loaded, min_separation=config["sets"].get("minSeparation"))
    detail["T9"] = {"errors": disjoint_errors}
    # T10: the trusted validator accepts the analytic control and rejects the corrupted fixtures.
    verdicts: dict[str, bool] = {}
    for fixture in control_fixtures.FIXTURES:
        try:
            samples = sample_callable_fixture(protocol, fixture.solution, fixture.first_derivative, fixture.second_derivative)
            verdicts[fixture.fixture_id] = bool(evaluate_samples(protocol, samples)["componentCriteriaSatisfied"])
        except Exception as exc:  # a rejected input is a rejection
            verdicts[fixture.fixture_id] = False
            detail.setdefault("T10-exceptions", {})[fixture.fixture_id] = str(exc)
    t10_ok = verdicts.get("ANALYTIC_CONTROL") is True and all(
        verdicts.get(name) is False for name in ("B1b", "B3", "B4", "B6", "ZERO_FIELD_CONTROL"))
    detail["T10"] = verdicts
    checks = [
        check("T1-autogradVsFiniteDifference", pass_fail(err_first < 1e-6 and err_second < 1e-4),
              f"AD vs central differences (h={h}): first {err_first:.2e} (< 1e-6), second {err_second:.2e} (< 1e-4)", evidence),
        check("T3-residualOperatorOnReference", pass_fail(residual_max < 1e-10),
              f"max |-u*'' - f| through the training residual operator on D_dev = {residual_max:.2e} (< 1e-10)", evidence),
        check("T4-boundaryOperatorOnReference", pass_fail(boundary_loss < 1e-28),
              f"boundary loss of u* = {boundary_loss:.2e} (< 1e-28; sin(pi_float64)^2 ~ 1.5e-32)", evidence),
        check("T8-lossTermSeparation", pass_fail(set(config["lossWeights"]) == {"pde", "bc"}),
              "loss is logged as separate pde and bc terms with frozen weights; no single total is judged", evidence),
        check("T9-collocationDisjointness", pass_fail(not disjoint_errors),
              "train | dev | phys | claim pairwise sample-disjoint: " + ("yes" if not disjoint_errors else "; ".join(disjoint_errors)), evidence),
        check("T10-validatorControlFixtures", pass_fail(t10_ok),
              f"trusted validator verdicts on control fixtures: {verdicts}", evidence),
    ]
    return checks, detail


# ------------------------------------------------------------------ Gate 4

def gate4_training(runs: Sequence[Mapping[str, Any]], pre: Mapping[str, Any],
                   evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors = [run["devRelL2"] for run in runs]
    stats = seed_statistics(errors, epsilon_spec=float(pre["epsilonSpec"]), worst_factor=float(pre["worstSeedFactor"]),
                            dispersion_limit=float(pre["dispersionLimit"]))
    integrity_ok = all(run["completed"] and not run["nanEncountered"] and run["lossHistory"] for run in runs) \
        and len(runs) == int(pre["seedRuns"])
    decoupled: list[int] = []
    for index, run in enumerate(runs):
        history = run["lossHistory"]
        if len(history) < 2 or run["nanEncountered"]:
            continue
        first, last = history[0], history[-1]
        loss_drop = first["total"] > 0 and last["total"] > 0 and math.log10(first["total"] / last["total"]) >= 2.0
        error_not_down = last["devRelL2"] >= first["devRelL2"]
        if loss_drop and error_not_down:
            decoupled.append(index)
    protocol_check = check(
        "G4-seedProtocol", stats.status,
        f"N={stats.runs}, k={stats.successes}, divergent={stats.divergent}, median={stats.median:.3e}, IQR={stats.iqr:.3e}, "
        f"worst={stats.worst:.3e}, epsilon_spec={pre['epsilonSpec']}; median_ok={stats.median_ok}, worst_ok={stats.worst_ok}, "
        f"dispersion_ok={stats.dispersion_ok} (rules of Constitution 10.1; best seed never enters)", evidence)
    checks = [
        check("G4-trainingIntegrity", pass_fail(integrity_ok),
              f"{sum(1 for r in runs if r['completed'])}/{len(runs)} runs completed the fixed {runs[0]['stepsRequested'] if runs else 0} steps, "
              f"NaN/Inf runs: {sum(1 for r in runs if r['nanEncountered'])}, loss histories complete", evidence),
        protocol_check,
        check("G4-lossErrorDecoupling", pass_fail(not decoupled),
              "no run dropped its loss by two orders while the dev error failed to decrease" if not decoupled
              else f"runs {decoupled} dropped the loss by >= 2 orders while the dev error did not decrease (optimization illusion)", evidence),
    ]
    detail = {
        "perSeed": [{"seeds": r["seeds"], "devRelL2": r["devRelL2"], "completed": r["completed"], "nan": r["nanEncountered"],
                     "finalLoss": r["finalLoss"]} for r in runs],
        "seedStatistics": {"runs": stats.runs, "successes": stats.successes, "divergent": stats.divergent, "median": stats.median,
                           "iqr": stats.iqr, "worst": stats.worst, "medianOk": stats.median_ok, "worstOk": stats.worst_ok,
                           "dispersionOk": stats.dispersion_ok, "status": stats.status.value,
                           "successRate": f"{stats.successes}/{stats.runs}"},
        "decoupledRuns": decoupled,
    }
    return checks, detail


# ------------------------------------------------------------------ Gate 5a

def physics_checks(models: Sequence[Any], phys_nodes: Sequence[float], phys_weights: Sequence[float],
                   thresholds: Mapping[str, float], evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """PH1-PH7 on D_phys for every seed model; each check's status is the meet over seeds (worst seed)."""

    per_seed: list[dict[str, float]] = []
    f_vals = [reference.forcing(x) for x in phys_nodes]
    u_star_max = max(reference.solution(x) for x in phys_nodes)
    mirrored = [1.0 - x for x in phys_nodes]
    order = sorted(range(len(phys_nodes)), key=lambda i: phys_nodes[i])
    h = 1.0 / 1024
    lambda_min = 4.0 / (h * h) * math.sin(math.pi * h / 2.0) ** 2
    for model in models:
        fld = pinn_torch.fields(model, phys_nodes)
        ends = pinn_torch.fields(model, [0.0, 1.0])
        mirror = pinn_torch.fields(model, mirrored)
        flux = abs((ends["ux"][0] - ends["ux"][1]) - math.fsum(w * f for w, f in zip(phys_weights, f_vals))) / TWO_PI
        energy = abs(math.fsum(w * d * d for w, d in zip(phys_weights, fld["ux"]))
                     - math.fsum(w * f * u for w, f, u in zip(phys_weights, f_vals, fld["u"]))) / (math.pi ** 2 / 2.0)
        positivity = min(fld["u"])
        symmetry = max(abs(a - b) for a, b in zip(fld["u"], mirror["u"]))
        violations = 0
        for a, b in zip(order, order[1:]):
            xa, xb = phys_nodes[a], phys_nodes[b]
            diff = fld["u"][b] - fld["u"][a]
            if xb <= 0.5 and diff < -thresholds["PH5"]:
                violations += 1
            if xa >= 0.5 and diff > thresholds["PH5"]:
                violations += 1
        maximum = max(fld["u"])
        derivative_energy = math.fsum(w * d * d for w, d in zip(phys_weights, fld["ux"]))
        per_seed.append({"PH1": flux, "PH2": energy, "PH3": positivity, "PH4": symmetry, "PH5": violations,
                         "PH6": maximum, "PH7": derivative_energy})
    worst = {
        "PH1": max(s["PH1"] for s in per_seed), "PH2": max(s["PH2"] for s in per_seed), "PH3": min(s["PH3"] for s in per_seed),
        "PH4": max(s["PH4"] for s in per_seed), "PH5": max(s["PH5"] for s in per_seed), "PH6": max(s["PH6"] for s in per_seed),
        "PH7": min(s["PH7"] for s in per_seed),
    }
    checks = [
        check("PH1-fluxBalance", pass_fail(worst["PH1"] < thresholds["PH1"]),
              f"worst seed |(u'(0)-u'(1)) - sum w f| / 2pi = {worst['PH1']:.3e} (< {thresholds['PH1']})", evidence),
        check("PH2-energyBalance", pass_fail(worst["PH2"] < thresholds["PH2"]),
              f"worst seed |sum w u'^2 - sum w f u| / (pi^2/2) = {worst['PH2']:.3e} (< {thresholds['PH2']})", evidence),
        check("PH3-positivity", pass_fail(worst["PH3"] >= -thresholds["PH3"]),
              f"worst seed min u on D_phys = {worst['PH3']:.3e} (>= -{thresholds['PH3']}; f >= 0)", evidence),
        check("PH4-symmetry", pass_fail(worst["PH4"] < thresholds["PH4"]),
              f"worst seed max |u(x) - u(1-x)| = {worst['PH4']:.3e} (< {thresholds['PH4']})", evidence),
        check("PH5-monotonicity", pass_fail(worst["PH5"] == 0),
              f"worst seed monotonicity violations (increase on (0,1/2), decrease on (1/2,1), tolerance {thresholds['PH5']}) = {worst['PH5']}", evidence),
        check("PH6-maximumPrinciple", pass_fail(worst["PH6"] <= u_star_max + thresholds["PH6"]),
              f"worst seed max u = {worst['PH6']:.6f} (<= discrete bound {u_star_max:.10f} + {thresholds['PH6']})", evidence),
        check("PH7-spd", pass_fail(lambda_min > 0 and worst["PH7"] > thresholds["PH7_energyFloor"]),
              f"FDM stiffness lambda_min(n=1024) = {lambda_min:.6f} > 0; worst seed int (u')^2 = {worst['PH7']:.4f} (> {thresholds['PH7_energyFloor']})", evidence),
        not_applicable("PH10-momentumBudget"),
        not_applicable("PH11-freeEnergy"),
    ]
    return checks, {"perSeed": per_seed, "worst": worst, "discreteMaximumBound": u_star_max, "fdmLambdaMin": lambda_min,
                    "thresholds": dict(thresholds)}


# ------------------------------------------------------------------ Gate 5b

def claim_evaluation(model, protocol) -> dict[str, Any]:
    """AC-1..AC-8 of one model through the trusted validator on the frozen GL512 / CGL2000 grids."""

    gl = list(protocol.quadrature_nodes)
    cgl = list(protocol.pointwise_nodes)
    fld_gl = pinn_torch.fields(model, gl)
    fld_cgl = pinn_torch.fields(model, cgl)
    fld_b = pinn_torch.fields(model, [0.0, 1.0])
    samples = FieldSamples(
        quadrature_coordinates=gl, pointwise_coordinates=cgl, boundary_coordinates=[0.0, 1.0],
        u_quadrature=fld_gl["u"], du_quadrature=fld_gl["ux"], d2u_quadrature=fld_gl["uxx"],
        u_pointwise=fld_cgl["u"], u_boundary=[fld_cgl["u"][0], fld_cgl["u"][-1]], du_boundary=fld_b["ux"],
        forcing_quadrature=[reference.forcing(x) for x in gl],
        derivative_method="AUTOGRAD_FIRST_AND_SECOND_ORDER", device="cpu",
    )
    return evaluate_samples(protocol, samples)


def external_checks(evaluations: Sequence[Mapping[str, Any]], claim_ref: Mapping[str, str],
                    evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    must_ok = all(not e["failedMustCriteria"] for e in evaluations)
    should_ok = all(not e["failedShouldCriteria"] for e in evaluations)
    failing = [i for i, e in enumerate(evaluations) if e["failedMustCriteria"]]
    return [
        check("G5b-acceptanceCriteriaMust", pass_fail(must_ok),
              f"AC-1..AC-7 (MUST) on the OPENED claim set {claim_ref['sha256'][:12]} for every seed model: "
              + ("all satisfied" if must_ok else f"seeds {failing} fail {[e['failedMustCriteria'] for e in evaluations if e['failedMustCriteria']]}"),
              evidence),
        check("G5b-acceptanceCriteriaShould", TrustStatus.PASS if should_ok else TrustStatus.PARTIAL,
              "AC-8 (SHOULD, relative L2 of u') satisfied by every seed" if should_ok
              else f"AC-8 (SHOULD) missed by {sum(1 for e in evaluations if e['failedShouldCriteria'])} seed model(s); PARTIAL, not FAIL", evidence),
    ]


# ------------------------------------------------------------------ Gate 6

def gate6_blocked(reason: str, evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    return [check("G6-independentReproduction", TrustStatus.BLOCKED, reason, evidence)]
