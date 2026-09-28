"""WSL loopback adapter for the Windows-only local llama.cpp service.

No external socket, pip dependency, model copy, or WSL networking change is
needed. Windows curl transports requests over WSL interop pipes. Both HTTP
servers bind to 127.0.0.1. A per-launch token protects this temporary adapter;
the parent holds stdin open and EOF shuts it down. Nothing is logged to disk.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if __package__:
    from .leo_reasoning import ReasoningError, describe, resolve
else:
    from leo_reasoning import ReasoningError, describe, resolve

MODEL = "local-qwen3-4b"
MAX_BODY = 2 * 1024 * 1024
MAX_RESPONSE = 8 * 1024 * 1024
CURL = "/mnt/c/Windows/System32/curl.exe"
LOCAL_COMPLETION_REMINDER = """

[Leo 本地模型的工作台协议]
本次传输提供两个私有协议动作，每次响应必须且只能选择其中一个。
普通回答已经准备好、不需要执行科学工作时，调用 finalize_response。
summary 是给用户的完整答案，completion_bullets 固定为 ["Answered the question"]。
summary 只写公开答案，不要附加 <think> 或 </think> 等思考协议标签；用户明确询问标签本身时保留原文引用。
用户说“只回答”或“不用工具”时，不要为回答运行计算；仍用 finalize_response
提交答案。这是回答的传输格式，不是额外计算或研究工具。
科学计算、文件操作或其他真实工作尚未完成时，选择 run_scientific_cell，
language 选择 python 或 r，code 填写遵循既有指令的一段真实代码，不带代码围栏。
该动作会交给原工作台实际执行，必须查看真实执行结果再继续，不得假称已经执行。
科学任务的 host.submit_output 仍放在真实 Python 代码中；完成要点必须以过去时
动作词开头，例如 ["Computed the result"]。不要 import host。
科学结果提交必须使用两个独立参数：host.submit_output({"summary": str(result)}, ["Computed the result"])。
第一个参数是结果字典，第二个参数是完成要点列表；不要把 completion_bullets 混入结果字典。
必须先真实计算 result，再调用 submit_output；如果它返回 error，先修复错误再提交，不能宣称完成。
不得捏造计算、工具执行、附件、指标或完成证据。不要在协议动作之外输出文字。
"""


def uses_native_protocol(payload: dict) -> bool:
    """Only the existing no-native workbench main loop gets this dialect.

    Titles, compaction, plan requests and caller-owned native tool catalogues
    retain their original wire contract. This does not advertise general
    native-tool support for the local model or change cloud capabilities.
    """
    return not payload.get("tools") and any(
        isinstance(message, dict) and message.get("role") == "system"
        and isinstance(message.get("content"), str)
        and "host.submit_output" in message["content"]
        and "Finishing:" in message["content"]
        for message in payload.get("messages", [])
    )


def native_protocol_tools() -> list[dict]:
    """A closed conversational subset of upstream's finalizer plus real cells.

    Fixed bullets avoid small-model factual sentences failing the upstream's
    completed-action validator. The model still generates the whole call;
    this adapter never constructs a completion from ordinary prose. Scientific
    completion and its richer evidence remain on the original host path.
    """
    return [
        {"type": "function", "function": {
            "name": "finalize_response",
            "description": "Submit a completed conversational answer without executing code. This is the response envelope, not a research tool. Never claim unperformed scientific work; use run_scientific_cell for work that remains.",
            "strict": False,
            "parameters": {"type": "object", "properties": {
                "summary": {"type": "string", "minLength": 1, "maxLength": 4000,
                            "description": "The exact complete user-visible answer."},
                "completion_bullets": {"type": "array", "items": {
                    "type": "string", "enum": ["Answered the question"]},
                    "minItems": 1, "maxItems": 1}},
                "required": ["summary", "completion_bullets"], "additionalProperties": False}}},
        {"type": "function", "function": {
            "name": "run_scientific_cell",
            "description": "Execute one real Python or R cell through the existing scientific workbench. Use when computation or other work remains. Inspect its actual result before completion. Python may use the existing host API, including host.submit_output for scientific completion.",
            "strict": False,
            "parameters": {"type": "object", "properties": {
                "language": {"type": "string", "enum": ["python", "r"]},
                "code": {"type": "string", "minLength": 1, "maxLength": 32768,
                         "description": "Actual code to execute, without markdown fences."}},
                "required": ["language", "code"], "additionalProperties": False}}},
    ]


class RelayError(Exception):
    def __init__(self, message: str, status: int = 502):
        self.status = status
        super().__init__(message)


def _user_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content
                         if isinstance(part, dict) and isinstance(part.get("text"), str))
    return ""


_INTRODUCTION_PATTERN = (
    r"(?P<request>hi|hello|hey|who are you|what is your name|你好|您好|你是谁|你叫什么名字)"
    r"[\s!?？！。．.，,]*"
)
_GATEWAY_LOCAL_CONTEXT_PATTERN = (
    r"\n\n\[System note: dynamic remote GPU configuration context\]\n"
    r"Accelerator state for this turn:\n"
    r"- Local execution: [0-9]+ local GPU\(s\): [^\r\n]+; container runtimes: [^\r\n]+\.\n"
    r"- SSH remote execution: no GPU hosts registered\.\n"
    r"Use `host\.accelerator_status\(\)` for the combined machine-readable view; "
    r"`host\.remote_gpu_status\(\)` describes SSH registrations only\.\n"
    r"Do not infer that local GPUs are absent from an empty SSH registry, and do "
    r"not infer that a model backend is ready merely because hardware is visible\."
)


def introduction_answer(payload: dict) -> str | None:
    """Recognize the exact identity vocabulary in the actual gateway envelope.

    The gateway appends its local accelerator context to user text. Recognize
    that complete, known structure for routing only; never split an arbitrary
    marker or remove any message from the model input. Unrecognized context,
    task-mode instructions, attachments and substantive requests stay on the
    normal path. These short identity templates implement the product name
    requested by the user; they never claim computation or other work.
    """
    for message in reversed(payload.get("messages", [])):
        if isinstance(message, dict) and message.get("role") == "user":
            match = re.fullmatch(
                _INTRODUCTION_PATTERN + "(?:" + _GATEWAY_LOCAL_CONTEXT_PATTERN + ")?",
                _user_text(message).strip(), re.IGNORECASE,
            )
            if match is None:
                return None
            request = match["request"].lower()
            if request in {"hi", "hello", "hey"}:
                return "Hello, I am Leo AI."
            if request in {"who are you", "what is your name"}:
                return "I am Leo AI."
            if request in {"你好", "您好"}:
                return "你好，我是Leo AI。"
            return "我是Leo AI。"
    return None


def is_simple_introduction(payload: dict) -> bool:
    return introduction_answer(payload) is not None


def preserve_think_literals(payload: dict) -> bool:
    # User text and tool-read source material can both contain literal tags.
    # Exclude system instructions and old assistant narration so one historic
    # malformed self-introduction cannot permanently disable the safeguard.
    return any(isinstance(message, dict) and message.get("role") in {"user", "tool", "function"}
               and re.search(r"think|思考标签|推理标签", _user_text(message), re.IGNORECASE)
               for message in payload.get("messages", []))


def introduction_response_format(answer: str | None = None) -> dict:
    """A model-generated complete action, never a prose-to-answer fallback."""
    arguments = native_protocol_tools()[0]["function"]["parameters"]
    if answer is not None:
        arguments["properties"]["summary"]["const"] = answer
    return {"type": "json_schema", "json_schema": {
        "name": "leo_introduction", "strict": True, "schema": {
            "type": "object", "properties": {
                "name": {"const": "finalize_response"},
                "arguments": arguments,
            }, "required": ["name", "arguments"], "additionalProperties": False,
        },
    }}


def _clean_think_suffix(text: str, *, preserve_literals: bool) -> str:
    """Remove only an unpaired trailing model control token in plain prose."""
    if (preserve_literals or "<think>" in text or "</think>" not in text
            or any(mark in text for mark in ("`", "~", '"', "'", "“", "”", "‘", "’"))
            or any(line.lstrip().startswith(">") for line in text.splitlines())):
        return text
    match = re.search(r"</think>(\s*)\Z", text)
    if match is None or text.count("</think>") != 1:
        return text
    return text[:match.start()] + match.group(1)


def curl_args(port: int, route: str, method: str, body: bytes | None) -> list[str]:
    # -q must be first: never read user .curlrc. No redirects, proxies, cookies,
    # credentials or arbitrary destinations are accepted from the client.
    args = [CURL, "-q", "--noproxy", "*", "--proto", "=http",
            "--connect-timeout", "5", "--max-time", "180", "--silent",
            "--show-error", "--no-buffer", "--include", "--request", method]
    if body is not None:
        args += ["--header", "Content-Type: application/json", "--data-binary", "@-"]
    return args + [f"http://127.0.0.1:{port}{route}"]


def split_response(data: bytes) -> tuple[int, dict[str, str], bytes]:
    head, separator, body = data.partition(b"\r\n\r\n")
    if not separator:
        head, separator, body = data.partition(b"\n\n")
    if not separator:
        raise RelayError("Local model returned an incomplete HTTP response.")
    status, headers = parse_headers(head)
    return status, headers, body


def parse_headers(head: bytes) -> tuple[int, dict[str, str]]:
    if len(head) > 32768:
        raise RelayError("Local model headers are too large.")
    lines = head.decode("iso-8859-1").splitlines()
    try:
        status = int(lines[0].split()[1])
        if not 200 <= status <= 599:
            raise ValueError
        headers = {}
        for line in lines[1:]:
            # Streaming transport includes the HTTP header terminator, while
            # split_response passes only the block before that terminator.
            if not line:
                break
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        return status, headers
    except (ValueError, IndexError) as exc:
        raise RelayError("Local model returned invalid HTTP headers.") from exc


def local_json(port: int, route: str, body: dict) -> dict:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        proc = subprocess.run(curl_args(port, route, "POST", encoded), input=encoded,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              timeout=40, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RelayError("Local model token counting is unavailable.") from exc
    if proc.returncode or len(proc.stdout) > MAX_RESPONSE:
        raise RelayError("Local model token counting failed.")
    status, _, raw = split_response(proc.stdout)
    if status != 200:
        raise RelayError("Local model rejected the chat template. Text-only input is supported.", 400)
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, UnicodeDecodeError) as exc:
        raise RelayError("Local model returned invalid token data.") from exc


def prepare_chat(payload: object, port: int, context: int) -> bytes:
    if not isinstance(payload, dict) or payload.get("model") != MODEL:
        raise RelayError("This local connection only serves local-qwen3-4b.", 400)
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise RelayError("A nonempty messages array is required.", 400)
    for message in messages:
        if not isinstance(message, dict):
            raise RelayError("Invalid chat message.", 400)
        content = message.get("content")
        if isinstance(content, list) and any(not isinstance(p, dict) or p.get("type") != "text" for p in content):
            raise RelayError("This 4B local model accepts text only; remove images or attachments.", 400)
    # The gateway validates its admission snapshot against the relay endpoint.
    # Re-resolve only the private choice against this fixed local model here;
    # neither internal metadata nor an arbitrary native budget reaches llama.
    endpoint = f"http://127.0.0.1:{port}/v1"
    try:
        capability = describe("local", MODEL, endpoint)
        reasoning = resolve("local", MODEL, endpoint,
                            payload.get("leo_reasoning_level", "default"), capability["revision"])
    except ReasoningError as exc:
        raise RelayError(str(exc), 400) from exc
    thinking = reasoning["choice"] != "default"
    result = dict(payload)
    result.pop("leo_reasoning_level", None)
    for key in ("thinking_budget_tokens", "reasoning_budget_tokens"):
        result.pop(key, None)
    if uses_native_protocol(payload):
        # Preserve every original message verbatim, and count the complete
        # protocol/tool schemas in the same llama template used for generation.
        identity_answer = introduction_answer(payload)
        simple_introduction = identity_answer is not None
        reminder = LOCAL_COMPLETION_REMINDER
        if simple_introduction:
            reminder = (
                "This request is a simple greeting or identity question. Produce only one JSON object "
                "matching the response schema with name=finalize_response and arguments containing "
                "the exact product identity answer fixed by that schema. Your application name is Leo AI. "
                "Do not execute code. Do not add prose outside JSON."
            )
        result["messages"] = list(messages) + [{"role": "system", "content": reminder}]
        if simple_introduction:
            # A named native tool choice can produce plain prose on this local
            # template; short greetings can also loop before opening a native
            # call. JSON grammar constrains the whole model-generated action.
            # We accept it only with a complete stop/DONE and validate the same
            # finalizer arguments before translating its transport envelope.
            # llama.cpp 5266f24da's autoparser puts its reasoning parser before
            # the JSON content schema. Explicit thinking therefore keeps this
            # grammar; only provider-separated reasoning_content is retained.
            for key in ("tools", "tool_choice", "parallel_tool_calls"):
                result.pop(key, None)
            result["response_format"] = introduction_response_format(identity_answer)
        else:
            result["tools"] = native_protocol_tools()
            result["tool_choice"] = "required"
            result["parallel_tool_calls"] = False
        if not thinking and not preserve_think_literals(payload):
            # enable_thinking=False alone does not stop this local Qwen build
            # from emitting a stray closing token or looping on old closers.
            # Ask the actual tokenizer for its two control IDs, never assume
            # IDs from a different checkpoint. User requests about the literal
            # tags bypass this constraint entirely.
            control_tokens = local_json(port, "/tokenize", {
                "content": "<think></think>", "add_special": False,
                "parse_special": True, "with_pieces": False,
            }).get("tokens")
            if (not isinstance(control_tokens, list) or len(control_tokens) != 2
                    or any(type(token) is not int or token < 0 for token in control_tokens)
                    or len(set(control_tokens)) != 2):
                raise RelayError("Local reasoning control tokens could not be verified.")
            bias = result.get("logit_bias") or {}
            if not isinstance(bias, dict):
                raise RelayError("Local logit_bias must be an object.", 400)
            result["logit_bias"] = {**bias, **{str(token): -100 for token in control_tokens}}
    requested = result.pop("max_completion_tokens", result.get("max_tokens", 512))
    if type(requested) is not int or requested <= 0:
        raise RelayError("max_tokens must be a positive integer.", 400)
    if thinking:
        for key in reasoning["remove_fields"]:
            result.pop(key, None)
        result.update(reasoning["payload"])
        # A thinking budget is per reasoning block, not promised effort or
        # answer length. Bound the entire completion and reserve 512 tokens
        # beyond that budget, including its forced closer/protocol overhead.
        result["max_tokens"] = reasoning["native_value"] + 512
        result["reasoning_format"] = "deepseek"
        if result.get("logit_bias") is not None:
            bias = result["logit_bias"]
            if not isinstance(bias, dict):
                raise RelayError("Local logit_bias must be an object.", 400)
            control_tokens = local_json(port, "/tokenize", {
                "content": "<think></think>", "add_special": False,
                "parse_special": True, "with_pieces": False,
            }).get("tokens")
            if (not isinstance(control_tokens, list) or len(control_tokens) != 2
                    or any(type(token) is not int or token < 0 for token in control_tokens)
                    or len(set(control_tokens)) != 2):
                raise RelayError("Local reasoning control tokens could not be verified.")
            result["logit_bias"] = {key: value for key, value in bias.items()
                                    if str(key) not in {str(token) for token in control_tokens}}
    else:
        result["max_tokens"] = min(requested, 512)
        result["chat_template_kwargs"] = {"enable_thinking": False}
        result["reasoning_effort"] = "none"
    # Do not silently discard tools, instructions or old user messages. The
    # upstream workbench owns history management; reject impossible requests.
    template = local_json(port, "/apply-template", result)
    prompt = template.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise RelayError("Local chat template is unavailable.")
    tokens = local_json(port, "/tokenize", {"content": prompt, "add_special": True,
                                           "parse_special": True, "with_pieces": False}).get("tokens")
    if (not isinstance(tokens, list) or not tokens
            or any(type(token) is not int or token < 0 for token in tokens)):
        raise RelayError("Local token count is unavailable.")
    if len(tokens) + result["max_tokens"] > context:
        raise RelayError(
            f"本地模型上下文为 {context} tokens；本次输入需要 {len(tokens)}，回答预留 {result['max_tokens']}。"
            "请新建对话或缩短输入；原始对话记录未被删除。", 400)
    return json.dumps(result, ensure_ascii=False).encode("utf-8")


def _strict_json(raw: str | bytes) -> object:
    def object_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    def invalid_constant(_value):
        raise ValueError("non-finite JSON value")

    try:
        return json.loads(raw, object_pairs_hook=object_pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RelayError("Local protocol returned invalid or incomplete JSON; nothing was executed.") from exc


def _reasoning_fields(message: dict) -> dict:
    """Keep provider reasoning separate; never parse it as an executable action."""
    if "reasoning_content" not in message:
        return {}
    value = message["reasoning_content"]
    if value is not None and not isinstance(value, str):
        raise RelayError("Local protocol has invalid reasoning content; nothing was executed.")
    return {"reasoning_content": value}


def _protocol_action(response: dict) -> str | None:
    """Validate one entire model-originated call; return only a real code cell.

    A None result is an unchanged, validated native finalizer. No code is
    executed here. Cancellation, code admission and evidence stay upstream.
    """
    if not isinstance(response, dict) or response.get("error"):
        raise RelayError("Local protocol did not produce a valid response; nothing was executed.")
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise RelayError("Local protocol requires exactly one response choice; nothing was executed.")
    choice = choices[0]
    message = choice.get("message")
    if (choice.get("finish_reason") != "tool_calls" or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or (message.get("content") is not None and not isinstance(message["content"], str))):
        raise RelayError("Local protocol requires a completed structured action; nothing was executed.")
    _reasoning_fields(message)
    prose = message.get("content") or ""
    # The original workbench explicitly requests a short explanation before
    # each action. Preserve that model-authored prose, but never let another
    # fenced action compete with the validated native call below.
    if re.search(r"`{3,}|~{3,}|<tool_call(?:\s|>)", prose):
        raise RelayError("Local protocol narration contains an additional action; nothing was executed.")
    calls = message.get("tool_calls")
    if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict):
        raise RelayError("Local protocol forbids multiple or mixed actions; nothing was executed.")
    call = calls[0]
    function = call.get("function")
    if (call.get("type") != "function" or not isinstance(call.get("id"), str)
            or not 1 <= len(call["id"]) <= 256 or not isinstance(function, dict)
            or set(function) != {"name", "arguments"}
            or not isinstance(function.get("arguments"), str)
            or len(function["arguments"].encode("utf-8")) > 262144):
        raise RelayError("Local protocol returned an invalid action envelope; nothing was executed.")
    args = _strict_json(function["arguments"])
    if not isinstance(args, dict):
        raise RelayError("Local protocol arguments must be an object; nothing was executed.")
    if function["name"] == "finalize_response":
        if (set(args) != {"summary", "completion_bullets"}
                or not isinstance(args.get("summary"), str)
                or not 1 <= len(args["summary"]) <= 4000
                or not args["summary"].strip()
                or args.get("completion_bullets") != ["Answered the question"]):
            raise RelayError("Local response submission has invalid arguments; nothing was executed.")
        return None
    if function["name"] != "run_scientific_cell" or set(args) != {"language", "code"}:
        raise RelayError("Local protocol returned an unknown action; nothing was executed.")
    code = args.get("code")
    if (args.get("language") not in ("python", "r") or not isinstance(code, str)
            or not code.strip() or len(code) > 32768 or "\x00" in code):
        raise RelayError("Local scientific cell has invalid arguments; nothing was executed.")
    # A longer fence preserves literal markdown nested in model-authored code.
    fence = "`" * max(3, max((len(run) + 1 for run in re.findall(r"`+", code)), default=3))
    cell = fence + args["language"] + "\n" + code + ("" if code.endswith("\n") else "\n") + fence
    return (prose + "\n\n" if prose else "") + cell


def _stream_response(raw: bytes, *, introduction: bool = False) -> dict:
    """Assemble bounded SSE only after EOF; truncated calls never reach users."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RelayError("Local protocol stream was not valid UTF-8; nothing was executed.") from exc
    response, function = {}, {"name": "", "arguments": ""}
    call_id, content, finish, done, saw_call = None, "", None, False, False
    reasoning_content, saw_reasoning = "", False
    for block in re.split(r"\r?\n\r?\n", text):
        data = "\n".join(line[5:].lstrip(" ") for line in block.splitlines() if line.startswith("data:"))
        if not data:
            continue
        if done:
            raise RelayError("Local protocol stream continued after completion; nothing was executed.")
        if data == "[DONE]":
            done = True
            continue
        event = _strict_json(data)
        if not isinstance(event, dict) or event.get("error"):
            raise RelayError("Local protocol stream failed; nothing was executed.")
        for key in ("id", "model", "created"):
            if key in event:
                # llama.cpp may stamp each chunk at its emission time. Only
                # request ID/model identify a stream; created is metadata.
                if key != "created" and key in response and response[key] != event[key]:
                    raise RelayError("Local protocol stream identity changed; nothing was executed.")
                response[key] = event[key]
        if event.get("usage") is not None:
            response["usage"] = event["usage"]
        choices = event.get("choices")
        if not isinstance(choices, list) or len(choices) > 1:
            raise RelayError("Local protocol stream has invalid choices; nothing was executed.")
        if not choices:
            continue
        choice = choices[0]
        if not isinstance(choice, dict) or choice.get("index") != 0 or finish is not None:
            raise RelayError("Local protocol stream has mixed or late actions; nothing was executed.")
        delta = choice.get("delta")
        if not isinstance(delta, dict) or delta.get("role", "assistant") != "assistant":
            raise RelayError("Local protocol stream has an invalid action delta; nothing was executed.")
        if delta.get("content") is not None:
            if not isinstance(delta["content"], str):
                raise RelayError("Local protocol stream has invalid content; nothing was executed.")
            content += delta["content"]
        reasoning = _reasoning_fields(delta).get("reasoning_content")
        if reasoning is not None:
            reasoning_content += reasoning
            saw_reasoning = True
        calls = delta.get("tool_calls") or []
        if introduction and calls:
            raise RelayError("Local introduction mixed JSON with native actions; nothing was executed.")
        if not isinstance(calls, list) or len(calls) > 1:
            raise RelayError("Local protocol forbids multiple or mixed actions; nothing was executed.")
        for call in calls:
            if (not isinstance(call, dict) or call.get("index") != 0
                    or call.get("type", "function") != "function"):
                raise RelayError("Local protocol forbids multiple or mixed actions; nothing was executed.")
            saw_call = True
            if call.get("id") is not None:
                if not isinstance(call["id"], str) or (call_id is not None and call_id != call["id"]):
                    raise RelayError("Local protocol stream action identity changed; nothing was executed.")
                call_id = call["id"]
            part = call.get("function", {})
            if not isinstance(part, dict) or set(part) - {"name", "arguments"}:
                raise RelayError("Local protocol stream has invalid arguments; nothing was executed.")
            for key in ("name", "arguments"):
                if key in part:
                    if not isinstance(part[key], str):
                        raise RelayError("Local protocol stream has invalid arguments; nothing was executed.")
                    function[key] += part[key]
        if choice.get("finish_reason") is not None:
            finish = choice["finish_reason"]
    expected_finish = "stop" if introduction else "tool_calls"
    if not done or finish != expected_finish or (saw_call if introduction else not saw_call):
        raise RelayError("Local protocol stream was incomplete; nothing was executed.")
    response["object"] = "chat.completion"
    message = {"role": "assistant", "content": content}
    if saw_reasoning:
        message["reasoning_content"] = reasoning_content
    if not introduction:
        message["tool_calls"] = [{"id": call_id, "type": "function", "function": function}]
    response["choices"] = [{"index": 0, "finish_reason": finish, "message": message}]
    return response


def adapt_introduction_response(raw: bytes, content_type: str, *, expected_summary: str | None = None) -> bytes:
    """Translate only a fully generated JSON finalizer into the host protocol."""
    if len(raw) > MAX_RESPONSE:
        raise RelayError("The local response exceeded its size limit.")
    streaming = content_type.split(";", 1)[0].strip().lower() == "text/event-stream"
    response = _stream_response(raw, introduction=True) if streaming else _strict_json(raw)
    if not isinstance(response, dict) or response.get("error"):
        raise RelayError("Local introduction did not produce a complete response.")
    choices = response.get("choices")
    request_id = response.get("id")
    if (not isinstance(choices, list) or len(choices) != 1
            or not isinstance(choices[0], dict) or choices[0].get("finish_reason") != "stop"
            or not isinstance(request_id, str) or not 1 <= len(request_id) <= 256):
        raise RelayError("Local introduction did not finish; nothing was submitted.")
    message = choices[0].get("message")
    if (not isinstance(message, dict) or message.get("role") != "assistant"
            or message.get("tool_calls") or not isinstance(message.get("content"), str)):
        raise RelayError("Local introduction contains an invalid action envelope.")
    reasoning = _reasoning_fields(message)
    action = _strict_json(message["content"])
    if (not isinstance(action, dict) or set(action) != {"name", "arguments"}
            or action.get("name") != "finalize_response" or not isinstance(action.get("arguments"), dict)):
        raise RelayError("Local introduction must contain a complete finalizer action.")
    if expected_summary is not None and action["arguments"].get("summary") != expected_summary:
        raise RelayError("Local introduction did not match the requested product identity.")
    call_id = "leo-intro-" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:24]
    choices[0]["message"] = {"role": "assistant", "content": "", **reasoning, "tool_calls": [{
        "id": call_id, "type": "function", "function": {
            "name": action["name"], "arguments": json.dumps(action["arguments"], ensure_ascii=False),
        },
    }]}
    choices[0]["finish_reason"] = "tool_calls"
    _protocol_action(response)
    return _serialize_protocol_response(response, streaming=streaming)


def adapt_native_response(raw: bytes, content_type: str, *, preserve_literals: bool = False) -> bytes:
    """Translate only an entire, validated model-authored scientific cell.

    Native finalizer bytes pass through unchanged except an unpaired trailing
    thinking control token in plain prose. Call identity and meaningful content
    remain unchanged. Prose alone, truncated JSON/SSE and
    mixed actions fail closed.
    The original gateway remains the only owner of execution and completion.
    """
    if len(raw) > MAX_RESPONSE:
        raise RelayError("The local response exceeded its size limit.")
    streaming = content_type.split(";", 1)[0].strip().lower() == "text/event-stream"
    response = _stream_response(raw) if streaming else _strict_json(raw)
    code = _protocol_action(response)
    message = response["choices"][0]["message"]
    changed = False
    if isinstance(message.get("content"), str):
        cleaned = _clean_think_suffix(message["content"], preserve_literals=preserve_literals)
        changed = cleaned != message["content"]
        message["content"] = cleaned
    if code is None:
        function = message["tool_calls"][0]["function"]
        arguments = _strict_json(function["arguments"])
        summary = _clean_think_suffix(arguments["summary"], preserve_literals=preserve_literals)
        if summary != arguments["summary"]:
            if not summary.strip():
                raise RelayError("Local finalizer contained no answer after its control token.")
            arguments["summary"] = summary
            function["arguments"] = json.dumps(arguments, ensure_ascii=False)
            changed = True
    if code is None and not changed:
        return raw
    if code is not None:
        code = _protocol_action(response)
        response["choices"][0]["message"] = {
            "role": "assistant", "content": code, **_reasoning_fields(message)}
        response["choices"][0]["finish_reason"] = "stop"
    return _serialize_protocol_response(response, streaming=streaming)


def _serialize_protocol_response(response: dict, *, streaming: bool) -> bytes:
    if not streaming:
        return json.dumps(response, ensure_ascii=True).encode("ascii")
    envelope = {key: value for key, value in response.items() if key != "choices" and key != "usage"}
    envelope["object"] = "chat.completion.chunk"
    delta = dict(response["choices"][0]["message"])
    if "tool_calls" in delta:
        delta["tool_calls"] = [{"index": 0, **call} for call in delta["tool_calls"]]
    chunks = [{**envelope, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
        {**envelope, "choices": [{"index": 0, "delta": {},
                                   "finish_reason": response["choices"][0]["finish_reason"]}]}]
    if "usage" in response:
        chunks.append({**envelope, "choices": [], "usage": response["usage"]})
    return ("".join("data: " + json.dumps(chunk, ensure_ascii=True) + "\n\n" for chunk in chunks)
            + "data: [DONE]\n\n").encode("ascii")


class RelayServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, model_port: int, context: int, token: str):
        self.model_port, self.context, self.token = model_port, context, token
        self.children: set[subprocess.Popen] = set()
        self.children_lock = threading.Lock()
        super().__init__(("127.0.0.1", 0), Handler)

    def close_children(self) -> None:
        with self.children_lock:
            children = list(self.children)
        for child in children:
            if child.poll() is None:
                child.terminate()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = "LeoLocal/1"
    sys_version = ""

    def log_message(self, *_args) -> None:
        pass

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(190)

    def error_json(self, status: int, message: str) -> None:
        body = json.dumps({"error": {"message": message, "type": "local_model_error", "code": status}}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self.forward("GET")

    def do_POST(self) -> None:
        self.forward("POST")

    def forward(self, method: str) -> None:
        if self.headers.get("Origin") is not None:
            self.error_json(403, "Browser-origin requests are not accepted by the model adapter.")
            return
        supplied = self.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied, "Bearer " + self.server.token):
            self.error_json(401, "The local model session is not authenticated.")
            return
        allowed = {"GET": {"/health", "/v1/models", "/v1/models/" + MODEL}, "POST": {"/v1/chat/completions"}}
        if self.path not in allowed[method]:
            self.error_json(404, "This local model route is unavailable.")
            return
        child = None
        response_started = False
        try:
            body = None
            native_protocol = False
            introduction_protocol = False
            expected_introduction = None
            preserve_literals = False
            if method == "POST":
                length = self.headers.get("Content-Length", "")
                if self.headers.get("Transfer-Encoding") or not length.isdecimal() or not 0 < int(length) <= MAX_BODY:
                    raise RelayError("Chat body must have a Content-Length of at most 2 MiB.", 413)
                raw = self.rfile.read(int(length))
                if len(raw) != int(length):
                    raise RelayError("The chat request was incomplete.", 400)
                try:
                    payload = json.loads(raw)
                except (ValueError, UnicodeDecodeError) as exc:
                    raise RelayError("The chat request is not UTF-8 JSON.", 400) from exc
                body = prepare_chat(payload, self.server.model_port, self.server.context)
                native_protocol = uses_native_protocol(payload)
                introduction_protocol = native_protocol and is_simple_introduction(payload)
                expected_introduction = introduction_answer(payload) if introduction_protocol else None
                preserve_literals = preserve_think_literals(payload)
            child = subprocess.Popen(curl_args(self.server.model_port, self.path, method, body),
                                     stdin=subprocess.PIPE if body is not None else subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            with self.server.children_lock:
                self.server.children.add(child)
            if body is not None:
                child.stdin.write(body)
                child.stdin.close()
            header = bytearray()
            while True:
                line = child.stdout.readline(32769)
                if not line:
                    raise RelayError("The Windows model service did not respond.")
                header.extend(line)
                if len(header) > 32768:
                    raise RelayError("The Windows model returned oversized headers.")
                if line in (b"\r\n", b"\n"):
                    break
            status, headers = parse_headers(bytes(header))
            if native_protocol and status == 200:
                # Never expose partial native cell arguments to the upstream
                # executor. Buffer this small bounded generation, verify its
                # terminal signal and whole schema, then publish atomically.
                buffered = bytearray()
                while True:
                    chunk = child.stdout.read1(4096)
                    if not chunk:
                        break
                    buffered.extend(chunk)
                    if len(buffered) > MAX_RESPONSE:
                        raise RelayError("The local response exceeded its size limit.")
                if child.wait(timeout=5) != 0:
                    raise RelayError("The local protocol transport was interrupted; nothing was executed.")
                content_type = headers.get("content-type", "application/json")
                adapted = (adapt_introduction_response(bytes(buffered), content_type,
                                                      expected_summary=expected_introduction)
                           if introduction_protocol else adapt_native_response(
                               bytes(buffered), content_type, preserve_literals=preserve_literals))
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(adapted)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "close")
                self.end_headers()
                response_started = True
                self.wfile.write(adapted)
                self.wfile.flush()
                return
            self.send_response(status)
            self.send_header("Content-Type", headers.get("content-type", "application/json"))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            response_started = True
            total = 0
            while True:
                chunk = child.stdout.read1(4096)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_RESPONSE:
                    raise RelayError("The local response exceeded its size limit.")
                self.wfile.write(chunk)
                self.wfile.flush()
            child.wait(timeout=5)
        except RelayError as exc:
            if not response_started:
                self.error_json(exc.status, str(exc))
        except (OSError, subprocess.TimeoutExpired, ValueError):
            if not response_started:
                try:
                    self.error_json(503, "本地模型连接中断，请在 Leo 设置中重新连接本地模型。")
                except OSError:
                    pass
        finally:
            self.close_connection = True
            if child is not None:
                if child.poll() is None:
                    child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                for pipe in (child.stdin, child.stdout):
                    if pipe is not None and not pipe.closed:
                        pipe.close()
                with self.server.children_lock:
                    self.server.children.discard(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-port", type=int, required=True)
    parser.add_argument("--context-size", type=int, required=True)
    args = parser.parse_args()
    token = os.environ.pop("LEO_LOCAL_RELAY_TOKEN", "")
    if not 1 <= args.model_port <= 65535 or not 1024 <= args.context_size <= 131072 or len(token) < 24:
        print(json.dumps({"ok": False, "code": "LOCAL_RELAY_CONFIG_INVALID"}), flush=True)
        return 2
    if not os.path.isfile(CURL):
        print(json.dumps({"ok": False, "code": "WINDOWS_CURL_MISSING"}), flush=True)
        return 2
    server = RelayServer(args.model_port, args.context_size, token)

    def parent_watch() -> None:
        try:
            while sys.stdin.buffer.read(1):
                pass
        finally:
            server.shutdown()
            server.close_children()

    threading.Thread(target=parent_watch, name="leo-parent-watch", daemon=True).start()
    print(json.dumps({"ok": True, "port": server.server_address[1]}), flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.close_children()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
