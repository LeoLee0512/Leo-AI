"""Gate executions of the Poisson 2D calibration experiment, one function per Gate.

Same shape as the 1D module: every function returns plain ``CheckResult``-shaped
dicts so the TrustVector is a direct rendering of what was executed and the
dimension status is the meet of the applicable checks.  Thresholds come from the
frozen experiment config and the frozen 2D contract; nothing here reads a
threshold from a result.  No new Gate and no new TrustStatus is introduced
(PART 12): the 2D-specific work is inside Gate 3 (component-separated
derivatives, four-edge boundary check) and Gate 5a (2D physics identities).

``gate4_training`` is imported unchanged from the 1D module: multi-seed training
integrity is dimension-independent (2D_REUSE_AUDIT section 3).
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.experiments.gates import check, dimension_status, gate4_training, pass_fail  # noqa: F401  (re-exported)
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set
from pinn.governance.trust_vector import TrustStatus
from pinn.reference import analytic_poisson2d as reference
from pinn.validation import poisson2d as validator
from scientific_reference.poisson2d_fdm import refinement_diagnostic, stiffness_min_eigenvalue

from . import datasets2d as ds
from . import pinn_torch2d as pinn2d

#: The frozen check registry (ProblemDefinition.checkApplicability); INV-A1 satisfied per dimension.
REGISTRY: list[dict[str, str]] = [
    {"checkId": "M1-fieldCountClosure", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M2-boundaryConditionCount", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M3-dimensionalHomogeneity", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M5-geometryBinding", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M6-referenceEquationBinding", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "T1-autogradVsFiniteDifference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T2-secondDerivativeComponentSeparation", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T3-residualOperatorOnReference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T4-boundaryOperatorFourEdges", "dimension": "impl", "applicability": "APPLICABLE"},
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
     "reason": "scalar Poisson equation has no momentum variable; adding a dimension does not create one"},
    {"checkId": "PH11-freeEnergy", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "steady elliptic equation has no dissipative free-energy structure; the energy identity PH2 covers it"},
    {"checkId": "G5b-acceptanceCriteriaMust", "dimension": "external", "applicability": "APPLICABLE"},
    {"checkId": "G5b-acceptanceCriteriaShould", "dimension": "external", "applicability": "APPLICABLE"},
    {"checkId": "G6-independentReproduction", "dimension": "repro", "applicability": "APPLICABLE"},
]


def not_applicable(check_id: str) -> dict[str, Any]:
    entry = next(e for e in REGISTRY if e["checkId"] == check_id)
    return {"checkId": check_id, "applicability": "NOT_APPLICABLE", "reason": entry["reason"]}


# ------------------------------------------------------------------ Gate 1

def gate1_math(pdef: Mapping[str, Any], evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    equations = pdef["pde"]["equations"]
    dependent = [v for v in pdef["variables"] if v["role"] == "dependent"]
    independent = [v for v in pdef["variables"] if v["role"] == "independent"]
    bcs = pdef["boundaryConditions"]
    units = {e["unit"] for e in pdef["units"]["entries"]}
    ranges = {v["name"]: v["domainRange"] for v in independent}
    regions = {r["id"] for r in pdef["geometry"]["regions"]}
    edge_regions = {"x0", "x1", "y0", "y1"}
    return [
        check("M1-fieldCountClosure", pass_fail(len(equations) == len(dependent) == 1),
              f"{len(equations)} equation(s) for {len(dependent)} dependent field(s) in {len(independent)} independent variables: closed", evidence),
        check("M2-boundaryConditionCount",
              pass_fail(len(bcs) == 4 and all(b["type"] == "dirichlet" for b in bcs)
                        and {b["regionRef"] for b in bcs} == edge_regions),
              f"{len(bcs)} Dirichlet conditions, one per edge of the square, for one second-order elliptic operator in 2D: "
              "the problem is determined (not Neumann-only, no edge left free)", evidence),
        check("M3-dimensionalHomogeneity", pass_fail(pdef["units"]["system"] == "nondimensional" and units == {"1"}),
              "nondimensional by construction; every term of -(u_xx + u_yy) - f carries the null dimension", evidence),
        check("M5-geometryBinding",
              pass_fail(ranges.get("x") == [0.0, 1.0] and ranges.get("y") == [0.0, 1.0]
                        and ({"interior"} | edge_regions) <= regions and all(b["regionRef"] in regions for b in bcs)
                        and pdef["geometry"]["dimension"] == 2 and pdef["geometry"]["domainType"] == "rectangle"),
              "domain (0,1)^2 with the four edge regions x0, x1, y0, y1 bound to the four conditions", evidence),
        check("M6-referenceEquationBinding",
              pass_fail(reference.EQUATION_BINDING ==
                        "-(u_xx+u_yy)(x,y)=2*pi^2*sin(pi*x)*sin(pi*y);(x,y) in (0,1)^2;u=0 on the four edges"),
              f"reference module binds {reference.EQUATION_BINDING}", evidence),
    ]


# ------------------------------------------------------------------ Gate 2

def gate2_baseline(phys_points: Sequence[Sequence[float]], boundary_points: Sequence[Sequence[float]],
                   evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    residual = max(abs(-(reference.dxx(x, y) + reference.dyy(x, y)) - reference.forcing(x, y)) for x, y in phys_points)
    boundary = max(abs(reference.solution(x, y)) for x, y in boundary_points)
    fdm = refinement_diagnostic()
    errors = [s["interior_max_error"] for s in fdm["solutions"]]
    measured = [entry["order"] for entry in fdm["orders"]]
    checks = [
        check("G2a-analyticReferenceVerification", pass_fail(residual < 1e-12 and boundary < 1e-14),
              f"max |-(u*_xx + u*_yy) - f| on D_phys = {residual:.3e} (< 1e-12); max |u*| on the four edges = {boundary:.3e} (< 1e-14)", evidence),
        check("G2b-fdmRefinement", pass_fail(fdm["componentCriteriaSatisfied"]),
              f"independent five-point FDM: interior max errors {['%.3e' % e for e in errors]} strictly decreasing="
              f"{fdm['errorsStrictlyDecreasing']}; observed orders {['%.4f' % o for o in measured]} in [1.8, 2.2]="
              f"{fdm['ordersInRange']}; linear solves converged={fdm['linearSolvesConverged']}", evidence),
    ]
    detail = {"analyticResidualMax": residual, "analyticBoundaryMax": boundary,
              "fdm": {k: v for k, v in fdm.items() if k != "solutions"},
              "fdmSolutions": fdm["solutions"], "fdmErrors": errors,
              "note": "the manufactured forcing is a discrete eigenvector of the five-point operator, so the CG solve "
                      "terminates in one or two iterations; Gate 2b therefore tests the discretization order, not the "
                      "linear solver's robustness (recorded, not hidden)"}
    return checks, detail


# ------------------------------------------------------------------ Gate 3

def gate3_implementation(config: Mapping[str, Any], sets: Mapping[str, Mapping[str, Any]],
                         dev_points: Sequence[Sequence[float]], claim_grids: Mapping[str, Any],
                         evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch  # type: ignore[import-not-found]

    detail: dict[str, Any] = {}
    threads = int(config["optimizer"].get("threads", 1))
    # T1: autograd first and second derivatives of a randomly initialised network against central differences,
    #     component by component (a correct sum with two wrong components must not pass).
    model = pinn2d.build_model(config, 424242, threads=threads)
    probes = [(0.137, 0.611), (0.5, 0.25), (0.86, 0.43)]
    h = 1e-4
    ad = pinn2d.fields(model, probes, threads=threads)
    with torch.no_grad():
        def u(x: float, y: float) -> float:
            return float(model(torch.tensor([[x, y]], dtype=torch.float64)).item())
        fd_x = [(u(x + h, y) - u(x - h, y)) / (2 * h) for x, y in probes]
        fd_y = [(u(x, y + h) - u(x, y - h)) / (2 * h) for x, y in probes]
        fd_xx = [(u(x + h, y) - 2 * u(x, y) + u(x - h, y)) / (h * h) for x, y in probes]
        fd_yy = [(u(x, y + h) - 2 * u(x, y) + u(x, y - h)) / (h * h) for x, y in probes]
    err = {
        "x": max(abs(a - b) for a, b in zip(ad["ux"], fd_x)),
        "y": max(abs(a - b) for a, b in zip(ad["uy"], fd_y)),
        "xx": max(abs(a - b) for a, b in zip(ad["uxx"], fd_xx)),
        "yy": max(abs(a - b) for a, b in zip(ad["uyy"], fd_yy)),
    }
    detail["T1"] = {"maxDiff": err, "h": h, "probes": [list(p) for p in probes]}
    # T2: component separation on an ASYMMETRIC analytic probe w = sin(2 pi x) sin(pi y).
    #     The manufactured solution itself is symmetric under (x, y) -> (y, x), so it cannot detect an axis swap;
    #     the probe can (w_xx = -4 pi^2 w, w_yy = -pi^2 w).
    xy = torch.tensor([[float(x), float(y)] for x, y in dev_points], dtype=torch.float64, requires_grad=True)
    w = torch.sin(2 * math.pi * xy[:, 0:1]) * torch.sin(math.pi * xy[:, 1:2])
    (gw,) = torch.autograd.grad(w, xy, grad_outputs=torch.ones_like(w), create_graph=True)
    (gwx,) = torch.autograd.grad(gw[:, 0:1], xy, grad_outputs=torch.ones_like(gw[:, 0:1]), create_graph=True)
    (gwy,) = torch.autograd.grad(gw[:, 1:2], xy, grad_outputs=torch.ones_like(gw[:, 1:2]), create_graph=True)
    wxx, wyy = gwx[:, 0:1], gwy[:, 1:2]
    exact_wxx = -((2 * math.pi) ** 2) * w
    exact_wyy = -(math.pi ** 2) * w
    err_wxx = float(torch.max(torch.abs(wxx - exact_wxx)).item())
    err_wyy = float(torch.max(torch.abs(wyy - exact_wyy)).item())
    swap_gap = float(torch.max(torch.abs(wxx - wyy)).item())
    detail["T2"] = {"maxDiffWxx": err_wxx, "maxDiffWyy": err_wyy, "swapDiscriminationGap": swap_gap,
                    "probe": "w = sin(2 pi x) sin(pi y)"}
    # T3: the training residual operator applied to the analytic reference through the same torch ops.
    u_star = torch.sin(math.pi * xy[:, 0:1]) * torch.sin(math.pi * xy[:, 1:2])
    (gu,) = torch.autograd.grad(u_star, xy, grad_outputs=torch.ones_like(u_star), create_graph=True)
    (gux,) = torch.autograd.grad(gu[:, 0:1], xy, grad_outputs=torch.ones_like(gu[:, 0:1]), create_graph=True)
    (guy,) = torch.autograd.grad(gu[:, 1:2], xy, grad_outputs=torch.ones_like(gu[:, 1:2]), create_graph=True)
    f = torch.tensor([[reference.forcing(x, y)] for x, y in dev_points], dtype=torch.float64)
    residual_max = float(torch.max(torch.abs(-(gux[:, 0:1] + guy[:, 1:2]) - f)).item())
    detail["T3"] = {"residualMaxOnReference": residual_max}
    # T4: the hard parameterization on all four edges, each edge measured separately.
    edge_nodes, _ = ds.boundary_nodes(32)
    edge_values = pinn2d.values(model, edge_nodes, threads=threads)
    per_edge = {"x0": 0.0, "x1": 0.0, "y0": 0.0, "y1": 0.0}
    for (x, y), value in zip(edge_nodes, edge_values):
        key = "x0" if x == 0.0 else "x1" if x == 1.0 else "y0" if y == 0.0 else "y1"
        per_edge[key] = max(per_edge[key], abs(value))
    detail["T4"] = {"perEdgeMaxAbsU": per_edge, "nodesPerEdge": 32}
    # T9: sample-level disjointness of the four registered sets.
    loaded = {role: load_evaluation_set(doc) for role, doc in sets.items()}
    disjoint_errors = disjointness_errors(loaded, min_separation=config["sets"].get("minSeparation"))
    detail["T9"] = {"errors": disjoint_errors, "minSeparation": config["sets"].get("minSeparation")}
    # T10: the trusted validator accepts the analytic control and rejects the corrupted fixtures.
    verdicts = validator.fixture_verdicts(
        quadrature_points=claim_grids["quadraturePoints"], quadrature_weights=claim_grids["quadratureWeights"],
        pointwise_points=claim_grids["pointwisePoints"], boundary_points=claim_grids["boundaryPoints"],
        boundary_weights=claim_grids["boundaryWeights"])
    t10_ok = verdicts.get("ANALYTIC_CONTROL") is True and all(
        value is False for key, value in verdicts.items() if key != "ANALYTIC_CONTROL")
    detail["T10"] = verdicts
    checks = [
        check("T1-autogradVsFiniteDifference",
              pass_fail(err["x"] < 1e-6 and err["y"] < 1e-6 and err["xx"] < 1e-4 and err["yy"] < 1e-4),
              f"AD vs central differences (h={h}) on a random network, per component: u_x {err['x']:.2e}, u_y {err['y']:.2e} "
              f"(< 1e-6); u_xx {err['xx']:.2e}, u_yy {err['yy']:.2e} (< 1e-4)", evidence),
        check("T2-secondDerivativeComponentSeparation",
              pass_fail(err_wxx < 1e-9 and err_wyy < 1e-9 and swap_gap > 1.0),
              f"asymmetric probe w = sin(2 pi x) sin(pi y): |w_xx - (-4 pi^2 w)| = {err_wxx:.2e}, |w_yy - (-pi^2 w)| = {err_wyy:.2e} "
              f"(< 1e-9 each); the two components differ by up to {swap_gap:.2f}, so an x/y swap in the residual operator would be "
              "detected here (the symmetric manufactured solution alone cannot detect it)", evidence),
        check("T3-residualOperatorOnReference", pass_fail(residual_max < 1e-10),
              f"max |-(u*_xx + u*_yy) - f| through the training residual operator on D_dev = {residual_max:.2e} (< 1e-10)", evidence),
        check("T4-boundaryOperatorFourEdges", pass_fail(max(per_edge.values()) == 0.0),
              f"hard parameterization u = x(1-x)y(1-y)N on 32 nodes per edge: max |u| per edge {per_edge} (exactly 0 by construction)", evidence),
        check("T8-lossTermSeparation", pass_fail(set(config["lossWeights"]) == {"pde"}),
              "the 2D loss carries a single pde term with a frozen weight and no boundary penalty; the Dirichlet data are enforced "
              "by construction and verified independently by T4", evidence),
        check("T9-collocationDisjointness", pass_fail(not disjoint_errors),
              "train | dev | phys | claim pairwise sample-disjoint at the preregistered minimum separation: "
              + ("yes" if not disjoint_errors else "; ".join(disjoint_errors)), evidence),
        check("T10-validatorControlFixtures", pass_fail(t10_ok),
              f"trusted 2D validator verdicts on the control fixtures: {verdicts}", evidence),
    ]
    return checks, detail


# ------------------------------------------------------------------ Gate 5a

def physics_checks(models: Sequence[Any], phys_points: Sequence[Sequence[float]], phys_weights: Sequence[float],
                   boundary_points: Sequence[Sequence[float]], boundary_weights: Sequence[float],
                   thresholds: Mapping[str, float], evidence: Sequence[Mapping[str, str]], *,
                   threads: int = 1) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """PH1-PH7 on D_phys for every seed model; each check's status is the meet over seeds (worst seed)."""

    f_vals = [reference.forcing(x, y) for x, y in phys_points]
    forcing_integral = math.fsum(w * f for w, f in zip(phys_weights, f_vals))
    u_star_max = max(reference.solution(x, y) for x, y in phys_points)
    swapped = [(y, x) for x, y in phys_points]
    n_axis = int(round(math.sqrt(len(phys_points))))
    lambda_min = stiffness_min_eigenvalue(1024)
    per_seed: list[dict[str, float]] = []
    for model in models:
        fld = pinn2d.fields(model, phys_points, threads=threads)
        mirror = pinn2d.values(model, swapped, threads=threads)
        dn = pinn2d.normal_derivatives(model, boundary_points, threads=threads)
        flux = math.fsum(w * d for w, d in zip(boundary_weights, dn))
        energy = math.fsum(w * (a * a + b * b) for w, a, b in zip(phys_weights, fld["ux"], fld["uy"]))
        forcing_energy = math.fsum(w * f * value for w, f, value in zip(phys_weights, f_vals, fld["u"]))
        violations = 0
        if n_axis * n_axis == len(phys_points):
            for i in range(n_axis):                      # rows: fixed x, y ascending
                row = fld["u"][i * n_axis:(i + 1) * n_axis]
                ys = [phys_points[i * n_axis + j][1] for j in range(n_axis)]
                for j in range(n_axis - 1):
                    diff = row[j + 1] - row[j]
                    if ys[j + 1] <= 0.5 and diff < -thresholds["PH5"]:
                        violations += 1
                    if ys[j] >= 0.5 and diff > thresholds["PH5"]:
                        violations += 1
            for j in range(n_axis):                      # columns: fixed y, x ascending
                column = [fld["u"][i * n_axis + j] for i in range(n_axis)]
                xs = [phys_points[i * n_axis + j][0] for i in range(n_axis)]
                for i in range(n_axis - 1):
                    diff = column[i + 1] - column[i]
                    if xs[i + 1] <= 0.5 and diff < -thresholds["PH5"]:
                        violations += 1
                    if xs[i] >= 0.5 and diff > thresholds["PH5"]:
                        violations += 1
        per_seed.append({
            "PH1": abs(flux + forcing_integral) / abs(forcing_integral),
            "PH2": abs(energy - forcing_energy) / reference.DIRICHLET_ENERGY,
            "PH3": min(fld["u"]),
            "PH4": max(abs(a - b) for a, b in zip(fld["u"], mirror)),
            "PH5": float(violations),
            "PH6": max(fld["u"]),
            "PH7": energy,
        })
    worst = {
        "PH1": max(s["PH1"] for s in per_seed), "PH2": max(s["PH2"] for s in per_seed), "PH3": min(s["PH3"] for s in per_seed),
        "PH4": max(s["PH4"] for s in per_seed), "PH5": max(s["PH5"] for s in per_seed), "PH6": max(s["PH6"] for s in per_seed),
        "PH7": min(s["PH7"] for s in per_seed),
    }
    checks = [
        check("PH1-fluxBalance", pass_fail(worst["PH1"] < thresholds["PH1"]),
              f"worst seed |closed boundary flux + int int f| / |int int f| = {worst['PH1']:.3e} (< {thresholds['PH1']}); "
              f"int int f on D_phys = {forcing_integral:.12f} (exact 8)", evidence),
        check("PH2-energyBalance", pass_fail(worst["PH2"] < thresholds["PH2"]),
              f"worst seed |int |grad u|^2 - int f u| / (pi^2/2) = {worst['PH2']:.3e} (< {thresholds['PH2']})", evidence),
        check("PH3-positivity", pass_fail(worst["PH3"] >= -thresholds["PH3"]),
              f"worst seed min u on D_phys = {worst['PH3']:.3e} (>= -{thresholds['PH3']}; f >= 0 on the square)", evidence),
        check("PH4-symmetry", pass_fail(worst["PH4"] < thresholds["PH4"]),
              f"worst seed max |u(x,y) - u(y,x)| = {worst['PH4']:.3e} (< {thresholds['PH4']}); the manufactured problem is invariant "
              "under the coordinate swap, and this is evidence, not a training constraint", evidence),
        check("PH5-monotonicity", pass_fail(worst["PH5"] == 0),
              f"worst seed monotonicity violations along the tensor grid lines (increase before the midline, decrease after, "
              f"tolerance {thresholds['PH5']}) = {int(worst['PH5'])}", evidence),
        check("PH6-maximumPrinciple", pass_fail(worst["PH6"] <= u_star_max + thresholds["PH6"]),
              f"worst seed max u = {worst['PH6']:.6f} (<= discrete bound {u_star_max:.10f} + {thresholds['PH6']})", evidence),
        check("PH7-spd", pass_fail(lambda_min > 0 and worst["PH7"] > thresholds["PH7_energyFloor"]),
              f"five-point stiffness lambda_min(n=1024) = {lambda_min:.6f} > 0; worst seed int |grad u|^2 = {worst['PH7']:.4f} "
              f"(> {thresholds['PH7_energyFloor']})", evidence),
        not_applicable("PH10-momentumBudget"),
        not_applicable("PH11-freeEnergy"),
    ]
    detail = {"perSeed": per_seed, "worst": worst, "discreteMaximumBound": u_star_max, "fdmLambdaMin": lambda_min,
              "forcingIntegral": forcing_integral, "thresholds": dict(thresholds)}
    return checks, detail


# ------------------------------------------------------------------ Gate 5b

def claim_evaluation(model, grids: Mapping[str, Any], *, threads: int = 1) -> dict[str, Any]:
    """AC2D-1..AC2D-9 of one model through the trusted 2D validator on the opened claim grids."""

    fld = pinn2d.fields(model, grids["quadraturePoints"], threads=threads)
    pointwise = pinn2d.values(model, grids["pointwisePoints"], threads=threads)
    boundary_values = pinn2d.values(model, grids["boundaryPoints"], threads=threads)
    dn = pinn2d.normal_derivatives(model, grids["boundaryPoints"], threads=threads)
    samples = validator.Fields2D(
        quadrature_points=grids["quadraturePoints"], quadrature_weights=grids["quadratureWeights"],
        u_quadrature=fld["u"], ux_quadrature=fld["ux"], uy_quadrature=fld["uy"],
        uxx_quadrature=fld["uxx"], uyy_quadrature=fld["uyy"],
        pointwise_points=grids["pointwisePoints"], u_pointwise=pointwise,
        boundary_points=grids["boundaryPoints"], boundary_weights=grids["boundaryWeights"],
        u_boundary=boundary_values, dn_boundary=dn,
        derivative_method="AUTOGRAD_FIRST_AND_SECOND_ORDER", device="cpu")
    return validator.evaluate_fields(samples, grid_label=grids["label"])


def external_checks(evaluations: Sequence[Mapping[str, Any]], claim_ref: Mapping[str, str],
                    evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    must_ok = all(not e["failedMustCriteria"] for e in evaluations)
    should_ok = all(not e["failedShouldCriteria"] for e in evaluations)
    failing = [i for i, e in enumerate(evaluations) if e["failedMustCriteria"]]
    return [
        check("G5b-acceptanceCriteriaMust", pass_fail(must_ok),
              f"AC2D-1..AC2D-7 and AC2D-9 (MUST) on the OPENED claim set {claim_ref['sha256'][:12]} for every seed model: "
              + ("all satisfied" if must_ok else
                 f"seeds {failing} fail {[e['failedMustCriteria'] for e in evaluations if e['failedMustCriteria']]}"), evidence),
        check("G5b-acceptanceCriteriaShould", TrustStatus.PASS if should_ok else TrustStatus.PARTIAL,
              "AC2D-8 (SHOULD, relative H1 seminorm of the gradient) satisfied by every seed" if should_ok
              else f"AC2D-8 (SHOULD) missed by {sum(1 for e in evaluations if e['failedShouldCriteria'])} seed model(s); PARTIAL, not FAIL", evidence),
    ]


# ------------------------------------------------------------------ Gate 6

def gate6_blocked(reason: str, evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    return [check("G6-independentReproduction", TrustStatus.BLOCKED, reason, evidence)]
