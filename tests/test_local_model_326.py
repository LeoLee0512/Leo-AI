"""3.2.6 · The local model: a web search the relay writes itself, thinking shown while it is generated,
and the same four effort levels as DeepSeek (owner, 2026-09-30)."""
import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
import leo_local_relay as relay  # noqa: E402
import leo_reasoning as reasoning  # noqa: E402


def completion(content, finish="stop", thinking=None):
    message = {"role": "assistant", "content": content}
    if thinking is not None:
        message["reasoning_content"] = thinking
    return json.dumps({"id": "chatcmpl-7", "model": relay.MODEL, "object": "chat.completion",
                       "choices": [{"index": 0, "finish_reason": finish, "message": message}]}).encode()


def test_a_search_becomes_the_one_fixed_cell_calling_the_daemons_search():
    action = {"name": "web_search", "arguments": {"query": "最近的 PINN 论文"}}
    out = json.loads(relay.adapt_action_response(completion(json.dumps(action, ensure_ascii=False)), "application/json"))
    content = out["choices"][0]["message"]["content"]
    assert out["choices"][0]["finish_reason"] == "stop" and content.startswith("```python\n") and content.endswith("```")
    code = content[len("```python\n"):-3]
    tree = ast.parse(code)
    calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    # 3.2.9: the count line and one-line titles/snippets add plain string methods, nothing else.
    assert calls[0] == "web_search" and set(calls[1:]) <= {"get", "format", "join", "split"}
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    query = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "web_search").args[0]
    assert query.value == "最近的 PINN 论文"


def test_a_hostile_query_stays_a_string():
    code = relay.web_search_cell('x"); import os; os.system("rm -rf /')
    tree = ast.parse(code)
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "web_search")
    assert call.args[0].value == 'x"); import os; os.system("rm -rf /'


@pytest.mark.parametrize("query", ["", "   ", "a\nb", "x" * 301])
def test_bad_queries_fail_closed(query):
    action = {"name": "web_search", "arguments": {"query": query}}
    with pytest.raises(relay.RelayError):
        relay.adapt_action_response(completion(json.dumps(action)), "application/json")


def test_the_reminder_and_grammar_offer_the_search():
    assert "web_search" in relay.LOCAL_COMPLETION_REMINDER and "不要自己写 requests" in relay.LOCAL_COMPLETION_REMINDER
    names = [o["properties"]["name"]["const"] for o in relay.action_response_format()["json_schema"]["schema"]["anyOf"]]
    assert names == ["finalize_response", "run_scientific_cell", "web_search"]


def sse(value):
    return ("data: " + json.dumps(value, ensure_ascii=False)).encode("utf-8")


def test_thinking_chunks_are_forwarded_and_nothing_else_is():
    thinking = sse({"id": "c1", "model": relay.MODEL, "created": 1,
                    "choices": [{"index": 0, "delta": {"reasoning_content": "先想一下"}, "finish_reason": None}]})
    out = relay.live_reasoning_event(thinking)
    event = json.loads(out.decode("ascii")[6:])
    assert event["choices"][0]["delta"] == {"role": "assistant", "reasoning_content": "先想一下"} and event["id"] == "c1"
    action = sse({"id": "c1", "choices": [{"index": 0, "delta": {"content": '{"name"'}, "finish_reason": None}]})
    done = sse({"id": "c1", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
    for other in (action, done, b"data: [DONE]", b": keep-alive", b"data: not json"):
        assert relay.live_reasoning_event(other) is None


def test_a_streamed_answer_does_not_repeat_thinking_already_shown():
    action = json.dumps({"name": "finalize_response", "arguments": {"summary": "好的。",
                                                                     "completion_bullets": ["Answered the question"]}},
                        ensure_ascii=False)
    raw = completion(action, thinking="先想一下")
    shown = json.loads(relay.adapt_action_response(raw, "application/json", reasoning_streamed=True))
    assert "reasoning_content" not in shown["choices"][0]["message"]
    kept = json.loads(relay.adapt_action_response(raw, "application/json"))
    assert kept["choices"][0]["message"]["reasoning_content"] == "先想一下"


def test_the_local_model_offers_the_same_four_effort_levels_as_deepseek():
    local = reasoning.describe("chatgpt", "local-qwen3-4b", "http://127.0.0.1:8080/v1")
    cloud = reasoning.describe("deepseek", "deepseek-v4-pro", "https://api.deepseek.com")
    offered = lambda d: [c["id"] for c in d["choices"] if c["available"]]  # noqa: E731
    assert offered(local) == offered(cloud) == ["default", "low", "high", "ultra"]
    assert {c["id"]: c["native_value"] for c in local["choices"] if c["available"]} == {
        "default": None, "low": 256, "high": 1024, "ultra": 4096}
    with pytest.raises(reasoning.ReasoningError, match="REASONING_CHOICE_UNAVAILABLE"):
        reasoning.resolve("chatgpt", "local-qwen3-4b", "http://127.0.0.1:8080/v1", "xhigh", local["revision"])
