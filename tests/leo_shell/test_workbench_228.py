"""2.2.8: the daemon URL is reused, a turn folds its steps, Smart answers read-only commands itself."""
import io
import json
import shutil
import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

import pytest

from leo_shell import bridge_client
from leo_shell.approvals import ApprovalCenter, is_read_only_command
from leo_shell.bridge_client import WslBridge
from leo_shell.workbench import WorkbenchGateway, route, shape_timeline


# -- the sign-in URL is reused ------------------------------------------------------------------

def bridge(tmp_path, calls):
    script = tmp_path / "leo_bridge.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    paths = SimpleNamespace(bridge_script=script, root=tmp_path)
    b = WslBridge(paths)

    def run(action, *args, **kwargs):
        calls.append(action)
        return {"client_url": "http://127.0.0.1:8760/?token=abc"} if action == "url" else {}
    b._run = run
    return b


def test_the_url_is_fetched_once_and_forgotten_on_failure_or_stop(tmp_path, monkeypatch):
    calls = []
    b = bridge(tmp_path, calls)
    for _ in range(5):
        assert b.client_url().endswith("token=abc")
    assert calls == ["url"]
    b.invalidate_client_url()
    b.client_url()
    assert calls == ["url", "url"]
    b.stop()
    b.client_url()
    assert calls == ["url", "url", "stop", "url"]
    now = time.monotonic()
    monkeypatch.setattr(bridge_client.time, "monotonic", lambda: now + WslBridge.CLIENT_URL_TTL + 1)
    b.client_url()
    assert calls[-1] == "url" and calls.count("url") == 4


class Opener:
    def __init__(self, outcomes):
        self.outcomes, self.seen = list(outcomes), []

    def open(self, request, timeout):
        self.seen.append(request.get_method())
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class Response(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def gateway(outcomes):
    source = SimpleNamespace(forgotten=0)

    class Source:
        def client_url(self):
            return "http://127.0.0.1:8760/?token=abc"

        def invalidate_client_url(self):
            source.forgotten += 1
    opener = Opener([Response(o) if isinstance(o, bytes) else o for o in outcomes])
    g = WorkbenchGateway(Source().client_url, opener=opener)
    return g, opener, source


def http_error(code):
    return HTTPError("http://127.0.0.1:8760/api/v1/x", code, "err", {}, io.BytesIO(b"{}"))


def test_a_refused_token_is_retried_once_with_a_fresh_url():
    g, opener, source = gateway([http_error(401), b'{"ok": true}'])
    assert g._exchange("POST", "/frames/f1/decision", {}, 1000)[0] == b'{"ok": true}'
    assert opener.seen == ["POST", "POST"] and source.forgotten == 1


def test_a_lost_connection_retries_reads_but_never_writes():
    g, opener, source = gateway([URLError("refused"), b'{"ok": true}'])
    assert g._exchange("GET", "/projects", None, 1000)[0] == b'{"ok": true}'
    assert opener.seen == ["GET", "GET"]
    g, opener, source = gateway([URLError("refused"), b'{"ok": true}'])
    with pytest.raises(ValueError, match="WORKBENCH_UNAVAILABLE"):
        g._exchange("POST", "/frames/f1/message", {}, 1000)
    assert opener.seen == ["POST"] and source.forgotten == 1, "a send that may have landed is never repeated"


# -- the steps behind a turn ------------------------------------------------------------------------

def test_the_timeline_route_and_shape_carry_no_arguments():
    assert route({"operation": "timeline", "frameId": "f1"}) == ("GET", "/frames/f1/action-timeline?limit=300", None)
    shaped = shape_timeline({"groups": [
        {"ordinal": 1, "turn_id": "t1", "kind": "user", "title": "问题", "status": "completed"},
        {"ordinal": 2, "turn_id": "t1", "kind": "code", "title": "x" * 500, "status": "completed",
         "permission": {"decision_id": "perm-1", "state": "allowed", "scope": "once"},
         "events": [{"name": "bash", "canonical_arguments": {"command": "secret"}}], "cost": {"usd": 1}},
        {"ordinal": 3, "kind": "weird", "status": "exploded"},
    ]})["groups"]
    assert shaped[1]["title"] == "x" * 160 and shaped[1]["names"] == ["bash"]
    assert shaped[1]["permission"] == {"decisionId": "perm-1", "state": "allowed"}
    assert shaped[2]["kind"] == "other" and shaped[2]["status"] == "other"
    assert "secret" not in json.dumps(shaped) and "cost" not in shaped[1]
    with pytest.raises(ValueError):
        shape_timeline({"groups": "nope"})


def test_a_turn_folds_its_remarks_and_steps_above_the_answer():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required for browser runtime regression")
    source = (Path(__file__).resolve().parents[2] / "stage/workbench.js").read_text(encoding="utf-8")
    harness = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  addEventListener(){}
  constructor(){this.children=[];this.value='';this.classList={add(){},remove(){}};this.lastChild={};}
  append(...items){this.children.push(...items)} replaceChildren(){this.children=[]}
  querySelector(){return this.child||(this.child=new Element())} focus(){} setAttribute(){} showModal(){} close(){}
}
const flush=async()=>{for(let i=0;i<20;i++)await new Promise(r=>setImmediate(r));};
const text=n=>(n.textContent||'')+(n.children||[]).map(text).join('');
const nodes=new Map();const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
const frame={id:'f-chat',project_id:'p-chat',name:'Pip'};
const messages=[{seq:1,message_id:'u1',role:'user',content:'请执行 pip list'},
  {seq:2,message_id:'a2',role:'assistant',content:'我来用命令行执行。'},
  {seq:3,message_id:'a3',role:'assistant',content:'抱歉，我换一种方式。'},
  {seq:4,message_id:'a4',role:'assistant',content:'前 5 行如下。'}];
const groups=[{kind:'user',status:'completed',title:'请执行 pip list'},
  {kind:'code',status:'failed',title:'运行 pip',permission:null},
  {kind:'native_tools',status:'completed',title:'',names:['bash'],permission:{decisionId:'perm-auto',state:'allowed'}}];
const data={projects:{projects:[{id:'p-chat',name:'P'}]},frames:{frames:[frame]},messages:{messages,has_earlier:false},
  execution:{owner:null},feedback:{feedback:{}},timeline:{groups},approval_mode:{mode:'smart'},
  approvals:{requests:[],autoApproved:[{decisionId:'perm-auto',command:'pip list',at:1}]},schedules:{items:[],history:[]}};
const api={get_state:async()=>({profiles:[]}),list_entity_states:async()=>({entities:[]}),
  list_session_models:async()=>({binding:null,models:[]}),workbench_request:async p=>({data:data[p.operation]})};
const ctx=vm.createContext({window:{pywebview:{api},navigator:{clipboard:{writeText:async()=>{}}},addEventListener(){}},
  document:{getElementById:el,createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},querySelector(s){return s===".desktop-menu"?new Element():null}},
  setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,clearInterval(){}});
(async()=>{
  vm.runInContext(source,ctx);await flush();
  await el('history').children.find(c=>String(c.className).includes('history-row')).children[0].onclick();await flush();
  const rows=el('messages').children;
  const answers=rows.filter(n=>n.className?.startsWith('message assistant'));
  assert.deepEqual(answers.map(text).map(t=>t.includes('前 5 行如下。')),[true]);
  const process=rows.find(n=>String(n.className).startsWith('process'));
  assert.ok(process,'the turn has a folded process');
  const body=text(process);
  for(const piece of ['我来用命令行执行。','抱歉，我换一种方式。','运行计算：运行 pip','调用工具：bash','Smart 自动放行（只读命令）','未成功'])
    assert.ok(body.includes(piece),piece);
  assert.ok(rows.indexOf(process)<rows.indexOf(answers[0]),'the process sits above the answer');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result = subprocess.run([node, "-e", harness], input=json.dumps(source), encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr


# -- Smart answers read-only commands -------------------------------------------------------------

class FakeGateway:
    def __init__(self, fail_decision=False):
        self.calls, self.fail_decision, self.next_id = [], fail_decision, 0
        self.done = threading.Event()

    def _exchange(self, method, path, body, limit):
        self.calls.append((method, path, body))
        if path.endswith("/decision"):
            self.done.set()
            if self.fail_decision:
                raise ValueError("WORKBENCH_REQUEST_FAILED")
        if path == "/permissions":
            self.next_id += 1
            return json.dumps({"ok": True, "rule_id": f"perm_{self.next_id:04d}"}).encode(), ""
        return b'{"ok": true}', ""


def event(command, **extra):
    return {"type": "await_permission", "frame_id": "f1", "decision_id": "perm-" + str(abs(hash(command)) % 10**8),
            "tool": "bash", "kind": "bash", "title": "Running", "input": {"command": command}, "target": command,
            "suggested_patterns": [command, "*"], "dangerous": False, **extra}


def center(tmp_path, gateway):
    return ApprovalCenter(tmp_path, gateway, lambda: "http://127.0.0.1:8760/?token=t", start_watcher=False)


@pytest.mark.parametrize("command", ["pip list", "pip list --format=columns", "python -m pip show numpy scipy",
                                     "python --version", "conda list", "ls -la data", "git log --oneline -n 5", "nvidia-smi"])
def test_known_read_only_forms(command):
    assert is_read_only_command(command)


@pytest.mark.parametrize("command", ["pip install numpy", "pip list | head", "pip list > out.txt", "pip list; rm -rf x",
                                     "cat .env", "ls $HOME", "ls ~", "echo hi", "git push", "python run.py",
                                     "pip show 'numpy'", "rm -rf /", "", None, "pip list " + "x" * 300])
def test_everything_else_still_asks(command):
    assert not is_read_only_command(command)


def test_smart_answers_a_read_only_command_and_records_it(tmp_path):
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    c.mode("f1")
    request = event("pip list")
    c._handle(request)
    assert gateway.done.wait(5)
    decision = [b for m, p, b in gateway.calls if p.endswith("/decision")][0]
    assert decision == {"decision_id": request["decision_id"], "allow": True, "scope": "once"}
    seen = c.pending("f1")
    assert seen["requests"] == [] and seen["autoApproved"][0]["command"] == "pip list"
    c._handle(request)  # re-sent after a reconnect: answered once, never twice
    time.sleep(0.2)
    assert len([1 for m, p, b in gateway.calls if p.endswith("/decision")]) == 1


@pytest.mark.parametrize("mode", ["off", "auto"])
def test_only_smart_answers_by_itself(tmp_path, mode):
    gateway = FakeGateway()
    c = center(tmp_path, gateway)
    c.set_mode("f1", mode)
    c._handle(event("pip list"))
    assert len(c.pending("f1")["requests"]) == 1


def test_a_dangerous_or_writing_command_still_asks_in_smart(tmp_path):
    c = center(tmp_path, FakeGateway())
    c.mode("f1")
    c._handle(event("pip list", dangerous=True))
    c._handle(event("pip install numpy"))
    assert len(c.pending("f1")["requests"]) == 2


def test_if_the_automatic_answer_fails_the_person_is_asked(tmp_path):
    gateway = FakeGateway(fail_decision=True)
    c = center(tmp_path, gateway)
    c.mode("f1")
    c._handle(event("pip list"))
    assert gateway.done.wait(5)
    for _ in range(50):
        if c.pending("f1")["requests"]:
            break
        time.sleep(0.05)
    seen = c.pending("f1")
    assert len(seen["requests"]) == 1 and seen["autoApproved"] == []
