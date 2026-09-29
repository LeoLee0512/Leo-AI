/* Research UI: rendering only. Native service owns confirmations and scientific state. */
(() => {
  "use strict";
  // Leo's own workbench is the only host; there is no upstream page to attach to any more.
  if (!window.LeoWorkbench) return false;
  if (window.__leoResearchPanel) return true;
  window.__leoResearchPanel = true;
  let overlay, task, plan, tab = "model", polling, busy = false, frameContext;
  const labels = {DRAFT:"问题草案", MODEL_CONFIRMED:"模型已确认", PREPARING:"正在准备运行确认包", READY_FOR_RUN_APPROVAL:"等待正式运行确认",
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
    PREPARATION_TIMED_OUT:"准备运行确认包超时；没有启动训练。可以以此草案新建任务重试。",
    RESEARCH_FAMILY_INVALID:"这个草案没有匹配已验证模板，不能准备正式运行。",
    PREPARATION_FAILED_SEE_EVIDENCE:"准备失败；没有启动训练。可以查看证据中的准备日志，或以此草案新建任务重试。",
    CREATE_NEW_TASK_FOR_REVISION:"这个任务已生成运行数据，不能再修改；请以此草案新建任务。",
    RESEARCH_TASK_ALREADY_RUNNING:"已有另一个科研任务正在计算；请等它结束或停止后再确认。",
    FORK_REQUIRES_STOPPED_WORKER:"计算仍在进行，结束或停止后才能以此草案新建任务。",
    FORK_REQUIRES_DRAFT:"这个任务还没有草案，无法复制。",
    PREPARATION_INTERRUPTED:"上次准备在应用关闭时中断，没有启动训练。可以重新准备；若已预留盲测集，请以此草案新建任务。",
    PREPARATION_ALREADY_EXISTS:"这个任务已经预留过盲测集，不能再次准备；请以此草案新建任务。",
    RUN_PLAN_IDENTITY_CHANGED:"准备确认包之后，代码、科学环境或准备数据发生了变化（例如软件升级），这份确认包不能再用于正式运行；请以此草案新建任务。",
    NO_FRESH_DISJOINT_CLAIM_SET:"本机的盲测集额度已用完，无法再准备新的正式运行。",
    RESEARCH_RUNTIME_UNAVAILABLE:"科研运行环境不可用：科学解释器或源码快照缺失，请检查安装。",
    ENTITLEMENT_REQUIRED:"此功能需要开通科研任务服务。",
    RECHECK_REQUIRES_COMPLETED:"只有已完成的运行可以重新核对。",
    EXPORT_EVIDENCE_INVALID:"证据核验没有通过，不能导出为可引用的证据包。"
  };
  // Where and why a run ended, in words; the raw codes stay in the task record.
  const phaseLabels = {main:"主实验", tier1:"Tier-1 扰动检验", reproduction:"独立复现", g6:"G6 复现判定", supervisor:"运行前核对"};
  const endReasons = {WORKER_LOST:"计算进程意外退出（可能是应用被关闭或系统睡眠）", RUN_CODE_CHANGED:"运行期间代码身份发生变化",
    PLAN_CODE_CHANGED:"代码与运行确认包不一致", PREPARED_EVIDENCE_CHANGED:"准备好的数据被改动", PLAN_ENVIRONMENT_CHANGED:"科学环境与运行确认包不一致",
    RUN_APPROVAL_STALE:"运行确认与确认包不一致", RESOURCE_BUSY:"另一项计算正在占用", RUN_NOT_ADMITTED:"任务不处于已确认运行的状态"};
  function ending(c) {
    if(!c)return "";
    const where=c.phase?"结束于「"+(phaseLabels[c.phase] || c.phase)+"」":"";
    const why=c.reason?(endReasons[c.reason] || c.reason):(c.exitCode!=null?"该阶段未通过（退出码 "+c.exitCode+"）":"");
    return [where,why].filter(Boolean).join("：");
  }
  const methodLabels = [["network","网络与边界"],["training","训练"],["sampling","配点采样"],["losses","损失权重"],["seeds","种子"],
    ["precision","数值精度"],["reference","参考解"],["acceptance","验收规则"],["validation","验证链"],["claimRule","结论规则"]];
  const RESTARTABLE = new Set(["STOPPED","INTERRUPTED","CANCELLED","TIMED_OUT"]);
  // Display names only; the raw key stays in the tooltip so records can still be matched.
  const dimensionLabels = {math:"数学",impl:"实现",train:"训练",physics:"物理",external:"外部精度",repro:"复现"};
  const statusLabels = {PASS:"通过",PARTIAL:"部分通过",FAIL:"未通过",BLOCKED:"受阻",NOT_CHECKED:"未检查",NOT_RUN:"未运行",NOT_APPLICABLE:"不适用"};
  const reasonLabels = {EVIDENCE_HASH_MISMATCH:"证据文件与清单哈希不符",EVIDENCE_VALIDATION_FAILED:"证据校验失败"};
  function chip(parent, text, kind) { const c=el("span",text,parent); c.className="trust-chip trust-"+kind; return c; }
  function hint(parent, text) { const p=paragraph(parent,text); p.className="research-hint"; return p; }
  function primary(b) { b.className="research-primary"; return b; }
  // Plan values are read by people here; the exact document stays in the full package below.
  function describe(key, value) {
    if(value && typeof value==="object") {
      if(key==="seedProtocol" && "runs" in value)
        return `${value.runs} 组种子 · init ${value.initBase}+i · sample ${value.sampleBase}+i · batch ${value.batchBase}+i`;
      if(key==="expectedTolerance" && "devRelL2MedianAbsDiff" in value)
        return `开发集相对 L2 中位数差 ≤ ${value.devRelL2MedianAbsDiff}`+(value.devRelL2MedianRelDiff!=null?` 且 ≤ ${value.devRelL2MedianRelDiff} 倍原中位数`:"")
          +(value.seedProtocolVerdictMustAgree?" · 种子判定必须一致":"");
      if(/^environment/.test(key) && ("frameworkVersion" in value || "osFamily" in value))
        return [value.osFamily,value.frameworkVersion,value.blasBackend,value.acceleratorClass,value.installationId].filter(Boolean).join(" · ");
      return Object.entries(value).map(([k,v])=>k+"："+(v && typeof v==="object"?JSON.stringify(v):v)).join(" · ");
    }
    return String(value);
  }
  function verdict(parent, v) {
    const allowed=v.allowedClaims || [];
    const kind=allowed.length?"claim":v.verified?"exploratory":"blocked";
    const card=el("section",undefined,parent);card.className="research-verdict verdict-"+kind;
    el("p","结论等级",card).className="verdict-label";
    el("h3",allowed.length?"允许声明 "+allowed.join("、"):v.verified?"只允许探索性描述":"尚不可下结论",card);
    const reason=v.reason && (labels[v.reason] || reasonLabels[v.reason] || (/^No current claim decision/.test(v.reason)?"没有当前结论判定，不允许精度声明。":v.reason));
    paragraph(card,(v.verified?"证据核验已通过当前记录。":"证据核验尚未通过。")+(reason?"当前状态："+reason:""));
    const chips=el("p",undefined,card);chips.className="verdict-claims";
    if(allowed.length)for(const c of allowed)chip(chips,"允许 "+c,"claim");
    else chip(chips,v.verified?"只允许探索性描述":"不可下结论",v.verified?"exploratory":"blocked");
    return card;
  }
  function dimensionChips(parent, vector) {
    const dims=el("div",undefined,parent);dims.className="research-dimensions";
    for(const [key,value]of Object.entries(vector)){
      const status=(typeof value==="string"?value:value?.status) || "NOT_CHECKED";
      const c=chip(dims,(dimensionLabels[key] || key)+" · "+(statusLabels[status] || status),status==="PASS"?"verified":status==="FAIL"?"failed":"blocked");
      c.title=key+" · "+status;
    }
    return dims;
  }
  async function openTasks(parent, scope) {
    const r=await api("list",scope==="all"?{scope:"all"}:await association());
    const list=el("div",undefined,parent);list.className="research-task-list";
    for(const item of r.tasks)button(list,`${labels[item.state] || item.state} · ${item.prompt.slice(0,60)}`+(scope==="all"&&item.frameId!==session().frameId?"（其他对话）":""),async()=>{task={taskId:item.taskId};await refresh();});
    if(!r.tasks.length)paragraph(list,scope==="all"?"还没有任何科研任务。":"此会话尚无科研任务。");
  }
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
  // A waiting text with "{s}" counts the seconds, so a long model call never looks frozen.
  async function action(fn, waiting) {
    if(busy)return; busy=true; overlay?.setAttribute("aria-busy","true");
    const text=waiting || "正在处理，请稍候。模型草拟可能需要一分钟；计算不会在确认前启动。";
    const started=Date.now();const show=()=>status(text.replace("{s}",String(Math.floor((Date.now()-started)/1000))));
    show();const ticker=text.includes("{s}")?setInterval(show,1000):null;
    overlay?.querySelectorAll("button").forEach(b=>b.disabled=true);
    try { await fn(); status("操作已完成。科学状态以验证结果为准。"); }
    catch(e){ status(e.message); }
    finally {if(ticker)clearInterval(ticker);busy=false; overlay?.removeAttribute("aria-busy");overlay?.querySelectorAll("button").forEach(b=>b.disabled=false);}
  }
  const DRAFTING="正在生成问题草案：模型正在思考，已等待 {s} 秒（推理模型通常需要 30–90 秒，最长 3 分钟）。计算不会在确认前启动。";
  function button(parent, text, fn, waiting) { const b=el("button",text,parent); b.type="button"; b.onclick=()=>action(fn,waiting);return b; }
  function layer(parent, text) { el("p",text,parent).className="guide-layer"; }
  // The reader's view of a verified run: conclusion first, then the checks in mathematical terms,
  // then why the records count as evidence. Every number comes from the run's records.
  function guideView(body, g) {
    const top=el("section",undefined,body);top.className="research-verdict verdict-claim guide-verdict";
    el("p","一句话结论",top).className="verdict-label";el("h3",g.headline,top);paragraph(top,g.subline);
    layer(body,"第一层 · 一页看懂");
    const nums=el("div",undefined,body);nums.className="guide-nums";
    for(const n of g.numbers){const c=el("div",undefined,nums);c.className="guide-num";el("small",n.label,c);el("b",n.value,c);paragraph(c,n.text);}
    const say=el("div",undefined,body);say.className="guide-say";
    for(const [kind,title,items] of [["can","可以这样说",g.can],["cannot","不能这样说",g.cannot]]){
      const box=el("div",undefined,say);box.className="guide-"+kind;el("h4",title,box);
      const list=el("ul",undefined,box);(items.length?items:["—"]).forEach(x=>el("li",x,list));
    }
    layer(body,"第二层 · 用数学语言看六项检查");
    for(const d of g.dimensions){
      const row=el("details",undefined,body);row.className="guide-dim";const head=el("summary",undefined,row);
      const name=el("span",undefined,head);name.className="guide-dim-name";el("strong",d.name,name);
      el("small",d.short+" · "+(statusLabels[d.status] || d.status),name);
      el("span",d.text,head).className="guide-dim-text";
      const checks=el("ul",undefined,row);
      for(const c of d.checks){const li=el("li",c.plain+"："+(statusLabels[c.status] || c.status),checks);if(c.reason)el("code",c.reason,li);}
    }
    layer(body,"第三层 · 凭什么说这是证据");
    const chain=el("ol",undefined,body);chain.className="guide-chain";
    for(const s of g.chain){const li=el("li",undefined,chain);el("strong",s.title,li);paragraph(li,s.text);el("span",s.proof,li).className="guide-proof";}
    const actions=el("div",undefined,body);actions.className="guide-actions";
    const result=el("section",undefined,body);result.className="guide-check";result.hidden=true;
    primary(button(actions,"一键重新核对",async()=>{
      const r=await api("recheck");result.hidden=false;result.replaceChildren();
      el("h4","重新核对",result);paragraph(result,"在你的电脑上逐项重算，不依赖原来的核验结果。");
      const list=el("ol",undefined,result);
      for(const s of r.steps){const li=el("li",undefined,list);li.className=s.passed?"ok":"bad";el("span",s.passed?"✓":"✗",li).className="mark";
        el("span",s.label+(s.detail?"（"+s.detail+"）":""),li);el("small",s.seconds+" 秒",li);}
      paragraph(result,r.passed?"核对通过：这份证据与原始计算记录一致，结论可以引用。":"核对未通过：请不要引用这份结论，并保留证据以便排查。").className=r.passed?"guide-pass":"guide-fail";
      result.scrollIntoView({block:"nearest"});
    },"正在重新核对：逐项重算指纹并复核结论，约需 10 秒。"));
    button(actions,"导出证据包（含证据说明书）",async()=>{const r=await api("export");paragraph(body,"已导出并校验："+r.path+"。包内的「证据说明书.html」可直接用浏览器打开。");},
      "正在导出：完整核验证据并生成证据说明书，约需 10 秒。");
    el("span","不必逐个阅读文件：重新核对会逐项重算指纹并复核结论。",actions).className="guide-note";
    const glossary=el("details",undefined,body);glossary.className="guide-more";el("summary","术语表",glossary);
    const gl=el("dl",undefined,glossary);for(const [term,text] of g.glossary){el("dt",term,gl);el("dd",text,gl);}
    const map=el("details",undefined,body);map.className="guide-more";el("summary","给想深入的读者：证据地图（每个文件是什么）",map);
    const ml=el("dl",undefined,map);for(const [file,text] of g.map){el("dt",file,ml);el("dd",text,ml);}
    rawFiles(map);
  }
  function rawFiles(parent) {
    button(parent,"列出全部证据文件",async()=>{const r=await api("evidence");const list=el("div",undefined,parent);list.className="research-task-list";
      for(const file of r.files)button(list,file,async()=>{const result=await api("evidence",{path:file});
        let preview=parent.querySelector("pre");if(!preview)preview=el("pre",undefined,parent);preview.textContent=result.text;});});
  }
  function paragraph(parent, text) { return el("p",text,parent); }
  function field(parent,label,value, multiline=false) {
    const l=el("label",label,parent), input=el(multiline?"textarea":"input",undefined,l);
    input.value=value || "";return input;
  }
  /* 2.2.11 · Two verified templates: 1D (domain [a, b], boundary {left, right}) and 2D on a
     rectangle (domain [[x0, x1], [y0, y1]], boundary {left, right, bottom, top}). */
  function isTwoD(d){return d?.templateId==="poisson2d-v1" || (Array.isArray(d?.domain)&&Array.isArray(d.domain[0]))
    || !!(d?.boundary&&("bottom" in d.boundary || "top" in d.boundary));}
  function box2(d){return Array.isArray(d?.domain)&&Array.isArray(d.domain[0])&&Array.isArray(d.domain[1])?d.domain:null;}
  function domainText(d){
    const box=box2(d);if(box)return `${box[0][0]} < x < ${box[0][1]}，${box[1][0]} < y < ${box[1][1]}`;
    return Array.isArray(d.domain)&&!isTwoD(d)?`${d.domain[0]} < x < ${d.domain[1]}`:"尚待补充";
  }
  function boundaryText(d){
    const b=d.boundary;if(!b)return "尚待补充";
    if(isTwoD(d)){const box=box2(d);const at=(axis,i)=>box?axis+" = "+box[axis==="x"?0:1][i]:"";
      return [["left","左边",at("x",0)],["right","右边",at("x",1)],["bottom","下边",at("y",0)],["top","上边",at("y",1)]]
        .map(([k,name,where])=>`${name}${where?"（"+where+"）":""} u = ${b[k]??"?"}`).join("；");}
    return Array.isArray(d.domain)?`u(${d.domain[0]}) = ${b.left}；u(${d.domain[1]}) = ${b.right}`:"尚待补充";
  }
  // The editor keeps the draft's shape; the person can switch a draft between 1D and 2D before saving.
  function draftEditor(parent,d,twoD){
    const editor=el("div",undefined,parent);editor.className="research-editor";
    const text=v=>v==null?"":String(v);
    const draw=dim2=>{
      editor.replaceChildren();
      const objective=field(editor,"研究目标",d.objective), equation=field(editor,"方程",d.equation);
      const box=box2(d), line=Array.isArray(d.domain)&&!box?d.domain:null, b=d.boundary||{};
      const numbers=dim2?{
        x0:field(editor,"x 下限",text(box?.[0]?.[0]??line?.[0])),x1:field(editor,"x 上限",text(box?.[0]?.[1]??line?.[1])),
        y0:field(editor,"y 下限",text(box?.[1]?.[0])),y1:field(editor,"y 上限",text(box?.[1]?.[1])),
        left:field(editor,"左边（x 下限处）Dirichlet 值",text(b.left)),right:field(editor,"右边（x 上限处）Dirichlet 值",text(b.right)),
        bottom:field(editor,"下边（y 下限处）Dirichlet 值",text(b.bottom)),top:field(editor,"上边（y 上限处）Dirichlet 值",text(b.top))}:{
        a:field(editor,"区域左端",text(line?.[0]??box?.[0]?.[0])),b:field(editor,"区域右端",text(line?.[1]??box?.[0]?.[1])),
        left:field(editor,"左端 Dirichlet 值",text(b.left)),right:field(editor,"右端 Dirichlet 值",text(b.right))};
      const missing=field(editor,"尚缺信息（每行一项）",d.missing.join("\n"),true), conflicts=field(editor,"冲突（每行一项）",d.conflicts.join("\n"),true);
      button(editor,dim2?"改为一维问题":"改为二维问题",async()=>draw(!dim2));
      button(editor,"保存修改并撤销原模型确认",async()=>{
        if(Object.values(numbers).some(x=>!x.value.trim() || !Number.isFinite(Number(x.value))))throw new Error("请填写有效数值。");
        const n=k=>Number(numbers[k].value), lines=x=>x.value.split("\n").map(s=>s.trim()).filter(Boolean);
        const shape=dim2?{domain:[[n("x0"),n("x1")],[n("y0"),n("y1")]],boundary:{left:n("left"),right:n("right"),bottom:n("bottom"),top:n("top")}}
          :{domain:[n("a"),n("b")],boundary:{left:n("left"),right:n("right")}};
        await api("update",{draft:{objective:objective.value,equation:equation.value,...shape,
          assumptions:d.assumptions,missing:lines(missing),conflicts:lines(conflicts)}});
        await refresh();
      });
    };
    draw(twoD);return editor;
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
      paragraph(body,"支持一维与二维 Poisson 校准（各有一个已验证模板，由草案自动识别）。其他问题可以整理为草案，暂不能启动正式求解。").className="research-prompt";
      const prompt=field(body,"研究问题", "",true);prompt.placeholder="请描述方程、区域、边界条件和你希望验证的命题。";
      primary(button(body,"创建任务并生成草案",async()=>{
        await api("create",{...await association(),prompt:prompt.value});
        try { await api("draft"); } finally { await refresh(); }
      },DRAFTING));
      button(body,"查看本会话的科研任务",async()=>openTasks(body,"frame"));
      button(body,"查看全部科研任务",async()=>openTasks(body,"all"));
      return;
    }
    paragraph(body,task.prompt).className="research-prompt";
    if(task.state==="DRAFT") {
      hint(body,task.draft ? "下一步：在“问题与模型”核对草案并确认模型；现在还没有启动计算。" : "下一步：生成问题草案，核对后确认模型；现在还没有启动计算。");
      if(tab!=="model")button(body,"前往问题与模型",async()=>{tab="model";await refresh();});
    } else if(["MODEL_CONFIRMED","PREPARING"].includes(task.state) && tab!=="run") {
      button(body,"前往准备运行确认包",async()=>{tab="run";await refresh();});
    } else if(task.state==="READY_FOR_RUN_APPROVAL" && tab!=="run") {
      button(body,"前往审阅运行确认包",async()=>{tab="run";await refresh();});
    }
    if(tab==="model") {
      if(!task.draft) {
        const failed=task.draftError;
        if(failed)hint(body,"上一次生成草案没有成功（等待了 "+failed.seconds+" 秒）："+(errors[failed.code] || failed.code+"。任务已保留，可以重试。"));
        else paragraph(body,"使用当前会话绑定的模型整理问题；生成草案不会执行代码。");
        primary(button(body,failed?"重新生成草案":"生成问题草案",async()=>{try{await api("draft");}finally{await refresh();}},DRAFTING)); return;
      }
      const d=task.draft;
      const objective=el("section",undefined,body);objective.className="research-section";
      el("h3","研究目标",objective);paragraph(objective,d.objective);
      const modelGrid=el("div",undefined,body);modelGrid.className="research-model-grid";
      const card=(label,text)=>{const c=el("section",undefined,modelGrid);c.className="research-model-card";el("h3",label,c);paragraph(c,text);};
      const twoD=isTwoD(d);
      card("问题类型",d.supported?(twoD?"二维 Poisson · 已验证模板":"一维 Poisson · 已验证模板"):(twoD?"二维问题 · 未匹配已验证模板":"未匹配已验证模板"));
      card("控制方程",d.supported?(twoD?"−(u_xx + u_yy) = 2π² sin(πx) sin(πy)":"−u″(x) = π² sin(πx)"):d.equation);
      card("求解区域",domainText(d));
      card("边界条件",boundaryText(d));
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
      if(!d.supported && d.unsupportedReasons?.length){
        // Say which field misses the verified template, so the person can fix it instead of starting over.
        const why=el("section",undefined,body);why.className="research-hint guide-why";
        el("strong","为什么暂不能准备运行",why);const list=el("ul",undefined,why);d.unsupportedReasons.forEach(r=>el("li",r,list));
        if(task.state==="DRAFT")paragraph(why,"可以点「修改模型草案」直接改正，不需要重新生成，也不占用盲测集。");
      }
      if(task.forkedFrom)paragraph(body,"本任务由 "+task.forkedFrom.taskId+" 的草案新建；原任务及其数据保持不变。");
      if(task.state==="DRAFT" || task.state==="MODEL_CONFIRMED") {
        let editor=null;
        button(body,"修改模型草案",async()=>{if(!editor)editor=draftEditor(body,d,twoD);});
      }
      if(task.state==="DRAFT" && d.supported)button(body,"审阅并确认模型",async()=>{await api("approve_model");await refresh();}).className="research-primary";
      if(task.modelApproval)paragraph(body,"模型确认："+task.modelApproval.at+" · "+task.modelApproval.contentHash);
    } else if(tab==="run") {
      if(task.state==="MODEL_CONFIRMED" && view.canPrepare){
        const q=view.quota;
        // Preparing reserves a blind claim grid for good; say so, and how many remain, before the click.
        if(q && q.remaining<=0)paragraph(body,errors.NO_FRESH_DISJOINT_CLAIM_SET);
        else {
          if(q)hint(body,`准备会永久占用本机 1 个${q.family==="poisson2d"?"二维":"一维"}盲测集（剩余 ${q.remaining} / ${q.capacity}；一维与二维分开计数）。之后无论准备或运行成败都不退还，这是防止反复试错的规则。`);
          primary(button(body,"准备运行确认包",async()=>{await api("prepare");await refresh();}));
        }
      }
      if(task.state==="PREPARING")hint(body,`正在准备运行确认包：核对代码身份，检查两个科学环境，并预留盲测集。最长约 ${view.prepareLimitMinutes || 5} 分钟，不会启动训练；可以关闭本面板，稍后回来查看。`);
      if(plan) {
        const limit=Math.round(plan.budgetSeconds/60);
        hint(body,"计划：主实验 → Tier-1 → 独立复现 → G6。"+(view.estimateMinutes?`预计约 ${view.estimateMinutes} 分钟，上限 ${limit} 分钟。`:`上限 ${limit} 分钟。`));
        const list=el("dl",undefined,body);
        for(const [key,label] of [["specHash","规格身份"],["codeHash","代码身份"],["claimMember","Claim 集"],["claimSampleSetHash","样本身份"],
          ["seedProtocol","种子方案"],["reproductionSeedOffset","复现种子偏移"],["parallelWorkers","并行训练进程"],["environmentA","环境 A"],["environmentB","环境 B"],["expectedTolerance","复现容差"]]){
          if(plan[key]==null)continue;
          el("dt",label,list);el("dd",describe(key,plan[key]),list);
        }
        const details=el("details",undefined,body);el("summary","完整运行确认包",details);el("pre",JSON.stringify(plan,null,2),details);
      }
      if(task.state==="READY_FOR_RUN_APPROVAL"){
        if(task.runBlocked){paragraph(body,errors[task.runBlocked.reason] || task.runBlocked.reason);forkButton(body);}
        else primary(button(body,"审阅并确认正式运行",async()=>{await api("approve_run");await refresh();}));
      }
      if(view.progress)paragraph(body,"当前阶段："+view.progress.phase+" · "+view.progress.at);
      if(["RUNNING","CANCELLING"].includes(task.state))button(body,"停止计算并保留证据",async()=>{await api("cancel");await refresh();});
      if(task.preparationError){
        paragraph(body,errors[task.preparationError] || "准备失败。请检查运行环境和准备日志；没有启动正式训练。");
        forkButton(body);
      }
      if(RESTARTABLE.has(task.state)){
        const why=ending(task.completion);
        paragraph(body,"这次计算已结束（"+(labels[task.state] || task.state)+"）"+(why?"，"+why:"")+"。证据原样保留，可在「验证与结论」和「证据」中查看。若要重新尝试，请以此草案新建任务。");
        forkButton(body);
      }
    } else if(tab==="verification") {
      const v=view.verification || {verified:false,allowedClaims:[]};
      verdict(body,v);
      if(v.dimensions){el("h3","可信度维度",body).className="research-subheading";dimensionChips(body,v.dimensions);}
      if(v.failure){
        // A run that ended without a decision still shows what it recorded: failures are evidence too.
        const f=v.failure;el("h3","这次运行记录下的结果",body).className="research-subheading";
        const facts=[];
        if(f.completion)facts.push(ending(f.completion));
        if(f.gate!=null)facts.push("未通过的门禁：Gate "+f.gate);
        if(f.observedSignatures?.length)facts.push("观察到的失败特征："+f.observedSignatures.join("、"));
        if(f.tier1Passed===false)facts.push("Tier-1 扰动检验未通过");
        if(f.finalState)facts.push("运行记录状态："+f.finalState);
        const list=el("ul",undefined,body);for(const fact of facts.filter(Boolean))el("li",fact,list);
        if(f.trustVector)dimensionChips(body,f.trustVector);
      }
      if(v.blockedClaims?.length){el("h3","被阻断的声明",body).className="research-subheading";
        for(const c of v.blockedClaims){const row=el("p",undefined,body);row.className="research-blocked";chip(row,c.level+" 被阻断","blocked");if(c.reason)row.append(" "+c.reason);}}
      if(v.verified){const interpretation=field(body,"人的科学解释与适用边界",task.humanReview?.interpretation || "",true);
        primary(button(body,"确认已审阅结论",async()=>{await api("review",{interpretation:interpretation.value});await refresh();}));}
      paragraph(body,"过程完成、测试通过与科学结论成立分别记录。人工解释不能提升机器允许的 Claim。");
    } else if(view.guide) {
      guideView(body,view.guide);
    } else {
      if(task.state==="COMPLETED" && view.verification && !view.verification.verified)
        hint(body,"证据核验没有通过，不生成证据说明书；原始文件仍原样保留在下面。");
      rawFiles(body);
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
    polling=setInterval(()=>{if(task && !busy && ["PREPARING","RUNNING","CANCELLING"].includes(task.state))action(refresh);},3000);
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
