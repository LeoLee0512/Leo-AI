"""3.2.0: the research panel speaks plainly (runs the real stage/research-panel.js in Node).

One fake DOM, one scenario per page: running and preparing show their steps and elapsed time
(A7, C4, C5); a claim is green with a ladder of levels (B1, C1); a stopped run tells what happened
and what to do (C3); the two native confirmations are two-line key buttons; the quota is drawn as
squares (C7); a locked model says so (C6); tasks are rows (A8); formulas go through the workbench's
own TeX renderer when it is there (C8); and the whole window is dimmed while the panel is open (D1).
"""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from leo_shell import research_words
from leo_shell.research_draft import TEMPLATE, TEMPLATE_METHOD, validate_draft

SOURCE = Path(__file__).resolve().parents[1] / "stage/research-panel.js"

HARNESS = r'''
const vm=require('node:vm');
const {source,scenarios}=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(tag) {this.tag=tag;this.children=[];this.textContent='';this.dataset={};this.style={};this.value='';this.attrs={};this.className='';}
  append(n) {this.children.push(n);n.parent=this;}
  remove() {if(this.parent)this.parent.children=this.parent.children.filter(c=>c!==this);}
  replaceChildren() {this.children=[];}
  setAttribute(k,v) {this.attrs[k]=String(v);} removeAttribute(k) {delete this.attrs[k];} addEventListener() {} focus() {}
  get localName() {return this.tag;}
  matches(sel) {
    if(sel.startsWith('.'))return this.className.split(' ').includes(sel.slice(1));
    const m=sel.match(/^(\w+)\[data-(\w+)\]$/);if(m)return this.tag===m[1]&&m[2] in this.dataset;
    return this.tag===sel;
  }
  querySelectorAll(sel) {return this.children.flatMap(n=>[...(n.matches(sel)?[n]:[]),...n.querySelectorAll(sel)]);}
  querySelector(s) {return this.querySelectorAll(s)[0];}
}
const text=n=>[n.textContent||'',...(n.children||[]).map(text)].filter(Boolean).join('|');
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const out={};
  for(const sc of scenarios){
    const body=new Element('body'), texCalls=[];
    let view=sc.view;
    const ctx=vm.createContext({window:{
      LeoWorkbench:{session:()=>({frameId:'f-test',projectId:'p-test'}),request:async()=>({project_id:'p-test'}),
        ...(sc.math?{math:(tex)=>{texCalls.push(tex);const m=new Element('math');m.textContent='[MathML]';return m;}}:{})},
      pywebview:{api:{research_request:async payload=>{
        if(payload.operation==='list')return {ok:true,tasks:sc.list||[]};
        return {ok:true,...view};
      }}}},
      setInterval:()=>1,clearInterval:()=>{},Date,
      document:{body,readyState:'complete',getElementById:()=>null,createElement:tag=>new Element(tag)}});
    vm.runInContext(source,ctx);
    body.querySelectorAll('button').find(b=>b.textContent==='科研任务').onclick();
    if(sc.list){
      body.querySelectorAll('button').find(b=>b.textContent==='查看全部科研任务').onclick();
      for(let i=0;i<6;i++)await tick();
    } else {
      ctx.window.LeoResearch.close();
      // Open straight onto the scenario's task through the listed row, the way a person does.
      sc.list=[{taskId:view.task.taskId,state:view.task.state,prompt:view.task.prompt,updatedAt:'2026-09-29T07:00:00Z',frameId:'f-test',family:'poisson1d'}];
      ctx.window.LeoResearch.open();
      body.querySelectorAll('button').find(b=>b.textContent==='查看全部科研任务').onclick();
      for(let i=0;i<6;i++)await tick();
      body.querySelectorAll('.task-row').find(r=>r.dataset.taskId===view.task.taskId).onclick();
      for(let i=0;i<6;i++)await tick();
      if(sc.tab){body.querySelectorAll('button').find(b=>b.dataset.tab===sc.tab).onclick();for(let i=0;i<6;i++)await tick();}
    }
    const overlay=body.querySelector('.leo-research-overlay');
    const main=overlay.querySelector('.leo-research-body');
    out[sc.name]={
      text:text(main),
      state:overlay.querySelector('.status-state').textContent,
      note:overlay.querySelector('.status-note').textContent,
      title:overlay.querySelector('.leo-research-title').textContent,
      buttons:main.querySelectorAll('button').map(b=>({label:b.textContent||b.dataset.label||'',cls:b.className,aria:b.attrs['aria-label']||''})),
      squares:main.querySelectorAll('.quota-squares').flatMap(q=>q.children.map(i=>i.className)),
      rows:main.querySelectorAll('.task-row').map(r=>({label:r.dataset.label||'',text:text(r)})),
      backdrop:body.querySelectorAll('.leo-research-backdrop').length,
      texCalls,
    };
    ctx.window.LeoResearch.close();
    out[sc.name].backdropAfterClose=body.querySelectorAll('.leo-research-backdrop').length;
  }
  console.log(JSON.stringify(out));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''


def draft(**extra):
    raw = {"objective": "验证基准", "equation": TEMPLATE["equation"], "domain": [0, 1], "boundary": {"left": 0, "right": 0},
           "assumptions": [], "missing": [], "conflicts": []}
    raw.update(extra)
    return validate_draft(raw, "验证基准")


def task(state, **extra):
    return {"taskId": "research-" + "b" * 32, "version": 4, "state": state, "prompt": "一维 Poisson 基准",
            "draft": draft(), "updatedAt": "2026-09-29T07:00:00Z", **extra}


PLAN = {"family": "poisson1d", "phases": ["main", "tier1", "reproduction", "g6"], "budgetSeconds": 3600,
        "specHash": "5d2e8c41" + "0" * 56, "codeHash": "84ac5b8f" + "1" * 56, "claimMember": "GL1152-CGL4010",
        "claimSampleSetHash": "e3a91f07" + "2" * 56, "seedProtocol": {"runs": 10, "initBase": 1, "sampleBase": 2, "batchBase": 3},
        "reproductionSeedOffset": 10000, "parallelWorkers": 1,
        "expectedTolerance": {"devRelL2MedianAbsDiff": 1e-4, "seedProtocolVerdictMustAgree": True}}
WORDS = research_words.panel_words("poisson1d")
APPROVAL = {"at": "2026-09-29T06:00:00Z", "contentHash": "sha256:3f9e1c0a7d24b5"}


def base(state, **extra):
    return {"task": task(state, modelApproval=APPROVAL), "quota": {"capacity": 32, "used": 4, "remaining": 28, "family": "poisson1d"},
            "canPrepare": state == "MODEL_CONFIRMED", "prepareLimitMinutes": 5, "words": WORDS,
            "verification": {"verified": False, "allowedClaims": [], "reason": state}, **extra}


def render(scenarios):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to execute the browser JavaScript regression")
    result = subprocess.run([node, "-e", HARNESS], input=json.dumps({"source": SOURCE.read_text(encoding="utf-8"), "scenarios": scenarios}),
                            text=True, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def pages():
    running = base("RUNNING", plan=PLAN, estimateMinutes=8,
                   progress={"phase": "tier1", "at": "2026-09-29T07:05:00Z",
                             "phases": [{"phase": "main", "startedAt": "2026-09-29T07:00:00Z"},
                                        {"phase": "tier1", "startedAt": "2026-09-29T07:05:00Z"}]})
    running["task"]["runApproval"] = {"at": "2026-09-29T07:00:00Z"}
    preparing = base("PREPARING", preparationProgress={"step": "environments", "at": "t"})
    preparing["task"]["preparationStartedAt"] = "2026-09-29T07:00:00Z"
    verification = {"verified": True, "allowedClaims": ["C0", "C1", "C2"],
                    "blockedClaims": [{"level": "C3", "reason": "no independently qualified C2 runs supplied",
                                       "plain": research_words.blocked_reason("no independently qualified C2 runs supplied")}],
                    "dimensions": {k: {"status": "PASS", "checks": []} for k in ("math", "impl", "train", "physics", "external", "repro")}}
    story = {"happened": "打开封存的盲测集核对时，10 个种子里有 1 个没有满足「局部误差」。", "means": "按规则不能声明精度。",
             "next": "可以以此草案新建任务再试一次。", "criteria": [],
             "facts": [{"plain": "没通过的是第 5 关「与精确解一致」", "raw": "Gate 5"},
                       {"plain": "观察到的问题：局部误差超标", "raw": "sLocalizedError"}]}
    stopped = base("STOPPED", verification={"verified": False, "allowedClaims": [], "reason": "STOPPED", "story": story,
                                            "failure": {"gate": 5, "observedSignatures": ["sLocalizedError"],
                                                        "trustVector": {"math": "PASS", "external": "FAIL", "repro": "NOT_RUN"}}})
    stopped["task"]["completion"] = {"state": "STOPPED", "phase": "main", "exitCode": 3}
    heat = base("DRAFT")
    heat["task"]["draft"] = draft(equation="-k*u''(x)=x")
    return render([
        {"name": "running", "view": running, "tab": "run"},
        {"name": "preparing", "view": preparing, "tab": "run"},
        {"name": "claim", "view": {**base("COMPLETED"), "verification": verification}, "tab": "verification"},
        {"name": "stopped", "view": stopped, "tab": "verification"},
        {"name": "ready", "view": base("READY_FOR_RUN_APPROVAL", plan=PLAN, estimateMinutes=8), "tab": "run"},
        {"name": "locked", "view": base("READY_FOR_RUN_APPROVAL", plan=PLAN), "tab": "model"},
        {"name": "confirmed", "view": base("MODEL_CONFIRMED"), "tab": "run"},
        {"name": "draft", "view": {**base("DRAFT"), "task": task("DRAFT")}, "tab": "model", "math": True},
        {"name": "heat", "view": heat, "tab": "model", "math": True},
        {"name": "list", "view": {}, "list": [
            {"taskId": "research-" + "c" * 32, "state": "RUNNING", "prompt": "二维 Poisson", "updatedAt": "2026-09-29T07:00:00Z", "frameId": "f-test", "family": "poisson2d"},
            {"taskId": "research-" + "d" * 32, "state": "DRAFT", "prompt": "热传导", "updatedAt": "2026-09-28T07:00:00Z", "frameId": "f-other", "family": None}]},
    ])


def test_the_old_catch_all_status_is_gone():
    assert "操作已完成" not in SOURCE.read_text(encoding="utf-8")


def test_a_running_task_shows_its_phases_and_elapsed_time(pages):
    page = pages["running"]
    for piece in ("正在计算 · 第 2 阶段，共 4 阶段", "主实验", "扰动检验", "独立复现", "复现判定", "进行中", "预计约 8 分", "上限 60 分", "Tier-1"):
        assert piece in page["text"], piece
    assert page["state"].startswith("正在计算 · 扰动检验 · 已用") and page["note"] == ""
    stop = next(b for b in page["buttons"] if b["label"] == "停止计算并保留证据")
    assert stop["cls"] == "research-danger-outline"
    assert "2026-09-29T" not in page["text"], "no raw UTC timestamps"


def test_a_preparing_task_shows_which_step_it_is_on(pages):
    page = pages["preparing"]
    assert "核对代码身份" in page["text"] and "检查两个科学环境" in page["text"] and "不会启动训练" in page["text"]
    assert page["state"].startswith("正在准备 · 已用") and "最长 5 分钟" in page["text"]


def test_a_claim_is_green_with_its_ladder_and_the_blocked_level_in_words(pages):
    page = pages["claim"]
    assert "可以声明：在这道题上，精度达到了事先约定的要求" in page["text"]
    for name in ("代码能正确运行", "训练收敛", "精度声明", "可推广结论", "本次到达", "还需要至少 5 次独立完成的合格运行"):
        assert name in page["text"], name
    assert "数学设定" in page["text"] and "G5b · external" in page["text"]
    assert any(b["label"] == "确认已审阅结论" and b["cls"] == "research-primary" for b in page["buttons"])
    assert "no independently qualified" not in page["text"].replace("C3 · no independently qualified C2 runs supplied", "")
    assert page["title"] == "科研任务 · 已完成，结论可引用"


def test_a_stopped_run_tells_what_happened_and_what_to_do(pages):
    page = pages["stopped"]
    for piece in ("不下结论：这次运行没有通过全部检查", "发生了什么", "这意味着什么", "你可以做什么", "局部误差", "原始记录（给想深入的人）",
                  "Gate 5", "sLocalizedError", "与精确解一致"):
        assert piece in page["text"], piece
    assert any(b["label"] == "以此草案新建任务" for b in page["buttons"]) and page["title"] == "科研任务 · 未通过，不下结论"


def test_the_run_confirmation_is_a_two_line_key_button_and_hashes_are_short(pages):
    page = pages["ready"]
    key = next(b for b in page["buttons"] if b["label"] == "审阅并确认正式运行")
    assert key["cls"] == "research-key" and "会弹出原生确认框" in key["aria"] and "只有你本人能点" in key["aria"]
    assert "这次会做什么" in page["text"] and "GL1152-CGL4010" in page["text"]
    assert "0" * 56 not in page["text"].split("完整运行确认包")[0], "no full hash before the raw package"


def test_a_locked_model_says_so_and_offers_a_new_task(pages):
    page = pages["locked"]
    assert "模型已确认并锁定" in page["text"] and "内容指纹 3f9e1c0a" in page["text"]
    assert not any(b["label"] == "修改模型草案" for b in page["buttons"])


def test_the_quota_is_drawn_as_squares_before_a_grid_is_spent(pages):
    page = pages["confirmed"]
    assert page["squares"].count("is-used") == 4 and page["squares"].count("is-next") == 1 and len(page["squares"]) == 32
    assert any(b["label"] == "准备运行确认包（用掉 1 个）" and b["cls"] == "research-primary" for b in page["buttons"])


def test_formulas_go_through_the_workbench_renderer(pages):
    draft_page, heat = pages["draft"], pages["heat"]
    assert draft_page["texCalls"] and draft_page["texCalls"][0] == "-u''(x) = \\pi^2 \\sin(\\pi x)"
    assert "[MathML]" in draft_page["text"]
    key = next(b for b in draft_page["buttons"] if b["label"] == "审阅并确认模型")
    assert key["cls"] == "research-key" and "不会开始计算" in key["aria"]
    assert heat["texCalls"][0] == "-k\\,u''(x)=x", heat["texCalls"]


def test_tasks_are_rows_with_state_type_and_conversation(pages):
    head, *rows = pages["list"]["rows"]
    assert head["label"] == "" and "状态|问题|类型|更新|对话" in head["text"]
    assert [r["label"] for r in rows] == ["正在计算", "问题草案"]
    assert "二维" in rows[0]["text"] and "本对话" in rows[0]["text"]
    assert "未匹配" in rows[1]["text"] and "其他对话" in rows[1]["text"]


def test_the_whole_window_is_dimmed_while_the_panel_is_open(pages):
    for page in pages.values():
        assert page["backdrop"] == 1 and page["backdropAfterClose"] == 0
