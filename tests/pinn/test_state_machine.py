"""Permission decisions never manufacture scientific evidence or verdicts."""

import pytest

from pinn.governance.state_machine import (
    GateStatus,
    claim_prerequisite_status,
    operation_prerequisite_status,
    postlock_gate1_status,
)


@pytest.mark.parametrize("prelock", [False, None, "PASS", "FAIL", 1])
def test_nonboolean_prelock_cannot_advance(tmp_path, prelock):
    path = tmp_path / "lock.json"
    path.write_text("fixture", encoding="utf-8")
    assert postlock_gate1_status(prelock_passed=prelock, lock_path=path,
                                verify_lock=lambda _: True) is GateStatus.BLOCKED


@pytest.mark.parametrize("result", [False, None, "PASS", "FAIL", 1, {}])
def test_truthy_verifier_results_do_not_pass(tmp_path, result):
    path = tmp_path / "lock.json"
    path.write_text("fixture", encoding="utf-8")
    assert postlock_gate1_status(prelock_passed=True, lock_path=path,
                                verify_lock=lambda _: result) is GateStatus.FAIL


def test_missing_lock_is_blocked_but_directory_is_failed(tmp_path):
    path = tmp_path / "lock.json"
    assert postlock_gate1_status(prelock_passed=True, lock_path=path,
                                verify_lock=lambda _: True) is GateStatus.BLOCKED
    path.mkdir()
    assert postlock_gate1_status(prelock_passed=True, lock_path=path,
                                verify_lock=lambda _: True) is GateStatus.FAIL


@pytest.mark.parametrize("error", [ValueError, RuntimeError, ImportError, OSError])
def test_verifier_exception_propagates_as_failed_gate(tmp_path, error):
    path = tmp_path / "lock.json"
    path.write_text("fixture", encoding="utf-8")

    def failing(_):
        raise error("failure")

    assert postlock_gate1_status(prelock_passed=True, lock_path=path,
                                verify_lock=failing) is GateStatus.FAIL


def test_operator_interrupt_not_swallowed(tmp_path):
    path = tmp_path / "lock.json"
    path.write_text("fixture", encoding="utf-8")

    def interrupted(_):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        postlock_gate1_status(prelock_passed=True, lock_path=path, verify_lock=interrupted)


def test_only_literal_verified_lock_passes(tmp_path):
    path = tmp_path / "lock.json"
    path.write_text("fixture", encoding="utf-8")
    assert postlock_gate1_status(prelock_passed=True, lock_path=path,
                                verify_lock=lambda _: True) is GateStatus.PASS


@pytest.mark.parametrize("claim,required", [
    ("C0", (1, 3)), ("C1", (1, 3, 4)), ("C2", (1, 2, 3, 4, 5, 6)),
])
def test_claim_uses_only_necessary_gates(claim, required):
    gates = {number: GateStatus.PASS for number in required}
    assert claim_prerequisite_status(claim, gates, evidence_level="A") is GateStatus.PASS
    for number in required:
        for status in (GateStatus.FAIL, GateStatus.PARTIAL, GateStatus.BLOCKED, "PASS", True):
            changed = {**gates, number: status}
            assert claim_prerequisite_status(claim, changed, evidence_level="A") is GateStatus.BLOCKED


def test_exploratory_optimization_does_not_imply_accuracy():
    gates = {number: GateStatus.PASS for number in range(1, 7)}
    gates[2] = GateStatus.FAIL
    assert claim_prerequisite_status("C0", gates, evidence_level="D") is GateStatus.PASS
    assert claim_prerequisite_status("C1", gates, evidence_level="D") is GateStatus.PASS
    assert claim_prerequisite_status("C2", gates, evidence_level="D") is GateStatus.BLOCKED
    gates[2] = GateStatus.PASS
    assert claim_prerequisite_status("C2", gates, evidence_level="D") is GateStatus.BLOCKED


@pytest.mark.parametrize("claim", ["C3", "C4", "C5", "UNKNOWN"])
def test_per_run_gates_cannot_claim_suite_robustness_or_out_of_scope(claim):
    gates = {number: GateStatus.PASS for number in range(1, 8)}
    assert claim_prerequisite_status(claim, gates, evidence_level="A") is GateStatus.BLOCKED


@pytest.mark.parametrize("gate,required", [(3, (1,)), (4, (1, 3)), (5, (1, 2, 3, 4)), (6, (4,))])
def test_downstream_operations_use_registered_dependencies(gate, required):
    gates = {number: GateStatus.PASS for number in required}
    assert operation_prerequisite_status(gate, gates, evidence_level="A") is GateStatus.PASS
    for number in required:
        changed = {**gates, number: GateStatus.FAIL}
        assert operation_prerequisite_status(gate, changed, evidence_level="A") is GateStatus.BLOCKED


@pytest.mark.parametrize("gate", [3, 4])
def test_failed_reference_only_allows_level_d_exploration(gate):
    gates = {1: GateStatus.PASS, 2: GateStatus.FAIL, 3: GateStatus.PASS, 4: GateStatus.PASS}
    assert operation_prerequisite_status(gate, gates, evidence_level="D") is GateStatus.PASS
    for evidence_level in ("A", "B", "C"):
        assert operation_prerequisite_status(gate, gates, evidence_level=evidence_level) is GateStatus.BLOCKED
    gates[1] = GateStatus.BLOCKED
    assert operation_prerequisite_status(gate, gates, evidence_level="D") is GateStatus.BLOCKED


def test_level_d_does_not_bypass_implementation_or_validation():
    gates = {number: GateStatus.PASS for number in range(1, 7)}
    gates[2] = GateStatus.FAIL
    assert operation_prerequisite_status(5, gates, evidence_level="D") is GateStatus.BLOCKED
    gates[3] = GateStatus.FAIL
    assert operation_prerequisite_status(4, gates, evidence_level="D") is GateStatus.BLOCKED


def test_gate6_failure_guard_preserves_explicit_level_d_case():
    gates = {1: GateStatus.PASS, 2: GateStatus.FAIL, 3: GateStatus.PASS,
             4: GateStatus.PASS, 5: GateStatus.BLOCKED}
    assert operation_prerequisite_status(6, gates, evidence_level="D") is GateStatus.PASS
    gates[5] = GateStatus.FAIL
    assert operation_prerequisite_status(6, gates, evidence_level="D") is GateStatus.BLOCKED
    gates[5] = GateStatus.PARTIAL
    assert operation_prerequisite_status(6, gates, evidence_level="A") is GateStatus.BLOCKED


def test_explicit_invalidated_spec_blocks_even_reproducibility():
    gates = {1: GateStatus.FAIL, 4: GateStatus.PASS}
    assert operation_prerequisite_status(6, gates, evidence_level="A") is GateStatus.BLOCKED


@pytest.mark.parametrize("status", [GateStatus.PARTIAL, GateStatus.BLOCKED, GateStatus.FAIL])
def test_partial_or_missing_upstream_never_advances_training(status):
    assert operation_prerequisite_status(4, {1: status, 3: GateStatus.PASS},
                                         evidence_level="D") is GateStatus.BLOCKED


def test_stop_the_line_and_unknown_evidence_fail_closed():
    gates = {number: GateStatus.PASS for number in range(1, 8)}
    for arguments in ({"evidence_level": "A", "stop_the_line": True},
                      {"evidence_level": "A", "stop_the_line": "false"},
                      {"evidence_level": "UNKNOWN"}):
        assert operation_prerequisite_status(4, gates, **arguments) is GateStatus.BLOCKED
        assert claim_prerequisite_status("C2", gates, **arguments) is GateStatus.BLOCKED
