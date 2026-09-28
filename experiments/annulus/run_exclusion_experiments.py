"""The five diagnosis-only discriminating experiments (external review ruling items 2 and 4).

Each one rules out one candidate root cause of ``sLocalizedError`` by doing something that
would have spoken if that cause were present -- an intervention on the variable it depends
on, or an injection of the cause followed by a measurement showing it is not there. None of
them reads D_claim, writes a ledger event, produces a claim, advances Trust, or has Tier-1
status. Tier-1 keeps its meaning: post-Gate-5 stress testing of an accepted result.

The designs, thresholds and decision rules are frozen before execution in
``experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md``; this file
only executes them and records what came out. It is declared in the experiment config's
``codeIdentityExtraFiles``.

    PYTHONPATH=. PYTHONIOENCODING=utf-8 <mamba python> -u -B \
        experiments/annulus/run_exclusion_experiments.py --device cuda
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

from pinn.experiments.common import (
    canonical_sha256,
    code_hash_from_manifest,
    code_manifest,
    environment_fingerprint,
    git_head,
    load_json,
    sha256_file,
    utc_now,
)
from pinn.experiments_annulus import checkpoint_annulus as ckpt
from pinn.experiments_annulus import datasets_annulus as ds
from pinn.experiments_annulus import diagnostics_annulus as diagnostics
from pinn.experiments_annulus import exclusion_annulus as ex
from pinn.experiments_annulus import pinn_torch_annulus as pinn
from pinn.experiments_annulus.localized_error_annulus import LOCALIZED_STATISTIC
from pinn.geometry import annulus as geo
from pinn.reference import analytic_annulus as reference

REPO = Path(__file__).resolve().parents[2]
BASELINE = Path("experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu")
DIAGNOSIS = Path("experiments/annulus/diagnosis/nested-budget-r1-paired")
OUT_DIR = Path("experiments/annulus/diagnosis/exclusions")
LEDGER = Path("experiments/annulus/ledger/pdef-annulus-poisson-v1.json")
PREREGISTRATION = "experiments/annulus/ANNULUS_EXCLUSION_EXPERIMENT_PREREGISTRATION_20260920.md"

THRESHOLD = 1e-3                     # the ACA-9 acceptance threshold; not a value of this round
R1_BUDGET = 120000
FAILING_SEED = 2

EXPERIMENTS = ("sampling", "implementation", "spec", "reference", "singularity")


def log(message: str) -> None:
    print(f"[{utc_now()}] {message}", flush=True)


def registered_sets() -> tuple[list, list, dict]:
    pdef = load_json(REPO / BASELINE / "problem_definition.json")
    out = []
    for role in ("train", "dev"):
        doc = load_json(REPO / BASELINE / f"sets/{role}.json")
        if canonical_sha256(doc) != pdef["evaluationSets"][role]["sha256"]:
            raise SystemExit(f"the stored {role} set is not the one the r1 ProblemDefinition names")
        out.append(ds.points_of(doc))
    return out[0], out[1], pdef


def evaluate_model(config, model, dev_points, phys_points, phys_weights, boundary) -> dict:
    threads = int(config["optimizer"].get("threads", 1))
    measured = diagnostics.dev_diagnostics(model, dev_points, phys_points, phys_weights, boundary,
                                           ex.RADIAL_BINS, ex.ANGULAR_SECTORS, threads=threads)
    worst = max(measured["cellRms"].items(), key=lambda kv: kv[1])
    return {"relL2": measured["relL2"], LOCALIZED_STATISTIC: measured[LOCALIZED_STATISTIC],
            "localizedPass": measured[LOCALIZED_STATISTIC] <= THRESHOLD,
            "normalizedResidualRms": measured["normalizedResidualRms"],
            "worstCell": worst[0], "worstCellRms": worst[1],
            "referenceRms": measured["referenceRms"], "cellRms": measured["cellRms"],
            "pointwiseAbsError": measured["pointwiseAbsError"], "u": measured["u"]}


# ===================================================================== rSamplingDeficiency

def experiment_sampling(config, pool, dev_points, phys_points, phys_weights, boundary, device) -> dict:
    """INTERVENTIONAL. Change the collocation set; if sampling were the lever, the failure moves."""

    seeds = {"init": config["seedProtocol"]["initBase"] + FAILING_SEED,
             "sample": config["seedProtocol"]["sampleBase"] + FAILING_SEED,
             "batch": config["seedProtocol"]["batchBase"] + FAILING_SEED}
    budget = json.loads(json.dumps(config))
    budget["optimizer"]["steps"] = R1_BUDGET
    probes: dict[str, dict] = {}

    def run(label: str, probe_pool, count: int, probe_seeds: dict, note: str) -> None:
        log(f"  {label}: {count} collocation points from a pool of {len(probe_pool)}, {probe_seeds}")
        record = pinn.train_run(budget, probe_pool, dev_points, probe_seeds, collocation_count=count,
                                device=device, log_every=20000)
        model = pinn.model_from_weights(budget, record["weights"],
                                        threads=int(budget["optimizer"].get("threads", 1)))
        measured = evaluate_model(budget, model, dev_points, phys_points, phys_weights, boundary)
        measured.pop("cellRms"), measured.pop("pointwiseAbsError"), measured.pop("u")
        probes[label] = {"note": note, "collocationCount": count, "poolSize": len(probe_pool),
                         "seeds": probe_seeds, "elapsedSeconds": record["elapsedSeconds"], **measured}
        log(f"    relL2 {measured['relL2']:.6e}  ACA-9 {measured[LOCALIZED_STATISTIC]:.6e} "
            f"-> {'PASS' if measured['localizedPass'] else 'FAIL'}")

    run("S1a", pool, len(pool), seeds,
        "every point of the registered pool: twice the r1 collocation density, fully paired")
    dense_pool = ds.area_uniform_interior(4096, 20261730)
    run("S1b", dense_pool, 2823, seeds,
        "area-density-matched count from a fresh pool; 2823 cannot be drawn from the 2048-point "
        "registered pool, so this probe is not paired and says so")
    for offset in (901, 902, 903):
        run(f"S{offset - 899}", pool, int(config["sampling"]["collocationCount"]),
            {**seeds, "sample": seeds["sample"] + offset},
            "same init and batch, a different draw from the same registered pool")

    # S5: is the hotspot region starved of collocation points?
    indices = load_json(REPO / BASELINE / f"runs/run-{FAILING_SEED:02d}.json")["collocationIndices"]
    counts: dict[str, int] = {}
    for index in indices:
        counts[ex.independent_cell_index(pool[index])] = counts.get(ex.independent_cell_index(pool[index]), 0) + 1
    for i in range(ex.RADIAL_BINS):
        for j in range(ex.ANGULAR_SECTORS):
            counts.setdefault(f"{i},{j}", 0)
    ordered = sorted(counts.values())
    median = (ordered[len(ordered) // 2] if len(ordered) % 2
              else 0.5 * (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]))
    hotspot = load_json(REPO / DIAGNOSIS / "DIAGNOSIS.json")["perSeed"][FAILING_SEED]["budgets"][
        str(R1_BUDGET)]["worstCell"]["cell"]
    s5 = {"hotspotCell": hotspot, "hotspotCollocationCount": counts[hotspot],
          "medianCellCollocationCount": median, "perCellCounts": dict(sorted(counts.items())),
          "hotspotNotStarved": counts[hotspot] >= median}
    log(f"  S5 (collocation density by cell): hotspot cell {hotspot} holds {counts[hotspot]} "
        f"collocation points against a median of {median}")

    a = (not probes["S1a"]["localizedPass"]) and (not probes["S1b"]["localizedPass"])
    b = s5["hotspotNotStarved"]
    alternative_failures = [k for k in ("S2", "S3", "S4") if not probes[k]["localizedPass"]]
    c = len(alternative_failures) <= 1
    return {
        "experimentId": "exp-annulus-dx-sampling", "cause": "rSamplingDeficiency", "kind": "interventional",
        "probes": probes, "S5": s5,
        "criteria": {
            "a_densityDoesNotRescue": {"satisfied": a,
                                       "detail": f"S1a ACA-9 {probes['S1a'][LOCALIZED_STATISTIC]:.6e}, "
                                                 f"S1b ACA-9 {probes['S1b'][LOCALIZED_STATISTIC]:.6e}, "
                                                 f"threshold {THRESHOLD:g}"},
            "b_hotspotNotStarved": {"satisfied": b,
                                    "detail": f"{s5['hotspotCollocationCount']} points in {hotspot} "
                                              f"against a median of {median}"},
            "c_failureDoesNotFollowTheDesign": {"satisfied": c,
                                                "detail": f"alternative draws failing: {alternative_failures}"},
        },
        "excluded": bool(a and b and c),
    }


# ===================================================================== rImplementationDefect

def experiment_implementation(config, dev_points, phys_points, phys_weights, boundary, device) -> dict:
    """POSITIVE-CONTROLLED. Push a known answer through the pipeline that produced the number."""

    import torch                                                          # noqa: PLC0415

    dtype = torch.float64
    threads = int(config["optimizer"].get("threads", 1))

    # I1: the oracle. The exact solution, through the production evaluation path.
    oracle = ex.solution_module(torch, dtype=dtype)
    i1 = evaluate_model(config, oracle, dev_points, phys_points, phys_weights, boundary)
    log(f"  I1 oracle: relL2 {i1['relL2']:.3e}  ACA-9 {i1[LOCALIZED_STATISTIC]:.3e}")

    # I2: the positive control. A bump inside one known cell must be found in that cell.
    target_cell = "2,5"
    radius = geo.radius_of_area_fraction((2 + 0.5) / ex.RADIAL_BINS)
    theta = (5 + 0.5) * (2.0 * math.pi / ex.ANGULAR_SECTORS)
    bx, by = geo.to_cartesian(radius, theta)
    bumped = ex.solution_module(torch, dtype=dtype,
                                bump={"x": bx, "y": by, "amplitude": 5e-3, "sigma": 0.02})
    i2 = evaluate_model(config, bumped, dev_points, phys_points, phys_weights, boundary)
    exact_dev = [reference.solution(x, y) for x, y in dev_points]
    i2_independent = ex.independent_localized_statistic(
        dev_points, [abs(a - b) for a, b in zip(i2["u"], exact_dev)], exact_dev)
    i2_relative = abs(i2[LOCALIZED_STATISTIC] - i2_independent["statistic"]) / i2_independent["statistic"]
    log(f"  I2 injected bump in cell {target_cell}: pipeline reports {i2['worstCell']}, "
        f"statistic agreement {i2_relative:.3e}")

    # I3: the failing seed's own number, recomputed by an independently written routine.
    checkpoint = load_json(REPO / DIAGNOSIS / f"checkpoints/seed-{FAILING_SEED:02d}-step-{R1_BUDGET}.json")
    model = pinn.model_from_weights(config, ckpt.model_weights(checkpoint), threads=threads)
    production = evaluate_model(config, model, dev_points, phys_points, phys_weights, boundary)
    independent = ex.independent_localized_statistic(dev_points, production["pointwiseAbsError"], exact_dev)
    i3_relative = abs(production[LOCALIZED_STATISTIC] - independent["statistic"]) / independent["statistic"]
    log(f"  I3 independent recomputation: production {production[LOCALIZED_STATISTIC]:.9e} vs "
        f"independent {independent['statistic']:.9e} (relative {i3_relative:.3e})")

    # I4: autodiff against central differences at the hotspot cell.
    hotspot = production["worstCell"]
    probes = [p for p in dev_points if ex.independent_cell_index(p) == hotspot][:16]
    fields = pinn.fields(model, probes, threads=threads)
    step = 1e-5
    worst_fd = 0.0
    for index, point in enumerate(probes):
        shifted = [[point[0] + step, point[1]], [point[0] - step, point[1]],
                   [point[0], point[1] + step], [point[0], point[1] - step]]
        values = pinn.values(model, shifted, threads=threads)
        fd_x = (values[0] - values[1]) / (2.0 * step)
        fd_y = (values[2] - values[3]) / (2.0 * step)
        for ad, fd in ((fields["ux"][index], fd_x), (fields["uy"][index], fd_y)):
            worst_fd = max(worst_fd, abs(ad - fd) / max(abs(fd), 1e-12))
    log(f"  I4 autodiff vs central differences over {len(probes)} hotspot points: worst relative {worst_fd:.3e}")

    criteria = {
        "I1_oracleIsMachineZero": {"satisfied": i1["relL2"] <= 1e-12 and i1[LOCALIZED_STATISTIC] <= 1e-12,
                                   "detail": f"relL2 {i1['relL2']:.3e}, ACA-9 {i1[LOCALIZED_STATISTIC]:.3e}"},
        "I2_positiveControlIsLocated": {"satisfied": i2["worstCell"] == target_cell and i2_relative <= 1e-9,
                                        "detail": f"injected {target_cell}, reported {i2['worstCell']}, "
                                                  f"statistic agreement {i2_relative:.3e}"},
        "I3_independentRecomputationAgrees": {"satisfied": i3_relative <= 1e-12,
                                              "detail": f"relative difference {i3_relative:.3e}"},
        "I4_autodiffMatchesFiniteDifferences": {"satisfied": worst_fd <= 1e-6,
                                                "detail": f"worst relative difference {worst_fd:.3e}"},
    }
    return {
        "experimentId": "exp-annulus-dx-implementation", "cause": "rImplementationDefect",
        "kind": "positive-controlled",
        "I1": {k: v for k, v in i1.items() if k not in ("cellRms", "pointwiseAbsError", "u")},
        "I2": {"targetCell": target_cell, "bump": {"x": bx, "y": by, "amplitude": 5e-3, "sigma": 0.02},
               "reportedWorstCell": i2["worstCell"], "productionStatistic": i2[LOCALIZED_STATISTIC],
               "independentStatistic": i2_independent["statistic"], "relativeDifference": i2_relative},
        "I3": {"productionStatistic": production[LOCALIZED_STATISTIC],
               "independentStatistic": independent["statistic"], "relativeDifference": i3_relative,
               "productionWorstCell": production["worstCell"], "independentWorstCell": independent["worstCell"]},
        "I4": {"points": len(probes), "cell": hotspot, "worstRelativeDifference": worst_fd, "step": step},
        "criteria": criteria,
        "excluded": all(entry["satisfied"] for entry in criteria.values()),
        "errorSpatialDistribution": {"cellRms": production["cellRms"], "worstCell": production["worstCell"],
                                     "referenceRms": production["referenceRms"]},
    }


# ===================================================================== rSpecDefect

def experiment_spec(dev_points) -> dict:
    """POSITIVE-CONTROLLED. Two independent routes to the same identity, then a deliberate defect."""

    import torch                                                          # noqa: PLC0415

    analytic = ex.spec_residual_analytic(dev_points)
    autodiff = ex.spec_residual_autodiff(torch, dev_points, dtype=torch.float64)
    boundary = ex.boundary_values()
    perturbed = ex.spec_residual_analytic(dev_points, forcing=lambda x, y: reference.forcing(x, y) * 1.000001)
    log(f"  C1 analytic route max |-Lap u* - f| = {analytic['maxAbsResidual']:.3e}")
    log(f"  C1 autodiff route max |-Lap u* - f| = {autodiff['maxAbsResidual']:.3e}")
    log(f"  C2 boundary max |u*| = {boundary}")
    log(f"  C3 positive control (forcing x 1.000001) = {perturbed['maxAbsResidual']:.3e}")

    criteria = {
        "C1_bothRoutesAreMachineZero": {
            "satisfied": analytic["maxAbsResidual"] <= 1e-12 and autodiff["maxAbsResidual"] <= 1e-12,
            "detail": f"analytic {analytic['maxAbsResidual']:.3e}, autodiff {autodiff['maxAbsResidual']:.3e}"},
        "C2_bothComponentsVanish": {"satisfied": all(v <= 1e-14 for v in boundary.values()),
                                    "detail": json.dumps({k: f"{v:.3e}" for k, v in boundary.items()})},
        "C3_positiveControlIsDetected": {"satisfied": perturbed["maxAbsResidual"] >= 1e-6,
                                         "detail": f"injected defect raises the residual to "
                                                   f"{perturbed['maxAbsResidual']:.3e}"},
    }
    return {"experimentId": "exp-annulus-dx-spec", "cause": "rSpecDefect", "kind": "positive-controlled",
            "C1": {"analytic": analytic, "autodiff": autodiff}, "C2": boundary, "C3": perturbed,
            "criteria": criteria, "excluded": all(e["satisfied"] for e in criteria.values())}


# ===================================================================== rReferenceDefect

def control_verdict(orders, band: tuple[float, float] = (1.8, 2.2)) -> tuple[bool, bool]:
    """``(executed, detected)`` for a convergence-order positive control.

    Fails closed on non-finite evidence. A deliberately wrong operator that diverged did not
    demonstrate anything: the control was supposed to stay convergent and lose second order,
    and NaN is not "outside the band", it is the absence of a measurement. Reading it as a
    pass is the same defect the localized-error trigger was hardened against on 2026-09-16,
    and it appeared here in this round's own code.
    """

    values = list(orders)
    executed = bool(values) and all(math.isfinite(float(o)) for o in values)
    detected = executed and any(not (band[0] <= float(o) <= band[1]) for o in values)
    return executed, detected


def experiment_reference(hotspot_cell: str, model_hotspot_rms: float) -> dict:
    """PATH AUDIT + POSITIVE-CONTROLLED. Can the reference even enter the number that failed?"""

    from scientific_reference import annulus_polar_fdm as fdm              # noqa: PLC0415

    audit = ex.statistic_call_path_modules()
    refinement = fdm.refinement_diagnostic(reference.forcing, reference.solution)
    orders = refinement["observedOrders"]
    finest = fdm.solve(reference.forcing, 64, 256)
    localized = ex.localized_reference_error(finest)
    reference_hotspot = localized["cellRms"].get(hotspot_cell, float("inf"))
    corrupted = ex.corrupted_polar_refinement([(16, 64), (32, 128)])
    corrupted_orders = corrupted["observedOrders"]
    control_executed, control_detected = control_verdict(corrupted_orders)
    log(f"  R1 modules reaching the numerical reference: {audit['modulesReachingTheNumericalReference']}")
    log(f"  R2 observed orders {['%.4f' % o for o in orders]}")
    log(f"  R3 reference error in the hotspot cell {hotspot_cell}: {reference_hotspot:.3e} "
        f"against the model's {model_hotspot_rms:.3e}")
    log(f"  R4 corrupted operator observed orders {['%.4f' % o for o in corrupted['observedOrders']]}")

    criteria = {
        "R1_theStatisticCannotReadTheReference": {
            "satisfied": not audit["statisticCanReadTheNumericalReference"],
            "detail": f"modules reaching scientific_reference: "
                      f"{audit['modulesReachingTheNumericalReference']}"},
        "R2_secondOrderConvergence": {"satisfied": all(1.8 <= o <= 2.2 for o in orders),
                                      "detail": f"observed orders {orders}"},
        "R3_referenceIsFarBelowTheModelInTheHotspot": {
            "satisfied": reference_hotspot <= model_hotspot_rms / 10.0,
            "detail": f"reference {reference_hotspot:.3e} vs model {model_hotspot_rms:.3e}"},
        "R4_positiveControlIsDetected": {
            "satisfied": control_detected,
            "controlExecuted": control_executed,
            "detail": (f"corrupted operator observed orders {corrupted_orders}" if control_executed else
                       f"the control produced non-finite orders {corrupted_orders}: the corrupted iteration "
                       "diverged instead of converging at a lower order, so the control did not execute and "
                       "demonstrates no sensitivity")},
    }
    return {"experimentId": "exp-annulus-dx-reference", "cause": "rReferenceDefect",
            "kind": "path audit + positive-controlled",
            "R1": audit, "R2": refinement, "R3": {"hotspotCell": hotspot_cell,
                                                  "referenceCellRms": reference_hotspot,
                                                  "modelCellRms": model_hotspot_rms,
                                                  "maxReferenceCellRms": localized["maxCellRms"]},
            "R4": {**corrupted, "controlExecuted": control_executed}, "criteria": criteria,
            "excluded": all(e["satisfied"] for e in criteria.values())}


# ===================================================================== rSingularityTreatment

def experiment_singularity(dev_points) -> dict:
    """POSITIVE-CONTROLLED. A real singularity would land against a circle; show the test can see that."""

    regularity = ex.regularity_by_cell(dev_points)
    diagnosis = load_json(REPO / DIAGNOSIS / "DIAGNOSIS.json")
    worst_cells = [seed["budgets"][str(b)]["worstCell"]["cell"]
                   for seed in diagnosis["perSeed"] for b in diagnosis["budgets"]]
    adjacent = [cell for cell in worst_cells if ex.boundary_adjacent(cell)]
    field = ex.singular_error_field(dev_points)
    exact_dev = [reference.solution(x, y) for x, y in dev_points]
    control = ex.independent_localized_statistic(dev_points, field["errors"], exact_dev)
    log(f"  G1 per-cell max |Lap u*|: max/median = {regularity['ratioMaxOverMedian']:.3f}")
    log(f"  G2 boundary-adjacent worst cells: {len(adjacent)} of {len(worst_cells)}")
    log(f"  G3 positive control hotspot: {control['worstCell']} "
        f"(adjacent={ex.boundary_adjacent(control['worstCell'])})")

    criteria = {
        "G1_theSolutionIsRegular": {"satisfied": regularity["ratioMaxOverMedian"] <= 10.0,
                                    "detail": f"max/median per-cell |Lap u*| = "
                                              f"{regularity['ratioMaxOverMedian']:.3f}"},
        "G2_noHotspotTouchesAcircle": {"satisfied": len(adjacent) == 0,
                                       "detail": f"{len(adjacent)} of {len(worst_cells)} worst cells are in "
                                                 f"radial bin 0 or 3"},
        "G3_positiveControlLandsOnTheBoundary": {
            "satisfied": control["worstCell"].split(",")[0] == "0",
            "detail": f"an r^(-1/3) field anchored on the inner circle is localized to "
                      f"{control['worstCell']}"},
    }
    return {"experimentId": "exp-annulus-dx-singularity", "cause": "rSingularityTreatment",
            "kind": "positive-controlled",
            "G1": {k: v for k, v in regularity.items() if k != "perCell"},
            "G2": {"worstCells": worst_cells, "boundaryAdjacent": adjacent, "total": len(worst_cells)},
            "G3": {"anchor": field["anchor"], "exponent": field["exponent"],
                   "hotspot": control["worstCell"], "statistic": control["statistic"]},
            "criteria": criteria, "excluded": all(e["satisfied"] for e in criteria.values())}


# ===================================================================== driver

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--experiments", default=",".join(EXPERIMENTS))
    args = parser.parse_args()
    wanted = [name.strip() for name in args.experiments.split(",") if name.strip()]
    for name in wanted:
        if name not in EXPERIMENTS:
            raise SystemExit(f"unknown experiment {name!r}; known: {EXPERIMENTS}")

    out = REPO / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    ledger_before = sha256_file(REPO / LEDGER)
    events_before = [e["event"] for e in load_json(REPO / LEDGER)]
    log(f"claim ledger before: {events_before} ({ledger_before[:12]}) -- no experiment here writes one")

    config = load_json(REPO / "experiments/annulus/configs/exp_annulus_baseline.json")
    extra = ["experiments/annulus/configs/exp_annulus_baseline.json",
             "experiments/annulus/run_exclusion_experiments.py"]
    manifest = code_manifest(REPO, extra)
    code_hash = code_hash_from_manifest(manifest)
    accelerator = "cpu-only"
    if args.device.startswith("cuda"):
        import torch                                                      # noqa: PLC0415
        accelerator = "cuda-" + torch.cuda.get_device_name(0)
    identity = {
        "marking": "DIAGNOSIS-ONLY DISCRIMINATING EXPERIMENTS", "formalEvidence": False,
        "tier1": False, "producesClaim": False, "advancesTrust": False, "claimSetEvents": [],
        "gitHead": git_head(REPO), "codeHash": code_hash, "environment": environment_fingerprint(
            accelerator_class=accelerator),
        "trainingDevice": args.device, "evaluationDevice": "cpu",
        "preregisteredIn": PREREGISTRATION, "ledgerSha256AtStart": ledger_before,
        "startedAt": utc_now(),
    }
    log(f"identity: codeHash={code_hash[:12]} device={args.device}")

    pool, dev_points, pdef = registered_sets()
    phys_points, phys_weights = ds.phys_grid(int(config["sets"]["physRadialOrder"]),
                                             int(config["sets"]["physAngularCount"]))
    boundary = ds.boundary_sets(int(config["sets"]["boundaryNodes"]))
    log(f"paired on r1's registered sets: train {len(pool)}, dev {len(dev_points)}; "
        f"specHash {pdef['specHash'][:12]}")

    results: dict[str, dict] = {}
    started = time.perf_counter()

    if "implementation" in wanted:
        log("exp-annulus-dx-implementation (rImplementationDefect)")
        results["implementation"] = experiment_implementation(config, dev_points, phys_points, phys_weights,
                                                              boundary, args.device)
    if "spec" in wanted:
        log("exp-annulus-dx-spec (rSpecDefect)")
        results["spec"] = experiment_spec(dev_points)
    if "singularity" in wanted:
        log("exp-annulus-dx-singularity (rSingularityTreatment)")
        results["singularity"] = experiment_singularity(dev_points)
    if "reference" in wanted:
        log("exp-annulus-dx-reference (rReferenceDefect)")
        hotspot = load_json(REPO / DIAGNOSIS / "DIAGNOSIS.json")["perSeed"][FAILING_SEED]["budgets"][
            str(R1_BUDGET)]["worstCell"]
        results["reference"] = experiment_reference(hotspot["cell"], hotspot["rmsError"])
    if "sampling" in wanted:
        log("exp-annulus-dx-sampling (rSamplingDeficiency)")
        results["sampling"] = experiment_sampling(config, pool, dev_points, phys_points, phys_weights,
                                                  boundary, args.device)

    ledger_after = sha256_file(REPO / LEDGER)
    events_after = [e["event"] for e in load_json(REPO / LEDGER)]
    for name, result in results.items():
        result.update({"preregisteredIn": PREREGISTRATION, "identity": identity,
                       "claimFirewall": {"ledgerSha256AtStart": ledger_before,
                                         "ledgerSha256AtEnd": ledger_after,
                                         "unchanged": ledger_after == ledger_before,
                                         "eventsAtEnd": events_after},
                       "finishedAt": utc_now()})
        path = out / f"{result['experimentId']}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        log(f"  {result['experimentId']}: {result['cause']} excluded={result['excluded']} -> {path.name}")

    # The summary is built from every artifact on disk, not only from this invocation: the
    # experiments have very different costs and are meant to be runnable in pieces, and a
    # summary that silently forgot the ones run earlier would be worse than no summary.
    on_disk = {}
    for path in sorted(out.glob("exp-annulus-dx-*.json")):
        record = load_json(path)
        on_disk[record["cause"]] = {"experiment": record["experimentId"], "excluded": record["excluded"],
                                    "kind": record["kind"], "artifact": path.name,
                                    "sha256": sha256_file(path), "finishedAt": record.get("finishedAt")}
    summary = {
        "marking": "DIAGNOSIS-ONLY", "formalEvidence": False,
        "identity": identity, "preregisteredIn": PREREGISTRATION,
        "exclusions": dict(sorted(on_disk.items())),
        "causesStillOpen": sorted(cause for cause, entry in on_disk.items() if not entry["excluded"]),
        "allExcluded": bool(on_disk) and all(entry["excluded"] for entry in on_disk.values()),
        "claimFirewall": {"ledgerSha256AtStart": ledger_before, "ledgerSha256AtEnd": ledger_after,
                          "unchanged": ledger_after == ledger_before,
                          "eventsAtStart": events_before, "eventsAtEnd": events_after},
        "elapsedSeconds": time.perf_counter() - started, "finishedAt": utc_now(),
    }
    (out / "EXCLUSIONS.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    log(f"claim firewall intact: {summary['claimFirewall']['unchanged']} (ledger {events_after})")
    log(f"all excluded: {summary['allExcluded']} -> {out / 'EXCLUSIONS.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
