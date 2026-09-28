"""Closing an annulus attempt after Gate 5: merge Tier-1, judge the G6 reproduction, apply G6.

The square experiment has these steps in ``runner2d.py`` (``run_redteam``,
``judge_reproduction``, ``run_apply_g6``); they are re-expressed here against the annulus
attempt's ARTIFACTS rather than imported, because the 2D functions resume a 2D attempt
object and importing them would bind the annulus verdict to the 2D runner's code. The
rules are the 2D rules unchanged:

* Tier-1 may maintain or downgrade a dimension, never upgrade one.
* C_repro (Constitution 54): same specHash, same codeHash, independent environment,
  different seed set, dev metrics within the tolerance frozen in the config.
* ACCEPTED only through Gate 6 PASS with a signed ClaimGateDecision (C2 allowed);
  anything else leaves the attempt in REPRODUCIBILITY_CHECK and says why.
"""

from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any, Mapping

from pinn.experiments.common import ArtifactStore, load_json, sha256_file, utc_now
from pinn.governance.canonical import canonical_sha256
from pinn.governance.state_machine import IllegalTransition, WorkflowState, advance
from pinn.governance.trust_loop import validate_run_record, validate_trust_vector
from pinn.governance.trust_vector import (
    EnvironmentFingerprint,
    RunQualification,
    TrustStatus,
    independent_environments,
    reproduction_status,
)

from . import gates_annulus as gates
from . import runner_annulus as runner
from .runner_annulus import DIMENSIONS, EXECUTOR, GATE_FROM_TRUST, build_decision, dimension_entry, log, repo_root

ORDER = {"PASS": 0, "PARTIAL": 1, "FAIL": 2, "BLOCKED": 3, "NOT_CHECKED": 4}


def _decision(attempt_dir: Path, vector_doc: Mapping[str, Any], tv_ref: Mapping[str, str], suffix: str
              ) -> dict[str, Any]:
    """The superseding ClaimGateDecision, through the same validated builder the attempt used."""

    first = load_json(attempt_dir / "claim_gate_decision.json")
    store = ArtifactStore(attempt_dir, producer=EXECUTOR)
    decision, _gate = build_decision(
        vector_doc, tv_ref, pdef=load_json(attempt_dir / "problem_definition.json"),
        code_hash=first["codeHash"], events=load_json(runner.LEDGER_DIR / f"{first['problemId']}.json"),
        run_record=load_json(attempt_dir / "run_record.json"), statement_ref=store.ref("claim_statements.json"),
        evidence_refs=[dict(tv_ref)],
        # decisionId allows [a-z0-9-] only (schema 1.2); the file suffixes use "_", the ids use "-"
        decision_id=f"{first['decisionId']}{suffix.replace('_', '-')}")
    return decision


def _superseding_vector(attempt_dir: Path, prior: Mapping[str, Any], dims: Mapping[str, Any], suffix: str
                        ) -> dict[str, Any]:
    """Schema-1.2 vector that supersedes ``prior``; validated against the frozen spec before it is written."""

    base_id = prior["recordId"].split("-tier1")[0].split("-g6")[0]
    document = {"schemaVersion": "pinn.trustVector/1.2", "recordId": f"{base_id}{suffix}",
                "problemId": prior["problemId"], "revision": prior["revision"], "specHash": prior["specHash"],
                "dimensions": copy.deepcopy(dict(dims)), "supersedesRecordId": prior["recordId"]}
    errors = validate_trust_vector(document, load_json(attempt_dir / "problem_definition.json"))
    if errors:
        raise SystemExit(f"TrustVector invalid: {errors}")
    return document


def _state(attempt_dir: Path) -> WorkflowState:
    return WorkflowState(load_json(attempt_dir / "attempt_state.json")["state"])


def merge_tier1(attempt_dir: Path) -> dict[str, Any]:
    """Fold ``tier1_redteam.json`` into a superseding trust vector and decision (downgrade only)."""

    attempt_dir = Path(attempt_dir)
    if _state(attempt_dir) is not WorkflowState.REPRODUCIBILITY_CHECK:
        raise SystemExit(f"Tier-1 is merged in REPRODUCIBILITY_CHECK; attempt is in {_state(attempt_dir).value}")
    store = ArtifactStore(attempt_dir, producer=EXECUTOR)
    tier1 = load_json(attempt_dir / "tier1_redteam.json")
    tier_ref = store.ref("tier1_redteam.json")
    prior = load_json(attempt_dir / "trust_vector.json")
    dims = copy.deepcopy(prior["dimensions"])
    for dim, impact in tier1["dimensionImpact"].items():
        entry = dims.get(dim)
        if entry is None or entry["status"] == "NOT_CHECKED":
            continue
        entry["perturbationsRun"] = sorted(r["id"] for r in tier1["results"] if r["dimension"] == dim)
        entry["worstCase"] = tier1["worstCase"][dim]
        if ORDER[impact] > ORDER[entry["status"]]:
            entry["status"] = impact
            entry["notes"] = (entry.get("notes", "") + f"; Tier-1 Red Team downgraded to {impact}: "
                              f"{tier1['worstCase'][dim]}").strip("; ")
        entry["evidencePointers"] = list(entry.get("evidencePointers", [])) + [tier_ref]
        entry["judgedAt"], entry["judgedBy"] = utc_now(), EXECUTOR
    vector_doc = _superseding_vector(attempt_dir, prior, dims, "-tier1")
    decision = _decision(attempt_dir, vector_doc, {"artifactId": "trust_vector_tier1.json",
                                                   "sha256": canonical_sha256(vector_doc)},
                         "_tier1")
    tv_ref = store.write_canonical("trust_vector_tier1.json", vector_doc, role="TRUST_VECTOR",
                                   parents=[tier_ref["artifactId"]])
    store.write_canonical("claim_gate_decision_tier1.json", decision, role="CLAIM_GATE_DECISION",
                          parents=[tv_ref["artifactId"]])
    allowed = [c["level"] for c in decision["allowedClaims"]]
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    summary.setdefault("redTeam", {})["tier1"] = {
        "passed": tier1["passed"], "dimensionImpact": tier1["dimensionImpact"], "worstCase": tier1["worstCase"],
        "trustVectorAfter": {d: dims[d]["status"] for d in dims}, "allowedClaimsAfter": allowed}
    store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    state = _state(attempt_dir).value
    store.transition(state, state, gate=None, result=f"TIER1:{'PASS' if tier1['passed'] else 'DOWNGRADE'}",
                     detail=str(tier1["dimensionImpact"]))
    log(f"Tier-1 merged: {tier1['dimensionImpact']}; allowed claims {allowed}")
    return {"trustVector": {d: dims[d]["status"] for d in dims}, "allowedClaims": allowed}


def judge_reproduction(original_dir: Path, reproduction_dir: Path, *, write: bool = True) -> dict[str, Any]:
    """C_repro per Constitution 54, with the tolerance frozen in the original attempt's config."""

    original_dir, reproduction_dir = Path(original_dir), Path(reproduction_dir)
    original_record = load_json(original_dir / "run_record.json")
    repro_record = load_json(reproduction_dir / "run_record.json")
    a = load_json(original_dir / "training_report.json")["seedStatistics"]
    b = load_json(reproduction_dir / "training_report.json")["seedStatistics"]
    if validate_run_record(original_record) or validate_run_record(repro_record):
        raise SystemExit("a RunRecord does not validate; reproduction cannot be judged")
    identity = load_json(original_dir / "identity.json")
    tolerance = load_json(repo_root() / identity["configPath"])["reproduction"]
    env_a = EnvironmentFingerprint.from_mapping(original_record["environment"])
    env_b = EnvironmentFingerprint.from_mapping(repro_record["environment"])
    independent = independent_environments(env_a, env_b)
    differing = sorted(k for k in env_a.strong_material()
                       if original_record["environment"][k] != repro_record["environment"].get(k))
    same_spec = original_record["specHash"] == repro_record["specHash"]
    same_code = original_record["codeHash"] == repro_record["codeHash"]
    different_seeds = original_record["seedSetId"] != repro_record["seedSetId"]
    a_med, b_med = a["median"], b["median"]
    diff = abs(a_med - b_med) if math.isfinite(a_med) and math.isfinite(b_med) else math.inf
    relative_limit = float(tolerance["devRelL2MedianRelDiff"]) * abs(a_med) if math.isfinite(a_med) else math.inf
    verdict_agree = a["status"] == b["status"]
    within = (diff <= float(tolerance["devRelL2MedianAbsDiff"]) and diff <= relative_limit
              and (verdict_agree or not tolerance.get("seedProtocolVerdictMustAgree", True)))
    qualification = [RunQualification(run_id=r["runId"], spec_hash=r["specHash"], code_hash=r["codeHash"],
                                      environment_id=r["environmentId"], seed_set_id=r["seedSetId"])
                     for r in (original_record, repro_record)]
    verdict = reproduction_status(*qualification, within_tolerance=within)
    line = (f"independent={independent} ({differing}), sameSpec={same_spec}, sameCode={same_code}, "
            f"differentSeeds={different_seeds}, median A {a_med:.3e} vs B {b_med:.3e} (|diff| {diff:.3e}; "
            f"absolute limit {tolerance['devRelL2MedianAbsDiff']}, relative limit {relative_limit:.3e}), "
            f"verdict A {a['status']} vs B {b['status']} -> C_repro {verdict.status.value}")
    report = {
        "reproductionOf": original_dir.name, "originalRunId": original_record["runId"],
        "reproductionRunId": repro_record["runId"], "specHash": repro_record["specHash"], "sameSpec": same_spec,
        "codeHashA": original_record["codeHash"], "codeHashB": repro_record["codeHash"], "sameCode": same_code,
        "seedSetIdA": original_record["seedSetId"], "seedSetIdB": repro_record["seedSetId"],
        "differentSeedSet": different_seeds, "environmentA": original_record["environment"],
        "environmentIdA": original_record["environmentId"], "environmentB": repro_record["environment"],
        "environmentIdB": repro_record["environmentId"], "independentEnvironments": independent,
        "strongFieldsDiffering": differing, "tolerance": tolerance,
        "metrics": {"medianA": a_med, "medianB": b_med, "medianAbsDiff": diff,
                    "successRateA": a["successRate"], "successRateB": b["successRate"],
                    "verdictA": a["status"], "verdictB": b["status"]},
        "relativeLimit": relative_limit, "withinTolerance": within, "cRepro": verdict.status.value,
        "problems": list(verdict.problems), "claimSetTouched": False, "judgedAt": utc_now(), "summaryLine": line,
    }
    if write:
        ArtifactStore(reproduction_dir, producer=EXECUTOR).write_json(
            "reproduction_report.json", report, role="REPRODUCTION_REPORT",
            parents=["run_record.json", "training_report.json"])
    log(f"judge-reproduction {reproduction_dir.name}: {line}")
    return report


def apply_g6(attempt_dir: Path, reproduction_dir: Path) -> dict[str, Any]:
    """Gate 6 on the original attempt; ACCEPTED only with PASS and a signed C2 decision."""

    attempt_dir, reproduction_dir = Path(attempt_dir), Path(reproduction_dir)
    if _state(attempt_dir) is not WorkflowState.REPRODUCIBILITY_CHECK:
        raise SystemExit(f"Gate 6 executes in REPRODUCIBILITY_CHECK; attempt is in {_state(attempt_dir).value}")
    report = load_json(reproduction_dir / "reproduction_report.json")
    if report["reproductionOf"] != attempt_dir.name:
        raise SystemExit("the reproduction report belongs to another attempt")
    status = TrustStatus(report["cRepro"])
    evidence = [{"artifactId": f"{reproduction_dir.name}/{name}", "sha256": sha256_file(reproduction_dir / name)}
                for name in ("reproduction_report.json", "run_record.json")]
    g6 = [gates.check("G6-independentReproduction", status, report["summaryLine"], evidence)]
    store = ArtifactStore(attempt_dir, producer=EXECUTOR)
    g6_ref = store.write_json("gate6_reproducibility_executed.json", {"checks": g6, "reproduction": report},
                              role="GATE_RESULT")
    base = "trust_vector_tier1.json" if (attempt_dir / "trust_vector_tier1.json").exists() else "trust_vector.json"
    prior = load_json(attempt_dir / base)
    dims = copy.deepcopy(prior["dimensions"])
    dims["repro"] = dimension_entry(status, g6, [g6_ref])
    vector_doc = _superseding_vector(attempt_dir, prior, dims, "-g6")
    decision = _decision(attempt_dir, vector_doc, {"artifactId": "trust_vector_g6.json",
                                                   "sha256": canonical_sha256(vector_doc)},
                         "_g6")
    tv_ref = store.write_canonical("trust_vector_g6.json", vector_doc, role="TRUST_VECTOR",
                                   parents=[g6_ref["artifactId"]])
    cgd_ref = store.write_canonical("claim_gate_decision_g6.json", decision, role="CLAIM_GATE_DECISION",
                                    parents=[tv_ref["artifactId"]])
    allowed = [c["level"] for c in decision["allowedClaims"]]
    result = GATE_FROM_TRUST[status]
    vector = {d: TrustStatus(dims[d]["status"]) if d in dims else TrustStatus.NOT_CHECKED for d in DIMENSIONS}
    before = WorkflowState.REPRODUCIBILITY_CHECK
    try:
        after = advance(before, 6, result, vector, claim_decision_signed="C2" in allowed)
        held = ""
    except IllegalTransition as exc:
        after, held = before, str(exc)
    store.transition(before.value, after.value, gate=6, result=result.value,
                     detail=f"C_repro={status.value} from {reproduction_dir.name}; decision {cgd_ref['artifactId']} "
                            f"allowed {allowed}" + (f"; held: {held}" if held else ""))
    store.write_json("attempt_state.json", {"state": after.value, "at": utc_now()}, role="STATE")
    summary = load_json(attempt_dir / "RUN_SUMMARY.json")
    summary.update({"g6": {"cRepro": status.value, "reproductionAttempt": reproduction_dir.name,
                           "report": report["metrics"], "independentEnvironments": report["independentEnvironments"],
                           "heldReason": held or None},
                    "finalState": after.value, "trustVectorFinal": {d: dims[d]["status"] for d in dims},
                    "allowedClaimsFinal": allowed, "decisionRefFinal": cgd_ref})
    store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    log(f"Gate 6 {result.value}: state {after.value}; allowed claims {allowed}" + (f" (held: {held})" if held else ""))
    return summary
