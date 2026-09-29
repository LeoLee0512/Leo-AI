"""2.2.11: the 2D Poisson template in the product loop — draft, quota, plan, budget, guide.

No model call and no training (the parallel trainer is tested under torch in
``test_poisson2d_parallel.py``; the full chain is the sandbox smoke).
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from leo_shell import evidence_guide
from leo_shell.research import PREPARE_TIMEOUT_SECONDS, ResearchService, task_family
from leo_shell.research_draft import (PROMPT, TEMPLATE, TEMPLATE_2D, TEMPLATE_METHOD_2D, TEMPLATES,
                                      equation_matches_template_2d, validate_draft)
from pinn.research import worker
from pinn.research.quota import CLAIM_GRID_CAPACITY, claim_grid_candidates, quota
from pinn.research.storage import read, write

ROOT = Path(__file__).resolve().parents[2]


def raw2d(**change):
    base = {"objective": "二维校准", "equation": TEMPLATE_2D["equation"], "domain": [[0, 1], [0, 1]],
            "boundary": {"left": 0, "right": 0, "bottom": 0, "top": 0}, "assumptions": [], "missing": [], "conflicts": []}
    base.update(change)
    return base


# -- the draft --------------------------------------------------------------------------------------

def test_the_2d_template_is_recognised_and_carries_its_own_method():
    draft = validate_draft(raw2d(), "二维校准")
    assert draft["supported"] is True and draft["templateId"] == "poisson2d-v1"
    assert draft["template"]["method"] == TEMPLATE_METHOD_2D and draft["template"]["solver"] == TEMPLATE_2D["solver"]
    one = validate_draft({**raw2d(), "equation": TEMPLATE["equation"], "domain": [0, 1], "boundary": {"left": 0, "right": 0}}, "x")
    assert one["templateId"] == "poisson1d-v1" and one["template"]["method"]["configId"] == "leo-poisson1d-hard-bc-v1"


@pytest.mark.parametrize("spelling", [
    "-(u_xx+u_yy)=2*pi^2*sin(pi*x)*sin(pi*y)",
    "−(u_xx + u_yy) = 2π² sin(πx) sin(πy)",
    "-Δu = 2π²·sin(πx)·sin(πy)",
    "-∇²u = 2*pi**2*sin(pi*y)*sin(pi*x)",
    "u_xx + u_yy = -2π² sin(πx) sin(πy)",
    "-∂²u/∂x² - ∂²u/∂y² = 2π² sin(πx) sin(πy)",
    "Δu + 2π² sin(πx) sin(πy) = 0",
])
def test_equivalent_spellings_of_the_2d_equation_match(spelling):
    assert equation_matches_template_2d(spelling)


@pytest.mark.parametrize("wrong", [
    "-(u_xx+u_yy)=pi^2*sin(pi*x)*sin(pi*y)",          # wrong amplitude
    "-(u_xx+u_yy)=2*pi^2*sin(2*pi*x)*sin(pi*y)",      # wrong wavenumber
    "-(u_xx-u_yy)=2*pi^2*sin(pi*x)*sin(pi*y)",        # not the Laplacian
    "-u''(x)=pi^2*sin(pi*x)",                          # the 1D equation
])
def test_other_2d_equations_do_not_match(wrong):
    assert not equation_matches_template_2d(wrong)


def test_a_2d_draft_that_misses_the_template_says_why_in_2d_terms():
    draft = validate_draft(raw2d(domain=[[0, 2], [0, 1]], boundary={"left": 0, "right": 1, "bottom": 0, "top": 0}), "q")
    assert draft["supported"] is False and draft["templateId"] is None and draft["template"] is None
    assert draft["unsupportedReasons"] == ["求解区域不是 0 < x < 1、0 < y < 1。", "边界条件不是四条边上 u = 0。"]
    wrong_equation = validate_draft(raw2d(equation="-(u_xx+u_yy)=1"), "q")
    assert wrong_equation["unsupportedReasons"][0].startswith("方程不是已验证二维模板")


def test_booleans_and_mixed_shapes_never_pass_as_the_2d_template():
    assert validate_draft(raw2d(domain=[[False, True], [0, 1]]), "q")["supported"] is False
    assert validate_draft(raw2d(boundary={"left": False, "right": 0, "bottom": 0, "top": 0}), "q")["supported"] is False
    # The 2D equation with a 1D domain and boundary is neither template.
    mixed = validate_draft(raw2d(domain=[0, 1], boundary={"left": 0, "right": 0}), "q")
    assert mixed["supported"] is False and mixed["unsupportedReasons"][0].startswith("求解区域")


def test_the_2d_method_summary_restates_the_frozen_product_config():
    config = json.loads((ROOT / "pinn/research/poisson2d-config.json").read_text(encoding="utf-8"))
    method = TEMPLATE_METHOD_2D
    assert method["configId"] == config["configId"] == "leo-poisson2d-hard-bc-v1"
    network, optimizer, sampling = config["network"], config["optimizer"], config["sampling"]
    assert f"{network['hiddenLayers']} 层 × {network['width']} 神经元" in method["network"]
    assert network["outputParameterization"] == "x(1-x)y(1-y)N" and "x(1−x)y(1−y)·N(x,y)" in method["network"]
    for value in (str(optimizer["steps"]), f"批量 {optimizer['batchSize']}", "1e-3", "1e-5"):
        assert value in method["training"], value
    for value in (sampling["poolSize"], sampling["poolSeed"], sampling["collocationCount"]):
        assert str(value) in method["sampling"]
    assert config["lossWeights"] == {"pde": 1.0} and "权重 1.0" in method["losses"]
    assert f"{config['seedProtocol']['runs']} 个种子" in method["seeds"]
    assert "≤ 1e-3（AC2D-1）" in method["acceptance"] and "AC2D-9" in method["acceptance"]
    assert f"≤ {config['preregistration']['worstSeedFactor']:g} 倍" in method["acceptance"]
    reproduction = config["reproduction"]
    assert f"≤ {reproduction['devRelL2MedianAbsDiff']:.0e}".replace("e-0", "e-") in method["validation"]
    assert f"≤ {reproduction['devRelL2MedianRelDiff']:g} 倍" in method["validation"]


def test_the_product_2d_config_is_the_accepted_calibration_method():
    product = json.loads((ROOT / "pinn/research/poisson2d-config.json").read_text(encoding="utf-8"))
    accepted = json.loads((ROOT / "experiments/poisson2d/configs/exp2d_baseline.json").read_text(encoding="utf-8"))
    for doc in (product, accepted):
        doc.pop("configId"), doc.pop("description")
    assert product == accepted


def test_the_prompt_names_both_verified_problems():
    assert "-(u_xx+u_yy)=2*pi^2*sin(pi*x)*sin(pi*y)" in PROMPT and "-u''(x)=pi^2*sin(pi*x)" in PROMPT
    assert "[[x0, x1], [y0, y1]]" in PROMPT and "bottom" in PROMPT
    assert set(TEMPLATES) == {"poisson1d-v1", "poisson2d-v1"}


# -- the blind grids --------------------------------------------------------------------------------

def test_2d_grids_follow_the_preregistered_construction_rule():
    grids = list(claim_grid_candidates("poisson2d"))
    assert len(grids) == CLAIM_GRID_CAPACITY and grids[0] == ("D2C-GL42-CGL62", 42, 62)
    orders = [gl for _, gl, _ in grids]
    assert len(set(orders)) == len(orders) and all(gl % 2 == 0 and gl >= 42 for gl in orders)
    primes = [cgl - 1 for _, _, cgl in grids]
    assert len(set(primes)) == len(primes)
    for p in primes:
        assert p >= 61 and all(p % d for d in range(2, int(p ** 0.5) + 1)), p
    # Disjoint from the calibration pool members GL32..38 / m-1 in {49, 53, 55, 59}, and from D_phys (GL40).
    assert not {32, 34, 36, 38, 40} & set(orders)
    with pytest.raises(ValueError):
        list(claim_grid_candidates("heat1d"))


def test_1d_and_2d_quotas_are_counted_apart(tmp_path):
    research, code = tmp_path / "research", tmp_path / "code"
    one = research / "tasks/research-a/work/experiments/poisson1d/problems"
    two = research / "tasks/research-b/work/experiments/poisson2d/problems"
    one.mkdir(parents=True), two.mkdir(parents=True)
    (one / "pdef-research-a-claim-GL1024-CGL4002.json").write_text("{}")
    (two / "pdef-research-b-claim-D2C-GL42-CGL62.json").write_text("{}")
    (two / "pdef-research-b-claim-pool.json").write_text("{}")
    registered = code / "experiments/poisson2d/problems"
    registered.mkdir(parents=True)
    (registered / "pdef-poisson2d-cal-v1-claim-D2C-GL32-CGL50.json").write_text("{}")   # calibration, not a candidate
    (registered / "pdef-smoke-claim-D2C-GL44-CGL68.json").write_text("{}")
    assert quota(research, code, "poisson1d") == {"capacity": 32, "used": 1, "remaining": 31, "family": "poisson1d"}
    assert quota(research, code, "poisson2d") == {"capacity": 32, "used": 2, "remaining": 30, "family": "poisson2d"}


# -- the worker -------------------------------------------------------------------------------------

def test_the_families_name_their_config_runner_and_budget():
    assert worker.CONFIG_2D in worker.IDENTITY_EXTRAS and worker.CONFIG in worker.IDENTITY_EXTRAS
    assert worker.family_of({"templateId": "poisson2d-v1"}) == "poisson2d"
    assert worker.family_of({"templateId": "poisson1d-v1"}) == "poisson1d"
    with pytest.raises(ValueError, match="RESEARCH_FAMILY_INVALID"):
        worker.family_of({"templateId": None})
    assert worker.FAMILIES["poisson1d"]["budgetSeconds"] == 3600
    assert worker.FAMILIES["poisson2d"]["budgetSeconds"] == 90 * 60
    assert worker.FAMILIES["poisson2d"]["runner"] == "pinn.experiments2d.runner2d"
    assert 1 <= worker.parallel_workers("poisson2d") <= 10 and worker.parallel_workers("poisson1d") == 1


def test_a_cancelled_phase_is_ended_with_everything_it_started(monkeypatch):
    calls = []
    child = SimpleNamespace(pid=4321, wait=lambda timeout=None: 0, terminate=lambda: calls.append("terminate"),
                            kill=lambda: calls.append("kill"))
    monkeypatch.setattr(worker.subprocess, "run", lambda args, **kw: calls.append(args))
    monkeypatch.setattr(worker.os, "name", "nt")
    worker._stop(child)
    assert calls == [["taskkill", "/T", "/F", "/PID", "4321"]]


def test_a_2d_plan_runs_its_phases_with_the_2d_runner(tmp_path, monkeypatch):
    """phase() takes the family from the plan and hands the attempt the plan's worker count."""
    seen = {}

    class FakeAttempt:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def run(self):
            return {"finalState": "REPRODUCIBILITY_CHECK"}

    fake_runner = SimpleNamespace(Attempt2D=FakeAttempt, LEDGER_DIR=Path("experiments/poisson2d/ledger"))
    monkeypatch.setattr(worker, "_runner", lambda family: fake_runner if family == "poisson2d" else None)
    task_root = tmp_path / ("research/tasks/research-" + "3" * 32)
    task_root.mkdir(parents=True)
    write(task_root / "execution-plan.json", {"family": "poisson2d", "problemId": "pdef-x", "claimMember": "D2C-GL42-CGL62",
                                              "parallelWorkers": 6,
                                              "context": {"codeRoot": str(tmp_path), "dataRoot": str(task_root / "work"),
                                                          "executor": "Leo AI research worker"}})
    assert worker.phase(task_root, tmp_path, "main") is True
    assert seen["workers"] == 6 and seen["claim_pool_member"] == "D2C-GL42-CGL62" and seen["seed_offset"] == 0
    assert seen["config_path"] == tmp_path / worker.CONFIG_2D
    assert seen["ledger_path"] == task_root / "work/experiments/poisson2d/ledger/pdef-x.json"
    worker.phase(task_root, tmp_path, "reproduction")
    assert seen["seed_offset"] == 10000 and seen["reproduction_of"] == task_root / "work/attempts/main"


# -- the desktop service ----------------------------------------------------------------------------

def make(tmp_path, runner):
    paths = SimpleNamespace(root=tmp_path, user=tmp_path / "user")
    for name in ("code", "python-a", "python-b"):
        (tmp_path / name).mkdir(exist_ok=True)
    return ResearchService(paths, confirm=lambda *_: True, background=False, command_runner=runner,
                           draft_provider=lambda frame, prompt: validate_draft(raw2d(), prompt),
                           runtime={"codeRoot": str(tmp_path / "code"), "pythonA": str(tmp_path / "python-a"),
                                    "pythonB": str(tmp_path / "python-b")})


def call(service, op, task=None, **extra):
    return service.dispatch(op, {"taskId": task and task["taskId"], "expectedVersion": task and task["version"], **extra})


def test_a_2d_task_shows_its_own_quota_and_gets_the_longer_preparation(tmp_path):
    timeouts = []

    def preparing(args, cwd=None, timeout=None, **kwargs):
        timeouts.append(timeout)
        task_root = Path(args[args.index("--task-root") + 1])
        problems = task_root / "work/experiments/poisson2d/problems"
        problems.mkdir(parents=True)
        (problems / f"pdef-{task_root.name}-claim-D2C-GL42-CGL62.json").write_text("{}", encoding="utf-8")
        write(task_root / "execution-plan.json", {"taskId": task_root.name, "modelHash": "m"})
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    service = make(tmp_path, preparing)
    task = call(service, "create", prompt="二维校准", frameId="f-a", projectId="p-a")["task"]
    task = call(service, "draft", task)["task"]
    assert task_family(task) == "poisson2d"
    task = call(service, "approve_model", task)["task"]
    view = call(service, "get", task)
    assert view["family"] == "poisson2d" and view["prepareLimitMinutes"] == 15
    assert view["quota"] == {"capacity": 32, "used": 0, "remaining": 32, "family": "poisson2d"}
    call(service, "prepare", task)
    assert timeouts == [PREPARE_TIMEOUT_SECONDS["poisson2d"]] == [900]
    after = call(service, "get", task)
    assert after["quota"]["used"] == 1 and after["quota"]["family"] == "poisson2d"


# -- the reader's guide -----------------------------------------------------------------------------

def test_the_guide_speaks_about_the_2d_problem(tmp_path):
    task_dir = tmp_path / ("research-" + "4" * 32)
    main = task_dir / "work/attempts/main"
    main.mkdir(parents=True)
    write(main / "RUN_SUMMARY.json", {"training": {"runs": 10, "divergent": 0, "median": 3.7e-5, "worst": 5e-5, "successRate": "10/10"},
                                      "claimEvaluation": {"perSeed": [{"AC2D-1": 4.1e-5, "AC2D-9": 1.5e-4}, {"AC2D-1": 6.2e-5}]},
                                      "g6": {"report": {"medianA": 3.7e-5, "medianB": 3.9e-5, "medianAbsDiff": 2e-6}}})
    write(task_dir / "execution-plan.json", {"family": "poisson2d", "createdAt": "2026-09-29T10:00:00Z",
                                             "solverConfiguration": {"preregistration": {"epsilonSpec": 1e-3}},
                                             "expectedTolerance": {"devRelL2MedianAbsDiff": 1e-4, "devRelL2MedianRelDiff": 0.5}})
    problems = task_dir / "work/experiments/poisson2d/problems"
    problems.mkdir(parents=True)
    write(problems / "pdef-x-claim-D2C-GL42-CGL62.json", {"samples": [{}] * 5364})
    verification = {"verified": True, "allowedClaims": ["C0", "C1", "C2"], "blockedClaims": [{"level": "C3"}],
                    "dimensions": {"physics": {"status": "PASS", "checks": [{"checkId": "PH4-symmetry", "status": "PASS"}]},
                                   "repro": {"status": "PASS"}}}
    guide = evidence_guide.build_guide(task_dir, {"taskId": task_dir.name, "prompt": "p"}, verification)
    assert "sin(πx)·sin(πy)" in guide["headline"] and "6.20 × 10⁻⁵" in guide["headline"]
    assert "二维 Poisson 问题" in guide["can"][0] and "5364" in guide["numbers"][0]["text"]
    physics = next(d for d in guide["dimensions"] if d["key"] == "physics")
    assert "x = y" in physics["text"] and physics["checks"][0]["plain"] == "关于对角线 x = y 交换对称"
    assert guide["problem"]["equation"].startswith("−(u_xx + u_yy)")
    assert dict(guide["glossary"])["硬边界"].startswith("把解写成 u = x(1−x)y(1−y)")
