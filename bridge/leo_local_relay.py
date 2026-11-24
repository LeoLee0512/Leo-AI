"""WSL loopback adapter for the Windows-only local llama.cpp service.

No external socket, pip dependency, model copy, or WSL networking change is
needed. Windows curl transports requests over WSL interop pipes. Both HTTP
servers bind to 127.0.0.1. A per-launch token protects this temporary adapter;
the parent holds stdin open and EOF shuts it down. Nothing is logged to disk,
except (3.2.11) the latest main-loop request, overwritten each time, for Leo's 「用量」 panel.
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
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if __package__:
    from .leo_reasoning import ReasoningError, describe, resolve
else:
    from leo_reasoning import ReasoningError, describe, resolve

MODEL = "local-qwen3-4b"
MAX_BODY = 2 * 1024 * 1024
MAX_RESPONSE = 8 * 1024 * 1024
CURL = "/mnt/c/Windows/System32/curl.exe"
# 3.2.3 · An answer may use up to this many tokens (it was 512, which cut longer answers inside the
# protocol call and failed the turn). A tight context shrinks it, never below LOCAL_MIN_ANSWER_TOKENS.
LOCAL_ANSWER_TOKENS = 2048
LOCAL_MIN_ANSWER_TOKENS = 512
# A light penalty against the loops this 4B model falls into (repeated sentences or emoji).
LOCAL_REPEAT_PENALTY = 1.1
# A finalizer answer is at most this long (upstream's limit); a longer one is cut with a note.
LOCAL_SUMMARY_LIMIT = 4000
TRUNCATED_NOTE = "\n\n（回答过长，已截断。）"
# 3.2.3 · The daemon lists every enabled skill in the system prompt (~2,300 tokens). This 4B model has
# no skill-search action in its two-action protocol, so the list only costs prefill time and
# distracts it; the relay drops that one block for the local model. Cloud models are unaffected.
SKILL_CATALOG_HEADING = "# Available skills (progressive disclosure)"
SKILL_CATALOG_NOTE = "(The skill catalog is omitted for this local model.)"
LOCAL_COMPLETION_REMINDER = """

[Leo 本地模型的工作台协议]
本次传输提供两个私有协议动作，每次响应只输出一个 JSON 对象，选择其中一个：
{"name": "finalize_response", "arguments": {"summary": "...", "completion_bullets": ["Answered the question"]}}
{"name": "run_scientific_cell", "arguments": {"language": "python", "code": "..."}}
{"name": "web_search", "arguments": {"query": "搜索词"}}
问题需要最新信息或网上的资料（新闻、最近的论文、软件版本、你不确定的事实）时选择 web_search，只填搜索词；
诗词原句、引文出处、人名、年份、数据这类你没有把握的事实，先用 web_search 查证，不要凭记忆编。
搜索词只写要查的原句片段或关键词，不要照抄整句提问，也不要带「的下一句」「是什么」这类问法；
例如问「无边落木萧萧下的下一句是」时，搜索词写「无边落木萧萧下」。
不要自己写 requests、urllib 或爬虫代码，沙箱不能直接联网。看到搜索结果后再用 finalize_response 作答，
只根据结果回答，并在答案末尾列出用到的来源网址。
普通回答已经准备好、不需要执行科学工作时，选择 finalize_response；问候、自我介绍、
“你会什么”、概念解释都直接用 finalize_response 回答，不要为此运行代码。
介绍自己能做什么时，只说这些：用 Python 或 R 做科学计算、数据分析和画图；读取和处理用户添加的文件；
解释科学概念、推导公式；在「科研任务」里按可信流程求解已验证的 PINN 问题。
不要提生物信息学、生物安全或其他没有列出的能力。
需要精确数值（大数、复杂运算、数据处理）时不要凭记忆写出数字，先用 run_scientific_cell 计算。
summary 是给用户的完整答案，简洁作答，不要重复同一句话；completion_bullets 固定为 ["Answered the question"]。
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


def _without_skill_catalog(text: str) -> str:
    """The text without the daemon's skill catalog block; unchanged unless the block is recognised."""
    lines = text.split("\n")
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == SKILL_CATALOG_HEADING)
    except StopIteration:
        return text
    # The heading, a short explanation, then one "- name: summary" line per skill or collection.
    first = next((i for i in range(start + 1, min(start + 8, len(lines))) if lines[i].startswith("- ")), None)
    if first is None:
        return text
    end = first
    while end < len(lines) and lines[end].startswith("- "):
        end += 1
    return "\n".join(lines[:start] + [SKILL_CATALOG_NOTE] + lines[end:])


def drop_gpu_note(messages: list) -> list:
    """3.2.8 · User messages without the gateway's appended GPU note (the exact known structure only).

    The note is for GPU work, which this 4B model does not do. Replaying the owner's conversation,
    it pulled answers off course (7/10 right with it, 10/10 without, 2026-09-30). Only a complete
    trailing note in that fixed format is removed; the person's own words are never changed.
    """
    note = re.compile("(?:" + _GATEWAY_LOCAL_CONTEXT_PATTERN + ")$")
    result = []
    for message in messages:
        content = message.get("content")
        if message.get("role") == "user" and isinstance(content, str) and note.search(content):
            message = {**message, "content": note.sub("", content)}
        elif message.get("role") == "user" and isinstance(content, list):
            message = {**message, "content": [
                {**part, "text": note.sub("", part["text"])} if isinstance(part.get("text"), str) else part
                for part in content]}
        result.append(message)
    return result


def drop_skill_catalog(messages: list) -> list:
    """System messages without the skill catalog; every other message and field is kept as is."""
    result = []
    for message in messages:
        content = message.get("content")
        if message.get("role") == "system" and isinstance(content, str) and SKILL_CATALOG_HEADING in content:
            message = {**message, "content": _without_skill_catalog(content)}
        elif message.get("role") == "system" and isinstance(content, list):
            parts = [{**part, "text": _without_skill_catalog(part["text"])}
                     if isinstance(part.get("text"), str) and SKILL_CATALOG_HEADING in part["text"] else part
                     for part in content]
            message = {**message, "content": parts}
        result.append(message)
    return result


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
        # 3.2.6 · The model only chooses the query; the relay writes the one fixed cell that calls the
        # daemon's own search (the same as cloud models use; results appear in 「网页」).
        {"type": "function", "function": {
            "name": "web_search",
            "description": "Search the web for current information. The workbench runs the search and shows the results; answer from them with finalize_response and cite their URLs.",
            "strict": False,
            "parameters": {"type": "object", "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": 300,
                          "description": "What to search for, in the user's language."}},
                "required": ["query"], "additionalProperties": False}}},
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
    arguments = _grammar_parameters(native_protocol_tools()[0])
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


def _grammar_parameters(tool: dict) -> dict:
    """A tool's parameters without length bounds (checked after generation by _protocol_action)."""
    parameters = json.loads(json.dumps(tool["function"]["parameters"]))
    for prop in parameters["properties"].values():
        prop.pop("minLength", None)
        prop.pop("maxLength", None)
    return parameters


def action_response_format() -> dict:
    """3.2.3 · Either protocol action as one JSON object. With native tool_choice=required this local
    build still wrote plain prose and looped to max_tokens (measured 2026-09-30); a JSON grammar makes
    the model generate a whole, well-formed action every time."""
    return {"type": "json_schema", "json_schema": {
        "name": "leo_action", "strict": True, "schema": {"anyOf": [
            {"type": "object", "properties": {
                "name": {"const": tool["function"]["name"]},
                "arguments": _grammar_parameters(tool),
            }, "required": ["name", "arguments"], "additionalProperties": False}
            for tool in native_protocol_tools()
        ]},
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
    messages = drop_gpu_note(drop_skill_catalog(messages))
    result = dict(payload)
    result["messages"] = messages
    result.pop("leo_reasoning_level", None)
    for key in ("thinking_budget_tokens", "reasoning_budget_tokens"):
        result.pop(key, None)
    if uses_native_protocol(payload):
        # Preserve every original message verbatim, and count the complete
        # protocol/tool schemas in the same llama template used for generation.
        identity_answer = fixed_answer(payload)
        simple_introduction = identity_answer is not None
        reminder = LOCAL_COMPLETION_REMINDER
        if simple_introduction and introduction_answer(payload) is not None:
            reminder = (
                "This request is a simple greeting or identity question. Produce only one JSON object "
                "matching the response schema with name=finalize_response and arguments containing "
                "the exact product identity answer fixed by that schema. Your application name is Leo AI. "
                "Do not execute code. Do not add prose outside JSON."
            )
        elif simple_introduction:
            reminder = (
                "The web search found nothing. Produce only one JSON object matching the response schema "
                "with name=finalize_response and arguments containing the exact answer fixed by that schema. "
                "Do not execute code. Do not add prose outside JSON."
            )
        result["messages"] = list(messages) + [{"role": "system", "content": reminder}]
        # A named native tool choice produces plain prose on this local template and
        # can loop until max_tokens (measured again for 3.2.3). A JSON grammar
        # constrains the whole model-generated action: a finalizer or one real cell.
        # We validate the complete action before translating its transport envelope.
        # llama.cpp 5266f24da's autoparser puts its reasoning parser before
        # the JSON content schema. Explicit thinking therefore keeps this
        # grammar; only provider-separated reasoning_content is retained.
        for key in ("tools", "tool_choice", "parallel_tool_calls"):
            result.pop(key, None)
        result["response_format"] = (introduction_response_format(identity_answer) if simple_introduction
                                     else action_response_format())
        result.setdefault("repeat_penalty", LOCAL_REPEAT_PENALTY)
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
    requested = result.pop("max_completion_tokens", result.get("max_tokens", LOCAL_ANSWER_TOKENS))
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
        result["max_tokens"] = min(requested, LOCAL_ANSWER_TOKENS)
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
    room = context - len(tokens)
    if not thinking and LOCAL_MIN_ANSWER_TOKENS <= room < result["max_tokens"]:
        # A long conversation keeps working with a smaller (still sufficient) answer budget.
        result["max_tokens"] = room
    if len(tokens) + result["max_tokens"] > context:
        raise RelayError(
            f"本地模型上下文为 {context} tokens；本次输入需要 {len(tokens)}，回答预留 {result['max_tokens']}。"
            "请新建对话或缩短输入；原始对话记录未被删除。", 400)
    if RECORD_PATH is not None and uses_native_protocol(payload):
        try:
            record_request(result["messages"], prompt, len(tokens), context, result["max_tokens"], port)
        except (OSError, RelayError, ValueError):
            pass  # The record is for the 「用量」 panel only; it never affects the request.
    return json.dumps(result, ensure_ascii=False).encode("utf-8")


# 3.2.11 · The 「用量」 panel shows the exact text of the latest main-loop request to the local model
# (after the relay's own changes) and how its tokens split. Only the latest request is kept, on this
# machine, readable by this user; titles and other side requests do not replace it.
RECORD_PATH = None
RECORD_TEXT_LIMIT = 400_000


def _default_record_path():
    data = os.environ.get("OPENAI4S_DATA_DIR") or os.path.join(os.path.expanduser("~"), ".local/share/leo-ai-studio/data")
    return os.path.join(data, "leo-local-last-request.json")


def _message_text(message: dict) -> str:
    text = _user_text(message)
    for call in message.get("tool_calls") or []:
        function = call.get("function") if isinstance(call, dict) else None
        if isinstance(function, dict):
            text += "\n" + str(function.get("name") or "") + " " + str(function.get("arguments") or "")
    return text


def record_parts(messages: list) -> dict:
    """The request split three ways: system instructions, earlier conversation, the latest question."""
    latest = max((i for i, m in enumerate(messages) if m.get("role") == "user"
                  and not _user_text(m).startswith("[Observation]")), default=None)
    parts = {"system": [], "history": [], "question": []}
    for i, message in enumerate(messages):
        key = "system" if message.get("role") == "system" else "question" if i == latest else "history"
        parts[key].append(_message_text(message))
    return {key: "\n".join(texts) for key, texts in parts.items()}


def record_request(messages: list, prompt: str, prompt_tokens: int, context: int, max_tokens: int, port: int) -> None:
    counts = {}
    for key, text in record_parts(messages).items():
        tokens = local_json(port, "/tokenize", {"content": text, "add_special": False,
                                                "parse_special": False, "with_pieces": False}).get("tokens") if text else []
        counts[key] = len(tokens) if isinstance(tokens, list) else 0
    record = {"version": 1, "at": int(time.time()), "model": MODEL, "context": context,
              "prompt_tokens": prompt_tokens, "max_tokens": max_tokens, "parts": counts,
              "text": prompt[:RECORD_TEXT_LIMIT], "truncated": len(prompt) > RECORD_TEXT_LIMIT}
    directory = os.path.dirname(RECORD_PATH)
    if not os.path.isdir(directory):
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".leo-last-request-", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
        os.chmod(temporary, 0o600)
        os.replace(temporary, RECORD_PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def print_last_request() -> int:
    """``leo_local_relay.py last-request``: the saved record as one JSON line (Leo runs this in WSL)."""
    try:
        with open(_default_record_path(), encoding="utf-8") as handle:
            record = json.load(handle)
        if not isinstance(record, dict) or record.get("version") != 1:
            record = {}
    except FileNotFoundError:
        record = {}
    except (OSError, ValueError):
        print(json.dumps({"ok": False, "error": {"code": "LOCAL_REQUEST_UNREADABLE", "message": "The saved request could not be read."}}))
        return 1
    print(json.dumps({"ok": True, "data": {"request": record}}, ensure_ascii=False))
    return 0


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


WEB_SEARCH_FOUND = "联网搜索：找到 {n} 条结果。"
WEB_SEARCH_EMPTY = "联网搜索：没有找到结果。"
_WEB_SEARCH_CALL = re.compile(r'^_r = host\.web_search\(("(?:[^"\\]|\\.)*"), num_results=5\)$', re.M)


def _query_literal(query: str) -> str:
    """A JSON string literal, which is also a valid Python literal. 3.2.9: readable Chinese in the cell
    (the step list shows it); ASCII escapes only when the text cannot be written as UTF-8."""
    try:
        literal = json.dumps(query, ensure_ascii=False)
        literal.encode("utf-8")
        if any(c in literal for c in "  \x85"):
            raise UnicodeError
        return literal
    except UnicodeError:
        return json.dumps(query, ensure_ascii=True)


def web_search_cell(query: str) -> str:
    """The fixed code for a local web search; the query enters only as a JSON string literal.

    3.2.9 · The first printed line says how many results came back, so the relay and the page can tell
    an empty search without guessing; titles and snippets are kept on one line each for the 「网页」 list.
    """
    literal = _query_literal(query.strip())
    return (
        f"_r = host.web_search({literal}, num_results=5)\n"
        "_rows = _r.get(\"results\") or []\n"
        f"print({WEB_SEARCH_FOUND!r}.format(n=len(_rows)) if _rows else {WEB_SEARCH_EMPTY!r})\n"
        "for _i, _x in enumerate(_rows, 1):\n"
        "    _t = ' '.join(str(_x.get('title') or '').split())\n"
        "    _s = ' '.join(str(_x.get('snippet') or '').split())[:300]\n"
        "    print(f\"{_i}. {_t}\\n   {_x.get('url', '')}\\n   {_s}\")\n"
    )


def searched_query(text: str) -> str | None:
    """The query of a relay-written search cell inside ``text`` (3.2.8 and 3.2.9 cells), else None."""
    match = _WEB_SEARCH_CALL.search(text or "")
    if match is None:
        return None
    try:
        query = json.loads(match.group(1))
    except ValueError:
        return None
    return query if isinstance(query, str) and query.strip() else None


def empty_search_answer(payload: dict) -> str | None:
    """3.2.9 · A fixed, honest answer when the search the model just asked for found nothing.

    Replaying the owner's conversation, after an empty search the 4B model invented a line of verse
    every time (0/8 right, and still 6/6 invented with an explicit "do not invent" rule), so this turn
    is not left to the model. Only the exact shape is recognised: the last message is the daemon's
    observation of the relay's own search cell, and that cell printed the empty line.
    """
    messages = [m for m in payload.get("messages", []) if isinstance(m, dict)]
    if len(messages) < 2:
        return None
    last, cell = messages[-1], messages[-2]
    observation = _user_text(last)
    if last.get("role") not in ("user", "tool") or not observation.startswith("[Observation]"):
        return None
    if cell.get("role") != "assistant":
        return None
    query = searched_query(_user_text(cell))
    if query is None:
        return None
    lines = [line.strip() for line in observation.splitlines()]
    try:
        start = lines.index("stdout:") + 1
        first = lines[start]
    except (ValueError, IndexError):
        return None
    shown = query.strip()[:80]
    if first == WEB_SEARCH_EMPTY or first.startswith("没有找到结果。"):
        return (f"我联网搜索了「{shown}」，但没有找到结果，所以这个问题我不能确定，不想编一个答案给你。"
                "可以换个说法再问；如果经常搜不到，可以在「设置 → 插件 → 联网搜索」里填写搜索 API Key。")
    if first.startswith("联网搜索：找到 ") and not results_mention(query, lines[start + 1:]):
        return (f"我联网搜索了「{shown}」，但搜到的网页和这个问题无关，所以我不能确定答案，不想编一个给你。"
                "可以换个说法再问；免费搜索在国内经常搜偏，在「设置 → 插件 → 联网搜索」里填写搜索 API Key 会可靠得多。")
    return None


def results_mention(query: str, lines: list) -> bool:
    """3.2.10 · Whether any result title or snippet contains one of the query's terms (two or more characters,
    spaces and case ignored). The owner's 「飞雪江南不见梅」 search came back as VPN and video-site pages twice,
    and the 4B model then invented a poem and a poet both times, even after being corrected.

    A query with no term that long cannot be shown to match. Treating that as a match used to skip
    the fixed answer and leave the model free to invent one.
    """
    text = "".join("".join(line.split()) for line in lines
                   if line and not line.startswith(("http://", "https://", "[usage", "[system]"))).lower()
    terms = ["".join(term.split()).strip("\"'“”‘’「」《》,.，。？?！!").lower() for term in query.split()]
    terms = [term for term in terms if len(term) >= 2]
    return bool(terms) and any(term in text for term in terms)


def fixed_answer(payload: dict) -> str | None:
    """Answers the relay fixes in advance: the product's self-introduction, and a search that found
    nothing (3.2.9) or nothing relevant (3.2.10)."""
    return introduction_answer(payload) or empty_search_answer(payload)


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
    if function["name"] == "web_search":
        query = args.get("query")
        if (set(args) != {"query"} or not isinstance(query, str) or not query.strip()
                or len(query) > 300 or any(ord(c) < 32 for c in query)):
            raise RelayError("Local web search has an invalid query; nothing was executed.")
        return (prose + "\n\n" if prose else "") + "```python\n" + web_search_cell(query) + "```"
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
    expected_finish = ("stop", "length") if introduction else ("tool_calls",)
    if not done or finish not in expected_finish or (saw_call if introduction else not saw_call):
        raise RelayError("Local protocol stream was incomplete; nothing was executed.")
    response["object"] = "chat.completion"
    message = {"role": "assistant", "content": content}
    if saw_reasoning:
        message["reasoning_content"] = reasoning_content
    if not introduction:
        message["tool_calls"] = [{"id": call_id, "type": "function", "function": function}]
    response["choices"] = [{"index": 0, "finish_reason": finish, "message": message}]
    return response


def _salvage_summary(content: str) -> str | None:
    """The answer text of a finalizer that ran out of tokens, or None (never a partial cell).

    Only a JSON finalizer cut inside its summary string qualifies. Long runs of one repeated
    fragment are collapsed, and the answer is marked as cut.
    """
    match = re.match(r'\s*\{\s*"name"\s*:\s*"finalize_response"\s*,\s*"arguments"\s*:\s*\{\s*"summary"\s*:\s*"', content)
    if match is None:
        return None
    text, i, rest = [], 0, content[match.end():]
    escapes = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f"}
    while i < len(rest):
        char = rest[i]
        if char == '"':
            return None  # the summary was complete; a cut elsewhere is not an answer to salvage
        if char == "\\":
            if i + 1 >= len(rest):
                break
            if rest[i + 1] == "u":
                digits = rest[i + 2:i + 6]
                if len(digits) < 4:
                    break
                try:
                    text.append(chr(int(digits, 16)))
                except ValueError:
                    return None
                i += 6
                continue
            if rest[i + 1] not in escapes:
                return None
            text.append(escapes[rest[i + 1]])
            i += 2
            continue
        text.append(char)
        i += 1
    answer = re.sub(r"(.{1,12}?)\1{12,}", r"\1\1\1…", "".join(text)).rstrip()
    return answer[:LOCAL_SUMMARY_LIMIT - len(TRUNCATED_NOTE)] + TRUNCATED_NOTE if answer.strip() else None


def adapt_action_response(raw: bytes, content_type: str, *, expected_summary: str | None = None,
                          preserve_literals: bool = False, reasoning_streamed: bool = False) -> bytes:
    """Translate one fully generated JSON action into the host protocol.

    A finalizer becomes the native finalizer call; a cell becomes the fenced code the original
    workbench executes. A finalizer cut by the token limit keeps its answer, marked as cut; a cut
    cell, prose, or any other shape fails closed and nothing is executed.
    """
    if len(raw) > MAX_RESPONSE:
        raise RelayError("The local response exceeded its size limit.")
    streaming = content_type.split(";", 1)[0].strip().lower() == "text/event-stream"
    response = _stream_response(raw, introduction=True) if streaming else _strict_json(raw)
    if not isinstance(response, dict) or response.get("error"):
        raise RelayError("Local model did not produce a complete response.")
    choices = response.get("choices")
    request_id = response.get("id")
    if (not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict)
            or choices[0].get("finish_reason") not in ("stop", "length")
            or not isinstance(request_id, str) or not 1 <= len(request_id) <= 256):
        raise RelayError("Local model did not finish its action; nothing was executed.")
    message = choices[0].get("message")
    if (not isinstance(message, dict) or message.get("role") != "assistant"
            or message.get("tool_calls") or not isinstance(message.get("content"), str)):
        raise RelayError("Local model returned an invalid action envelope; nothing was executed.")
    reasoning = _reasoning_fields(message)
    if reasoning_streamed:
        reasoning = {}  # already sent to the gateway as it was generated
    if choices[0]["finish_reason"] == "stop":
        action = _strict_json(message["content"])
    else:
        summary = _salvage_summary(message["content"])
        if summary is None:
            raise RelayError("Local model ran out of tokens before finishing its action; nothing was executed.")
        action = {"name": "finalize_response",
                  "arguments": {"summary": summary, "completion_bullets": ["Answered the question"]}}
    if (not isinstance(action, dict) or set(action) != {"name", "arguments"}
            or action.get("name") not in ("finalize_response", "run_scientific_cell", "web_search")
            or not isinstance(action.get("arguments"), dict)):
        raise RelayError("Local model must return one complete protocol action; nothing was executed.")
    arguments = action["arguments"]
    if action["name"] == "finalize_response":
        if expected_summary is not None and arguments.get("summary") != expected_summary:
            raise RelayError("Local introduction did not match the requested product identity.")
        if isinstance(arguments.get("summary"), str):
            summary = _clean_think_suffix(arguments["summary"], preserve_literals=preserve_literals)
            if len(summary) > LOCAL_SUMMARY_LIMIT:
                summary = summary[:LOCAL_SUMMARY_LIMIT - len(TRUNCATED_NOTE)] + TRUNCATED_NOTE
            arguments["summary"] = summary
    elif expected_summary is not None:
        raise RelayError("Local introduction must contain a complete finalizer action.")
    call_id = "leo-local-" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:24]
    choices[0]["message"] = {"role": "assistant", "content": "", **reasoning, "tool_calls": [{
        "id": call_id, "type": "function", "function": {
            "name": action["name"], "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }]}
    choices[0]["finish_reason"] = "tool_calls"
    code = _protocol_action(response)
    if code is not None:
        choices[0]["message"] = {"role": "assistant", "content": code, **reasoning}
        choices[0]["finish_reason"] = "stop"
    return _serialize_protocol_response(response, streaming=streaming)


def live_reasoning_event(event: bytes) -> bytes | None:
    """3.2.6 · One SSE event that carries only model thinking, re-emitted for the gateway at once.

    Thinking is not an action, so it can be shown while the model thinks; the action itself stays
    buffered and is published only after it has been validated whole. Anything else returns None.
    """
    lines = event.decode("utf-8", "replace").splitlines()
    data = "\n".join(line[5:].lstrip(" ") for line in lines if line.startswith("data:"))
    if not data or data == "[DONE]":
        return None
    try:
        value = json.loads(data)
    except ValueError:
        return None
    choices = value.get("choices") if isinstance(value, dict) else None
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return None
    delta = choices[0].get("delta")
    thinking = delta.get("reasoning_content") if isinstance(delta, dict) else None
    if (not isinstance(thinking, str) or not thinking or delta.get("content") or delta.get("tool_calls")
            or choices[0].get("finish_reason") is not None):
        return None
    envelope = {key: value[key] for key in ("id", "model", "created") if key in value}
    chunk = {**envelope, "object": "chat.completion.chunk", "choices": [
        {"index": 0, "delta": {"role": "assistant", "reasoning_content": thinking}, "finish_reason": None}]}
    return ("data: " + json.dumps(chunk, ensure_ascii=True) + "\n\n").encode("ascii")


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
                expected_introduction = fixed_answer(payload) if native_protocol else None
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
                # 3.2.6 · In a stream, thinking is forwarded as it is generated (it is not an action).
                content_type = headers.get("content-type", "application/json")
                streaming = content_type.split(";", 1)[0].strip().lower() == "text/event-stream"
                buffered, pending, live = bytearray(), b"", False
                while True:
                    chunk = child.stdout.read1(4096)
                    if not chunk:
                        break
                    buffered.extend(chunk)
                    if len(buffered) > MAX_RESPONSE:
                        raise RelayError("The local response exceeded its size limit.")
                    if not streaming:
                        continue
                    pending = (pending + chunk).replace(b"\r\n", b"\n")
                    while b"\n\n" in pending:
                        event, pending = pending.split(b"\n\n", 1)
                        thinking = live_reasoning_event(event)
                        if thinking is None:
                            continue
                        if not response_started:
                            self.send_response(status)
                            self.send_header("Content-Type", content_type)
                            self.send_header("Cache-Control", "no-store")
                            self.send_header("Connection", "close")
                            self.end_headers()
                            response_started = live = True
                        self.wfile.write(thinking)
                        self.wfile.flush()
                if child.wait(timeout=5) != 0:
                    raise RelayError("The local protocol transport was interrupted; nothing was executed.")
                adapted = adapt_action_response(bytes(buffered), content_type,
                                                expected_summary=expected_introduction,
                                                preserve_literals=preserve_literals, reasoning_streamed=live)
                if not response_started:
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
            else:
                try:
                    self.wfile.write(("data: " + json.dumps({"error": {"message": str(exc), "type": "relay_error"}},
                                                           ensure_ascii=True) + "\n\n").encode("ascii"))
                    self.wfile.flush()
                except OSError:
                    pass
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
    global RECORD_PATH
    RECORD_PATH = _default_record_path()

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
    raise SystemExit(print_last_request() if sys.argv[1:] == ["last-request"] else main())
