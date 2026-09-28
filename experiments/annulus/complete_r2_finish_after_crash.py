"""Complete the bookkeeping of the r2 attempt after its finish() crashed (2026-09-26).

WHAT HAPPENED. ``exp-geometry1-annulus-poisson-r2`` passed Gate 4 (10/10, median dev
rel-L2 1.406e-4) and Gate 5 (C_physics PASS, C_external PASS on DAC-M1, now BURNT) and
moved to REPRODUCIBILITY_CHECK. ``AttemptAnnulus.finish()`` then wrote trust_vector.json
and crashed building the ClaimGateDecision: it called ``claim_gate(..., environment_id=,
qualified_c2_runs=)`` -- keywords that function never had -- and treated its ClaimGate
result as a dict. The path had never executed (r1 stopped at Gate 4). Nothing measured
was lost; claim_gate_decision.json and RUN_SUMMARY.json were never written.

WHY THIS SCRIPT AND NOT A FIX IN pinn/ FIRST. The G6 reproduction and the Tier-1 Red Team
must run under the attempt's own codeHash (b9f9e6def344...). Editing pinn/ before they
start would move it. This file lives outside the code-identity boundary, changes no
verdict, and computes the decision with the UNCHANGED governance function ``claim_gate``,
in the validated schema-1.2 form the square experiment uses (runner2d.decision_document).
Every artifact it writes says so (``completedAfterCrash``), with this file's sha256.

    PYTHONPATH=. python experiments/annulus/complete_r2_finish_after_crash.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pinn.experiments.common import ArtifactStore, load_json, utc_now
from pinn.governance.trust_loop import trust_vector_statuses, validate_claim_gate_decision
from pinn.governance.trust_vector import CLAIM_LEVELS, claim_gate

ATTEMPT = Path("experiments/annulus/runs/exp-geometry1-annulus-poisson-r2")
LEDGER = Path("experiments/annulus/ledger/pdef-annulus-poisson-v1.json")
EXECUTOR = "experiments/annulus/complete_r2_finish_after_crash.py (Claude, captain)"

STATEMENTS = {
    "C0": "The frozen annular Poisson problem definition is mathematically consistent and the implementation computes "
          "this problem (math, impl PASS; hard two-component boundary enforcement and polar derivatives verified).",
    "C1": "Under the frozen revision-2 training protocol (240k steps, LR prefix 120k) the annulus PINN training is reliable "
          "across the preregistered seed set (train PASS); accuracy is not asserted.",
    "C2": "Every seed model agrees with the analytic reference within the preregistered ACA-1..ACA-9 on the opened blind "
          "claim set DAC-M1 and satisfies the annulus physics checks; Tier-1 Red Team maintained; independent "
          "reproduction confirmed.",
    "C3": "The C2 result holds across >= 5 independently qualified runs of the same method identity.",
}


def layout_1_2_view(vector_doc: dict) -> dict:
    """The on-disk vector in the schema-1.2 layout, for VALIDATION ONLY (never written).

    ``AttemptAnnulus.trust_vector_document`` still emits the pre-1.2 layout (top-level
    runRef/codeHash/environmentId/generatedAt/generatedBy; per-dimension ``evidenceRefs``).
    The validator stops at those schema errors and would then skip every substantive
    check, so the decision is validated against this view instead: same record id, same
    statuses, same checks; only field names and placement differ. The measured file is
    left exactly as the run wrote it; the layout gap is recorded as a finding.
    """
    dimensions = {}
    for name, entry in vector_doc["dimensions"].items():
        view = {key: value for key, value in entry.items() if key != "evidenceRefs"}
        if entry["status"] != "NOT_CHECKED":
            view.update({"evidencePointers": entry.get("evidenceRefs", []), "judgedAt": vector_doc["generatedAt"],
                         "judgedBy": vector_doc["generatedBy"]})
        dimensions[name] = view
    return {"schemaVersion": "pinn.trustVector/1.2", "recordId": vector_doc["recordId"],
            "problemId": vector_doc["problemId"], "revision": vector_doc["revision"],
            "specHash": vector_doc["specHash"], "dimensions": dimensions}


def main() -> int:
    if (ATTEMPT / "claim_gate_decision.json").exists() or (ATTEMPT / "RUN_SUMMARY.json").exists():
        raise SystemExit("the attempt already has a decision or a summary; nothing to complete")
    state = load_json(ATTEMPT / "attempt_state.json")["state"]
    if state != "REPRODUCIBILITY_CHECK":
        raise SystemExit(f"expected REPRODUCIBILITY_CHECK after the Gate 5 PASS, found {state}")
    me = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    completion = {"reason": "AttemptAnnulus.finish() raised TypeError in claim_gate(); see this file's docstring",
                  "by": EXECUTOR, "scriptSha256": me, "at": utc_now()}

    store = ArtifactStore(ATTEMPT, producer=EXECUTOR)
    identity = load_json(ATTEMPT / "identity.json")
    pdef = load_json(ATTEMPT / "problem_definition.json")
    record = load_json(ATTEMPT / "run_record.json")
    vector_doc = load_json(ATTEMPT / "trust_vector.json")
    events = load_json(LEDGER)
    tv_ref = store.ref("trust_vector.json")

    gate = claim_gate(trust_vector_statuses(vector_doc), evidence_level="A", spec_hash=pdef["specHash"],
                      code_hash=identity["codeHash"], exploratory=False, stop_the_line=False)
    statement_ref = store.write_json("claim_statements.json", STATEMENTS, role="CLAIM_STATEMENT")
    evidence_refs = [dict(tv_ref)] + [store.ref(p) for p in ("gate4_training.json", "gate5b_external.json")]
    decision = {
        "schemaVersion": "pinn.claimGateDecision/1.2", "decisionId": "cgd-exp-geometry1-annulus-poisson-r2",
        "problemId": pdef["problemId"], "revision": pdef["revision"], "specHash": pdef["specHash"],
        "codeHash": identity["codeHash"], "claimSetSha256": pdef["evaluationSets"]["claim"]["sha256"],
        "ledgerHead": events[-1]["eventId"],
        "trustVectorRef": {"artifactId": vector_doc["recordId"], "sha256": tv_ref["sha256"]},
        "referenceEvidenceLevel": "A", "runMode": "FORMAL", "qualifiedC2Runs": [],
        "allowedClaims": [{"level": level, "statementRef": statement_ref, "evidenceRefs": evidence_refs,
                           "failureConditions": [
                               {"condition": "the frozen ProblemDefinition, reference or code identity is revised",
                                "consequence": "INVALIDATE_DECISION"},
                               {"condition": "a later independent reproduction falls outside the preregistered tolerance",
                                "consequence": "DOWNGRADE"}]}
                          for level in gate.allowed],
        "blockedClaims": [{"level": level, "reason": "; ".join(gate.blocked.get(level, ("not licensed",))),
                           "missingPreconditions": list(gate.blocked.get(level, ()))}
                          for level in CLAIM_LEVELS if level not in gate.allowed],
        "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value,
                        "evidenceRef": dict(tv_ref)},
        "generatedAt": utc_now(), "decidedBy": EXECUTOR,
    }
    view = layout_1_2_view(vector_doc)
    layout_errors = validate_claim_gate_decision(decision, vector_doc, pdef, claim_set_events=events,
                                                 run_records={record["runId"]: record})
    if any(not error.startswith("trustVector: ") for error in layout_errors):
        raise SystemExit(f"ClaimGateDecision invalid: {layout_errors}")
    errors = validate_claim_gate_decision(decision, view, pdef, claim_set_events=events,
                                          run_records={record["runId"]: record})
    if errors:
        raise SystemExit(f"ClaimGateDecision invalid against the 1.2 view: {errors}")
    completion["validation"] = {
        "result": "valid against the schema-1.2 view of trust_vector.json (all substantive checks executed)",
        "onDiskVectorLayoutErrors": layout_errors,
        "finding": "AttemptAnnulus.trust_vector_document emits the pre-1.2 layout; fix after G6, prospectively"}
    decision_ref = store.write_canonical("claim_gate_decision.json", decision, role="CLAIM_GATE_DECISION",
                                         parents=[tv_ref["artifactId"]], note="completed after the finish() crash")

    training = load_json(ATTEMPT / "training_report.json")["seedStatistics"]
    external = load_json(ATTEMPT / "gate5b_external.json")
    sets = {role: load_json(ATTEMPT / f"sets/{role}.json") for role in ("train", "dev", "phys", "claim")}
    summary = {
        "attemptId": ATTEMPT.name, "problemId": pdef["problemId"], "revision": pdef["revision"],
        "reproductionOf": None, "seedOffset": identity["seedOffset"],
        "codeHash": identity["codeHash"], "environmentId": identity["environmentId"], "gitHead": identity["gitHead"],
        "workspaceDirty": bool(identity["dirtyCodeIdentityPaths"]), "trainingDevice": identity["executionDevice"]["training"],
        "prelock": load_json(ATTEMPT / "prelock.json")["prelockStatus"],
        "specHash": pdef["specHash"], "claimSetSha256": pdef["evaluationSets"]["claim"]["sha256"],
        "claimSampleSetHash": external["claimSampleSetHash"], "ledgerHead": events[-1]["eventId"],
        "claimPoolMember": "DAC-M1",
        "evaluationSets": {"sizes": {role: len(doc["samples"]) for role, doc in sets.items()}},
        "training": training,
        "claimEvaluation": {"perSeed": [seed["metrics"] for seed in external["perSeed"]],
                            "failedMust": [seed["failedMust"] for seed in external["perSeed"]],
                            "failedShould": [seed["failedShould"] for seed in external["perSeed"]]},
        "trustVector": {name: entry["status"] for name, entry in vector_doc["dimensions"].items()},
        "allowedClaims": list(gate.allowed), "blockedClaims": [lvl for lvl in CLAIM_LEVELS if lvl not in gate.allowed],
        "highestAllowedClaim": gate.highest_allowed or "BLOCKED",
        "weakestLink": {"dimensions": list(gate.weakest_dimensions), "status": gate.weakest_status.value},
        "decisionRef": decision_ref, "finalState": state,
        "completedAfterCrash": completion,
    }
    store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY", note="completed after the finish() crash")
    store.transition(state, state, gate=None, result="FINISH_COMPLETED_AFTER_CRASH",
                     detail=f"decision {decision_ref['sha256'][:12]} allowed {list(gate.allowed)}; by {EXECUTOR} "
                            f"(sha256 {me[:12]})")
    print(json.dumps({"allowed": list(gate.allowed), "blocked": summary["blockedClaims"],
                      "weakestLink": summary["weakestLink"], "decision": decision_ref}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
