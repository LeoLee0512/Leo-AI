"""Revision 2 of the annulus attempt (owner's ruling 2026-09-26): what was frozen before it ran.

Torch-free; the parallel-equals-sequential check lives in ``test_annulus_parallel.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from pinn.governance.trust_loop import problem_definition_spec_hash

REPO = Path(__file__).resolve().parents[2]
ANNULUS = REPO / "experiments/annulus"
R1_CONFIG = ANNULUS / "configs/exp_annulus_baseline.json"
R2_CONFIG = ANNULUS / "configs/exp_annulus_r2_240k.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_r2_differs_from_r1_only_in_budget_schedule_seeds_and_driver():
    r1, r2 = _json(R1_CONFIG), _json(R2_CONFIG)
    assert r2["optimizer"]["steps"] == 240000 and r2["optimizer"]["lrPrefixSteps"] == 120000
    changed = {key for key in r1 if r1[key] != r2[key]}
    assert changed == {"configId", "description", "optimizer", "seedProtocol", "codeIdentityExtraFiles"}
    for key in ("lr", "finalLr", "batchSize", "threads", "name"):
        assert r1["optimizer"][key] == r2["optimizer"][key], key
    assert r2["codeIdentityExtraFiles"] == ["experiments/annulus/run_formal_annulus_r2.py"]
    assert r1["reproduction"] == r2["reproduction"], "the G6 tolerance was frozen for r1 and is inherited"


def test_r2_problem_definition_keeps_the_r1_spec_and_names_dac_m1():
    r1 = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-r1.json")
    r2 = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-r2.json")
    assert r2["revision"] == 2
    assert r2["specHash"] == r1["specHash"] == problem_definition_spec_hash(r2)
    assert r2["frozenAt"] == r1["frozenAt"], "the specification is the one frozen for r1, not re-frozen"
    pool = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-claim-pool.json")["members"]
    assert pool["DAC-M1"]["designatedRevision"] == 2
    assert r2["evaluationSets"]["claim"]["sha256"] == pool["DAC-M1"]["artifactHash"]
    for role in ("train", "dev", "phys"):
        assert r2["evaluationSets"][role] == r1["evaluationSets"][role], role


def _seeds(config, offset=0):
    protocol = config["seedProtocol"]
    return {protocol[base] + offset + i for base in ("initBase", "sampleBase", "batchBase")
            for i in range(protocol["runs"])}


def test_r2_seeds_are_new_and_disjoint_from_r1_and_from_its_own_reproduction():
    r1, r2 = _json(R1_CONFIG), _json(R2_CONFIG)
    offset = r2["reproduction"]["seedOffset"]
    main, repro = _seeds(r2), _seeds(r2, offset)
    assert len(main) == 30 and len(repro) == 30
    assert not main & _seeds(r1) and not main & _seeds(r1, offset)
    assert not repro & _seeds(r1) and not repro & _seeds(r1, offset)
    assert not main & repro
    assert not main & {20261200, 20261210, 20261220}, "smoke bases"


def test_the_driver_holds_no_machine_path():
    text = (ANNULUS / "run_formal_annulus_r2.py").read_text(encoding="utf-8")
    assert "C:/Users" not in text and "C:\\\\Users" not in text and "envB2D" not in text


def test_parallel_workers_is_execution_not_config():
    for config in (_json(R1_CONFIG), _json(R2_CONFIG)):
        assert "workers" not in json.dumps(config["optimizer"])
    source = (REPO / "pinn/experiments_annulus/runner_annulus.py").read_text(encoding="utf-8")
    assert '"executionParallelism"' in source


def test_closure_never_upgrades_and_holds_without_a_signed_c2():
    from pinn.experiments_annulus import closure_annulus as closure
    from pinn.governance.state_machine import IllegalTransition, WorkflowState, advance, GateStatus
    from pinn.governance.trust_vector import TrustStatus

    assert closure.ORDER["PASS"] < closure.ORDER["PARTIAL"] < closure.ORDER["FAIL"]
    vector = {d: TrustStatus.PASS for d in closure.DIMENSIONS}
    try:
        advance(WorkflowState.REPRODUCIBILITY_CHECK, 6, GateStatus.PASS, vector, claim_decision_signed=False)
    except IllegalTransition:
        pass
    else:
        raise AssertionError("ACCEPTED without a signed decision must be illegal")
    assert advance(WorkflowState.REPRODUCIBILITY_CHECK, 6, GateStatus.PASS, vector,
                   claim_decision_signed=True) is WorkflowState.ACCEPTED
