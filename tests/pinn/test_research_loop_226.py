"""2.2.6: the in-product loop's recovery paths, entitlement checkpoint and blind-set quota.

No model call and no training: preparation and the worker are replaced by fakes that write the
files the real ones write, so each rule the desktop depends on is pinned without a formal run.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from leo_shell.research import ResearchService
from leo_shell.research_draft import TEMPLATE, unfence, validate_draft
from pinn.research import worker
from pinn.research.quota import CLAIM_GRID_CAPACITY, claim_grid_candidates, quota
from pinn.research.storage import read, write


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


def preparing_ok(args, cwd=None, **kwargs):
    """What a successful ``worker prepare`` leaves behind: a reserved grid and a plan."""
    task_root = Path(args[args.index("--task-root") + 1])
    problems = task_root / "work/experiments/poisson1d/problems"
    problems.mkdir(parents=True)
    (problems / f"pdef-{task_root.name}-claim-GL1024-CGL4002.json").write_text("{}", encoding="utf-8")
    write(task_root / "execution-plan.json", {"taskId": task_root.name, "modelHash": "m"})
    return SimpleNamespace(returncode=0, stdout=b"prepared\n", stderr=b"")


# -- drafts --------------------------------------------------------------------------------

def test_a_fenced_json_reply_is_read_and_nothing_else_is_stripped():
    body = '{"objective": "x"}'
    assert unfence("```json\n" + body + "\n```") == body
    assert unfence("```\n" + body + "\n```\n") == body
    assert unfence("  " + body + "  ") == body
    # Prose around a fence is not a draft; it is left for the strict parser to refuse.
    assert unfence("Here it is:\n```json\n" + body + "\n```") .startswith("Here it is")


# -- entitlement checkpoint ------------------------------------------------------------------

def test_the_entitlement_checkpoint_guards_every_costly_operation_and_nothing_else(tmp_path):
    seen = []
    def refuse(operation, context):
        seen.append((operation, dict(context)))
        raise ValueError("ENTITLEMENT_REQUIRED")
    service = make(tmp_path, entitlement=refuse)
    for operation in ("create", "fork", "draft", "prepare", "approve_run"):
        with pytest.raises(ValueError, match="ENTITLEMENT_REQUIRED"):
            call(service, operation, prompt="p", frameId="f-a", projectId="p-a")
    assert [op for op, _ in seen] == ["create", "fork", "draft", "prepare", "approve_run"]
    # Only public identifiers reach the checkpoint: never a prompt or a draft.
    assert all(set(context) == {"taskId", "frameId"} for _, context in seen)
    assert call(service, "list", frameId="f-a") == {"ok": True, "tasks": []}


def test_the_default_checkpoint_allows_everything(tmp_path):
    from leo_shell.entitlements import COSTLY, check
    assert COSTLY == {"create", "fork", "draft", "prepare", "approve_run"}
    for operation in COSTLY:
        assert check(operation, {"taskId": None, "frameId": "f"}) is None


# -- listing ---------------------------------------------------------------------------------

def test_every_conversation_can_be_listed_newest_first(tmp_path, monkeypatch):
    # Timestamps have one-second resolution; give each save its own second.
    ticks = iter(f"2026-09-28T10:00:{n:02d}Z" for n in range(60))
    monkeypatch.setattr("leo_shell.research.utc_now", lambda: next(ticks))
    service = make(tmp_path)
    first = call(service, "create", prompt="a", frameId="f-a", projectId="p")["task"]
    second = call(service, "create", prompt="b", frameId="f-b", projectId="p")["task"]
    assert [t["taskId"] for t in call(service, "list", frameId="f-a")["tasks"]] == [first["taskId"]]
    every = call(service, "list", scope="all")["tasks"]
    assert [t["taskId"] for t in every] == [second["taskId"], first["taskId"]]
    assert {t["frameId"] for t in every} == {"f-a", "f-b"}


# -- preparation -----------------------------------------------------------------------------

def test_preparation_moves_through_preparing_and_reserves_one_grid(tmp_path):
    service = make(tmp_path, command_runner=preparing_ok)
    task = confirmed(service)
    view = call(service, "get", task)
    assert view["canPrepare"] is True and view["quota"] == {"capacity": CLAIM_GRID_CAPACITY, "used": 0, "remaining": CLAIM_GRID_CAPACITY,
                                                        "family": "poisson1d"}
    result = call(service, "prepare", task)
    assert result["task"]["state"] == "READY_FOR_RUN_APPROVAL"
    events = [read(p)["event"] for p in sorted(service._directory(task["taskId"]).glob("events/*.json"))]
    assert events[-2:] == ["PREPARATION_STARTED", "PLAN_PREPARED"]
    view = call(service, "get", result["task"])
    assert view["quota"]["used"] == 1 and view["canPrepare"] is False


def test_a_failed_preparation_keeps_its_grid_and_points_to_a_new_task(tmp_path):
    def fails_after_reserving(args, **kwargs):
        preparing_ok(args, **kwargs)
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"boom\n")
    service = make(tmp_path, command_runner=fails_after_reserving)
    task = call(service, "prepare", confirmed(service))["task"]
    assert task["state"] == "MODEL_CONFIRMED" and task["preparationError"] == "PREPARATION_FAILED_SEE_EVIDENCE"
    assert call(service, "get", task)["canPrepare"] is False
    with pytest.raises(ValueError, match="PREPARATION_ALREADY_EXISTS"):
        call(service, "prepare", task)
    fork = call(service, "fork", task)["task"]
    assert fork["state"] == "DRAFT" and fork["forkedFrom"]["preparationError"] == "PREPARATION_FAILED_SEE_EVIDENCE"


def test_a_preparation_left_behind_by_an_earlier_session_is_marked_interrupted(tmp_path):
    service = make(tmp_path)
    task = confirmed(service)
    directory = service._directory(task["taskId"])
    task["state"] = "PREPARING"
    service._save(directory, task, "PREPARATION_STARTED")
    fresh = make(tmp_path)  # a new app session: no preparation thread of its own
    after = call(fresh, "get", task)["task"]
    assert after["state"] == "MODEL_CONFIRMED" and after["preparationError"] == "PREPARATION_INTERRUPTED"


def test_the_background_preparation_does_not_hold_the_service(tmp_path):
    release = __import__("threading").Event()
    def slow(args, **kwargs):
        release.wait(10)
        return preparing_ok(args, **kwargs)
    service = make(tmp_path, command_runner=slow, background=True)
    task = call(service, "prepare", confirmed(service))["task"]
    assert task["state"] == "PREPARING"
    # While it prepares, the panel can still read and list.
    assert call(service, "get", task)["task"]["state"] == "PREPARING"
    assert len(call(service, "list", frameId="f-a")["tasks"]) == 1
    with pytest.raises(ValueError, match="FORK_REQUIRES_STOPPED_WORKER"):
        call(service, "fork", task)
    release.set()
    for _ in range(200):
        if read(service._directory(task["taskId"]) / "state.json")["state"] != "PREPARING":
            break
        __import__("time").sleep(0.02)
    assert read(service._directory(task["taskId"]) / "state.json")["state"] == "READY_FOR_RUN_APPROVAL"


# -- admission and results -------------------------------------------------------------------

def test_a_stale_plan_is_recorded_so_the_panel_can_offer_a_new_task(tmp_path):
    service = make(tmp_path, command_runner=preparing_ok)
    task = call(service, "prepare", confirmed(service))["task"]
    service.command_runner = lambda *a, **k: SimpleNamespace(returncode=1, stdout=b"", stderr=b"")
    with pytest.raises(ValueError, match="RUN_PLAN_IDENTITY_CHANGED"):
        call(service, "approve_run", task)
    after = read(service._directory(task["taskId"]) / "state.json")
    assert after["state"] == "READY_FOR_RUN_APPROVAL" and after["runBlocked"]["reason"] == "RUN_PLAN_IDENTITY_CHANGED"


def _running(service, task):
    directory = service._directory(task["taskId"])
    task["state"] = "RUNNING"
    return directory, service._save(directory, task, "TEST_RUNNING")["task"]


def test_why_a_run_stopped_travels_with_the_task_and_its_failure_is_shown(tmp_path):
    service = make(tmp_path)
    directory, task = _running(service, confirmed(service))
    write(directory / "completion.json", {"state": "STOPPED", "phase": "main", "exitCode": 3, "allowedClaims": [], "at": "t"})
    main = directory / "work/attempts/main"
    main.mkdir(parents=True)
    write(main / "RUN_SUMMARY.json", {"finalState": "FAILURE_RECORDED", "highestAllowedClaim": "BLOCKED",
        "trustVector": {"external": "FAIL", "train": "PASS"}, "failure": {"gate": 5, "observedSignatures": ["sLocalizedError"], "medians": {}}})
    view = call(service, "get", task)
    assert view["task"]["state"] == "STOPPED"
    assert view["task"]["completion"] == {"state": "STOPPED", "phase": "main", "exitCode": 3, "at": "t"}
    failure = view["verification"]["failure"]
    assert view["verification"]["verified"] is False and view["verification"]["allowedClaims"] == []
    assert failure["gate"] == 5 and failure["observedSignatures"] == ["sLocalizedError"]
    assert failure["trustVector"]["external"] == "FAIL" and failure["completion"]["phase"] == "main"


def test_a_lost_worker_is_named_as_such(tmp_path):
    service = make(tmp_path)
    directory, task = _running(service, confirmed(service))
    write(directory / "worker-owner.json", {"pid": 99999999})
    after = call(service, "get", task)["task"]
    assert after["state"] == "INTERRUPTED" and after["completion"]["reason"] == "WORKER_LOST"


def test_closing_the_app_stops_runs_and_leaves_preparations_to_be_marked(tmp_path):
    service = make(tmp_path)
    run_directory, running = _running(service, confirmed(service))
    other = confirmed(service, frame="f-b")
    other_directory = service._directory(other["taskId"])
    other["state"] = "PREPARING"
    service._save(other_directory, other, "PREPARATION_STARTED")
    service._preparing.add(other["taskId"])
    assert sorted(service.busy_tasks()) == sorted([running["taskId"], other["taskId"]])
    service.stop_for_close()
    assert read(run_directory / "state.json")["state"] == "CANCELLING"
    assert read(run_directory / "cancel-request.json")["reason"] == "APP_CLOSED"
    assert read(other_directory / "state.json")["state"] == "PREPARING"


# -- quota -----------------------------------------------------------------------------------

def test_the_quota_counts_candidate_grids_once_wherever_they_are_recorded(tmp_path):
    research, code = tmp_path / "research", tmp_path / "code"
    task_problems = research / "tasks/research-a/work/experiments/poisson1d/problems"
    task_problems.mkdir(parents=True)
    (task_problems / "pdef-research-a-claim-GL1024-CGL4002.json").write_text("{}")
    (task_problems / "pdef-research-a-claim-pool.json").write_text("{}")
    registered = code / "experiments/poisson1d/problems"
    registered.mkdir(parents=True)
    (registered / "pdef-smoke-claim-GL1056-CGL4004.json").write_text("{}")
    (registered / "pdef-smoke-claim-GL1024-CGL4002.json").write_text("{}")   # same grid, counted once
    (registered / "pdef-poisson1d-cal-v1-claim-GL32-CGL50.json").write_text("{}")  # historical, not a candidate
    assert quota(research) == {"capacity": 32, "used": 1, "remaining": 31, "family": "poisson1d"}
    assert quota(research, code) == {"capacity": 32, "used": 2, "remaining": 30, "family": "poisson1d"}
    assert list(claim_grid_candidates())[:2] == [("GL1024-CGL4002", 1024, 4002), ("GL1056-CGL4004", 1056, 4004)]


# -- worker ----------------------------------------------------------------------------------

def test_a_supervisor_failure_is_recorded_as_stopped_with_its_reason(tmp_path, monkeypatch):
    task_root = tmp_path / ("research/tasks/research-" + "0" * 32)
    task_root.mkdir(parents=True)
    def stale(task_root, root):
        raise ValueError("PLAN_CODE_CHANGED")
    monkeypatch.setattr(worker, "_execute", stale)
    with pytest.raises(ValueError, match="PLAN_CODE_CHANGED"):
        worker.execute(task_root, tmp_path)
    completion = read(task_root / "completion.json")
    assert completion["state"] == "STOPPED" and completion["phase"] == "supervisor" and completion["reason"] == "PLAN_CODE_CHANGED"


def test_a_recorded_completion_is_never_overwritten_by_a_later_error(tmp_path, monkeypatch):
    task_root = tmp_path / ("research/tasks/research-" + "1" * 32)
    task_root.mkdir(parents=True)
    def cancelled_then_crashed(task_root, root):
        write(task_root / "completion.json", {"state": "CANCELLED", "allowedClaims": [], "at": "t"})
        raise RuntimeError("late")
    monkeypatch.setattr(worker, "_execute", cancelled_then_crashed)
    with pytest.raises(RuntimeError):
        worker.execute(task_root, tmp_path)
    assert read(task_root / "completion.json")["state"] == "CANCELLED"


def test_preparation_refuses_a_task_that_is_not_preparing(tmp_path, monkeypatch):
    task_root = tmp_path / ("research/tasks/research-" + "2" * 32)
    task_root.mkdir(parents=True)
    write(task_root / "state.json", {"state": "MODEL_CONFIRMED", "modelApproval": {"contentHash": "x"}, "draft": {}})
    monkeypatch.setattr(worker, "scientific_identity", lambda root: [])
    monkeypatch.setattr(worker, "environment_fingerprint", lambda: {"installationId": "a"})
    monkeypatch.setattr(worker, "_environment", lambda python, root: {"installationId": "b"})
    monkeypatch.setattr("pinn.governance.trust_vector.independent_environments", lambda a, b: True)
    monkeypatch.setattr("pinn.governance.trust_vector.EnvironmentFingerprint.from_mapping", staticmethod(lambda m: m))
    with pytest.raises(ValueError, match="MODEL_APPROVAL_REQUIRED"):
        worker.prepare(task_root, tmp_path, tmp_path)
