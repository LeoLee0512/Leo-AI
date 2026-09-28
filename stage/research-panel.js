/* Research UI: rendering only. Native service owns confirmations and scientific state. */
(() => {
  "use strict";
  // Leo's own workbench is the only host; there is no upstream page to attach to any more.
  if (!window.LeoWorkbench) return false;
  if (window.__leoResearchPanel) return true;
  window.__leoResearchPanel = true;
  let overlay, task, plan, tab = "model", polling, busy = false, frameContext;
  const labels = {DRAFT:"问题草案", MODEL_CONFIRMED:"模型已确认", READY_FOR_RUN_APPROVAL:"等待正式运行确认",
    RUNNING:"正在计算", CANCELLING:"正在停止", CANCELLED:"已取消", TIMED_OUT:"预算耗尽",
    STOPPED:"计算或验证未通过", INTERRUPTED:"运行中断", COMPLETED:"计算流程结束"};
  const errors = {
    RESEARCH_SELECT_SESSION_MODEL:"请先在聊天输入框中选择一个已配置的会话模型，再生成草案。",
    MODEL_CONNECT_BEFORE_SELECTION:"请先连接模型，再回到科研任务生成草案。",
    MODEL_KEY_UNAVAILABLE:"当前会话模型没有可读取的密钥，请检查该模型配置。",
    RESEARCH_MODEL_UNAVAILABLE:"服务端不支持当前模型名称，请检查 API 模型 ID；这不表示密钥未保存。",
    RESEARCH_PROVIDER_AUTH_FAILED:"模型服务拒绝了凭据，请检查当前会话绑定的密钥。",
    RESEARCH_PROVIDER_RATE_LIMITED:"模型服务限流或额度不足，请检查账户状态后重试。",
    RESEARCH_PROVIDER_UNAVAILABLE:"模型服务暂时不可用，草案尚未生成，请稍后重试。",
    RESEARCH_PROVIDER_REQUEST_REJECTED:"模型服务拒绝了草拟请求，请检查模型及接口兼容性。",
    RESEARCH_CONNECTION_FAILED:"无法连接模型服务，请检查网络和服务地址。",
    RESEARCH_DRAFT_TIMEOUT:"生成草案超时；任务已保留，可以重试。",
    RESEARCH_DRAFT_FORMAT_INVALID:"模型返回内容不符合草案格式；未执行任何计算，可以重试。",
    RESEARCH_DRAFT_FAILED:"草案生成失败；任务已保留，未执行任何计算。",
    PREPARATION_TIMED_OUT:"准备运行确认包超时（5 分钟）；没有启动训练。可以以此草案新建任务重试。",
    PREPARATION_FAILED_SEE_EVIDENCE:"准备失败；没有启动训练。可以查看证据中的准备日志，或以此草案新建任务重试。",
    CREATE_NEW_TASK_FOR_REVISION:"这个任务已生成运行数据，不能再修改；请以此草案新建任务。",
    RESEARCH_TASK_ALREADY_RUNNING:"已有另一个科研任务正在计算；请等它结束或停止后再确认。",
    FORK_REQUIRES_STOPPED_WORKER:"计算仍在进行，结束或停止后才能以此草案新建任务。",
    FORK_REQUIRES_DRAFT:"这个任务还没有草案，无法复制。"
  };
  const methodLabels = [["network","网络与边界"],["training","训练"],["sampling","配点采样"],["losses","损失权重"],["seeds","种子"],
    ["precision","数值精度"],["reference","参考解"],["acceptance","验收规则"],["validation","验证链"],["claimRule","结论规则"]];
  const RESTARTABLE = new Set(["STOPPED","INTERRUPTED","CANCELLED","TIMED_OUT"]);
  function chip(parent, text, kind) { const c=el("span",text,parent); c.className="trust-chip trust-"+kind; return c; }
  function forkButton(parent) {
    return button(parent,"以此草案新建任务",async()=>{await api("fork");tab="model";plan=null;await refresh();});
  }
  const el = (tag, text, parent) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(parent)parent.append(n); return n; };
  function session() { return window.LeoWorkbench.session(); }
  async function association() {
    const ids=session();
    if(!ids.frameId) throw new Error("请先打开一个科研会话。");
    const frame=await window.LeoWorkbench.request("frame",{frameId:ids.frameId});
    if(!frame.project_id) throw new Error("当前会话缺少项目身份。");
    return {...ids,projectId:frame.project_id};
  }
  async function api(operation, extra={}) {
    if(!window.pywebview?.api?.research_request) throw new Error("科研任务需要 Leo AI 桌面运行环境。");
    const result=await window.pywebview.api.research_request({operation,taskId:task?.taskId,expectedVersion:task?.version,...extra});
    if(result.task)task=result.task;
    if(!result.ok) { const code=result.code || result.message || "操作失败"; throw new Error(errors[code] || code); }
    if(result.plan)plan=result.plan;
    return result;
  }
  function status(text) { if(overlay)overlay.querySelector(".leo-research-status").textContent=text; }
  async function action(fn) {
    if(busy)return; busy=true; overlay?.setAttribute("aria-busy","true");
    status("正在处理，请稍候。模型草拟可能需要一分钟；计算不会在确认前启动。");
    overlay?.querySelectorAll("button").forEach(b=>b.disabled=true);
    try { await fn(); status("操作已完成。科学状态以验证结果为准。"); }
    catch(e){ status(e.message); }
    finally {busy=false; overlay?.removeAttribute("aria-busy");overlay?.querySelectorAll("button").forEach(b=>b.disabled=false);}
  }
  function button(parent, text, fn) { const b=el("button",text,parent); b.type="button"; b.onclick=()=>action(fn);return b; }
  function paragraph(parent, text) { return el("p",text,parent); }
  function field(parent,label,value, multiline=false) {
    const l=el("label",label,parent), input=el(multiline?"textarea":"input",undefined,l);
    input.value=value || "";return input;
  }
  function close(){clearInterval(polling);overlay?.remove();overlay=null;}
  async function refresh(){if(!task)return; const r=await api("get");render(r);}
  function render(view={}) {
    if(!overlay)return;
    const body=overlay.querySelector(".leo-research-body"); body.replaceChildren();
    overlay.querySelectorAll("nav button[data-tab]").forEach(b=>{
      if(b.dataset.tab===tab)b.setAttribute("aria-current","step");else b.removeAttribute("aria-current");
    });
    overlay.querySelector(".leo-research-title").textContent="科研任务 · "+(task?labels[task.state] || task.state:"创建任务");
    if(!task) {
      paragraph(body,"首版支持 1D Poisson 校准。其他问题可以整理为草案，暂不能启动正式求解。");
      const prompt=field(body,"研究问题", "",true);prompt.placeholder="请描述方程、区域、边界条件和你希望验证的命题。";
      button(body,"创建任务并生成草案",async()=>{
        await api("create",{...await association(),prompt:prompt.value});
        try { await api("draft"); } finally { await refresh(); }
      });
      button(body,"查看本会话的科研任务",async()=>{
        const r=await api("list",await association());
        const list=el("div",undefined,body);
        for(const item of r.tasks)button(list,`${labels[item.state] || item.state} · ${item.prompt.slice(0,60)}`,async()=>{task={taskId:item.taskId};await refresh();});
        if(!r.tasks.length)paragraph(list,"此会话尚无科研任务。");
      });
      return;
    }
    paragraph(body,task.prompt);
    if(task.state==="DRAFT") {
      paragraph(body,task.draft ? "下一步：在“问题与模型”核对草案并确认模型；现在还没有启动计算。" : "下一步：生成问题草案，核对后确认模型；现在还没有启动计算。");
      if(tab!=="model")button(body,"前往问题与模型",async()=>{tab="model";await refresh();});
    } else if(task.state==="MODEL_CONFIRMED" && tab!=="run") {
      button(body,"前往准备运行确认包",async()=>{tab="run";await refresh();});
    } else if(task.state==="READY_FOR_RUN_APPROVAL" && tab!=="run") {
      button(body,"前往审阅运行确认包",async()=>{tab="run";await refresh();});
    }
    if(tab==="model") {
      if(!task.draft) {
        paragraph(body,"使用当前会话绑定的模型整理问题；生成草案不会执行代码。");
        button(body,"生成问题草案",async()=>{await api("draft");await refresh();}); return;
      }
      const d=task.draft;
      const objective=el("section",undefined,body);objective.className="research-section";
      el("h3","研究目标",objective);paragraph(objective,d.objective);
      const modelGrid=el("div",undefined,body);modelGrid.className="research-model-grid";
      const card=(label,text)=>{const c=el("section",undefined,modelGrid);c.className="research-model-card";el("h3",label,c);paragraph(c,text);};
      card("控制方程",d.supported?"−u″(x) = π² sin(πx)":d.equation);
      card("求解区域",Array.isArray(d.domain)?`${d.domain[0]} < x < ${d.domain[1]}`:"尚待补充");
      card("边界条件",d.boundary&&Array.isArray(d.domain)?`u(${d.domain[0]}) = ${d.boundary.left}；u(${d.domain[1]}) = ${d.boundary.right}`:"尚待补充");
      card("参考与方法",d.template?`${d.template.reference} · ${d.template.solver}`:"尚未选择已验证求解方案");
      el("h3","假设与待补信息",body).className="research-subheading";
      const list=el("ul",undefined,body);
      d.assumptions.forEach(a=>el("li",`${a.source==="USER"?"用户提供":"模板建议"}：${a.text}${a.quote?"（"+a.quote+"）":""}`,list));
      [...d.missing.map(x=>"缺失："+x),...d.conflicts.map(x=>"冲突："+x)].forEach(x=>el("li",x,list));
      if(d.template?.method){
        el("h3","方法与验收规则（已验证模板，确认模型即一并确认）",body).className="research-subheading";
        const method=el("dl",undefined,body);
        for(const [key,label] of methodLabels){ if(d.template.method[key]){el("dt",label,method);el("dd",d.template.method[key],method);} }
      }
      paragraph(body,d.supportMessage);
      if(task.forkedFrom)paragraph(body,"本任务由 "+task.forkedFrom.taskId+" 的草案新建；原任务及其数据保持不变。");
      if(task.state==="DRAFT" || task.state==="MODEL_CONFIRMED") {
        button(body,"修改模型草案",async()=>{
          const editor=el("div",undefined,body);
          const objective=field(editor,"研究目标",d.objective), equation=field(editor,"方程",d.equation);
          const left=field(editor,"区域左端",d.domain?.[0]?.toString()), right=field(editor,"区域右端",d.domain?.[1]?.toString());
          const bcLeft=field(editor,"左端 Dirichlet 值",d.boundary?.left?.toString()), bcRight=field(editor,"右端 Dirichlet 值",d.boundary?.right?.toString());
          const missing=field(editor,"尚缺信息（每行一项）",d.missing.join("\n"),true), conflicts=field(editor,"冲突（每行一项）",d.conflicts.join("\n"),true);
          button(editor,"保存修改并撤销原模型确认",async()=>{
            if([left,right,bcLeft,bcRight].some(x=>!x.value.trim() || !Number.isFinite(Number(x.value))))throw new Error("请填写有效数值。");
            const lines=x=>x.value.split("\n").map(s=>s.trim()).filter(Boolean);
            await api("update",{draft:{objective:objective.value,equation:equation.value,domain:[Number(left.value),Number(right.value)],
              boundary:{left:Number(bcLeft.value),right:Number(bcRight.value)},assumptions:d.assumptions,missing:lines(missing),conflicts:lines(conflicts)}});
            await refresh();
          });
        });
      }
      if(task.state==="DRAFT" && d.supported)button(body,"审阅并确认模型",async()=>{await api("approve_model");await refresh();}).className="research-primary";
      if(task.modelApproval)paragraph(body,"模型确认："+task.modelApproval.at+" · "+task.modelApproval.contentHash);
    } else if(tab==="run") {
      if(task.state==="MODEL_CONFIRMED")button(body,"准备运行确认包",async()=>{await api("prepare");await refresh();});
      if(plan) {
        paragraph(body,`计划：主实验 → Tier-1 → 独立复现 → G6。预算 ${plan.budgetSeconds/60} 分钟。`);
        const list=el("dl",undefined,body);
        for(const [key,value] of Object.entries({"规格身份":plan.specHash,"代码身份":plan.codeHash,"Claim 集":plan.claimMember,
          "样本身份":plan.claimSampleSetHash,"种子方案":JSON.stringify(plan.seedProtocol),"复现种子偏移":plan.reproductionSeedOffset,
          "环境 A":JSON.stringify(plan.environmentA),"环境 B":JSON.stringify(plan.environmentB),"复现容差":JSON.stringify(plan.expectedTolerance)})){
          el("dt",key,list);el("dd",String(value),list);
        }
        const details=el("details",undefined,body);el("summary","完整运行确认包",details);el("pre",JSON.stringify(plan,null,2),details);
      }
      if(task.state==="READY_FOR_RUN_APPROVAL")button(body,"审阅并确认正式运行",async()=>{await api("approve_run");await refresh();});
      if(view.progress)paragraph(body,"当前阶段："+view.progress.phase+" · "+view.progress.at);
      if(["RUNNING","CANCELLING"].includes(task.state))button(body,"停止计算并保留证据",async()=>{await api("cancel");await refresh();});
      if(task.preparationError){
        paragraph(body,errors[task.preparationError] || "准备失败。请检查运行环境和准备日志；没有启动正式训练。");
        forkButton(body);
      }
      if(RESTARTABLE.has(task.state)){paragraph(body,"这次计算已结束（"+(labels[task.state] || task.state)+"），证据原样保留。若要重新尝试，请以此草案新建任务。");forkButton(body);}
    } else if(tab==="verification") {
      const v=view.verification || {verified:false,allowedClaims:[]};
      paragraph(body,"证据核验："+(v.verified?"已通过当前记录核验":"尚未通过")+"；允许声明："+(v.allowedClaims?.join("、") || "无"));
      const claims=el("p",undefined,body);
      if(v.allowedClaims?.length)for(const c of v.allowedClaims)chip(claims,"允许 "+c,"claim");
      else chip(claims,v.verified?"只允许探索性描述":"不可下结论",v.verified?"exploratory":"blocked");
      if(v.reason)paragraph(body,"当前状态："+(labels[v.reason] || v.reason));
      if(v.dimensions){const dims=el("p",undefined,body);
        for(const [key,value]of Object.entries(v.dimensions))chip(dims,key+" · "+value.status,value.status==="PASS"?"verified":value.status==="FAIL"?"failed":"blocked");}
      if(v.blockedClaims)for(const c of v.blockedClaims){const row=el("p",undefined,body);chip(row,c.level+" 被阻断","blocked");row.append(" "+c.reason);}
      if(v.verified){const interpretation=field(body,"人的科学解释与适用边界",task.humanReview?.interpretation || "",true);
        button(body,"确认已审阅结论",async()=>{await api("review",{interpretation:interpretation.value});await refresh();});}
      paragraph(body,"过程完成、测试通过与科学结论成立分别记录。人工解释不能提升机器允许的 Claim。");
    } else {
      button(body,"列出证据文件",async()=>{const r=await api("evidence");const list=el("div",undefined,body);
        for(const file of r.files)button(list,file,async()=>{const result=await api("evidence",{path:file});
          let preview=body.querySelector("pre");if(!preview)preview=el("pre",undefined,body);preview.textContent=result.text;});});
      button(body,"导出审计与复现资料",async()=>{const r=await api("export");paragraph(body,"已导出并校验："+r.path);});
    }
  }
  function open() {
    if(overlay)return;
    if(frameContext!==session().frameId){task=null;plan=null;tab="model";frameContext=session().frameId;}
    overlay=el("section",undefined,document.body);overlay.className="leo-research-overlay";overlay.setAttribute("role","dialog");overlay.setAttribute("aria-modal","true");overlay.setAttribute("aria-label","科研任务");
    const header=el("header",undefined,overlay);el("h2","科研任务",header).className="leo-research-title";
    const exit=el("button","关闭",header);exit.onclick=close;
    const nav=el("nav",undefined,overlay);
    for(const [key,label]of [["model","问题与模型"],["run","运行"],["verification","验证与结论"],["evidence","证据"]]){
      const b=button(nav,label,async()=>{tab=key;await refresh();if(!task)render();});b.dataset.tab=key;
    }
    button(nav,"新建任务",async()=>{task=null;plan=null;tab="model";render();});
    el("main",undefined,overlay).className="leo-research-body";
    const live=el("p","",overlay);live.className="leo-research-status";live.setAttribute("role","status");
    render();if(task)action(refresh);
    polling=setInterval(()=>{if(task && !busy && ["RUNNING","CANCELLING"].includes(task.state))action(refresh);},3000);
    overlay.addEventListener("keydown",event=>{
      if(event.key==="Escape" && !busy){event.preventDefault();close();return;}
      if(event.key!=="Tab")return;
      const focusable=[...overlay.querySelectorAll("button:not(:disabled),input,textarea,summary")];
      const first=focusable[0], last=focusable[focusable.length-1];
      if(event.shiftKey && document.activeElement===first){event.preventDefault();last?.focus();}
      if(!event.shiftKey && document.activeElement===last){event.preventDefault();first?.focus();}
    });
    exit.focus();
  }
  function install(){if(document.getElementById("leo-research-entry"))return;const b=el("button","科研任务",document.body);b.id="leo-research-entry";b.onclick=open;}
  window.LeoResearch={open,close};
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
  return true;
})();
