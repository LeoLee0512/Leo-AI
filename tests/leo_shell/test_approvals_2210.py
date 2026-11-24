"""2.2.10: the daemon's own rule list is the truth, so a stray Leo-managed rule is removed on open."""
import json

from leo_shell import approvals
from leo_shell.approvals import ApprovalCenter, RULES, public_request, standing_pattern


class Daemon:
    """A stateful stand-in for the daemon's permission routes (upsert keyed on tool + pattern)."""

    def __init__(self, rules=()):
        self.rules, self.calls, self.n = {}, [], 0
        for tool, pattern, decision in rules:
            self.add(tool, pattern, decision)

    def add(self, tool, pattern, decision):
        for rule in self.rules.values():
            if (rule["tool"], rule["pattern"]) == (tool, pattern):
                rule["decision"] = decision
                return rule["rule_id"]
        self.n += 1
        rule_id = f"perm_{self.n:04d}"
        self.rules[rule_id] = {"rule_id": rule_id, "scope": "conversation", "tool": tool, "pattern": pattern,
                               "decision": decision}
        return rule_id

    def keys(self):
        return sorted((r["tool"], r["pattern"], r["decision"]) for r in self.rules.values())

    def _exchange(self, method, path, body, limit):
        self.calls.append((method, path, body))
        if method == "GET" and path.endswith("/permissions"):
            reply = {"root_frame_id": "f1", "project_id": "p", "rules": {
                "global": [{"rule_id": "perm_global", "tool": "bash", "pattern": "*", "decision": "ask"}],
                "project": [], "conversation": [dict(r) for r in self.rules.values()]}}
        elif method == "POST" and path == "/permissions":
            reply = {"ok": True, "rule_id": self.add(body["tool"], body["pattern"], body["decision"])}
        elif method == "DELETE":
            self.rules.pop(path.rsplit("/", 1)[1], None)
            reply = {"ok": True}
        else:
            reply = {"ok": True}
        return json.dumps(reply).encode(), "application/json"


def center(tmp_path, daemon):
    return ApprovalCenter(tmp_path, daemon, lambda: "http://127.0.0.1:8760/?token=t", start_watcher=False,
                          clock=lambda: 1000.0)


def stored(tmp_path):
    return json.loads((tmp_path / "approval-modes.json").read_text(encoding="utf-8"))["frames"]["f1"]


def test_a_stray_write_rule_is_removed_when_the_conversation_is_opened(tmp_path):
    # The rule an old live-test script left behind: recorded nowhere, but asking on every write.
    daemon = Daemon([("write_file", "*", "ask"), ("edit_file", "*", "ask")])
    c = center(tmp_path, daemon)
    assert c.mode("f1") == {"mode": "smart"}
    assert daemon.keys() == [("edit_file", "*", "ask")]
    assert stored(tmp_path)["rules"] == [rid for rid, r in daemon.rules.items() if r["tool"] == "edit_file"]


def test_it_is_checked_once_per_run_not_on_every_open(tmp_path):
    daemon = Daemon()
    c = center(tmp_path, daemon)
    c.mode("f1")
    reads = lambda: [1 for m, p, b in daemon.calls if m == "GET"]
    assert len(reads()) == 1
    c.mode("f1")
    c.mode("f1")
    assert len(reads()) == 1


def test_a_rule_the_person_granted_is_never_touched(tmp_path):
    daemon = Daemon([("bash", "pip list", "allow"), ("write_file", "notes/*", "allow"), ("write_file", "*", "ask")])
    center(tmp_path, daemon).mode("f1")
    assert daemon.keys() == sorted([("bash", "pip list", "allow"), ("write_file", "notes/*", "allow"),
                                    ("edit_file", "*", "ask")])
    assert not any(m == "DELETE" and p.endswith(("perm_0001", "perm_0002")) for m, p, b in daemon.calls)


def test_a_missing_mode_rule_is_written_back(tmp_path):
    daemon = Daemon()
    c = center(tmp_path, daemon)
    c.mode("f1")
    daemon.rules.clear()
    c2 = center(tmp_path, daemon)  # a new run of the app
    c2.mode("f1")
    assert daemon.keys() == [("edit_file", "*", "ask")]
    assert stored(tmp_path)["rules"] == list(daemon.rules)


def test_the_global_rules_are_never_deleted(tmp_path):
    daemon = Daemon()
    center(tmp_path, daemon).mode("f1")
    assert not any(m == "DELETE" and "perm_global" in p for m, p, b in daemon.calls)


def test_a_wrong_decision_on_a_managed_rule_is_corrected(tmp_path):
    daemon = Daemon([("edit_file", "*", "allow")])
    center(tmp_path, daemon).mode("f1")
    assert daemon.keys() == [("edit_file", "*", "ask")]


def test_switching_mode_also_clears_strays_of_the_old_mode(tmp_path):
    daemon = Daemon()
    c = center(tmp_path, daemon)
    c.mode("f1")
    daemon.add("write_file", "*", "ask")  # written behind Leo's back
    c.set_mode("f1", "auto")
    assert daemon.keys() == sorted((t, p, d) for t, p, d in RULES["auto"])


def test_an_unreadable_list_is_not_fatal_and_is_retried(tmp_path):
    daemon = Daemon()
    real = daemon._exchange

    def flaky(method, path, body, limit):
        if method == "GET":
            raise ValueError("WORKBENCH_UNAVAILABLE")
        return real(method, path, body, limit)

    daemon._exchange = flaky
    c = center(tmp_path, daemon)
    assert c.mode("f1") == {"mode": "smart"}
    assert "f1" not in c._reconciled
    daemon._exchange = real
    c.mode("f1")
    assert "f1" in c._reconciled


def test_a_grant_with_no_pattern_only_allows_this_one_call(tmp_path):
    assert standing_pattern({}) is None
    assert standing_pattern({"patterns": ["*"], "target": ""}) is None
    daemon = Daemon()
    c = center(tmp_path, daemon)
    c._handle({"type": "await_permission", "frame_id": "f1", "decision_id": "perm-1", "tool": "bash",
               "input": {"command": "make"}, "suggested_patterns": ["*"], "target": ""})
    c.decide("f1", "perm-1", True, "conversation")
    method, path, body = daemon.calls[-1]
    assert path == "/frames/f1/decision" and body["scope"] == "once" and "pattern" not in body
    # A decision whose request the app no longer remembers (it was restarted) must not become a `*` rule.
    c.decide("f1", "perm-2", True, "conversation")
    assert daemon.calls[-1][2]["scope"] == "once" and "pattern" not in daemon.calls[-1][2]


def test_every_managed_key_is_a_rule_some_mode_writes():
    assert ("write_file", "*") in approvals.MANAGED and ("bash", "*") in approvals.MANAGED
    assert ("bash", "pip list") not in approvals.MANAGED
