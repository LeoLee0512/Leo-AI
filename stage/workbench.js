/* Leo owns this document. All content from models is rendered as text. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = {projects:[],frames:[],project:null,frame:null,binding:null,messages:[],before:null,cursor:null,execution:null,loading:false,sending:false,epoch:0,feedback:{}};
  let poll, openedAt=0, started=false, hiddenIds=new Set(), shellState;
  const drafts=new Map();
  function keepDraft(){if(state.frame)drafts.set(state.frame.id,$('message-input').value);}
  const errorText={WORKBENCH_UNAVAILABLE:'暂时无法连接工作区。请返回开始页重新连接；未发送的内容仍保留在输入框中。',WORKBENCH_CONFLICT:'当前会话正在执行其他操作，请等待完成后重试。',WORKBENCH_REQUEST_FAILED:'工作区请求未完成，请稍后重试。',WORKBENCH_NOT_FOUND:'这个文件不属于当前对话，无法预览。',WORKBENCH_RESPONSE_INVALID:'工作区返回的内容无法识别，请稍后重试。',MODEL_BINDING_CONFLICT:'会话模型已变化，请重新选择。',MODEL_KEY_UNAVAILABLE:'当前模型没有可读取的密钥，请在模型设置中检查。',MODEL_CREDENTIALS_NOT_READY:'模型凭据尚未就绪，请在模型设置中检查后重试。',MODEL_REVISION_UNAVAILABLE:'会话绑定的模型配置已不可用，请重新选择已配置的模型。',MODEL_SELECTION_REQUIRED:'请先为这个会话选择已配置的模型。',REASONING_CAPABILITY_CHANGED:'模型能力已变化，请重新选择模型后发送。',START_PAGE_UNAVAILABLE:'暂时无法打开模型设置，请稍后重试。'};
  function notice(message){$('notice').hidden=false;$('notice').querySelector('span').textContent=errorText[message]||message;}
  async function native(method,payload){const bridge=window.pywebview?.api;if(!bridge?.[method])throw new Error('桌面连接尚未就绪，请稍候。');const result=await (payload===undefined?bridge[method]():bridge[method](payload));if(result?.ok===false)throw new Error(errorText[result.message]||result.message||'操作未完成');return result;}
  async function request(operation,extra={}){return (await native('workbench_request',{operation,...extra})).data;}
  function act(fn){return async event=>{try{await fn(event);}catch(error){notice(error.message||'操作未完成');}};}
  function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  function title(frame){return frame?.name||frame?.task_summary||'未命名对话';}
  function stamp(value){const parsed=new Date(typeof value==='number'&&value<1e12?value*1000:value);return Number.isNaN(+parsed)?null:parsed;}
  function date(value){const parsed=stamp(value);return parsed?parsed.toLocaleDateString('zh-CN',{month:'short',day:'numeric'}):'';}
  function dayGroup(value){const d=stamp(value);if(!d)return '更早';const today=new Date();today.setHours(0,0,0,0);const day=new Date(d);day.setHours(0,0,0,0);const diff=Math.round((today-day)/864e5);return diff<=0?'今天':diff===1?'昨天':diff<7?'近 7 天':'更早';}
  function visibleFrames(){return state.frames.filter(f=>!hiddenIds.has(f.id)&&!hiddenIds.has(f.project_id)&&(!state.project||f.project_id===state.project));}

  /* One visible view at a time; the rail and the top bar follow it. */
  // Static markup, the same drawing as the notebook entry in the navigation.
  const NOTEBOOK_SVG='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 3.5h10a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2h-10z"/><path d="M6.5 3.5v17"/><path d="M4.5 7.5h4M4.5 12h4M4.5 16.5h4"/><path d="M11.5 15l1.9-2.8 1.8 1.4 1.8-3.1"/></svg>';
  function notebookIcon(){const icon=el('span','','card-icon hue-indigo');icon.innerHTML=NOTEBOOK_SVG;return icon;}
  const views=['home-view','chat-view','notebook-view','schedule-view'];
  let current='home-view';
  function show(view){
    current=view;
    for(const id of views)$(id).hidden=id!==view;
    $('nav-home').classList[view==='home-view'?'add':'remove']('active');
    $('nav-tools').classList[view==='notebook-view'?'add':'remove']('active');
    $('nav-schedule').classList[view==='schedule-view'?'add':'remove']('active');
    $('notebook-button').hidden=view!=='chat-view';
    $('home-button').hidden=view==='home-view';
    if(view!=='notebook-view')clearTimeout(nb.timer);
  }
  function updateHeader(){const project=state.projects.find(p=>(p.id||p.project_id)===state.project);$('project-name').textContent=project?.name||'科研空间';$('page-title').textContent=current==='notebook-view'?'笔记本与计算':current==='schedule-view'?'定时任务':state.frame?title(state.frame):'工作台';$('rename-chat').hidden=!state.frame||current!=='chat-view';}
  function home(){keepDraft();state.epoch++;nb.epoch++;state.frame=null;state.messages=[];state.execution=null;clearTimeout(poll);show('home-view');updateHeader();renderHistory();}
  function renderHistory(){const query=$('history-search').value.trim().toLowerCase();const frames=visibleFrames();$('history').replaceChildren();let group=null;for(const f of frames.filter(f=>title(f).toLowerCase().includes(query))){const g=dayGroup(f.updated_at);if(g!==group){group=g;$('history').append(el('p',g,'history-group'));}const active=state.frame?.id===f.id;const row=el('div',undefined,'history-row'+(active?' active':''));const b=el('button',title(f),'history-item'+(active?' active':''));b.title=title(f);b.onclick=act(()=>openFrame(f));row.append(b,moreButton({entity_type:'session',entity_id:f.id,title:title(f)}));$('history').append(row);}$('history-count').textContent=String(frames.length);if(!frames.length)$('history').append(el('p','还没有对话。从一个问题开始。','muted'));$('recent-list').replaceChildren();for(const f of frames.slice(0,3)){const b=el('button',undefined,'recent-row');b.append(el('span','↳'),el('strong',title(f)),el('small',date(f.updated_at)),el('span','↗'));b.onclick=act(()=>openFrame(f));$('recent-list').append(b);}if(!frames.length)$('recent-list').append(el('p','开始对话后，可以从这里回到你的思路。','muted'));$('more-history').hidden=!state.cursor;renderSwitcher();}
  async function loadFrames(append=false){const data=await request('frames',{projectId:state.project||'all',...(append&&state.cursor?{cursor:state.cursor}:{})});state.frames=append?[...state.frames,...(data.frames||[])]:data.frames||[];state.cursor=data.next_cursor||null;renderHistory();}
  async function chooseName(label,value=''){const dialog=$('input-dialog');$('input-dialog-title').textContent=label;$('dialog-value').value=value;dialog.returnValue='';dialog.showModal();$('dialog-value').focus();return new Promise(resolve=>dialog.addEventListener('close',()=>resolve(dialog.returnValue==='save'?$('dialog-value').value.trim():null),{once:true}));}
  async function newFrame(){if(state.loading)return;state.loading=true;try{if(!state.project){const name=await chooseName('给你的第一个项目起个名字','我的研究');if(!name)return;const p=await request('create_project',{name});state.projects.push(p);state.project=p.id||p.project_id;renderProjects();}const f=await request('create_frame',{projectId:state.project});state.frames.unshift(f);await openFrame(f,true);$('message-input').focus();}finally{state.loading=false;}}
  function renderProjects(){const select=$('project-select');select.replaceChildren();for(const p of state.projects){const option=el('option',p.name||'未命名项目');option.value=p.id||p.project_id;select.append(option);}if(!state.projects.length){const option=el('option','新建一个科研项目');option.value='';select.append(option);}select.value=state.project||'';renderSwitcher();updateHeader();}
  /* Project switcher. Tiles take a stable colour from the project id. */
  const CHECK_SVG='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>';
  function projectKey(p){return p?.id||p?.project_id||'';}
  function paintTile(node,p){const name=String(p?.name||'').trim();let h=0;for(const ch of projectKey(p)||name)h=(h*31+ch.codePointAt(0))>>>0;node.textContent=name?[...name][0].toUpperCase():'＋';node.className='tile '+(p?'tile-'+(h%5+1):'tile-empty');}
  function renderSwitcher(){const p=state.projects.find(x=>projectKey(x)===state.project);paintTile($('project-tile'),p);$('project-switch-name').textContent=p?.name||(state.projects.length?'选择项目':'新建一个项目');$('project-switch-meta').textContent=p?'当前项目 · '+visibleFrames().length+' 个对话':'还没有项目';if(projectPopOpen)renderProjectOptions();}
  function renderProjectOptions(){const q=String($('project-search').value||'').trim().toLowerCase();const host=$('project-options');host.replaceChildren();const list=state.projects.filter(p=>String(p.name||'').toLowerCase().includes(q));for(const p of list){const on=projectKey(p)===state.project;const b=el('button',undefined,'project-option'+(on?' selected':''));b.type='button';b.setAttribute('role','option');b.setAttribute('aria-selected',String(on));b.title=p.name||'';const tile=el('span');paintTile(tile,p);b.append(tile,el('span',p.name||'未命名项目','po-name'));if(on){const check=el('span','','po-check');check.innerHTML=CHECK_SVG;b.append(check);}b.onclick=act(async()=>{closeProjectPop();$('project-switch').focus();if(!on)await switchProject(projectKey(p));});const row=el('div',undefined,'project-row');row.append(b,moreButton({entity_type:'project',entity_id:projectKey(p),title:p.name||'未命名项目'}));host.append(row);}if(!list.length)host.append(el('p',state.projects.length?'没有匹配的项目。':'还没有项目。','muted'));}
  let projectPopOpen=false;
  function openProjectPop(){projectPopOpen=true;closePickers();$('project-search').value='';renderProjectOptions();$('project-pop').hidden=false;$('project-switch').setAttribute('aria-expanded','true');$('project-search').focus();}
  function closeProjectPop(){if(!projectPopOpen)return;projectPopOpen=false;$('project-pop').hidden=true;$('project-switch').setAttribute('aria-expanded','false');}
  /* Row menu: archive is reversible and immediate; delete moves to the recycle bin after a
     confirmation. Permanent removal stays in the manager, behind its typed confirmation. */
  const MORE_SVG='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5.5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="18.5" cy="12" r="1.3"/></svg>';
  let menuItem=null,menuAnchor=null;
  function moreButton(item){const b=el('button','','row-more');b.type='button';b.innerHTML=MORE_SVG;b.title='更多操作';b.ariaLabel='“'+item.title+'”的更多操作';b.ariaHasPopup='menu';b.onclick=event=>{event?.stopPropagation?.();menuAnchor===b?closeItemMenu():openItemMenu(b,item);};return b;}
  function openItemMenu(anchor,item){closeItemMenu();closePickers();menuItem=item;menuAnchor=anchor;anchor.classList.add('open');const menu=$('item-menu');menu.hidden=false;
    const r=anchor.getBoundingClientRect(),w=menu.offsetWidth,h=menu.offsetHeight;
    menu.style.left=Math.max(8,Math.min(r.right-w,innerWidth-w-8))+'px';menu.style.top=(r.bottom+4+h>innerHeight-8?Math.max(8,r.top-4-h):r.bottom+4)+'px';
    $('item-archive').focus();}
  function closeItemMenu(){const item=menuItem;if(!menuAnchor&&!item)return null;$('item-menu').hidden=true;menuAnchor?.classList.remove('open');menuItem=null;menuAnchor=null;return item;}
  const kindName=item=>item.entity_type==='project'?'项目':'对话';
  async function switchProject(id){state.project=id;$('project-select').value=id;home();renderSwitcher();await loadFrames();}

  /* Custom pickers draw a native <select>, which stays the source of truth for value,
     options, disabled state and change events. */
  const CHEVRON_SVG='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>',SPARK_SVG='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3.5 13.9 9l5.6 1.9-5.6 1.9L12 18.5l-1.9-5.7L4.5 10.9 10.1 9z"/></svg>',GAUGE_SVG='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 16.5a8 8 0 1 1 15 0"/><path d="m12 13 3.5-4"/><circle cx="12" cy="13.2" r="1.2"/></svg>';
  const openPickers=new Set();
  function closePickers(except){for(const p of [...openPickers])if(p!==except)p.close();}
  function enhanceSelect(select,{icon='',up=false,variant='field'}={}){
    if(!select||select.dataset.picker)return;select.dataset.picker='1';
    const wrap=el('div',undefined,'picker picker-'+variant+(up?' picker-up':''));select.before(wrap);
    const button=el('button',undefined,'picker-button');button.type='button';button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');
    const name=select.getAttribute('aria-label')||select.closest('label')?.firstChild?.textContent?.trim();if(name)button.setAttribute('aria-label',name);
    if(icon){const i=el('span','','picker-icon');i.innerHTML=icon;button.append(i);}
    const text=el('span','','picker-text'),chevron=el('span','','picker-chevron');chevron.innerHTML=CHEVRON_SVG;button.append(text,chevron);
    const list=el('div',undefined,'picker-list');list.setAttribute('role','listbox');list.hidden=true;
    // The button comes first, so a wrapping <label> activates it rather than the hidden select.
    wrap.append(button,list,select);select.classList.add('native-hidden');select.tabIndex=-1;select.setAttribute('aria-hidden','true');
    const sync=()=>{const o=select.options[select.selectedIndex];text.textContent=o?o.textContent:'';button.title=text.textContent;button.disabled=select.disabled;};
    const picker={close(){if(list.hidden)return;list.hidden=true;button.setAttribute('aria-expanded','false');openPickers.delete(picker);},
      open(){closePickers(picker);closeProjectPop();list.replaceChildren();
        for(const o of select.options){const item=el('button',undefined,'picker-option'+(o.selected?' selected':''));item.type='button';item.setAttribute('role','option');item.setAttribute('aria-selected',String(o.selected));item.disabled=o.disabled;if(o.title)item.title=o.title;item.append(el('span',o.textContent,'picker-option-text'));
          if(o.selected){const check=el('span','','picker-check');check.innerHTML=CHECK_SVG;item.append(check);}
          item.onclick=()=>{picker.close();button.focus();if(select.value!==o.value){select.value=o.value;select.dispatchEvent(new Event('change',{bubbles:true}));}};list.append(item);}
        list.hidden=false;button.setAttribute('aria-expanded','true');openPickers.add(picker);(list.querySelector('.selected:not(:disabled)')||list.querySelector('button:not(:disabled)'))?.focus();}};
    button.onclick=()=>list.hidden?picker.open():picker.close();
    button.onkeydown=e=>{if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();picker.open();}};
    list.onkeydown=e=>{const items=[...list.querySelectorAll('button:not(:disabled)')],i=items.indexOf(document.activeElement);if(e.key==='Escape'){e.preventDefault();e.stopPropagation();picker.close();button.focus();}else if(e.key==='Tab')picker.close();else if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){e.preventDefault();items[e.key==='Home'?0:e.key==='End'?items.length-1:(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length]?.focus();}};
    new MutationObserver(sync).observe(select,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled']});
    // Code sets select.value directly in many places; the label follows every assignment.
    const value=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value');
    Object.defineProperty(select,'value',{configurable:true,get(){return value.get.call(this);},set(v){value.set.call(this,v);sync();}});
    select.addEventListener('change',sync);sync();
  }
  async function refreshModels(fresh=false){const fid=state.frame?.id;if(!fid)return;const data=await native('list_session_models',{frame_id:fid});if(state.frame?.id!==fid)return;state.binding=data.binding;const select=$('model-select');select.replaceChildren();const empty=el('option','选择会话模型');empty.value='';select.append(empty);for(const m of data.models||[]){const o=el('option',m.name+' · '+m.model);o.value=m.id;o.disabled=!m.available;select.append(o);}select.value=data.binding?.native_profile_id||'';renderEffort();if(fresh&&data.active_native_profile_id){select.value=data.active_native_profile_id;await selectModel();}}
  async function selectModel(){const id=$('model-select').value,fid=state.frame?.id;if(!id||!fid)return;const binding=state.binding;const data=await native('select_session_model',{frame_id:fid,native_profile_id:id,expected_binding:{profile_id:binding.profile_id,revision:binding.revision}});if(state.frame?.id===fid){state.binding=data.binding;renderEffort();}}
  async function prepareMessage(fid,previous){
    const data=await native('list_session_models',{frame_id:fid});
    let binding=data.binding;
    if(!binding?.native_profile_id)throw new Error('MODEL_SELECTION_REQUIRED');
    if(previous?.profile_id!==binding.profile_id||previous?.revision!==binding.revision)throw new Error('MODEL_BINDING_CONFLICT');
    if(binding.credential_ready===false){
      const restored=await native('select_session_model',{frame_id:fid,native_profile_id:binding.native_profile_id,
        expected_binding:{profile_id:binding.profile_id,revision:binding.revision}});
      binding=restored.binding;
    }
    if(binding.credential_ready!==true)throw new Error('MODEL_CREDENTIALS_NOT_READY');
    if(state.frame?.id!==fid)throw new Error('会话已切换，原消息未发送。');
    state.binding=binding;
    const capability=binding.reasoning,choice=$('effort-select').value||'default';
    if(!capability?.revision||previous?.reasoning?.revision!==capability.revision||!capability.choices?.some(c=>c.id===choice&&c.available===true)){renderEffort();throw new Error('REASONING_CAPABILITY_CHANGED');}
    return {modelBinding:{profile_id:binding.profile_id,revision:binding.revision},reasoningSelection:{choice,capability_revision:capability.revision}};
  }
  function codeBlock(language,code){const box=el('div',undefined,'code-block');const head=el('div',undefined,'code-head');head.append(el('span',language.trim()||'代码','code-lang'));const copy=el('button','复制','code-copy');copy.type='button';copy.onclick=act(async()=>{await copyText(code);flash(copy,'已复制');});head.append(copy);const pre=el('pre');pre.append(el('code',code));box.append(head,pre);return box;}
  /* 2.2.10 · **bold** and links to this conversation's files. A link never gets an address: it is a
     button that finds the file among the conversation's own artifacts and previews it in a dialog. */
  const ARTIFACT_LINK=/^\[((?:\\.|[^\]\\])+)\]\(\/api\/(?:v1\/)?artifacts\/([^)\s]+)\)$/;
  const INLINE=/(\[(?:\\.|[^\]\\])+\]\(\/api\/(?:v1\/)?artifacts\/[^)\s]+\)|\*\*[^*]+\*\*)/g;
  function artifactRef(target){const parts=String(target).split('/');const last=parts.pop();let value=last;try{value=decodeURIComponent(last);}catch(_){}
    return {value,version:parts.at(-1)==='versions'};}
  function inlineNode(chunk){
    const link=ARTIFACT_LINK.exec(chunk);
    if(link){const label=link[1].replace(/\\([\[\]])/g,'$1');const ref=artifactRef(link[2]);const b=el('button',label,'artifact-link');b.type='button';b.title='预览 '+label;
      b.onclick=act(()=>openArtifactPreview(ref,label));return b;}
    return chunk.startsWith('**')&&chunk.endsWith('**')?el('strong',chunk.slice(2,-2)):document.createTextNode(chunk);}
  function messageContent(host,text){const parts=String(text||'').split(/```([^\n]*)\n([\s\S]*?)```/g);for(let i=0;i<parts.length;i+=3){let part=parts[i];
    // Blank lines that only separate text from a code block are the block's own spacing.
    if(i>0)part=part.replace(/^\n+/,'');if(i+2<parts.length)part=part.replace(/\n+$/,'');
    {const body=el('div',undefined,'message-body');for(const [index,line]of part.split('\n').entries()){if(index)body.append(document.createTextNode('\n'));if(/^#{1,3} /.test(line))body.append(el('strong',line.replace(/^#+ /,'')));else{line.split(INLINE).forEach(chunk=>body.append(inlineNode(chunk)));}}host.append(body);}if(i+2<parts.length)host.append(codeBlock(parts[i+1],parts[i+2]));}}
  function answerText(content){
    // The runtime appends this protocol checklist to its final summary. Hide
    // that section only; retain findings, limitations, artifacts and quotations.
    const lines=String(content||'').split('\n'), kept=[];
    let fence=null;
    for(let i=0;i<lines.length;i++){
      const marker=lines[i].match(/^\s{0,3}(`{3,}|~{3,})/);
      if(marker){if(!fence)fence=marker[1];else if(marker[1][0]===fence[0]&&marker[1].length>=fence.length)fence=null;kept.push(lines[i]);continue;}
      if(!fence&&/^(完成内容：|Completed work:)\s*$/.test(lines[i])){
        let end=i+1;
        while(end<lines.length&&/^- \S/.test(lines[end]))end++;
        if(end>i+1&&end<=i+5&&(end===lines.length||!lines[end].trim())){i=end-1;continue;}
      }
      kept.push(lines[i]);
    }
    return kept.join('\n').trim();
  }
  function displayMessages(messages=state.messages){
    const rows=[];
    let previous=null;
    for(const raw of [...messages].sort((a,b)=>a.seq-b.seq)){
      if(raw.role!=='assistant'){rows.push(raw);previous=null;continue;}
      // Failure and reviewed/evidence-bearing records keep their own identity.
      const protectedRow=raw.failure||raw.review_status||raw.turn_id||raw.execution_id||raw.artifact_refs?.length;
      const content=protectedRow?raw.content:answerText(raw.content);
      if(!content&&!protectedRow)continue;
      const row={...raw,content};
      if(!protectedRow&&previous&&previous.content===content)continue;
      rows.push(row);previous=protectedRow?null:row;
    }
    return rows;
  }
  /* 2.2.8 · A turn reads as its answer; the in-between remarks and the steps behind it fold into
     「思考与步骤」 above it. Steps come from the daemon's own action timeline (no arguments). */
  const STEP_KIND={code:'运行计算',native_tools:'调用工具',delegate:'交给子助手',other:'步骤'};
  const STEP_STATUS={completed:['完成','ok'],failed:['未成功','bad'],running:['进行中','run'],cancelled:['已取消',''],interrupted:['已中断',''],pending:['等待中','run'],proposed:['准备中','run']};
  function permissionText(p){if(!p)return '';const s=String(p.state||'').toLowerCase();
    if((approval.auto||[]).some(a=>a.decisionId===p.decisionId))return 'Smart 自动放行（只读命令）';
    if(/allow|approv|grant/.test(s))return '经你批准';if(/den|reject/.test(s))return '已被你拒绝';
    if(/time|expire/.test(s))return '审批超时，未执行';if(/pend|wait/.test(s))return '等待你批准';return '';}
  function timelineTurns(){const turns=[];let current=null;
    for(const g of state.timeline||[]){if(g.kind==='user'){current=[];current.turnId=g.turnId||null;turns.push(current);continue;}
      if(current&&['code','native_tools','delegate','other'].includes(g.kind)){if(!current.turnId)current.turnId=g.turnId||null;current.push(g);}}
    return turns;}
  /* 2.2.11 · The model's own reasoning (DeepSeek reasoning_content), one entry per model call,
     shown as plain text: it is the model's working, not a checked result. */
  function turnThoughts(turnId){if(!turnId)return [];return (state.thoughts||[]).filter(t=>t.turnId===turnId).sort((a,b)=>(a.engineTurn??0)-(b.engineTurn??0));}
  function thoughtList(thoughts){const list=el('ol',undefined,'process-thoughts');
    thoughts.forEach((t,i)=>{const li=el('li');const item=el('details',undefined,'thought');
      item.append(el('summary','第 '+(i+1)+' 次调用'+(t.status&&t.status!=='completed'?' · 未完成':'')+(t.truncated?' · 已截断':'')));
      item.append(el('pre',t.text,'thought-text'));li.append(item);list.append(li);});
    return list;}
  function messageRow(m){const row=el('article',undefined,'message '+m.role+(m.failure?' failure':''));row.append(el('header',m.role==='assistant'?'LEO AI':'你'));messageContent(row,m.content);if(m.failure)row.append(el('p','本次调用未完成'+(m.failure.request_id?' · 支持 ID：'+m.failure.request_id:''),'muted'));row.append(actionBar(m,row));return row;}
  function processBlock(notes,steps,running,thoughts=[]){const box=el('details',undefined,'process'+(running?' running':''));if(running)box.open=true;
    box.append(el('summary',(running?'正在思考与执行':'思考与步骤')+' · '+(notes.length+steps.length+thoughts.length)+' 项'));
    if(thoughts.length){box.append(el('p','模型思考 · 原文，未经核实','process-label'));box.append(thoughtList(thoughts));}
    if(notes.length){box.append(el('p','过程说明','process-label'));const list=el('ol',undefined,'process-notes');for(const m of notes){const li=el('li');messageContent(li,m.content);list.append(li);}box.append(list);}
    if(steps.length){box.append(el('p','执行步骤','process-label'));const list=el('ol',undefined,'process-steps');
      for(const g of steps){const [label,kind]=STEP_STATUS[g.status]||['',''];const li=el('li',undefined,'process-step'+(kind?' '+kind:''));
        li.append(el('span',label||'—','step-status'),el('span',(STEP_KIND[g.kind]||'步骤')+'：'+(g.kind==='native_tools'&&g.names?.length?g.names.join('、'):(g.title||'')),'step-title'));
        const perm=permissionText(g.permission);if(perm)li.append(el('span',perm,'step-perm'));list.append(li);}
      box.append(list);}
    return box;}
  function renderMessages(scroll=false){const area=$('messages');const scroller=$('chat-scroll');const atEnd=scroller.scrollHeight-scroller.scrollTop-scroller.clientHeight<130;area.replaceChildren();
    if(!state.messages.length){const empty=el('div',undefined,'message-empty');empty.append(el('p','✦','eyebrow'),el('h2','一个好问题，是发现的开始。'),el('p','可以讨论一个原理，也可以整理一个真实研究任务。','muted'));area.append(empty);}
    const turns=[];let current=null;
    for(const m of displayMessages()){if(!['assistant','user'].includes(m.role))continue;
      if(m.role==='user'||!current){current={user:m.role==='user'?m:null,replies:[]};turns.push(current);if(m.role==='user')continue;}
      current.replies.push(m);}
    const stepTurns=timelineTurns();let userIndex=stepTurns.length-turns.filter(x=>x.user).length;
    turns.forEach((turn,i)=>{
      if(turn.user)area.append(messageRow(turn.user));
      const steps=turn.user?(stepTurns[userIndex++]||[]):[];
      const thoughts=turnThoughts(steps.turnId||turn.user?.turn_id);
      const running=i===turns.length-1&&!!state.execution;
      let answer=-1;if(!running)for(let k=turn.replies.length-1;k>=0;k--)if(!turn.replies[k].failure){answer=k;break;}
      const notes=turn.replies.filter((m,k)=>!m.failure&&(running||k<answer));
      if(notes.length||steps.length||thoughts.length)area.append(processBlock(notes,steps,running,thoughts));
      for(const m of turn.replies)if(!notes.includes(m))area.append(messageRow(m));
    });
    if(scroll||atEnd)scroller.scrollTop=scroller.scrollHeight;}
  async function refreshTimeline(fid,force){if(!force&&Date.now()-(state.timelineAt||0)<15000)return;state.timelineAt=Date.now();
    // The stored reasoning is re-read whole each time, so while a turn runs it is fetched at most every 5 s.
    const wantThoughts=Date.now()-(state.thoughtsAt||0)>=5000;if(wantThoughts)state.thoughtsAt=Date.now();
    try{const [d,t]=await Promise.all([request('timeline',{frameId:fid}),wantThoughts?request('thoughts',{frameId:fid}).catch(()=>null):null]);if(state.frame?.id!==fid)return;const next=d.groups||[];
      const thoughts=t?(t.thoughts||[]):(state.thoughts||[]);
      if(JSON.stringify(next)!==JSON.stringify(state.timeline||[])||JSON.stringify(thoughts)!==JSON.stringify(state.thoughts||[])){state.timeline=next;state.thoughts=thoughts;renderMessages();}}catch(_){}}
  function running(execution){state.execution=execution;const active=!!execution;$('working').hidden=!active;$('stop').hidden=!active;$('send').hidden=active;$('model-select').disabled=active;$('effort-select').disabled=active;$('elapsed').textContent=active&&openedAt?' · '+Math.max(0,Math.floor((Date.now()-openedAt)/1000))+' 秒':'';}
  async function refreshChat(epoch=state.epoch){const fid=state.frame?.id;if(!fid||epoch!==state.epoch)return;const [data,queue]=await Promise.all([request('messages',{frameId:fid}),request('execution',{frameId:fid})]);if(epoch!==state.epoch)return;const seen=new Map(state.messages.map(m=>[m.message_id||m.seq,m]));for(const m of data.messages||[])seen.set(m.message_id||m.seq,m);const next=[...seen.values()];const changed=JSON.stringify(next)!==JSON.stringify(state.messages);state.messages=next;if(state.before===null){state.before=data.next_before_seq;$('earlier-messages').hidden=!data.has_earlier;}if(changed)renderMessages();const owner=queue.owner||queue.queue?.[0]||null;running(owner);refreshApprovals(fid);refreshTimeline(fid,changed||!!owner);clearTimeout(poll);poll=setTimeout(()=>refreshChat(epoch).catch(e=>{notice(e.message);poll=setTimeout(()=>refreshChat(epoch).catch(e=>notice(e.message)),5000);}),owner?1700:6000);}
  async function openFrame(frame,fresh=false){keepDraft();state.epoch++;nb.epoch++;clearTimeout(poll);state.frame=frame;state.project=frame.project_id;state.messages=[];state.timeline=[];state.thoughts=[];state.thoughtsAt=0;state.timelineAt=0;state.before=null;state.binding=null;openedAt=0;$('message-input').value=drafts.get(frame.id)||'';show('chat-view');$('earlier-messages').hidden=true;$('project-select').value=state.project;updateHeader();renderHistory();renderMessages();state.feedback={};request('feedback',{frameId:frame.id}).then(d=>{if(state.frame?.id===frame.id){state.feedback=d.feedback||{};renderMessages();}}).catch(()=>{});await Promise.all([refreshModels(fresh),refreshChat(),loadMode(frame)]);}
  async function send(){if(state.sending||!state.frame)return;const input=$('message-input');const value=input.value.trim();if(!value)return;state.sending=true;$('send').disabled=true;const originalFrame=state.frame;const fid=originalFrame.id;try{const selection=await prepareMessage(fid,state.binding);await request('send',{frameId:fid,text:value,...selection});$('notice').hidden=true;if(state.frame?.id===fid){input.value='';drafts.delete(fid);openedAt=Date.now();await refreshChat();}if(!originalFrame.name){await request('rename',{frameId:fid,name:value.slice(0,60)});if(state.frame?.id===fid)state.frame.name=value.slice(0,60);updateHeader();}await loadFrames();}finally{state.sending=false;$('send').disabled=false;}}
  async function research(){if(!state.frame)await newFrame();if(state.frame)window.LeoResearch?.open();}

  /* Message actions. Copy takes the selection inside that message when there is one;
     ratings are stored with the conversation; forwarding only ever fills an input box. */
  // What the message looks like on screen: no bold or heading markers, no code-fence lines.
  function plainText(text){return String(text||'').split('\n').filter(line=>!/^```/.test(line)).map(line=>line.replace(/^#{1,3} /,'').replace(/\*\*([^*]+)\*\*/g,'$1')).join('\n');}
  function messageKey(m){return String(m.message_id||('seq-'+m.seq)).replace(/[^A-Za-z0-9_.:-]/g,'-').slice(0,128);}
  async function copyText(text){
    try{if(window.navigator?.clipboard?.writeText){await window.navigator.clipboard.writeText(text);return;}}catch(e){}
    let copied=false;
    try{const area=document.createElement('textarea');area.value=text;area.setAttribute('readonly','');area.style.position='fixed';area.style.opacity='0';
      document.body.append(area);area.select();copied=document.execCommand('copy');area.remove();}catch(e){}
    if(!copied)await native('copy_text',{text});
  }
  function selectionWithin(node){const s=window.getSelection?.();if(!s||s.isCollapsed||!s.rangeCount)return '';const r=s.getRangeAt(0);return node.contains?.(r.commonAncestorContainer)?s.toString():'';}
  function flash(button,text){const before=button.textContent;button.textContent=text;setTimeout(()=>{button.textContent=before;},1400);}
  function actionBar(m,row){
    const bar=el('div',undefined,'message-actions');
    const copy=el('button','复制','msg-action');copy.title='复制整条；先选中其中一段，就只复制所选';
    copy.onclick=act(async()=>{const part=selectionWithin(row);await copyText(part||plainText(m.content));flash(copy,part?'已复制所选':'已复制');});
    bar.append(copy);
    if(m.role==='assistant'){
      const key=messageKey(m);
      for(const [rating,label,hint] of [['up','赞','这条回复有帮助'],['down','踩','这条回复有问题']]){
        const on=state.feedback[key]===rating;
        const b=el('button',label,'msg-action rate '+rating+(on?' active':''));b.title=on?'再点一次取消':hint;b.setAttribute('aria-pressed',String(on));
        b.onclick=act(async()=>{const fid=state.frame?.id;if(!fid)return;const next=state.feedback[key]===rating?null:rating;
          await request('set_feedback',{frameId:fid,key,rating:next});if(state.frame?.id!==fid)return;
          if(next)state.feedback[key]=next;else delete state.feedback[key];renderMessages();});
        bar.append(b);
      }
    }
    const candidate=m.role==='assistant'?themeFromMessage(m.content):null;if(candidate){const themeButton=el('button','预览主题','msg-action');themeButton.onclick=act(()=>previewTheme(candidate));bar.append(themeButton);}
    const forward=el('button','转发','msg-action');forward.title=m.role==='assistant'?'转发这条回复':'转发这个提问';forward.onclick=act(()=>openForward(m));bar.append(forward);
    return bar;
  }
  let forwarding=null;
  function forwardText(m){
    const content=String(m.content||'');
    if(m.role!=='assistant')return content;
    return '以下内容转发自 Leo AI 在「'+title(state.frame)+'」中的回复：\n\n'+content.split('\n').map(line=>'> '+line).join('\n')+'\n\n';
  }
  function shareText(m){
    const who=m.role==='assistant'?'Leo AI 的回复':'我的提问';
    return who+'（来自 Leo AI Studio ·「'+title(state.frame)+'」）\n\n'+plainText(m.content)+(m.role==='assistant'?'\n\n— 由 AI 生成，重要结论请核对证据。':'');
  }
  function openForward(m){
    forwarding=m;const list=$('forward-targets');list.replaceChildren();
    const fresh=el('button',undefined,'forward-target');fresh.append(el('span','＋'),el('strong','新对话'));fresh.onclick=act(()=>forwardTo(null));list.append(fresh);
    for(const f of visibleFrames().filter(f=>f.id!==state.frame?.id).slice(0,8)){
      const b=el('button',undefined,'forward-target');b.append(el('span','↳'),el('strong',title(f)),el('small',date(f.updated_at)));b.onclick=act(()=>forwardTo(f));list.append(b);
    }
    $('forward-kind').textContent=m.role==='assistant'?'转发这条回复':'转发这个提问';
    $('forward-dialog').showModal();
  }
  async function forwardTo(target){
    const m=forwarding;if(!m)return;const text=forwardText(m);$('forward-dialog').close();
    if(target){const kept=drafts.get(target.id);drafts.set(target.id,kept?kept+'\n\n'+text:text);await openFrame(target);}
    else{await newFrame();if(!state.frame)return;$('message-input').value=text;}
    $('notice').hidden=false;$('notice').querySelector('span').textContent='已放进输入框，核对后再发送。';
    $('message-input').focus();
  }

  /* Notebook: a read-only record of what Leo actually executed in a conversation.
     Everything comes through the native gateway; no upstream page is ever loaded. */
  const nb={frame:null,epoch:0,timer:null,artifacts:[],previewId:null,images:Promise.resolve()};
  const cellStatus={ok:['trust-verified','完成'],success:['trust-verified','完成'],error:['trust-failed','出错'],failed:['trust-failed','出错'],
    running:['trust-compute','运行中'],queued:['trust-compute','排队中'],cancelled:['trust-blocked','已取消'],interrupted:['trust-blocked','已中断']};
  const kernelText={running:['trust-compute','内核运行中'],stopped:['trust-blocked','内核已停止'],ended:['trust-blocked','内核已结束'],none:['trust-blocked','内核未启动']};
  function chip(text,cls){return el('span',text,'trust-chip '+cls);}
  function size(bytes){if(typeof bytes!=='number')return '';if(bytes<1024)return bytes+' B';if(bytes<1048576)return (bytes/1024).toFixed(1)+' KB';return (bytes/1048576).toFixed(1)+' MB';}
  function glyph(a){const t=(a.contentType||'').toLowerCase(),n=(a.filename||'').toLowerCase();if(t.startsWith('image/'))return '◧';if(/\.(csv|tsv|json|txt|md|log|dat)$/.test(n)||t.startsWith('text/'))return '≣';if(/\.(py|r)$/.test(n))return '⌁';return '▤';}
  function findArtifact(name){const base=String(name).split('/').pop();return nb.artifacts.find(a=>a.filename===name)||nb.artifacts.find(a=>(a.filename||'').split('/').pop()===base)||null;}
  function notebookChrome(hasFrame){for(const id of ['nb-kernel','nb-refresh','nb-open-chat','nb-switch'])$(id).hidden=!hasFrame;}
  function renderPicker(){
    notebookChrome(false);$('nb-layout').hidden=true;$('nb-title').textContent='笔记本与计算';
    $('nb-subtitle').textContent='选择一个对话，查看 Leo 在其中实际执行的代码、输出与产物。';
    const host=$('nb-empty');host.hidden=false;host.replaceChildren();
    host.append(notebookIcon(),el('h2','选择一个对话，查看它的计算记录'),el('p','笔记本如实记录计算过程；结论是否成立，以验证证据为准。','muted'));
    const list=el('div',undefined,'nb-pick');const frames=visibleFrames().slice(0,12);
    for(const f of frames){const b=el('button');b.append(el('span','↳'),el('strong',title(f)),el('small',date(f.updated_at)));b.onclick=act(()=>openNotebook(f));list.append(b);}
    if(!frames.length)list.append(el('p','还没有对话。先开始一个对话，让 Leo 帮你计算。','muted'));
    host.append(list);
  }
  function renderKernel(kernel){const [cls,label]=kernelText[kernel?.state]||kernelText.none;const node=$('nb-kernel');node.className='trust-chip '+cls;node.textContent=label;}
  function renderArtifacts(){
    const host=$('nb-artifacts');host.replaceChildren();$('nb-artifact-count').textContent=nb.artifacts.length?nb.artifacts.length+' 个':'';
    if(!nb.artifacts.length)host.append(el('p','这个对话还没有产生文件。','muted'));
    for(const a of nb.artifacts){const b=el('button',undefined,'nb-artifact'+(nb.previewId===a.id?' active':''));b.append(el('span',glyph(a)),el('strong',a.filename||a.id),el('small',size(a.size)));b.title=a.filename||a.id;b.onclick=act(()=>previewArtifact(a));host.append(b);}
  }
  async function previewArtifact(a){
    const fid=nb.frame?.id,epoch=nb.epoch;if(!fid)return;
    nb.previewId=a.id;renderArtifacts();$('nb-preview').hidden=false;$('nb-preview-title').textContent=a.filename||'预览';
    const body=$('nb-preview-body');body.replaceChildren(el('p','正在读取…','muted'));
    const p=await request('artifact_preview',{frameId:fid,artifactId:a.id});
    if(epoch!==nb.epoch||nb.previewId!==a.id)return;
    paintPreview(body,p,a);
  }
  function paintPreview(body,p,a){
    body.replaceChildren();
    if(p.kind==='image'){const img=el('img');img.alt=a.filename||'';img.src=p.dataUri;body.append(img);}
    else if(p.kind==='text'){body.append(el('pre',p.text));if(p.truncated)body.append(el('p','文件较大，只显示前 256 KB。','muted'));}
    else body.append(el('p','这种文件（'+(p.contentType||'未知类型')+(p.size!=null?'，'+size(p.size):'')+'）暂不能在这里预览。','muted'));
  }
  /* A link in an answer: only a file listed for this conversation is ever requested. */
  const artifactLists=new Map();let artifactOpen=0;
  function matchArtifact(list,ref){const base=ref.value.split('/').pop();
    return list.find(a=>a.id===ref.value)||(ref.version?list.find(a=>a.versionId===ref.value):null)||list.find(a=>a.filename===ref.value)||list.find(a=>(a.filename||'').split('/').pop()===base)||null;}
  async function openArtifactPreview(ref,label){
    const fid=state.frame?.id;if(!fid)return;
    const dialog=$('artifact-dialog'),body=$('artifact-dialog-body'),token=++artifactOpen;
    $('artifact-dialog-title').textContent=label||'文件预览';body.replaceChildren(el('p','正在读取…','muted'));
    if(!dialog.open)dialog.showModal();
    try{
      let list=artifactLists.get(fid),art=list?matchArtifact(list,ref):null;
      if(!art){list=(await request('artifacts',{frameId:fid})).artifacts||[];artifactLists.set(fid,list);art=matchArtifact(list,ref);}
      if(token!==artifactOpen)return;
      if(!art){body.replaceChildren(el('p','这个文件不在本对话的产物中，无法预览。','muted'));return;}
      $('artifact-dialog-title').textContent=art.filename||label||'文件预览';
      const p=await request('artifact_preview',{frameId:fid,artifactId:art.id});
      if(token!==artifactOpen)return;
      paintPreview(body,p,art);
    }catch(error){if(token===artifactOpen)body.replaceChildren(el('p','读取失败：'+(error.message||'请稍后重试'),'muted'));}
  }
  function figureList(names){
    const box=el('div',undefined,'nb-figures');
    for(const name of names){
      const fig=el('figure');const art=findArtifact(name);
      if(!art){fig.append(el('figcaption',name+' · 未在本对话的产物中找到'));box.append(fig);continue;}
      const img=el('img');img.alt=name;fig.append(img,el('figcaption',name));box.append(fig);
      const epoch=nb.epoch,fid=nb.frame.id;
      // One figure at a time: previews are base64 round trips through the native bridge.
      nb.images=nb.images.then(async()=>{if(epoch!==nb.epoch)return;try{const p=await request('artifact_preview',{frameId:fid,artifactId:art.id});
        if(epoch!==nb.epoch)return;if(p.kind==='image')img.src=p.dataUri;else{img.hidden=true;fig.append(el('small','不是可显示的图片','muted'));}}
        catch(e){img.hidden=true;fig.append(el('small','图片读取失败','muted'));}});
    }
    return box;
  }
  function renderCells(log){
    const host=$('nb-cells');host.replaceChildren();const entries=log.entries||[];
    $('nb-layout').hidden=false;
    const empty=$('nb-empty');empty.hidden=!!entries.length;empty.replaceChildren();
    if(!entries.length){
      empty.append(notebookIcon(),el('h2','这个对话还没有计算记录'),el('p','在对话里请 Leo 运行代码，代码单元、输出和图表会按顺序出现在这里。','muted'));
      const back=el('button','回到对话，开始计算','primary');back.onclick=act(()=>openFrame(nb.frame));empty.append(back);
      $('nb-layout').hidden=!nb.artifacts.length;return;
    }
    if(log.omitted)host.append(el('p','较早的 '+log.omitted+' 个单元未显示。','muted'));
    for(const c of entries){
      const card=el('article',undefined,'nb-cell');const head=el('header');
      const [cls,label]=cellStatus[c.status]||['trust-blocked',c.status||'未知'];
      head.append(el('strong','单元 '+(c.cellIndex??c.ordinal)),chip(c.language==='r'?'R':'Python','trust-compute'),chip(label,cls));
      if(c.attemptCount>1)head.append(chip('第 '+c.attempt+'/'+c.attemptCount+' 次尝试',c.latest?'trust-exploratory':'trust-blocked'));
      if(c.stale)head.append(chip('上游已变化，结果可能过时','trust-exploratory'));
      head.append(el('span',typeof c.cpuSeconds==='number'?'CPU '+c.cpuSeconds.toFixed(2)+' 秒':'','nb-meta'));
      card.append(head,el('pre',c.source||'（空单元）','nb-code'));
      if(c.stdout)card.append(el('pre',c.stdout,'nb-out'));
      if(c.stderr)card.append(el('pre',c.stderr,'nb-out stderr'));
      if(c.error)card.append(el('pre',c.error,'nb-out error'));
      if(c.figures?.length)card.append(figureList(c.figures));
      if(c.filesWritten?.length){const files=el('div',undefined,'nb-files');files.append(el('small','写入文件'));for(const n of c.filesWritten)files.append(el('span',n));card.append(files);}
      if(c.truncated)card.append(el('p','输出较长，只显示前 64 KB。','muted nb-files'));
      host.append(card);
    }
  }
  async function loadNotebook(epoch=nb.epoch){
    const fid=nb.frame?.id;if(!fid||epoch!==nb.epoch)return;
    const [log,kernel,arts]=await Promise.all([request('notebook',{frameId:fid}),request('kernel',{frameId:fid}).catch(()=>null),request('artifacts',{frameId:fid}).catch(()=>({artifacts:[]}))]);
    if(epoch!==nb.epoch)return;
    nb.artifacts=arts.artifacts||[];renderKernel(kernel);renderArtifacts();renderCells(log);
    clearTimeout(nb.timer);
    if(kernel?.state==='running'&&current==='notebook-view')nb.timer=setTimeout(()=>loadNotebook(epoch).catch(e=>notice(e.message)),8000);
  }
  async function openNotebook(frame=state.frame){
    keepDraft();state.epoch++;clearTimeout(poll);nb.epoch++;nb.frame=frame||null;nb.previewId=null;nb.images=Promise.resolve();
    show('notebook-view');$('nb-preview').hidden=true;$('nb-cells').replaceChildren();
    if(!nb.frame){updateHeader();renderPicker();return;}
    state.frame=nb.frame;state.project=nb.frame.project_id||state.project;updateHeader();renderHistory();
    notebookChrome(true);$('nb-title').textContent=title(nb.frame);$('nb-subtitle').textContent='这个对话中由 Leo 实际执行的代码、输出与产物。记录只读，每一步保留原样。';
    $('nb-empty').hidden=true;$('nb-layout').hidden=true;$('nb-kernel').className='trust-chip trust-blocked';$('nb-kernel').textContent='正在读取…';
    await loadNotebook(nb.epoch);
  }

  async function settings(){$('model-editor').hidden=true;$('settings-status').textContent='';shellState=await native('get_state');const area=$('settings-profiles');area.replaceChildren();for(const p of shellState.profiles||[]){const row=el('div',undefined,'settings-profile');row.append(el('strong',p.name),el('p',p.model+' · '+(p.has_key?'密钥已保存':'未配置密钥')));area.append(row);}if(!area.childElementCount)area.append(el('p','还没有模型配置。','muted'));selectSettingsTab('models');$('settings-dialog').showModal();}
  async function applyAppearance(){
    // The start page saves the theme; the workbench follows it instead of keeping its own palette.
    try{const s=await native('get_state');const theme=s?.appearance?.theme;const root=document.documentElement;
      if(root&&typeof theme==='string'&&/^[a-z0-9-]{1,40}$/.test(theme))root.setAttribute('data-leo-theme',theme);await refreshPreferences();}catch(e){}
  }

  // Local visibility is reversible; permanent removal goes through the native gate.
  let entities=[],allProjects=[];
  async function readEntities(){let offset=0,rows=[];do{const result=await native('list_entity_states',{offset,limit:1000});rows.push(...(result.entities||[]));offset=result.next_offset;}while(offset!==null&&offset!==undefined);entities=rows;hiddenIds=new Set();for(const r of rows){hiddenIds.add(r.entity_id);for(const id of r.snapshot?.member_session_ids||[])hiddenIds.add(id);}}
  async function allFrames(projectId='all'){let cursor=null,frames=[],seen=new Set();do{const d=await request('frames',{projectId,...(cursor?{cursor}:{})});frames.push(...(d.frames||[]));cursor=d.next_cursor;if(cursor&&seen.has(cursor))throw new Error('对话分页未能继续，请重试。');seen.add(cursor);}while(cursor);return frames;}
  async function reloadWorkspace(){await readEntities();allProjects=(await request('projects')).projects||[];state.projects=allProjects.filter(p=>!hiddenIds.has(p.id||p.project_id));if(!state.projects.some(p=>(p.id||p.project_id)===state.project))state.project=state.projects[0]?.id||state.projects[0]?.project_id||null;renderProjects();await loadFrames();}
  function confirmAction(title,description,permanent=false){const d=$('confirm-dialog');$('confirm-title').textContent=title;$('confirm-description').textContent=description;$('confirm-label').hidden=!permanent;$('confirm-value').value='';$('confirm-accept').disabled=permanent;$('confirm-value').oninput=()=>{$('confirm-accept').disabled=permanent&&$('confirm-value').value!=='彻底删除';};d.returnValue='';d.showModal();return new Promise(resolve=>d.addEventListener('close',()=>resolve(d.returnValue==='confirm'&&(!permanent||$('confirm-value').value==='彻底删除')),{once:true}));}
  const manageAct=fn=>async()=>{try{$('manage-status').textContent='';await fn();}catch(e){$('manage-status').textContent=errorText[e.message]||e.message;}};
  async function manageItems(){if(!$('manage-dialog').open)$('manage-dialog').showModal();await renderManager();}
  async function renderManager(){await readEntities();allProjects=(await request('projects')).projects||[];const kind=$('manage-kind').value||'session',filter=$('manage-state').value||'active';let rows;
    if(filter==='active'){rows=kind==='project'?allProjects.filter(p=>!hiddenIds.has(p.id||p.project_id)).map(p=>({entity_type:kind,entity_id:p.id||p.project_id,title:p.name})): (await allFrames()).filter(f=>!hiddenIds.has(f.id)&&!hiddenIds.has(f.project_id)).map(f=>({entity_type:kind,entity_id:f.id,title:title(f)}));}
    else rows=entities.filter(r=>r.entity_type===kind&&r.state===filter);
    const area=$('manage-list');area.replaceChildren();if(!rows.length)area.append(el('p','这里暂时没有内容。','muted'));
    for(const item of rows){const row=el('div',undefined,'manage-row');row.append(el('strong',item.title||'未命名'));const actions=el('div',undefined,'row-actions');
      const button=(label,fn)=>{const b=el('button',label,'quiet');b.onclick=manageAct(async()=>{b.disabled=true;try{await fn();await reloadWorkspace();await renderManager();}finally{b.disabled=false}});actions.append(b);};
      if(filter==='active')button('归档',()=>markItem(item,'archived'));
      else button('恢复',async()=>{await native('restore_entity',{entity_type:item.entity_type,entity_id:item.entity_id,expected_revision:item.revision});});
      if(filter!=='trashed')button('移入回收站',async()=>{if(await confirmAction('移入回收站',`“${item.title||'未命名'}”将从工作区隐藏，可以从回收站恢复。`))await markItem(item,'trashed');});
      else button('彻底删除',async()=>{if(!await confirmAction('彻底删除',`永久删除“${item.title||'未命名'}”${kind==='project'?'及其中所有对话':''}。相关执行将停止，消息和关联计算记录将被移除。已导出的文件和历史备份不受影响。`,true))return;await native('purge_entity',{entity_type:kind,entity_id:item.entity_id,expected_revision:item.revision,confirm_id:item.entity_id});for(const id of [item.entity_id,...(item.snapshot?.member_session_ids||[])])drafts.delete(id);home();});
      row.append(actions);area.append(row);
    }
  }
  async function markItem(item,visibility){const record={entity_type:item.entity_type,entity_id:item.entity_id,title:(item.title||'').slice(0,160),state:visibility};if(item.entity_type==='project'){const members=await allFrames(item.entity_id);record.snapshot={snapshot_version:1,member_session_ids:members.map(f=>f.id)};}await native('mark_entity',record);if(state.frame&&(item.entity_id===state.frame.id||item.entity_id===state.frame.project_id))home();}
  $('manage-items').onclick=manageAct(async()=>{closeProjectPop();await manageItems();});$('manage-close').onclick=()=>$('manage-dialog').close();$('manage-kind').onchange=manageAct(renderManager);$('manage-state').onchange=manageAct(renderManager);
  $('return-start').onclick=act(async()=>{if($('message-input').value.trim()&&!await confirmAction('返回主页面','未发送的草稿不会带到主页面。确认返回？'))return;await native('return_to_start');});

  const effortMemory=new Map();
  function effortKey(){return state.frame?.id+':'+state.binding?.native_profile_id;}
  function renderEffort(){const select=$('effort-select'),key=effortKey();let chosen=effortMemory.get(key);if(!chosen){try{chosen=localStorage.getItem('leo-effort:'+key);}catch(_){}}const choices=state.binding?.reasoning?.choices||[];if(!choices.some(c=>c.id===chosen&&c.available))chosen='default';select.replaceChildren();for(const c of choices.filter(c=>c.available)){const nativeLabel=c.native_value&&typeof c.native_value==='string'?c.native_value:c.label||c.id;const o=el('option',c.id==='default'?'思考强度 · 默认':'思考强度 · '+nativeLabel);o.value=c.id;o.title=c.semantics||'';select.append(o);}if(!choices.length){const o=el('option','思考强度 · 默认');o.value='default';select.append(o);}select.value=chosen;select.disabled=!!state.execution;effortMemory.set(key,chosen);}
  $('effort-select').onchange=()=>{const key=effortKey(),value=$('effort-select').value;effortMemory.set(key,value);try{localStorage.setItem('leo-effort:'+key,value);}catch(_){}};

  function editModel(id){const p=(shellState.profiles||[]).find(p=>p.id===id);$('wb-profile').value=p?.id||'';$('wb-name').value=p?.name||'';$('wb-preset').value=p?.preset||shellState.presets?.[0]?.id||'';const preset=(shellState.presets||[]).find(x=>x.id===$('wb-preset').value)||{};$('wb-model').value=p?.model||preset.model||'';$('wb-base').value=p?.base_url||preset.base_url||'';$('wb-key').value='';$('wb-delete').disabled=!p;syncWorkbenchPreset(false);}
  function syncWorkbenchPreset(reset){const p=(shellState.presets||[]).find(x=>x.id===$('wb-preset').value)||{};if(reset){$('wb-model').value=p.model||'';$('wb-base').value=p.base_url||'';}const local=p.id==='local-qwen';$('wb-model').readOnly=local;$('wb-base').readOnly=local||p.editable_base_url===false;$('wb-key-label').hidden=local;}
  async function modelEditor(){shellState=await native('get_state');const select=$('wb-profile');select.replaceChildren();const empty=el('option','＋ 新建模型配置');empty.value='';select.append(empty);for(const p of shellState.profiles||[]){const o=el('option',p.name);o.value=p.id;select.append(o);}const preset=$('wb-preset');preset.replaceChildren();for(const p of shellState.presets||[]){const o=el('option',p.label);o.value=p.id;preset.append(o);}$('model-editor').hidden=false;editModel(shellState.active_profile_id||'');}
  const modelAct=fn=>async e=>{e?.preventDefault();try{$('settings-status').textContent='';await fn();}catch(err){$('settings-status').textContent=errorText[err.message]||err.message;}};
  $('configure-models').onclick=modelAct(modelEditor);$('wb-profile').onchange=()=>editModel($('wb-profile').value);$('wb-preset').onchange=()=>syncWorkbenchPreset(true);
  $('wb-model-form').onsubmit=modelAct(async()=>{await native('save_profile',{profile_id:$('wb-profile').value||null,name:$('wb-name').value,preset:$('wb-preset').value,model:$('wb-model').value,base_url:$('wb-base').value,api_key:$('wb-key-label').hidden?'':$('wb-key').value,activate:false});$('wb-key').value='';await modelEditor();if(state.frame)await refreshModels();$('settings-status').textContent='已保存。可在对话输入框选择此模型。';});
  $('wb-delete').onclick=modelAct(async()=>{const id=$('wb-profile').value;if(!id||!await confirmAction('删除模型配置','将移除此配置及已保存的密钥。历史消息会保留。'))return;await native('delete_profile',{profile_id:id});await modelEditor();if(state.frame)await refreshModels();$('settings-status').textContent='配置已删除。';});

  // Personal profile, declarative appearance and application menus.
  Object.assign(errorText,{ACCOUNT_LOGIN_REQUIRED:'请先登录再修改个人资料。',ACCOUNT_PROFILE_INVALID:'用户名需为 1–60 字，简介最多 500 字。',ACCOUNT_AVATAR_INVALID:'头像格式不正确，请重新选择图片。',ACCOUNT_PASSWORD_INVALID:'密码需为 10–256 位。',ACCOUNT_EMAIL_INVALID:'请输入有效邮箱。',ACCOUNT_EXISTS:'这个邮箱已经注册，请登录。',ACCOUNT_CREDENTIALS_INVALID:'邮箱、密码或恢复码不正确。',ACCOUNT_RETRY_LATER:'尝试次数较多，请一分钟后重试。',ACCOUNT_UNAVAILABLE:'暂时无法读取本地账号，请重试。',THEME_INVALID:'主题格式不正确，请参考下载的 JSON 模板。',THEME_CONTRAST_LOW:'文字与背景对比度不足，请调整配色后重试。',THEME_UNAVAILABLE:'主题设置暂时无法保存，请重试。',CLIPBOARD_UNAVAILABLE:'暂时无法读取剪贴板，可使用 Ctrl V 粘贴。',CLIPBOARD_BUSY:'剪贴板正被其他程序占用，请稍后重试或使用 Ctrl V 粘贴。',CLIPBOARD_TEXT_INVALID:'剪贴板内容过大或不是文本，请缩短后重试。'});
  let personal=null,authMode='login',avatarDraft='',profileBusy=false;
  function avatarInto(node,account){node.replaceChildren();if(account?.avatar?.startsWith('data:image/png;base64,')){const img=el('img');img.src=account.avatar;img.alt='';node.append(img);}else node.textContent=(account?.display_name||account?.email||'○').slice(0,1).toUpperCase();}
  function identity(){avatarInto($('identity-avatar'),personal);$('identity-name').textContent=personal?.display_name||personal?.email?.split('@')[0]||'访客';$('identity-bio').textContent=personal?(personal.bio||'个人资料与账号'):'登录 / 注册';}
  async function refreshIdentity(){personal=(await native('account_request',{operation:'state'})).account;identity();}
  function profileView(){const signed=!!personal;$('profile-auth').hidden=signed;$('profile-form').hidden=!signed;$('profile-title').textContent=signed?'个人资料':authMode==='register'?'注册本地账号':authMode==='reset'?'找回本地账号':'登录本地账号';if(signed){$('profile-name').value=personal.display_name||personal.email.split('@')[0];$('profile-bio').value=personal.bio||'';avatarDraft=personal.avatar||'';avatarInto($('profile-avatar'),personal);$('profile-account-email').textContent=personal.email;}else{$('profile-confirm-label').hidden=authMode==='login';$('profile-confirm').required=authMode!=='login';$('profile-recovery-label').hidden=authMode!=='reset';$('profile-recovery').required=authMode==='reset';$('profile-password').autocomplete=authMode==='login'?'current-password':'new-password';$('profile-auth-submit').textContent={login:'登录',register:'注册',reset:'重置密码'}[authMode];}for(const b of document.querySelectorAll('[data-auth-mode]'))b.classList.toggle('selected',b.dataset.authMode===authMode);}
  async function openProfile(){await refreshIdentity();$('profile-status').textContent='';profileView();$('profile-dialog').showModal();}
  const profileAction=fn=>async event=>{event?.preventDefault();if(profileBusy)return;profileBusy=true;const controls=[...$('profile-dialog').querySelectorAll('button,input,textarea')];for(const c of controls)c.disabled=true;try{$('profile-status').textContent='';await fn();}catch(e){$('profile-status').textContent=errorText[e.message]||e.message;}finally{profileBusy=false;for(const c of controls)c.disabled=false;}};
  $('profile-button').onclick=act(openProfile);$('profile-close').onclick=()=>$('profile-dialog').close();
  for(const b of document.querySelectorAll('[data-auth-mode]'))b.onclick=()=>{authMode=b.dataset.authMode;$('profile-auth-form').reset();$('profile-status').textContent='';profileView();};
  $('profile-auth-form').onsubmit=profileAction(async()=>{if(authMode!=='login'&&$('profile-password').value!==$('profile-confirm').value)throw Error('两次密码不一致。');const r=await native('account_request',{operation:authMode,email:$('profile-email').value,password:$('profile-password').value,recovery_code:$('profile-recovery').value});personal=r.account;$('profile-auth-form').reset();identity();profileView();if(r.recovery_code){$('profile-issued-code').hidden=false;$('profile-issued-code').textContent='请保存恢复码，仅显示一次：\n'+r.recovery_code;}$('profile-status').textContent='已登录，可以完善个人资料。';});
  $('profile-form').onsubmit=profileAction(async()=>{const r=await native('account_request',{operation:'update_profile',display_name:$('profile-name').value,bio:$('profile-bio').value,avatar:avatarDraft});personal=r.account;identity();$('profile-status').textContent='个人资料已保存。';});
  $('profile-logout').onclick=profileAction(async()=>{await native('account_request',{operation:'logout'});personal=null;avatarDraft='';identity();authMode='login';$('profile-form').reset();$('profile-auth-form').reset();$('profile-issued-code').textContent='';$('profile-issued-code').hidden=true;profileView();});
  $('profile-dialog').addEventListener('cancel',e=>{if(profileBusy)e.preventDefault();});
  $('profile-dialog').addEventListener('close',()=>{$('profile-auth-form').reset();$('profile-issued-code').textContent='';$('profile-issued-code').hidden=true;$('profile-avatar-file').value='';avatarDraft='';});
  $('profile-avatar-file').onchange=profileAction(async()=>{const file=$('profile-avatar-file').files[0];if(!file)return;if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>5*1024*1024)throw Error('请选择不超过 5 MB 的 PNG、JPEG 或 WebP 图片。');const bitmap=await createImageBitmap(file);try{const canvas=document.createElement('canvas');canvas.width=256;canvas.height=256;const side=Math.min(bitmap.width,bitmap.height);canvas.getContext('2d').drawImage(bitmap,(bitmap.width-side)/2,(bitmap.height-side)/2,side,side,0,0,256,256);const url=canvas.toDataURL('image/png');if(url.length>350000)throw Error('头像文件过大，请选择更简单的图片。');avatarDraft=url;avatarInto($('profile-avatar'),{...personal,avatar:url});}finally{bitmap.close();$('profile-avatar-file').value='';}});
  $('profile-avatar-clear').onclick=()=>{avatarDraft='';avatarInto($('profile-avatar'),{...personal,avatar:''});};

  let preferences={mode:'system',theme:null},pendingTheme=null;
  const customProps=['paper','paper-2','surface','surface-2','ink','ink-2','muted','faint','accent','accent-strong','accent-soft','accent-wash','on-accent','rail','rail-2','rail-ink','rail-muted','rail-mark','bg','text','text-2'];
  const sampleTheme={name:'静谧纸页',colors:{paper:'#F2E8D8',surface:'#FAF4E9',ink:'#30271F',accent:'#9C3A28',rail:'#2E251D',rail_ink:'#EFE4D2'}};
  function applyPreferences(value){const root=document.documentElement;root.dataset.leoMode=value.mode;for(const k of customProps)root.style.removeProperty('--'+k);if(value.theme){const c=value.theme.colors;const rgb=c.accent.slice(1).match(/../g).map(h=>parseInt(h,16)/255);const lum=rgb.map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((n,x,i)=>n+x*[.2126,.7152,.0722][i],0);const values={paper:c.paper,'paper-2':c.surface,surface:c.surface,'surface-2':c.paper,ink:c.ink,'ink-2':c.ink,muted:c.ink,faint:c.ink,accent:c.accent,'accent-strong':c.accent,'accent-soft':c.accent,'accent-wash':c.surface,'on-accent':lum>.179?'#000000':'#FFFFFF',rail:c.rail,'rail-2':c.rail,'rail-ink':c.rail_ink,'rail-muted':c.rail_ink,'rail-mark':c.rail_ink};for(const [k,v]of Object.entries(values))root.style.setProperty('--'+k,v);}}
  async function refreshPreferences(){preferences=(await native('workspace_preferences',{operation:'get'})).preferences;applyPreferences(preferences);}
  function selectSettingsTab(tab){for(const b of document.querySelectorAll('[data-settings-tab]'))b.setAttribute('aria-selected',String(b.dataset.settingsTab===tab));for(const p of document.querySelectorAll('[data-settings-pane]'))p.hidden=p.dataset.settingsPane!==tab;if(tab==='appearance')act(loadAppearance)();$('settings-dialog').scrollTop=0;}
  for(const b of document.querySelectorAll('[data-settings-tab]'))b.onclick=()=>selectSettingsTab(b.dataset.settingsTab);
  async function loadAppearance(){try{shellState=await native('get_state');await refreshPreferences();$('appearance-mode').value=preferences.mode;const select=$('appearance-theme');select.replaceChildren();for(const [id,label]of [['ink-autumn','淡墨浓秋'],['deep-sea-molten-orange','深海熔橙'],['amethyst-teal','紫晶青绿']]){const o=el('option',label);o.value=id;select.append(o);}if(preferences.theme){const o=el('option',preferences.theme.name+'（自定义）');o.value='custom';select.append(o);}select.value=preferences.theme?'custom':shellState.appearance?.theme||'ink-autumn';$('appearance-status').textContent='';}catch(e){$('appearance-status').textContent=errorText[e.message]||e.message;}}
  const appearanceAction=fn=>async()=>{try{$('appearance-status').textContent='';await fn();}catch(e){$('appearance-status').textContent=errorText[e.message]||e.message;}};
  $('appearance-save').onclick=appearanceAction(async()=>{const theme=$('appearance-theme').value;if(theme!=='custom'){await native('save_appearance',{theme,locale:shellState?.appearance?.locale||'zh'});document.documentElement.dataset.leoTheme=theme;}preferences=(await native('workspace_preferences',{operation:'save',mode:$('appearance-mode').value,theme:theme==='custom'?preferences.theme:null})).preferences;applyPreferences(preferences);$('appearance-status').textContent='外观已保存。';});
  function download(name,text,mime){const url=URL.createObjectURL(new Blob([text],{type:mime}));const a=el('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);}
  $('theme-template').onclick=()=>download('leo-theme.json',JSON.stringify(sampleTheme,null,2),'application/json');
  $('custom-theme-upload').onclick=()=>$('custom-theme-file').click();
  async function previewTheme(value){const r=await native('workspace_preferences',{operation:'validate',theme:value});pendingTheme=r.theme;applyPreferences({...preferences,theme:pendingTheme});$('theme-preview-title').textContent='预览 · '+pendingTheme.name;$('theme-preview-status').textContent='';$('theme-preview-dialog').showModal();}
  $('custom-theme-file').onchange=appearanceAction(async()=>{const file=$('custom-theme-file').files[0];try{if(!file)return;if(file.size>8192)throw Error('主题文件最多 8 KB。');let value;try{value=JSON.parse(await file.text());}catch(_){throw Error('THEME_INVALID');}await previewTheme(value);}finally{$('custom-theme-file').value='';}});
  for(const id of ['theme-preview-close','theme-preview-cancel'])$(id).onclick=()=>$('theme-preview-dialog').close();
  $('theme-preview-dialog').addEventListener('close',()=>{pendingTheme=null;applyPreferences(preferences);});
  $('theme-preview-apply').onclick=async()=>{if(!pendingTheme)return;$('theme-preview-apply').disabled=true;try{preferences=(await native('workspace_preferences',{operation:'save',mode:preferences.mode,theme:pendingTheme})).preferences;$('theme-preview-dialog').close();applyPreferences(preferences);if($('settings-dialog').open)await loadAppearance();}catch(e){$('theme-preview-status').textContent=errorText[e.message]||e.message;}finally{$('theme-preview-apply').disabled=false;}};
  $('theme-conversation').onclick=appearanceAction(async()=>{const wish=$('theme-prompt').value.trim()||'温暖、安静、适合长时间阅读';$('settings-dialog').close();await newFrame();if(!state.frame)return;$('message-input').value='请为 Leo AI Studio 设计一个主题：'+wish+'。只输出一个 JSON 代码块，格式严格参考：\n'+JSON.stringify(sampleTheme,null,2)+'\n只允许 name 和 colors 两个字段，colors 只包含这六个颜色，使用 #RRGGBB。正文对 paper 和 surface 的对比度、侧栏文字对 rail 的对比度均至少 4.5:1。不要输出 CSS、HTML 或外部链接。';$('message-input').focus();notice('主题需求已放入新对话，请核对后发送。');});
  function themeFromMessage(content){if(typeof content!=='string'||content.length>50000)return null;const candidates=[content,...Array.from(content.matchAll(/```(?:json)?\s*([\s\S]*?)```/g),m=>m[1])];for(const text of candidates){try{const value=JSON.parse(text.trim());const keys=Object.keys(sampleTheme.colors);if(value&&typeof value.name==='string'&&value.colors&&keys.every(k=>/^#[0-9a-fA-F]{6}$/.test(value.colors[k]||'')))return {name:value.name,colors:Object.fromEntries(keys.map(k=>[k,value.colors[k]]))};}catch(_){}}return null;}

  let editTarget=null,editSelection=null,textScale=1;
  function setTextScale(next){textScale=Math.round(Math.min(1.5,Math.max(.85,next))*100)/100;document.documentElement.style.setProperty('--text-scale',String(textScale));}
  function captureEdit(){const target=document.activeElement;editTarget=target?.matches('input:not([type=file]),textarea')?target:null;editSelection=editTarget?{start:editTarget.selectionStart,end:editTarget.selectionEnd,value:editTarget.value}:null;}
  const menuGroups=[...document.querySelectorAll('.menu-group')];
  function closeMenus(){for(const g of menuGroups){g.querySelector('[role=menu]').hidden=true;g.firstElementChild.setAttribute('aria-expanded','false');}}
  function openMenu(g){closeMenus();g.querySelector('[role=menu]').hidden=false;g.firstElementChild.setAttribute('aria-expanded','true');const editable=editTarget&&!editTarget.disabled&&!editTarget.readOnly&&typeof editSelection?.start==='number';for(const b of g.querySelectorAll('[data-edit]')){const op=b.dataset.edit;b.disabled=!editable&&op!=='copy';if(['copy','cut'].includes(op))b.disabled=editTarget?.type==='password'||!(editSelection?.end>editSelection?.start||window.getSelection()?.toString());}g.querySelector('[data-command=export]')?.toggleAttribute('disabled',!state.frame);}
  for(const g of menuGroups){const trigger=g.firstElementChild;trigger.onpointerdown=e=>{captureEdit();e.preventDefault();};trigger.onclick=()=>g.querySelector('[role=menu]').hidden?openMenu(g):closeMenus();trigger.onkeydown=e=>{if(['ArrowDown','Enter',' '].includes(e.key)){e.preventDefault();captureEdit();openMenu(g);g.querySelector('[role=menu] button:not(:disabled)')?.focus();}};}
  document.addEventListener('pointerdown',e=>{if(!e.target.closest('.desktop-menu'))closeMenus();});
  document.querySelector('.desktop-menu').addEventListener('keydown',e=>{const g=e.target.closest('.menu-group');if(!g)return;if(e.key==='Escape'){closeMenus();g.firstElementChild.focus();e.preventDefault();}else if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)&&e.target.closest('[role=menu]')){const items=[...g.querySelectorAll('[role=menu] button:not(:disabled)')],i=items.indexOf(e.target);items[e.key==='Home'?0:e.key==='End'?items.length-1:(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length]?.focus();e.preventDefault();}else if(['ArrowLeft','ArrowRight'].includes(e.key)){const next=menuGroups[(menuGroups.indexOf(g)+(e.key==='ArrowRight'?1:-1)+menuGroups.length)%menuGroups.length];openMenu(next);next.querySelector('[role=menu] button:not(:disabled)')?.focus();e.preventDefault();}});
  for(const b of document.querySelectorAll('[data-edit]'))b.onclick=act(async()=>{const operation=b.dataset.edit,target=editTarget,range=editSelection;const selected=target&&range?target.value.slice(range.start,range.end):window.getSelection()?.toString()||'';closeMenus();if(operation==='copy'){if(target?.type!=='password')await copyText(selected);return;}if(!target||target.disabled||target.readOnly||typeof range?.start!=='number')return;if(target.value!==range.value)throw Error('输入内容已变化，请重新选择。');target.focus();target.setSelectionRange(range.start,range.end);if(operation==='selectAll'){target.select();return;}if(operation==='paste'){const r=await native('paste_text');if(target.value!==range.value)throw Error('输入内容已变化，请重新粘贴。');target.focus();target.setSelectionRange(range.start,range.end);document.execCommand('insertText',false,r.text||'');}else if(operation==='cut'){if(target.type==='password')return;await copyText(selected);if(target.value!==range.value)throw Error('输入内容已变化，请重新选择。');target.focus();target.setSelectionRange(range.start,range.end);document.execCommand('delete');}else document.execCommand(operation);});
  function toggleSidebar(){document.body.classList.toggle('sidebar-collapsed');$('sidebar-toggle').setAttribute('aria-expanded',String(!document.body.classList.contains('sidebar-collapsed')));}
  $('sidebar-toggle').onclick=toggleSidebar;
  async function exportConversation(){const frame=state.frame;if(!frame)throw Error('请先打开一个对话。');let before=null,messages=[],seen=new Set();do{const r=await request('messages',{frameId:frame.id,...(before?{before}:{})});messages.push(...r.messages||[]);if(!r.has_earlier)break;before=r.next_before_seq;if(before===null||before===undefined||seen.has(before))throw Error('消息分页未完成，请重试。');seen.add(before);}while(true);const unique=[...new Map(messages.map(m=>[m.message_id||m.seq,m])).values()].sort((a,b)=>a.seq-b.seq);const text='# '+title(frame)+'\n\n'+displayMessages(unique).filter(m=>['user','assistant'].includes(m.role)).map(m=>'## '+(m.role==='user'?'你':'Leo AI')+'\n\n'+plainText(m.content)).join('\n\n');download('leo-conversation.md',text,'text/markdown;charset=utf-8');}
  const commands={new:()=>newFrame(),project:()=>$('new-project').click(),export:exportConversation,'import-theme':async()=>{await settings();selectSettingsTab('appearance');$('custom-theme-file').click();},home:()=>$('return-start').click(),search:()=>{document.body.classList.remove('sidebar-collapsed');$('sidebar-toggle').setAttribute('aria-expanded','true');$('history-search').focus();},sidebar:toggleSidebar,'zoom-in':()=>setTextScale(textScale+.1),'zoom-out':()=>setTextScale(textScale-.1),'zoom-reset':()=>setTextScale(1),appearance:async()=>{await settings();selectSettingsTab('appearance');},about:async()=>{await settings();selectSettingsTab('about');},guide:()=>$('help-dialog').showModal()};
  for(const b of document.querySelectorAll('[data-command]'))b.onclick=act(async()=>{closeMenus();await commands[b.dataset.command]();});
  $('help-close').onclick=()=>$('help-dialog').close();
  $('artifact-close').onclick=()=>$('artifact-dialog').close();

  /* 2.2.7 · Approval mode per conversation, and the tool calls the daemon is waiting on.
     The daemon gates tool calls; Leo shows each pending request and answers it. Research
     confirmations are native dialogs and never pass through here. */
  Object.assign(errorText,{WORKBENCH_SCHEDULE_TIME_PASSED:'这个时间已经过去了，请选一个将来的时间。',WORKBENCH_SCHEDULE_TIME_INVALID:'请填写有效的日期和时间。',
    WORKBENCH_SCHEDULE_TEXT_INVALID:'请填写到点要发送的消息（不超过 8000 字）。',WORKBENCH_SCHEDULE_LIMIT:'定时任务已达上限（100 个），请先删除不用的任务。',
    WORKBENCH_INVALID_REQUEST:'请求内容无效，请检查后重试。'});
  const MODE_LABEL={off:'Off',smart:'Smart',auto:'Auto'};
  const approval={frame:null,mode:'smart',pending:[],auto:[]};
  const TOOL_NAMES={bash:'运行一条命令行',exec_background:'启动一个后台进程',write_file:'写入一个文件',edit_file:'修改一个文件',read_file:'读取一个文件',
    glob:'查找文件',grep:'搜索文件内容',list_dir:'列出目录',mcp_call:'调用外部工具',mcp_resource_read:'读取外部工具资源',mcp_prompt_get:'读取外部工具提示',
    credentials_set:'写入一项凭据',skills_edit:'修改技能',skills_delete:'删除技能',skills_publish:'发布技能',skills_rollback:'回滚技能',web_fetch:'打开网页',
    web_search:'联网搜索',web_download:'下载文件',request_network_access:'申请联网',env_setup:'配置计算环境',delegate:'把任务交给子助手',save_artifact:'保存结果文件'};
  // The daemon's side-effect classes (openai4s/tools/taxonomy.py), in plain words.
  const SIDE_EFFECTS={read_only:'只读，不改动任何东西',workspace_write:'会改写工作区里的文件',runtime_mutation:'会改变计算环境或启动进程',
    external_write:'会向外部服务写入或发送数据',high_risk:'高风险操作'};
  function renderMode(){$('approval-label').textContent=MODE_LABEL[approval.mode]||'Smart';$('approval-button').classList[approval.mode==='auto'?'add':'remove']('auto');
    for(const o of document.querySelectorAll('#approval-pop [data-mode]')){const on=o.dataset.mode===approval.mode;o.classList[on?'add':'remove']('on');o.setAttribute('aria-checked',String(on));o.querySelector('em').textContent=on?'✓':'';}}
  async function loadMode(frame){approval.frame=frame.id;approval.mode='smart';approval.pending=[];approval.auto=[];renderMode();renderApprovals();
    try{const r=await request('approval_mode',{frameId:frame.id});if(approval.frame===frame.id){approval.mode=r.mode;renderMode();}}
    catch(e){if(approval.frame===frame.id)notice('审批模式暂时没有写入工作区（'+e.message+'），下次打开对话时会重试。');}}
  function closeApprovalPop(){$('approval-pop').hidden=true;$('approval-button').setAttribute('aria-expanded','false');}
  function confirmAuto(){const d=$('auto-dialog');$('auto-understood').checked=false;$('auto-accept').disabled=true;d.returnValue='';d.showModal();
    return new Promise(resolve=>d.addEventListener('close',()=>resolve(d.returnValue==='confirm'),{once:true}));}
  async function chooseMode(mode){closeApprovalPop();if(!state.frame||mode===approval.mode)return;if(mode==='auto'&&!await confirmAuto())return;
    const fid=state.frame.id;const r=await request('approval_set_mode',{frameId:fid,mode});if(state.frame?.id===fid){approval.mode=r.mode;renderMode();}}
  function standingPattern(r){const c=(r.patterns||[]).filter(p=>p&&p!=='*');return c.length?c[c.length-1]:(r.target||'*');}
  function renderApprovals(){const box=$('approvals');box.replaceChildren();
    for(const r of approval.pending){
      const card=el('section',undefined,'approval-card'+(r.dangerous?' dangerous':''));card.setAttribute('role','alertdialog');
      const head=el('header');head.append(el('strong','Leo 想'+(TOOL_NAMES[r.tool]||('使用「'+r.tool+'」'))),el('span','· 需要你的同意才会继续'),
        el('span',(MODE_LABEL[approval.mode]||'')+' 模式'+(r.dangerous?' · 高风险操作':''),'tag'));card.append(head);
      const body=el('div',undefined,'approval-body');
      if(r.title&&r.title!==r.tool)body.append(el('p',r.title,'approval-title'));
      if(r.target||r.input)body.append(el('pre',r.target||r.input));
      const dl=el('dl');const row=(k,v)=>{if(v){dl.append(el('dt',k),el('dd',v));}};
      row('操作类型',r.tool);row('影响',SIDE_EFFECTS[r.sideEffect]||r.sideEffect);row('来源',r.subAgent?'子助手':'');row('说明',r.reason);body.append(dl);card.append(body);
      const acts=el('div',undefined,'approval-actions');
      const once=el('button','允许这一次','primary');once.onclick=act(()=>decide(r,true,'once'));
      const pattern=standingPattern(r);const always=el('button','本对话内都允许同类操作','quiet');always.title='允许范围：'+pattern;always.onclick=act(()=>decide(r,true,'conversation'));
      const deny=el('button','拒绝','quiet deny');deny.onclick=act(()=>decide(r,false,'once'));acts.append(once,always,deny);card.append(acts);
      const left=Math.max(0,Math.ceil((r.expiresAt*1000-Date.now())/60000));
      card.append(el('p','约 '+left+' 分钟内未处理将自动拒绝，对话会继续并说明被拒绝的原因。','approval-timer'));box.append(card);}
  }
  async function decide(r,allow,scope){const fid=approval.frame;await request('approval_decide',{frameId:fid,decisionId:r.decisionId,allow,scope});
    approval.pending=approval.pending.filter(x=>x.decisionId!==r.decisionId);renderApprovals();if(state.frame?.id===fid)await refreshChat();}
  async function refreshApprovals(fid){if(approval.frame!==fid)return;try{const r=await request('approvals',{frameId:fid});if(approval.frame!==fid)return;
    const next=r.requests||[];if(JSON.stringify(next)!==JSON.stringify(approval.pending)){approval.pending=next;renderApprovals();}const auto=r.autoApproved||[];if(JSON.stringify(auto)!==JSON.stringify(approval.auto)){approval.auto=auto;renderMessages();}}catch(_){}}

  /* 2.2.7 · Scheduled messages: at a chosen minute Leo sends a prepared message into a conversation,
     only while it is open. Missed times are shown, never sent on their own. */
  const sched={items:[],history:[],editing:null,repeat:'once',timer:null};
  const REPEAT_TEXT={once:'仅一次',daily:'每天',weekdays:'每个工作日',weekly:'每周'};
  const RUN_STATUS={sent:['已完成','ok'],sent_late:['已补发','ok'],missed:['已错过','miss'],failed:['发送失败','bad'],sending:['发送中',''],dismissed:['已忽略','']};
  const pad=n=>String(n).padStart(2,'0');
  function localDate(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
  function whenParts(stamp,repeat){if(!stamp)return ['—',REPEAT_TEXT[repeat]||''];const d=new Date(stamp);const today=new Date();today.setHours(0,0,0,0);
    const day=new Date(d);day.setHours(0,0,0,0);const diff=Math.round((day-today)/864e5);
    const dayText=diff===0?'今天':diff===1?'明天':diff===-1?'昨天':(d.getMonth()+1)+'月'+d.getDate()+'日';
    const repeatText=repeat==='weekly'?'每周'+'日一二三四五六'[d.getDay()]:REPEAT_TEXT[repeat]||'';
    return [pad(d.getHours())+':'+pad(d.getMinutes()),repeat?dayText+' · '+repeatText:dayText];}
  function chip(text,kind){return el('span',text,'sched-chip'+(kind?' '+kind:''));}
  function scheduleRow(item){const row=el('div',undefined,'sched-item'+(item.enabled?'':' paused'));
    const [clock,sub]=whenParts(item.nextRun||item.date+'T'+item.time,item.repeat);const when=el('div',undefined,'sched-when');when.append(el('b',clock),el('small',item.enabled?sub:(item.repeat==='weekly'?'每周'+'日一二三四五六'[new Date(item.date+'T00:00').getDay()]:REPEAT_TEXT[item.repeat])));
    const what=el('div',undefined,'sched-what');what.append(el('strong',item.frameName),el('p','「'+item.text+'」'));
    const meta=el('div',undefined,'sched-meta');meta.append(chip(item.enabled?'已启用':'已暂停',item.enabled?'ok':''),chip('发往：'+item.frameName));what.append(meta);
    const ops=el('div',undefined,'sched-ops');
    const toggle=el('button',item.enabled?'暂停':'继续','quiet');toggle.onclick=act(async()=>{await request('schedule_toggle',{id:item.id,enabled:!item.enabled});await loadSchedules();});
    const edit=el('button','编辑','quiet');edit.onclick=act(()=>openScheduleDialog(item));
    const del=el('button','删除','quiet deny');del.onclick=act(async()=>{if(!await confirmAction('删除定时任务','「'+item.frameName+'」的这个定时任务将被删除，已发送的消息不受影响。'))return;await request('schedule_delete',{id:item.id});await loadSchedules();});
    ops.append(toggle,edit,del);row.append(when,what,ops);return row;}
  function historyRow(h){const [label,kind]=RUN_STATUS[h.status]||[h.status,''];const row=el('div',undefined,'sched-item'+(h.status==='missed'?' missed':h.status==='failed'?' failed':''));
    const [clock,sub]=whenParts(h.due);const when=el('div',undefined,'sched-when');when.append(el('b',clock),el('small',sub));
    const what=el('div',undefined,'sched-what');what.append(el('strong',h.frameName));
    const text={missed:'Leo 当时没有打开，这一次没有发送。',failed:'没有发出'+(h.detail?'（'+(errorText[h.detail]||h.detail)+'）':'')+'。',sent:'已发送。',sent_late:'已由你手动补发。',sending:'正在发送。',dismissed:'已忽略这一次。'}[h.status]||'';
    what.append(el('p',text));const meta=el('div',undefined,'sched-meta');meta.append(chip(label,kind));what.append(meta);
    const ops=el('div',undefined,'sched-ops');
    if(['missed','failed'].includes(h.status)){const now=el('button','现在发送','quiet');now.onclick=act(async()=>{await request('schedule_send_now',{recordId:h.id});await loadSchedules();});
      const skip=el('button','忽略','quiet');skip.onclick=act(async()=>{await request('schedule_dismiss',{recordId:h.id});await loadSchedules();});ops.append(now,skip);}
    else if(['sent','sent_late'].includes(h.status)){const open=el('button','打开对话','quiet');open.onclick=act(async()=>{const f=state.frames.find(x=>x.id===h.frameId);if(!f)throw Error('这个对话已不在当前列表中。');await openFrame(f);});ops.append(open);}
    row.append(when,what,ops);return row;}
  function renderSchedules(){const list=$('schedule-list'),hist=$('schedule-history');list.replaceChildren();hist.replaceChildren();
    for(const item of sched.items)list.append(scheduleRow(item));if(!sched.items.length)list.append(el('p','还没有定时任务。点「新建定时任务」，选一个对话、写好消息、定好时间。','muted sched-empty'));
    for(const h of sched.history)hist.append(historyRow(h));if(!sched.history.length)hist.append(el('p','还没有执行记录。','muted sched-empty'));
    const active=sched.items.filter(i=>i.enabled).length;$('schedule-badge').hidden=!active;$('schedule-badge').textContent=String(active);}
  async function loadSchedules(){const r=await request('schedules');sched.items=r.items||[];sched.history=r.history||[];renderSchedules();}
  async function openSchedules(){keepDraft();state.epoch++;nb.epoch++;clearTimeout(poll);state.frame=null;approval.frame=null;show('schedule-view');updateHeader();renderHistory();await loadSchedules();
    clearInterval(sched.timer);sched.timer=setInterval(()=>{if(current==='schedule-view')loadSchedules().catch(()=>{});else clearInterval(sched.timer);},30000);}
  function setRepeat(value){sched.repeat=value;for(const b of document.querySelectorAll('#schedule-repeat [data-repeat]')){const on=b.dataset.repeat===value;b.classList[on?'add':'remove']('on');b.setAttribute('aria-checked',String(on));}}
  function openScheduleDialog(item){const frames=state.frames.filter(f=>!hiddenIds.has(f.id)&&!hiddenIds.has(f.project_id));
    if(!frames.length)throw Error('请先新建一个对话，再为它设定时任务。');
    const select=$('schedule-frame');select.replaceChildren(...frames.map(f=>{const o=el('option',title(f));o.value=f.id;return o;}));
    const soon=new Date(Date.now()+10*60000);sched.editing=item||null;$('schedule-dialog-title').textContent=item?'编辑定时任务':'新建定时任务';
    select.value=item?.frameId||state.frame?.id||frames[0].id;if(item&&select.value!==item.frameId){const o=el('option',item.frameName);o.value=item.frameId;select.append(o);select.value=item.frameId;}
    $('schedule-text').value=item?.text||'';$('schedule-date').value=item?.date||localDate(soon);$('schedule-time').value=item?.time||pad(soon.getHours())+':'+pad(soon.getMinutes());
    setRepeat(item?.repeat||'once');$('schedule-error').textContent='';$('schedule-hint').textContent='执行时沿用该对话的模型与审批模式；随时可以暂停、编辑或删除。';
    const d=$('schedule-dialog');d.returnValue='';d.showModal();$('schedule-text').focus();}
  async function saveSchedule(){const select=$('schedule-frame');const payload={frameId:select.value,frameName:select.selectedOptions[0]?.textContent||'',
      text:$('schedule-text').value,date:$('schedule-date').value,time:$('schedule-time').value,repeat:sched.repeat};if(sched.editing)payload.id=sched.editing.id;
    try{await request('schedule_save',payload);}catch(e){$('schedule-error').textContent=e.message;return;}
    $('schedule-dialog').close();await loadSchedules();}

  async function start(){if(started)return;started=true;applyAppearance();refreshIdentity().catch(()=>{$('identity-bio').textContent='账号暂不可用，点击重试';});try{await reloadWorkspace();$('connection').lastChild.textContent=' 工作区已连接';loadSchedules().catch(()=>{});try{const intent=(await native('appearance_intent',{operation:'take'})).intent;if(intent){await settings();selectSettingsTab('appearance');$('theme-prompt').placeholder=intent==='chat'?'描述你喜欢的风格，然后点击通过会话创建':'例如：安静的蓝色书房';}}catch(_){}}catch(e){started=false;$('connection').lastChild.textContent=' 连接未完成';notice(e.message);}}
  $('notice').querySelector('button').onclick=()=>{$('notice').hidden=true;};$('new-chat').onclick=act(newFrame);$('nav-home').onclick=home;$('brand-home').onclick=e=>{e.preventDefault();home();};$('home-button').onclick=home;
  for(const id of ['hero-research','card-research','nav-research','composer-research'])$(id).onclick=act(research);
  for(const id of ['card-tools','nav-tools'])$(id).onclick=act(()=>openNotebook());
  $('notebook-button').onclick=act(()=>openNotebook(state.frame));
  $('nb-refresh').onclick=act(()=>loadNotebook());$('nb-open-chat').onclick=act(()=>nb.frame&&openFrame(nb.frame));$('nb-switch').onclick=act(()=>openNotebook(null));
  $('card-chat').onclick=act(newFrame);$('send').onclick=act(send);$('message-input').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();act(send)();}};
  $('stop').onclick=act(async()=>{const e=state.execution;const owner=e.owner||{kind:e.owner_kind||e.kind,id:e.owner_id||e.id};await request('cancel',{frameId:state.frame.id,executionId:e.execution_id,owner});await refreshChat();});
  $('approval-button').onclick=()=>{const pop=$('approval-pop');pop.hidden=!pop.hidden;$('approval-button').setAttribute('aria-expanded',String(!pop.hidden));};
  for(const b of document.querySelectorAll('#approval-pop [data-mode]'))b.onclick=act(()=>chooseMode(b.dataset.mode));
  $('approval-pop').addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();closeApprovalPop();$('approval-button').focus();}});
  document.addEventListener('pointerdown',e=>{if(!e.target?.closest?.('.approval-picker'))closeApprovalPop();});
  $('auto-understood').onchange=()=>{$('auto-accept').disabled=!$('auto-understood').checked;};
  $('nav-schedule').onclick=act(openSchedules);$('schedule-new').onclick=act(()=>openScheduleDialog(null));
  for(const b of document.querySelectorAll('#schedule-repeat [data-repeat]'))b.onclick=()=>setRepeat(b.dataset.repeat);
  $('schedule-save').onclick=e=>{e.preventDefault();act(saveSchedule)();};
  $('model-select').onchange=act(selectModel);$('history-search').oninput=renderHistory;$('more-history').onclick=act(()=>loadFrames(true));
  $('project-select').onchange=act(()=>switchProject($('project-select').value));
  $('item-archive').onclick=act(async()=>{const item=closeItemMenu();if(!item)return;await markItem(item,'archived');await reloadWorkspace();notice(kindName(item)+'“'+item.title+'”已归档，可在「管理对话与项目 → 已归档」恢复。');});
  $('item-trash').onclick=act(async()=>{const item=closeItemMenu();if(!item)return;if(!await confirmAction('删除'+kindName(item),'“'+item.title+'”'+(item.entity_type==='project'?'及其中所有对话':'')+'将移入回收站，可以在「管理对话与项目 → 回收站」恢复，或在那里彻底删除。'))return;await markItem(item,'trashed');await reloadWorkspace();});
  $('item-menu').addEventListener('keydown',e=>{const items=[$('item-archive'),$('item-trash')],i=items.indexOf(document.activeElement);if(e.key==='Escape'){e.preventDefault();e.stopPropagation();const anchor=menuAnchor;closeItemMenu();anchor?.focus();}else if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();items[(i+1)%2].focus();}else if(e.key==='Tab')closeItemMenu();});
  $('project-switch').onclick=()=>projectPopOpen?closeProjectPop():openProjectPop();
  $('project-search').oninput=renderProjectOptions;
  $('project-pop').addEventListener('keydown',e=>{const items=[$('project-search'),...$('project-pop').querySelectorAll('button:not(:disabled)')],i=items.indexOf(document.activeElement);if(e.key==='Escape'){e.preventDefault();closeProjectPop();$('project-switch').focus();}else if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();items[(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length]?.focus();}});
  document.addEventListener('pointerdown',e=>{const t=e.target;if(!t?.closest?.('.picker'))closePickers();if(!t?.closest?.('.item-menu,.row-more'))closeItemMenu();if(!t?.closest?.('.project-switch-wrap'))closeProjectPop();});
  if(window.MutationObserver&&window.HTMLSelectElement){enhanceSelect($('model-select'),{icon:SPARK_SVG,up:true,variant:'chip'});enhanceSelect($('effort-select'),{icon:GAUGE_SVG,up:true,variant:'chip'});for(const id of ['appearance-mode','appearance-theme','wb-profile','wb-preset','manage-kind','manage-state','schedule-frame'])enhanceSelect($(id));}
  $('new-project').onclick=act(async()=>{closeProjectPop();const name=await chooseName('新建项目');if(!name)return;const p=await request('create_project',{name});state.projects.push(p);state.project=p.id||p.project_id;home();renderProjects();await loadFrames();});
  $('rename-chat').onclick=act(async()=>{const name=await chooseName('重命名对话',title(state.frame));if(!name)return;const fid=state.frame.id;await request('rename',{frameId:fid,name});if(state.frame?.id===fid)state.frame.name=name;updateHeader();await loadFrames();});
  $('earlier-messages').onclick=act(async()=>{const epoch=state.epoch;const data=await request('messages',{frameId:state.frame.id,before:state.before});if(epoch!==state.epoch)return;state.before=data.next_before_seq;$('earlier-messages').hidden=!data.has_earlier;const seen=new Map(state.messages.map(m=>[m.message_id||m.seq,m]));for(const m of data.messages||[])seen.set(m.message_id||m.seq,m);state.messages=[...seen.values()];renderMessages();});
  $('forward-close').onclick=()=>$('forward-dialog').close();$('forward-copy').onclick=act(async()=>{if(!forwarding)return;await copyText(shareText(forwarding));flash($('forward-copy'),'已复制分享文本');});
  $('settings-button').onclick=act(settings);$('close-settings').onclick=()=>$('settings-dialog').close();
  document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='n'&&!document.querySelector('dialog[open]')){e.preventDefault();act(newFrame)();}});
  window.LeoShell={openSettings:()=>act(settings)()};window.LeoWorkbench={request,session:()=>({frameId:state.frame?.id,projectId:state.project}),ready:true};
  window.setStatus=message=>notice(message);
  window.addEventListener('pywebviewready',start,{once:true});if(window.pywebview?.api)start();
  setTimeout(()=>{if(!started){notice('正在等待桌面连接。若长时间未连接，请重新打开 Leo AI Studio。');}},12000);
})();
