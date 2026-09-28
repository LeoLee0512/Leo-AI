"""Execute the research panel the way the workbench inlines it."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest


def test_research_panel_installs_only_inside_leo_workbench():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to execute the browser JavaScript regression")
    source = (Path(__file__).resolve().parents[1] / "stage/research-panel.js").read_text(encoding="utf-8")
    harness = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
function context(workbench=true) {
  const callbacks=[];
  // The old upstream-page globals are present on purpose: they must no longer be enough.
  const ctx=vm.createContext({window:{__LEO_INJECT_CONFIG__:{version:1},LeoStudio:{version:1},
    LeoWorkbench:workbench ? {session:()=>({}),request:async()=>({})} : undefined},
    location:{hostname:'127.0.0.1',port:'8760'},
    document:{readyState:'loading',addEventListener:(name,fn)=>callbacks.push(name)}});
  return {ctx,callbacks};
}
const good=context();
assert.equal(vm.runInContext(source,good.ctx),true,'the workbench host installs the panel');
assert.equal(vm.runInContext(source,good.ctx),true,'running it again is harmless');
assert.deepEqual(good.callbacks,['DOMContentLoaded'],'a second run must not duplicate entry points');
assert.equal(vm.runInContext(source,context(false).ctx),false,'without the workbench there is no host, even at the old upstream origin');
'''
    result = subprocess.run([node, "-e", harness], input=json.dumps(source), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_research_draft_failure_keeps_task_and_provides_next_step():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to execute the browser JavaScript regression")
    source = (Path(__file__).resolve().parents[1] / "stage/research-panel.js").read_text(encoding="utf-8")
    harness = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(tag) {this.tag=tag;this.children=[];this.textContent='';this.dataset={};this.style={};}
  append(n) {this.children.push(n);}
  replaceChildren() {this.children=[];}
  setAttribute() {} removeAttribute() {} addEventListener() {} focus() {}
  querySelectorAll(selector) {
    return this.children.flatMap(n=>[...(selector.startsWith('.') ? n.className===selector.slice(1) : n.tag===selector) ? [n] : [],...n.querySelectorAll(selector)]);
  }
  querySelector(s) {return this.querySelectorAll(s)[0];}
}
const body=new Element('body'), calls=[];
const task={taskId:'research-test',version:1,state:'DRAFT',prompt:'Poisson test',draft:null};
const ctx=vm.createContext({window:{
  LeoWorkbench:{session:()=>({frameId:'f-test',projectId:'p-test'}),request:async()=>({project_id:'p-test'})},
  pywebview:{api:{research_request:async payload=>{
    calls.push(payload.operation);
    if(payload.operation==='draft')return {ok:false,message:'RESEARCH_MODEL_UNAVAILABLE'};
    return {ok:true,task,verification:{verified:false,allowedClaims:[],reason:'DRAFT'}};
  }}}},
  setInterval:()=>1,clearInterval:()=>{},
  document:{body,readyState:'complete',getElementById:()=>null,createElement:tag=>new Element(tag)}});
function button(text) {const b=body.querySelectorAll('button').find(n=>n.textContent===text);assert.ok(b,text);return b;}
async function click(text) {button(text).onclick();await new Promise(r=>setImmediate(r));}
(async()=>{
  assert.equal(vm.runInContext(source,ctx),true);
  await click('科研任务');
  await click('创建任务并生成草案');
  assert.deepEqual(calls,['create','draft','get']);
  assert.match(body.querySelector('.leo-research-status').textContent,/模型名称/);
  assert.ok(button('生成问题草案'),'failed draft remains retryable');
  await click('验证与结论');
  assert.ok(button('前往问题与模型'),'verification view must not strand a draft');
  await click('前往问题与模型');
  assert.ok(button('生成问题草案'));
  assert.ok(!calls.includes('approve_model') && !calls.includes('approve_run'));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    result = subprocess.run([node, "-e", harness], input=json.dumps(source), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
