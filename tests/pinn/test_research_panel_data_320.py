"""3.2.0: what the research panel needs to speak plainly and show progress.

The service adds plain words (``leo_shell/research_words.py``, outside the code identity), a failure
story read from the run's own gate-5b record, and timing: when preparation started, which step it
is on, and when each run phase began. Nothing here changes a verdict; these are view fields only.
"""
import json
from pathlib import Path
from types import SimpleNamespace

from leo_shell import research_words
from leo_shell.research import ResearchService
from leo_shell.research_draft import TEMPLATE, validate_draft
from pinn.research import worker
from pinn.research.storage import digest, read, write


def raw():
    return {"objective": "验证基准", "equation": TEMPLATE["equation"], "domain": [0, 1],
            "boundary": {"left": 0, "right": 0}, "assumptions": [], "missing": [], "conflicts": []}


def make(tmp_path, **kwargs):
    paths = SimpleNamespace(root=tmp_path, user=tmp_path / "user")
    for name in ("code", "python-a", "python-b"):
        (tmp_path / name).mkdir(exist_ok=True)
    options = {"confirm": lambda *_: True, "background": False,
               "draft_provider": lambda frame, prompt: validate_draft(raw(), prompt),
               "runtime": {"codeRoot": str(tmp_path / "code"), "pythonA": str(tmp_path / "python-a"),
                           "pythonB": str(tmp_path / "python-b")}}
    options.update(kwargs)
    return ResearchService(paths, **options)


def call(service, op, task=None, **extra):
    return service.dispatch(op, {"taskId": task and task["taskId"], "expectedVersion": task and task["version"], **extra})


def confirmed(service, frame="f-a"):
    task = call(service, "create", prompt="验证基准", frameId=frame, projectId="p-a")["task"]
    task = call(service, "draft", task)["task"]
    return call(service, "approve_model", task)["task"]


def gate5b(directory, failing_seed=2):
    main = Path(directory) / "work/attempts/main"
    main.mkdir(parents=True, exist_ok=True)
    seeds = [{"metrics": {"AC2D-1": 1.9e-4, "AC2D-9": 7.2e-4}, "failedMust": []} for _ in range(10)]
    seeds[failing_seed] = {"metrics": {"AC2D-1": 3.7e-4, "AC2D-9": 1.079e-3}, "failedMust": ["AC2D-9"]}
    write(main / "gate5b_external.json", {"perSeed": seeds, "thresholds": {"AC2D-1": 1e-3, "AC2D-9": 1e-3}})
    return main


# -- words ---------------------------------------------------------------------------------

def test_the_words_live_outside_the_research_code_identity():
    assert "leo_shell/research_words.py" not in worker.IDENTITY_EXTRAS
    words = research_words.panel_words("poisson2d")
    assert [s["level"] for s in words["claimLadder"]] == ["C0", "C1", "C2", "C3"]
    assert [d["key"] for d in words["dimensions"]] == ["math", "impl", "train", "physics", "external", "repro"]
    assert set(words["phases"]) >= {"main", "tier1", "reproduction", "g6"} and words["family"] == "二维"
    assert research_words.panel_words("annulus")["family"] == "环形"
    assert [s["key"] for s in words["preparationSteps"]] == ["identity", "environments", "claim", "plan"]


def test_a_failure_story_names_the_criterion_the_seeds_and_the_line(tmp_path):
    gate5b(tmp_path)
    failure = {"gate": 5, "observedSignatures": ["sLocalizedError"], "finalState": "STOPPED_THE_LINE",
               "tier1Passed": False, "completion": {"state": "STOPPED", "phase": "main", "exitCode": 3}}
    story = research_words.failure_story(tmp_path, {"state": "STOPPED"}, failure)
    assert "10 个种子里有 1 个没有满足「局部误差（最差一小块区域）」" in story["happened"]
    assert "1.08 × 10⁻³" in story["happened"] and "约定上限 1 × 10⁻³" in story["happened"]
    assert story["criteria"] == [{"criterion": "AC2D-9", "seeds": 1, "worst": 1.079e-3, "name": "局部误差（最差一小块区域）",
                                  "threshold": 1e-3, "total": 10}]
    raws = [f["raw"] for f in story["facts"]]
    assert raws == ["phase main · exit 3", "Gate 5", "sLocalizedError", "Tier-1 FAIL", "STOPPED_THE_LINE"]
    assert all(f["plain"] for f in story["facts"]) and "以此草案新建任务" in story["next"]


def test_a_story_is_still_told_without_any_run_record(tmp_path):
    for state, needle in (("CANCELLED", "被停止"), ("TIMED_OUT", "时间上限"), ("INTERRUPTED", "意外退出")):
        story = research_words.failure_story(tmp_path, {"state": state, "completion": {"state": state, "reason": "WORKER_LOST"}}, None)
        assert needle in story["happened"] and story["criteria"] == []
    # A damaged record only makes the sentence shorter; it never raises.
    (tmp_path / "work/attempts/main").mkdir(parents=True)
    (tmp_path / "work/attempts/main/gate5b_external.json").write_text("{not json", encoding="utf-8")
    assert research_words.failure_story(tmp_path, {"state": "STOPPED"}, {"gate": 5})["happened"]


def test_blocked_claims_get_plain_words_and_keep_their_machine_reason():
    verification = {"blockedClaims": [{"level": "C3", "reason": "no independently qualified C2 runs supplied"},
                                      {"level": "C2", "reason": "something new"}]}
    research_words.annotate_verification(verification)
    first, second = verification["blockedClaims"]
    assert first["reason"] == "no independently qualified C2 runs supplied" and "5 次独立完成" in first["plain"]
    assert "plain" not in second


def test_numbers_are_shown_the_way_people_write_them():
    assert research_words.sci(1e-3) == "1 × 10⁻³" and research_words.sci(1.079e-3) == "1.08 × 10⁻³"
    assert research_words.sci("x") == "x"


# -- service -------------------------------------------------------------------------------

def test_the_service_attaches_words_and_a_story_to_a_stopped_run(tmp_path):
    service = make(tmp_path)
    task = confirmed(service)
    directory = service._directory(task["taskId"])
    task["state"] = "RUNNING"
    task = service._save(directory, task, "TEST_RUNNING")["task"]
    write(directory / "completion.json", {"state": "STOPPED", "phase": "main", "exitCode": 3, "allowedClaims": [], "at": "t"})
    main = gate5b(directory)
    write(main / "RUN_SUMMARY.json", {"finalState": "FAILURE_RECORDED", "trustVector": {"external": "FAIL"},
                                      "failure": {"gate": 5, "observedSignatures": ["sLocalizedError"]}})
    view = call(service, "get", task)
    assert view["words"]["claimLadder"][2]["name"] == "精度声明"
    story = view["verification"]["story"]
    assert story["criteria"][0]["criterion"] == "AC2D-9" and view["verification"]["failure"]["gate"] == 5
    # The verdict fields themselves are untouched.
    assert view["verification"]["verified"] is False and view["verification"]["allowedClaims"] == []


def test_preparation_records_when_it_started_and_the_list_names_the_family(tmp_path):
    def preparing(args, cwd=None, **kwargs):
        task_root = Path(args[args.index("--task-root") + 1])
        state = read(task_root / "state.json")
        assert state["state"] == "PREPARING" and state["preparationStartedAt"].endswith("Z")
        write(task_root / "preparation-progress.json", {"step": "claim", "at": "t"})
        write(task_root / "execution-plan.json", {"taskId": task_root.name, "modelHash": "m"})
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
    service = make(tmp_path, command_runner=preparing)
    task = confirmed(service)
    task = call(service, "prepare", task)["task"]
    assert task["state"] == "READY_FOR_RUN_APPROVAL" and task["preparationStartedAt"]
    listed = call(service, "list", frameId="f-a")["tasks"]
    assert listed[0]["family"] == "poisson1d"
    # Preparation progress is shown only while preparing.
    assert "preparationProgress" not in call(service, "get", task)


def test_an_unmatched_draft_is_listed_without_a_family(tmp_path):
    unmatched = {**raw(), "equation": "-k*u''(x)=x"}
    service = make(tmp_path, draft_provider=lambda frame, prompt: validate_draft(unmatched, prompt))
    task = call(service, "create", prompt="热传导", frameId="f-b", projectId="p-a")["task"]
    call(service, "draft", task)
    assert call(service, "list", frameId="f-b")["tasks"][0]["family"] is None


# -- worker --------------------------------------------------------------------------------

def test_each_run_phase_keeps_its_start_time(tmp_path, monkeypatch):
    task_root = tmp_path / ("research/tasks/research-" + "3" * 32)
    task_root.mkdir(parents=True)
    plan = {"phases": ["main", "tier1", "reproduction", "g6"], "budgetSeconds": 60, "codeManifest": [],
            "pythonA": "a", "pythonB": "b"}
    write(task_root / "state.json", {"state": "RUNNING"})
    write(task_root / "run-approval.json", {"contentHash": digest(plan), "taskId": task_root.name})
    seen = []

    class Child:
        returncode = 0
        def __init__(self, command, **kwargs):
            seen.append(read(task_root / "progress.json"))
        def poll(self):
            return 0
    monkeypatch.setattr(worker, "check_plan", lambda task_root, root: plan)
    monkeypatch.setattr(worker, "scientific_identity", lambda root: [])
    monkeypatch.setattr(worker.subprocess, "Popen", Child)
    monkeypatch.setattr(worker, "verify_attempt", lambda path: {"verified": True})
    monkeypatch.setattr(worker, "tree_hashes", lambda *a, **k: {})
    worker._execute(task_root, tmp_path)
    assert [s["phase"] for s in seen] == plan["phases"]
    last = seen[-1]
    assert [p["phase"] for p in last["phases"]] == plan["phases"] and last["at"] == last["phases"][-1]["startedAt"]
    assert all(p["startedAt"].endswith("Z") for p in last["phases"])
    assert read(task_root / "completion.json")["state"] == "COMPLETED"


def test_preparation_says_which_step_it_is_on(tmp_path, monkeypatch):
    task_root = tmp_path / ("research/tasks/research-" + "4" * 32)
    task_root.mkdir(parents=True)
    write(task_root / "state.json", {"state": "MODEL_CONFIRMED", "modelApproval": {"contentHash": "x"}, "draft": {}})
    steps = []
    real_write = worker.write

    def spy(path, data, **kwargs):
        if Path(path).name == "preparation-progress.json":
            steps.append(data["step"])
        return real_write(path, data, **kwargs)
    monkeypatch.setattr(worker, "write", spy)
    monkeypatch.setattr(worker, "scientific_identity", lambda root: [])
    monkeypatch.setattr(worker, "environment_fingerprint", lambda: {"installationId": "a"})
    monkeypatch.setattr(worker, "_environment", lambda python, root: {"installationId": "b"})
    monkeypatch.setattr("pinn.governance.trust_vector.independent_environments", lambda a, b: True)
    monkeypatch.setattr("pinn.governance.trust_vector.EnvironmentFingerprint.from_mapping", staticmethod(lambda m: m))
    try:
        worker.prepare(task_root, tmp_path, tmp_path)
    except ValueError as error:
        assert str(error) == "MODEL_APPROVAL_REQUIRED"
    assert steps == ["identity", "environments"]
    # The progress file sits beside the task, never inside the evidence tree.
    assert not (task_root / "work").exists() and json.loads((task_root / "preparation-progress.json").read_text("utf-8"))["step"] == "environments"
