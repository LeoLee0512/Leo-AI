"""Bounded native gateway for Leo's own frontend. No daemon token enters HTML."""
import base64
import binascii
import hashlib
import json
import re
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlencode, urlsplit
from urllib.request import Request, ProxyHandler, build_opener

from .bridge_client import WslBridge
from .session_models import _NoRedirect

_JSON_LIMIT = 4 * 1024 * 1024
# The execution log carries every cell's captured output; it is trimmed below
# before anything reaches the page, so the transport may read more than it keeps.
_NOTEBOOK_JSON_LIMIT = 16 * 1024 * 1024
_NOTEBOOK_MAX_ENTRIES = 400
_NOTEBOOK_TEXT_LIMIT = 64 * 1024
_NOTEBOOK_MAX_NAMES = 50
_ARTIFACT_MAX_ITEMS = 500
_PREVIEW_IMAGE_LIMIT = 3 * 1024 * 1024
_PREVIEW_TEXT_LIMIT = 256 * 1024
_KERNEL_STATES = {"none", "running", "stopped", "ended"}
# Raster formats are recognised by their bytes, not by the server's word for them.
_IMAGE_MAGIC = {"image/png": (b"\x89PNG\r\n\x1a\n",), "image/jpeg": (b"\xff\xd8\xff",),
                "image/gif": (b"GIF87a", b"GIF89a"), "image/webp": (b"RIFF",)}
_TEXT_TYPES = {"application/json", "application/xml", "application/x-yaml", "application/yaml",
               "application/csv", "application/x-tex", "application/javascript"}
_TEXT_SUFFIXES = (".txt", ".csv", ".tsv", ".json", ".md", ".py", ".r", ".log", ".yaml", ".yml",
                  ".tex", ".xml", ".ini", ".toml", ".dat")


# Operations answered inside the shell rather than by the daemon (approval modes, schedules).
# The desktop registers them at start-up; the page reaches them through the same bounded
# workbench_request entry, so no new native method is exposed to the page.
_LOCAL_HANDLERS = {}


def register_local(operations, handler):
    for operation in operations:
        _LOCAL_HANDLERS[operation] = handler


def unregister_local(operations):
    for operation in operations:
        _LOCAL_HANDLERS.pop(operation, None)


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


def text_value(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value.strip()


# 3.1.0 · Files a person adds to a conversation. The daemon places them in the conversation's working
# directory, where the AI opens them by name; Leo keeps names to letters, digits, "_", "-" and "." so a
# name also works when it is mentioned in a message.
UPLOAD_MAX_BYTES = 25 * 1024 * 1024


def upload_name(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 400:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    name = value.replace("\\", "/").rsplit("/", 1)[-1].strip()
    stem, dot, extension = name.rpartition(".")
    if not dot or not stem.strip("."):  # a leading dot (.bashrc) starts a name, not an extension
        stem, extension = name, ""
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("._")[:100] or "file"
    extension = re.sub(r"[^A-Za-z0-9]+", "", extension)[:12]
    return stem + ("." + extension if extension else "")


def upload_content(value):
    """The page's base64 text, checked strictly; the bytes themselves are never kept here."""
    if not isinstance(value, str) or len(value) > (UPLOAD_MAX_BYTES + 2) // 3 * 4:
        raise ValueError("WORKBENCH_UPLOAD_TOO_LARGE")
    try:
        size = len(base64.b64decode(value, validate=True))
    except (ValueError, binascii.Error):
        raise ValueError("WORKBENCH_INVALID_REQUEST") from None
    if size > UPLOAD_MAX_BYTES:
        raise ValueError("WORKBENCH_UPLOAD_TOO_LARGE")
    return value


# 3.1.0 · A command typed into 「终端」 runs as one cell in the conversation's own sandboxed kernel,
# through host.bash, so the same approval policy applies as to the AI's commands. The page sends
# only the command text; Leo writes the cell. The command enters the cell as ascii() of the string,
# an exact ASCII-only Python literal, so nothing in it can become code. The first line repeats it as
# JSON so the notebook and 「终端」 can show the command instead of the cell.
TERMINAL_MARK = "# leo-terminal "
TERMINAL_TIMEOUT = 300


def terminal_code(command, run_id):
    return (f"{TERMINAL_MARK}{run_id} {json.dumps(command, ensure_ascii=True)}\n"
            "def _leo_terminal():\n"
            "    import sys\n"
            "    try:\n"
            f"        result = host.bash({ascii(command)}, timeout={TERMINAL_TIMEOUT})\n"
            "    except Exception as error:\n"
            "        print('[没有执行] ' + str(error))\n"
            "        return\n"
            "    print(result.get('stdout') or '', end='')\n"
            "    if result.get('stderr'):\n"
            "        print(result['stderr'], end='', file=sys.stderr)\n"
            "    print('\\n[exit %s]' % result.get('exit_code'))\n"
            "_leo_terminal()\n"
            "del _leo_terminal\n")


def terminal_command(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 8000 or "\x00" in value:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value.strip()


# 3.1.0 · 「插件」. Skills are the daemon's own catalogue. Connectors (MCP servers) run outside the kernel
# sandbox with the daemon's rights, so Leo adds only the ones it has checked, never an arbitrary command,
# and never shows a connector's launch command, arguments or error text to the page.
CONNECTOR_ALLOWLIST = {
    "example": ("示例连接器", "回显、当前时间、计算器和随机整数。不联网、不需要安装，用来确认连接器能正常工作。"),
}
SKILL_DOCUMENT_LIMIT = 1024 * 1024


def plugin_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return quote(value, safe="")


def flag(value):
    if type(value) is not bool:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


# 3.2.1 · 「Python」: code typed in the side panel runs as one cell in the conversation's sandboxed
# kernel, exactly as typed (it is the person's own code; the kernel's sandbox and its approvals for host
# calls stay in force). The first line marks the cell so the panel can show it as the person's.
PYTHON_MARK = "# leo-python "
PYTHON_MAX_CODE = 100_000


def python_code(code, run_id):
    if not isinstance(code, str) or not code.strip() or len(code) > PYTHON_MAX_CODE or "\x00" in code:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return f"{PYTHON_MARK}{run_id}\n{code}"


def terminal_run_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{16}", value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


def search_key(value):
    """A search API key as typed: visible ASCII only, no spaces inside, at most 256 characters."""
    key = value.strip() if isinstance(value, str) else ""
    if not key or len(key) > 256 or any(not 33 <= ord(c) <= 126 for c in key):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return key


def route(payload):
    """The browser chooses operations, never an arbitrary URL or HTTP method."""
    if not isinstance(payload, dict):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    op = payload.get("operation")
    if op == "projects":
        return "GET", "/projects", None
    if op == "create_project":
        return "POST", "/projects", {"name": text_value(payload.get("name"), 120)}
    if op == "frames":
        query = {"project_id": identifier(payload.get("projectId", "all")), "limit": 100}
        if payload.get("cursor"):
            cursor = text_value(payload["cursor"], 512)
            query["cursor"] = cursor
        return "GET", "/frames?" + urlencode(query), None
    if op == "create_frame":
        return "POST", "/frames", {"project_id": identifier(payload.get("projectId"))}
    if op == "skills":
        return "GET", "/skills/catalog", None
    if op == "skill_toggle":
        return "PUT", "/skills/catalog/" + plugin_name(payload.get("name")) + "/enabled", {"enabled": flag(payload.get("enabled"))}
    if op == "skill_import":
        content = payload.get("content")
        if not isinstance(content, str) or not content.strip() or len(content.encode("utf-8")) > SKILL_DOCUMENT_LIMIT:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        return "POST", "/skills/import", {"content": content}
    if op == "skill_delete":
        return "DELETE", "/skills/" + plugin_name(payload.get("name")), None
    if op == "connectors":
        return "GET", "/connectors", None
    if op == "connector_toggle":
        return "PUT", "/connectors/" + plugin_name(payload.get("id")) + "/enabled", {"enabled": flag(payload.get("enabled"))}
    if op == "connector_probe":
        return "POST", "/connectors/" + plugin_name(payload.get("id")) + "/probe", {}
    if op == "connector_delete":
        return "DELETE", "/connectors/" + plugin_name(payload.get("id")), None
    # 3.2.9 · The search API key goes straight to the daemon's own search setting (stored in its secret
    # store); Leo keeps no copy, and the page only ever learns whether a key is set.
    if op == "search_config":
        return "GET", "/search/config", None
    if op == "search_key_save":
        return "PUT", "/search/config", {"api_key": search_key(payload.get("apiKey"))}
    if op == "search_key_clear":
        return "PUT", "/search/config", {"clear_api_key": True}
    frame = identifier(payload.get("frameId"))
    path = "/frames/" + frame
    if op == "frame":
        return "GET", path, None
    if op == "messages":
        query = {"limit": 100, "newest_first": 1}
        if payload.get("before") is not None:
            if type(payload["before"]) is not int or payload["before"] < 0:
                raise ValueError("WORKBENCH_INVALID_REQUEST")
            query["before_seq"] = payload["before"]
        return "GET", path + "/messages?" + urlencode(query), None
    if op == "rename":
        return "PATCH", path, {"name": text_value(payload.get("name"), 160)}
    if op == "send":
        binding = payload.get("modelBinding")
        reasoning = payload.get("reasoningSelection")
        if (not isinstance(binding, dict) or type(binding.get("revision")) is not int
                or binding["revision"] < 1 or not isinstance(reasoning, dict)):
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        return "POST", path + "/message", {"input_data": {"request": text_value(payload.get("text"), 64000)},
            "model_binding": {"profile_id": identifier(binding.get("profile_id")), "revision": binding["revision"]},
            "reasoning_selection": {"choice": identifier(reasoning.get("choice")),
                                    "capability_revision": text_value(reasoning.get("capability_revision"), 160)},
            "plan": False, "explore": False, "wait": False}
    if op == "cancel":
        owner = payload.get("owner")
        if not isinstance(owner, dict):
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        return "POST", path + "/cancel", {"execution_id": identifier(payload.get("executionId")),
            "owner": {"kind": identifier(owner.get("kind")), "id": identifier(owner.get("id"))}}
    if op == "execution":
        return "GET", path + "/execution-queue", None
    if op == "timeline":
        return "GET", path + "/action-timeline?limit=300", None
    if op == "context":
        return "GET", path + "/context", None
    if op == "thoughts":
        return "GET", path + "/leo-projections", None
    if op == "steps":
        return "GET", path + "/steps", None
    if op == "terminal_run":
        run_id = terminal_run_id(payload.get("runId"))
        return "POST", path + "/kernel/execute", {"code": terminal_code(terminal_command(payload.get("command")), run_id),
            "language": "python", "execution_id": "leo-term-" + run_id}
    if op == "python_run":
        run_id = terminal_run_id(payload.get("runId"))
        return "POST", path + "/kernel/execute", {"code": python_code(payload.get("code"), run_id),
            "language": "python", "execution_id": "leo-py-" + run_id}
    if op == "python_interrupt":
        run_id = terminal_run_id(payload.get("runId"))
        # A REPL cell's owner is the user REPL with the cell's own execution id (upstream submit_repl).
        return "POST", path + "/kernel/interrupt", {"execution_id": "leo-py-" + run_id,
            "owner": {"kind": "user_repl", "id": "leo-py-" + run_id}}
    if op == "upload":
        # Only the conversation, a cleaned name and checked content; never a project or workspace id.
        return "POST", "/uploads", {"frame_id": frame, "filename": upload_name(payload.get("filename")),
                                    "content_base64": upload_content(payload.get("data"))}
    if op == "artifacts":
        return "GET", path + "/artifacts", None
    if op == "notebook":
        return "GET", path + "/execution-log", None
    if op == "kernel":
        return "GET", path + "/kernel", None
    if op == "artifact_preview":
        return "GET", "/artifacts/" + identifier(payload.get("artifactId")), None
    if op == "feedback":
        return "GET", path + "/feedback", None
    if op == "set_feedback":
        # One rating per message; None clears it. The key is the message's own id.
        key = payload.get("key")
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", key):
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        rating = payload.get("rating")
        if rating not in ("up", "down", None):
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        return "POST", path + "/feedback", {"key": key, "rating": rating}
    raise ValueError("WORKBENCH_INVALID_REQUEST")


def shape_feedback(result):
    ratings = result.get("feedback") if isinstance(result, dict) else None
    if not isinstance(ratings, dict):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    return {"feedback": {key: value for key, value in ratings.items()
                         if isinstance(key, str) and len(key) <= 128 and value in ("up", "down")}}


def _clip(value, limit=_NOTEBOOK_TEXT_LIMIT):
    text = value if isinstance(value, str) else ""
    return (text[:limit], True) if len(text) > limit else (text, False)


def _names(value):
    if not isinstance(value, list):
        return []
    return [item[:255] for item in value if isinstance(item, str) and item][:_NOTEBOOK_MAX_NAMES]


def _count(value):
    return value if type(value) is int and value >= 0 else None


def shape_notebook(result):
    """Keep the fields the notebook view renders; nothing else reaches the page."""
    if not isinstance(result, dict) or not isinstance(result.get("entries"), list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    rows = [row for row in result["entries"] if isinstance(row, dict)]
    entries = []
    for ordinal, row in enumerate(rows[-_NOTEBOOK_MAX_ENTRIES:], max(1, len(rows) - _NOTEBOOK_MAX_ENTRIES + 1)):
        clipped = {}
        truncated = False
        for key in ("source", "stdout", "stderr", "error"):
            clipped[key], cut = _clip(row.get(key))
            truncated = truncated or cut
        seconds = row.get("cpu_seconds")
        status = row.get("status") if isinstance(row.get("status"), str) else "ok"
        language = row.get("language") if row.get("language") in ("python", "r") else "python"
        terminal = _terminal_cell(row.get("source"))
        python_run = _python_cell(row.get("source"))
        if python_run:
            # Show the person's code, not Leo's marker line.
            clipped["source"] = _clip(row["source"].split("\n", 1)[1] if "\n" in row["source"] else "")[0]
        entries.append({
            "ordinal": ordinal,
            "origin": "user" if row.get("origin") == "user" else "agent",
            "terminalRun": terminal[0] if terminal else None,
            "pythonRun": python_run,
            "command": terminal[1] if terminal else None,
            "cellIndex": _count(row.get("cell_index")),
            "language": language,
            "status": status[:32],
            **clipped,
            "truncated": truncated,
            "figures": _names(row.get("figures")),
            "filesWritten": _names(row.get("files_written")),
            "attempt": _count(row.get("attempt")) or 1,
            "attemptCount": _count(row.get("attempt_count")) or 1,
            "latest": row.get("is_latest_attempt") is not False,
            "stale": row.get("stale") is True,
            "cpuSeconds": seconds if isinstance(seconds, (int, float)) and not isinstance(seconds, bool) and seconds >= 0 else None,
        })
    return {"entries": entries, "total": len(rows), "omitted": max(0, len(rows) - _NOTEBOOK_MAX_ENTRIES)}


def _python_cell(source):
    """The run id when a cell is one the person ran from 「Python」, else None."""
    if not isinstance(source, str) or not source.startswith(PYTHON_MARK):
        return None
    run_id = source.split("\n", 1)[0][len(PYTHON_MARK):]
    return run_id if re.fullmatch(r"[0-9a-f]{16}", run_id) else None


def _terminal_cell(source):
    """(run id, command) when a cell is one Leo wrote for 「终端」, else None."""
    if not isinstance(source, str) or not source.startswith(TERMINAL_MARK):
        return None
    first = source.split("\n", 1)[0][len(TERMINAL_MARK):]
    run_id, _, literal = first.partition(" ")
    try:
        command = json.loads(literal)
    except ValueError:
        return None
    if not re.fullmatch(r"[0-9a-f]{16}", run_id) or not isinstance(command, str):
        return None
    return run_id, _clip(command, 8000)[0]


def _version_id(row):
    """The newest version's id, so a link to an exact version (trusted delivery) finds its file."""
    for key in ("latest_version_id", "version_id"):
        value = row.get(key)
        if isinstance(value, str) and re.fullmatch(r"v-[A-Za-z0-9_-]{1,120}", value):
            return value
    return ""


def shape_artifacts(result):
    if not isinstance(result, list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    artifacts = []
    for row in result:
        if not isinstance(row, dict):
            continue
        ident = row.get("artifact_id") or row.get("id")
        if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", ident):
            continue
        filename = row.get("filename") if isinstance(row.get("filename"), str) else ""
        content_type = row.get("content_type") if isinstance(row.get("content_type"), str) else ""
        artifacts.append({"id": ident, "filename": filename[:255], "contentType": content_type[:120],
                          "size": _count(row.get("size_bytes")),
                          "versionId": _version_id(row),
                          "createdAt": row.get("created_at") if isinstance(row.get("created_at"), str) else "",
                          "upload": row.get("is_user_upload") is True})
        if len(artifacts) >= _ARTIFACT_MAX_ITEMS:
            break
    return {"artifacts": artifacts}


def shape_kernel(result):
    if not isinstance(result, dict):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    state = result.get("state") if result.get("state") in _KERNEL_STATES else "none"
    return {"state": state, "alive": result.get("alive") is True, "generation": _count(result.get("generation")) or 0}


def preview_payload(raw, content_type, meta):
    """Turn artifact bytes into something the CSP-locked page can show inertly."""
    kind = (content_type or meta.get("contentType") or "").split(";", 1)[0].strip().lower()
    name = (meta.get("filename") or "").lower()
    base = {"id": meta["id"], "filename": meta.get("filename", ""), "contentType": kind, "size": meta.get("size")}
    magic = _IMAGE_MAGIC.get(kind)
    if magic and len(raw) <= _PREVIEW_IMAGE_LIMIT and raw.startswith(magic) and (kind != "image/webp" or raw[8:12] == b"WEBP"):
        return {**base, "kind": "image", "dataUri": f"data:{kind};base64," + base64.b64encode(raw).decode("ascii")}
    if kind == "image/svg+xml" and len(raw) <= _PREVIEW_IMAGE_LIMIT:
        # An <img> never runs an SVG's scripts, and the page CSP only allows data: images.
        return {**base, "kind": "image", "dataUri": "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")}
    if kind.startswith("text/") or kind in _TEXT_TYPES or name.endswith(_TEXT_SUFFIXES):
        text = raw[:_PREVIEW_TEXT_LIMIT].decode("utf-8", errors="replace")
        return {**base, "kind": "text", "text": text, "truncated": len(raw) > _PREVIEW_TEXT_LIMIT}
    return {**base, "kind": "binary"}


_TIMELINE_KINDS = {"user", "code", "native_tools", "delegate", "finalize", "terminal", "no_action",
                   "permission_resolution", "system", "turn"}
_TIMELINE_STATUS = {"running", "completed", "failed", "cancelled", "interrupted", "pending", "proposed"}


def shape_timeline(result):
    """What the page needs to fold a turn's steps: kind, title, status and approval — no arguments.

    The daemon's timeline already withholds commands, URLs and raw results; this keeps only the
    few fields the folded view draws, bounded.
    """
    groups = result.get("groups") if isinstance(result, dict) else None
    if not isinstance(groups, list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    shaped = []
    for group in groups[-300:]:
        if not isinstance(group, dict):
            continue
        kind = group.get("kind") if group.get("kind") in _TIMELINE_KINDS else "other"
        permission = group.get("permission") if isinstance(group.get("permission"), dict) else None
        names = []
        for event in group.get("events") or []:
            name = event.get("name") if isinstance(event, dict) else None
            if isinstance(name, str) and name and name not in names and len(names) < 6:
                names.append(name[:80])
        shaped.append({
            "ordinal": group.get("ordinal") if type(group.get("ordinal")) is int else None,
            "turnId": _clip(group.get("turn_id"), 160)[0] or None,
            "kind": kind,
            "title": _clip(group.get("title"), 160)[0],
            "status": group.get("status") if group.get("status") in _TIMELINE_STATUS else "other",
            "names": names,
            "permission": {"decisionId": _clip(permission.get("decision_id"), 120)[0],
                           "state": _clip(permission.get("state"), 40)[0]} if permission else None,
            # 3.2.11 · 「用量」: the model call's own token counts (numbers only) and model name.
            "model": _clip(group.get("model"), 120)[0] or None,
            "usage": _usage(group.get("usage")),
        })
    return {"groups": shaped}


_USAGE_KEYS = {"input_tokens": "input", "output_tokens": "output", "cache_read": "cacheRead",
               "reasoning_tokens": "reasoning"}


def _usage(value):
    if not isinstance(value, dict):
        return None
    usage = {name: value[key] for key, name in _USAGE_KEYS.items() if _count(value.get(key)) is not None}
    return usage or None


# The daemon's context parts, in Chinese for the 「用量」 panel.
_CONTEXT_LAYERS = {"system_prompt": "系统提示", "text": "对话文字", "images": "图片", "tool_schemas": "工具说明",
                   "tool_calls": "工具调用", "tool_results": "工具结果", "artifact_refs": "文件引用", "wire_state": "其他"}


def shape_context(result):
    """The daemon's estimate of what the conversation sends each turn, and the model's limit (numbers only)."""
    if not isinstance(result, dict):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    layers = []
    for layer in result.get("layers") if isinstance(result.get("layers"), list) else []:
        kind = layer.get("kind") if isinstance(layer, dict) else None
        tokens = _count(layer.get("token_count")) if isinstance(layer, dict) else None
        if kind in _CONTEXT_LAYERS and tokens:
            layers.append({"kind": kind, "label": _CONTEXT_LAYERS[kind], "tokens": tokens})
    return {"estimate": _count(result.get("token_count")), "limit": _count(result.get("token_limit")),
            "outputReserve": _count(result.get("output_reserve")), "messages": _count(result.get("message_count")),
            "compactions": _count(result.get("compaction_count")) or 0, "layers": layers}


_THOUGHT_SOURCES = {"reasoning_content", "reasoning"}
_THOUGHT_MAX_ITEMS = 200
_THOUGHT_TEXT_LIMIT = 32 * 1024


def shape_thoughts(result):
    """2.2.11 · The model's own reasoning text, one entry per model call, for the fold.

    The bridge overlay (``bridge/leo_thought_runtime.py``) stores what the provider streamed as
    ``reasoning_content`` before anything is shown; this keeps only that channel, only when the
    stored digest matches the text, and bounds what reaches the page.
    """
    rows = result.get("projections") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    thoughts = []
    for row in rows:
        if not isinstance(row, dict) or row.get("channel") != "thought" or row.get("source_field") not in _THOUGHT_SOURCES:
            continue
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        if row.get("content_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            continue
        clipped, cut = _clip(text, _THOUGHT_TEXT_LIMIT)
        thoughts.append({"turnId": _clip(row.get("turn_id"), 160)[0] or None,
                         "groupId": _clip(row.get("group_id"), 160)[0] or None,
                         "engineTurn": _count(row.get("engine_turn")),
                         "status": _clip(row.get("status"), 40)[0],
                         "text": clipped, "truncated": cut})
    omitted = max(0, len(thoughts) - _THOUGHT_MAX_ITEMS)
    return {"thoughts": thoughts[omitted:], "hasMore": result.get("has_more") is True or omitted > 0}


_STEP_LIMIT = 200
_OUTPUT_PREVIEW = 4000


def _web_url(value):
    """An address the page may show and offer to open: http(s) only, bounded."""
    if not isinstance(value, str) or len(value) > 2048 or not re.match(r"https?://", value, re.I):
        return None
    return value


def _when(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return _clip(value, 64)[0] or None


def shape_steps(result):
    """3.1.0 · What the AI (or the person, from 「终端」) ran and read, for 「终端」 and 「网页」.

    Commands keep the daemon's own redacted text and output previews; searches keep titles,
    addresses and snippets; page reads keep the address and a short excerpt. Everything is text for
    the page, nothing is rendered as HTML, and the daemon returns only a conversation's first 800 steps.
    """
    rows = result.get("steps") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    commands, web = [], []
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = row.get("kind")
        given = row.get("input") if isinstance(row.get("input"), dict) else {}
        out = row.get("output") if isinstance(row.get("output"), dict) else {}
        base = {"seq": _count(row.get("seq")), "status": _clip(row.get("status"), 40)[0], "at": _when(row.get("created_at")),
                "summary": _clip(row.get("summary"), 240)[0]}
        if kind == "bash":
            streams = {}
            for name in ("stdout", "stderr"):
                stream = out.get(name)
                text = stream.get("preview") if isinstance(stream, dict) else stream
                clipped, cut = _clip(text if isinstance(text, str) else "", _OUTPUT_PREVIEW)
                streams[name] = clipped
                streams[name + "Truncated"] = cut or (isinstance(stream, dict) and (stream.get("truncated") is True
                                                                                   or (_count(stream.get("dropped_chars")) or 0) > 0))
            diff = out.get("workspace_diff") if isinstance(out.get("workspace_diff"), dict) else {}
            changed = [name for key in ("created", "modified", "deleted") for name in _names(diff.get(key))][:50]
            code = out.get("exit_code")
            commands.append({**base, "command": _clip(given.get("command"), 1000)[0], "cwd": _clip(given.get("cwd"), 300)[0],
                             "exitCode": code if isinstance(code, int) and not isinstance(code, bool) else None,
                             "durationMs": _count(out.get("duration_ms")), **streams, "changed": changed,
                             "error": _clip(out.get("error"), 600)[0]})
        elif kind == "search":
            results = []
            for item in out.get("results") if isinstance(out.get("results"), list) else []:
                if isinstance(item, dict) and len(results) < 8:
                    results.append({"title": _clip(item.get("title"), 300)[0], "url": _web_url(item.get("url")),
                                    "snippet": _clip(item.get("snippet"), 300)[0]})
            web.append({**base, "type": "search", "query": _clip(given.get("query"), 400)[0],
                        "database": _clip(given.get("database"), 80)[0], "source": _clip(out.get("source"), 80)[0],
                        "results": results})
        elif kind == "fetch":
            content = out.get("content") if isinstance(out.get("content"), str) else ""
            web.append({**base, "type": "fetch", "url": _web_url(given.get("url")), "finalUrl": _web_url(out.get("url")),
                        "download": bool(given.get("path")), "excerpt": _clip(content, 600)[0], "chars": len(content),
                        "error": _clip(out.get("error"), 600)[0]})
    seqs = [_count(row.get("seq")) for row in rows if isinstance(row, dict)]
    return {"commands": commands[-_STEP_LIMIT:], "web": web[-_STEP_LIMIT:], "capped": len(rows) >= 800,
            "lastSeq": max([n for n in seqs if n is not None], default=0)}


def shape_skills(result):
    rows = result.get("skills") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    skills = []
    for row in rows[:2000]:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            continue
        readiness = row.get("readiness") if isinstance(row.get("readiness"), dict) else {}
        skills.append({"name": _clip(row["name"], 128)[0], "title": _clip(row.get("displayName") or row["name"], 160)[0],
                       "description": _clip(row.get("description"), 400)[0],
                       "scope": row.get("scope") if row.get("scope") in ("bundled", "personal", "project") else "bundled",
                       "collection": _clip(row.get("collection"), 80)[0], "editable": row.get("editable") is True,
                       "enabled": row.get("enabled") is not False,
                       "ready": readiness.get("state") if readiness.get("state") in ("ready", "needs_setup", "unknown") else "unknown",
                       "missing": _names(readiness.get("missing"))[:8]})
    return {"skills": skills}


def shape_connectors(result):
    """Name, description and state only: no launch command, arguments or environment names."""
    rows = result.get("connectors") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    connectors = []
    for row in rows[:200]:
        ident = row.get("connector_id") if isinstance(row, dict) else None
        if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", ident):
            continue
        known = CONNECTOR_ALLOWLIST.get(ident)
        connectors.append({"id": ident, "name": known[0] if known else _clip(row.get("name") or ident, 120)[0],
                           "description": known[1] if known else _clip(row.get("description"), 400)[0],
                           "enabled": row.get("enabled") is not False and row.get("enabled") != 0,
                           "managed": row.get("managed") is True, "hasCredentials": row.get("has_env") is True,
                           "leoChecked": known is not None})
    available = [{"id": ident, "name": name, "description": text} for ident, (name, text) in CONNECTOR_ALLOWLIST.items()
                 if ident not in {c["id"] for c in connectors}]
    return {"connectors": connectors, "available": available}


def shape_probe(result):
    """Tool names when the connector answered; a failure carries no text (it can echo arguments)."""
    if not isinstance(result, dict) or result.get("ok") is not True:
        return {"ok": False, "tools": []}
    tools = result.get("tools") if isinstance(result.get("tools"), list) else []
    names = [_clip(tool.get("name"), 80)[0] for tool in tools if isinstance(tool, dict) and isinstance(tool.get("name"), str)]
    return {"ok": True, "tools": names[:50], "count": len(names)}


def shape_ok(result):
    return {"ok": True}


def shape_search_config(result):
    """Only whether a search key is set; the daemon never returns the key, and nothing else is passed on."""
    if not isinstance(result, dict):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    return {"configured": result.get("api_key_configured") is True}


def shape_python_interrupt(result):
    # The daemon answers ok: false when that cell holds no running lease (still queued, or already done).
    if not isinstance(result, dict) or result.get("ok") is False:
        raise ValueError("PYTHON_INTERRUPT_REFUSED")
    return {"ok": True}


def shape_terminal_run(result):
    if not isinstance(result, dict) or result.get("status") != "accepted":
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    position = result.get("queue_position")
    return {"accepted": True, "queuePosition": position if isinstance(position, int) and not isinstance(position, bool) else None}


def shape_upload(result):
    if not isinstance(result, dict):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    ident = result.get("artifact_id") or result.get("id")
    if not isinstance(ident, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", ident):
        raise ValueError("WORKBENCH_RESPONSE_INVALID")
    return {"id": ident, "filename": _clip(result.get("filename"), 255)[0]}


_SHAPERS = {"notebook": shape_notebook, "artifacts": shape_artifacts, "kernel": shape_kernel,
            "feedback": shape_feedback, "timeline": shape_timeline, "thoughts": shape_thoughts,
            "steps": shape_steps, "terminal_run": shape_terminal_run, "python_run": shape_terminal_run,
            "python_interrupt": shape_python_interrupt, "upload": shape_upload,
            "skills": shape_skills, "connectors": shape_connectors, "connector_probe": shape_probe,
            "skill_toggle": shape_ok, "skill_import": shape_ok, "skill_delete": shape_ok,
            "connector_toggle": shape_ok, "connector_delete": shape_ok,
            "context": shape_context,
            "search_config": shape_search_config, "search_key_save": shape_search_config,
            "search_key_clear": shape_search_config}
# Operations whose raw daemon answer may exceed the ordinary limit before it is trimmed.
_LARGE_OPERATIONS = {"notebook", "thoughts", "steps", "skills"}
# Operations that may take longer than an ordinary call: a file of up to 25 MB crosses to the daemon.
_SLOW_OPERATIONS = {"upload": 180, "connector_probe": 90}


class WorkbenchGateway:
    def __init__(self, client_url, opener=None):
        self._client_url = client_url
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())

    def purge(self, kind, ident):
        # Deliberately absent from the generic browser operation router.
        if kind not in {"session", "project"}:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        path = ("/frames/" if kind == "session" else "/projects/") + identifier(ident)
        raw, _ = self._exchange("DELETE", path, None, _JSON_LIMIT)
        if len(raw) > _JSON_LIMIT:
            raise ValueError("WORKBENCH_RESPONSE_INVALID")
        result = json.loads(raw)
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise ValueError("WORKBENCH_RESPONSE_INVALID")
        return result

    def add_connector(self, payload):
        """3.1.0 · Add a connector from the daemon's own directory, only if Leo has checked it."""
        ident = payload.get("id") if isinstance(payload, dict) else None
        if ident not in CONNECTOR_ALLOWLIST:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        raw, _ = self._exchange("GET", "/connectors/directory", None, _JSON_LIMIT)
        try:
            directory = json.loads(raw).get("directory")
        except (ValueError, AttributeError):
            raise ValueError("WORKBENCH_RESPONSE_INVALID") from None
        entry = next((item for item in directory or [] if isinstance(item, dict) and item.get("id") == ident), None)
        command = entry.get("command") if entry else None
        if (not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command)
                or entry.get("env")):
            raise ValueError("WORKBENCH_RESPONSE_INVALID")
        body = {"connector_id": ident, "name": entry.get("name") or ident, "description": entry.get("description") or "",
                "command": command, "enabled": True}
        if isinstance(entry.get("args"), list):
            body["args"] = entry["args"]
        self._exchange("POST", "/connectors", body, _JSON_LIMIT)
        return {"ok": True}

    def request(self, payload):
        operation = payload.get("operation") if isinstance(payload, dict) else None
        local = _LOCAL_HANDLERS.get(operation) if isinstance(operation, str) else None
        if local is not None:
            return {"ok": True, "data": local(payload)}
        method, path, body = route(payload)
        if operation == "artifact_preview":
            return {"ok": True, "data": self._preview(payload, path)}
        limit = _NOTEBOOK_JSON_LIMIT if operation in _LARGE_OPERATIONS else _JSON_LIMIT
        slow = _SLOW_OPERATIONS.get(operation)
        raw, _ = self._exchange(method, path, body, limit, slow) if slow else self._exchange(method, path, body, limit)
        if len(raw) > limit:
            raise ValueError("WORKBENCH_RESPONSE_INVALID")
        try:
            result = json.loads(raw)
        except ValueError:
            raise ValueError("WORKBENCH_UNAVAILABLE") from None
        shaper = _SHAPERS.get(operation)
        if shaper is not None:
            return {"ok": True, "data": shaper(result)}
        if not isinstance(result, dict):
            raise ValueError("WORKBENCH_RESPONSE_INVALID")
        return {"ok": True, "data": result}

    def _preview(self, payload, path):
        """Only an artifact listed for the open session may be previewed."""
        listing = self.request({"operation": "artifacts", "frameId": payload.get("frameId")})["data"]["artifacts"]
        meta = next((item for item in listing if item["id"] == payload.get("artifactId")), None)
        if meta is None:
            raise ValueError("WORKBENCH_NOT_FOUND")
        raw, content_type = self._exchange("GET", path, None, _PREVIEW_IMAGE_LIMIT)
        return preview_payload(raw, content_type, meta)

    def _forget_url(self):
        """The sign-in URL is cached by the bridge; drop it after a failure so it is asked for again."""
        invalidate = getattr(getattr(self._client_url, "__self__", None), "invalidate_client_url", None)
        if callable(invalidate):
            invalidate()

    def _exchange(self, method, path, body, limit, timeout=30):
        """Read at most ``limit + 1`` bytes so callers can tell a cut from a fit.

        A refused token (401/403) never ran anything, so it is retried once with a fresh URL.
        A connection failure is retried only for reads: a write may already have landed.
        """
        try:
            return self._exchange_once(method, path, body, limit, timeout)
        except _StaleEndpoint as stale:
            self._forget_url()
            if not stale.retry and method != "GET":
                raise ValueError("WORKBENCH_UNAVAILABLE") from None
            try:
                return self._exchange_once(method, path, body, limit, timeout)
            except _StaleEndpoint:
                raise ValueError("WORKBENCH_UNAVAILABLE") from None

    def _exchange_once(self, method, path, body, limit, timeout=30):
        url = self._client_url()
        if not WslBridge._is_valid_client_url(url):
            raise ValueError("WORKBENCH_UNAVAILABLE")
        parsed = urlsplit(url)
        tokens = parse_qs(parsed.query).get("token", [])
        if len(tokens) != 1 or not tokens[0] or any(ord(c) < 33 for c in tokens[0]):
            raise ValueError("WORKBENCH_UNAVAILABLE")
        headers = {"Authorization": "Bearer " + tokens[0], "Content-Type": "application/json"}
        request = Request("http://" + parsed.netloc + "/api/v1" + path,
                          data=json.dumps(body, allow_nan=False).encode() if body is not None else None,
                          headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=timeout) as response:
                raw = response.read(limit + 1)
                received = getattr(response, "headers", None)
                content_type = received.get("Content-Type", "") if received is not None else ""
            return raw, content_type
        except HTTPError as error:
            # Return known public codes only; never reflect an arbitrary server body.
            public_codes = {"MODEL_BINDING_CONFLICT", "MODEL_REVISION_UNAVAILABLE", "MODEL_SELECTION_REQUIRED",
                            "MODEL_KEY_UNAVAILABLE", "MODEL_CREDENTIALS_NOT_READY", "REASONING_CAPABILITY_CHANGED"}
            try:
                payload = json.loads(error.read(8193))
                code = payload.get("code", "").upper() if isinstance(payload, dict) else ""
            except (ValueError, AttributeError, OSError):
                code = ""
            if code in public_codes:
                raise ValueError(code) from None
            if error.code in (401, 403):
                raise _StaleEndpoint(retry=True) from None
            raise ValueError("WORKBENCH_CONFLICT" if error.code == 409 else "WORKBENCH_REQUEST_FAILED") from None
        except OSError:
            raise _StaleEndpoint(retry=False) from None


class _StaleEndpoint(Exception):
    """The cached daemon URL did not work; ``retry`` is True when nothing can have run."""

    def __init__(self, retry):
        super().__init__("WORKBENCH_UNAVAILABLE")
        self.retry = retry
