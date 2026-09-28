"""Check the calibrated localized-error rule against the completed 2D run (Final Closure Audit issue 5).

This is a CHECK, never part of the calibration: the threshold was fixed by the
synthetic fixtures before this script ran.  It recomputes the per-seed block
statistics from the STORED predictions on D_dev (no retraining, no claim data) and
appends the result to LOCALIZED_ERROR_CALIBRATION.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from pinn.experiments.common import load_json, utc_now
from pinn.experiments2d import datasets2d as ds
from pinn.experiments2d import localized_error as le
from pinn.experiments2d import pinn_torch2d as pinn2d
from pinn.reference import analytic_poisson2d as reference

ATTEMPT = Path("experiments/poisson2d/runs/exp2d-poisson-calibration-r1")
RECORD = Path("experiments/poisson2d/LOCALIZED_ERROR_CALIBRATION.json")
BLOCKS = 8


def main() -> int:
    document = load_json(RECORD)
    chosen = document["chosen"]["candidate"]
    threshold = document["chosen"]["threshold"]
    identity = load_json(ATTEMPT / "identity.json")
    config = load_json(Path(identity["configPath"]))
    threads = int(config["optimizer"].get("threads", 1))
    dev = ds.points_of(load_json(ATTEMPT / "sets/dev.json"))
    exact = [reference.solution(x, y) for x, y in dev]

    per_seed = []
    for path in sorted(ATTEMPT.glob("runs/run-*.json")):
        run = load_json(path)
        model = pinn2d.model_from_weights(config, run["weights"], threads=threads)
        values = pinn2d.values(model, dev, threads=threads)
        errors = [a - b for a, b in zip(values, exact)]
        stats = le.block_statistics(dev, errors, exact, BLOCKS)
        per_seed.append({"run": path.name,
                         **{name: function(stats) for name, function in le.CANDIDATES.items()},
                         "firesUnderChosenRule": le.signature_fired(stats, candidate=chosen, threshold=threshold),
                         "firesUnderOld1DRule": le.candidate_a_max_over_median(stats) > 3.0})
    document["completedRunCheck"] = {
        "note": "check only -- the threshold was fixed by the synthetic fixtures before this ran; the completed run's "
                "values never entered the calibration",
        "set": "dev", "blocksPerAxis": BLOCKS, "seeds": len(per_seed),
        "chosenCandidate": chosen, "threshold": threshold,
        "chosenStatisticRange": [min(s[chosen] for s in per_seed), max(s[chosen] for s in per_seed)],
        "oldRuleStatisticRange": [min(s["A-maxOverMedian"] for s in per_seed),
                                  max(s["A-maxOverMedian"] for s in per_seed)],
        "anySeedFiresUnderChosenRule": any(s["firesUnderChosenRule"] for s in per_seed),
        "seedsFiringUnderOld1DRule": sum(1 for s in per_seed if s["firesUnderOld1DRule"]),
        "perSeed": per_seed,
        "checkedAt": utc_now(),
    }
    fires = sum(1 for s in per_seed if s["firesUnderChosenRule"])
    old_fires = document["completedRunCheck"]["seedsFiringUnderOld1DRule"]
    document["deploymentVerdict"] = {
        "deployable": fires == 0,
        "falsePositiveSeedsChosenRule": fires, "falsePositiveSeedsOld1DRule": old_fires, "seeds": len(per_seed),
        "decision": ("NOT CALIBRATED FOR DEPLOYMENT" if fires else "CALIBRATED"),
        "reasoning": (
            "The completed 2D run is a fully validated solution (every acceptance criterion satisfied by every seed, "
            "Tier-1 maintained, Gate 6 reproduced), so any localized-error signature that fires on it is a false "
            f"positive. The inherited 1D rule fires on {old_fires}/{len(per_seed)} seeds and must not be carried into "
            f"2D. The best calibrated candidate still fires on {fires}/{len(per_seed)} seeds. The threshold is NOT "
            "raised to silence them: fitting a threshold to the observed run is exactly the post-hoc tuning this "
            "audit forbids. What the synthetic null family cannot reproduce is the block-to-block tail of a real "
            "trained error field; a trustworthy threshold needs an EMPIRICAL null distribution built from several "
            "validated runs (the full sense of candidate D, a dimension-conditioned reference distribution), and only "
            "one validated 2D run exists."),
        "prospectiveProtocol": [
            "for d >= 2 the localized-error REQUIREMENT is carried by an acceptance criterion of the AC2D-9 form (a "
            "fixed relative bound per block), which is what the 2D calibration used and which behaved correctly "
            "(worst seed 1.568e-4 against a 1e-3 threshold)",
            "the SYMPTOM signature sLocalizedError is registered NOT CALIBRATED for d >= 2: until an empirical null "
            "distribution exists it must not be used to name a root cause",
            "the inherited 1D constant 3.0 on a max/median statistic is retired for d >= 2 (machine-verified false "
            "positives on a validated run)",
            "a future experiment that needs the symptom must first collect block statistics from >= 5 validated runs "
            "and preregister the resulting quantile as its threshold",
        ],
    }
    RECORD.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    check = document["completedRunCheck"]
    print(f"chosen rule {chosen} > {threshold:.3f}: range {check['chosenStatisticRange'][0]:.3f} - "
          f"{check['chosenStatisticRange'][1]:.3f}; fires on any seed: {check['anySeedFiresUnderChosenRule']}")
    print(f"old 1D rule (max/median > 3.0): range {check['oldRuleStatisticRange'][0]:.3f} - "
          f"{check['oldRuleStatisticRange'][1]:.3f}; would fire on {check['seedsFiringUnderOld1DRule']}/{len(per_seed)} seeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
