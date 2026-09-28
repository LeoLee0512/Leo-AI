"""Weakest-link calculus: claims are gated by the meet of the vector, never by an average."""

import pytest

from pinn.governance.state_machine import GateStatus
from pinn.governance.trust_vector import (
    CLAIM_LEVELS,
    DIMENSIONS,
    SUPPORT_RANK,
    Applicability,
    CheckResult,
    EnvironmentFingerprint,
    NoApplicableCheck,
    RunQualification,
    TrustStatus,
    allowed_claim_levels,
    c3_run_support,
    claim_gate,
    coerce_vector,
    dimension_status_from_checks,
    environment_id,
    independent_environments,
    meet,
    reproduction_status,
    seed_set_id,
    seed_statistics,
    training_reliability_status,
    weakest_link,
)

P, PA, F, B, N = (
    TrustStatus.PASS,
    TrustStatus.PARTIAL,
    TrustStatus.FAIL,
    TrustStatus.BLOCKED,
    TrustStatus.NOT_CHECKED,
)
SPEC = "a" * 64
CODE = "b" * 64


def vector(math=P, impl=P, train=P, physics=P, external=P, repro=P):
    return {"math": math, "impl": impl, "train": train, "physics": physics, "external": external, "repro": repro}


def runs(count=5, *, environments=("env-a", "env-b"), spec=SPEC, code=CODE, seed_sets=None):
    seed_sets = seed_sets or [f"seeds-{index}" for index in range(count)]
    return [
        RunQualification(run_id=f"run-{index}", spec_hash=spec, code_hash=code,
                         environment_id=environments[index % len(environments)], seed_set_id=seed_sets[index])
        for index in range(count)
    ]


def test_chain_order_is_fail_blocked_not_checked_partial_pass():
    assert sorted(TrustStatus, key=SUPPORT_RANK.__getitem__) == [F, B, N, PA, P]


def test_meet_is_the_weakest_and_needs_input():
    assert meet([P, PA, P]) is PA
    assert meet([P, N, PA]) is N
    assert meet([B, F]) is F
    assert meet([P]) is P
    with pytest.raises(ValueError):
        meet([])
    with pytest.raises(TypeError):
        meet([P, "PASS"])


def test_weakest_link_reports_every_tied_dimension_in_fixed_order():
    status, dimensions = weakest_link(vector(external=PA, train=PA))
    assert status is PA
    assert dimensions == ("train", "external")
    assert weakest_link(vector()) == (P, DIMENSIONS)


# ------------------------------------------------ DeepSeek math-core §4.4 examples

def test_example_1_all_pass_level_a_allows_up_to_c2():
    gate = claim_gate(vector(), evidence_level="A")
    assert gate.allowed == ("C0", "C1", "C2")
    assert gate.highest_allowed == "C2"
    assert "C3" in gate.blocked


def test_example_2_unchecked_reproducibility_blocks_c2():
    assert allowed_claim_levels(vector(repro=N), evidence_level="A") == ("C0", "C1")


def test_example_3_one_fail_is_not_outvoted_by_five_passes():
    assert allowed_claim_levels(vector(train=F), evidence_level="A") == ("C0",)
    assert allowed_claim_levels(vector(physics=F), evidence_level="A") == ("C0", "C1")


def test_example_4_partial_is_not_pass():
    assert allowed_claim_levels(vector(physics=PA), evidence_level="A") == ("C0", "C1")


def test_example_5_blocked_external_with_level_d():
    assert allowed_claim_levels(vector(external=B), evidence_level="D") == ("C0", "C1")


def test_example_6_fail_and_blocked_cap_claims_identically_but_report_differently():
    assert allowed_claim_levels(vector(physics=F), evidence_level="A") == allowed_claim_levels(
        vector(physics=B), evidence_level="A"
    )
    assert weakest_link(vector(physics=F))[0] is F
    assert weakest_link(vector(physics=B))[0] is B


def test_example_7_level_d_excludes_c2_even_when_everything_passes():
    gate = claim_gate(vector(), evidence_level="D")
    assert gate.allowed == ("C0", "C1")
    assert any("evidence level D" in reason for reason in gate.blocked["C2"])


# ------------------------------------------------------------- C3 independence

def test_c3_needs_five_independently_qualified_c2_runs():
    assert allowed_claim_levels(vector(), evidence_level="A", c2_runs=runs(4),
                                spec_hash=SPEC, code_hash=CODE) == ("C0", "C1", "C2")
    assert allowed_claim_levels(vector(), evidence_level="A", c2_runs=runs(5),
                                spec_hash=SPEC, code_hash=CODE) == ("C0", "C1", "C2", "C3")


def test_copied_runs_do_not_count_as_independent():
    same_seeds = c3_run_support(runs(5, seed_sets=["seeds-0"] * 5), spec_hash=SPEC, code_hash=CODE)
    assert same_seeds.qualified_runs == 1
    assert not same_seeds.satisfied
    assert any("distinct seed set" in problem for problem in same_seeds.problems)


def test_c3_needs_two_execution_environments():
    single = c3_run_support(runs(5, environments=("env-a",)), spec_hash=SPEC, code_hash=CODE)
    assert single.qualified_runs == 5
    assert not single.satisfied
    assert any("environment" in problem for problem in single.problems)
    gate = claim_gate(vector(), evidence_level="A", c2_runs=runs(5, environments=("env-a",)),
                      spec_hash=SPEC, code_hash=CODE)
    assert "C3" in gate.blocked


def test_runs_of_another_method_do_not_count():
    foreign = runs(3, spec=SPEC, code=CODE) + runs(2, code="c" * 64)
    support = c3_run_support(foreign, spec_hash=SPEC, code_hash=CODE)
    assert support.qualified_runs == 3
    assert any("different spec or code identity" in problem for problem in support.problems)
    with pytest.raises(TypeError):
        c3_run_support([("run-1", SPEC, CODE, "env", "seeds")], spec_hash=SPEC, code_hash=CODE)
    with pytest.raises(ValueError):
        RunQualification(run_id="", spec_hash=SPEC, code_hash=CODE, environment_id="env", seed_set_id="s")


def test_runs_without_method_identity_fail_closed():
    gate = claim_gate(vector(), evidence_level="A", c2_runs=runs(5))
    assert gate.allowed == ()
    assert set(gate.blocked) == set(CLAIM_LEVELS)


def test_exploratory_runs_are_capped_at_c1():
    gate = claim_gate(vector(), evidence_level="A", c2_runs=runs(9), spec_hash=SPEC, code_hash=CODE,
                      exploratory=True)
    assert gate.allowed == ("C0", "C1")
    assert any("EXPLORATORY" in reason for reason in gate.blocked["C2"])
    assert any("EXPLORATORY" in reason for reason in gate.blocked["C3"])


@pytest.mark.parametrize("kwargs", [
    {"evidence_level": "E"},
    {"evidence_level": "A", "stop_the_line": True},
    {"evidence_level": "A", "stop_the_line": "false"},
    {"evidence_level": "A", "exploratory": "no"},
])
def test_fail_closed_inputs_block_every_level(kwargs):
    gate = claim_gate(vector(), **kwargs)
    assert gate.allowed == ()
    assert set(gate.blocked) == set(CLAIM_LEVELS)


def test_blocked_reasons_name_the_dimensions():
    gate = claim_gate(vector(train=N, repro=PA), evidence_level="B")
    assert gate.allowed == ("C0",)
    assert "train=NOT_CHECKED" in gate.blocked["C1"][0]
    assert gate.weakest_status is N
    assert gate.weakest_dimensions == ("train",)


def test_statuses_have_no_arithmetic():
    with pytest.raises(TypeError):
        P + F
    with pytest.raises(TypeError):
        sum([P, F], 0)
    with pytest.raises(TypeError):
        P / 2


@pytest.mark.parametrize("bad", [
    {},
    {**vector(), "extra": P},
    {dimension: P for dimension in DIMENSIONS[:-1]},
    {**vector(), "math": "pass"},
    {**vector(), "math": 1},
    {**vector(), "math": None},
])
def test_malformed_vectors_are_rejected(bad):
    with pytest.raises(ValueError):
        coerce_vector(bad)


def test_plain_strings_are_accepted_but_other_enums_are_not():
    assert coerce_vector({dimension: "PASS" for dimension in DIMENSIONS})["math"] is P
    with pytest.raises(ValueError):
        coerce_vector({**vector(), "math": GateStatus.PASS})
    with pytest.raises(TypeError):
        coerce_vector(["PASS"] * 6)


# ------------------------------------------------------- applicability typing

def test_not_applicable_checks_have_no_status_and_leave_the_meet():
    momentum = CheckResult("momentumBudget", Applicability.NOT_APPLICABLE, reason="scalar Poisson problem has no momentum")
    flux = CheckResult("fluxBalance", Applicability.APPLICABLE, status=P)
    symmetry = CheckResult("symmetry", Applicability.APPLICABLE, status=PA)
    assert dimension_status_from_checks([momentum, flux, symmetry]) is PA
    assert dimension_status_from_checks([]) is N


def test_all_not_applicable_is_an_illegal_registration_not_a_weak_not_checked():
    """INV-A1 (2026-09-15 review, issue 1): "applicability assessed, nothing owed" is not a dimension state."""

    momentum = CheckResult("momentumBudget", Applicability.NOT_APPLICABLE, reason="scalar Poisson problem has no momentum")
    energy = CheckResult("freeEnergy", Applicability.NOT_APPLICABLE, reason="covered by the energy identity")
    with pytest.raises(NoApplicableCheck):
        dimension_status_from_checks([momentum])
    with pytest.raises(NoApplicableCheck):
        dimension_status_from_checks([momentum, energy])
    assert issubclass(NoApplicableCheck, ValueError)


@pytest.mark.parametrize("kwargs", [
    {"applicability": Applicability.APPLICABLE},
    {"applicability": Applicability.APPLICABLE, "status": "PASS"},
    {"applicability": Applicability.NOT_APPLICABLE, "status": P, "reason": "why"},
    {"applicability": Applicability.NOT_APPLICABLE},
    {"applicability": Applicability.NOT_APPLICABLE, "reason": "  "},
])
def test_check_results_are_well_typed(kwargs):
    with pytest.raises(ValueError):
        CheckResult("check", **kwargs)
    with pytest.raises(TypeError):
        CheckResult("check", "NOT_APPLICABLE", reason="string is not the type")
    with pytest.raises(TypeError):
        dimension_status_from_checks([{"checkId": "x"}])


# --------------------------------------------------------------- seed protocol

def test_seed_rule_pass_partial_fail_bands():
    ok = {"median_ok": True, "worst_ok": True, "iqr_ok": True}
    assert training_reliability_status(runs=10, successes=10, **ok) is P
    assert training_reliability_status(runs=10, successes=9, **ok) is P
    assert training_reliability_status(runs=10, successes=8, **ok) is PA
    assert training_reliability_status(runs=10, successes=7, **ok) is F
    assert training_reliability_status(runs=20, successes=17, **ok) is PA


def test_worst_seed_and_iqr_hold_the_dimension_at_partial():
    assert training_reliability_status(runs=10, successes=10, median_ok=True, worst_ok=False, iqr_ok=True) is PA
    assert training_reliability_status(runs=10, successes=10, median_ok=True, worst_ok=True, iqr_ok=False) is PA
    assert training_reliability_status(runs=10, successes=10, median_ok=False, worst_ok=True, iqr_ok=True) is F


def test_transitional_run_counts_cap_at_partial_and_too_few_runs_block():
    ok = {"median_ok": True, "worst_ok": True, "iqr_ok": True}
    assert training_reliability_status(runs=5, successes=5, **ok) is PA
    assert training_reliability_status(runs=5, successes=3, **ok) is F
    assert training_reliability_status(runs=4, successes=4, **ok) is B


@pytest.mark.parametrize("kwargs", [
    {"runs": 10, "successes": 11},
    {"runs": -1, "successes": 0},
    {"runs": True, "successes": 1},
    {"runs": 10, "successes": 10, "median_ok": "yes"},
    {"runs": 10, "successes": 10, "minimum_runs": 3},
])
def test_seed_rule_rejects_malformed_inputs(kwargs):
    arguments = {"median_ok": True, "worst_ok": True, "iqr_ok": True, **kwargs}
    with pytest.raises(ValueError):
        training_reliability_status(**arguments)


# ------------------------------------------------- seed statistics (draft 3)

EPS = 1e-3
OK10 = [8e-4] * 10


def test_seed_statistics_bands_from_the_errors_themselves():
    assert seed_statistics(OK10, epsilon_spec=EPS).status is P
    assert seed_statistics(OK10[:9] + [5e-3], epsilon_spec=EPS).status is PA       # k/N = 0.9 but worst > 3 eps
    assert seed_statistics(OK10[:9] + [2e-3], epsilon_spec=EPS).status is P        # k/N = 0.9, worst within 3 eps
    assert seed_statistics(OK10[:8] + [2e-3] * 2, epsilon_spec=EPS).status is PA  # k/N = 0.8
    assert seed_statistics(OK10[:7] + [2e-3] * 3, epsilon_spec=EPS).status is F   # k/N = 0.7
    assert seed_statistics(OK10[:5], epsilon_spec=EPS).status is PA               # transitional N = 5
    assert seed_statistics(OK10[:4], epsilon_spec=EPS).status is B                # protocol not executed
    assert seed_statistics([], epsilon_spec=EPS).status is B


def test_dispersion_rule_has_no_division_and_no_floor():
    """Issue 5 (2026-09-15): median = 0 is handled by comparison, never by IQR / median."""

    exact = seed_statistics([0.0] * 10, epsilon_spec=EPS)
    assert (exact.median, exact.iqr, exact.dispersion_ok, exact.status) == (0.0, 0.0, True, P)
    spread = seed_statistics([0.0] * 6 + [1e-12] * 4, epsilon_spec=EPS)     # median 0, IQR > 0
    assert spread.median == 0.0 and spread.iqr > 0 and spread.dispersion_ok is False
    assert spread.status is PA
    near_zero = seed_statistics([1e-16] * 5 + [5e-16] * 5, epsilon_spec=EPS)   # median 3e-16, IQR 4e-16
    assert near_zero.dispersion_ok is False and near_zero.status is PA
    boundary = seed_statistics([1e-16] * 5 + [3e-16] * 5, epsilon_spec=EPS)    # IQR == median: not above
    assert boundary.dispersion_ok is True and boundary.status is P
    tight = seed_statistics([5e-4] * 5 + [6e-4] * 5, epsilon_spec=EPS)
    assert tight.dispersion_ok is True and tight.status is P


def test_divergent_runs_stay_in_n_and_never_in_k():
    nan = seed_statistics(OK10[:9] + [float("nan")], epsilon_spec=EPS)
    assert (nan.runs, nan.successes, nan.divergent) == (10, 9, 1)
    assert nan.worst == float("inf") and nan.worst_ok is False and nan.status is PA
    inf = seed_statistics(OK10[:7] + [float("inf")] * 3, epsilon_spec=EPS)
    assert inf.status is F and inf.divergent == 3
    half = seed_statistics([float("inf")] * 5 + OK10[:5], epsilon_spec=EPS)
    assert half.median == float("inf") and half.status is F


def test_worst_seed_caps_at_partial_and_median_fails():
    worst = seed_statistics(OK10[:9] + [4e-3], epsilon_spec=EPS)
    assert worst.worst_ok is False and worst.status is PA
    median = seed_statistics([2e-3] * 10, epsilon_spec=EPS)
    assert median.median_ok is False and median.status is F


@pytest.mark.parametrize("bad,exc", [
    ({"errors": [-1e-4] + OK10[:9]}, ValueError),
    ({"errors": ["0.1"] + OK10[:9]}, ValueError),
    ({"errors": [True] + OK10[:9]}, ValueError),
    ({"errors": OK10, "epsilon_spec": 0}, ValueError),
    ({"errors": OK10, "epsilon_spec": float("nan")}, ValueError),
    ({"errors": OK10, "dispersion_limit": 0}, ValueError),
    ({"errors": "0.1,0.2", "epsilon_spec": EPS}, TypeError),
])
def test_seed_statistics_rejects_malformed_inputs(bad, exc):
    arguments = {"epsilon_spec": EPS, **bad}
    with pytest.raises(exc):
        seed_statistics(**arguments)


# ---------------------------------------------- environment identity (draft 3)

BASE = dict(machineId="m1", osFamily="windows", acceleratorClass="cpu-only", frameworkVersion="torch-2.4",
            blasBackend="openblas", dependencyLockHash="c" * 64, installationId="venv-1",
            osVersion="11.0.26200", pythonVersion="3.12.4", acceleratorDriver="")


def env(**changes):
    return EnvironmentFingerprint(**{**BASE, **changes})


def test_case_a_same_machine_independent_installation_is_independent():
    assert independent_environments(env(), env(installationId="conda-2", dependencyLockHash="d" * 64))
    assert independent_environments(env(), env(installationId="conda-2"))


def test_case_b_same_machine_same_image_is_the_same_environment():
    image = "sha256-of-image"
    assert not independent_environments(env(installationId=image), env(installationId=image))
    assert environment_id(env(installationId=image)) == environment_id(env(installationId=image))


def test_case_c_different_machine_same_lockfile_is_independent():
    assert independent_environments(env(), env(machineId="m2"))


def test_case_d_cluster_nodes_are_independent_only_when_their_machine_ids_differ():
    assert independent_environments(env(machineId="node-01"), env(machineId="node-02"))
    assert not independent_environments(env(machineId="node-01"), env(machineId="node-01"))


def test_case_e_different_os_or_accelerator_is_independent():
    assert independent_environments(env(), env(osFamily="linux"))
    assert independent_environments(env(), env(acceleratorClass="nvidia-rtx-4090"))


def test_patch_level_differences_never_make_a_new_environment():
    weak = env(osVersion="11.0.99999", pythonVersion="3.12.9", acceleratorDriver="560.1")
    assert not independent_environments(env(), weak)
    assert environment_id(env()) == environment_id(weak)


def test_environment_identity_is_derived_not_declared():
    with pytest.raises(ValueError):
        EnvironmentFingerprint.from_mapping({**BASE, "hostname": "box-7"})
    with pytest.raises(ValueError):
        EnvironmentFingerprint.from_mapping({k: v for k, v in BASE.items() if k != "machineId"})
    with pytest.raises(ValueError):
        env(machineId="  ")
    with pytest.raises(TypeError):
        independent_environments(env(), BASE)
    assert environment_id(EnvironmentFingerprint.from_mapping(BASE)) == environment_id(env())


def test_seed_set_identity_is_the_values_not_the_name():
    assert seed_set_id([3, 1, 2]) == seed_set_id([1, 2, 3]) == seed_set_id([1, 1, 2, 3])
    assert seed_set_id([1, 2, 3]) != seed_set_id([1, 2, 4])
    with pytest.raises(ValueError):
        seed_set_id([])
    with pytest.raises(ValueError):
        seed_set_id([1, -2])
    with pytest.raises(ValueError):
        seed_set_id([True])


def test_run_qualification_from_record_derives_both_identities():
    a = RunQualification.from_record(run_id="run-a", spec_hash=SPEC, code_hash=CODE, environment=BASE, seeds=[1, 2, 3])
    b = RunQualification.from_record(run_id="run-b", spec_hash=SPEC, code_hash=CODE, environment=env(), seeds=[3, 2, 1])
    assert a.environment_id == b.environment_id == environment_id(env())
    assert a.seed_set_id == b.seed_set_id
    renamed = c3_run_support([a, b], spec_hash=SPEC, code_hash=CODE)
    assert renamed.qualified_runs == 1


# ------------------------------------------------ Gate 6 reproduction (draft 3)

def test_reproduction_uses_the_same_environment_rule_as_c3():
    original = RunQualification.from_record(run_id="run-0", spec_hash=SPEC, code_hash=CODE, environment=env(), seeds=[1, 2])
    other_machine = RunQualification.from_record(run_id="run-1", spec_hash=SPEC, code_hash=CODE,
                                                 environment=env(machineId="m2"), seeds=[3, 4])
    assert reproduction_status(original, other_machine, within_tolerance=True).status is P
    assert reproduction_status(original, other_machine, within_tolerance=False).status is F
    same_env = RunQualification.from_record(run_id="run-2", spec_hash=SPEC, code_hash=CODE,
                                            environment=env(pythonVersion="3.12.9"), seeds=[3, 4])
    verdict = reproduction_status(original, same_env, within_tolerance=True)
    assert verdict.status is B and any("same execution environment" in p for p in verdict.problems)
    same_seeds = RunQualification.from_record(run_id="run-3", spec_hash=SPEC, code_hash=CODE,
                                              environment=env(machineId="m2"), seeds=[2, 1])
    assert reproduction_status(original, same_seeds, within_tolerance=True).status is B
    other_method = RunQualification.from_record(run_id="run-4", spec_hash=SPEC, code_hash="d" * 64,
                                                environment=env(machineId="m2"), seeds=[9])
    assert reproduction_status(original, other_method, within_tolerance=True).status is B
    assert reproduction_status(original, original, within_tolerance=True).status is B
    with pytest.raises(ValueError):
        reproduction_status(original, other_machine, within_tolerance="yes")
