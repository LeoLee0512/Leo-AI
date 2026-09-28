"""Resume fidelity fixture: does a checkpoint really continue the same trajectory?

Phase II of the annulus diagnosis rests on one claim -- that 180k is the exact
continuation of its own 120k state and 240k of its own 180k. That claim is worth
nothing unless resume is verified first, on something small enough to run in a minute
and structured like the real thing. So:

    continuous   0 -> 2000
    split        0 -> 1000, checkpoint, reload, 1000 -> 2000

and the two are compared where it matters. The LR prefix is deliberately set to 1200,
between the checkpoint (1000) and the end (2000), so the resumed half crosses the point
where the schedule stops decaying and starts being held -- the one place where a
scheduler restored to the wrong position would silently produce a different trajectory.

The contract is BITWISE. That is not an aspiration: on this machine the r1 ensemble was
re-run from the same seeds on the same device and reproduced its weights with a maximum
absolute difference of 0.0 and an identical dev error, so anything looser would be
accepting less than the code has already demonstrated.

    marking         DIAGNOSTIC FIXTURE
    formalEvidence  false
    sets read       D_dev only; no claim set exists in this file

    PYTHONPATH=. PYTHONIOENCODING=utf-8 <mamba python> -u -B \
        experiments/annulus/resume_fidelity_annulus.py --device cuda
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pinn.experiments_annulus import datasets_annulus as ds
from pinn.experiments_annulus import pinn_torch_annulus as pinn

OUT = Path("experiments/annulus/diagnosis/RESUME_FIDELITY.json")

TOTAL = 2000
CHECKPOINT = 1000
PREFIX = 1200          # between CHECKPOINT and TOTAL on purpose: the resume crosses the LR hold
SEEDS = {"init": 20261200, "sample": 20261210, "batch": 20261220}     # exploratory bases, not the formal ones

CONFIG = {
    "configId": "annulus-resume-fidelity-fixture",
    "network": {"hiddenLayers": 4, "width": 64, "activation": "tanh", "input": "x,y", "output": "u",
                "outputParameterization": "(R^2-s)(s-a^2)N"},
    "optimizer": {"name": "Adam", "lr": 1e-3, "finalLr": 1e-5, "steps": TOTAL, "batchSize": 128,
                  "threads": 1, "lrPrefixSteps": PREFIX},
    "lossWeights": {"pde": 1.0},
}


def flatten(value, out=None):
    out = [] if out is None else out
    if isinstance(value, dict):
        for key in sorted(value):
            flatten(value[key], out)
    elif isinstance(value, list):
        for item in value:
            flatten(item, out)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        out.append(float(value))
    return out


def max_abs_diff(a, b) -> tuple[float, int]:
    fa, fb = flatten(a), flatten(b)
    if len(fa) != len(fb):
        return float("inf"), -1
    if not fa:
        return 0.0, 0
    return max(abs(x - y) for x, y in zip(fa, fb)), len(fa)


def train(steps: int, *, device: str, pool, dev, checkpoint_steps, resume_from=None):
    config = json.loads(json.dumps(CONFIG))
    config["optimizer"]["steps"] = steps
    captured: dict[int, dict] = {}
    run = pinn.train_run(config, pool, dev, SEEDS, collocation_count=128, log_every=250, device=device,
                         checkpoint_steps=checkpoint_steps,
                         checkpoint_sink=lambda step, state: captured.__setitem__(step, state),
                         resume_from=resume_from)
    return run, captured


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pool = ds.area_uniform_interior(256, 20261230)
    dev = ds.area_uniform_interior(192, 20261240)

    started = time.perf_counter()
    print(f"continuous 0 -> {TOTAL}")
    cont_run, cont_ckpt = train(TOTAL, device=args.device, pool=pool, dev=dev,
                                checkpoint_steps=(CHECKPOINT, TOTAL))
    print(f"split      0 -> {CHECKPOINT}, reload, {CHECKPOINT} -> {TOTAL}")
    first_run, first_ckpt = train(CHECKPOINT, device=args.device, pool=pool, dev=dev,
                                  checkpoint_steps=(CHECKPOINT,))
    # the checkpoint goes through JSON exactly as it would on disk: a state that only
    # survives in memory is not a checkpoint
    carried = json.loads(json.dumps(first_ckpt[CHECKPOINT]))
    second_run, second_ckpt = train(TOTAL, device=args.device, pool=pool, dev=dev,
                                    checkpoint_steps=(TOTAL,), resume_from=carried)

    a, b = cont_ckpt[TOTAL], second_ckpt[TOTAL]
    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")

    d, n = max_abs_diff(a["modelState"], b["modelState"])
    check("modelParametersIdentical", d == 0.0, f"max |dW| = {d:.3e} over {n} values")
    d, n = max_abs_diff(a["optimizerState"]["state"], b["optimizerState"]["state"])
    check("optimizerStateIdentical", d == 0.0, f"max |d(m_t, v_t, step)| = {d:.3e} over {n} values")
    check("schedulerPositionIdentical", a["scheduler"] == b["scheduler"], json.dumps(b["scheduler"]))
    check("learningRateIdentical", a["scheduler"]["currentLr"] == b["scheduler"]["currentLr"],
          f"{b['scheduler']['currentLr']} (held terminal after prefix {PREFIX})")
    check("batchGeneratorStateIdentical", a["batchGeneratorState"] == b["batchGeneratorState"],
          "torch.Generator byte state")
    check("orderAndCursorIdentical", a["order"] == b["order"] and a["cursor"] == b["cursor"],
          f"cursor {b['cursor']}, order length {len(b['order'])}")
    check("rngStatesIdentical", a["rngStates"] == b["rngStates"], "global CPU (and CUDA) RNG states")
    check("devMetricIdentical", cont_run["devRelL2"] == second_run["devRelL2"],
          f"continuous {cont_run['devRelL2']:.17e} vs resumed {second_run['devRelL2']:.17e}")
    check("checkpointAtCutIdentical", cont_ckpt[CHECKPOINT]["modelState"] == first_ckpt[CHECKPOINT]["modelState"],
          f"the step-{CHECKPOINT} state of the continuous run equals the split run's")
    tail = {e["step"]: e for e in second_run["lossHistory"]}
    cont_tail = {e["step"]: e for e in cont_run["lossHistory"] if e["step"] > CHECKPOINT}
    shared = sorted(set(tail) & set(cont_tail))
    same = all(tail[s]["total"] == cont_tail[s]["total"] and tail[s]["lr"] == cont_tail[s]["lr"] for s in shared)
    check("lossAndLrHistoryIdentical", bool(shared) and same,
          f"{len(shared)} shared logged steps after the cut: {shared}")
    check("resumeStartedWhereItStopped", second_run["resumedFromStep"] == CHECKPOINT,
          f"resumedFromStep = {second_run['resumedFromStep']}")

    verdict = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    document = {
        "marking": "DIAGNOSTIC FIXTURE", "formalEvidence": False,
        "purpose": "verify that a checkpoint resumes the SAME optimization trajectory before the "
                   "ten-seed nested budget intervention is started (PART 6)",
        "contract": "bitwise; justified by the observed r1 re-run agreement (max |dW| = 0.0 on the same "
                    "device and seeds)",
        "design": {"total": TOTAL, "checkpoint": CHECKPOINT, "lrPrefixSteps": PREFIX,
                   "note": "the prefix sits between the checkpoint and the end, so the resumed half crosses "
                           "the point where the schedule stops decaying"},
        "seeds": SEEDS, "device": args.device,
        "resumeFidelity": verdict, "checks": checks,
        "elapsedSeconds": time.perf_counter() - started,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nresume fidelity: {verdict}  -> {OUT}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
