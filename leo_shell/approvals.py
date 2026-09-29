"""Approval mode per conversation, and the approval requests the daemon is waiting on.

The upstream daemon already gates tool calls: a rule decides allow / deny / ask, and an "ask"
blocks the turn until someone answers (it times out as a denial after 15 minutes). Leo never
showed those requests, so a turn that needed approval simply stalled. This module

* keeps each conversation's mode (Off / Smart / Auto) and writes it as conversation-scoped
  rules through the daemon's own permission API (upstream code is never changed);
* listens on the daemon's event socket for ``await_permission`` / ``permission_resolved`` and
  hands the pending requests to the page;
* answers a request through ``POST /frames/{id}/decision``.

Research confirmations are not tool calls and never pass through here: no mode can approve them.
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .websocket_client import WebSocket, WebSocketClosed

MODES = ("off", "smart", "auto")
DEFAULT_MODE = "smart"
RULES_VERSION = 2  # 2: Smart no longer asks before new files are written (owner, 2026-09-29)
TIMEOUT_SECONDS = 900  # upstream permissions.DEFAULT_TIMEOUT

# Tools the daemon allows without asking (storage/permissions.py default rules, version 4).
ALLOWED_BY_DEFAULT = ("read_file", "write_file", "edit_file", "glob", "grep", "list_dir", "save_artifact",
                      "delegate", "env_setup", "web_fetch", "web_search", "science_search")
# Tools that ask by default, by rule or because no rule matches them.
ASKED_BY_DEFAULT = ("bash", "exec_background", "mcp_call", "mcp_resource_read", "mcp_prompt_get",
                    "credentials_set", "skills_edit", "skills_delete", "skills_publish", "skills_rollback",
                    "web_download", "materialise_artifact", "restore_artifact_version", "request_network_access",
                    "compute_submit", "stage_model_asset", "register_remote_capability", "dynamic_tool_define",
                    "dynamic_tool_promote", "dynamic_tool_activate", "dynamic_tool_rollback")
# A conversation rule beats a global one of equal specificity, so these override the defaults.
RULES = {
    "off": [(tool, "*", "ask") for tool in ALLOWED_BY_DEFAULT]
           + [("mcp_call", "volcengine-datapro/dataPro_search", "ask")],
    # The model writes helper scripts all the time (six in one turn of the owner's test), so writing a
    # file stays allowed; changing an existing one (edit_file) asks.
    "smart": [("edit_file", "*", "ask")],
    "auto": [(tool, "*", "allow") for tool in ASKED_BY_DEFAULT],
}
# A rule is Leo's when its (tool, pattern) is one a mode writes. Rules the person grants with
# "allow this kind in this conversation" carry a specific pattern, so they never match.
MANAGED = frozenset((tool, pattern) for rules in RULES.values() for tool, pattern, _ in rules)
# Smart mode answers these commands itself (owner, 2026-09-29: read-only commands such as
# `pip list` should not ask). The daemon gives no per-command verdict for bash, so Leo decides,
# conservatively: the whole command must match one of these forms, and any shell operator,
# quote, expansion or glob sends it back to the person.
_SHELL_SYNTAX = re.compile(r"[;&|<>`$(){}\[\]\\*?!~'\"#\n\r]")
_READ_ONLY_COMMANDS = tuple(re.compile(p) for p in (
    r"(pip3?|python3? -m pip) (list|freeze)( --format[= ](columns|freeze|json))?( (--outdated|-o|--user))*",
    r"(pip3?|python3? -m pip) show [A-Za-z0-9_.\-]+( [A-Za-z0-9_.\-]+){0,9}",
    r"python3? (-V|--version)",
    r"(conda|mamba|micromamba) (list|info|env list)",
    r"ls( -[A-Za-z]+)*( [A-Za-z0-9_./\-]+){0,5}",
    r"pwd|whoami|date|nproc|lscpu|nvidia-smi",
    r"uname( -[a-z]+)?",
    r"(free|df)( -h)?",
    r"which [A-Za-z0-9_.\-]+",
    r"git (status|branch|diff( --stat)?|log( --oneline)?( -n ?[0-9]{1,3})?)",
))


def is_read_only_command(command):
    """True only for a short, plain command that exactly matches a known read-only form."""
    if not isinstance(command, str):
        return False
    text = " ".join(command.split())
    if not text or len(text) > 200 or _SHELL_SYNTAX.search(text):
        return False
    return any(form.fullmatch(text) for form in _READ_ONLY_COMMANDS)


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_DECISION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


def _frame(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("WORKBENCH_INVALID_REQUEST")
    return value


def _clip(value, limit):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + "…"


def public_request(event, received_at):
    """What the page may show about a pending request: bounded, and never a credential."""
    tool = str(event.get("tool") or "")
    data = event.get("input") if isinstance(event.get("input"), dict) else {}
    if tool == "credentials_set":
        data = {}
    patterns = [p for p in event.get("suggested_patterns") or [] if isinstance(p, str)][:6]
    return {"decisionId": event["decision_id"], "tool": tool, "kind": str(event.get("kind") or tool),
            "title": _clip(event.get("title") or tool, 200), "target": _clip(event.get("target") or "", 400),
            "input": _clip(data, 1200) if data else "", "dangerous": event.get("dangerous") is True,
            "sideEffect": _clip(event.get("side_effect_class") or "", 60), "subAgent": event.get("sub_agent") is True,
            "patterns": [_clip(p, 200) for p in patterns],
            "reason": _clip(event.get("policy_review_reason") or "", 400),
            "receivedAt": received_at, "expiresAt": received_at + TIMEOUT_SECONDS}


def standing_pattern(request):
    """The narrowest-but-useful pattern for "allow this kind in this conversation": the most
    general suggestion that is not the bare wildcard, else the exact target. With neither there is
    no pattern short of ``*`` (every call of the tool), which is a mode's rule and not a grant:
    the caller then allows this one call only."""
    candidates = [p for p in request.get("patterns") or [] if p and p != "*"]
    return candidates[-1] if candidates else (request.get("target") or None)


class ModeStore:
    """``user/approval-modes.json``: each conversation's mode and the rule ids Leo wrote for it."""

    def __init__(self, user_dir: Path) -> None:
        self._path = Path(user_dir) / "approval-modes.json"
        self._lock = threading.RLock()

    def read(self) -> dict:
        with self._lock:
            try:
                if self._path.is_symlink():
                    raise OSError
                document = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(document, dict) and isinstance(document.get("frames"), dict):
                    return document
            except (OSError, ValueError):
                pass
            return {"version": 1, "frames": {}}

    def write(self, document: dict) -> None:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            handle, temp = tempfile.mkstemp(dir=self._path.parent, prefix=".approval-", suffix=".tmp")
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    json.dump(document, stream, ensure_ascii=False, sort_keys=True)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, self._path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)


class ApprovalCenter:
    def __init__(self, user_dir: Path, gateway, client_url, *, logger=None, clock=time.time,
                 connect=WebSocket.connect, start_watcher=True) -> None:
        self._store = ModeStore(user_dir)
        self._gateway = gateway          # WorkbenchGateway, for its bounded HTTP exchange
        self._client_url = client_url    # returns the daemon URL with its token
        self._logger = logger or logging.getLogger(__name__)
        self._clock = clock
        self._connect = connect
        self._lock = threading.RLock()
        self._wake = threading.Condition(self._lock)
        self._frames: dict[str, float] = {}   # subscribed conversation -> last interest
        self._pending: dict[str, dict] = {}   # decision id -> public request (+ frameId)
        self._first_seen: dict[str, float] = {}  # survives reconnects, so the countdown does not reset
        self._auto: dict[str, list] = {}         # conversation -> requests Smart answered itself
        self._reconciled: set[str] = set()       # conversations whose daemon rules were checked this run
        self._stop = threading.Event()
        self._url = None
        self._thread = None
        if start_watcher:
            self._thread = threading.Thread(target=self._run, name="leo-approval-watcher", daemon=True)
            self._thread.start()

    # -- modes --------------------------------------------------------------------------------

    def _call(self, method, path, body=None):
        raw, _ = self._gateway._exchange(method, path, body, 1024 * 1024)
        result = json.loads(raw) if raw else {}
        if not isinstance(result, dict):
            raise ValueError("WORKBENCH_RESPONSE_INVALID")
        return result

    def _apply(self, frame_id, mode, previous):
        created = []
        try:
            for tool, pattern, decision in RULES[mode]:
                result = self._call("POST", "/permissions", {"scope": "conversation", "frame_id": frame_id,
                                                              "tool": tool, "pattern": pattern, "decision": decision})
                rule = result.get("rule_id")
                if not isinstance(rule, str) or not _ID.fullmatch(rule):
                    raise ValueError("WORKBENCH_RESPONSE_INVALID")
                created.append(rule)
        except ValueError:
            # Leave no half-applied mode behind: remove what this attempt wrote.
            self._remove(created)
            raise
        # Upserts keyed on (scope, conversation, tool, pattern) may return an id we already own.
        self._remove([rule for rule in previous if rule not in created])
        return created

    def _remove(self, rules):
        for rule in rules:
            try:
                self._call("DELETE", "/permissions/" + rule)
            except ValueError:
                self._logger.info("approval rule %s was already gone", rule)

    def _reconcile(self, frame_id, mode):
        """Make the daemon's conversation rules agree with the mode, and return the ids Leo owns.

        ``approval-modes.json`` only knows the rules Leo wrote through it; a rule written some other
        way (a script, an older build) would keep asking or allowing behind the mode's back. So the
        daemon's own list is the truth: a Leo-managed rule (see ``MANAGED``) that the mode does not
        want is deleted and a wanted one that is missing is written. Rules with any other pattern are
        the person's own grants and are never touched. Returns None when the list is unavailable.
        """
        try:
            listing = self._call("GET", "/frames/" + frame_id + "/permissions")
        except ValueError:
            self._logger.info("approval rules of %s could not be read; not reconciled", frame_id)
            return None
        rules = listing.get("rules")
        found = rules.get("conversation") if isinstance(rules, dict) else None
        if not isinstance(found, list):
            return None
        wanted = set(RULES[mode])
        keep, stray = {}, []
        for rule in found:
            if not isinstance(rule, dict) or not isinstance(rule.get("rule_id"), str) or not _ID.fullmatch(rule["rule_id"]):
                continue
            triple = (rule.get("tool"), rule.get("pattern"), rule.get("decision"))
            if triple[:2] not in MANAGED:
                continue
            if triple in wanted:
                keep[triple] = rule["rule_id"]
            else:
                stray.append(rule["rule_id"])
        if stray:
            self._logger.info("removing %d approval rule(s) of %s that do not belong to %s mode", len(stray), frame_id, mode)
            self._remove(stray)
        owned = list(keep.values())
        try:
            for tool, pattern, decision in RULES[mode]:
                if (tool, pattern, decision) not in keep:
                    result = self._call("POST", "/permissions", {"scope": "conversation", "frame_id": frame_id, "tool": tool,
                                                                  "pattern": pattern, "decision": decision})
                    rule = result.get("rule_id")
                    if not isinstance(rule, str) or not _ID.fullmatch(rule):
                        raise ValueError("WORKBENCH_RESPONSE_INVALID")
                    owned.append(rule)
        except ValueError:
            self._logger.warning("approval rules of %s could not be completed; will retry on next open", frame_id)
            return None
        return owned

    def mode(self, frame_id):
        """The conversation's mode, written to the daemon first if it is not there yet, and checked
        against the daemon's actual rules the first time this run sees the conversation."""
        frame_id = _frame(frame_id)
        with self._lock:
            document = self._store.read()
            entry = document["frames"].get(frame_id) or {}
            mode = entry.get("mode") if entry.get("mode") in MODES else DEFAULT_MODE
            changed = False
            if entry.get("applied") != RULES_VERSION:
                entry = {"mode": mode, "rules": self._apply(frame_id, mode, entry.get("rules") or []),
                         "applied": RULES_VERSION, "updatedAt": int(self._clock())}
                changed = True
            if frame_id not in self._reconciled:
                owned = self._reconcile(frame_id, mode)
                if owned is not None:
                    self._reconciled.add(frame_id)
                    if sorted(owned) != sorted(entry.get("rules") or []):
                        entry = {**entry, "rules": owned, "updatedAt": int(self._clock())}
                        changed = True
            if changed:
                document["frames"][frame_id] = entry
                self._store.write(document)
            return {"mode": mode}

    def set_mode(self, frame_id, mode):
        frame_id = _frame(frame_id)
        if mode not in MODES:
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        with self._lock:
            document = self._store.read()
            entry = document["frames"].get(frame_id) or {}
            rules = self._apply(frame_id, mode, entry.get("rules") or [])
            owned = self._reconcile(frame_id, mode)  # a stray rule of the old mode would outlive the switch
            if owned is not None:
                self._reconciled.add(frame_id)
                rules = owned
            document["frames"][frame_id] = {"mode": mode, "rules": rules, "applied": RULES_VERSION,
                                            "updatedAt": int(self._clock())}
            self._store.write(document)
            return {"mode": mode}

    # -- pending requests ------------------------------------------------------------------------

    def pending(self, frame_id):
        frame_id = _frame(frame_id)
        with self._lock:
            if frame_id not in self._frames:
                self._frames[frame_id] = self._clock()
                self._wake.notify_all()
            self._frames[frame_id] = self._clock()
            now = self._clock()
            items = [dict(r) for r in self._pending.values() if r["frameId"] == frame_id and r["expiresAt"] > now]
            return {"requests": sorted(items, key=lambda r: r["receivedAt"]),
                    "autoApproved": [dict(a) for a in self._auto.get(frame_id, [])[-50:]]}

    def watch(self, frame_id):
        """Subscribe without reading, e.g. before a scheduled message is sent."""
        self.pending(frame_id)

    def decide(self, frame_id, decision_id, allow, scope):
        frame_id = _frame(frame_id)
        if not isinstance(decision_id, str) or not _DECISION.fullmatch(decision_id):
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        if type(allow) is not bool or scope not in ("once", "conversation"):
            raise ValueError("WORKBENCH_INVALID_REQUEST")
        with self._lock:
            request = self._pending.get(decision_id)
        body = {"decision_id": decision_id, "allow": allow, "scope": scope if allow else "once"}
        if allow and scope == "conversation":
            pattern = standing_pattern(request or {})
            if pattern:
                body["pattern"] = pattern
            else:
                body["scope"] = "once"
        if not allow:
            body["message"] = "denied by the user in Leo"
        try:
            self._call("POST", "/frames/" + frame_id + "/decision", body)
        finally:
            # Answered, expired or already resolved elsewhere: in every case it no longer waits here.
            with self._lock:
                self._pending.pop(decision_id, None)
        return {"decided": True}

    # -- event socket ---------------------------------------------------------------------------------

    def _handle(self, message):
        kind = message.get("type") if isinstance(message, dict) else None
        if kind == "await_permission":
            decision, frame = message.get("decision_id"), message.get("frame_id")
            if isinstance(decision, str) and _DECISION.fullmatch(decision) and isinstance(frame, str) and _ID.fullmatch(frame):
                if self._answer_read_only(frame, decision, message):
                    return
                with self._lock:
                    seen = self._first_seen.setdefault(decision, self._clock())
                    request = public_request(message, seen)
                    request["frameId"] = frame
                    self._pending[decision] = request
        elif kind == "permission_resolved":
            with self._lock:
                self._pending.pop(message.get("decision_id"), None)

    def _answer_read_only(self, frame, decision, message):
        """In Smart, a plain read-only command is allowed once without asking, and recorded."""
        if message.get("tool") != "bash" or message.get("dangerous") is True:
            return False
        data = message.get("input") if isinstance(message.get("input"), dict) else {}
        command = data.get("command")
        if not is_read_only_command(command):
            return False
        entry = self._store.read()["frames"].get(frame) or {}
        if (entry.get("mode") if entry.get("mode") in MODES else DEFAULT_MODE) != "smart":
            return False
        with self._lock:
            if any(a["decisionId"] == decision for a in self._auto.get(frame, [])):
                return True  # re-sent after a reconnect; already answered
            self._auto.setdefault(frame, []).append({"decisionId": decision, "command": _clip(" ".join(command.split()), 200),
                                                     "at": self._clock()})
            self._auto[frame] = self._auto[frame][-50:]
        threading.Thread(target=self._auto_decide, args=(frame, decision, message),
                         name="leo-approval-auto", daemon=True).start()
        return True

    def _auto_decide(self, frame, decision, message):
        try:
            self._call("POST", "/frames/" + frame + "/decision",
                       {"decision_id": decision, "allow": True, "scope": "once"})
        except ValueError:
            # Could not answer (already resolved, expired or daemon gone): show it to the person instead.
            self._logger.warning("read-only command could not be approved automatically")
            with self._lock:
                self._auto[frame] = [a for a in self._auto.get(frame, []) if a["decisionId"] != decision]
                request = public_request(message, self._first_seen.setdefault(decision, self._clock()))
                request["frameId"] = frame
                self._pending[decision] = request

    def _endpoint(self):
        if self._url is None:
            self._url = self._client_url()
        parsed = urlsplit(self._url)
        tokens = parse_qs(parsed.query).get("token", [])
        if parsed.hostname not in ("127.0.0.1", "localhost") or len(tokens) != 1:
            self._url = None
            raise ConnectionError("WORKBENCH_UNAVAILABLE")
        return parsed.hostname, parsed.port or 80, tokens[0]

    def _run(self):
        backoff = 1.0
        while not self._stop.is_set():
            with self._lock:
                while not self._frames and not self._stop.is_set():
                    self._wake.wait(5)
                # Forget conversations nobody has looked at for an hour, and long-expired requests.
                for frame, seen in list(self._frames.items()):
                    if self._clock() - seen > 3600:
                        del self._frames[frame]
                for decision, seen in list(self._first_seen.items()):
                    if self._clock() - seen > 2 * TIMEOUT_SECONDS:
                        del self._first_seen[decision]
            if self._stop.is_set():
                return
            try:
                host, port, token = self._endpoint()
                socket = self._connect(host, port, "/api/v1/ws", {"Authorization": "Bearer " + token})
            except Exception:
                self._url = None
                forget = getattr(self._gateway, "_forget_url", None)
                if callable(forget):
                    forget()
                self._stop.wait(backoff)
                backoff = min(backoff * 2, 30.0)
                continue
            backoff = 1.0
            self._serve(socket)

    def _serve(self, socket):
        subscribed = set()
        last_ping = time.monotonic()
        try:
            socket.settimeout(1.0)
            while not self._stop.is_set():
                with self._lock:
                    wanted = set(self._frames)
                for frame in wanted - subscribed:
                    # The daemon re-sends every request still pending for the conversation.
                    socket.send_text(json.dumps({"type": "view_session", "root_frame_id": frame,
                                                 "since_seq": 0, "epoch": None}))
                    subscribed.add(frame)
                for frame in subscribed - wanted:
                    socket.send_text(json.dumps({"type": "unview_session", "root_frame_id": frame}))
                    subscribed.discard(frame)
                if time.monotonic() - last_ping > 20:
                    socket.send_text('{"type":"ping"}')
                    last_ping = time.monotonic()
                try:
                    text = socket.recv_text()
                except TimeoutError:
                    continue
                try:
                    self._handle(json.loads(text))
                except ValueError:
                    continue
        except (WebSocketClosed, OSError, ConnectionError):
            pass
        finally:
            socket.close()
            with self._lock:
                # They come back with the subscription on reconnect.
                self._pending = {k: v for k, v in self._pending.items() if v["frameId"] not in subscribed}

    def close(self):
        self._stop.set()
        with self._lock:
            self._wake.notify_all()
