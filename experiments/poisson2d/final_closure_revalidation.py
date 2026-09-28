"""Re-validate the whole 2D evidence chain without retraining (Final Closure Audit issue 6).

Every document is handed back to its own validator; the ledger, the claim-set
lifecycle, the reproduction verdict and the claim decision are recomputed from the
stored records.  Nothing is trained, nothing is opened, nothing is rewritten.

Writes experiments/poisson2d/FINAL_CLOSURE_REVALIDATION.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from pinn.experiments.common import code_hash_from_manifest, code_manifest, load_json, sha256_file, utc_now
from pinn.experiments2d.runner2d import derived_claim_status, judge_reproduction
from pinn.governance.claim_set_ledger import validate_claim_set_ledger
from pinn.governance.trust_loop import (
    problem_definition_spec_hash,
    validate_claim_gate_decision,
    validate_problem_definition,
    validate_run_record,
    validate_trust_vector,
)

ROOT = Path(".")
ATTEMPT = ROOT / "experiments/poisson2d/runs/exp2d-poisson-calibration-r1"
REPRO = ROOT / "experiments/poisson2d/runs/repro-envb2d-r1"
LEDGER = ROOT / "experiments/poisson2d/ledger/pdef-poisson2d-cal-v1.json"
REGISTRY = ROOT / "experiments/poisson2d/ledger/sample_set_registry.json"
OUT = ROOT / "experiments/poisson2d/FINAL_CLOSURE_REVALIDATION.json"


def main() -> int:
    checks: dict[str, object] = {}
    pdef = load_json(ATTEMPT / "problem_definition.json")
    events = load_json(LEDGER)
    registry = load_json(REGISTRY)
    sets = {role: load_json(ATTEMPT / f"sets/{role}.json") for role in ("train", "dev", "phys", "claim")}

    checks["specHashRecomputes"] = problem_definition_spec_hash(pdef) == pdef["specHash"]
    checks["problemDefinitionErrors"] = validate_problem_definition(
        pdef, claim_set_events=events, evaluation_sets=sets, sample_set_hashes=registry)
    checks["ledgerErrors"] = validate_claim_set_ledger(events, sample_set_hashes=registry)

    opened = [e for e in events if e["event"] == "OPENED"]
    checks["claimSetsOpened"] = len(opened)
    checks["claimSetOpenedOnce"] = len(opened) == 1
    member_status, _ = derived_claim_status(events, problem_id=pdef["problemId"], revision=pdef["revision"],
                                            artifact_hash=opened[0]["claimSetSha256"],
                                            sample_hash=opened[0]["sampleSetHash"])
    checks["consumedMemberLedgerStatus"] = member_status

    run_record = load_json(ATTEMPT / "run_record.json")
    repro_record = load_json(REPRO / "run_record.json")
    checks["runRecordErrors"] = validate_run_record(run_record)
    checks["reproRunRecordErrors"] = validate_run_record(repro_record)

    vectors = {}
    for name in ("trust_vector.json", "trust_vector_tier1.json", "trust_vector_g6.json", "trust_vector_g6_p11.json"):
        path = ATTEMPT / name
        if path.exists():
            vectors[name] = validate_trust_vector(load_json(path), pdef)
    checks["trustVectorErrors"] = vectors

    decisions = {}
    for name in ("claim_gate_decision.json", "claim_gate_decision_tier1.json", "claim_gate_decision_g6.json",
                 "claim_gate_decision_g6_p11.json"):
        path = ATTEMPT / name
        if not path.exists():
            continue
        decision = load_json(path)
        vector_name = {"claim_gate_decision.json": "trust_vector.json",
                       "claim_gate_decision_tier1.json": "trust_vector_tier1.json",
                       "claim_gate_decision_g6.json": "trust_vector_g6.json",
                       "claim_gate_decision_g6_p11.json": "trust_vector_g6_p11.json"}[name]
        decisions[name] = validate_claim_gate_decision(decision, load_json(ATTEMPT / vector_name), pdef,
                                                       claim_set_events=events,
                                                       run_records={run_record["runId"]: run_record})
    checks["claimGateDecisionErrors"] = decisions

    final_vector = load_json(ATTEMPT / "trust_vector_g6_p11.json")
    final_decision = load_json(ATTEMPT / "claim_gate_decision_g6_p11.json")
    checks["finalTrustVector"] = {d: entry["status"] for d, entry in final_vector["dimensions"].items()}
    checks["finalAllowedClaims"] = [c["level"] for c in final_decision["allowedClaims"]]
    checks["finalBlockedClaims"] = [c["level"] for c in final_decision["blockedClaims"]]
    checks["state"] = load_json(ATTEMPT / "attempt_state.json")["state"]

    repro_report = judge_reproduction(ATTEMPT, REPRO, write=False)
    checks["reproductionRecomputed"] = {"cRepro": repro_report["cRepro"], "sameSpec": repro_report["sameSpec"],
                                        "sameCode": repro_report["sameCode"],
                                        "independent": repro_report["independentEnvironments"],
                                        "differentSeeds": repro_report["differentSeedSet"],
                                        "withinTolerance": repro_report["withinTolerance"],
                                        "medianAbsDiff": repro_report["metrics"]["medianAbsDiff"]}

    identity = load_json(ATTEMPT / "identity.json")
    current = code_hash_from_manifest(code_manifest(Path(".").resolve(), [identity["configPath"]]))
    checks["codeIdentity"] = {
        "recordedCodeHash": identity["codeHash"],
        "currentTreeCodeHash": current,
        "unchanged": current == identity["codeHash"],
        "note": ("The closure audit fixed the claim-pool guard and added the localized-error module, so the working "
                 "tree's code identity has moved on. The ACCEPTED decision is bound to the recorded codeHash, whose "
                 "exact bytes are recoverable from the commit that carried the run; Constitution chapter 66 therefore "
                 "requires the NEXT formal run to bump the revision. The 1D round set the same precedent when its "
                 "runner gained subcommands after the accepted run."),
    }
    evidence_unchanged = {}
    for name in ("gate5b_external.json", "gate4_training.json", "gate5a_physics.json", "run_record.json",
                 "trust_vector_g6.json", "claim_gate_decision_g6.json", "tier1_redteam.json"):
        evidence_unchanged[name] = sha256_file(ATTEMPT / name)
    checks["evidenceHashes"] = evidence_unchanged

    problems = []
    if not checks["specHashRecomputes"]:
        problems.append("specHash does not recompute")
    for key in ("problemDefinitionErrors", "ledgerErrors", "runRecordErrors", "reproRunRecordErrors"):
        if checks[key]:
            problems.append(f"{key}: {checks[key]}")
    for group in ("trustVectorErrors", "claimGateDecisionErrors"):
        for name, errors in checks[group].items():
            if errors:
                problems.append(f"{group}.{name}: {errors}")
    if not checks["claimSetOpenedOnce"]:
        problems.append("the claim set was opened more than once")
    if checks["consumedMemberLedgerStatus"] not in ("OPENED", "BURNT"):
        problems.append("the consumed claim set is not marked opened in the ledger")
    if checks["reproductionRecomputed"]["cRepro"] != "PASS":
        problems.append("the reproduction no longer judges PASS")
    if any(status != "PASS" for status in checks["finalTrustVector"].values()):
        problems.append(f"trust vector is not six-dimension PASS: {checks['finalTrustVector']}")
    if checks["finalAllowedClaims"] != ["C0", "C1", "C2"]:
        problems.append(f"allowed claims changed: {checks['finalAllowedClaims']}")
    if checks["state"] != "ACCEPTED":
        problems.append(f"state is {checks['state']}")

    document = {"purpose": "Final Closure Audit issue 6: re-validate the evidence chain without retraining",
                "revalidatedAt": utc_now(), "retrained": False, "claimSetReopened": False,
                "checks": checks, "problems": problems,
                "verdict": "CURRENT 2D C2: CONFIRMED" if not problems else "CURRENT 2D C2: SUSPENDED"}
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"verdict": document["verdict"], "problems": problems,
                      "finalTrustVector": checks["finalTrustVector"], "allowed": checks["finalAllowedClaims"],
                      "state": checks["state"], "cRepro": checks["reproductionRecomputed"]["cRepro"],
                      "codeIdentityUnchanged": checks["codeIdentity"]["unchanged"]}, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
