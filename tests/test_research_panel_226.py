"""2.2.6 research panel: quota before preparing, stale plans, why a run ended, failure evidence."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

HARNESS = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const {source,view}=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(tag) {this.tag=tag;this.children=[];this.textContent='';this.dataset={};this.style={};}
  append(...nodes) {for(const n of nodes)this.children.push(typeof n==='string'?Object.assign(new Element('#text'),{textContent:n}):n);}
  replaceChildren() {this.children=[];}
  setAttribute() {} removeAttribute() {} addEventListener() {} focus() {}
  querySelectorAll(selector) {
    return this.children.flatMap(n=>[...(selector.startsWith('.') ? n.className===selector.slice(1) : n.tag===selector) ? [n] : [],...n.querySelectorAll(selector)]);
  }
  querySelector(s) {return this.querySelectorAll(s)[0];}
}
const text=n=>n.textContent+n.children.map(text).join(' ');
const body=new Element('body'), calls=[];
const ctx=vm.createContext({window:{
  LeoWorkbench:{session:()=>({frameId:'f-test',projectId:'p-test'}),request:async()=>({project_id:'p-test'})},
  pywebview:{api:{research_request:async payload=>{
    calls.push(payload.operation);
    if(payload.operation==='list')return {ok:true,tasks:[{taskId:view.task.taskId,state:view.task.state,prompt:'Poisson test',frameId:'f-other'}]};
    return {ok:true,...view};
  }}}},
  setInterval:()=>1,clearInterval:()=>{},
  document:{body,readyState:'complete',getElementById:()=>null,createElement:tag=>new Element(tag)}});
const buttons=()=>body.querySelectorAll('button');
function button(label) {const b=buttons().find(n=>n.textContent===label||n.textContent.startsWith(label));assert.ok(b,label);return b;}
async function click(label) {button(label).onclick();for(let i=0;i<5;i++)await new Promise(r=>setImmediate(r));}
(async()=>{
  assert.equal(vm.runInContext(source,ctx),true);
  await click('科研任务');
  await click('查看全部科研任务');
  assert.match(text(body),/其他对话/,'tasks of other conversations are listed and marked');
  await click('计算');   // "计算或验证未通过 · …" or any listed task: open it
  await click('运行');
  const run=text(body.querySelector('.leo-research-body')||body), runLabels=buttons().map(b=>b.textContent);
  await click('验证与结论');
  const verification=text(body.querySelector('.leo-research-body')||body);
  console.log(JSON.stringify({run,verification,labels:runLabels,calls}));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''


def render(view):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to execute the browser JavaScript regression")
    source = (Path(__file__).resolve().parents[1] / "stage/research-panel.js").read_text(encoding="utf-8")
    # The listed item's label starts with its state label; give every scenario one that starts with "计算".
    harness = HARNESS.replace("await click('计算');", "await click(" + json.dumps(view["listLabel"]) + ");")
    result = subprocess.run([node, "-e", harness], input=json.dumps({"source": source, "view": view}),
                            text=True, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def task(state, **extra):
    return {"taskId": "research-" + "a" * 32, "version": 3, "state": state, "prompt": "Poisson test",
            "draft": {"supported": True, "objective": "o", "equation": "e", "domain": [0, 1],
                      "boundary": {"left": 0, "right": 0}, "assumptions": [], "missing": [], "conflicts": []}, **extra}


def test_the_quota_is_stated_before_a_grid_is_reserved():
    out = render({"listLabel": "模型已确认", "task": task("MODEL_CONFIRMED"), "canPrepare": True,
                  "quota": {"capacity": 32, "used": 1, "remaining": 31},
                  "verification": {"verified": False, "allowedClaims": [], "reason": "MODEL_CONFIRMED"}})
    assert "剩余 31 / 32" in out["run"] and "准备运行确认包" in out["labels"]


def test_no_preparation_is_offered_once_the_quota_is_spent():
    out = render({"listLabel": "模型已确认", "task": task("MODEL_CONFIRMED"), "canPrepare": True,
                  "quota": {"capacity": 32, "used": 32, "remaining": 0},
                  "verification": {"verified": False, "allowedClaims": [], "reason": "MODEL_CONFIRMED"}})
    assert "额度已用完" in out["run"] and "准备运行确认包" not in out["labels"]


def test_a_stale_plan_offers_a_new_task_instead_of_an_admission():
    out = render({"listLabel": "等待正式运行确认", "canPrepare": False, "quota": {"capacity": 32, "used": 1, "remaining": 31},
                  "task": task("READY_FOR_RUN_APPROVAL", runBlocked={"reason": "RUN_PLAN_IDENTITY_CHANGED", "at": "t"}),
                  "verification": {"verified": False, "allowedClaims": [], "reason": "READY_FOR_RUN_APPROVAL"}})
    assert "审阅并确认正式运行" not in out["labels"] and "以此草案新建任务" in out["labels"]
    assert "不能再用于正式运行" in out["run"]


def test_a_stopped_run_says_where_it_ended_and_shows_what_it_recorded():
    out = render({"listLabel": "计算或验证未通过", "canPrepare": False, "quota": {"capacity": 32, "used": 1, "remaining": 31},
                  "task": task("STOPPED", completion={"state": "STOPPED", "phase": "main", "exitCode": 3, "at": "t"}),
                  "verification": {"verified": False, "allowedClaims": [], "reason": "STOPPED", "failure": {
                      "gate": 5, "observedSignatures": ["sLocalizedError"], "finalState": "FAILURE_RECORDED",
                      "trustVector": {"external": "FAIL", "train": "PASS"},
                      "completion": {"state": "STOPPED", "phase": "main", "exitCode": 3}}}})
    assert "结束于「主实验」" in out["run"] and "以此草案新建任务" in out["labels"]
    assert "尚不可下结论" in out["verification"] and "Gate 5" in out["verification"]
    assert "sLocalizedError" in out["verification"] and "外部精度 · 未通过" in out["verification"]


def test_a_preparing_task_explains_what_is_happening():
    out = render({"listLabel": "正在准备运行确认包", "task": task("PREPARING"), "canPrepare": False,
                  "quota": {"capacity": 32, "used": 1, "remaining": 31},
                  "verification": {"verified": False, "allowedClaims": [], "reason": "PREPARING"}})
    assert "不会启动训练" in out["run"] and "准备运行确认包" not in out["labels"]
