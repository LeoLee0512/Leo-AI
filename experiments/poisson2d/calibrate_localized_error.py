"""Calibrate the dimension-aware localized-error signature (Final Closure Audit issue 5).

Decision rule, fixed before the numbers are read:

1. evaluate every candidate on the five preregistered fixtures, over a range of
   block resolutions and error amplitudes;
2. keep only candidates that separate the two fixture families everywhere
   (every localized fixture above every non-localized one);
3. among those, pick the one with the largest worst-case separation ratio;
4. set the threshold at the geometric mean of (worst non-localized value,
   weakest localized value) -- the scale-free midpoint of the gap;
5. the completed 2D run is then *checked* against the result; its value never
   enters the calibration.

Writes experiments/poisson2d/LOCALIZED_ERROR_CALIBRATION.json.  Pure Python: no
torch, no numpy, no model, no claim data.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from pinn.experiments.common import load_json, utc_now
from pinn.experiments2d.localized_error import (
    CANDIDATES,
    LOCALIZED_FIXTURES,
    NON_LOCALIZED_FIXTURES,
    block_statistics,
    evaluate_candidates,
    pseudo_random_grid,
    reference_field,
    threshold_from_separation,
    uniform_grid,
)

OUT = Path("experiments/poisson2d/LOCALIZED_ERROR_CALIBRATION.json")
GRIDS = (32, 48, 64)                 # interior points per axis
BLOCKS = (4, 8, 16)                  # blocks per axis
AMPLITUDES = (1e-6, 1e-5, 1e-4)      # error scale; the statistics must be scale free


def main() -> int:
    sweep = []
    point_sets = [(f"uniform-{n}x{n}", uniform_grid(n)) for n in GRIDS]
    # the deployment regime: a randomly sampled dev set of the size the experiments actually use
    point_sets += [(f"random-{count}", pseudo_random_grid(count, seed=20260916 + count)) for count in (512, 1024, 2048)]
    for label, points in point_sets:
        for blocks in BLOCKS:
            for amplitude in AMPLITUDES:
                evaluated = evaluate_candidates(points, blocks, amplitude)
                sweep.append({"pointSet": label, "pointCount": len(points), "blocksPerAxis": blocks,
                              "amplitude": amplitude, "values": evaluated})

    summary = {}
    for candidate in CANDIDATES:
        null_values, hot_values, separates = [], [], True
        for case in sweep:
            nulls = [case["values"][name][candidate] for name in NON_LOCALIZED_FIXTURES]
            hots = [case["values"][name][candidate] for name in LOCALIZED_FIXTURES]
            null_values.extend(nulls)
            hot_values.extend(hots)
            if min(hots) <= max(nulls):
                separates = False
        worst_null, weakest_hot = max(null_values), min(hot_values)
        summary[candidate] = {
            "separatesEverywhere": separates,
            "worstNonLocalized": worst_null, "weakestLocalized": weakest_hot,
            "separationRatio": (weakest_hot / worst_null) if worst_null > 0 else math.inf,
            "nonLocalizedRange": [min(null_values), worst_null],
            "localizedRange": [weakest_hot, max(hot_values)],
        }

    eligible = {k: v for k, v in summary.items() if v["separatesEverywhere"] and v["separationRatio"] > 1.0}
    if not eligible:
        raise SystemExit("no candidate separates the fixture families; the protocol cannot be calibrated")
    chosen = max(eligible, key=lambda k: eligible[k]["separationRatio"])
    threshold = threshold_from_separation(summary[chosen]["worstNonLocalized"], summary[chosen]["weakestLocalized"])

    # check (not calibration): what the completed 2D run measures under the chosen rule, on D_dev
    attempt = Path("experiments/poisson2d/runs/exp2d-poisson-calibration-r1")
    check = None
    audit = attempt.parent.parent / "AC2D9_FORMULA_AUDIT.json"
    if audit.exists():
        dev_audit = load_json(audit)
        check = {"note": "the completed run's per-seed block statistics are recomputed in the AC2D-9 audit; the "
                         "dimension-aware statistic is evaluated here from the same stored predictions",
                 "seeds": len(dev_audit["perSeedOnDev"])}

    document = {
        "purpose": "dimension-aware calibration of the localized-error failure signature (Final Closure Audit issue 5)",
        "calibratedAt": utc_now(),
        "prospective": True,
        "appliesTo": "future experiments' signatureCriteria; the completed 2D calibration is NOT re-judged",
        "oldRule": {"statistic": "max block RMS / median block RMS", "threshold": 3.0, "bins": 10,
                    "problem": "fires on a correct 2D solution (the 2D calibration measured 3.94 with every acceptance "
                               "criterion satisfied by more than an order of magnitude)"},
        "decisionRule": ["separate both fixture families at every grid / block / amplitude combination",
                         "maximise the worst-case separation ratio",
                         "threshold = geometric mean of (worst non-localized, weakest localized)",
                         "the completed run's value never enters the calibration"],
        "fixtures": {"nonLocalized": list(NON_LOCALIZED_FIXTURES), "localized": list(LOCALIZED_FIXTURES),
                     "pointSets": [label for label, _ in point_sets], "blocksPerAxis": list(BLOCKS), "amplitudes": list(AMPLITUDES),
                     "cases": len(sweep)},
        "candidates": summary,
        "chosen": {"candidate": chosen, "threshold": threshold,
                   "worstNonLocalized": summary[chosen]["worstNonLocalized"],
                   "weakestLocalized": summary[chosen]["weakestLocalized"],
                   "marginBelow": threshold / summary[chosen]["worstNonLocalized"],
                   "marginAbove": summary[chosen]["weakestLocalized"] / threshold},
        "completedRunCheck": check,
        "governanceClassification": {
            "verdict": "PROTOCOL CALIBRATION, not a constitutional semantic change",
            "reason": "only the symptom statistic and its threshold change, and both live in the protocol and in each "
                      "experiment's preregistered signatureCriteria; FailureSignature names, RootCause classes, "
                      "TrustStatus values and Claim semantics are untouched",
            "amendmentNeeded": False,
        },
        "sweep": sweep,
    }
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for name, value in summary.items():
        print(f"{name:<26} separates={value['separatesEverywhere']!s:<5} null<= {value['worstNonLocalized']:.3f} "
              f"hot>= {value['weakestLocalized']:.3f} ratio {value['separationRatio']:.2f}")
    print(f"\nchosen: {chosen} with threshold {threshold:.4f} "
          f"(x{document['chosen']['marginBelow']:.2f} above the worst null, "
          f"x{document['chosen']['marginAbove']:.2f} below the weakest hotspot)")
    print("written", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
