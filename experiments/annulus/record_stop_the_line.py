"""File the annulus r1 attempt's rUndetermined DiagnosisRecord and stop the line.

Owner's decision of 2026-09-26: the root cause of the Gate 5b failure (seed 2's
ACA-9 = 1.038e-03 on D_dev, 1.079e-03 on the claim set, threshold 1e-3) stays
UNDETERMINED, so the attempt moves FAILURE_RECORDED -> STOPPED_THE_LINE and the
next step is a human ruling.  Constitution ch. 3.1 / 3.2 item 3 and ch. 58 (a
negative result is a legitimate endpoint).

What this script does, and nothing else:

* builds the DiagnosisRecord from the exclusion round's own artifacts, keeping
  the two causes that WERE excluded (rImplementationDefect, rSpecDefect) as
  exclusion records -- the validator does not require them for rUndetermined,
  but dropping them would lose what the round established;
* validates it with ``trust_loop.validate_diagnosis_record`` and lets
  ``state_machine.diagnose`` decide the state (it must answer STOPPED_THE_LINE);
* writes diagnosis_record.json / diagnosis_verdict.json through the attempt's
  ArtifactStore, appends the transition, and rewrites attempt_state.json *and*
  re-registers its hash (the 1D ``finish_diagnosis`` rewrote the file without
  re-registering it, leaving a stale manifest hash).

It trains nothing, opens no claim set, and refuses to run twice.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pinn.experiments.common import ArtifactStore, load_json, sha256_file, utc_now  # noqa: E402
from pinn.governance.state_machine import (  # noqa: E402
    FailureSignature, RootCauseClass, WorkflowState, admissible_root_causes, diagnose,
)
from pinn.governance.trust_loop import diagnosis_coverage_errors, validate_diagnosis_record  # noqa: E402

ATTEMPT = ROOT / "experiments/annulus/runs/exp-geometry1-annulus-poisson-r1-gpu"
EXCLUSIONS = ROOT / "experiments/annulus/diagnosis/exclusions"
NESTED = ROOT / "experiments/annulus/diagnosis/nested-budget-r1-paired/DIAGNOSIS.json"
REPORT = ROOT / "docs/pinn-trust-loop/ANNULUS_EXCLUSION_DIAGNOSIS_REPORT_20260920.md"
CONSTITUTION_VERSION = "1.2"
DECIDED_BY = "Claude (captain), on the owner's decision of 2026-09-26"


def repo_ref(path: Path) -> dict[str, str]:
    """Evidence outside the attempt folder is named by its repository path."""
    return {"artifactId": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def main() -> int:
    state = load_json(ATTEMPT / "attempt_state.json")["state"]
    if state != WorkflowState.FAILURE_RECORDED.value or (ATTEMPT / "diagnosis_record.json").exists():
        raise SystemExit(f"refusing: attempt is {state!r}; a diagnosis may only be filed once, from FAILURE_RECORDED")
    failure = load_json(ATTEMPT / "failure_record.json")
    pdef = load_json(ATTEMPT / "problem_definition.json")
    summary = load_json(EXCLUSIONS / "EXCLUSIONS.json")
    if failure["observedSignatures"] != ["sLocalizedError"] or failure["constitutionVersion"] != CONSTITUTION_VERSION:
        raise SystemExit("failure record does not match the premise of this script")
    for cause in ("rImplementationDefect", "rSpecDefect"):
        if summary["exclusions"][cause]["excluded"] is not True:
            raise SystemExit(f"{cause} is no longer recorded as excluded")
        if sha256_file(EXCLUSIONS / summary["exclusions"][cause]["artifact"]) != summary["exclusions"][cause]["sha256"]:
            raise SystemExit(f"{cause}: exclusion artifact changed since the round finished")

    store = ArtifactStore(ATTEMPT)
    sampling = repo_ref(EXCLUSIONS / "exp-annulus-dx-sampling.json")
    signature_evidence = {"errorSpatialDistribution": store.ref("dev_diagnostics.json"), "samplingConfigDiff": sampling}
    excludes = {
        "rImplementationDefect": {"experiment": "exp-annulus-dx-implementation", "observed": (
            "positive-controlled: the exact solution through the production pipeline gives relL2 6.055e-18 and ACA-9 "
            "4.437e-17; a bump injected into cell 2,5 is reported at 2,5; an independently written routine reproduces the "
            "statistic with relative difference 0.000e+00; autodiff vs finite differences worst 2.225e-08")},
        "rSpecDefect": {"experiment": "exp-annulus-dx-spec", "observed": (
            "positive-controlled: -Lap u* - f is 0.000e+00 analytically and 3.553e-15 by autodiff; both boundary components "
            "vanish (outer 2.115e-16, inner 2.952e-17); an injected defect raises the residual to 1.752e-05 and is detected")},
    }
    pointers = [store.ref("failure_record.json"), repo_ref(EXCLUSIONS / "EXCLUSIONS.json")]
    pointers += [repo_ref(EXCLUSIONS / f"exp-annulus-dx-{name}.json")
                 for name in ("implementation", "spec", "sampling", "reference", "singularity")]
    pointers += [repo_ref(NESTED), repo_ref(REPORT)]
    record = {
        "schemaVersion": "pinn.diagnosisRecord/1.0",
        "diagnosisId": f"dg-{ATTEMPT.name}-r1",
        "problemId": pdef["problemId"],
        "revision": pdef["revision"],
        "specHash": pdef["specHash"],
        "constitutionVersion": CONSTITUTION_VERSION,
        "problemClass": "forward",
        "signature": "sLocalizedError",
        "observedSignatures": ["sLocalizedError"],
        "explainedSignatures": ["sLocalizedError"],
        "signatureEvidence": signature_evidence,
        "rootCause": RootCauseClass.UNDETERMINED.value,
        "discriminatingExperiment": {
            # The experiment whose result made the candidates inseparable: more density and a reshuffled draw both
            # cure the failing seed, so sampling and optimization overlap by definition (ruling 1, 2026-09-21).
            "experimentId": "exp-annulus-dx-sampling",
            "evaluationSet": "dev",
            "excludes": excludes,
            "evidencePointers": pointers,
        },
        "round": 1,
        "decidedBy": DECIDED_BY,
        "decidedAt": utc_now(),
    }
    errors = validate_diagnosis_record(record, constitution_version=CONSTITUTION_VERSION)
    coverage = diagnosis_coverage_errors([record]) if not errors else []
    if errors or coverage:
        raise SystemExit(f"record invalid: {errors + coverage}")
    evidence = {key: ref["artifactId"] for key, ref in signature_evidence.items()}
    evidence["discriminatingExperiment"] = record["discriminatingExperiment"]
    new_state, route = diagnose(WorkflowState.FAILURE_RECORDED, FailureSignature.LOCALIZED_ERROR,
                                RootCauseClass.UNDETERMINED, evidence, constitution_version=CONSTITUTION_VERSION)
    if new_state is not WorkflowState.STOPPED_THE_LINE or route is not None:
        raise SystemExit(f"state machine answered {new_state}, expected STOPPED_THE_LINE")

    candidates = [cause.value for cause in admissible_root_causes(CONSTITUTION_VERSION)[FailureSignature.LOCALIZED_ERROR]]
    still_open = [c for c in candidates if c not in excludes]
    store.write_canonical("diagnosis_record.json", record, role="DIAGNOSIS_RECORD",
                          parents=["failure_record.json", "dev_diagnostics.json"])
    store.write_json("diagnosis_verdict.json", {
        "attempted": "rUndetermined",
        "recordErrors": [], "coverageErrors": [],
        "rootCause": "rUndetermined",
        "state": new_state.value,
        "route": None,
        "admissibleCandidates": candidates,
        "excluded": sorted(excludes),
        "notExcluded": still_open,
        "notExcludedNotes": {
            "rOptimizationFailure": "supported by B* = 180k in the nested budget intervention, but the exclusion round showed that more collocation points and a reshuffled draw also cure the failing seed, so the budget result is not a necessary explanation",
            "rSamplingDeficiency": "interventional evidence points towards it (2x density ACA-9 6.62e-04, 2.76x 5.77e-04, both PASS) yet the operative variable was the draw, not the density; not separable from optimization this round",
            "rReferenceDefect": "R1 and R2 hold but the reference's own error in the hotspot cell is only 2.7x below the model's where 10x was preregistered; the corrupted-operator control never executed",
            "rSingularityTreatment": "G1 and G3 hold, G2 found one boundary-adjacent worst cell; G3 ran as observational, not positive-controlled",
            "rCapacityLimit": "never excluded: the budget intervention held 4x64 fixed and varied only steps; FACTOR_CONTROL requires an architecture intervention",
        },
        "ownerDecision": {
            "date": "2026-09-26",
            "choice": "write rUndetermined and stop the line",
            "next": "a human ruling; whether a revision 2 follows is the owner's later call",
        },
        "unconfirmedRecords": [
            "STATUS.json on branch claude/leo-ai-workbench-plan-6f38e9 attributes to 2026-09-20 an owner ruling 'diagnosisOnlyTier1: AUTHORIZED, revision2Budget: 240000'; the science records still list the budget as open, and the owner did not confirm it when asked on 2026-09-26. Nothing here relies on it.",
        ],
        "claimSets": {"DAC-M0": "BURNT (unchanged)", "DAC-M1": "NEVER_SEALED", "DAC-M2": "NEVER_SEALED", "DAC-M3": "NEVER_SEALED"},
    }, role="DIAGNOSIS_VERDICT")
    store.transition(WorkflowState.FAILURE_RECORDED.value, new_state.value, gate=None, result="STOP:rUndetermined",
                     detail=f"observed=['sLocalizedError']; excluded={sorted(excludes)}; notExcluded={still_open}; owner decision 2026-09-26")
    state_path = ATTEMPT / "attempt_state.json"
    state_path.write_text(json.dumps({"at": utc_now(), "state": new_state.value}, indent=2) + "\n", encoding="utf-8", newline="\n")
    store.register("attempt_state.json", sha256_file(state_path), role="STATE", parents=["diagnosis_record.json"],
                   note="FAILURE_RECORDED -> STOPPED_THE_LINE (rUndetermined)")
    print(json.dumps({"state": new_state.value, "diagnosisId": record["diagnosisId"], "notExcluded": still_open}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
