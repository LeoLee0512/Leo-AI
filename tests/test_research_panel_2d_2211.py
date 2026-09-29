"""2.2.11: the research panel shows a 2D draft in 2D terms and edits it in its own shape."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from leo_shell.research_draft import TEMPLATE_2D, TEMPLATE_METHOD_2D

HARNESS = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(tag) {this.tag=tag;this.children=[];this.textContent='';this.dataset={};this.style={};this.value='';}
  append(n) {this.children.push(n);}
  replaceChildren() {this.children=[];}
  setAttribute() {} removeAttribute() {} addEventListener() {} focus() {}
  querySelectorAll(selector) {
    return this.children.flatMap(n=>[...(selector.startsWith('.') ? n.className===selector.slice(1) : n.tag===selector) ? [n] : [],...n.querySelectorAll(selector)]);
  }
  querySelector(s) {return this.querySelectorAll(s)[0];}
}
const text=n=>(n.textContent||'')+(n.children||[]).map(text).join('|');
const body=new Element('body'), calls=[];
let task=input.task;
const ctx=vm.createContext({window:{
  LeoWorkbench:{session:()=>({frameId:'f-test',projectId:'p-test'}),request:async()=>({project_id:'p-test'})},
  pywebview:{api:{research_request:async payload=>{
    calls.push(payload);
    if(payload.operation==='create'||payload.operation==='draft'||payload.operation==='get'||payload.operation==='update')
      return {ok:true,task,quota:input.quota,prepareLimitMinutes:15,canPrepare:task.state==='MODEL_CONFIRMED',
              verification:{verified:false,allowedClaims:[],reason:task.state}};
    return {ok:true,task};
  }}}},
  setInterval:()=>1,clearInterval:()=>{},
  document:{body,readyState:'complete',getElementById:()=>null,createElement:tag=>new Element(tag)}});
const buttons=()=>body.querySelectorAll('button');
function button(label) {const b=buttons().find(n=>n.textContent===label);assert.ok(b,label);return b;}
async function click(label) {button(label).onclick();for(let i=0;i<5;i++)await new Promise(r=>setImmediate(r));}
function input_(label) {const l=body.querySelectorAll('label').find(n=>n.textContent===label);assert.ok(l,label);return l.children[0];}
(async()=>{
  assert.equal(vm.runInContext(input.source,ctx),true);
  await click('科研任务');
  await click('创建任务并生成草案');
  const page=text(body);
  for(const piece of ['二维 Poisson · 已验证模板','−(u_xx + u_yy) = 2π² sin(πx) sin(πy)','0 < x < 1，0 < y < 1',
                      '左边（x = 0） u = 0；右边（x = 1） u = 0；下边（y = 0） u = 0；上边（y = 1） u = 0','4 层 × 64 神经元'])
    assert.ok(page.includes(piece),piece);
  await click('修改模型草案');
  assert.equal(input_('y 上限').value,'1');
  assert.equal(input_('上边（y 上限处）Dirichlet 值').value,'0');
  await click('改为一维问题');
  assert.equal(input_('区域左端').value,'0');
  assert.ok(!body.querySelectorAll('label').some(n=>n.textContent==='y 上限'),'the 1D editor has no y');
  await click('改为二维问题');
  input_('x 上限').value='2';
  await click('保存修改并撤销原模型确认');
  const update=calls.find(c=>c.operation==='update');
  assert.equal(JSON.stringify(update.draft.domain),'[[0,2],[0,1]]');
  assert.equal(JSON.stringify(update.draft.boundary),'{"left":0,"right":0,"bottom":0,"top":0}');
  // Preparing: the 2D quota is named and counted apart, and the longer preparation is announced.
  task={...task,state:'MODEL_CONFIRMED'};
  await click('运行');
  const run=text(body);
  assert.ok(run.includes('1 个二维盲测集（剩余 31 / 32；一维与二维分开计数）'),run);
  console.log('ok');
})().catch(e=>{console.error(e);process.exitCode=1;});
'''


def test_a_2d_draft_is_shown_and_edited_in_2d_terms():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to execute the browser JavaScript regression")
    source = (Path(__file__).resolve().parents[1] / "stage/research-panel.js").read_text(encoding="utf-8")
    draft = {"schemaVersion": "leo.problemDraft/1", "objective": "二维校准", "equation": TEMPLATE_2D["equation"],
             "domain": [[0, 1], [0, 1]], "boundary": {"left": 0, "right": 0, "bottom": 0, "top": 0},
             "assumptions": [], "missing": [], "conflicts": [], "templateId": "poisson2d-v1", "supported": True,
             "template": {**TEMPLATE_2D, "method": TEMPLATE_METHOD_2D}, "unsupportedReasons": [],
             "supportMessage": "需人工核对问题、方法与验收规则后才能准备运行"}
    task = {"taskId": "research-" + "5" * 32, "version": 2, "state": "DRAFT", "prompt": "二维校准", "draft": draft}
    payload = {"source": source, "task": task, "quota": {"capacity": 32, "used": 1, "remaining": 31, "family": "poisson2d"}}
    result = subprocess.run([node, "-e", HARNESS], input=json.dumps(payload), encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
