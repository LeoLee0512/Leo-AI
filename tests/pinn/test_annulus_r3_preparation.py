"""Revision 3 (owner's ruling B, 2026-09-26): r2 void, the method repeated on DAC-M2 with the code fixed."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pinn.governance.trust_loop import problem_definition_spec_hash

REPO = Path(__file__).resolve().parents[2]
ANNULUS = REPO / "experiments/annulus"
R2_CONFIG = ANNULUS / "configs/exp_annulus_r2_240k.json"
R3_CONFIG = ANNULUS / "configs/exp_annulus_r3_240k.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _seeds(config, offset=0):
    protocol = config["seedProtocol"]
    return {protocol[base] + offset + i for base in ("initBase", "sampleBase", "batchBase")
            for i in range(protocol["runs"])}


def test_r3_repeats_the_r2_method_with_new_seeds_and_its_own_driver():
    r2, r3 = _json(R2_CONFIG), _json(R3_CONFIG)
    assert {key for key in r2 if r2[key] != r3[key]} == {"configId", "description", "seedProtocol",
                                                         "codeIdentityExtraFiles"}
    assert r3["optimizer"] == r2["optimizer"] and r3["optimizer"]["steps"] == 240000
    assert r3["codeIdentityExtraFiles"] == ["experiments/annulus/run_formal_annulus_r3.py"]
    offset = r3["reproduction"]["seedOffset"]
    used = _seeds(r2) | _seeds(r2, offset) | _seeds(_json(ANNULUS / "configs/exp_annulus_baseline.json"))
    assert not (_seeds(r3) | _seeds(r3, offset)) & used and not _seeds(r3) & _seeds(r3, offset)


def test_r3_problem_definition_keeps_the_spec_and_names_the_never_sealed_dac_m2():
    r1 = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-r1.json")
    r3 = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-r3.json")
    assert r3["revision"] == 3 and r3["specHash"] == r1["specHash"] == problem_definition_spec_hash(r3)
    member = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-claim-pool.json")["members"]["DAC-M2"]
    assert member["designatedRevision"] == 3 and r3["evaluationSets"]["claim"]["sha256"] == member["artifactHash"]
    ledger = _json(ANNULUS / "ledger/pdef-annulus-poisson-v1.json")
    # r3 ran (2026-09-26/27): DAC-M2 was sealed and opened exactly once, both at revision 3; DAC-M3 never appears
    m2 = [(e["event"], e["revision"]) for e in ledger if e["claimSetSha256"] == member["artifactHash"]]
    assert m2 == [("SEALED", 3), ("OPENED", 3)]
    m3 = _json(ANNULUS / "problems/pdef-annulus-poisson-v1-claim-pool.json")["members"]["DAC-M3"]["artifactHash"]
    assert not any(e["claimSetSha256"] == m3 for e in ledger)


def test_every_registered_annulus_check_is_emitted_by_some_gate():
    source = (REPO / "pinn/experiments_annulus/gates_annulus.py").read_text(encoding="utf-8")
    registered = re.findall(r'"checkId": "([^"]+)", "dimension": "(\w+)"', source)
    emitted = set(re.findall(r'(?:check|not_applicable)\("([A-Za-z0-9]+-[A-Za-z]+)"', source))
    shared = {"G4-trainingIntegrity", "G4-seedProtocol", "G4-lossErrorDecoupling"}   # pinn.experiments.gates
    missing = [check for check, _dimension in registered if check not in emitted | shared]
    assert missing == [], f"registered but never recorded: {missing}"
    assert 'not_applicable("PH10-momentumBudget")' in source and 'not_applicable("PH11-freeEnergy")' in source


def test_the_runner_validates_before_the_claim_set_is_opened_and_before_it_writes():
    source = (REPO / "pinn/experiments_annulus/runner_annulus.py").read_text(encoding="utf-8")
    validation = source[source.index("    def phase_validation"):]
    assert validation.index("self.preflight_decision()") < validation.index('event="OPENED"')
    entry = source[source.index("def dimension_entry"):source.index("def statuses_of")]
    assert '"schemaVersion": "pinn.trustVector/1.2"' in source
    assert '"evidencePointers"' in entry and '"evidenceRefs"' not in entry, "the dimension entry uses the 1.2 layout"
    assert "environment_id=" not in source and "qualified_c2_runs=" not in source
    finish = source[source.index("    def finish"):source.index("    def run(self)")]
    assert finish.index("self.decision_document(") < finish.index('write_json("claim_statements.json"')
    closure = (REPO / "pinn/experiments_annulus/closure_annulus.py").read_text(encoding="utf-8")
    assert "build_decision(" in closure and "claim_gate(" not in closure, "one validated decision builder"


def test_r2_is_recorded_void_and_its_ruling_script_refuses_to_rerun():
    text = (ANNULUS / "record_r2_void.py").read_text(encoding="utf-8")
    assert "VOID_NO_CLAIM" in text and "the ruling is already recorded" in text


def test_the_r3_driver_holds_no_machine_path_and_runs_the_formal_defaults():
    text = (ANNULUS / "run_formal_annulus_r3.py").read_text(encoding="utf-8")
    assert "C:/Users" not in text and "envB2D" not in text
    assert 'REVISION = 3' in text and 'CLAIM_MEMBER = "DAC-M2"' in text
