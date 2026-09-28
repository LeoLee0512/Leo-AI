"""Bounded native gateway for Leo's own frontend. No daemon token enters HTML."""
import base64
import json
import re
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlsplit
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


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


def text_value(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value.strip()


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
        entries.append({
            "ordinal": ordinal,
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


_SHAPERS = {"notebook": shape_notebook, "artifacts": shape_artifacts, "kernel": shape_kernel,
            "feedback": shape_feedback}


class WorkbenchGateway:
    def __init__(self, client_url, opener=None):
        self._client_url = client_url
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())

    def request(self, payload):
        method, path, body = route(payload)
        operation = payload.get("operation")
        if operation == "artifact_preview":
            return {"ok": True, "data": self._preview(payload, path)}
        limit = _NOTEBOOK_JSON_LIMIT if operation == "notebook" else _JSON_LIMIT
        raw, _ = self._exchange(method, path, body, limit)
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

    def _exchange(self, method, path, body, limit):
        """Read at most ``limit + 1`` bytes so callers can tell a cut from a fit."""
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
            with self._opener.open(request, timeout=30) as response:
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
            raise ValueError("WORKBENCH_CONFLICT" if error.code == 409 else "WORKBENCH_REQUEST_FAILED") from None
        except OSError:
            raise ValueError("WORKBENCH_UNAVAILABLE") from None
