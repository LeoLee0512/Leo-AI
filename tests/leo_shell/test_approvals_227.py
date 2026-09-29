"""2.2.7: approval modes become conversation rules; pending tool calls reach the page and get answered."""
import base64
import hashlib
import json
import socket
import struct
import threading

import pytest

from leo_shell import approvals, workbench
from leo_shell.approvals import ApprovalCenter, RULES, public_request, standing_pattern
from leo_shell.websocket_client import WebSocket, WebSocketClosed


class FakeGateway:
    def __init__(self, fail_after=None):
        self.calls, self.next_id, self.fail_after = [], 0, fail_after

    def _exchange(self, method, path, body, limit):
        self.calls.append((method, path, body))
        if method == "POST" and path == "/permissions":
            if self.fail_after is not None and self.next_id >= self.fail_after:
                raise ValueError("WORKBENCH_REQUEST_FAILED")
            self.next_id += 1
            return json.dumps({"ok": True, "rule_id": f"perm_{self.next_id:04d}"}).encode(), "application/json"
        return json.dumps({"ok": True}).encode(), "application/json"


def center(tmp_path, gateway=None):
    return ApprovalCenter(tmp_path, gateway or FakeGateway(), lambda: "http://127.0.0.1:8760/?token=t",
                          start_watcher=False, clock=lambda: 1000.0)


def posted(gateway):
    return [(b["tool"], b["pattern"], b["decision"]) for m, p, b in gateway.calls if m == "POST" and p == "/permissions"]


def test_a_conversation_starts_in_smart_and_its_rules_are_written_once(tmp_path):
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    assert c.mode("f1") == {"mode": "smart"}
    assert c.mode("f1") == {"mode": "smart"}
    assert posted(gateway) == RULES["smart"]
    assert all(b["scope"] == "conversation" and b["frame_id"] == "f1" for m, p, b in gateway.calls if m == "POST")


def test_switching_mode_replaces_only_the_rules_leo_wrote(tmp_path):
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    c.mode("f1")
    c.set_mode("f1", "off")
    deleted = [p for m, p, b in gateway.calls if m == "DELETE"]
    assert deleted == ["/permissions/perm_0001"]
    assert posted(gateway)[1:] == RULES["off"]
    assert json.loads((tmp_path / "approval-modes.json").read_text(encoding="utf-8"))["frames"]["f1"]["mode"] == "off"


def test_off_asks_for_every_tool_the_daemon_allows_by_default_and_auto_allows_every_asked_one():
    off = {tool for tool, _, decision in RULES["off"] if decision == "ask"}
    assert set(approvals.ALLOWED_BY_DEFAULT) <= off
    auto = {tool for tool, _, decision in RULES["auto"] if decision == "allow"}
    assert {"bash", "exec_background", "mcp_call", "credentials_set"} <= auto
    # 2.2.9: Smart lets the model write files (it writes helper scripts constantly) and asks before edits.
    assert RULES["smart"] == [("edit_file", "*", "ask")]
    # No mode ever writes a deny, so the daemon's own deny rules (e.g. *.env) always stay in force.
    assert all(decision != "deny" for rules in RULES.values() for _, _, decision in rules)


def test_a_half_applied_mode_is_rolled_back_and_the_old_mode_kept(tmp_path):
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    c.mode("f1")
    gateway.fail_after = 4
    with pytest.raises(ValueError):
        c.set_mode("f1", "off")
    deleted = [p for m, p, b in gateway.calls if m == "DELETE"]
    assert deleted == ["/permissions/perm_0002", "/permissions/perm_0003", "/permissions/perm_0004"]
    assert json.loads((tmp_path / "approval-modes.json").read_text(encoding="utf-8"))["frames"]["f1"]["mode"] == "smart"


@pytest.mark.parametrize("frame,mode", [("../x", "smart"), ("f1", "yolo"), ("f1", None)])
def test_invalid_mode_requests_are_refused(tmp_path, frame, mode):
    with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
        center(tmp_path).set_mode(frame, mode)


EVENT = {"type": "await_permission", "frame_id": "f1", "decision_id": "perm-1a2b3c", "tool": "bash", "kind": "bash",
         "title": "Running git", "input": {"command": "git push"}, "target": "git push",
         "suggested_patterns": ["git push", "git push *", "git *", "*"], "dangerous": False, "side_effect_class": "read"}


def test_a_pending_request_reaches_its_own_conversation_only(tmp_path):
    c = center(tmp_path)
    c._handle(EVENT)
    request = c.pending("f1")["requests"][0]
    assert request["decisionId"] == "perm-1a2b3c" and request["target"] == "git push"
    assert request["expiresAt"] == 1000.0 + approvals.TIMEOUT_SECONDS
    assert c.pending("f2")["requests"] == []
    c._handle({"type": "permission_resolved", "decision_id": "perm-1a2b3c"})
    assert c.pending("f1")["requests"] == []


def test_credentials_are_never_shown_and_long_input_is_clipped():
    secret = public_request({**EVENT, "tool": "credentials_set", "input": {"value": "sk-secret"}}, 0)
    assert "sk-secret" not in json.dumps(secret)
    long = public_request({**EVENT, "input": {"content": "x" * 5000}}, 0)
    assert len(long["input"]) <= 1201


def test_the_standing_pattern_is_the_broadest_non_wildcard_suggestion():
    assert standing_pattern(public_request(EVENT, 0)) == "git *"
    assert standing_pattern({"patterns": ["*"], "target": "a.txt"}) == "a.txt"


def test_answers_go_to_the_decision_route(tmp_path):
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    c._handle(EVENT)
    c.decide("f1", "perm-1a2b3c", True, "conversation")
    method, path, body = gateway.calls[-1]
    assert (method, path) == ("POST", "/frames/f1/decision")
    assert body == {"decision_id": "perm-1a2b3c", "allow": True, "scope": "conversation", "pattern": "git *"}
    assert c.pending("f1")["requests"] == []
    c.decide("f1", "perm-9", False, "conversation")
    assert gateway.calls[-1][2]["scope"] == "once" and "message" in gateway.calls[-1][2]


@pytest.mark.parametrize("allow,scope", [("yes", "once"), (True, "global"), (True, "project")])
def test_only_once_or_this_conversation_can_be_granted(tmp_path, allow, scope):
    with pytest.raises(ValueError):
        center(tmp_path).decide("f1", "perm-1", allow, scope)


def test_local_operations_never_reach_the_daemon():
    seen = []
    workbench.register_local(("probe_op",), lambda payload: seen.append(payload) or {"x": 1})
    try:
        gateway = workbench.WorkbenchGateway(lambda: pytest.fail("no daemon call expected"))
        assert gateway.request({"operation": "probe_op", "frameId": "f1"}) == {"ok": True, "data": {"x": 1}}
    finally:
        workbench.unregister_local(("probe_op",))
    # Once unregistered the name is just an unknown operation to the bounded router.
    with pytest.raises(ValueError, match="WORKBENCH_INVALID_REQUEST"):
        workbench.WorkbenchGateway(lambda: "").request({"operation": "probe_op", "frameId": "f1"})


# -- the event socket ----------------------------------------------------------------------------

def _frame(payload, opcode=0x1, fin=True):
    head = bytes([(0x80 if fin else 0) | opcode])
    n = len(payload)
    head += bytes([n]) if n < 126 else bytes([126]) + struct.pack("!H", n)
    return head + payload


def _serve_once(frames, received):
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    def run():
        conn, _ = server.accept()
        request = b""
        while b"\r\n\r\n" not in request:
            request += conn.recv(4096)
        key = next(l.split(b":", 1)[1].strip() for l in request.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key"))
        received.append(request)
        accept = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                     b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n")
        for chunk in frames:
            conn.sendall(chunk)
        conn.settimeout(2)
        try:
            received.append(conn.recv(4096))
        except OSError:
            pass
        conn.close()
        server.close()

    threading.Thread(target=run, daemon=True).start()
    return server.getsockname()[1]


def test_the_client_handshakes_reassembles_fragments_and_answers_pings():
    received = []
    message = json.dumps(EVENT).encode()
    port = _serve_once([_frame(b"hi", opcode=0x9), _frame(message[:10], fin=False), _frame(message[10:], opcode=0x0),
                        _frame(struct.pack("!H", 1000), opcode=0x8)], received)
    ws = WebSocket.connect("127.0.0.1", port, "/api/v1/ws", {"Authorization": "Bearer t"})
    assert json.loads(ws.recv_text())["decision_id"] == "perm-1a2b3c"
    with pytest.raises(WebSocketClosed):
        ws.recv_text()
    ws.close()
    assert b"Authorization: Bearer t" in received[0]
    assert received[1][0] == 0x8A, "the ping was answered with a pong before anything else"


def test_a_timeout_mid_frame_does_not_lose_the_stream():
    ws = WebSocket.__new__(WebSocket)
    ws._buffer = b""
    frame = _frame(b'{"type":"x"}')
    chunks = [frame[:3], TimeoutError(), frame[3:]]

    class Sock:
        def recv(self, n):
            item = chunks.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
    ws._sock = Sock()
    with pytest.raises(TimeoutError):
        ws.recv_text()
    assert ws.recv_text() == '{"type":"x"}'


def test_the_watcher_subscribes_and_collects_requests(tmp_path):
    sent, done = [], threading.Event()

    class FakeSocket:
        def __init__(self):
            self.queue = [json.dumps(EVENT)]

        def settimeout(self, s):
            pass

        def send_text(self, text):
            sent.append(json.loads(text))

        def recv_text(self):
            if self.queue:
                return self.queue.pop(0)
            done.set()
            raise WebSocketClosed()

        def close(self):
            pass

    c = ApprovalCenter(tmp_path, FakeGateway(), lambda: "http://127.0.0.1:8760/?token=t",
                       connect=lambda *a, **k: FakeSocket())
    try:
        c.watch("f1")
        assert done.wait(5)
        assert {"type": "view_session", "root_frame_id": "f1", "since_seq": 0, "epoch": None} in sent
    finally:
        c.close()


def test_rules_written_by_an_older_version_are_replaced_on_next_open(tmp_path):
    (tmp_path / "approval-modes.json").write_text(json.dumps({"version": 1, "frames": {"f1": {
        "mode": "smart", "rules": ["perm_old_write", "perm_old_edit"], "applied": 1}}}), encoding="utf-8")
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    assert c.mode("f1") == {"mode": "smart"}
    assert posted(gateway) == [("edit_file", "*", "ask")]
    assert sorted(p for m, p, b in gateway.calls if m == "DELETE") == ["/permissions/perm_old_edit", "/permissions/perm_old_write"]
    stored = json.loads((tmp_path / "approval-modes.json").read_text(encoding="utf-8"))["frames"]["f1"]
    assert stored["applied"] == approvals.RULES_VERSION and stored["rules"] == ["perm_0001"]
