"""End-to-end smoke test of the 2D runner in a temporary sandbox.

Not part of the experiment and not committed: it points LEDGER_DIR / PROBLEMS_DIR /
REGISTRY_PATH and the output root at a temporary directory, uses a tiny throwaway
configuration and a throwaway problemId, and checks that the whole pipeline runs:
identity -> problem freeze -> claim seal -> G1..G3 -> training -> G4 -> G5a/G5b
(claim OPENED) -> G6 BLOCKED -> TrustVector -> ClaimGateDecision -> trust report,
and, in a second pass, the Gate 4 failure path.

    PYTHONPATH=. <mamba python> -B <this file> <sandbox dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def build_config(sandbox: Path, epsilon: float) -> Path:
    config = {
        "configId": f"poisson2d-smoke-{epsilon:g}",
        "description": "throwaway smoke configuration; never a formal run",
        "network": {"hiddenLayers": 2, "width": 16, "activation": "tanh", "input": "x,y", "output": "u",
                    "initialization": "torch default", "outputParameterization": "x(1-x)y(1-y)N"},
        "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-4, "schedule": "exponential", "steps": 300,
                      "batchSize": 64, "threads": 1, "stopping": "fixed step count"},
        "lossWeights": {"pde": 1.0},
        "sampling": {"poolSize": 128, "poolSeed": 20260801, "collocationCount": 64, "rule": "smoke"},
        "seedProtocol": {"runs": 10, "initBase": 20260700, "sampleBase": 20260710, "batchBase": 20260720, "rule": "smoke"},
        "sets": {"devSize": 64, "devSeed": 20260802, "physOrder": 8, "boundaryOrder": 8, "minSeparation": 1e-9},
        "preregistration": {"errorNorm": "relativeL2", "epsilonSpec": epsilon, "worstSeedFactor": 3.0,
                            "dispersionLimit": 5.0, "qoiBand": None},
        "physicsThresholds": {"PH1": 10.0, "PH2": 10.0, "PH3": 10.0, "PH4": 10.0, "PH5": 10.0, "PH6": 10.0,
                              "PH7_energyFloor": 1e-14},
        "signatureCriteria": {"sPdeResidual": {"normalizedResidualRms": 0.01}, "sBcResidual": {"maxBoundaryAbs": 1e-4},
                              # d >= 2 trigger: the preregistered localized acceptance criterion (AC2D-9)
                              "sLocalizedError": {"tilesPerAxis": 8, "bins": 64, "maxBinToMedianBinRatio": 3.0,
                                                  "criterion": "AC2D-9", "statistic": "maxTileRmsErrorOverReferenceRms",
                                                  "normalization": "globalReferenceRms", "partitionKind": "uniformTiles",
                                                  "operator": "<=", "threshold": 1e-3, "evaluationSet": "dev",
                                                  "preregisteredIn": "experiments/poisson2d/smoke_runner2d.py (sandbox smoke test, not a formal run)"},
                              "sConservation": {"PH1": 0.01}, "sPinnCfd": {"rule": "median > epsilonSpec"},
                              "sSeedSensitive": {"rule": "Constitution 10.1"}},
        "reproduction": {"devRelL2MedianAbsDiff": 1.0, "devRelL2MedianRelDiff": 5.0, "seedProtocolVerdictMustAgree": True,
                         "seedOffset": 10000},
        "thresholdSources": {"acceptanceCriteria": "smoke", "physics": "smoke", "signatures": "smoke"},
    }
    path = sandbox / f"smoke_config_{epsilon:g}.json"
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def main() -> int:
    sandbox = Path(sys.argv[1]).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    from pinn.experiments2d import runner2d
    from pinn.experiments2d import gates2d

    # Sandbox only: a 300-step toy model cannot meet the real acceptance thresholds, so the Gate 5b verdict (and only
    # that verdict) is forced to PASS here to exercise the tail (decision, Gate 6, Tier-1, plots). The thresholds
    # themselves are NOT touched: lifting them makes Gate 3's T10 control fixtures fail, which is the correct behaviour
    # and was observed in an earlier smoke pass.
    _claim_evaluation = gates2d.claim_evaluation

    def _relaxed(model, grids, **kw):
        out = _claim_evaluation(model, grids, **kw)
        out["failedMustCriteria"] = []
        out["failedShouldCriteria"] = []
        out["componentCriteriaSatisfied"] = True
        return out

    gates2d.claim_evaluation = _relaxed

    runner2d.LEDGER_DIR = sandbox / "ledger"
    runner2d.PROBLEMS_DIR = sandbox / "problems"
    runner2d.REGISTRY_PATH = sandbox / "ledger" / "sample_set_registry.json"
    runner2d.PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)

    # loose epsilon: the whole pipeline including the claim set and the decision
    loose = build_config(sandbox, 1.0)
    runner2d.run_register_pool("pdef-poisson2d-smoke", ["SMOKE-GL8-CGL14:8:14", "SMOKE-GL10-CGL20:10:20"], 1, loose)
    attempt = runner2d.Attempt2D(config_path=loose, attempt_id="smoke-pass", problem_id="pdef-poisson2d-smoke", revision=1,
                                 out_root=sandbox / "runs", ledger_path=sandbox / "ledger/pdef-poisson2d-smoke.json",
                                 reenter_from=None, claim_pool_member="SMOKE-GL8-CGL14")
    summary = attempt.run()
    print(json.dumps({k: summary.get(k) for k in ("finalState", "trustVector", "highestAllowedClaim", "allowedClaims")},
                     ensure_ascii=False, indent=2))
    assert summary["finalState"] == "REPRODUCIBILITY_CHECK", summary["finalState"]
    assert summary["trustVector"]["external"] == "PASS", summary["trustVector"]
    assert summary["highestAllowedClaim"] == "C1", summary["highestAllowedClaim"]

    # Tier-1 Red Team on the smoke attempt (exercises every applicable perturbation incl. P7 and P8)
    runner2d.run_redteam(sandbox / "runs/smoke-pass", label="tier1")

    # plots
    paths = __import__("pinn.experiments2d.report2d", fromlist=["report2d"]).plots(sandbox / "runs/smoke-pass")
    print("plots:", [p.name for p in paths])

    # reproduction pass: same config, different seeds, stops after Gate 4
    repro = runner2d.Attempt2D(config_path=loose, attempt_id="smoke-repro", problem_id="pdef-poisson2d-smoke", revision=1,
                               out_root=sandbox / "runs", ledger_path=sandbox / "ledger/pdef-poisson2d-smoke.json",
                               reenter_from=None, claim_pool_member="SMOKE-GL8-CGL14", seed_offset=10000,
                               reproduction_of=sandbox / "runs/smoke-pass")
    repro_summary = repro.run()
    print("reproduction:", json.dumps(repro_summary["reproduction"], ensure_ascii=False))
    assert repro_summary["reproduction"]["cRepro"] == "BLOCKED", "same environment must not qualify as independent"

    # strict epsilon: the Gate 4 failure path with the 2D diagnostics
    strict = build_config(sandbox, 1e-6)
    fail = runner2d.Attempt2D(config_path=strict, attempt_id="smoke-fail", problem_id="pdef-poisson2d-smokefail", revision=1,
                              out_root=sandbox / "runs", ledger_path=sandbox / "ledger/pdef-poisson2d-smokefail.json",
                              reenter_from=None, claim_pool_member="SMOKE-GL10-CGL20")
    runner2d.run_register_pool("pdef-poisson2d-smokefail", ["SMOKE-GL10-CGL20:10:20"], 1, strict)
    fail_summary = fail.run()
    print("failure path:", fail_summary["finalState"], fail_summary["failure"]["observedSignatures"])
    assert fail_summary["finalState"] == "FAILURE_RECORDED"
    assert fail_summary["failure"]["observedSignatures"], "no signature fired on an obviously bad run"
    ledger = json.loads((sandbox / "ledger/pdef-poisson2d-smokefail.json").read_text(encoding="utf-8"))
    assert all(e["event"] != "OPENED" for e in ledger), "a Gate 4 failure must never open the claim set"
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
