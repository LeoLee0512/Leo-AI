"""3.2.3 · The local-model relay: no skill catalog for the 4B model, an answer budget that no longer
cuts ordinary answers at 512 tokens, and every protocol action as one grammar-constrained JSON object
(with native tool_choice this llama.cpp/Qwen3 build wrote prose and looped - measured 2026-09-30).
The llama.cpp calls are replaced by a fake that counts tokens."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
import leo_local_relay as relay  # noqa: E402

CATALOG = "\n".join([
    relay.SKILL_CATALOG_HEADING,
    "These skills exist but their full instructions are NOT loaded yet. Use search_skills when relevant.",
    "",
    "- scvi-tools: Probabilistic single-cell RNA-seq with scvi-tools.",
    "- single-step-retrosynthesis: Generate ranked one-step precursor sets for a product.",
    "- bioSkills collection: 561 pinned third-party bioinformatics recipes are available on demand.",
])
SYSTEM = ("You are the Leo AI workbench.\nUse host.submit_output when done.\nFinishing: call host.submit_output.\n\n"
          + CATALOG + "\n\n# Kernel rules\nRun one cell at a time.")


def test_the_catalog_block_is_dropped_and_everything_else_kept():
    out = relay._without_skill_catalog(SYSTEM)
    assert relay.SKILL_CATALOG_HEADING not in out and "bioSkills" not in out and "scvi-tools" not in out
    assert relay.SKILL_CATALOG_NOTE in out
    assert out.startswith("You are the Leo AI workbench.") and out.endswith("# Kernel rules\nRun one cell at a time.")
    assert "Finishing:" in out and "host.submit_output" in out


def test_text_without_a_recognisable_catalog_is_left_alone():
    assert relay._without_skill_catalog("no catalog here") == "no catalog here"
    # A heading with no list after it is not a catalog block: nothing is cut.
    lonely = relay.SKILL_CATALOG_HEADING + "\nsome prose\n\n# Next\nmore prose"
    assert relay._without_skill_catalog(lonely) == lonely


def test_only_system_messages_are_touched():
    user = {"role": "user", "content": CATALOG}
    parts = {"role": "system", "content": [{"type": "text", "text": SYSTEM}]}
    out = relay.drop_skill_catalog([{"role": "system", "content": SYSTEM}, user, parts])
    assert "bioSkills" not in out[0]["content"] and out[1] is user
    assert "bioSkills" not in out[2]["content"][0]["text"]


class FakeLlama:
    """Answers the relay's template and tokenizer calls; the prompt is n tokens long."""

    def __init__(self, n):
        self.n = n
        self.template_request = None

    def __call__(self, port, route, body):
        if route == "/apply-template":
            self.template_request = body
            return {"prompt": "P"}
        if route == "/tokenize" and body.get("content") == "<think></think>":
            return {"tokens": [151667, 151668]}
        if route == "/tokenize":
            return {"tokens": list(range(self.n))}
        raise AssertionError(route)


def chat(max_tokens=None):
    payload = {"model": relay.MODEL, "messages": [{"role": "system", "content": SYSTEM},
                                                   {"role": "user", "content": "你会什么？列出你能做的事情。"}]}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    return payload


@pytest.mark.parametrize("prompt_tokens, requested, expected", [
    (10_000, None, 2048),     # the reported case: ~10k prompt, an ordinary answer gets 2048, not 512
    (10_000, 4096, 2048),     # never above the cap
    (10_000, 300, 300),       # never above what the caller asked for
    (15_000, None, 1384),     # a long conversation shrinks the budget to what is left
])
def test_the_answer_budget(monkeypatch, prompt_tokens, requested, expected):
    fake = FakeLlama(prompt_tokens)
    monkeypatch.setattr(relay, "local_json", fake)
    body = json.loads(relay.prepare_chat(chat(requested), 8080, 16384))
    assert body["max_tokens"] == expected
    sent = "\n".join(m["content"] for m in body["messages"] if isinstance(m.get("content"), str))
    assert "bioSkills" not in sent and relay.SKILL_CATALOG_NOTE in sent
    assert any(m.get("role") == "user" and "你会什么" in m["content"] for m in body["messages"])


def test_a_prompt_that_leaves_less_than_512_tokens_is_refused_with_a_clear_message(monkeypatch):
    monkeypatch.setattr(relay, "local_json", FakeLlama(16_000))
    with pytest.raises(relay.RelayError, match="本地模型上下文为 16384 tokens"):
        relay.prepare_chat(chat(), 8080, 16384)


def test_every_protocol_turn_asks_for_one_json_action_without_native_tools(monkeypatch):
    fake = FakeLlama(9000)
    monkeypatch.setattr(relay, "local_json", fake)
    body = json.loads(relay.prepare_chat(chat(), 8080, 16384))
    assert "tools" not in body and "tool_choice" not in body and "parallel_tool_calls" not in body
    options = body["response_format"]["json_schema"]["schema"]["anyOf"]
    assert [o["properties"]["name"]["const"] for o in options] == ["finalize_response", "run_scientific_cell", "web_search"]
    # Lengths are checked after generation; in the grammar they slow sampling badly.
    assert "maxLength" not in json.dumps(options) and "minLength" not in json.dumps(options)
    assert body["repeat_penalty"] == relay.LOCAL_REPEAT_PENALTY
    assert "finalize_response" in body["messages"][-1]["content"] and "JSON" in body["messages"][-1]["content"]


def completion(content, finish="stop"):
    return json.dumps({"id": "chatcmpl-1", "model": relay.MODEL, "object": "chat.completion",
                       "choices": [{"index": 0, "finish_reason": finish,
                                    "message": {"role": "assistant", "content": content}}]}).encode()


def test_a_json_answer_becomes_the_native_finalizer():
    action = {"name": "finalize_response", "arguments": {"summary": "我能做科学计算和数据分析。",
                                                         "completion_bullets": ["Answered the question"]}}
    out = json.loads(relay.adapt_action_response(completion(json.dumps(action, ensure_ascii=False)), "application/json"))
    choice = out["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    call = choice["message"]["tool_calls"][0]
    assert call["function"]["name"] == "finalize_response"
    assert json.loads(call["function"]["arguments"])["summary"] == "我能做科学计算和数据分析。"


def test_a_json_cell_becomes_fenced_code_for_the_workbench():
    action = {"name": "run_scientific_cell", "arguments": {"language": "python", "code": "print(2 ** 100)"}}
    out = json.loads(relay.adapt_action_response(completion(json.dumps(action)), "application/json"))
    choice = out["choices"][0]
    assert choice["finish_reason"] == "stop" and "tool_calls" not in choice["message"]
    assert choice["message"]["content"] == "```python\nprint(2 ** 100)\n```"


def test_an_answer_cut_by_the_token_limit_is_kept_and_marked():
    cut = '{"name": "finalize_response", "arguments": {"summary": "2 的 100 次方是 1267650600228229401496' + "0" * 400
    out = json.loads(relay.adapt_action_response(completion(cut, "length"), "application/json"))
    summary = json.loads(out["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])["summary"]
    assert summary.startswith("2 的 100 次方是 1267650600228229401496") and summary.endswith(relay.TRUNCATED_NOTE)
    assert "0" * 60 not in summary  # the runaway repetition is collapsed


@pytest.mark.parametrize("content, finish", [
    ('{"name": "run_scientific_cell", "arguments": {"language": "python", "code": "x = 1\nfor i in', "length"),
    ("我会执行科学计算、数据分析、模拟实验等科学研究任务。", "stop"),
    ("我会执行科学计算、数据分析。我会执行科学计算、数据分析。", "length"),
    ('{"name": "delete_everything", "arguments": {}}', "stop"),
])
def test_cut_cells_prose_and_unknown_actions_fail_closed(content, finish):
    with pytest.raises(relay.RelayError):
        relay.adapt_action_response(completion(content, finish), "application/json")


def test_a_streamed_json_action_is_republished_as_one_native_call():
    action = json.dumps({"name": "finalize_response", "arguments": {"summary": "你好，我是 Leo AI。",
                                                                     "completion_bullets": ["Answered the question"]}},
                        ensure_ascii=False)
    chunks = [action[:20], action[20:]]
    sse = "".join("data: " + json.dumps({"id": "chatcmpl-9", "model": relay.MODEL, "choices": [
        {"index": 0, "delta": {"role": "assistant", "content": part}, "finish_reason": None}]}, ensure_ascii=False) + "\n\n"
        for part in chunks)
    sse += "data: " + json.dumps({"id": "chatcmpl-9", "model": relay.MODEL, "choices": [
        {"index": 0, "delta": {}, "finish_reason": "stop"}]}) + "\n\ndata: [DONE]\n\n"
    out = relay.adapt_action_response(sse.encode("utf-8"), "text/event-stream").decode("ascii")
    events = [json.loads(line[6:]) for line in out.split("\n") if line.startswith("data: {")]
    call = events[0]["choices"][0]["delta"]["tool_calls"][0]
    assert call["function"]["name"] == "finalize_response" and events[1]["choices"][0]["finish_reason"] == "tool_calls"
    assert out.rstrip().endswith("data: [DONE]")


def test_the_local_model_describes_only_what_leo_really_does():
    # Owner, 2026-09-30: the 4B model listed "bioinformatics" when asked what it can do.
    reminder = relay.LOCAL_COMPLETION_REMINDER
    assert "科学计算" in reminder and "PINN" in reminder
    assert "不要提生物信息学" in reminder
