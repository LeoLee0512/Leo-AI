"""2.2.11: the model's own reasoning (DeepSeek reasoning_content) shows in the 「思考与步骤」 fold."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from leo_shell.workbench import WorkbenchGateway, route, shape_thoughts


def row(text, **extra):
    base = {"channel": "thought", "source_field": "reasoning_content", "turn_id": "t1", "group_id": "ag-1",
            "engine_turn": 0, "status": "completed", "text": text,
            "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "execution_id": "ex-secret", "provider": "deepseek"}
    base.update(extra)
    return base


def test_the_thoughts_route_reads_the_stored_projections():
    assert route({"operation": "thoughts", "frameId": "f1"}) == ("GET", "/frames/f1/leo-projections", None)
    with pytest.raises(ValueError):
        route({"operation": "thoughts", "frameId": "../x"})


def test_only_provider_reasoning_with_a_matching_digest_reaches_the_page():
    shaped = shape_thoughts({"version": 1, "has_more": False, "projections": [
        row("先比较两种方法"),
        row("我先检查相关文件", channel="progress", source_field=None),
        row("wrong source", source_field="content"),
        {**row("tampered"), "text": "tampered!"},
        row("   "),
        row("x" * 40000, engine_turn=1, status="running"),
        "junk",
    ]})
    thoughts = shaped["thoughts"]
    assert [t["text"][:7] for t in thoughts] == ["先比较两种方法", "x" * 7]
    assert thoughts[0] == {"turnId": "t1", "groupId": "ag-1", "engineTurn": 0, "status": "completed",
                           "text": "先比较两种方法", "truncated": False}
    assert len(thoughts[1]["text"]) == 32 * 1024 and thoughts[1]["truncated"] is True
    assert thoughts[1]["status"] == "running" and shaped["hasMore"] is False
    assert "ex-secret" not in json.dumps(shaped) and "deepseek" not in json.dumps(shaped)
    with pytest.raises(ValueError):
        shape_thoughts({"projections": "nope"})
    with pytest.raises(ValueError):
        shape_thoughts([])


def test_the_newest_thoughts_are_kept_and_the_cut_is_reported():
    shaped = shape_thoughts({"has_more": False, "projections": [row(f"思考 {i}", engine_turn=i) for i in range(230)]})
    assert len(shaped["thoughts"]) == 200 and shaped["thoughts"][0]["text"] == "思考 30"
    assert shaped["hasMore"] is True
    assert shape_thoughts({"has_more": True, "projections": []}) == {"thoughts": [], "hasMore": True}


def test_the_gateway_reads_a_large_answer_before_trimming_it():
    seen = {}

    class Gateway(WorkbenchGateway):
        def _exchange(self, method, path, body, limit):
            seen["limit"] = limit
            return json.dumps({"projections": [row("a")]}).encode(), "application/json"

    g = Gateway(lambda: "http://127.0.0.1:1/?token=t")
    assert g.request({"operation": "thoughts", "frameId": "f1"})["data"]["thoughts"][0]["text"] == "a"
    assert seen["limit"] == 16 * 1024 * 1024


HARNESS = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
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
const messages=[{seq:1,message_id:'u1',role:'user',content:'第一问'},
  {seq:2,message_id:'a2',role:'assistant',content:'第一答。'},
  {seq:3,message_id:'u3',role:'user',content:'第二问'},
  {seq:4,message_id:'a4',role:'assistant',content:'第二答。'}];
const groups=[{kind:'user',turnId:'t1',status:'completed',title:'第一问'},
  {kind:'user',turnId:'t2',status:'completed',title:'第二问'},
  {kind:'native_tools',turnId:'t2',status:'completed',title:'',names:['list_dir'],permission:null}];
const data={projects:{projects:[{id:'p-chat',name:'P'}]},frames:{frames:[frame]},messages:{messages,has_earlier:false},
  execution:{owner:null},feedback:{feedback:{}},timeline:{groups},approval_mode:{mode:'smart'},
  approvals:{requests:[],autoApproved:[]},schedules:{items:[],history:[]},thoughts:input.thoughts};
const api={get_state:async()=>({profiles:[]}),list_entity_states:async()=>({entities:[]}),
  list_session_models:async()=>({binding:null,models:[]}),workbench_request:async p=>{
    if(p.operation==='thoughts'&&input.failThoughts)throw new Error('WORKBENCH_UNAVAILABLE');return {data:data[p.operation]};}};
const ctx=vm.createContext({window:{pywebview:{api},navigator:{clipboard:{writeText:async()=>{}}},addEventListener(){}},
  document:{getElementById:el,createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},querySelector(s){return s===".desktop-menu"?new Element():null}},
  setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,clearInterval(){}});
(async()=>{
  vm.runInContext(input.source,ctx);await flush();
  await el('history').children.find(c=>String(c.className).includes('history-row')).children[0].onclick();await flush();
  const rows=el('messages').children;
  const folds=rows.filter(n=>String(n.className).startsWith('process'));
  const answers=rows.filter(n=>String(n.className).startsWith('message assistant'));
  console.log(JSON.stringify({folds:folds.map(text),answers:answers.map(text),
    order:rows.map(n=>String(n.className).startsWith('process')?'fold':String(n.className).split(' ')[1]||'')}));
})().catch(e=>{console.error(e);process.exitCode=1});
'''


def render(thoughts, fail=False):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required for browser runtime regression")
    source = (Path(__file__).resolve().parents[2] / "stage/workbench.js").read_text(encoding="utf-8")
    payload = {"source": source, "thoughts": {"thoughts": thoughts, "hasMore": False}, "failThoughts": fail}
    result = subprocess.run([node, "-e", HARNESS], input=json.dumps(payload), encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_each_turn_folds_its_own_thoughts_above_its_answer():
    out = render([
        {"turnId": "t2", "groupId": "g2", "engineTurn": 1, "status": "completed", "text": "再看目录", "truncated": False},
        {"turnId": "t1", "groupId": "g1", "engineTurn": 0, "status": "completed", "text": "只需直接回答", "truncated": False},
        {"turnId": "t2", "groupId": "g3", "engineTurn": 0, "status": "running", "text": "先想想<b>", "truncated": True},
        {"turnId": "t9", "groupId": "g9", "engineTurn": 0, "status": "completed", "text": "别的回合", "truncated": False},
    ])
    # A turn with no steps and no remarks still folds when the model thought about it.
    assert out["order"] == ["user", "fold", "assistant", "user", "fold", "assistant"]
    first, second = out["folds"]
    assert "只需直接回答" in first and "再看目录" not in first and "思考与步骤 · 1 项" in first
    assert "模型思考 · 原文，未经核实" in second and "思考与步骤 · 3 项" in second
    assert second.index("先想想<b>") < second.index("再看目录"), "calls are ordered as the model made them"
    assert "第 1 次调用 · 未完成 · 已截断" in second and "调用工具：list_dir" in second
    assert all("别的回合" not in fold for fold in out["folds"])
    assert all("思考" not in answer for answer in out["answers"])


def test_without_stored_thoughts_the_fold_is_unchanged():
    for out in (render([]), render([], fail=True)):
        assert out["order"] == ["user", "assistant", "user", "fold", "assistant"]
        assert "模型思考" not in out["folds"][0] and "思考与步骤 · 1 项" in out["folds"][0]
