"""Exact source transforms and isolated, durable public model projections.

No model execution or installation occurs when importing this module. The
central runtime installer owns source verification and installing all patches.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

VERSION = 1
MAX_TEXT = 262144
TABLE = "leo_model_projections"
SCHEMA = '''CREATE TABLE leo_model_projections (
    projection_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    root_frame_id TEXT NOT NULL REFERENCES frames(frame_id) ON DELETE CASCADE,
    branch_id TEXT NOT NULL,
    event_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY (projection_id, seq)
)'''


class ProjectionError(RuntimeError):
    pass


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _schema(store, *, create: bool) -> bool:
    connection = store._conn
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise ProjectionError("LEO_PROJECTION_FOREIGN_KEYS_DISABLED")
    row = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone()
    if row is None:
        if not create:
            return False
        connection.execute(SCHEMA)
        connection.commit()
        row = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone()
    if row[0] != SCHEMA:
        raise ProjectionError("LEO_PROJECTION_SCHEMA_MISMATCH")
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (TABLE,)).fetchone():
        raise ProjectionError("LEO_PROJECTION_SCHEMA_MISMATCH")
    foreign = connection.execute("PRAGMA foreign_key_list(leo_model_projections)").fetchall()
    if len(foreign) != 1 or tuple(foreign[0])[2:7] != ("frames", "root_frame_id", "frame_id", "NO ACTION", "CASCADE"):
        raise ProjectionError("LEO_PROJECTION_SCHEMA_MISMATCH")
    return True


def _append(store, event: dict) -> None:
    raw = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    with store._lock:
        if store._conn.in_transaction:
            raise ProjectionError("LEO_PROJECTION_TRANSACTION_ALREADY_ACTIVE")
        _schema(store, create=True)
        try:
            store._conn.execute(
                "INSERT INTO leo_model_projections(projection_id,seq,root_frame_id,branch_id,event_json,created_at) VALUES(?,?,?,?,?,?)",
                (event["projection_id"], event["seq"], event["frame_id"], event["branch_id"], raw, int(time.time()*1000)))
            store._conn.commit()
        except Exception:
            store._conn.rollback()
            raise


def read_projections(store, root_frame_id: str, branch_id: str | None = None) -> dict:
    """Read only this session/branch; never expose arbitrary wire-state blobs."""
    branch_id = branch_id or root_frame_id
    with store._lock:
        if not _schema(store, create=False):
            return {"version": VERSION, "projections": [], "has_more": False}
        ids = store._conn.execute(
            "SELECT projection_id, MAX(created_at) AS last_at FROM leo_model_projections WHERE root_frame_id=? AND branch_id=? GROUP BY projection_id ORDER BY last_at DESC, projection_id DESC LIMIT 501",
            (root_frame_id, branch_id)).fetchall()
        selected = [row[0] for row in ids[:500]]
        result = []
        for projection_id in reversed(selected):
            events = store._conn.execute(
                "SELECT seq,event_json FROM leo_model_projections WHERE projection_id=? AND root_frame_id=? AND branch_id=? ORDER BY seq",
                (projection_id, root_frame_id, branch_id)).fetchall()
            text, current = "", None
            for expected, row in enumerate(events, 1):
                event = json.loads(row[1])
                if (row[0] != expected or event.get("seq") != expected
                        or event.get("projection_id") != projection_id
                        or event.get("frame_id") != root_frame_id or event.get("branch_id") != branch_id):
                    raise ProjectionError("LEO_PROJECTION_EVIDENCE_INVALID")
                if event["op"] == "append":
                    text += event["text"]
                elif event["op"] not in {"bind", "terminal"}:
                    raise ProjectionError("LEO_PROJECTION_EVIDENCE_INVALID")
                if len(text) > MAX_TEXT:
                    raise ProjectionError("LEO_PROJECTION_EVIDENCE_INVALID")
                current = event
            if current is not None:
                result.append({**current, "op": "snapshot", "text": text,
                               "content_sha256": _sha(text)})
        return {"version": VERSION, "projections": result, "has_more": len(ids) > 500}


class ProjectionState:
    """One engine iteration; every published event first becomes durable."""

    def __init__(self, store, send, *, frame_id, branch_id, turn_id, execution_id,
                 engine_turn, provider, model):
        if (type(engine_turn) is not int or engine_turn < 0
                or any(type(value) is not str or not value for value in
                       (frame_id, branch_id, turn_id, execution_id))):
            raise ProjectionError("LEO_PROJECTION_IDENTITY_INVALID")
        self.store, self.send = store, send
        self.identity = dict(frame_id=frame_id, branch_id=branch_id, turn_id=turn_id,
                             execution_id=execution_id, engine_turn=engine_turn,
                             provider=provider, model=model)
        self.channels = {}
        self.group_id = None

    def projection_id(self, channel):
        return f"leo:{self.identity['execution_id']}:{self.identity['engine_turn']}:{channel}"

    def _publish(self, channel, op, **values):
        state = self.channels.setdefault(channel, {"seq": 0, "text": "", "status": "running"})
        event = {"type": "leo_model_projection", "version": VERSION,
                 **self.identity, "projection_id": self.projection_id(channel), "channel": channel,
                 "op": op, "seq": state["seq"]+1, "group_id": self.group_id,
                 "status": state["status"],
                 **({"source_field": state["source_field"]} if channel == "thought" and "source_field" in state else {}),
                 **values}
        _append(self.store, event)
        state["seq"] = event["seq"]
        # UI delivery may fail after persistence; do not repeat a committed
        # provider request. REST replay recovers the same identity/sequence.
        self.send(event)

    def append(self, channel, text, source_field=None):
        if channel not in {"thought", "progress"} or type(text) is not str:
            raise ProjectionError("LEO_PROJECTION_CONTENT_INVALID")
        if not text:
            return
        if channel == "thought" and source_field not in {"reasoning_content", "reasoning"}:
            raise ProjectionError("LEO_THOUGHT_SOURCE_INVALID")
        state = self.channels.setdefault(channel, {"seq": 0, "text": "", "status": "running"})
        if state["status"] != "running":
            raise ProjectionError("LEO_PROJECTION_ALREADY_TERMINAL")
        if len(state["text"])+len(text) > MAX_TEXT:
            raise ProjectionError("LEO_PROJECTION_TOO_LARGE")
        if channel == "thought":
            state["source_field"] = source_field
        self._publish(channel, "append", text=text, **({"source_field": source_field} if source_field else {}))
        state["text"] += text

    def progress_send(self, event):
        if event.get("type") == "text_chunk" and event.get("block_type") == "text":
            self.append("progress", event.get("chunk", ""))
        else:
            self.send(event)

    def bind(self, group_id):
        if type(group_id) is not str or not group_id:
            raise ProjectionError("LEO_PROJECTION_GROUP_MISSING")
        self.group_id = group_id
        for channel in self.channels:
            self._publish(channel, "bind")

    def finish(self, status):
        if status not in {"completed", "failed", "cancelled"}:
            raise ProjectionError("LEO_PROJECTION_STATUS_INVALID")
        for channel, state in self.channels.items():
            if state["status"] == "running":
                self._publish(channel, "terminal", status=status)
                state["status"] = status

    def metadata(self, text, channel="progress"):
        return {"version": VERSION, **self.identity, "channel": channel,
                "projection_id": self.projection_id(channel), "group_id": self.group_id,
                "content_sha256": _sha(text)}


def merged_metadata(existing, projection):
    result = dict(existing or {})
    if projection is not None:
        result["leo_projection"] = projection
    return result or None


def candidate_metadata(text, blocks, final_block, *, turn_id, execution_id):
    """Annotate existing exact candidate bytes; never rewrite reviewed input."""
    segments = [{"channel": "progress", "text": str(block.get("text") or "")} for block in blocks]
    if final_block is not None:
        final_text = str(final_block["text"])
        final_segments = final_block.get("leo_segments")
        if final_segments is None:
            segments.append({"channel": "final", "text": final_text})
        elif _valid_final_segments(final_text, final_segments):
            segments.extend(final_segments)
        else:
            return None
    joined = "\n\n".join(item["text"] for item in segments).strip()
    if joined != text:
        return None
    return {"version": VERSION, "channel": "candidate", "turn_id": turn_id,
            "execution_id": execution_id, "content_sha256": _sha(text),
            "segments": [{**item, "content_sha256": _sha(item["text"])} for item in segments]}


def _valid_final_segments(text, segments):
    return (type(segments) is list and all(type(item) is dict and item.get("channel") in {"final", "completion_record"}
            and type(item.get("text")) is str for item in segments)
            and "\n\n".join(item["text"] for item in segments) == text)


def final_metadata(text, *, turn_id, execution_id, segments=None):
    result = {"version": VERSION, "channel": "final", "turn_id": turn_id,
              "execution_id": execution_id, "projection_id": "leo:"+execution_id+":final",
              "content_sha256": _sha(text)}
    if segments is not None and _valid_final_segments(text, segments):
        result["segments"] = [{**item, "content_sha256": _sha(item["text"])} for item in segments]
    return result


def attach_reasoning(message, reasoning):
    if reasoning is not None and type(reasoning) is not str:
        raise ProjectionError("LEO_THOUGHT_CONTENT_INVALID")
    return {**message, **({"reasoning_content": reasoning} if reasoning else {})}


def runtime_modules():
    root = Path(__file__).parent
    return {"openai4s/leo_reasoning.py": (root/"leo_reasoning.py").read_bytes(),
            "openai4s/leo_thought.py": Path(__file__).read_bytes()}


def patches():
    """Return whole-source-bound replacements; the central installer applies."""
    return _PATCHES


_PATCHES = {
    "openai4s/server/completions.py": {
        "source_sha256": "d917d69948778424b6c5ca772fe766c7386e321755e948d5903ca0a5179fecca",
        "replacements": [
            ("    trusted_delivery: bool = False,\n", "    trusted_delivery: bool = False,\n    leo_segments: list | None = None,\n"),
            ("    previous = _normalized(previous_text)\n    parts: list[str] = []\n",
             "    previous = _normalized(previous_text)\n    parts: list[str] = []\n"
             "    completion_index = None\n"
             "    if leo_segments is not None:\n"
             "        if type(leo_segments) is not list:\n            raise TypeError(\"LEO_COMPLETION_SEGMENTS_INVALID\")\n"
             "        leo_segments.clear()\n"),
            ("        parts.append(heading + \"\\n\" + \"\\n\".join(f\"- {item}\" for item in fresh_bullets))\n",
             "        completion_index = len(parts)\n"
             "        parts.append(heading + \"\\n\" + \"\\n\".join(f\"- {item}\" for item in fresh_bullets))\n"),
            ('''    if not parts and require_fallback:
        return "任务已完成。" if zh else "The task is complete."
    return "\\n\\n".join(parts)
''', '''    if not parts and require_fallback:
        if leo_segments is not None:
            leo_segments.append({"channel": "final", "text": "任务已完成。" if zh else "The task is complete."})
        return "任务已完成。" if zh else "The task is complete."
    if leo_segments is not None:
        leo_segments.extend({"channel": "completion_record" if index == completion_index else "final", "text": part}
                            for index, part in enumerate(parts))
    return "\\n\\n".join(parts)
'''),
        ],
    },
    "openai4s/server/gateway.py": {
        "source_sha256": "db33c3e3e7b4d618881e7899646d8de55c9c1794b47f57c5b97c7d2a2227a192",
        "replacements": [
            ("from openai4s.server.action_timeline import ActionTimelineService\n",
             "from openai4s.server.action_timeline import ActionTimelineService\n"
             "from openai4s.leo_thought import read_projections, merged_metadata, candidate_metadata, final_metadata\n"),
            ("            \"candidate_resolved\",\n        ):\n",
             "            \"candidate_resolved\",\n            \"leo_model_projection\",\n        ):\n"),
            ("            gate_mode = \"off\"\n",
             "            action_ledger.leo_execution_id = turn_execution_id\n"
             "            st.leo_turn_id = str(action_ledger.turn_id)\n"
             "            gate_mode = \"off\"\n"),
            ("        result = engine.run(state)\n        st.last_engine_completion = result.completion\n",
             "        try:\n            result = engine.run(state)\n"
             "        except BaseException:\n"
             "            events.finish_projection(\"cancelled\" if st.cancel.is_set() else \"failed\")\n"
             "            raise\n"
             "        events.finish_projection(\"completed\" if result.stop_reason in {\"submitted\", \"plan\"} else \"cancelled\" if result.stop_reason == \"cancelled\" else \"failed\")\n"
             "        st.last_engine_completion = result.completion\n"),
            ("                    previous_text=prior_text,\n",
             "                    previous_text=prior_text if gate_armed else \"\",\n"),
            ("                    require_fallback=not bool(st.last_model_prose.strip()),\n",
             "                    require_fallback=(not bool(st.last_model_prose.strip())) if gate_armed else True,\n"),
            ("                final_text = completion_message(\n", "                leo_final_segments = []\n                final_text = completion_message(\n"),
            ("                    trusted_delivery=self.stage1_trusted_delivery,\n                )\n                if final_text:\n",
             "                    trusted_delivery=self.stage1_trusted_delivery,\n"
             "                    leo_segments=leo_final_segments,\n                )\n                if final_text:\n"),
            ("                            \"artifacts\": produced_artifacts,\n                        }\n                    else:\n",
             "                            \"artifacts\": produced_artifacts,\n"
             "                            \"leo_segments\": leo_final_segments,\n                        }\n                    else:\n"),
            ("                            final_text=final_text,\n                            delivered_at=delivered_at,\n",
             "                            final_text=final_text,\n                            leo_segments=leo_final_segments,\n                            delivered_at=delivered_at,\n"),
            ("        already_streamed: bool = False,\n        message_metadata: Mapping[str, Any] | None = None,\n",
             "        already_streamed: bool = False,\n        leo_segments: list | None = None,\n        message_metadata: Mapping[str, Any] | None = None,\n"),
            ("                    \"candidate_content_sha256\": candidate_original_sha256,\n                }\n                if candidate_answer:\n",
             "                    \"candidate_content_sha256\": candidate_original_sha256,\n"
             "                    \"leo_projection\": candidate_metadata(candidate_answer, assistant_visible, candidate_final,\n"
             "                        turn_id=str(action_ledger.turn_id), execution_id=turn_execution_id),\n"
             "                }\n                if candidate_answer:\n"),
            ("                                    \"chunk\": str(candidate_final[\"text\"]) + \"\\n\",\n",
             "                                    \"chunk\": str(candidate_final[\"text\"]) + \"\\n\",\n"
             "                                    \"leo_projection\": provisional_metadata.get(\"leo_projection\"),\n"),
            ("                    created_at=blk.get(\"at\"),\n                    metadata=provisional_metadata,\n",
             "                    created_at=blk.get(\"at\"),\n"
             "                    metadata=merged_metadata(provisional_metadata, blk.get(\"leo_projection\")),\n"),
            ("                        created_at=block.get(\"at\"),\n                    )\n                    block[\"persisted\"] = True\n",
             "                        created_at=block.get(\"at\"),\n"
             "                        metadata=merged_metadata(None, block.get(\"leo_projection\")),\n"
             "                    )\n                    block[\"persisted\"] = True\n"),
            ("        if self.stage1_trusted_delivery and produced_artifacts:\n            try:\n                delivery_service = self.completion_delivery\n",
             "        if not (message_metadata or {}).get(\"leo_projection\"):\n"
             "            message_metadata = merged_metadata(message_metadata, final_metadata(final_text,\n"
             "                turn_id=getattr(st, \"leo_turn_id\", execution_id), execution_id=execution_id, segments=leo_segments))\n"
             "        if self.stage1_trusted_delivery and produced_artifacts:\n            try:\n                delivery_service = self.completion_delivery\n"),
            ("                    \"message_id\": message_id,\n                }\n            )\n            if not already_streamed:\n",
             "                    \"message_id\": message_id,\n"
             "                    \"leo_projection\": message_metadata.get(\"leo_projection\"),\n"
             "                }\n            )\n            if not already_streamed:\n"),
            ("                        \"message_id\": message_id,\n                    }\n                )\n            if publish:\n",
             "                        \"message_id\": message_id,\n"
             "                        \"leo_projection\": message_metadata.get(\"leo_projection\"),\n"
             "                    }\n                )\n            if publish:\n"),
            ("        assistant_visible.append({\"at\": delivered_at, \"text\": final_text})\n",
             "        assistant_visible.append({\"at\": delivered_at, \"text\": final_text,\n"
             "                                  \"leo_projection\": message_metadata.get(\"leo_projection\")})\n"),
            ('''                    "chunk": final_text + "\\n",
                }
            )
        return {
            "ok": True,''',
             '''                    "chunk": final_text + "\\n",
                    "leo_projection": message_metadata.get("leo_projection"),
                }
            )
        return {
            "ok": True,'''),
            ("                r\"action-timeline|execution-queue|context|security|\"\n",
             "                r\"action-timeline|leo-projections|execution-queue|context|security|\"\n"),
            ("            m = re.fullmatch(r\"/frames/([^/]+)/action-timeline\", sub)\n",
             "            m = re.fullmatch(r\"/frames/([^/]+)/leo-projections\", sub)\n"
             "            if m and method == \"GET\":\n"
             "                self._json(read_projections(store, m.group(1), (q.get(\"branch_id\") or [None])[0]))\n"
             "                return\n"
             "            m = re.fullmatch(r\"/frames/([^/]+)/action-timeline\", sub)\n"),
        ],
    },
    "openai4s/config.py": {
        "source_sha256": "8e50e9fa301993340f79a30a8072a41b535d6e618af8c7efece547e3cab5b33b",
        "replacements": [("    timeout_s: float = float(os.environ.get(\"OPENAI4S_LLM_TIMEOUT\", \"120\"))\n",
                          "    timeout_s: float = float(os.environ.get(\"OPENAI4S_LLM_TIMEOUT\", \"120\"))\n"
                          "    reasoning_choice: str = \"default\"\n"
                          "    reasoning_capability_revision: str | None = None\n"
                          "    reasoning_snapshot: dict | None = None\n")],
    },
    "openai4s/agent/events.py": {
        "source_sha256": "d0bc5b4ae08cfc4efca3a841fedbede25fc3e35b1ae218e6d915b440ee828b63",
        "replacements": [
            ("@dataclass(frozen=True)\nclass ReplyReceived:",
             "@dataclass(frozen=True)\nclass ReasoningDelta:\n    text: str\n    turn: int\n    source_field: str\n\n\n@dataclass(frozen=True)\nclass ReplyReceived:"),
            ("    | TextDelta\n", "    | TextDelta\n    | ReasoningDelta\n"),
        ],
    },
    "openai4s/agent/engine.py": {
        "source_sha256": "eb087db2144d9d7d0040968376e3208d8891c60844dc552980825556350c2d1c",
        "replacements": [
            ("    TextDelta,\n", "    TextDelta,\n    ReasoningDelta,\n"),
            ("            raw_reply = self.model.complete(state.messages, on_delta)\n",
             "            # Optional independent channel preserves the existing callable ModelPort.\n"
             "            on_delta.reasoning_delta = lambda text, source: self.event_sink.emit(ReasoningDelta(text, turn, source))\n"
             "            on_delta.fatal_projection_errors = True\n"
             "            raw_reply = self.model.complete(state.messages, on_delta)\n"),
        ],
    },
    "openai4s/llm/providers/openai.py": {
        "source_sha256": "2a8e28801717493dd9bd26cff691978e31930aa957c6d0a4e52fed2af6ab6447",
        "replacements": [
            ("from ..messages import _openai_messages\n",
             "from ..messages import _openai_messages\nfrom openai4s.leo_reasoning import apply_request\nfrom openai4s.leo_thought import attach_reasoning\n"),
            ("    effort = os.environ.get(\"OPENAI4S_LLM_REASONING_EFFORT\")\n    if effort:\n        payload[\"reasoning_effort\"] = effort\n",
             "    payload = apply_request(payload, cfg, base, model)\n"),
            ("    content = msg.get(\"content\") or \"\"\n", "    content = msg.get(\"content\") or \"\"\n"
             "    rc = msg.get(\"reasoning_content\") if msg.get(\"reasoning_content\") is not None else msg.get(\"reasoning\")\n"
             "    if rc is not None and type(rc) is not str:\n        raise LLMError(\"LEO_THOUGHT_CONTENT_INVALID\")\n"),
            ('''        "reasoning": msg.get("reasoning_content"),
        "usage": body.get("usage", {}),
        "finish_reason": "tool_calls" if calls else provider_finish,
        "provider_finish_reason": provider_finish,
        "tool_calls": calls,
        "assistant_message": _assistant_message(content, calls, wire_state),''',
             '''        "reasoning": rc,
        "leo_reasoning_source": "reasoning_content" if msg.get("reasoning_content") is not None else "reasoning",
        "usage": body.get("usage", {}),
        "finish_reason": "tool_calls" if calls else provider_finish,
        "provider_finish_reason": provider_finish,
        "tool_calls": calls,
        "assistant_message": attach_reasoning(_assistant_message(content, calls, wire_state), rc),'''),
            ('''            except Exception:  # noqa: BLE001 — a UI callback must never kill the stream
                pass
        rc = delta.get("reasoning_content") or delta.get("reasoning")
        if rc:
            reasoning.append(rc)
''', '''            except Exception:  # Durable projection failures must stop this request.
                if getattr(on_delta, "fatal_projection_errors", False):
                    raise
        source = "reasoning_content" if delta.get("reasoning_content") is not None else "reasoning"
        rc = delta.get(source)
        if rc is not None and type(rc) is not str:
            raise LLMError("LEO_THOUGHT_CONTENT_INVALID")
        if rc:
            reasoning.append(rc)
            receiver = getattr(on_delta, "reasoning_delta", None)
            if callable(receiver):
                # Thought is public output too: never replay it on retry.
                state["output_committed"] = True
                receiver(rc, source)
'''),
            ('''        "reasoning": "".join(reasoning) or None,
        "usage": state["usage"],
        "finish_reason": "tool_calls" if calls else provider_finish,
        "provider_finish_reason": provider_finish,
        "tool_calls": calls,
        "assistant_message": _assistant_message(content, calls, wire_state),''',
             '''        "reasoning": "".join(reasoning) or None,
        "usage": state["usage"],
        "finish_reason": "tool_calls" if calls else provider_finish,
        "provider_finish_reason": provider_finish,
        "tool_calls": calls,
        "assistant_message": attach_reasoning(_assistant_message(content, calls, wire_state), "".join(reasoning) or None),'''),
        ],
    },
    "openai4s/llm/messages.py": {
        "source_sha256": "b61f50acb576c7e9dda65b0aa207a5eecaf7e6c328043f000ed7c3ad451e5690",
        "replacements": [
            ("        if role == \"assistant\" and message.get(\"tool_calls\"):\n",
             "        if role == \"assistant\" and message.get(\"reasoning_content\") is not None:\n"
             "            if type(message[\"reasoning_content\"]) is not str:\n"
             "                raise LLMError(\"LEO_THOUGHT_CONTENT_INVALID\")\n"
             "            item[\"reasoning_content\"] = message[\"reasoning_content\"]\n"
             "        if role == \"assistant\" and message.get(\"tool_calls\"):\n"),
        ],
    },
    "openai4s/server/agent_run.py": {
        "source_sha256": "cc52e2abd7f0ba287b41e34f14cdf518e15b2f774ea61cde5c568bc60d0659ed",
        "replacements": [
            ("    TextDelta,\n", "    TextDelta,\n    ReasoningDelta,\n"),
            ("from openai4s.agent.runtime import format_observation\n",
             "from openai4s.agent.runtime import format_observation\nfrom openai4s.leo_thought import ProjectionState\n"),
            ("    _current_action: Action | None = field(default=None, init=False)\n",
             "    _current_action: Action | None = field(default=None, init=False)\n"
             "    _leo_projection: Any = field(default=None, init=False)\n"),
            ("        if isinstance(event, TurnStarted):\n            self.current_prose = \"\"\n",
             "        if isinstance(event, TurnStarted):\n"
             "            self.finish_projection(\"completed\")\n"
             "            if self.action_ledger is not None:\n"
             "                ledger = self.action_ledger\n"
             "                self._leo_projection = ProjectionState(ledger.store, self.send, frame_id=self.root_frame_id,\n"
             "                    branch_id=ledger.branch_id or self.root_frame_id, turn_id=ledger.turn_id,\n"
             "                    execution_id=getattr(ledger, \"leo_execution_id\", ledger.turn_id),\n"
             "                    engine_turn=event.turn, provider=ledger.provider, model=ledger.model)\n"
             "            self.current_prose = \"\"\n"),
            ("            self._current_action = None\n            self._streamer = ProseStreamer(\n                self.send,\n",
             "            self._current_action = None\n            self._streamer = ProseStreamer(\n                self._leo_send,\n"),
            ("        if self._streamer is None:\n            self._streamer = ProseStreamer(\n                self.send,\n",
             "        if self._streamer is None:\n            self._streamer = ProseStreamer(\n                self._leo_send,\n"),
            ("        elif isinstance(event, TextDelta):\n",
             "        elif isinstance(event, ReasoningDelta):\n"
             "            if self._leo_projection is not None:\n"
             "                self._leo_projection.append(\"thought\", event.text, event.source_field)\n"
             "        elif isinstance(event, TextDelta):\n"),
            ("        elif isinstance(event, ReplyReceived):\n            streamer = self._ensure_streamer()\n",
             "        elif isinstance(event, ReplyReceived):\n"
             "            if self._leo_projection is not None and event.reply.reasoning:\n"
             "                seen = self._leo_projection.channels.get(\"thought\", {}).get(\"text\", \"\")\n"
             "                if not seen:\n"
             "                    source = event.reply.extra.get(\"leo_reasoning_source\", \"reasoning_content\")\n"
             "                    self._leo_projection.append(\"thought\", event.reply.reasoning, source)\n"
             "                elif seen != event.reply.reasoning:\n"
             "                    raise RuntimeError(\"LEO_THOUGHT_STREAM_MISMATCH\")\n"
             "            streamer = self._ensure_streamer()\n"),
            ("                    {\"at\": int(time.time() * 1000) - 1, \"text\": prose}\n",
             "                    {\"at\": int(time.time() * 1000) - 1, \"text\": prose,\n"
             "                     \"leo_projection\": self._leo_metadata(prose)}\n"),
            ("                if not streamer.emitted_any:\n                    self.send(\n",
             "                if not streamer.emitted_any:\n                    self._leo_send(\n"),
            ("        elif isinstance(event, ActionRouted):\n            self._current_action = event.action\n",
             "        elif isinstance(event, ActionRouted):\n"
             "            if self._leo_projection is not None:\n"
             "                self._leo_projection.bind(self.action_ledger.current_group_id)\n"
             "            self._current_action = event.action\n"),
            ("    def _ensure_streamer(self) -> ProseStreamer:\n",
             "    def finish_projection(self, status):\n"
             "        if self._leo_projection is not None:\n"
             "            self._leo_projection.finish(status)\n\n"
             "    def _leo_send(self, event):\n"
             "        if self._leo_projection is None:\n"
             "            self.send(event)\n"
             "        else:\n"
             "            self._leo_projection.progress_send(event)\n\n"
             "    def _leo_metadata(self, text):\n"
             "        return self._leo_projection.metadata(text) if self._leo_projection is not None else None\n\n"
             "    def _ensure_streamer(self) -> ProseStreamer:\n"),
            ('''                "at": int(time.time() * 1000) - (1 if before_action else 0),
                "text": prose,
''', '''                "at": int(time.time() * 1000) - (1 if before_action else 0),
                "text": prose,
                "leo_projection": self._leo_metadata(prose),
'''),
            ('''        self.send(
            {
                "type": "text_chunk",
                "frame_id": self.root_frame_id,
                "block_type": "text",
                "chunk": prose + "\\n",
''', '''        self._leo_send(
            {
                "type": "text_chunk",
                "frame_id": self.root_frame_id,
                "block_type": "text",
                "chunk": prose + "\\n",
'''),
        ],
    },
}
