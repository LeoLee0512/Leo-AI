"""3.2.11 · 「用量」: temperature per model, context, tokens and cache hits (owner, 2026-09-30:
「可以调节温度，查看上下文，查看消耗的token、缓存命中率等」)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge"))
import leo_local_relay as relay  # noqa: E402
import leo_reasoning as reasoning  # noqa: E402
from leo_shell import workbench  # noqa: E402
from leo_shell.model_usage import ModelUsage  # noqa: E402


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI4S_DATA_DIR", str(tmp_path))
    return tmp_path


# -- temperature ------------------------------------------------------------------------------------

def test_a_temperature_is_kept_per_model(data_dir):
    reasoning.set_model_temperature("deepseek-v4-pro", 0.3)
    reasoning.set_model_temperature("local-qwen3-4b", 1.2)
    assert reasoning.model_temperature("deepseek-v4-pro") == 0.3
    assert reasoning.model_temperature("local-qwen3-4b") == 1.2
    reasoning.set_model_temperature("deepseek-v4-pro", None)
    assert reasoning.model_temperatures() == {"local-qwen3-4b": 1.2}
    assert json.loads((data_dir / reasoning.TEMPERATURE_FILE).read_text())["version"] == 1


@pytest.mark.parametrize("value", [-0.1, 1.51, float("nan"), float("inf"), True, "0.5"])
def test_out_of_range_temperatures_are_refused(data_dir, value):
    with pytest.raises(reasoning.ReasoningError):
        reasoning.set_model_temperature("deepseek-chat", value)


def test_a_damaged_file_means_the_default(data_dir):
    (data_dir / reasoning.TEMPERATURE_FILE).write_text("{not json")
    assert reasoning.model_temperatures() == {}
    (data_dir / reasoning.TEMPERATURE_FILE).write_text(json.dumps({"version": 1, "models": {"a": 9, "b": 0.4}}))
    assert reasoning.model_temperatures() == {"b": 0.4}


def cfg(temperature=0.7):
    return SimpleNamespace(provider="chatgpt", temperature=temperature, reasoning_choice="default",
                           reasoning_capability_revision=None, reasoning_snapshot=None)


def test_the_setting_replaces_only_the_daemons_default_temperature(data_dir):
    reasoning.set_model_temperature("deepseek-chat", 0.2)
    sent = reasoning.apply_request({"model": "deepseek-chat", "temperature": 0.7}, cfg(), "https://api.deepseek.com", "deepseek-chat")
    assert sent["temperature"] == 0.2
    # Titles (0.3) and compaction (0.2) ask for their own temperature; that stays.
    title = reasoning.apply_request({"model": "deepseek-chat", "temperature": 0.3}, cfg(), "https://api.deepseek.com", "deepseek-chat")
    assert title["temperature"] == 0.3
    other = reasoning.apply_request({"model": "other", "temperature": 0.7}, cfg(), "https://api.deepseek.com", "other")
    assert other["temperature"] == 0.7


def test_the_local_model_gets_its_temperature_too(data_dir):
    reasoning.set_model_temperature("local-qwen3-4b", 0.1)
    sent = reasoning.apply_request({"model": "local-qwen3-4b", "temperature": 0.7}, cfg(),
                                   "http://127.0.0.1:43210/v1", "local-qwen3-4b")
    assert sent["temperature"] == 0.1 and sent["leo_reasoning_level"] == "default"


def test_the_command_line_leo_runs(data_dir, capsys):
    assert reasoning.main(["set-temperature", "deepseek-chat", "0.4"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] and out["data"]["temperatures"] == {"deepseek-chat": 0.4} and out["data"]["default"] == 0.7
    assert reasoning.main(["clear-temperature", "deepseek-chat"]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["temperatures"] == {}
    assert reasoning.main(["set-temperature", "deepseek-chat", "hot"]) == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "TEMPERATURE_INVALID"


# -- the local model's latest request ---------------------------------------------------------------

def test_the_request_splits_into_instructions_history_and_question():
    parts = relay.record_parts([
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "第一问"},
        {"role": "assistant", "content": None, "tool_calls": [{"function": {"name": "finalize_response", "arguments": "{\"summary\":\"答\"}"}}]},
        {"role": "user", "content": "第二问"},
        {"role": "assistant", "content": "```python\nprint(1)\n```"},
        {"role": "user", "content": "[Observation]\nstdout:\n1"},
        {"role": "system", "content": "REMINDER"}])
    assert parts["system"] == "SYS\nREMINDER"
    assert parts["question"] == "第二问"
    assert "第一问" in parts["history"] and "finalize_response" in parts["history"] and "[Observation]" in parts["history"]


class FakeLlama:
    def __call__(self, port, route, body):
        if route == "/apply-template":
            return {"prompt": "<|im_start|>system\nSYS...<|im_start|>user\n你好吗<|im_end|>"}
        if route == "/tokenize" and body.get("content") == "<think></think>":
            return {"tokens": [151667, 151668]}
        if route == "/tokenize" and body.get("add_special") is False:
            return {"tokens": list(range(len(body["content"])))}
        return {"tokens": list(range(9000))}


def payload(text):
    return {"model": relay.MODEL, "messages": [
        {"role": "system", "content": "host.submit_output ... Finishing: ..."}, {"role": "user", "content": text}]}


def test_the_latest_main_request_is_recorded_and_read_back(data_dir, monkeypatch, capsys):
    monkeypatch.setattr(relay, "local_json", FakeLlama())
    monkeypatch.setattr(relay, "RECORD_PATH", relay._default_record_path())
    relay.prepare_chat(payload("你好吗今天"), 8080, 16384)
    assert relay.print_last_request() == 0
    record = json.loads(capsys.readouterr().out)["data"]["request"]
    assert record["prompt_tokens"] == 9000 and record["context"] == 16384
    assert record["parts"]["question"] == len("你好吗今天") and record["parts"]["system"] > 0
    assert record["text"].startswith("<|im_start|>system")
    assert oct((data_dir / "leo-local-last-request.json").stat().st_mode & 0o777) in ("0o600", "0o666")


def test_side_requests_do_not_replace_the_record(data_dir, monkeypatch):
    monkeypatch.setattr(relay, "local_json", FakeLlama())
    monkeypatch.setattr(relay, "RECORD_PATH", relay._default_record_path())
    relay.prepare_chat({"model": relay.MODEL, "messages": [{"role": "user", "content": "给这段对话起个标题"}]}, 8080, 16384)
    assert not (data_dir / "leo-local-last-request.json").exists()


def test_no_record_is_written_unless_the_relay_is_running(data_dir, monkeypatch):
    monkeypatch.setattr(relay, "local_json", FakeLlama())
    assert relay.RECORD_PATH is None
    relay.prepare_chat(payload("你好吗"), 8080, 16384)
    assert not (data_dir / "leo-local-last-request.json").exists()


def test_reading_before_any_request_gives_nothing(data_dir, capsys):
    assert relay.print_last_request() == 0
    assert json.loads(capsys.readouterr().out)["data"]["request"] == {}


# -- the page's data ----------------------------------------------------------------------------------

def test_context_and_call_usage_reach_the_page_as_numbers_only():
    assert workbench.route({"operation": "context", "frameId": "f-1"}) == ("GET", "/frames/f-1/context", None)
    shaped = workbench.shape_context({"token_count": 9100, "token_limit": 16384, "output_reserve": 0, "message_count": 7,
                                      "compaction_count": 0, "layers": [
                                          {"kind": "system_prompt", "token_count": 7000, "name": "System Prompt"},
                                          {"kind": "text", "token_count": 2100}, {"kind": "images", "token_count": 0},
                                          {"kind": "secret", "token_count": 5}]})
    assert shaped["limit"] == 16384 and shaped["estimate"] == 9100
    assert shaped["layers"] == [{"kind": "system_prompt", "label": "系统提示", "tokens": 7000},
                                {"kind": "text", "label": "对话文字", "tokens": 2100}]
    timeline = workbench.shape_timeline({"groups": [{"kind": "finalize", "model": "deepseek-v4-pro", "usage": {
        "input_tokens": 15460, "output_tokens": 32, "cache_read": 15360, "cache_write": 0, "total_tokens": 15492, "note": "x"}}]})
    assert timeline["groups"][0]["usage"] == {"input": 15460, "output": 32, "cacheRead": 15360}
    assert timeline["groups"][0]["model"] == "deepseek-v4-pro"


class Runner:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        return SimpleNamespace(stdout=json.dumps(self.reply, ensure_ascii=False).encode("utf-8"), returncode=0)


def test_leo_asks_wsl_for_temperatures_with_the_bridge_scripts(tmp_path):
    runner = Runner({"ok": True, "data": {"temperatures": {"deepseek-chat": 0.4, "bad\n": 1}, "default": 0.7}})
    usage = ModelUsage(tmp_path, "Ubuntu", runner=runner)
    result = usage.handle({"operation": "model_temperature_set", "model": "deepseek-chat", "value": 0.4})
    assert result == {"temperatures": {"deepseek-chat": 0.4}, "default": 0.7, "min": 0.0, "max": 1.5}
    argv = runner.calls[-1]
    assert argv[:3] == ["wsl.exe", "-d", "Ubuntu"] and argv[-4:] == [argv[-4], "set-temperature", "deepseek-chat", "0.4"]
    assert argv[-4].endswith("/leo_reasoning.py") and "-I" in argv
    usage.handle({"operation": "model_temperature_set", "model": "deepseek-chat", "value": None})
    assert runner.calls[-1][-2:] == ["clear-temperature", "deepseek-chat"]
    for bad in ({"model": "", "value": 0.5}, {"model": "m", "value": 2}, {"model": "m", "value": "0.5"}):
        with pytest.raises(ValueError):
            usage.handle({"operation": "model_temperature_set", **bad})


def test_the_latest_request_is_shaped_for_the_page(tmp_path):
    runner = Runner({"ok": True, "data": {"request": {"version": 1, "at": 1790000000, "context": 16384, "prompt_tokens": 9000,
                                                      "max_tokens": 2048, "parts": {"system": 7000, "history": 1500, "question": 12},
                                                      "text": "全文", "truncated": False}}})
    hidden = ModelUsage(tmp_path, runner=runner).handle({"operation": "local_last_request"})
    assert hidden["request"]["promptTokens"] == 9000 and hidden["request"]["text"] == ""
    result = ModelUsage(tmp_path, runner=runner).handle({"operation": "local_last_request", "promptTokens": 9000})
    assert result["request"]["parts"] == {"system": 7000, "history": 1500, "question": 12}
    assert result["request"]["promptTokens"] == 9000 and result["request"]["text"] == "全文"
    other = ModelUsage(tmp_path, runner=runner).handle({"operation": "local_last_request", "promptTokens": 100})
    assert other["request"]["text"] == "" and other["request"]["parts"]["question"] == 12
    assert "-I" not in runner.calls[-1] and runner.calls[-1][-1] == "last-request"


def test_without_the_bridge_folder_the_panel_says_unavailable():
    with pytest.raises(ValueError, match="WORKBENCH_USAGE_UNAVAILABLE"):
        ModelUsage(None).handle({"operation": "model_temperatures"})


def test_the_page_has_the_usage_panel():
    html = (ROOT / "stage" / "workbench.html").read_text(encoding="utf-8")
    js = (ROOT / "stage" / "workbench.js").read_text(encoding="utf-8")
    for ident in ("usage-button", "usage-pop", "usage-temp", "usage-bar", "usage-hit", "fulltext-dialog"):
        assert f'id="{ident}"' in html
    assert "request('model_temperature_set'" in js and "request('context'" in js and "request('local_last_request'" in js
