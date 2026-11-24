/* Research UI: rendering only. Native service owns confirmations and scientific state. */
(() => {
  "use strict";
  // Leo's own workbench is the only host; there is no upstream page to attach to any more.
  if (!window.LeoWorkbench) return false;
  if (window.__leoResearchPanel) return true;
  window.__leoResearchPanel = true;
  let overlay, backdrop, task, plan, view = {}, tab = "model", polling, busy = false, frameContext;
  /* 3.2.0 · The panel speaks plainly: internal codes (C0–C3, G1–G6, Tier-1, signatures, hashes) are
     written out in words, and the raw code follows in small grey type so records can still be matched.
     Longer sentences come from the service (leo_shell/research_words.py, outside the code identity). */
  const labels = {DRAFT:"问题草案", MODEL_CONFIRMED:"模型已确认", PREPARING:"正在准备运行确认包", READY_FOR_RUN_APPROVAL:"等待正式运行确认",
    RUNNING:"正在计算", CANCELLING:"正在停止", CANCELLED:"已停止", TIMED_OUT:"超出时间上限",
    STOPPED:"计算或验证未通过", INTERRUPTED:"运行中断", COMPLETED:"计算流程结束"};
  const shortLabels = {DRAFT:"草案", MODEL_CONFIRMED:"模型已确认", PREPARING:"正在准备", READY_FOR_RUN_APPROVAL:"等待确认运行",
    RUNNING:"正在计算", CANCELLING:"正在停止", CANCELLED:"已停止", TIMED_OUT:"超出时间上限", STOPPED:"未通过",
    INTERRUPTED:"运行中断", COMPLETED:"已完成"};
  const stateKind = {PREPARING:"run", RUNNING:"run", CANCELLING:"run", READY_FOR_RUN_APPROVAL:"warn", COMPLETED:"ok",
    STOPPED:"no", INTERRUPTED:"no", CANCELLED:"no", TIMED_OUT:"no"};
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
  // Fallbacks for when the service sends no words (an older service); the service's words win.
  const phaseLabels = {main:"主实验", tier1:"扰动检验", reproduction:"独立复现", g6:"复现判定", supervisor:"运行前核对"};
  const phaseRaw = {main:"main", tier1:"Tier-1", reproduction:"reproduction", g6:"G6", supervisor:"supervisor"};
  const endReasons = {WORKER_LOST:"计算进程意外退出（可能是应用被关闭或系统睡眠）", RUN_CODE_CHANGED:"运行期间代码身份发生变化",
    PLAN_CODE_CHANGED:"代码与运行确认包不一致", PREPARED_EVIDENCE_CHANGED:"准备好的数据被改动", PLAN_ENVIRONMENT_CHANGED:"科学环境与运行确认包不一致",
    RUN_APPROVAL_STALE:"运行确认与确认包不一致", RESOURCE_BUSY:"另一项计算正在占用", RUN_NOT_ADMITTED:"任务不处于已确认运行的状态"};
  const statusLabels = {PASS:"通过",PARTIAL:"部分通过",FAIL:"未通过",BLOCKED:"受阻",NOT_CHECKED:"未检查",NOT_RUN:"未进行",NOT_APPLICABLE:"不适用"};
  const dimensionFallback = [["math","数学设定","G1"],["impl","实现","G3"],["train","训练","G4"],["physics","物理","G5a"],["external","与精确解一致","G5b"],["repro","独立复现","G6"]];
  const reasonLabels = {EVIDENCE_HASH_MISMATCH:"证据文件与清单哈希不符",EVIDENCE_VALIDATION_FAILED:"证据校验失败"};
  const methodLabels = [["network","网络与边界"],["training","训练"],["sampling","配点采样"],["losses","损失权重"],["seeds","种子"],
    ["precision","数值精度"],["reference","参考解"],["acceptance","验收规则"],["validation","验证链"],["claimRule","结论规则"]];
  const RESTARTABLE = new Set(["STOPPED","INTERRUPTED","CANCELLED","TIMED_OUT"]);
  const LOCKED = new Set(["PREPARING","READY_FOR_RUN_APPROVAL","RUNNING","CANCELLING","CANCELLED","TIMED_OUT","STOPPED","INTERRUPTED","COMPLETED"]);
  const BUSY = new Set(["PREPARING","RUNNING","CANCELLING"]);
  const words = () => view.words || {};
  // 3.2.2 · Three verified problem families; their names in one place.
  const familyNames = {poisson1d:"一维", poisson2d:"二维", annulus:"环形"};

  // ---------------------------------------------------------------- small builders
  const el = (tag, text, parent, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; if(parent)parent.append(n); return n; };
  function paragraph(parent, text, cls) { return el("p",text,parent,cls); }
  function hint(parent, text) { return paragraph(parent,text,"research-hint"); }
  function info(parent) { return el("div",undefined,parent,"research-info"); }
  function raw(parent, text) { if(text)el("span",text,parent,"research-raw"); }
  function chip(parent, text, kind) { return el("span",text,parent,"trust-chip trust-"+kind); }
  function tick(parent, kind) { return el("span",{ok:"✓",bad:"✕",no:"–",wait:"",run:""}[kind],parent,"research-tick tick-"+kind); }
  function card(parent, cls) { return el("section",undefined,parent,"research-card"+(cls?" "+cls:"")); }
  function primary(b) { b.className="research-primary"; return b; }
  function secondary(b) { b.className="research-secondary"; return b; }
  function quiet(b) { b.className="research-quiet"; return b; }
  function dangerOutline(b) { b.className="research-danger-outline"; return b; }
  function subheading(parent, text, note) { const h=el("h3",text,parent,"research-subheading"); if(note)el("small",note,h); return h; }
  function button(parent, text, fn, waiting) { const b=el("button",text,parent); b.type="button"; b.onclick=()=>action(fn,waiting); return b; }
  // The two confirmations that open a native dialog get a two-line button: they are "the" click.
  function keyButton(parent, title, subtitle, fn, waiting) {
    const b=el("button",undefined,parent,"research-key"); b.type="button"; b.dataset.label=title; b.setAttribute("aria-label",title+"。"+subtitle);
    el("span","▶",b,"key-icon"); const t=el("span",undefined,b,"key-text"); el("b",title,t); el("small",subtitle,t); el("span","›",b,"key-arrow");
    b.onclick=()=>action(fn,waiting); return b;
  }
  function details(parent, summary) { const d=el("details",undefined,parent,"research-details"); el("summary",summary,d); return d; }
  function kv(parent, rows) { const dl=el("dl",undefined,parent,"research-kv"); for(const [k,v,r] of rows){el("dt",k,dl);const dd=el("dd",v,dl);raw(dd,r);} return dl; }
  const short = h => { if(typeof h!=="string")return h; const v=h.replace(/^sha256:/,""); return v.length>12 ? v.slice(0,8) : v; };
  const pad = n => String(n).padStart(2,"0");
  function when(iso) {
    const d=new Date(iso); if(!iso || isNaN(d.getTime()))return "";
    const now=new Date(), time=pad(d.getHours())+":"+pad(d.getMinutes());
    return d.toDateString()===now.toDateString() ? "今天 "+time : (d.getMonth()+1)+"月"+d.getDate()+"日 "+time;
  }
  function clock(iso) { const d=new Date(iso); return !iso || isNaN(d.getTime()) ? "" : pad(d.getHours())+":"+pad(d.getMinutes()); }
  function since(iso) { const t=new Date(iso).getTime(); return isNaN(t) ? null : Math.max(0,Math.floor((Date.now()-t)/1000)); }
  function duration(seconds, precise) {
    if(seconds==null)return "";
    const m=Math.floor(seconds/60), s=seconds%60;
    if(m>=60)return Math.floor(m/60)+" 小时 "+(m%60)+" 分";
    return precise ? (m?m+" 分 ":"")+pad(s)+" 秒" : (m?m+" 分":s+" 秒");
  }
  function ending(c) {
    if(!c)return "";
    const where=c.phase?"结束于「"+phaseName(c.phase)+"」":"";
    const why=c.reason?(words().endReasons?.[c.reason] || endReasons[c.reason] || c.reason):(c.exitCode!=null?"该阶段未通过（退出码 "+c.exitCode+"）":"");
    return [where,why].filter(Boolean).join("：");
  }
  function phaseName(key) { return words().phases?.[key]?.name || phaseLabels[key] || key; }
  function forkButton(parent, small) {
    const b=primary(button(parent,"以此草案新建任务",async()=>{await api("fork");tab="model";plan=null;await refresh();}));
    if(small)b.className+=" small"; return b;
  }

  // ---------------------------------------------------------------- formulas
  const TEMPLATE_TEX = {"poisson1d-v1":"-u''(x) = \\pi^2 \\sin(\\pi x)", "poisson2d-v1":"-(u_{xx} + u_{yy}) = 2\\pi^2 \\sin(\\pi x)\\sin(\\pi y)",
    "annulus-v1":"-(u_{xx} + u_{yy}) = f,\\quad u^* = (1-s)(s-a^2)\\,(1 + 0.2\\sin(\\pi x)\\cos(2\\pi y) + 0.1x - 0.1y)"};
  // The verified templates' reference and method in words; the draft keeps the exact identifiers.
  const METHOD_TEXT = {"poisson1d-v1":"参考解：精确解 sin(πx)；方法：硬边界 PINN，u = x(1−x)·N(x)，边界条件自然精确满足",
    "poisson2d-v1":"参考解：精确解 sin(πx)·sin(πy)；方法：硬边界 PINN，u = x(1−x)y(1−y)·N(x, y)",
    "annulus-v1":"参考解：制造解 u*（见控制方程），a = 0.35；方法：硬边界 PINN，u = (1−s)(s−a²)·N(x, y)，内外两圈上精确为 0"};
  const TEMPLATE_TEXT = {"poisson1d-v1":"−u″(x) = π² sin(πx)", "poisson2d-v1":"−(u_xx + u_yy) = 2π² sin(πx) sin(πy)",
    "annulus-v1":"−(u_xx + u_yy) = f，u* = (1−s)(s−a²)(1 + 0.2 sin(πx) cos(2πy) + 0.1x − 0.1y)"};
  // A person's ASCII equation, read conservatively; anything unusual keeps the original text.
  function asciiTex(s) {
    return String(s).replace(/\*\*/g,"^").replace(/u"|u''/g,"u''").replace(/\bu_([a-z]{1,3})\b/g,"u_{$1}")
      .replace(/\b(sin|cos|tan|exp|log|ln|sinh|cosh|tanh)\b/g,"\\$1").replace(/\bpi\b/g,"\\pi ").replace(/\^(\d+)/g,"^{$1}")
      .replace(/\*/g,"\\,");
  }
  function formula(parent, tex, fallback) {
    const math=window.LeoWorkbench.math;
    if(typeof math==="function" && tex){
      try{const node=math(tex,false);if(node && String(node.localName||node.tagName||"").toLowerCase()==="math"){const span=el("span",undefined,parent,"research-formula");span.append(node);return span;}}
      catch(_){/* shown as text below */}
    }
    return el("span",fallback,parent,"research-formula");
  }
  function equation(parent, d) {
    if(d.supported && TEMPLATE_TEX[d.templateId])return formula(parent,TEMPLATE_TEX[d.templateId],TEMPLATE_TEXT[d.templateId]);
    if(d.supported)return formula(parent,null,isAnnulus(d)?TEMPLATE_TEXT["annulus-v1"]:isTwoD(d)?TEMPLATE_TEXT["poisson2d-v1"]:TEMPLATE_TEXT["poisson1d-v1"]);
    return formula(parent,d.equation?asciiTex(d.equation):null,d.equation || "尚待补充");
  }

  // ---------------------------------------------------------------- service
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

  // ---------------------------------------------------------------- status bar
  /* Left: what the task is doing right now (never the result of the last click). Right: the last
     action's result or error, or a waiting message while one runs. */
  function stateLine() {
    if(!task)return "还没有选择任务";
    const s=task.state;
    if(s==="PREPARING")return "正在准备 · 已用 "+duration(since(task.preparationStartedAt || task.updatedAt),true);
    if(s==="RUNNING"){const p=view.progress;return "正在计算"+(p?.phase?" · "+phaseName(p.phase):"")+" · 已用 "+duration(since(task.runApproval?.at || task.updatedAt),true);}
    if(s==="CANCELLING")return "正在停止，已有记录会全部保留";
    if(s==="COMPLETED")return (view.verification?.verified?"已完成":"已完成，证据核验未通过")+" · "+when(task.updatedAt)+" 结束";
    if(RESTARTABLE.has(s))return (shortLabels[s] || s)+" · "+when(task.updatedAt)+" · 证据已原样保留";
    if(s==="READY_FOR_RUN_APPROVAL")return "确认包已就绪 · 等待你确认正式运行";
    if(s==="MODEL_CONFIRMED")return "模型已确认 · 尚未准备运行";
    return task.draft?"草案 · 还没有启动计算":"还没有草案 · 还没有启动计算";
  }
  function statusParts() { const bar=overlay?.querySelector(".leo-research-status"); return bar ? [bar.querySelector(".status-state"),bar.querySelector(".status-note")] : []; }
  function paintState() { const [state]=statusParts(); if(state){state.textContent=stateLine();state.dataset.busy=String(!!(task && BUSY.has(task.state)));} }
  function status(text, kind) { const [,note]=statusParts(); if(note){note.textContent=text || "";note.dataset.kind=kind || "";} }
  // A waiting text with "{s}" counts the seconds, so a long model call never looks frozen.
  async function action(fn, waiting, done) {
    if(busy)return; busy=true; overlay?.setAttribute("aria-busy","true");
    const text=waiting || "正在处理，请稍候。";
    const started=Date.now();const show=()=>status(text.replace("{s}",String(Math.floor((Date.now()-started)/1000))),"wait");
    show();const ticker=text.includes("{s}")?setInterval(show,1000):null;
    overlay?.querySelectorAll("button").forEach(b=>b.disabled=true);
    try { await fn(); status(done ? "✓ "+done+" · "+clock(new Date().toISOString()) : "", done?"ok":undefined); }
    catch(e){ status(e.message,"error"); }
    finally {if(ticker)clearInterval(ticker);busy=false; overlay?.removeAttribute("aria-busy");overlay?.querySelectorAll("button").forEach(b=>b.disabled=false);paintState();}
  }
  // Polling never touches the note: a background refresh is not something the person did.
  async function quietRefresh() {
    if(busy)return; busy=true;
    try { await refresh(); } catch(e){ status(e.message,"error"); } finally { busy=false; paintState(); }
  }
  const DRAFTING="正在生成问题草案：模型正在思考，已等待 {s} 秒（推理模型通常需要 30–90 秒，最长 3 分钟）。计算不会在确认前启动。";

  // ---------------------------------------------------------------- task list (A8)
  async function openTasks(parent, scope) {
    const r=await api("list",scope==="all"?{scope:"all"}:await association());
    parent.querySelector(".research-task-list")?.remove?.();
    const list=el("div",undefined,parent,"research-task-list");
    if(!r.tasks.length){paragraph(list,scope==="all"?"还没有任何科研任务。":"此会话尚无科研任务。","research-empty");return;}
    const head=el("div",undefined,list,"task-row task-head");
    for(const t of ["状态","问题","类型","更新","对话"])el("span",t,head);
    for(const item of r.tasks){
      const row=el("button",undefined,list,"task-row"); row.type="button"; row.dataset.taskId=item.taskId; row.dataset.label=labels[item.state] || item.state;
      row.setAttribute("aria-label",(shortLabels[item.state] || item.state)+" · "+item.prompt);
      const s=el("span",undefined,row); chip(s,shortLabels[item.state] || item.state,stateKind[item.state] || "plain");
      el("span",item.prompt,row,"task-prompt");
      el("span",familyNames[item.family] || (item.hasDraft===false?"尚无草案":"未匹配"),row,"task-meta");
      el("span",when(item.updatedAt),row,"task-meta");
      el("span",item.frameId===session().frameId?"本对话":"其他对话",row,"task-meta");
      row.onclick=()=>action(async()=>{task={taskId:item.taskId};await refresh();});
    }
  }

  // ---------------------------------------------------------------- draft display (A13, C8)
  /* 2.2.11 · Two verified templates: 1D (domain [a, b], boundary {left, right}) and 2D on a
     rectangle (domain [[x0, x1], [y0, y1]], boundary {left, right, bottom, top}). */
  function isTwoD(d){return d?.templateId==="poisson2d-v1" || (Array.isArray(d?.domain)&&Array.isArray(d.domain[0]))
    || !!(d?.boundary&&("bottom" in d.boundary || "top" in d.boundary));}
  function box2(d){return Array.isArray(d?.domain)&&Array.isArray(d.domain[0])&&Array.isArray(d.domain[1])?d.domain:null;}
  /* 3.2.2 · The annulus: domain {annulus: [a, R]}, boundary {inner, outer}. */
  function isAnnulus(d){return d?.templateId==="annulus-v1" || !!(d?.domain && !Array.isArray(d.domain) && typeof d.domain==="object" && "annulus" in d.domain)
    || !!(d?.boundary && ("inner" in d.boundary || "outer" in d.boundary));}
  function ring(d){const r=d?.domain?.annulus;return Array.isArray(r)&&r.length===2?r:null;}
  function shapeOf(d){return isAnnulus(d)?"annulus":isTwoD(d)?"2d":"1d";}
  function domainText(d){
    if(isAnnulus(d)){const r=ring(d);return r?`${r[0]} < r < ${r[1]}（r² = x² + y²，环形）`:"尚待补充";}
    const box=box2(d);if(box)return `${box[0][0]} < x < ${box[0][1]}，${box[1][0]} < y < ${box[1][1]}`;
    return Array.isArray(d.domain)&&!isTwoD(d)?`${d.domain[0]} < x < ${d.domain[1]}`:"尚待补充";
  }
  // One row per edge, so a condition never breaks at its "=".
  function boundaryRows(d){
    const b=d.boundary;if(!b)return [];
    if(isAnnulus(d)){const r=ring(d);return [["内圈"+(r?" r = "+r[0]:""),"u = "+(b.inner??"?")],["外圈"+(r?" r = "+r[1]:""),"u = "+(b.outer??"?")]];}
    if(isTwoD(d)){const box=box2(d);const at=(axis,i)=>box?axis+" = "+box[axis==="x"?0:1][i]:"";
      return [["left","左边",at("x",0)],["right","右边",at("x",1)],["bottom","下边",at("y",0)],["top","上边",at("y",1)]]
        .map(([k,name,where])=>[name+(where?" "+where:""),"u = "+(b[k]??"?")]);}
    return Array.isArray(d.domain)?[["左端 x = "+d.domain[0],"u = "+b.left],["右端 x = "+d.domain[1],"u = "+b.right]]:[];
  }

  // ---------------------------------------------------------------- editor (A15)
  // The editor keeps the draft's shape; the person can switch a draft between 1D and 2D before saving.
  function field(parent,label,value,multiline=false,cls) {
    const l=el("label",label,parent,cls), input=el(multiline?"textarea":"input",undefined,l);
    input.value=value || "";return input;
  }
  function draftEditor(parent,d,shape,onClose){
    const editor=el("section",undefined,parent,"research-editor");
    const text=v=>v==null?"":String(v);
    const draw=mode=>{
      const dim2=mode==="2d";
      editor.replaceChildren();
      const top=el("div",undefined,editor,"editor-top");el("h3","修改模型草案",top);
      const seg=el("div",undefined,top,"research-seg");seg.setAttribute("role","group");seg.setAttribute("aria-label","问题维度");
      for(const [key,label] of [["1d","一维"],["2d","二维"],["annulus","环形"]]){
        const b=el("button",label,seg,"seg-btn"+(key===mode?" is-on":""));b.type="button";b.setAttribute("aria-pressed",String(key===mode));
        b.onclick=()=>{if(key!==mode)draw(key);};
      }
      const objective=field(editor,"研究目标",d.objective);
      const eq=el("div",undefined,editor,"editor-equation");
      const equationInput=field(eq,"方程",d.equation);
      const preview=el("p",undefined,eq,"editor-preview");
      const showPreview=()=>{preview.replaceChildren();el("span","预览：",preview);formula(preview,asciiTex(equationInput.value),equationInput.value);};
      equationInput.oninput=showPreview;showPreview();
      const box=box2(d), line=Array.isArray(d.domain)&&!box?d.domain:null, b=d.boundary||{};
      const grid=el("div",undefined,editor,"editor-grid");
      const domain=el("div",undefined,grid,"editor-domain");el("h4","求解区域",domain);
      const bound=el("div",undefined,grid,"editor-boundary");el("h4","边界值（u 在边上的值）",bound);
      const range=(label,lo,hi)=>{const r=el("div",undefined,domain,"editor-range");
        const a=field(r,label+" 下限",lo,false,"compact");el("span","< "+label+" <",r,"range-sep");const z=field(r,label+" 上限",hi,false,"compact");return [a,z];};
      let numbers;
      if(mode==="annulus"){
        const r=ring(d);
        const rr=el("div",undefined,domain,"editor-range");
        const a=field(rr,"内半径",text(r?.[0]),false,"compact");el("span","< r <",rr,"range-sep");const R=field(rr,"外半径",text(r?.[1]),false,"compact");
        const rings=el("div",undefined,bound,"boundary-line");
        const inner=field(rings,"内圈",text(b.inner),false,"compact");el("span",undefined,rings,"ring-shape");const outer=field(rings,"外圈",text(b.outer),false,"compact");
        numbers={a,R,inner,outer};
      } else if(dim2){
        const [x0,x1]=range("x",text(box?.[0]?.[0]??line?.[0]),text(box?.[0]?.[1]??line?.[1]));
        const [y0,y1]=range("y",text(box?.[1]?.[0]),text(box?.[1]?.[1]));
        const square=el("div",undefined,bound,"boundary-square");
        const top_=field(square,"上边",text(b.top),false,"compact edge-top"), left=field(square,"左边",text(b.left),false,"compact edge-left");
        el("span",undefined,square,"square-shape");
        const right=field(square,"右边",text(b.right),false,"compact edge-right"), bottom=field(square,"下边",text(b.bottom),false,"compact edge-bottom");
        numbers={x0,x1,y0,y1,left,right,bottom,top:top_};
      } else {
        const [a,z]=range("x",text(line?.[0]??box?.[0]?.[0]),text(line?.[1]??box?.[0]?.[1]));
        const ends=el("div",undefined,bound,"boundary-line");
        const left=field(ends,"左端",text(b.left),false,"compact"); el("span",undefined,ends,"line-shape"); const right=field(ends,"右端",text(b.right),false,"compact");
        numbers={a,b:z,left,right};
      }
      const missing=field(editor,"尚缺信息（每行一项）",d.missing.join("\n"),true), conflicts=field(editor,"冲突（每行一项）",d.conflicts.join("\n"),true);
      const foot=el("div",undefined,editor,"research-footer");
      el("span",task?.state==="MODEL_CONFIRMED"?"保存后会撤销原来的模型确认，需要重新确认。":"保存后需要确认模型。",foot,"footer-note");
      quiet(button(foot,"取消",async()=>{editor.remove?.();onClose?.();}));
      primary(button(foot,"保存修改",async()=>{
        const bad=Object.values(numbers).filter(x=>!x.value.trim() || !Number.isFinite(Number(x.value)));
        for(const x of Object.values(numbers))x.setAttribute("aria-invalid",String(bad.includes(x)));
        if(bad.length)throw new Error("请填写有效数值。");
        const n=k=>Number(numbers[k].value), lines=x=>x.value.split("\n").map(s=>s.trim()).filter(Boolean);
        const shape=mode==="annulus"?{domain:{annulus:[n("a"),n("R")]},boundary:{inner:n("inner"),outer:n("outer")}}
          :dim2?{domain:[[n("x0"),n("x1")],[n("y0"),n("y1")]],boundary:{left:n("left"),right:n("right"),bottom:n("bottom"),top:n("top")}}
          :{domain:[n("a"),n("b")],boundary:{left:n("left"),right:n("right")}};
        await api("update",{draft:{objective:objective.value,equation:equationInput.value,...shape,
          assumptions:d.assumptions,missing:lines(missing),conflicts:lines(conflicts)}});
        await refresh();
      },undefined,"已保存修改"));
    };
    draw(shape);return editor;
  }

  // ---------------------------------------------------------------- verification (B1, C1, C3)
  function claimHeadline(top) {
    return {C3:"可以声明：这是一个可推广的结论",C2:"可以声明：在这道题上，精度达到了事先约定的要求",
      C1:"只能说明训练收敛，还不能声明精度",C0:"只能说明代码能正确运行，还不能声明精度"}[top] || "只允许探索性描述";
  }
  function ladder(parent, v) {
    const allowed=new Set(v.allowedClaims || []), steps=words().claimLadder || [];
    if(!steps.length)return;
    subheading(parent,"结论等级","从低到高，每一级都要求前一级成立");
    const grid=el("div",undefined,parent,"research-ladder");
    const top=[...allowed].sort().pop();
    for(const s of steps){
      const reached=allowed.has(s.level), c=card(grid,"ladder-step"+(reached?" is-reached":"")+(s.level===top?" is-top":""));
      const head=el("div",undefined,c,"ladder-head");tick(head,reached?"ok":"no");el("b",s.name,head);
      const blocked=(v.blockedClaims || []).find(b=>b.level===s.level);
      el("p",s.level===top?s.text+" · 本次到达":reached?s.text:(blocked?.plain || s.text),c);
      raw(c,s.level);
    }
  }
  function dimensionCards(parent, vector, failedDimension) {
    const known=words().dimensions?.length ? words().dimensions : dimensionFallback.map(([key,name,gate])=>({key,name,gate,text:""}));
    subheading(parent,"六项检查","按执行顺序");
    const grid=el("div",undefined,parent,"research-dimensions");
    for(const d of known){
      if(!(d.key in vector))continue;
      const value=vector[d.key], status=(typeof value==="string"?value:value?.status) || "NOT_CHECKED";
      const kind=status==="PASS"?"verified":status==="FAIL"?"failed":"blocked";
      const c=card(grid,"dimension-card dimension-"+kind);
      const head=el("div",undefined,c,"dimension-head");el("b",d.name,head);
      chip(head,(words().status || statusLabels)[status] || status,kind);
      el("p",d.key===failedDimension && view.verification?.story?.criteria?.length ? storyCriteria(view.verification.story) : d.text,c);
      raw(c,d.gate+" · "+d.key);
    }
    return grid;
  }
  function storyCriteria(story) {
    return story.criteria.map(c=>`${c.total} 个种子里有 ${c.seeds} 个没有满足「${c.name}」`).join("；")+"。";
  }
  function verdictCard(parent, kind, eyebrow, headline, text) {
    const c=el("section",undefined,parent,"research-verdict verdict-"+kind);
    // "1 × 10⁻³" must never break across lines (A13): the spaces around × become non-breaking.
    const keep=t=>String(t).replace(/ × /g,"\u00a0×\u00a0");
    el("p",eyebrow,c,"verdict-label"); el("h3",keep(headline),c); if(text)paragraph(c,keep(text)); return c;
  }
  function verificationView(body) {
    const v=view.verification || {verified:false,allowedClaims:[]}, allowed=v.allowedClaims || [];
    const story=v.story, failure=v.failure;
    if(v.verified && allowed.length){
      const top=[...allowed].sort().pop();
      verdictCard(body,"claim","结论",claimHeadline(top),view.guide?.subline || "证据核验已通过当前记录。");
      ladder(body,v);
    } else if(story){
      verdictCard(body,"blocked","结论","不下结论：这次运行没有通过全部检查","失败本身也是结果，所有记录都原样保留，可以核对。");
    } else {
      const reason=v.reason && (labels[v.reason] || reasonLabels[v.reason] || (/^No current claim decision/.test(v.reason)?"没有当前结论判定，不允许精度声明。":v.reason));
      verdictCard(body,v.verified?"exploratory":"blocked","结论",v.verified?"只允许探索性描述":"尚不可下结论",
        (v.verified?"证据核验已通过当前记录。":"证据核验尚未通过。")+(reason?"当前状态："+reason:""));
    }
    const vector=v.dimensions || failure?.trustVector;
    const failedDimension=failure?.gate!=null ? {1:"math",3:"impl",4:"train",5:"external",6:"repro"}[failure.gate] : null;
    if(vector)dimensionCards(body,vector,failedDimension);
    if(story){
      const grid=el("div",undefined,body,"research-story");
      for(const [title,text] of [["发生了什么",story.happened],["这意味着什么",story.means],["你可以做什么",story.next]]){
        const c=card(grid);el("h4",title,c);paragraph(c,text);
        if(title==="你可以做什么" && RESTARTABLE.has(task.state))forkButton(c,true);
      }
      if(story.facts?.length){
        const more=details(body,"原始记录（给想深入的人）");
        const list=el("ul",undefined,more,"research-facts");
        for(const f of story.facts){const li=el("li",f.plain,list);raw(li,f.raw);}
      }
    } else if(failure){
      // An older service without story words still shows what the run recorded.
      subheading(body,"这次运行记录下的结果");
      const list=el("ul",undefined,body,"research-facts");
      if(failure.completion)el("li",ending(failure.completion),list);
      if(failure.gate!=null){const li=el("li","未通过的检查：第 "+failure.gate+" 关",list);raw(li,"Gate "+failure.gate);}
      for(const s of failure.observedSignatures || []){const li=el("li","观察到的问题："+(words().signatures?.[s] || s),list);raw(li,s);}
      if(failure.finalState){const li=el("li","记录状态："+(words().finalStates?.[failure.finalState] || failure.finalState),list);raw(li,failure.finalState);}
    }
    if(v.blockedClaims?.length && !(v.verified && allowed.length)){
      subheading(body,"被阻断的结论");
      for(const c of v.blockedClaims){const row=el("p",undefined,body,"research-blocked");chip(row,"更高一级结论暂不允许","blocked");
        el("span",c.plain || c.reason || "",row);raw(row,c.level+(c.reason?" · "+c.reason:""));}
    }
    if(v.verified){
      subheading(body,"你的科学解释与适用边界");
      const interpretation=el("textarea",undefined,el("label",undefined,body,"research-review"));
      interpretation.value=task.humanReview?.interpretation || "";
      interpretation.placeholder="例如：只说明这一个问题、这组边界条件下的精度，不推广到其他方程……";
      const row=el("div",undefined,body,"research-actions");
      primary(button(row,"确认已审阅结论",async()=>{await api("review",{interpretation:interpretation.value});await refresh();},undefined,"已保存你的审阅"));
      el("span","你的解释会随结论一起保存，但不能提高机器允许的等级。",row,"research-note");
    }
    paragraph(body,"过程完成、测试通过与科学结论成立分别记录。人工解释不能提升机器允许的结论等级。","research-footnote");
  }

  // ---------------------------------------------------------------- evidence (guide)
  function layer(parent, text) { el("p",text,parent,"guide-layer"); }
  // The reader's view of a verified run: conclusion first, then the checks in mathematical terms,
  // then why the records count as evidence. Every number comes from the run's records.
  function guideView(body, g) {
    verdictCard(body,"claim","一句话结论",g.headline,g.subline).className+=" guide-verdict";
    layer(body,"第一层 · 一页看懂");
    const nums=el("div",undefined,body,"guide-nums");
    for(const n of g.numbers){const c=el("div",undefined,nums,"guide-num");el("small",n.label,c);el("b",n.value,c);paragraph(c,n.text);}
    const say=el("div",undefined,body,"guide-say");
    for(const [kind,title,items] of [["can","可以这样说",g.can],["cannot","不能这样说",g.cannot]]){
      const box=el("div",undefined,say,"guide-"+kind);el("h4",title,box);
      const list=el("ul",undefined,box);(items.length?items:["—"]).forEach(x=>el("li",x,list));
    }
    layer(body,"第二层 · 用数学语言看六项检查");
    for(const d of g.dimensions){
      const row=el("details",undefined,body,"guide-dim");const head=el("summary",undefined,row);
      const name=el("span",undefined,head,"guide-dim-name");el("strong",d.name,name);
      el("small",d.short+" · "+(statusLabels[d.status] || d.status),name);
      el("span",d.text,head,"guide-dim-text");
      const checks=el("ul",undefined,row);
      for(const c of d.checks){const li=el("li",c.plain+"："+(statusLabels[c.status] || c.status),checks);if(c.reason)raw(li,c.reason);}
    }
    layer(body,"第三层 · 凭什么说这是证据");
    const chain=el("ol",undefined,body,"guide-chain");
    for(const s of g.chain){const li=el("li",undefined,chain);el("strong",s.title,li);paragraph(li,s.text);el("span",s.proof,li,"guide-proof");}
    const actions=el("div",undefined,body,"guide-actions");
    const result=el("section",undefined,body,"guide-check");result.hidden=true;
    primary(button(actions,"一键重新核对",async()=>{
      const r=await api("recheck");result.hidden=false;result.replaceChildren();
      el("h4","重新核对",result);paragraph(result,"在你的电脑上逐项重算，不依赖原来的核验结果。");
      const list=el("ol",undefined,result);
      for(const s of r.steps){const li=el("li",undefined,list,s.passed?"ok":"bad");el("span",s.passed?"✓":"✗",li,"mark");
        el("span",s.label+(s.detail?"（"+s.detail+"）":""),li);el("small",s.seconds+" 秒",li);}
      paragraph(result,r.passed?"核对通过：这份证据与原始计算记录一致，结论可以引用。":"核对未通过：请不要引用这份结论，并保留证据以便排查。",r.passed?"guide-pass":"guide-fail");
      result.scrollIntoView?.({block:"nearest"});
    },"正在重新核对：逐项重算指纹并复核结论，约需 10 秒。","重新核对完成"));
    secondary(button(actions,"导出证据包（含证据说明书）",async()=>{const r=await api("export");paragraph(body,"已导出并校验："+r.path+"。包内的「证据说明书.html」可直接用浏览器打开。","research-done");},
      "正在导出：完整核验证据并生成证据说明书，约需 10 秒。","已导出证据包"));
    el("span","不必逐个阅读文件：重新核对会逐项重算指纹并复核结论。",actions,"guide-note");
    const glossary=details(body,"术语表");glossary.className+=" guide-more";
    const gl=el("dl",undefined,glossary);for(const [term,text] of g.glossary){el("dt",term,gl);el("dd",text,gl);}
    const map=details(body,"给想深入的读者：证据地图（每个文件是什么）");map.className+=" guide-more";
    const ml=el("dl",undefined,map);for(const [file,text] of g.map){el("dt",file,ml);el("dd",text,ml);}
    rawFiles(map);
  }
  function rawFiles(parent) {
    const row=el("div",undefined,parent,"research-actions");
    secondary(button(row,"列出全部证据文件",async()=>{const r=await api("evidence");parent.querySelector(".research-files")?.remove?.();
      const list=el("div",undefined,parent,"research-files");
      for(const file of r.files){const b=el("button",file,list,"file-row");b.type="button";b.onclick=()=>action(async()=>{const result=await api("evidence",{path:file});
        let preview=parent.querySelector("pre");if(!preview)preview=el("pre",undefined,parent);preview.textContent=result.text;});}}));
    return row;
  }

  // ---------------------------------------------------------------- run tab (C5, C7, C4, C1)
  function quotaCard(body, q) {
    const c=card(body,"research-quota");
    const n=el("div",undefined,c,"quota-number");
    const big=el("p",undefined,n,"quota-big");el("span",String(q.remaining),big);el("small"," / "+q.capacity,big);
    el("p",(familyNames[q.family] || "一维")+"盲测集剩余",n,"quota-caption");
    const right=el("div",undefined,c,"quota-body");
    const squares=el("div",undefined,right,"quota-squares");squares.setAttribute("aria-hidden","true");
    const used=q.capacity-q.remaining;
    for(let i=0;i<q.capacity;i++)el("i",undefined,squares,i<used?"is-used":i===used?"is-next":"");
    paragraph(right,`准备会永久占用本机 1 个${familyNames[q.family] || "一维"}盲测集（剩余 ${q.remaining} / ${q.capacity}；一维、二维、环形各自分开计数）。之后无论准备或运行成败都不退还——这是防止反复试到「碰巧通过」的规则。`);
  }
  function preparingCard(body) {
    const c=card(body,"research-progress");
    const head=el("div",undefined,c,"progress-head");el("b","正在准备运行确认包",head);
    const limit=view.prepareLimitMinutes || 5;
    el("span","已用 "+duration(since(task.preparationStartedAt || task.updatedAt),true)+" / 最长 "+limit+" 分钟",head,"progress-time");
    const steps=words().preparationSteps || [];
    const current=view.preparationProgress?.step, index=steps.findIndex(s=>s.key===current);
    const list=el("ul",undefined,c,"research-timeline");
    steps.forEach((s,i)=>{const li=el("li",undefined,list,i<index?"is-done":i===index?"is-current":"is-waiting");
      tick(li,i<index?"ok":i===index?"run":"wait");el("b",s.name,li);el("span","— "+s.text,li,"step-text");});
    paragraph(c,`正在准备运行确认包：核对代码身份，检查两个科学环境，并预留盲测集。最长约 ${limit} 分钟，不会启动训练；完成后需要你亲自确认正式运行才会计算。可以关闭本面板，稍后回来查看。`,"research-note");
  }
  function runningCard(body) {
    const phases=plan?.phases || ["main","tier1","reproduction","g6"], p=view.progress || {};
    const history=p.phases || (p.phase?[{phase:p.phase,startedAt:p.at}]:[]);
    const index=Math.max(0,phases.indexOf(p.phase));
    const elapsed=since(task.runApproval?.at || history[0]?.startedAt || task.updatedAt);
    const c=card(body,"research-progress");
    const head=el("div",undefined,c,"progress-head");
    el("b",(task.state==="CANCELLING"?"正在停止":"正在计算")+" · 第 "+(index+1)+" 阶段，共 "+phases.length+" 阶段",head);
    const limit=plan?.budgetSeconds?Math.round(plan.budgetSeconds/60):null;
    el("span",["已用 "+duration(elapsed),view.estimateMinutes?"预计约 "+view.estimateMinutes+" 分":"",limit?"上限 "+limit+" 分":""].filter(Boolean).join(" · "),head,"progress-time");
    const bar=el("div",undefined,c,"research-bar");const fill=el("i",undefined,bar);
    const fraction=view.estimateMinutes&&elapsed!=null?Math.min(.95,elapsed/(view.estimateMinutes*60)):(index+.5)/phases.length;
    fill.style.width=Math.round(fraction*100)+"%";
    const steps=el("ol",undefined,c,"research-steps");
    phases.forEach((name,i)=>{
      const li=el("li",undefined,steps,i<index?"is-done":i===index?"is-current":"is-waiting");
      tick(li,i<index?"ok":i===index?"run":"wait");el("b",phaseName(name),li);
      const start=history.find(h=>h.phase===name)?.startedAt, next=history.find(h=>h.phase===phases[i+1])?.startedAt;
      el("span",i<index?clock(start)+(next?" – "+clock(next):""):i===index?"进行中 · "+duration(since(start)):"等待",li,"step-time");
      raw(li,phaseRaw[name] || name);
    });
    const text=words().phases?.[phases[index]]?.text;
    if(text)paragraph(c,phaseName(phases[index])+"："+text.replace("{runs}",String(plan?.seedProtocol?.runs || 10)),"research-note");
  }
  function planSummary(body) {
    const c=card(body,"research-plan");
    // Before the run it says what will happen; afterwards what did, with each phase's start time when recorded.
    const done=!["READY_FOR_RUN_APPROVAL","MODEL_CONFIRMED","PREPARING"].includes(task.state);
    const started=Object.fromEntries(((view.progress||{}).phases||[]).map(p=>[p.phase,p.startedAt]));
    el("h4",done?"这次做了什么":"这次会做什么",c);
    const list=el("ol",undefined,c);
    for(const name of plan.phases || []){const li=el("li",undefined,list);el("b",phaseName(name),li);
      const text=words().phases?.[name]?.text;if(text)el("span","："+text.replace("{runs}",String(plan.seedProtocol?.runs || 10)),li);
      if(done && started[name])el("span","（"+when(started[name])+" 开始）",li,"research-note");}
    const limit=Math.round(plan.budgetSeconds/60);
    const family=familyNames[plan.family] || "";
    const meta=el("p",undefined,c,"research-note");
    const ended=done && task.completion?.at ? "，"+when(task.completion.at)+" 结束" : "";
    el("span",done?`运行确认 ${when(task.runApproval?.at) || "—"}${ended} · 用掉 1 个${family}盲测集`
      :(view.estimateMinutes?`预计约 ${view.estimateMinutes} 分钟，`:"")+`上限 ${limit} 分钟 · 已预留 1 个${family}盲测集`,meta);raw(meta,plan.claimMember);
    const who=details(body,`身份与环境（问题规格 ${short(plan.specHash) || "—"} · 代码 ${short(plan.codeHash) || "—"} · 环境 A / B）`);
    const rows=[];
    for(const [key,label] of [["specHash","问题规格指纹"],["codeHash","代码指纹"],["claimMember","盲测集编号"],["claimSampleSetHash","盲测样本指纹"],
      ["seedProtocol","种子方案"],["reproductionSeedOffset","复现种子偏移"],["parallelWorkers","并行训练进程"],["environmentA","环境 A（计算）"],["environmentB","环境 B（复现）"],["expectedTolerance","复现容差"]]){
      if(plan[key]==null)continue;rows.push([label,describe(key,plan[key])]);
    }
    kv(who,rows);
    const all=details(body,"完整运行确认包（原始 JSON）");el("pre",JSON.stringify(plan,null,2),all);
  }
  // Plan values are read by people here; the exact document stays in the full package below.
  function describe(key, value) {
    if(value && typeof value==="object") {
      if(key==="seedProtocol" && "runs" in value)
        return `${value.runs} 组种子 · 初始化 ${value.initBase}+i · 采样 ${value.sampleBase}+i · 批次 ${value.batchBase}+i`;
      if(key==="expectedTolerance" && "devRelL2MedianAbsDiff" in value)
        return `两次开发集误差中位数相差 ≤ ${value.devRelL2MedianAbsDiff}`+(value.devRelL2MedianRelDiff!=null?`，且 ≤ 原中位数的 ${value.devRelL2MedianRelDiff} 倍`:"")
          +(value.seedProtocolVerdictMustAgree?"；种子判定必须一致":"");
      if(/^environment/.test(key) && ("frameworkVersion" in value || "osFamily" in value))
        return [value.osFamily,value.frameworkVersion,value.blasBackend,value.acceleratorClass,short(value.installationId)].filter(Boolean).join(" · ");
      return Object.entries(value).map(([k,v])=>k+"："+(v && typeof v==="object"?JSON.stringify(v):v)).join(" · ");
    }
    return typeof value==="string" && /^[0-9a-f]{40,}$/.test(value) ? short(value)+"…" : String(value);
  }
  function runView(body) {
    if(task.state==="MODEL_CONFIRMED" && view.canPrepare){
      const q=view.quota;
      // Preparing reserves a blind claim grid for good; say so, and how many remain, before the click.
      if(q && q.remaining<=0)paragraph(body,errors.NO_FRESH_DISJOINT_CLAIM_SET,"research-hint");
      else {
        if(q)quotaCard(body,q);
        const row=el("div",undefined,body,"research-actions");
        primary(button(row,"准备运行确认包（用掉 1 个）",async()=>{await api("prepare");await refresh();},undefined,"已开始准备"));
      }
    }
    if(task.state==="PREPARING")preparingCard(body);
    if(["RUNNING","CANCELLING"].includes(task.state)){
      runningCard(body);
      const row=el("div",undefined,body,"research-actions");
      if(task.state==="RUNNING")dangerOutline(button(row,"停止计算并保留证据",async()=>{await api("cancel");await refresh();},undefined,"已请求停止"));
      el("span","停止后已有的记录全部保留，但本次不会得出结论。",row,"research-note");
    }
    if(task.state==="READY_FOR_RUN_APPROVAL" && plan)planSummary(body);
    else if(plan)planSummary(details(body,"运行确认包"));
    if(task.state==="READY_FOR_RUN_APPROVAL"){
      if(task.runBlocked){paragraph(body,errors[task.runBlocked.reason] || task.runBlocked.reason,"research-hint");forkButton(el("div",undefined,body,"research-actions"));}
      else {
        const row=el("div",undefined,body,"research-actions");
        keyButton(row,"审阅并确认正式运行",["会弹出原生确认框",view.estimateMinutes?"预计约 "+view.estimateMinutes+" 分钟":"","只有你本人能点"].filter(Boolean).join(" · "),
          async()=>{await api("approve_run");await refresh();},undefined);
      }
    }
    if(task.preparationError){
      paragraph(body,errors[task.preparationError] || "准备失败。请检查运行环境和准备日志；没有启动正式训练。","research-hint");
      forkButton(el("div",undefined,body,"research-actions"));
    }
    if(RESTARTABLE.has(task.state)){
      const why=ending(task.completion);
      paragraph(body,"这次计算已结束（"+(labels[task.state] || task.state)+"）"+(why?"，"+why:"")+"。证据原样保留，可在「验证与结论」和「证据」中查看。若要重新尝试，请以此草案新建任务。");
      forkButton(el("div",undefined,body,"research-actions"));
    }
    if(task.state==="COMPLETED")paragraph(body,"计算流程已结束（"+when(task.updatedAt)+"）。结论见「验证与结论」，证据见「证据」。");
  }

  // ---------------------------------------------------------------- model tab (C6, A13)
  function lockBanner(body) {
    const a=task.modelApproval;if(!a)return;
    const locked=LOCKED.has(task.state);
    const box=info(body);box.className+=locked?" is-locked":"";
    el("span",locked?"🔒":"✓",box,"info-icon");
    const text=el("span",undefined,box,"info-text");
    el("b",locked?"模型已确认并锁定":"模型已确认",text);
    el("span"," · "+when(a.at)+" 由你在本机确认。"+(locked?"已经准备了运行确认包，模型不能再改；要改请以此草案新建任务。":"准备运行确认包之前还可以修改，修改会撤销这次确认。"),text);
    raw(text,"内容指纹 "+short(a.contentHash));
    if(locked && !BUSY.has(task.state))secondary(button(box,"以此草案新建任务",async()=>{await api("fork");tab="model";plan=null;await refresh();}));
  }
  function modelView(body) {
    if(!task.draft) {
      const failed=task.draftError;
      if(failed)hint(body,"上一次生成草案没有成功（等待了 "+failed.seconds+" 秒）："+(errors[failed.code] || failed.code+"。任务已保留，可以重试。"));
      else paragraph(body,"使用当前会话绑定的模型整理问题；生成草案不会执行代码。");
      primary(button(body,failed?"重新生成草案":"生成问题草案",async()=>{try{await api("draft");}finally{await refresh();}},DRAFTING)); return;
    }
    const d=task.draft, twoD=isTwoD(d), annulus=isAnnulus(d);
    lockBanner(body);
    const objective=el("section",undefined,body,"research-section");
    el("h3","研究目标",objective);paragraph(objective,d.objective);
    const grid=el("div",undefined,body,"research-model-grid");
    const small=(label,text)=>{const c=card(grid,"research-model-card");el("h3",label,c);paragraph(c,text);return c;};
    small("问题类型",d.supported?(annulus?"环形域 Poisson · 已验证模板":twoD?"二维 Poisson · 已验证模板":"一维 Poisson · 已验证模板")
      :(annulus?"环形问题 · 未匹配已验证模板":twoD?"二维问题 · 未匹配已验证模板":"未匹配已验证模板"));
    small("参考与方法",METHOD_TEXT[d.templateId] || (d.template?`参考解 ${d.template.reference}；方法 ${d.template.solver}`:"尚未选择已验证求解方案"));
    const eq=card(grid,"research-model-card is-wide");el("h3","控制方程",eq);const line=el("p",undefined,eq,"model-equation");equation(line,d);
    paragraph(eq,"区域 "+domainText(d),"research-note");
    const bc=card(grid,"research-model-card is-wide");el("h3","边界条件",bc);
    const rows=boundaryRows(d);if(rows.length)kv(bc,rows);else paragraph(bc,"尚待补充");
    subheading(body,"假设与待补信息");
    const list=el("ul",undefined,body,"research-list");
    d.assumptions.forEach(a=>el("li",`${a.source==="USER"?"用户提供":"模板建议"}：${a.text}${a.quote?"（"+a.quote+"）":""}`,list));
    [...d.missing.map(x=>"缺失："+x),...d.conflicts.map(x=>"冲突："+x)].forEach(x=>el("li",x,list));
    if(!list.children.length)el("li","没有。",list);
    if(d.template?.method){
      subheading(body,"方法与验收规则","已验证模板，确认模型即一并确认");
      const method=el("dl",undefined,body,"research-method");
      for(const [key,label] of methodLabels){ if(d.template.method[key]){el("dt",label,method);el("dd",d.template.method[key],method);} }
    }
    paragraph(body,d.supportMessage,"research-note");
    if(!d.supported && d.unsupportedReasons?.length){
      // Say which field misses the verified template, so the person can fix it instead of starting over.
      const why=el("section",undefined,body,"research-hint guide-why");
      el("strong","为什么暂不能准备运行",why);const reasons=el("ul",undefined,why);d.unsupportedReasons.forEach(r=>el("li",r,reasons));
      if(task.state==="DRAFT")paragraph(why,"可以点「修改模型草案」直接改正，不需要重新生成，也不占用盲测集。");
    }
    if(task.forkedFrom)paragraph(body,"本任务由 "+task.forkedFrom.taskId+" 的草案新建；原任务及其数据保持不变。","research-note");
    const row=el("div",undefined,body,"research-actions");
    if(task.state==="DRAFT" || task.state==="MODEL_CONFIRMED") {
      let editor=null;
      secondary(button(row,"修改模型草案",async()=>{if(!editor)editor=draftEditor(body,d,shapeOf(d),()=>{editor=null;});editor.scrollIntoView?.({block:"start"});}));
    }
    if(task.state==="DRAFT" && d.supported)
      keyButton(row,"审阅并确认模型","会弹出原生确认框 · 确认后才能准备运行，不会开始计算",async()=>{await api("approve_model");await refresh();});
  }

  // ---------------------------------------------------------------- render
  function titleText() {
    if(!task)return "科研任务 · 创建任务";
    if(task.state==="COMPLETED")return "科研任务 · "+(view.verification?.verified?"已完成，结论可引用":"已完成，证据核验未通过");
    if(task.state==="STOPPED")return "科研任务 · 未通过，不下结论";
    return "科研任务 · "+(labels[task.state] || task.state);
  }
  function close(){clearInterval(polling);overlay?.remove();backdrop?.remove();overlay=null;backdrop=null;}
  async function refresh(){if(!task)return; const r=await api("get");render(r);}
  function render(next) {
    if(next)view=next;
    if(!overlay)return;
    // Without a task there is only the create page; the step tabs must not claim otherwise.
    if(!task)tab="model";
    const body=overlay.querySelector(".leo-research-body"); body.replaceChildren();
    overlay.querySelectorAll("nav button[data-tab]").forEach(b=>{
      if(b.dataset.tab===tab)b.setAttribute("aria-current","step");else b.removeAttribute("aria-current");
    });
    overlay.querySelector(".leo-research-title").textContent=titleText();
    paintState();
    if(!task) {
      view={};
      paragraph(body,"支持三个已验证模板：一维 Poisson、单位正方形上的二维 Poisson、环形域 Poisson（由草案自动识别）。其他问题可以整理为草案，暂不能启动正式求解。","research-prompt");
      const prompt=field(body,"研究问题", "",true);prompt.placeholder="请描述方程、区域、边界条件和你希望验证的命题。";
      const row=el("div",undefined,body,"research-actions");
      primary(button(row,"创建任务并生成草案",async()=>{
        await api("create",{...await association(),prompt:prompt.value});
        try { await api("draft"); } finally { await refresh(); }
      },DRAFTING));
      secondary(button(row,"查看本会话的科研任务",async()=>openTasks(body,"frame")));
      secondary(button(row,"查看全部科研任务",async()=>openTasks(body,"all")));
      return;
    }
    paragraph(body,task.prompt,"research-prompt");
    if(task.state==="DRAFT") {
      if(tab!=="model"){hint(body,task.draft ? "下一步：在「问题与模型」核对草案并确认模型；现在还没有启动计算。" : "下一步：生成问题草案，核对后确认模型；现在还没有启动计算。");
        secondary(button(el("div",undefined,body,"research-actions"),"前往问题与模型",async()=>{tab="model";await refresh();}));}
    } else if(["MODEL_CONFIRMED","PREPARING"].includes(task.state) && tab!=="run") {
      secondary(button(el("div",undefined,body,"research-actions"),"前往准备运行确认包",async()=>{tab="run";await refresh();}));
    } else if(task.state==="READY_FOR_RUN_APPROVAL" && tab!=="run") {
      secondary(button(el("div",undefined,body,"research-actions"),"前往审阅运行确认包",async()=>{tab="run";await refresh();}));
    }
    if(tab==="model")modelView(body);
    else if(tab==="run")runView(body);
    else if(tab==="verification")verificationView(body);
    else if(view.guide)guideView(body,view.guide);
    else {
      if(task.state==="COMPLETED" && view.verification && !view.verification.verified)
        hint(body,"证据核验没有通过，不生成证据说明书；原始文件仍原样保留在下面。");
      if(view.verification?.story){
        const c=card(body,"research-summary");el("h4","这次运行没有得出结论",c);paragraph(c,view.verification.story.happened);
        secondary(button(c,"查看原因与下一步",async()=>{tab="verification";await refresh();}));
      }
      const row=rawFiles(body);
      secondary(button(row,"导出审计与复现资料",async()=>{const r=await api("export");paragraph(body,"已导出并校验："+r.path,"research-done");},undefined,"已导出"));
    }
  }
  function open() {
    if(overlay)return;
    if(frameContext!==session().frameId){task=null;plan=null;view={};tab="model";frameContext=session().frameId;}
    // The whole window dims and stops taking clicks while the panel is open (D1).
    backdrop=el("div",undefined,document.body,"leo-research-backdrop");
    overlay=el("section",undefined,document.body,"leo-research-overlay");overlay.setAttribute("role","dialog");overlay.setAttribute("aria-modal","true");overlay.setAttribute("aria-label","科研任务");
    const header=el("header",undefined,overlay);el("h2","科研任务",header,"leo-research-title");
    const exit=secondary(el("button","关闭",header));exit.type="button";exit.onclick=close;
    const nav=el("nav",undefined,overlay);
    for(const [key,label]of [["model","问题与模型"],["run","运行"],["verification","验证与结论"],["evidence","证据"]]){
      const b=button(nav,label,async()=>{tab=key;await refresh();if(!task)render();});b.dataset.tab=key;
    }
    secondary(button(nav,"新建任务",async()=>{task=null;plan=null;view={};tab="model";render();}));
    el("main",undefined,overlay,"leo-research-body");
    const live=el("div",undefined,overlay,"leo-research-status");live.setAttribute("role","status");
    el("span","",live,"status-state");el("span","",live,"status-note");
    render();if(task)quietRefresh();
    polling=setInterval(()=>{if(task && BUSY.has(task.state))quietRefresh();},3000);
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
