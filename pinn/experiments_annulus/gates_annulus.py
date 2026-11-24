"""Gate executions of the annular Poisson experiment, one function per Gate.

Same shape as the square-2D module: every function returns plain ``CheckResult``-shaped
dicts, so the TrustVector is a direct rendering of what was executed. **No new Gate and
no new TrustStatus is introduced** (Geometry Lift 1 section 22); the geometry work lives
inside the existing gates:

  * Gate 1 binds the geometry contract (two boundary components, a hole, curved edges);
  * Gate 3 gains three implementation checks that a rectangle never needed --
    membership masking, per-component normal orientation, and the quadrature Jacobian --
    plus the hard factor checked on BOTH circles;
  * Gate 5a's flux identity is reported per component, because the inner outward normal
    points into the hole and a sign error there is partly cancelled by the outer one;
  * Gate 5b is unchanged: every MUST criterion on every seed model.

``gate4_training`` is imported unchanged from the 1D module: multi-seed training
integrity is geometry-independent.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from pinn.experiments.gates import check, dimension_status, gate4_training, pass_fail  # noqa: F401  (re-exported)
from pinn.geometry import annulus as geo
from pinn.governance.evaluation_sets import disjointness_errors, load_evaluation_set
from pinn.governance.trust_vector import TrustStatus
from pinn.reference import analytic_annulus as reference
from pinn.validation import annulus as validator
from scientific_reference.annulus_polar_fdm import min_eigenvalue, refinement_diagnostic

from . import datasets_annulus as ds
from . import pinn_torch_annulus as pinn

#: The frozen check registry (ProblemDefinition.checkApplicability).
REGISTRY: list[dict[str, str]] = [
    {"checkId": "M1-fieldCountClosure", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M2-boundaryConditionCount", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M3-dimensionalHomogeneity", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M5-geometryBinding", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "M6-referenceEquationBinding", "dimension": "math", "applicability": "APPLICABLE"},
    {"checkId": "T1-autogradVsFiniteDifference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T2-secondDerivativeComponentSeparation", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T3-residualOperatorOnReference", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T4-hardBoundaryBothComponents", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T8-lossTermSeparation", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T9-collocationDisjointness", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T10-validatorControlFixtures", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T11-geometryMembership", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T12-boundaryNormalOrientation", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "T13-quadratureJacobian", "dimension": "impl", "applicability": "APPLICABLE"},
    {"checkId": "G4-trainingIntegrity", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "G4-seedProtocol", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "G4-lossErrorDecoupling", "dimension": "train", "applicability": "APPLICABLE"},
    {"checkId": "PH1-fluxBalance", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH2-energyBalance", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH3-positivity", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH4-symmetry", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "the manufactured solution is deliberately asymmetric (g carries sin(pi x) cos(2 pi y) and the slopes "
               "+0.1x, -0.1y), so the domain's rotational symmetry is not a symmetry of the solution and there is no "
               "swap invariance to test. Registered rather than faked: an invented symmetry would be a check that "
               "cannot fail"},
    {"checkId": "PH5-monotonicity", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "on the square the solution was monotone along a coordinate ray from the boundary; on the annulus the "
               "non-radial modulation removes any monotone direction. The information it carried (no spurious "
               "oscillation) is covered by PH6 and by the localized criterion ACA-9"},
    {"checkId": "PH6-maximumPrinciple", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH7-spd", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH8-geometryMembership", "dimension": "physics", "applicability": "APPLICABLE"},
    {"checkId": "PH10-momentumBudget", "dimension": "physics", "applicability": "NOT_APPLICABLE",
     "reason": "scalar Poisson equation has no momentum variable; a curved domain does not create one"},
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
    regions = {r["id"] for r in pdef["geometry"]["regions"]}
    components = {"outerBoundary", "innerBoundary"}
    geometry = pdef["geometry"]
    # the annulus lives in the interior region's params: the schema's domainType
    # vocabulary has no annulus and its geometry object takes no extra properties
    # (reported as an AMENDMENT CANDIDATE rather than patched)
    interior = next(r for r in geometry["regions"] if r["id"] == "interior")["params"]
    return [
        check("M1-fieldCountClosure", pass_fail(len(equations) == len(dependent) == 1),
              f"{len(equations)} equation(s) for {len(dependent)} dependent field(s) in {len(independent)} independent "
              "variables: closed", evidence),
        check("M2-boundaryConditionCount",
              pass_fail(len(bcs) == 2 and all(b["type"] == "dirichlet" for b in bcs)
                        and {b["regionRef"] for b in bcs} == components),
              f"{len(bcs)} Dirichlet conditions, one per boundary COMPONENT (outer and inner), for one second-order "
              "elliptic operator on a multiply connected domain: the problem is determined, and neither component is "
              "left free -- the failure mode a lift from a simply connected square invites", evidence),
        check("M3-dimensionalHomogeneity", pass_fail(pdef["units"]["system"] == "nondimensional" and units == {"1"}),
              "nondimensional by construction; every term of -(u_xx + u_yy) - f carries the null dimension", evidence),
        check("M5-geometryBinding",
              pass_fail(interior["geometryType"] == "annulus" and geometry["dimension"] == 2
                        and interior["multiplyConnected"] is True
                        and interior["innerRadius"] == geo.INNER_RADIUS
                        and interior["outerRadius"] == geo.OUTER_RADIUS
                        and interior["geometryId"] == geo.GEOMETRY["geometryId"]
                        and interior["membership"] == geo.GEOMETRY["membership"]
                        and components <= regions and "hole" in regions
                        and all(b["regionRef"] in regions for b in bcs)),
              f"domain {geo.GEOMETRY['membership']} with the two boundary components bound to the two conditions and "
              f"the hole registered as excluded; geometryId {interior.get('geometryId')} matches the frozen geometry "
              f"contract (carried in regions[].params: the schema's domainType vocabulary has no annulus, which is "
              f"reported as an AMENDMENT CANDIDATE rather than patched)", evidence),
        check("M6-referenceEquationBinding",
              pass_fail(interior["equation"] == "-(u_xx+u_yy)(x,y)=f(x,y);a^2<x^2+y^2<1;u=0 on r=a and r=1"
                        and abs(reference.INTEGRAL_U - math.pi * (1 - geo.INNER_RADIUS ** 2) ** 3 / 6) < 1e-15),
              "reference module binds the manufactured solution u* = (1-s)(s-a^2) g and its analytic source; the "
              "closed-form integral matches pi (1 - a^2)^3 / 6", evidence),
    ]


# ------------------------------------------------------------------ Gate 2

def gate2_baseline(phys_points: Sequence[Sequence[float]], boundary_sets: Mapping[str, Mapping[str, Any]],
                   evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """G2a: the analytic reference verifies itself. G2b: an independent polar FDM converges at order 2."""

    residual = max(abs(-reference.laplacian(x, y) - reference.forcing(x, y)) for x, y in phys_points)
    boundary = max(max(abs(reference.solution(x, y)) for x, y in block["points"])
                   for block in boundary_sets.values())
    fdm = refinement_diagnostic(reference.forcing, reference.solution)
    errors = [level["relL2"] for level in fdm["levels"]]
    orders = fdm["observedOrders"]
    decreasing = all(errors[i] > errors[i + 1] for i in range(len(errors) - 1))
    orders_ok = all(1.8 <= order <= 2.2 for order in orders)
    converged = all(level["converged"] for level in fdm["levels"])
    checks = [
        check("G2a-analyticReferenceVerification", pass_fail(residual < 1e-12 and boundary < 1e-14),
              f"max |-Lap u* - f| on D_phys = {residual:.3e} (< 1e-12); max |u*| on both boundary components = "
              f"{boundary:.3e} (< 1e-14)", evidence),
        check("G2b-fdmRefinement", pass_fail(decreasing and orders_ok and converged),
              f"independent second-order polar FDM (numpy only, no autograd, no model): relative L2 errors "
              f"{['%.3e' % e for e in errors]} strictly decreasing={decreasing}; observed orders "
              f"{['%.4f' % o for o in orders]} in [1.8, 2.2]={orders_ok}; linear solves converged={converged}",
              evidence),
    ]
    detail = {"analyticResidualMax": residual, "analyticBoundaryMax": boundary, "fdm": fdm,
              "independence": fdm["independence"]}
    return checks, detail


# ------------------------------------------------------------------ Gate 3

def gate3_implementation(config: Mapping[str, Any], sets: Mapping[str, Mapping[str, Any]],
                         dev_points: Sequence[Sequence[float]], claim_grids: Mapping[str, Any],
                         boundary_sets: Mapping[str, Mapping[str, Any]],
                         evidence: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch  # type: ignore[import-not-found]

    detail: dict[str, Any] = {}
    threads = int(config["optimizer"].get("threads", 1))
    model = pinn.build_model(config, 424242, threads=threads)

    # T1: autograd first and second derivatives of a random network against central differences,
    #     component by component (a correct sum of two wrong components must not pass).
    probes = [geo.to_cartesian(0.5, 0.7), geo.to_cartesian(0.85, 2.3), geo.to_cartesian(0.4, 4.9)]
    step = 1e-4
    ad = pinn.fields(model, probes, threads=threads)
    with torch.no_grad():
        def u(x: float, y: float) -> float:
            return float(model(torch.tensor([[x, y]], dtype=torch.float64)).item())
        fd_x = [(u(x + step, y) - u(x - step, y)) / (2 * step) for x, y in probes]
        fd_y = [(u(x, y + step) - u(x, y - step)) / (2 * step) for x, y in probes]
        fd_xx = [(u(x + step, y) - 2 * u(x, y) + u(x - step, y)) / (step * step) for x, y in probes]
        fd_yy = [(u(x, y + step) - 2 * u(x, y) + u(x, y - step)) / (step * step) for x, y in probes]
    err = {"x": max(abs(a - b) for a, b in zip(ad["ux"], fd_x)),
           "y": max(abs(a - b) for a, b in zip(ad["uy"], fd_y)),
           "xx": max(abs(a - b) for a, b in zip(ad["uxx"], fd_xx)),
           "yy": max(abs(a - b) for a, b in zip(ad["uyy"], fd_yy))}
    detail["T1"] = {"maxDiff": err, "h": step, "probes": [list(p) for p in probes]}

    # T2: component separation on an asymmetric analytic probe (w_xx and w_yy differ by construction).
    xy = torch.tensor([[float(x), float(y)] for x, y in dev_points], dtype=torch.float64, requires_grad=True)
    w = torch.sin(2 * math.pi * xy[:, 0:1]) * torch.cos(math.pi * xy[:, 1:2])
    (gw,) = torch.autograd.grad(w, xy, grad_outputs=torch.ones_like(w), create_graph=True)
    (gwx,) = torch.autograd.grad(gw[:, 0:1], xy, grad_outputs=torch.ones_like(gw[:, 0:1]), create_graph=True)
    (gwy,) = torch.autograd.grad(gw[:, 1:2], xy, grad_outputs=torch.ones_like(gw[:, 1:2]), create_graph=True)
    wxx, wyy = gwx[:, 0:1], gwy[:, 1:2]
    err_wxx = float(torch.max(torch.abs(wxx - (-((2 * math.pi) ** 2) * w))).item())
    err_wyy = float(torch.max(torch.abs(wyy - (-(math.pi ** 2) * w))).item())
    swap_gap = float(torch.max(torch.abs(wxx - wyy)).item())
    detail["T2"] = {"maxDiffWxx": err_wxx, "maxDiffWyy": err_wyy, "swapDiscriminationGap": swap_gap,
                    "probe": "w = sin(2 pi x) cos(pi y)"}

    # T3: the training residual operator applied to the analytic reference through the same torch ops.
    s = xy[:, 0:1] ** 2 + xy[:, 1:2] ** 2
    u_star = ((geo.OUTER_RADIUS ** 2 - s) * (s - geo.INNER_RADIUS ** 2)
              * (1.0 + 0.2 * torch.sin(math.pi * xy[:, 0:1]) * torch.cos(2 * math.pi * xy[:, 1:2])
                 + 0.1 * xy[:, 0:1] - 0.1 * xy[:, 1:2]))
    (gu,) = torch.autograd.grad(u_star, xy, grad_outputs=torch.ones_like(u_star), create_graph=True)
    (gux,) = torch.autograd.grad(gu[:, 0:1], xy, grad_outputs=torch.ones_like(gu[:, 0:1]), create_graph=True)
    (guy,) = torch.autograd.grad(gu[:, 1:2], xy, grad_outputs=torch.ones_like(gu[:, 1:2]), create_graph=True)
    f = torch.tensor([[reference.forcing(x, y)] for x, y in dev_points], dtype=torch.float64)
    residual_max = float(torch.max(torch.abs(-(gux[:, 0:1] + guy[:, 1:2]) - f)).item())
    detail["T3"] = {"residualMaxOnReference": residual_max}

    # T4: the hard parameterization on BOTH components, each measured separately.
    per_component = {}
    for component, block in boundary_sets.items():
        values = pinn.values(model, block["points"], threads=threads)
        per_component[component] = max(abs(v) for v in values)
    detail["T4"] = {"perComponentMaxAbsU": per_component,
                    "nodesPerComponent": {c: len(b["points"]) for c, b in boundary_sets.items()}}

    # T8 / T9
    loaded = {role: load_evaluation_set(document) for role, document in sets.items()}
    disjoint_errors = disjointness_errors(loaded, min_separation=config["sets"].get("minSeparation"))
    detail["T9"] = {"errors": disjoint_errors, "minSeparation": config["sets"].get("minSeparation")}

    # T10: the trusted validator accepts the analytic control and rejects every corrupted fixture.
    verdicts = validator.fixture_verdicts(
        quadrature_points=claim_grids["quadraturePoints"], quadrature_weights=claim_grids["quadratureWeights"],
        pointwise_points=claim_grids["pointwisePoints"], boundary=claim_grids["boundary"])
    t10_ok = all(v["verdictCorrect"] for v in verdicts)
    detail["T10"] = verdicts

    # T11 (new): geometry membership -- the classifier, and every registered set on the domain.
    probe_points = {
        "interior": [geo.to_cartesian(geo.radius_of_area_fraction(t), theta)
                     for t in (0.05, 0.5, 0.95) for theta in (0.3, 2.7, 5.1)],
        "hole": [geo.to_cartesian(r, theta) for r in (0.0, 0.2, 0.349) for theta in (0.3, 2.7)],
        "outside": [geo.to_cartesian(r, theta) for r in (1.001, 1.5) for theta in (0.3, 2.7)],
        "onOuter": [geo.to_cartesian(geo.OUTER_RADIUS, theta) for theta in (0.0, 1.2, 3.9)],
        "onInner": [geo.to_cartesian(geo.INNER_RADIUS, theta) for theta in (0.0, 1.2, 3.9)],
    }
    classification = {name: sorted({geo.classify(p, tolerance=1e-12) for p in points})
                      for name, points in probe_points.items()}
    membership_ok = (classification["interior"] == [geo.INTERIOR] and classification["hole"] == [geo.IN_HOLE]
                     and classification["outside"] == [geo.OUTSIDE] and classification["onOuter"] == [geo.ON_OUTER]
                     and classification["onInner"] == [geo.ON_INNER])
    set_membership = {}
    for role, document in sets.items():
        points = ds.points_of(document)
        report = geo.membership_report(points)
        set_membership[role] = {"illegal": len(report["illegal"]), "count": len(points)}
    sets_clean = all(entry["illegal"] == 0 for entry in set_membership.values())
    detail["T11"] = {"classification": classification, "sets": set_membership}

    # T12 (new): the outward normals of the two components, including the sign a square never had.
    normal_checks = []
    for theta in (0.0, 1.1, 2.6, 4.7):
        outer_point = geo.to_cartesian(geo.OUTER_RADIUS, theta)
        inner_point = geo.to_cartesian(geo.INNER_RADIUS, theta)
        n_out = geo.outward_normal(outer_point, geo.OUTER)
        n_in = geo.outward_normal(inner_point, geo.INNER)
        normal_checks.append({
            "theta": theta,
            "outerRadialComponent": n_out[0] * outer_point[0] + n_out[1] * outer_point[1],
            "innerRadialComponent": n_in[0] * inner_point[0] + n_in[1] * inner_point[1],
            "outerUnit": math.hypot(*n_out), "innerUnit": math.hypot(*n_in)})
    normals_ok = all(entry["outerRadialComponent"] > 0 and entry["innerRadialComponent"] < 0
                     and abs(entry["outerUnit"] - 1.0) < 1e-15 and abs(entry["innerUnit"] - 1.0) < 1e-15
                     for entry in normal_checks)
    # and the identity that makes the sign matter: the analytic flux closes only with the inner normal inward
    flux = {}
    for component, block in boundary_sets.items():
        flux[component] = math.fsum(
            weight * reference.normal_derivative(x, y, component)
            for weight, (x, y) in zip(block["weights"], block["points"]))
    forcing_integral = math.fsum(w * reference.forcing(x, y)
                                 for w, (x, y) in zip(claim_grids["physWeights"], claim_grids["physPoints"]))
    correct_defect = abs(sum(flux.values()) + forcing_integral) / abs(forcing_integral)
    flipped_defect = abs(flux[geo.OUTER] - flux[geo.INNER] + forcing_integral) / abs(forcing_integral)
    detail["T12"] = {"normals": normal_checks, "fluxPerComponent": flux,
                     "analyticFluxDefect": correct_defect, "defectWithFlippedInnerNormal": flipped_defect}
    orientation_ok = normals_ok and correct_defect < 1e-9 and flipped_defect > 1e-2

    # T13 (new): the quadrature Jacobian -- area, a known integral, and no node on a boundary.
    area = math.fsum(claim_grids["physWeights"])
    integral_u = math.fsum(w * reference.solution(x, y)
                           for w, (x, y) in zip(claim_grids["physWeights"], claim_grids["physPoints"]))
    area_error = abs(area - geo.area()) / geo.area()
    integral_error = abs(integral_u - reference.INTEGRAL_U) / abs(reference.INTEGRAL_U)
    jacobian_ok = area_error < 1e-12 and integral_error < 1e-10
    detail["T13"] = {"quadratureArea": area, "exactArea": geo.area(), "areaRelativeError": area_error,
                     "integralU": integral_u, "exactIntegralU": reference.INTEGRAL_U,
                     "integralRelativeError": integral_error,
                     "jacobian": "dx dy = ((R^2 - a^2)/2) dt dtheta (constant)"}

    checks = [
        check("T1-autogradVsFiniteDifference",
              pass_fail(err["x"] < 1e-6 and err["y"] < 1e-6 and err["xx"] < 1e-4 and err["yy"] < 1e-4),
              f"AD vs central differences (h={step}) on a random network, per component: u_x {err['x']:.2e}, "
              f"u_y {err['y']:.2e} (< 1e-6); u_xx {err['xx']:.2e}, u_yy {err['yy']:.2e} (< 1e-4)", evidence),
        check("T2-secondDerivativeComponentSeparation",
              pass_fail(err_wxx < 1e-9 and err_wyy < 1e-9 and swap_gap > 1.0),
              f"asymmetric probe w = sin(2 pi x) cos(pi y): |w_xx + 4 pi^2 w| = {err_wxx:.2e}, |w_yy + pi^2 w| = "
              f"{err_wyy:.2e} (< 1e-9 each); the two components differ by up to {swap_gap:.2f}, so an x/y swap in the "
              "residual operator is detectable here", evidence),
        check("T3-residualOperatorOnReference", pass_fail(residual_max < 1e-10),
              f"max |-Lap u* - f| through the training residual operator on D_dev = {residual_max:.2e} (< 1e-10)",
              evidence),
        check("T4-hardBoundaryBothComponents", pass_fail(max(per_component.values()) < 1e-14),
              f"hard parameterization u = (R^2 - s)(s - a^2) N on both circles: max |u| per component "
              f"{ {k: '%.2e' % v for k, v in per_component.items()} } (round-off, not a penalty)", evidence),
        check("T8-lossTermSeparation", pass_fail(set(config["lossWeights"]) == {"pde"}),
              "the annulus loss carries a single pde term with a frozen weight and no boundary penalty; both Dirichlet "
              "components are enforced by construction and verified independently by T4", evidence),
        check("T9-collocationDisjointness", pass_fail(not disjoint_errors),
              "train | dev | phys | claim pairwise sample-disjoint at the preregistered minimum separation: "
              + ("yes" if not disjoint_errors else "; ".join(disjoint_errors)), evidence),
        check("T10-validatorControlFixtures", pass_fail(t10_ok),
              "trusted annulus validator on its control fixtures: "
              + ", ".join(f"{v['fixture']}={'accepted' if v['accepted'] else 'rejected'}"
                          f"{'' if v['verdictCorrect'] else ' (WRONG)'}" for v in verdicts), evidence),
        check("T11-geometryMembership", pass_fail(membership_ok and sets_clean),
              f"the classifier separates interior / hole / exterior / both circles ({classification}); every "
              f"registered evaluation set is strictly inside the annulus ({set_membership})", evidence),
        check("T12-boundaryNormalOrientation", pass_fail(orientation_ok),
              f"outer normal points away from the origin and inner normal into the hole (unit length to 1e-15); the "
              f"analytic flux identity closes to {correct_defect:.2e} with the registered normals and to "
              f"{flipped_defect:.2e} if the inner sign is flipped -- the check the square never needed", evidence),
        check("T13-quadratureJacobian", pass_fail(jacobian_ok),
              f"geometry-native quadrature: area {area:.12f} vs exact {geo.area():.12f} (relative {area_error:.2e}); "
              f"int u* dA relative error {integral_error:.2e}; Jacobian constant in the area fraction", evidence),
    ]
    return checks, detail


# ------------------------------------------------------------------ Gate 5a

def physics_checks(models: Sequence[Any], phys_points: Sequence[Sequence[float]], phys_weights: Sequence[float],
                   boundary_sets: Mapping[str, Mapping[str, Any]], thresholds: Mapping[str, float],
                   evidence: Sequence[Mapping[str, str]], *, threads: int = 1
                   ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """PH1-PH8 on D_phys for every seed model; each check's status is the meet over seeds (worst seed)."""

    forcing_values = [reference.forcing(x, y) for x, y in phys_points]
    forcing_integral = math.fsum(w * f for w, f in zip(phys_weights, forcing_values))
    u_star_max = max(abs(reference.solution(x, y)) for x, y in phys_points)
    spd = min_eigenvalue(24, 96)
    per_seed: list[dict[str, Any]] = []
    for model in models:
        fld = pinn.fields(model, phys_points, threads=threads)
        flux_components = {}
        for component, block in boundary_sets.items():
            dn = pinn.normal_derivatives(model, block["points"], component, threads=threads)
            flux_components[component] = math.fsum(w * value for w, value in zip(block["weights"], dn))
        flux_total = math.fsum(flux_components.values())
        dirichlet = math.fsum(w * (ux * ux + uy * uy) for w, ux, uy in zip(phys_weights, fld["ux"], fld["uy"]))
        forcing_energy = math.fsum(w * f * value for w, f, value in zip(phys_weights, forcing_values, fld["u"]))
        exact_values = [reference.solution(x, y) for x, y in phys_points]
        sign_violations = sum(1 for value, exact in zip(fld["u"], exact_values)
                              if exact > 1e-3 * u_star_max and value <= 0.0)
        membership = geo.membership_report(phys_points)
        per_seed.append({
            "fluxDefect": abs(flux_total + forcing_integral) / abs(forcing_integral),
            "fluxPerComponent": flux_components,
            "energyDefect": abs(dirichlet - forcing_energy) / reference.DIRICHLET_ENERGY,
            "signViolations": sign_violations,
            "maxAbsU": max(abs(v) for v in fld["u"]),
            "dirichletEnergy": dirichlet,
            "illegalPhysPoints": len(membership["illegal"]),
        })
    worst = {
        "flux": max(entry["fluxDefect"] for entry in per_seed),
        "energy": max(entry["energyDefect"] for entry in per_seed),
        "sign": max(entry["signViolations"] for entry in per_seed),
        "maximum": max(entry["maxAbsU"] for entry in per_seed),
        "energyFloor": min(entry["dirichletEnergy"] for entry in per_seed),
        "illegal": max(entry["illegalPhysPoints"] for entry in per_seed),
    }
    maximum_ratio = worst["maximum"] / u_star_max
    checks = [
        check("PH1-fluxBalance", pass_fail(worst["flux"] <= thresholds["PH1"]),
              f"worst-seed |int_dOmega du/dn ds + int_Omega f dA| / |int f dA| = {worst['flux']:.3e} "
              f"(<= {thresholds['PH1']}), summed over BOTH components with each component's own outward normal; "
              f"per-component fluxes of the worst seed: "
              f"{ {k: '%.4f' % v for k, v in max(per_seed, key=lambda e: e['fluxDefect'])['fluxPerComponent'].items()} }",
              evidence),
        check("PH2-energyBalance", pass_fail(worst["energy"] <= thresholds["PH2"]),
              f"worst-seed |int |grad u|^2 - int f u| / DIRICHLET_ENERGY = {worst['energy']:.3e} "
              f"(<= {thresholds['PH2']}); no boundary term because u vanishes on both components", evidence),
        check("PH3-positivity", pass_fail(worst["sign"] == 0),
              f"the model keeps the sign of the reference where the reference is not near zero: "
              f"{worst['sign']} violation(s) over all seeds", evidence),
        not_applicable("PH4-symmetry"),
        not_applicable("PH5-monotonicity"),
        check("PH6-maximumPrinciple", pass_fail(maximum_ratio <= 1.0 + thresholds["PH6"]),
              f"worst-seed max |u_theta| / max |u*| = {maximum_ratio:.6f} (<= 1 + {thresholds['PH6']})", evidence),
        check("PH7-spd", pass_fail(worst["energyFloor"] > thresholds["PH7_energyFloor"] and spd["lambdaMin"] > 0.0),
              f"Dirichlet energy of every seed model > {thresholds['PH7_energyFloor']} (worst "
              f"{worst['energyFloor']:.6f}); the independent polar operator's smallest eigenvalue is "
              f"{spd['lambdaMin']:.4f} > 0", evidence),
        check("PH8-geometryMembership", pass_fail(worst["illegal"] == 0),
              f"every physics evaluation point is strictly inside the annulus ({worst['illegal']} illegal); the hole "
              "is not part of the domain and no identity may be integrated across it", evidence),
        # Registered NOT_APPLICABLE in REGISTRY and therefore in every frozen ProblemDefinition;
        # a registered check is recorded even when it cannot apply. Omitting these two is what
        # made the r2 trust vector invalid (2026-09-26, owner's ruling: revision 3).
        not_applicable("PH10-momentumBudget"),
        not_applicable("PH11-freeEnergy"),
    ]
    detail = {"perSeed": per_seed, "worst": worst, "forcingIntegral": forcing_integral,
              "uStarMax": u_star_max, "spdWitness": spd,
              "thresholds": dict(thresholds)}
    return checks, detail


# ------------------------------------------------------------------ Gate 5b

def claim_evaluation(model, grids: Mapping[str, Any], *, threads: int = 1) -> dict[str, Any]:
    """Evaluate one model on the OPENED claim member and hand the numbers to the trusted validator."""

    quadrature = pinn.fields(model, grids["quadraturePoints"], threads=threads)
    pointwise = pinn.values(model, grids["pointwisePoints"], threads=threads)
    boundary: dict[str, dict[str, Any]] = {}
    for component, block in grids["boundary"].items():
        boundary[component] = {
            "points": block["points"], "weights": block["weights"],
            "u": pinn.values(model, block["points"], threads=threads),
            "dn": pinn.normal_derivatives(model, block["points"], component, threads=threads),
        }
    fields = validator.FieldsAnnulus(
        quadrature_points=grids["quadraturePoints"], quadrature_weights=grids["quadratureWeights"],
        u_quadrature=quadrature["u"], ux_quadrature=quadrature["ux"], uy_quadrature=quadrature["uy"],
        uxx_quadrature=quadrature["uxx"], uyy_quadrature=quadrature["uyy"],
        pointwise_points=grids["pointwisePoints"], u_pointwise=pointwise, boundary=boundary)
    return validator.evaluate_fields(fields, grid_label=grids["label"])


def external_checks(evaluations: Sequence[Mapping[str, Any]], claim_ref: Mapping[str, str],
                    evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    must_ok = all(not e["failedMustCriteria"] for e in evaluations)
    should_ok = all(not e["failedShouldCriteria"] for e in evaluations)
    failing = [i for i, e in enumerate(evaluations) if e["failedMustCriteria"]]
    return [
        check("G5b-acceptanceCriteriaMust", pass_fail(must_ok),
              f"ACA-1..ACA-7 and ACA-9 (MUST) on the OPENED claim set {claim_ref['sha256'][:12]} for every seed model: "
              + ("all satisfied" if must_ok else
                 f"seeds {failing} fail {[e['failedMustCriteria'] for e in evaluations if e['failedMustCriteria']]}"),
              evidence),
        check("G5b-acceptanceCriteriaShould",
              TrustStatus.PASS if should_ok else TrustStatus.PARTIAL,
              "ACA-8 (SHOULD, relative H1 seminorm) satisfied by every seed" if should_ok
              else f"ACA-8 (SHOULD) missed by {sum(1 for e in evaluations if e['failedShouldCriteria'])} seed model(s); "
                   "PARTIAL, not FAIL", evidence),
    ]


# ------------------------------------------------------------------ Gate 6

def gate6_blocked(reason: str, evidence: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    return [check("G6-independentReproduction", TrustStatus.BLOCKED, reason, evidence)]
