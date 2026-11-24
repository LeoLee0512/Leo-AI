"""3.2.2: the research panel shows and edits an annulus draft, and the three 3.2.0 live-check fixes.

Runs the real stage/research-panel.js in Node with a small fake DOM (as the 2.2.11 2D panel test).
"""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from leo_shell.research_draft import TEMPLATE_ANNULUS, validate_draft

SOURCE = Path(__file__).resolve().parents[1] / "stage/research-panel.js"

HARNESS = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(tag) {this.tag=tag;this.children=[];this.textContent='';this.dataset={};this.style={};this.value='';this.attrs={};this.className='';}
  append(n) {this.children.push(n);n.parent=this;}
  remove() {if(this.parent)this.parent.children=this.parent.children.filter(c=>c!==this);}
  replaceChildren() {this.children=[];}
  setAttribute(k,v) {this.attrs[k]=String(v);} removeAttribute(k) {delete this.attrs[k];} addEventListener() {} focus() {}
  get localName() {return this.tag;}
  matches(sel) {
    // Enough of CSS for the panel: ".class", "tag", and the last part of "nav button[data-tab]".
    const last=sel.trim().split(/\s+/).pop(), attr=last.match(/^(\w+)\[data-(\w+)\]$/);
    if(attr)return this.tag===attr[1] && attr[2] in this.dataset;
    return last.startsWith('.') ? this.className.split(' ').includes(last.slice(1)) : this.tag===last;
  }
  querySelectorAll(sel) {return this.children.flatMap(n=>[...(n.matches(sel)?[n]:[]),...n.querySelectorAll(sel)]);}
  querySelector(s) {return this.querySelectorAll(s)[0];}
}
const text=n=>[n.textContent||'',...(n.children||[]).map(text)].filter(Boolean).join('|');
const tick=async()=>{for(let i=0;i<6;i++)await new Promise(r=>setImmediate(r));};
const body=new Element('body'), calls=[], tex=[];
let task=input.task;
const ctx=vm.createContext({window:{
  LeoWorkbench:{session:()=>({frameId:'f-test',projectId:'p-test'}),request:async()=>({project_id:'p-test'}),
    math:t=>{tex.push(t);const m=new Element('math');m.textContent='[MathML]';return m;}},
  pywebview:{api:{research_request:async payload=>{
    calls.push(payload);
    if(payload.operation==='list')return {ok:true,tasks:input.list};
    return {ok:true,task,quota:{capacity:8,used:0,remaining:8,family:'annulus'},canPrepare:task.state==='MODEL_CONFIRMED',
            prepareLimitMinutes:30,plan:input.plan,progress:input.progress,
            verification:{verified:false,allowedClaims:[],reason:task.state}};
  }}}},
  setInterval:()=>1,clearInterval:()=>{},Date,
  document:{body,readyState:'complete',getElementById:()=>null,createElement:tag=>new Element(tag)}});
const buttons=()=>body.querySelectorAll('button');
const labelOf=n=>n.textContent||n.dataset.label||'';
function button(label) {const b=buttons().find(n=>labelOf(n)===label);assert.ok(b,label);return b;}
async function click(label) {button(label).onclick();await tick();}
function input_(label) {const l=body.querySelectorAll('label').find(n=>n.textContent===label);assert.ok(l,label);return l.children[0];}
const main=()=>body.querySelector('.leo-research-body');
(async()=>{
  vm.runInContext(input.source,ctx);
  await click('科研任务');
  const out={};
  // No task: clicking a later step must not leave it highlighted over the create page.
  const navButton=key=>body.querySelectorAll('button').find(b=>b.dataset.tab===key);
  await click('验证与结论');
  out.currentAfterClick=Object.fromEntries(['model','verification'].map(k=>[k,navButton(k).attrs['aria-current']||'']));
  out.createPage=text(main());
  // The task list names a task without a draft as such, and the annulus family.
  await click('查看全部科研任务');
  out.rows=body.querySelectorAll('.task-row').map(text);
  // Open the annulus draft.
  body.querySelectorAll('.task-row').find(r=>r.dataset.taskId===task.taskId).onclick();await tick();
  out.model=text(main());
  out.tex=tex.slice();
  await click('修改模型草案');
  out.editorLabels=body.querySelectorAll('label').map(l=>l.textContent);
  assert.equal(input_('内半径').value,'0.35');
  assert.equal(input_('外半径').value,'1');
  input_('外圈').value='0';
  await click('保存修改');
  out.update=calls.find(c=>c.operation==='update').draft;
  // A finished run's page says what was done, with the phase start times.
  task={...task,state:'COMPLETED',runApproval:{at:'2026-09-29T07:00:00Z'},completion:{state:'COMPLETED',at:'2026-09-29T14:30:00Z'}};
  await click('运行');
  out.run=text(main());
  console.log(JSON.stringify(out));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''


def test_an_annulus_draft_is_shown_and_edited_and_the_live_check_fixes_hold():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to execute the browser JavaScript regression")
    raw = {"objective": "环形域校准", "equation": TEMPLATE_ANNULUS["equation"], "domain": {"annulus": [0.35, 1]},
           "boundary": {"inner": 0, "outer": 0}, "assumptions": [], "missing": [], "conflicts": []}
    draft = validate_draft(raw, "环形域校准")
    task = {"taskId": "research-" + "e" * 32, "version": 2, "state": "DRAFT", "prompt": "环形域校准", "draft": draft,
            "updatedAt": "2026-09-29T07:00:00Z"}
    listed = [{"taskId": task["taskId"], "state": "DRAFT", "prompt": "环形域校准", "updatedAt": "2026-09-29T07:00:00Z",
               "frameId": "f-test", "family": "annulus", "hasDraft": True},
              {"taskId": "research-" + "f" * 32, "state": "DRAFT", "prompt": "草案没生成", "updatedAt": "2026-09-28T07:00:00Z",
               "frameId": "f-test", "family": None, "hasDraft": False}]
    plan = {"family": "annulus", "phases": ["main", "tier1", "reproduction", "g6"], "budgetSeconds": 57600,
            "claimMember": "ANN-Q44-A137", "specHash": "a" * 64, "codeHash": "b" * 64, "seedProtocol": {"runs": 10}}
    progress = {"phase": "g6", "at": "2026-09-29T14:00:00Z",
                "phases": [{"phase": "main", "startedAt": "2026-09-29T07:00:00Z"},
                           {"phase": "tier1", "startedAt": "2026-09-29T09:10:00Z"}]}
    payload = {"source": SOURCE.read_text(encoding="utf-8"), "task": task, "list": listed, "plan": plan, "progress": progress}
    result = subprocess.run([node, "-e", HARNESS], input=json.dumps(payload), encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip().splitlines()[-1])
    assert out["currentAfterClick"] == {"model": "step", "verification": ""}
    assert "三个已验证模板" in out["createPage"] and "环形域 Poisson" in out["createPage"]
    header, *rows = out["rows"]
    assert "状态|问题|类型|更新|对话" in header and "环形" in rows[0] and "尚无草案" in rows[1]
    for piece in ("环形域 Poisson · 已验证模板", "0.35 < r < 1", "内圈 r = 0.35|u = 0", "外圈 r = 1|u = 0", "[MathML]",
                  "制造解 u*"):
        assert piece in out["model"], piece
    assert out["tex"] and out["tex"][0].startswith("-(u_{xx} + u_{yy}) = f,") and "\\cos(2\\pi y)" in out["tex"][0]
    assert {"内半径", "外半径", "内圈", "外圈"} <= set(out["editorLabels"]) and "y 上限" not in out["editorLabels"]
    assert out["update"]["domain"] == {"annulus": [0.35, 1]} and out["update"]["boundary"] == {"inner": 0, "outer": 0}
    assert "这次做了什么" in out["run"] and "这次会做什么" not in out["run"] and "用掉 1 个环形盲测集" in out["run"]
    assert "开始）" in out["run"]
