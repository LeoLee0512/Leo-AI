"""Record the owner's ruling that revision 2 yields no claim (2026-09-26, option B).

``exp-geometry1-annulus-poisson-r2`` passed Gates 1-5 (Gate 4 10/10, median dev rel-L2
1.406e-4; C_physics and C_external PASS on DAC-M1, which is BURNT) and then:

* ``finish()`` crashed building the ClaimGateDecision (``claim_gate`` called with
  keywords it never had, its result read as a dict), so no decision and no summary exist;
* completing the record showed the trust vector itself is invalid: the frozen spec
  registers PH10-momentumBudget and PH11-freeEnergy (both NOT_APPLICABLE, with reasons)
  and Gate 5a never recorded them -- "a registered check cannot be silently omitted".

Offered (A) a superseding record that adds the two registrations verbatim, (B) void r2
and repeat the method as revision 3 on DAC-M2 after fixing the code, (C) wait, the owner
chose B. This script writes that ruling into the attempt and nothing else: no measured
artifact is edited, the state file is left where the run put it (REPRODUCIBILITY_CHECK --
there is no workflow state for "voided by ruling", and inventing one would be an
amendment), and no ClaimGateDecision, Tier-1 or G6 will ever be written for r2.
It refuses to run twice.

    PYTHONPATH=. python experiments/annulus/record_r2_void.py
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pinn.experiments.common import ArtifactStore, load_json, utc_now

ATTEMPT = Path("experiments/annulus/runs/exp-geometry1-annulus-poisson-r2")
REPRO = Path("experiments/annulus/runs/exp-geometry1-annulus-poisson-r2-repro-envB")
EXECUTOR = "experiments/annulus/record_r2_void.py (Claude, captain)"


def main() -> int:
    if (ATTEMPT / "owner_ruling_void.json").exists():
        raise SystemExit("the ruling is already recorded")
    if (ATTEMPT / "claim_gate_decision.json").exists():
        raise SystemExit("r2 has a decision; this record assumes it has none")
    me = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    state = load_json(ATTEMPT / "attempt_state.json")["state"]
    record = {
        "attemptId": ATTEMPT.name, "ruling": "VOID_NO_CLAIM", "option": "B", "ruledBy": "owner",
        "ruledAt": "2026-09-26", "recordedAt": utc_now(), "recordedBy": EXECUTOR, "scriptSha256": me,
        "stateLeftAt": state,
        "measured": {"gate4": "PASS 10/10, median dev rel-L2 1.406e-4", "gate5": "C_physics PASS, C_external PASS",
                     "claimMember": "DAC-M1", "claimMemberStatus": "BURNT (OPENED at revision 2; never reusable)"},
        "whyVoid": [
            "AttemptAnnulus.finish() raised TypeError in claim_gate(): no ClaimGateDecision and no RUN_SUMMARY exist",
            "trust_vector.json omits the registered NOT_APPLICABLE checks PH10-momentumBudget and PH11-freeEnergy "
            "(and is in the pre-1.2 layout); by the constitution a registered check cannot be silently omitted",
        ],
        "consequences": [
            "no ClaimGateDecision, Tier-1 or G6 is ever written for this attempt; it licenses no claim level",
            "the measured artifacts stay exactly as written; nothing is re-labelled",
            "the method is repeated unchanged as revision 3 on DAC-M2 after the code is fixed "
            "(EXPERIMENT_ANNULUS_R3_PREREGISTRATION_20260926.md)",
            "the r2 numbers are NOT evidence for r3 and must not be pooled with it",
        ],
        "leftovers": {
            "claim_statements.json": "written by complete_r2_finish_after_crash.py before it validated (an "
                                     "ordering defect of that script) and kept as is; it asserts nothing",
            "reproduction": f"{REPRO.name}: Env B reproduction started 18:46Z, stopped by Claude after the "
                            "ruling (no longer needed); partial, never judged, kept as is",
        },
    }
    store = ArtifactStore(ATTEMPT, producer=EXECUTOR)
    ref = store.write_json("owner_ruling_void.json", record, role="OWNER_RULING")
    store.transition(state, state, gate=None, result="OWNER_RULING:VOID_NO_CLAIM",
                     detail=f"option B; no decision, Tier-1 or G6 for r2; record {ref['sha256'][:12]}")
    if REPRO.is_dir():
        ArtifactStore(REPRO, producer=EXECUTOR).write_json("INTERRUPTED.json", {
            "interruptedAt": "2026-09-26 (after the owner's ruling on r2)", "by": EXECUTOR,
            "reason": "r2 was ruled void (no claim), so its G6 reproduction serves no purpose; stopped mid-training",
            "judged": False}, role="INTERRUPTION_NOTE")
    print(f"recorded {ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
