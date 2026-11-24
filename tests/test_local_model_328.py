"""3.2.8 · The local model no longer sees the gateway's GPU note appended to every user message.

Replaying the owner's conversation (「人间四月芳菲尽的下一句」, answered 「山寺空bell」) with the note:
7/10 right at the daemon's temperature; without it 10/10 (2026-09-30)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bridge"))
import leo_local_relay as relay  # noqa: E402

NOTE = ("\n\n[System note: dynamic remote GPU configuration context]\n"
        "Accelerator state for this turn:\n"
        "- Local execution: 1 local GPU(s): NVIDIA GeForce RTX 4060 Laptop GPU; container runtimes: none.\n"
        "- SSH remote execution: no GPU hosts registered.\n"
        "Use `host.accelerator_status()` for the combined machine-readable view; "
        "`host.remote_gpu_status()` describes SSH registrations only.\n"
        "Do not infer that local GPUs are absent from an empty SSH registry, and do "
        "not infer that a model backend is ready merely because hardware is visible.")


def test_the_note_is_removed_and_the_persons_words_are_kept():
    out = relay.drop_gpu_note([{"role": "user", "content": "人间四月芳菲尽的下一句" + NOTE},
                               {"role": "assistant", "content": "山寺桃花始盛开" + NOTE},
                               {"role": "user", "content": [{"type": "text", "text": "床前明月光" + NOTE}]}])
    assert out[0]["content"] == "人间四月芳菲尽的下一句"
    assert out[1]["content"].endswith(NOTE), "only user messages carry the gateway note"
    assert out[2]["content"][0]["text"] == "床前明月光"


def test_text_that_only_resembles_the_note_is_left_alone():
    partial = "关于 GPU：[System note: dynamic remote GPU configuration context] 这是我自己写的"
    assert relay.drop_gpu_note([{"role": "user", "content": partial}])[0]["content"] == partial
    middle = "前面" + NOTE + "\n后面还有我自己的话"
    assert relay.drop_gpu_note([{"role": "user", "content": middle}])[0]["content"] == middle


class FakeLlama:
    def __call__(self, port, route, body):
        if route == "/apply-template":
            self.messages = body["messages"]
            return {"prompt": "P"}
        if route == "/tokenize" and body.get("content") == "<think></think>":
            return {"tokens": [151667, 151668]}
        return {"tokens": list(range(9000))}


def test_the_relay_sends_the_question_without_the_note(monkeypatch):
    fake = FakeLlama()
    monkeypatch.setattr(relay, "local_json", fake)
    payload = {"model": relay.MODEL, "messages": [
        {"role": "system", "content": "host.submit_output ... Finishing: ..."},
        {"role": "user", "content": "人间四月芳菲尽的下一句" + NOTE}]}
    body = json.loads(relay.prepare_chat(payload, 8080, 16384))
    users = [m["content"] for m in body["messages"] if m["role"] == "user"]
    assert users == ["人间四月芳菲尽的下一句"]
    # Greetings are still recognised with the note present (they are matched on the original payload).
    assert relay.introduction_answer({"messages": [{"role": "user", "content": "你好" + NOTE}]}) is not None
