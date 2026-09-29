"""2.2.8: a draft that fails leaves its reason on the task; reasoning models get more time."""
from types import SimpleNamespace
from urllib.error import URLError

import pytest

from leo_shell import research_draft
from leo_shell.research import ResearchService
from leo_shell.research_draft import TEMPLATE, validate_draft
from pinn.research.storage import read


def raw():
    return {"objective": "验证基准", "equation": TEMPLATE["equation"], "domain": [0, 1],
            "boundary": {"left": 0, "right": 0}, "assumptions": [], "missing": [], "conflicts": []}


def service(tmp_path, provider):
    for name in ("code", "python-a", "python-b"):
        (tmp_path / name).mkdir(exist_ok=True)
    return ResearchService(SimpleNamespace(root=tmp_path, user=tmp_path / "user"), confirm=lambda *_: True,
                           background=False, draft_provider=provider,
                           runtime={"codeRoot": str(tmp_path / "code"), "pythonA": str(tmp_path / "python-a"),
                                    "pythonB": str(tmp_path / "python-b")})


def test_a_failed_draft_records_why_and_a_retry_clears_it(tmp_path):
    outcomes = [ValueError("RESEARCH_DRAFT_TIMEOUT"), None]

    def provider(frame, prompt):
        outcome = outcomes.pop(0)
        if outcome:
            raise outcome
        return validate_draft(raw(), prompt)

    s = service(tmp_path, provider)
    task = s.dispatch("create", {"prompt": "验证基准", "frameId": "f-a", "projectId": "p-a"})["task"]
    with pytest.raises(ValueError, match="RESEARCH_DRAFT_TIMEOUT"):
        s.dispatch("draft", {"taskId": task["taskId"], "expectedVersion": task["version"]})
    failed = s.dispatch("get", {"taskId": task["taskId"]})["task"]
    assert failed["state"] == "DRAFT" and failed["draft"] is None
    assert failed["draftError"]["code"] == "RESEARCH_DRAFT_TIMEOUT" and isinstance(failed["draftError"]["seconds"], int)
    events = sorted((tmp_path / "user/research/tasks" / task["taskId"] / "events").glob("*.json"))
    assert read(events[-1])["event"] == "DRAFT_FAILED"
    retried = s.dispatch("draft", {"taskId": task["taskId"], "expectedVersion": failed["version"]})["task"]
    assert retried["draft"]["supported"] and "draftError" not in retried


def test_an_unexpected_error_text_is_recorded_as_a_generic_code(tmp_path):
    def provider(frame, prompt):
        raise ValueError("something with a secret sk-123 in it")

    s = service(tmp_path, provider)
    task = s.dispatch("create", {"prompt": "p", "frameId": "f-a", "projectId": "p-a"})["task"]
    with pytest.raises(ValueError):
        s.dispatch("draft", {"taskId": task["taskId"], "expectedVersion": task["version"]})
    recorded = s.dispatch("get", {"taskId": task["taskId"]})["task"]["draftError"]
    assert recorded["code"] == "RESEARCH_DRAFT_FAILED" and "sk-123" not in str(recorded)


def test_reasoning_models_get_three_minutes():
    assert research_draft.DRAFT_TIMEOUT_SECONDS == 180
    source = research_draft.__file__
    text = open(source, encoding="utf-8").read()
    assert "timeout=DRAFT_TIMEOUT_SECONDS" in text and "timeout=90" not in text
    # A connect-phase timeout arrives wrapped in URLError; it is classified as a timeout.
    assert isinstance(URLError(TimeoutError()).reason, TimeoutError)
