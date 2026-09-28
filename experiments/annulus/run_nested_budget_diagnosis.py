"""Prospective nested optimization-budget intervention on the annulus (DIAGNOSTIC, not a claim run).

This is not a formal attempt and it cannot become one. It opens no claim set, it writes
no ledger event, it produces no TrustVector and no ClaimGateDecision, and it reads only
the REGISTERED D_train and D_dev of the r1 attempt -- the same points, verified by their
recorded sha256, so the comparison is paired rather than merely similar.

The question it exists to answer is narrow: does the SAME 4x64 tanh network, with the
same sampling, the same optimizer and the same first 120000 steps, satisfy the existing
localized acceptance criterion on D_dev when the optimization is simply continued? A yes
discriminates rOptimizationFailure from rCapacityLimit, because a capacity that has
actually reached the criterion is not a capacity limit. A no leaves rCapacityLimit viable
and the round stops there.

Each seed is trained ONCE, 0 -> 240000, and checkpointed at 120000 / 180000 / 240000, so
180k is by construction the continuation of its own 120k state and 240k of its own 180k.
No network is initialised three times. The learning rate follows the budget-decoupled
fixed-prefix schedule: the r1 exponential decay over the first 120000 steps, then held at
the terminal value. Resume fidelity and prefix equivalence are verified separately and
must pass before this driver is run.

Everything a verdict depends on lives here or under ``pinn/``; this file is therefore
declared in the diagnostic config's ``codeIdentityExtraFiles``.

    PYTHONPATH=. PYTHONIOENCODING=utf-8 <mamba python> -u -B \
        experiments/annulus/run_nested_budget_diagnosis.py --device cuda
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
from pinn.experiments_annulus import pinn_torch_annulus as pinn
from pinn.experiments_annulus.localized_error_annulus import (
    LOCALIZED_STATISTIC,
    preregistered_localized_criterion,
)
from pinn.governance.trust_vector import seed_statistics

REPO = Path(__file__).resolve().parents[2]
BASELINE_ATTEMPT = Path("experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu")
DIAGNOSIS_DIR = Path("experiments/annulus/diagnosis")
CONFIG_PATH = DIAGNOSIS_DIR / "config_nested_budget.json"
LEDGER = Path("experiments/annulus/ledger/pdef-annulus-poisson-v1.json")
PREREGISTRATION = "experiments/annulus/ANNULUS_NESTED_BUDGET_INTERVENTION_PREREGISTRATION_20260919.md"

#: Preregistered and frozen before any diagnostic training. 240000 is the maximum; there is
#: no rule anywhere in this file that escalates past it.
BUDGETS: tuple[int, ...] = (120000, 180000, 240000)
LR_PREFIX_STEPS = 120000

#: PART 10. The only intended differences from r1 over the first 120000 steps are how the
#: schedule is represented and the fact that state is now written out. Both are supposed to
#: change nothing, and on this machine the r1 ensemble reproduced itself bit for bit from the
#: same seeds on the same device (max |dW| = 0.0), so the preregistered tolerance is bitwise
#: with a relative floor recorded for the case where a future host is not bit-reproducible.
PREFIX_EQUIVALENCE_RELATIVE_TOLERANCE = 1e-12


def log(message: str) -> None:
    print(f"[{utc_now()}] {message}", flush=True)


def diagnostic_config(baseline: dict, budget: int, *, budgets=BUDGETS, prefix_steps: int = LR_PREFIX_STEPS,
                      smoke: bool = False) -> dict:
    """The r1 method, with the schedule detached from the budget and nothing else touched."""

    config = json.loads(json.dumps(baseline))
    config["configId"] = "annulus-nested-budget-diagnosis-v1"
    config["description"] = (
        "DIAGNOSTIC configuration of the prospective nested optimization-budget intervention. "
        "Derived from the frozen r1 configuration annulus-poisson-hard-bc-v1 by exactly two changes: "
        f"optimizer.steps 120000 -> {budget}, and optimizer.lrPrefixSteps = {prefix_steps} added so the "
        "learning-rate schedule is a property of the method rather than of the requested budget. Architecture, "
        "collocation, batch size, optimizer settings, loss, geometry, thresholds and the localized acceptance "
        "contract are unchanged. This configuration is NOT a revision: it opens no claim set and produces no "
        "claim."
    )
    config["optimizer"]["steps"] = int(budget)
    config["optimizer"]["lrPrefixSteps"] = int(prefix_steps)
    config["diagnostic"] = {
        "marking": "SANDBOX SMOKE" if smoke else "DIAGNOSTIC",
        "formalEvidence": False,
        "purpose": "discriminate rOptimizationFailure from rCapacityLimit for sLocalizedError",
        "setsRead": ["D_train (registered, r1)", "D_dev (registered, r1)"],
        "claimSetsRead": [],
        "budgets": list(budgets),
        "maximumBudget": max(budgets),
        "escalationBeyondMaximum": "forbidden by the preregistration",
        "preregisteredIn": PREREGISTRATION,
    }
    config["codeIdentityExtraFiles"] = ["experiments/annulus/run_nested_budget_diagnosis.py"]
    return config


def paired_seed_triplets(baseline: dict, count: int) -> list[dict[str, int]]:
    """The r1 seed identities, unchanged. A paired design needs the same seeds, not new ones."""

    sp = baseline["seedProtocol"]
    return [{"index": i, "init": sp["initBase"] + i, "sample": sp["sampleBase"] + i, "batch": sp["batchBase"] + i}
            for i in range(count)]


def registered_sets(attempt: Path) -> tuple[dict, dict, dict]:
    """r1's registered train and dev sets, each checked against the ProblemDefinition it was frozen in."""

    pdef = load_json(REPO / attempt / "problem_definition.json")
    sets = {}
    for role in ("train", "dev"):
        doc = load_json(REPO / attempt / f"sets/{role}.json")
        digest = canonical_sha256(doc)
        if digest != pdef["evaluationSets"][role]["sha256"]:
            raise SystemExit(f"the stored {role} set is not the one the r1 ProblemDefinition names")
        sets[role] = doc
    return sets["train"], sets["dev"], pdef


def localized_pass(value: float, criterion: dict) -> bool:
    if criterion["operator"] != "<=":
        raise SystemExit(f"unsupported operator {criterion['operator']!r}")
    return math.isfinite(value) and value <= float(criterion["threshold"])


def evaluate(config: dict, checkpoint: dict, dev_points, phys_points, phys_weights, boundary, criterion) -> dict:
    """D_dev metrics of one checkpoint, computed on the CPU exactly as the formal gates do."""

    weights = ckpt.model_weights(checkpoint)
    model = pinn.model_from_weights(config, weights, threads=int(config["optimizer"].get("threads", 1)))
    measured = diagnostics.dev_diagnostics(model, dev_points, phys_points, phys_weights, boundary,
                                           int(criterion["radialBins"]), int(criterion["angularSectors"]),
                                           threads=int(config["optimizer"].get("threads", 1)))
    worst_cell = max(measured["cellRms"].items(), key=lambda kv: kv[1])
    return {
        "relL2": measured["relL2"],
        LOCALIZED_STATISTIC: measured[LOCALIZED_STATISTIC],
        "localizedPass": localized_pass(measured[LOCALIZED_STATISTIC], criterion),
        "normalizedResidualRms": measured["normalizedResidualRms"],
        "maxBoundaryAbs": measured["maxBoundaryAbs"],
        "fluxBalance": measured["fluxBalance"],
        "localizedRatio": measured["localizedRatio"],
        "worstCell": {"cell": worst_cell[0], "rmsError": worst_cell[1]},
        "cellsCovered": measured["cellsCovered"],
        "cellsExpected": measured["cellsExpected"],
        "referenceRms": measured["referenceRms"],
    }


def budget_verdict(per_seed: list[dict], budget: int, epsilon_spec: float, prereg: dict, criterion: dict) -> dict:
    """Every-seed judgement of one budget. No average is allowed to stand in for a seed."""

    errors = [s["budgets"][str(budget)]["relL2"] for s in per_seed]
    stats = seed_statistics(errors, epsilon_spec=epsilon_spec,
                            worst_factor=float(prereg["worstSeedFactor"]),
                            dispersion_limit=float(prereg["dispersionLimit"]))
    localized = [s["budgets"][str(budget)]["localizedPass"] for s in per_seed]
    finite = [math.isfinite(s["budgets"][str(budget)][LOCALIZED_STATISTIC]) for s in per_seed]
    completed = [s["budgets"][str(budget)]["trainingCompleted"] for s in per_seed]
    localized_values = [s["budgets"][str(budget)][LOCALIZED_STATISTIC] for s in per_seed]
    return {
        "budget": budget,
        "reliability": {"runs": stats.runs, "successes": stats.successes, "divergent": stats.divergent,
                        "median": stats.median, "iqr": stats.iqr, "worst": stats.worst,
                        "medianOk": stats.median_ok, "worstOk": stats.worst_ok,
                        "dispersionOk": stats.dispersion_ok, "status": stats.status.value},
        "reliabilityPass": stats.status.value == "PASS",
        "localized": {"criterionId": criterion["criterionId"], "statistic": LOCALIZED_STATISTIC,
                      "threshold": float(criterion["threshold"]), "seedPolicy": criterion["seedPolicy"],
                      "passing": sum(1 for ok in localized if ok), "of": len(localized),
                      "failingSeedIndices": [i for i, ok in enumerate(localized) if not ok],
                      "median": sorted(localized_values)[len(localized_values) // 2],
                      "worst": max(localized_values)},
        "localizedPass": all(localized),
        "noDivergenceOrInvalidEvidence": all(finite) and all(completed) and stats.divergent == 0,
        "allPass": (stats.status.value == "PASS" and all(localized) and all(finite) and all(completed)
                    and stats.divergent == 0),
    }


def select_b_star(verdicts: list[dict], baseline_budget: int) -> int | None:
    """The MINIMAL preregistered budget above the baseline at which every seed passes.

    Minimal, not "the one that looks best": the candidates are fixed in advance and the first
    that satisfies every condition wins. If none does, the answer is ``None`` -- and there is
    deliberately no branch anywhere that reacts to ``None`` by trying a larger budget. An
    escalation rule is how a diagnosis turns into a search for a number that passes.
    """

    for verdict in sorted(verdicts, key=lambda v: v["budget"]):
        if verdict["budget"] > baseline_budget and verdict["allPass"]:
            return int(verdict["budget"])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--baseline-attempt", type=Path, default=BASELINE_ATTEMPT)
    parser.add_argument("--out", type=Path, default=DIAGNOSIS_DIR / "nested-budget-r1-paired")
    parser.add_argument("--smoke", action="store_true",
                        help="sandbox rehearsal of the whole pipeline on a tiny budget; it is marked SANDBOX, "
                             "writes to its own directory and cannot stand in for the diagnosis. It exists "
                             "because a twelve-hour run is a bad place to discover an API mismatch.")
    args = parser.parse_args()

    budgets, prefix_steps = BUDGETS, LR_PREFIX_STEPS
    if args.smoke:
        budgets, prefix_steps = (300, 450, 600), 300
        args.out = DIAGNOSIS_DIR / ".smoke"
        args.seeds = min(args.seeds, 2)

    out = REPO / args.out
    (out / "checkpoints").mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- firewall, before anything else
    ledger_before = sha256_file(REPO / LEDGER)
    events_before = [e["event"] for e in load_json(REPO / LEDGER)]
    log(f"claim ledger before: {events_before} ({ledger_before[:12]}) -- this driver writes no ledger event")

    baseline_config = load_json(REPO / "experiments/annulus/configs/exp_annulus_baseline.json")
    config = diagnostic_config(baseline_config, max(budgets), budgets=budgets, prefix_steps=prefix_steps,
                               smoke=args.smoke)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    (REPO / CONFIG_PATH).write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8", newline="\n")

    criterion = preregistered_localized_criterion(config["signatureCriteria"], dimension=2)
    if criterion["evaluationSet"] != "dev":
        raise SystemExit("the diagnosis may only read D_dev")
    epsilon_spec = float(config["preregistration"]["epsilonSpec"])

    extra = [CONFIG_PATH.as_posix(), *config["codeIdentityExtraFiles"]]
    manifest = code_manifest(REPO, extra)
    code_hash = code_hash_from_manifest(manifest)
    environment = environment_fingerprint(
        accelerator_class=("cpu-only" if not args.device.startswith("cuda")
                           else "cuda-" + __import__("torch").cuda.get_device_name(0)))
    identity = {
        "marking": "DIAGNOSTIC", "formalEvidence": False,
        "kind": "prospective nested optimization-budget intervention",
        "gitHead": git_head(REPO), "codeHash": code_hash, "codeManifest": manifest,
        "configPath": CONFIG_PATH.as_posix(), "configSha256": sha256_file(REPO / CONFIG_PATH),
        "environment": environment, "trainingDevice": args.device, "evaluationDevice": "cpu",
        "baselineAttempt": args.baseline_attempt.as_posix(),
        "baselineCodeHash": load_json(REPO / args.baseline_attempt / "identity.json")["codeHash"],
        "budgets": list(budgets), "lrPrefixSteps": int(prefix_steps), "smoke": bool(args.smoke),
        "preregisteredIn": PREREGISTRATION,
        "claimSetsTouched": [], "ledgerSha256AtStart": ledger_before,
        "note": "a diagnostic implementation identity, not a claim revision; r1 keeps its own codeHash",
        "startedAt": utc_now(),
    }
    (out / "identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    log(f"diagnostic identity: codeHash={code_hash[:12]} (r1 was {identity['baselineCodeHash'][:12]}) "
        f"device={args.device} accelerator={environment['acceleratorClass']}")

    # ---------------------------------------------------------------- paired data, from r1's registered sets
    train_set, dev_set, pdef = registered_sets(args.baseline_attempt)
    pool = ds.points_of(train_set)
    dev_points = ds.points_of(dev_set)
    phys_points, phys_weights = ds.phys_grid(int(config["sets"]["physRadialOrder"]),
                                             int(config["sets"]["physAngularCount"]))
    boundary = ds.boundary_sets(int(config["sets"]["boundaryNodes"]))
    log(f"paired on r1's REGISTERED sets: train {len(pool)}, dev {len(dev_points)}; specHash {pdef['specHash'][:12]}")

    triplets = paired_seed_triplets(baseline_config, args.seeds)
    baseline_runs = {} if args.smoke else {i: load_json(REPO / args.baseline_attempt / f"runs/run-{i:02d}.json")
                                           for i in range(args.seeds)}

    per_seed: list[dict] = []
    started = time.perf_counter()
    for triplet in triplets:
        index = triplet["index"]
        seeds = {k: triplet[k] for k in ("init", "sample", "batch")}
        log(f"seed {index}: one launch, 0 -> {max(budgets)}, checkpoints at {list(budgets)}; {seeds}")
        captured: dict[int, dict] = {}

        def sink(step: int, state: dict, _index: int = index) -> None:
            captured[step] = state
            path = out / "checkpoints" / f"seed-{_index:02d}-step-{step}.json"
            path.write_text(json.dumps(state, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

        run = pinn.train_run(config, pool, dev_points, seeds,
                             collocation_count=int(config["sampling"]["collocationCount"]),
                             device=args.device, checkpoint_steps=budgets, checkpoint_sink=sink)
        history = {e["step"]: e for e in run["lossHistory"]}
        entry = {"index": index, "seeds": seeds, "elapsedSeconds": run["elapsedSeconds"],
                 "nanEncountered": run["nanEncountered"], "lrSchedule": run["lrSchedule"], "budgets": {}}
        for budget in budgets:
            measured = evaluate(config, captured[budget], dev_points, phys_points, phys_weights, boundary, criterion)
            measured.update({
                "step": budget,
                "trainingCompleted": budget in captured,
                "loss": history[budget]["total"] if budget in history else None,
                "pdeLoss": history[budget]["pde"] if budget in history else None,
                "lrReportedAfterStep": history[budget].get("lr") if budget in history else None,
                "devRelL2OnDevice": captured[budget]["devRelL2"],
            })
            entry["budgets"][str(budget)] = measured
            log(f"  {budget:>7}: relL2 {measured['relL2']:.6e}  {LOCALIZED_STATISTIC} "
                f"{measured[LOCALIZED_STATISTIC]:.6e} -> {'PASS' if measured['localizedPass'] else 'FAIL'}  "
                f"residual {measured['normalizedResidualRms']:.3e}")
        # PART 10: the prefix must reproduce r1, or nothing after it can be read causally
        if args.smoke:
            entry["prefixEquivalence"] = {"skipped": "SANDBOX: a 300-step prefix is not the r1 prefix",
                                          "withinTolerance": True, "sameSeeds": True}
            per_seed.append(entry)
            continue
        old = baseline_runs[index]
        old_history = {e["step"]: e for e in old["lossHistory"]}
        new_120k = captured[120000]["devRelL2"]
        old_120k = old_history[120000]["devRelL2"]
        delta = new_120k - old_120k
        entry["prefixEquivalence"] = {
            "oldDevRelL2At120k": old_120k, "newDevRelL2At120k": new_120k, "delta": delta,
            "bitwise": new_120k == old_120k,
            "relativeDelta": (abs(delta) / abs(old_120k)) if old_120k else float("inf"),
            "withinTolerance": (new_120k == old_120k
                                or (old_120k and abs(delta) / abs(old_120k) <= PREFIX_EQUIVALENCE_RELATIVE_TOLERANCE)),
            "oldSeeds": old["seeds"], "sameSeeds": dict(old["seeds"]) == seeds,
        }
        log(f"  prefix vs r1 @120k: old {old_120k:.17e} new {new_120k:.17e} "
            f"bitwise={entry['prefixEquivalence']['bitwise']}")
        per_seed.append(entry)

    # ---------------------------------------------------------------- verdicts
    prefix_ok = all(s["prefixEquivalence"]["withinTolerance"] and s["prefixEquivalence"]["sameSeeds"]
                    for s in per_seed)
    prereg = config["preregistration"]
    verdicts = [budget_verdict(per_seed, b, epsilon_spec, prereg, criterion) for b in budgets]
    b_star = select_b_star(verdicts, min(budgets))

    ledger_after = sha256_file(REPO / LEDGER)
    events_after = [e["event"] for e in load_json(REPO / LEDGER)]
    firewall_ok = ledger_after == ledger_before and events_after == events_before

    document = {
        "marking": "SANDBOX SMOKE" if args.smoke else "DIAGNOSTIC", "formalEvidence": False,
        "schemaVersion": "pinn.annulus.budgetDiagnosis/1.0",
        "identity": identity,
        "preregisteredIn": PREREGISTRATION,
        "budgets": list(budgets), "maximumBudget": max(budgets),
        "escalation": "forbidden: no budget beyond the preregistered maximum is attempted by this driver",
        "localizedCriterion": criterion,
        "epsilonSpec": epsilon_spec,
        "prefixEquivalence": {"verdict": "PASS" if prefix_ok else "FAIL",
                              "tolerance": {"bitwise": True,
                                            "relativeFallback": PREFIX_EQUIVALENCE_RELATIVE_TOLERANCE},
                              "perSeed": [s["prefixEquivalence"] for s in per_seed]},
        "perSeed": per_seed,
        "budgetVerdicts": verdicts,
        "bStar": b_star,
        "bStarRule": "the smallest preregistered budget above 120000 at which ALL seeds satisfy the existing "
                     "training-reliability condition AND the existing localized acceptance criterion AND show no "
                     "divergence or invalid evidence; no average may stand in for a seed",
        "claimFirewall": {"ledgerSha256AtStart": ledger_before, "ledgerSha256AtEnd": ledger_after,
                          "eventsAtStart": events_before, "eventsAtEnd": events_after,
                          "unchanged": firewall_ok, "claimSetsOpened": []},
        "elapsedSeconds": time.perf_counter() - started,
        "finishedAt": utc_now(),
    }
    (out / "DIAGNOSIS.json").write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")

    log(f"prefix equivalence: {'PASS' if prefix_ok else 'FAIL'}")
    for v in verdicts:
        log(f"  budget {v['budget']:>7}: reliability {v['reliability']['status']} "
            f"localized {v['localized']['passing']}/{v['localized']['of']} "
            f"(worst {v['localized']['worst']:.6e}) -> allPass={v['allPass']}")
    log(f"B* = {b_star if b_star else 'NONE'}")
    log(f"claim firewall intact: {firewall_ok} (ledger {events_after})")
    log(f"-> {out / 'DIAGNOSIS.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
