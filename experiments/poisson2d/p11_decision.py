"""Sign the ClaimGateDecision for the P11-supplemented TrustVector (Final Closure Audit issue 2).

Reads the stored records only; no training, no claim set access.  Kept outside the
code identity manifest for the same reason as p11_supplement.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from pinn.experiments.common import load_json
from pinn.experiments2d import runner2d
from pinn.governance.trust_vector import DIMENSIONS

ATTEMPT = Path("experiments/poisson2d/runs/exp2d-poisson-calibration-r1")


def main() -> int:
    attempt = runner2d.resume_attempt(ATTEMPT)
    vector = load_json(ATTEMPT / "trust_vector_g6_p11.json")
    attempt.dimensions = vector["dimensions"]
    tv_ref = attempt.store.ref("trust_vector_g6_p11.json")
    decision = attempt.decision_document(vector, tv_ref, suffix="_g6_p11")
    ref = attempt.store.write_canonical("claim_gate_decision_g6_p11.json", decision, role="CLAIM_GATE_DECISION",
                                        parents=[tv_ref["artifactId"]])
    summary = load_json(ATTEMPT / "RUN_SUMMARY.json")
    p11 = load_json(ATTEMPT / "tier1_p11_supplement.json")
    summary.setdefault("redTeam", {})["tier1_p11_supplement"] = {
        "status": p11["status"], "deltaQ": p11["deltaQ"], "e2Baseline": p11["baseline"]["e2"],
        "e2Perturbed": p11["perturbed"]["e2"], "regionTiles": p11["region"]["tileCount"],
        "densifiedShare": p11["region"]["densifiedShare"],
        "reason": p11["reasonForSupplement"],
    }
    summary["trustVectorFinal"] = {d: vector["dimensions"][d]["status"] for d in DIMENSIONS}
    summary["allowedClaimsFinal"] = attempt.summary["allowedClaims"]
    summary["highestAllowedClaimFinal"] = attempt.summary["highestAllowedClaim"]
    summary["decisionRefFinal"] = ref
    attempt.store.write_json("RUN_SUMMARY.json", summary, role="SUMMARY")
    attempt.store.transition(attempt.state.value, attempt.state.value, gate=None, result="TIER1_SUPPLEMENT:P11",
                             detail=f"supplemental P11 {p11['status']} (delta_q {p11['deltaQ']:.3e}); "
                                    f"TrustVector {vector['recordId']} supersedes {vector['supersedesRecordId']}; "
                                    f"decision {ref['artifactId']}")
    from pinn.experiments2d import report2d

    report2d.write_trust_report(ATTEMPT, attempt.root)
    print(json.dumps({"state": attempt.state.value, "vector": summary["trustVectorFinal"],
                      "allowed": attempt.summary["allowedClaims"],
                      "highest": attempt.summary["highestAllowedClaim"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
