/* Leo owns this document. All content from models is rendered as text. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const state = {projects:[],frames:[],project:null,frame:null,binding:null,messages:[],before:null,cursor:null,execution:null,loading:false,sending:false,epoch:0,feedback:{}};
  let poll, openedAt=0, started=false, hiddenIds=new Set(), shellState;
  const drafts=new Map();
  function keepDraft(){if(state.frame)drafts.set(state.frame.id,$('message-input').value);}
  const errorText={WORKBENCH_USAGE_UNAVAILABLE:'用量信息暂时读不到（需要 WSL 中的计算后端）。',WORKBENCH_UNAVAILABLE:'暂时无法连接工作区。请返回开始页重新连接；未发送的内容仍保留在输入框中。',WORKBENCH_CONFLICT:'当前会话正在执行其他操作，请等待完成后重试。',WORKBENCH_REQUEST_FAILED:'工作区请求未完成，请稍后重试。',WORKBENCH_NOT_FOUND:'这个文件不属于当前对话，无法预览。',WORKBENCH_RESPONSE_INVALID:'工作区返回的内容无法识别，请稍后重试。',MODEL_BINDING_CONFLICT:'会话模型已变化，请重新选择。',MODEL_KEY_UNAVAILABLE:'当前模型没有可读取的密钥，请在模型设置中检查。',MODEL_CREDENTIALS_NOT_READY:'模型凭据尚未就绪，请在模型设置中检查后重试。',MODEL_REVISION_UNAVAILABLE:'会话绑定的模型配置已不可用，请重新选择已配置的模型。',MODEL_SELECTION_REQUIRED:'请先为这个会话选择已配置的模型。',REASONING_CAPABILITY_CHANGED:'模型能力已变化，请重新选择模型后发送。',START_PAGE_UNAVAILABLE:'暂时无法打开模型设置，请稍后重试。'};
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
    $('notebook-button').hidden=view!=='chat-view';$('terminal-button').hidden=view!=='chat-view';$('python-button').hidden=view!=='chat-view';$('web-button').hidden=view!=='chat-view';
    if(view!=='chat-view')closeSide();
    $('home-button').hidden=view==='home-view';
    if(view!=='notebook-view')clearTimeout(nb.timer);
  }
  function updateHeader(){const project=state.projects.find(p=>(p.id||p.project_id)===state.project);$('project-name').textContent=project?.name||'科研空间';$('page-title').textContent=current==='notebook-view'?'笔记本与计算':current==='schedule-view'?'定时任务':state.frame?title(state.frame):'工作台';$('rename-chat').hidden=!state.frame||current!=='chat-view';}
  function home(){keepDraft();state.epoch++;nb.epoch++;state.frame=null;state.messages=[];state.execution=null;clearTimeout(poll);show('home-view');updateHeader();renderHistory();}
  function renderHistory(){const raw=$('history-search').value.trim(),query=raw.toLowerCase();const frames=visibleFrames();$('history').replaceChildren();let group=null;
    // 3.1.0 · A search counts what it found and says so when it finds nothing.
    const matched=frames.filter(f=>title(f).toLowerCase().includes(query));
    if(query&&frames.length&&!matched.length)$('history').append(el('p','没有标题包含「'+raw+'」的对话。'+(state.cursor?'还有更早的对话未加载，可以点「加载更多对话」后再找。':''),'muted history-empty'));
    for(const f of matched){const g=dayGroup(f.updated_at);if(g!==group){group=g;$('history').append(el('p',g,'history-group'));}const active=state.frame?.id===f.id;const row=el('div',undefined,'history-row'+(active?' active':''));const b=el('button',title(f),'history-item'+(active?' active':''));b.title=title(f);b.onclick=act(()=>openFrame(f));row.append(b,moreButton({entity_type:'session',entity_id:f.id,title:title(f)}));$('history').append(row);}$('history-count').textContent=query?matched.length+' / '+frames.length:String(frames.length);if(!frames.length)$('history').append(el('p','还没有对话。从一个问题开始。','muted'));$('recent-list').replaceChildren();for(const f of frames.slice(0,3)){const b=el('button',undefined,'recent-row');b.append(el('span','↳'),el('strong',title(f)),el('small',date(f.updated_at)),el('span','↗'));b.onclick=act(()=>openFrame(f));$('recent-list').append(b);}if(!frames.length)$('recent-list').append(el('p','开始对话后，可以从这里回到你的思路。','muted'));$('more-history').hidden=!state.cursor;renderSwitcher();}
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
  async function refreshModels(fresh=false){const fid=state.frame?.id;if(!fid)return;const data=await native('list_session_models',{frame_id:fid});if(state.frame?.id!==fid)return;state.binding=data.binding;state.models=data.models||[];const select=$('model-select');select.replaceChildren();const empty=el('option','选择会话模型');empty.value='';select.append(empty);for(const m of data.models||[]){const o=el('option',m.local?'本地模型':m.name+' · '+m.model);o.value=m.id;o.disabled=!m.available;select.append(o);}select.value=data.binding?.native_profile_id||'';renderEffort();if(fresh&&data.active_native_profile_id){select.value=data.active_native_profile_id;await selectModel();}}
  /* 3.2.13 · Switching between the local model and a cloud one restarts the daemon (seconds). A second choice
     made meanwhile carried the old binding and was refused (「会话模型已变化」), and the list kept showing a
     model that was not in use. The list now waits for the switch, and after any failure shows the real one. */
  async function selectModel(){const select=$('model-select'),id=select.value,fid=state.frame?.id;if(!id||!fid)return;const binding=state.binding;
    select.disabled=true;
    try{const data=await native('select_session_model',{frame_id:fid,native_profile_id:id,expected_binding:{profile_id:binding.profile_id,revision:binding.revision}});if(state.frame?.id===fid){state.binding=data.binding;renderEffort();}}
    catch(error){if(state.frame?.id===fid)await refreshModels().catch(()=>{});throw error;}
    finally{select.disabled=false;}}
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
  /* 3.1.0 · Markdown and formulas. An answer is parsed here and built node by node, never as HTML.
     Formulas become MathML, which the window draws natively; a formula that does not parse (or a
     window without MathML) shows its TeX source as code instead of vanishing. A link to one of this
     conversation's files previews it in a dialog; a web link asks Leo, which confirms before a
     browser opens. User messages are shown exactly as typed. */
  function artifactRef(target){const parts=String(target).split('/');const last=parts.pop();let value=last;try{value=decodeURIComponent(last);}catch(_){}
    return {value,version:parts.at(-1)==='versions'};}
  function clickable(node,hint,run){node.setAttribute('role','button');node.tabIndex=0;node.title=hint;node.onclick=act(run);
    node.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();node.onclick(event);}};return node;}
  function linkNode(label,target,image){
    const text=label.replace(/\\([\[\]])/g,'$1')||(image?'图片':'链接'),file=/^\/api\/(?:v1\/)?artifacts\/(\S+)$/.exec(target);
    if(file){const ref=artifactRef(file[1]);return clickable(el('a',text,'artifact-link'),'预览 '+text,()=>openArtifactPreview(ref,text));}
    if(/^https?:\/\//i.test(target))return clickable(el('a',image?'图片：'+text:text,'web-link'),target,()=>request('open_link',{url:target}));
    return document.createTextNode(text);}
  // Inline rules, tried only where their first character appears. `_` and bare addresses also need
  // a non-word character before them, so snake_case names and words stay as written.
  const LINK=/!?\[((?:\\.|[^\]\\])+)\]\(([^()\s]+(?:\([^()\s]*\)[^()\s]*)*)(?:\s+"[^"]*")?\)/y;
  const INLINE_RULES={
    '`':[[/(`+)(?!`)([\s\S]*?[^`])\1(?!`)/y,m=>el('code',m[2].replace(/^ ([\s\S]*) $/,'$1'),'md-code')]],
    '$':[[/\$\$([\s\S]+?)\$\$/y,m=>math(m[1],true)],
      // `$` needs text right inside both ends and no digit after the closing one, so "$5 and $10" is money.
      [/\$(?=[^\s$])((?:\\.|[^$\\\n])+?)(?<=[^\s\\])\$(?!\d)/y,m=>math(m[1],false)]],
    '\\':[[/\\\[([\s\S]+?)\\\]/y,m=>math(m[1],true)],[/\\\(([\s\S]+?)\\\)/y,m=>math(m[1],false)],
      [/\\([!-\/:-@\[-`{-~])/y,m=>document.createTextNode(m[1])]],
    '[':[[LINK,m=>linkNode(m[1],m[2],false)]],
    '!':[[LINK,m=>linkNode(m[1],m[2],true)]],
    '<':[[/<br\s*\/?>/iy,()=>document.createTextNode('\n')]],
    'h':[[/https?:\/\/[^\s<>"'`\u3000-\u303f\uff00-\uffef]+(?<![.,;:!?'")\]}])/y,m=>linkNode(m[0],m[0],false)]],
    '*':[[/\*\*(?=\S)([\s\S]*?\S)\*\*/y,m=>inlines(el('strong'),m[1])],[/\*(?=[^\s*])([\s\S]*?[^\s*])\*/y,m=>inlines(el('em'),m[1])]],
    '_':[[/__(?=\S)([\s\S]*?\S)__(?![\p{L}\p{N}])/uy,m=>inlines(el('strong'),m[1])],[/_(?=[^\s_])([\s\S]*?[^\s_])_(?![\p{L}\p{N}])/uy,m=>inlines(el('em'),m[1])]],
    '~':[[/~~(?=\S)([\s\S]*?\S)~~/y,m=>inlines(el('del'),m[1])]]};
  function inlines(host,text){
    let plain='';const flush=()=>{if(plain)host.append(document.createTextNode(plain));plain='';};
    for(let i=0;i<text.length;){
      const c=text[i],rules=Object.hasOwn(INLINE_RULES,c)?INLINE_RULES[c]:null;let made=null,length=0;
      if(rules&&!((c==='_'||c==='h')&&/[\p{L}\p{N}]/u.test(text[i-1]||'')))
        for(const [pattern,make] of rules){pattern.lastIndex=i;const m=pattern.exec(text);if(m){made=make(m);length=m[0].length;break;}}
      if(made){flush();host.append(made);i+=length;}else plain+=text[i++];}
    flush();return host;}
  // Blocks: headings, rules, quotes, tables, display formulas, lists and paragraphs. A single line
  // break inside a paragraph stays a line break, as people write in chat.
  const HEADING=/^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$/,RULE=/^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$/,QUOTE=/^ {0,3}> ?/,
    LIST_ITEM=/^( *)([-*+]|\d{1,9}[.)])(?: +(.*))?$/,TABLE_RULE=/^ *\|? *:?-+:? *(?:\| *:?-+:? *)*\|? *$/,
    MATH_OPEN=/^ *(\$\$|\\\[)(.*)$/,MATH_ENV=/^ *\\begin\{(equation|align|aligned|gather|gathered|multline|eqnarray|split|cases|[pbBvV]?matrix)(\*?)\}/;
  const indentOf=line=>line.length-line.trimStart().length;
  const tableStart=(lines,i)=>lines[i].includes('|')&&i+1<lines.length&&lines[i+1].includes('|')&&TABLE_RULE.test(lines[i+1]);
  function mathBlock(lines,i){
    let m=MATH_OPEN.exec(lines[i]),close,text;
    if(m){close=m[1]==='$$'?'$$':'\\]';text=m[2];}
    else if((m=MATH_ENV.exec(lines[i]))){close='\\end{'+m[1]+m[2]+'}';text=lines[i].trim();}
    else return null;
    for(let j=i;j<lines.length;j++){if(j>i)text+='\n'+lines[j];const at=text.indexOf(close);
      if(at>=0){const env=close.startsWith('\\end');if(text.slice(at+close.length).trim())return null;
        return {tex:env?text.slice(0,at+close.length):text.slice(0,at),next:j+1};}}
    return null;}
  const startsBlock=(lines,i)=>HEADING.test(lines[i])||RULE.test(lines[i])||QUOTE.test(lines[i])||LIST_ITEM.test(lines[i])||tableStart(lines,i)||!!mathBlock(lines,i);
  function tableCells(line){
    let s=line.trim();if(s.startsWith('|'))s=s.slice(1);if(s.endsWith('|')&&!s.endsWith('\\|'))s=s.slice(0,-1);
    // A `|` inside code or a formula (|x|, \|v\|) belongs to it, not to the table.
    const kept=[...s.matchAll(/`[^`]*`|\$\$[\s\S]+?\$\$|\$(?=[^\s$])(?:\\.|[^$\\])+?(?<=[^\s\\])\$(?!\d)|\\\([\s\S]+?\\\)/g)].map(m=>[m.index,m.index+m[0].length]);
    const cells=[];let cell='';
    for(let k=0;k<s.length;k++){const inside=kept.some(([a,b])=>k>a&&k<b);
      if(!inside&&s[k]==='\\'&&s[k+1]==='|'){cell+='|';k++;continue;}
      if(!inside&&s[k]==='|'){cells.push(cell.trim());cell='';continue;}
      cell+=s[k];}
    cells.push(cell.trim());return cells;}
  function table(host,lines,i){
    const head=tableCells(lines[i]),aligns=tableCells(lines[i+1]).map(c=>/^:-+:$/.test(c)?'center':/-:$/.test(c)?'right':/^:-/.test(c)?'left':'');
    const row=(cells,tag)=>{const tr=el('tr');head.forEach((_,k)=>{const cell=inlines(el(tag),cells[k]??'');if(aligns[k])cell.style.textAlign=aligns[k];tr.append(cell);});return tr;};
    const box=el('div',undefined,'md-table'),grid=el('table'),top=el('thead'),body=el('tbody');
    top.append(row(head,'th'));i+=2;
    while(i<lines.length&&lines[i].trim()&&lines[i].includes('|'))body.append(row(tableCells(lines[i++]),'td'));
    grid.append(top,body);box.append(grid);host.append(box);return i;}
  function list(host,lines,i){
    const first=LIST_ITEM.exec(lines[i]),base=first[1].length,ordered=/\d/.test(first[2]);
    const node=el(ordered?'ol':'ul');if(ordered&&parseInt(first[2],10)!==1)node.start=parseInt(first[2],10);
    for(;;){
      let k=i;while(k<lines.length&&!lines[k].trim())k++;
      const m=k<lines.length?LIST_ITEM.exec(lines[k]):null;
      if(!m||m[1].length>base+1||/\d/.test(m[2])!==ordered||RULE.test(lines[k]))break;
      // An item owns the lines indented under it (nested lists, more paragraphs) and plain lines that
      // simply continue its text.
      const inner=Math.min(m[1].length+m[2].length+1,base+2),body=[m[3]||''];i=k+1;
      while(i<lines.length){
        if(!lines[i].trim()){let next=i;while(next<lines.length&&!lines[next].trim())next++;
          if(next<lines.length&&indentOf(lines[next])>=inner){while(i<next){body.push('');i++;}continue;}
          break;}
        if(indentOf(lines[i])>=inner){body.push(lines[i].slice(inner));i++;continue;}
        if(startsBlock(lines,i))break;
        body.push(lines[i++].trim());}
      const li=el('li'),task=/^\[([ xX])\]\s+/.exec(body[0]);
      if(task){body[0]=body[0].slice(task[0].length);li.className='md-task';li.append(el('span',task[1]===' '?'☐':'☑','md-check'),blocks(el('div'),body));}
      else blocks(li,body);
      node.append(li);}
    host.append(node);return i;}
  function blocks(host,lines){
    for(let i=0;i<lines.length;){
      const line=lines[i];let m,block;
      if(!line.trim()){i++;continue;}
      if((m=HEADING.exec(line))){host.append(inlines(el('h'+Math.min(6,m[1].length+2),undefined,'md-h'),m[2]));i++;}
      else if(RULE.test(line)){host.append(el('hr'));i++;}
      else if(QUOTE.test(line)){const inner=[];while(i<lines.length&&QUOTE.test(lines[i]))inner.push(lines[i++].replace(QUOTE,''));host.append(blocks(el('blockquote'),inner));}
      else if(tableStart(lines,i))i=table(host,lines,i);
      else if((block=mathBlock(lines,i))){const box=el('div',undefined,'md-math');box.append(math(block.tex,true));host.append(box);i=block.next;}
      else if(LIST_ITEM.test(line))i=list(host,lines,i);
      else{const para=[line.trim()];i++;while(i<lines.length&&lines[i].trim()&&!startsBlock(lines,i))para.push(lines[i++].trim());
        host.append(inlines(el('p'),para.join('\n')));}}
    return host;}
  function messageContent(host,text,plain){
    if(plain){host.append(el('div',String(text||''),'message-body'));return;}
    const parts=String(text||'').split(/```([^\n]*)\n([\s\S]*?)```/g);
    for(let i=0;i<parts.length;i+=3){
      if(parts[i].trim())host.append(blocks(el('div',undefined,'message-body'),parts[i].replace(/\t/g,'    ').split('\n')));
      if(i+2<parts.length)host.append(codeBlock(parts[i+1],parts[i+2]));}}
  /* TeX → MathML. Covers what answers use: fractions, roots, scripts and limits, Greek, operators and
     relations, function names, accents, \left…\right, \text and font styles (drawn with Unicode math
     letters), matrices, cases and aligned lines. An unknown command stays visible as its name. */
  const MATH_NS='http://www.w3.org/1998/Math/MathML',MATHML=typeof MathMLElement==='function'&&typeof document.createElementNS==='function';
  function math(tex,display){
    const source=String(tex).trim();
    if(MATHML&&source){try{return mml('math',[texParse(source)],display?{display:'block'}:{});}catch(_){/* shown as source below */}}
    return el('code',source||String(tex),'tex-raw');}
  function mml(tag,children=[],attrs={}){const n=document.createElementNS(MATH_NS,tag);for(const k in attrs)n.setAttribute(k,attrs[k]);
    for(const c of Array.isArray(children)?children:[children])n.append(c);return n;}
  const TEX_GREEK={alpha:'α',beta:'β',gamma:'γ',delta:'δ',epsilon:'ϵ',varepsilon:'ε',zeta:'ζ',eta:'η',theta:'θ',vartheta:'ϑ',iota:'ι',kappa:'κ',
    lambda:'λ',mu:'μ',nu:'ν',xi:'ξ',omicron:'ο',pi:'π',varpi:'ϖ',rho:'ρ',varrho:'ϱ',sigma:'σ',varsigma:'ς',tau:'τ',upsilon:'υ',phi:'ϕ',
    varphi:'φ',chi:'χ',psi:'ψ',omega:'ω',Gamma:'Γ',Delta:'Δ',Theta:'Θ',Lambda:'Λ',Xi:'Ξ',Pi:'Π',Sigma:'Σ',Upsilon:'Υ',Phi:'Φ',Psi:'Ψ',Omega:'Ω'};
  const TEX_MI={infty:'∞',partial:'∂',nabla:'∇',hbar:'ℏ',ell:'ℓ',emptyset:'∅',varnothing:'∅',aleph:'ℵ',Re:'ℜ',Im:'ℑ',wp:'℘',imath:'ı',jmath:'ȷ',
    angle:'∠',triangle:'△',square:'□',top:'⊤',bot:'⊥',degree:'°',dagger:'†',checkmark:'✓',S:'§',backslash:'∖'};
  const TEX_MO={times:'×',cdot:'⋅',cdotp:'⋅',pm:'±',mp:'∓',div:'÷',ast:'∗',star:'⋆',circ:'∘',bullet:'∙',oplus:'⊕',ominus:'⊖',otimes:'⊗',odot:'⊙',
    cup:'∪',cap:'∩',setminus:'∖',wedge:'∧',land:'∧',vee:'∨',lor:'∨',neg:'¬',lnot:'¬',leq:'≤',le:'≤',geq:'≥',ge:'≥',leqslant:'⩽',geqslant:'⩾',
    neq:'≠',ne:'≠',approx:'≈',equiv:'≡',sim:'∼',simeq:'≃',cong:'≅',propto:'∝',ll:'≪',gg:'≫',lesssim:'≲',gtrsim:'≳',prec:'≺',succ:'≻',
    preceq:'⪯',succeq:'⪰',doteq:'≐',coloneqq:'≔',in:'∈',notin:'∉',ni:'∋',subset:'⊂',subseteq:'⊆',supset:'⊃',supseteq:'⊇',subsetneq:'⊊',
    perp:'⊥',parallel:'∥',mid:'∣',nmid:'∤',models:'⊨',vdash:'⊢',to:'→',rightarrow:'→',leftarrow:'←',gets:'←',Rightarrow:'⇒',Leftarrow:'⇐',
    Leftrightarrow:'⇔',leftrightarrow:'↔',iff:'⟺',implies:'⟹',impliedby:'⟸',mapsto:'↦',longrightarrow:'⟶',longleftarrow:'⟵',
    Longrightarrow:'⟹',uparrow:'↑',downarrow:'↓',rightleftharpoons:'⇌',forall:'∀',exists:'∃',nexists:'∄',therefore:'∴',because:'∵',
    prime:'′',ldots:'…',dots:'…',dotsc:'…',cdots:'⋯',dotsb:'⋯',dotsm:'⋯',vdots:'⋮',ddots:'⋱',colon:':',vert:'|',Vert:'‖',lvert:'|',rvert:'|',
    lVert:'‖',rVert:'‖',langle:'⟨',rangle:'⟩',lceil:'⌈',rceil:'⌉',lfloor:'⌊',rfloor:'⌋',lbrace:'{',rbrace:'}',lbrack:'[',rbrack:']',bmod:'mod',mod:'mod'};
  const TEX_DELIMS=new Set(['vert','Vert','lvert','rvert','lVert','rVert','langle','rangle','lceil','rceil','lfloor','rfloor','lbrace','rbrace','lbrack','rbrack']);
  const TEX_BIG={sum:'∑',prod:'∏',coprod:'∐',bigcup:'⋃',bigcap:'⋂',bigoplus:'⨁',bigotimes:'⨂',bigvee:'⋁',bigwedge:'⋀',bigsqcup:'⨆',
    int:'∫',iint:'∬',iiint:'∭',oint:'∮'};
  const TEX_FUNCS=new Set('sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh coth log ln lg exp det dim ker deg gcd arg hom Pr tr rank sgn'.split(' '));
  const TEX_LIMITS={lim:'lim',limsup:'lim sup',liminf:'lim inf',max:'max',min:'min',sup:'sup',inf:'inf',argmax:'arg max',argmin:'arg min'};
  const TEX_ACCENTS={hat:['^'],widehat:['^',1],bar:['¯'],overline:['‾',1],tilde:['~'],widetilde:['~',1],vec:['→'],dot:['˙'],ddot:['¨'],
    check:['ˇ'],breve:['˘'],acute:['´'],grave:['`'],overrightarrow:['→',1],overleftarrow:['←',1]};
  const TEX_SPACE={',':'0.1667em',':':'0.2222em','>':'0.2222em',';':'0.2778em',' ':'0.25em',quad:'1em',qquad:'2em',enspace:'0.5em',
    thinspace:'0.1667em',medspace:'0.2222em',thickspace:'0.2778em'};
  const TEX_FONT_COMMANDS={mathrm:'rm',mathup:'rm',mathbf:'bf',mathbb:'bb',Bbb:'bb',mathcal:'cal',mathscr:'cal',mathfrak:'frak',mathsf:'sf',
    mathtt:'tt',mathit:'it',boldsymbol:'bi',bm:'bi',pmb:'bi',mathbfit:'bi'};
  const TEX_FONT_SWITCHES={rm:'rm',bf:'bf',sf:'sf',tt:'tt',it:'it',cal:'cal'};
  const TEX_FONTS={bf:[0x1D400,0x1D41A,0x1D7CE,0x1D6A8,0x1D6C2],bi:[0x1D468,0x1D482,0x1D7CE,0x1D71C,0x1D736],cal:[0x1D49C,0x1D4B6],
    frak:[0x1D504,0x1D51E],bb:[0x1D538,0x1D552,0x1D7D8],sf:[0x1D5A0,0x1D5BA,0x1D7E2],tt:[0x1D670,0x1D68A,0x1D7F6]};
  const TEX_FONT_HOLES={cal:{B:'ℬ',E:'ℰ',F:'ℱ',H:'ℋ',I:'ℐ',L:'ℒ',M:'ℳ',R:'ℛ',e:'ℯ',g:'ℊ',o:'ℴ'},frak:{C:'ℭ',H:'ℌ',I:'ℑ',R:'ℜ',Z:'ℨ'},
    bb:{C:'ℂ',H:'ℍ',N:'ℕ',P:'ℙ',Q:'ℚ',R:'ℝ',Z:'ℤ'}};
  const TEX_FENCES={pmatrix:['(',')'],bmatrix:['[',']'],Bmatrix:['{','}'],vmatrix:['|','|'],Vmatrix:['‖','‖'],cases:['{',''],dcases:['{',''],rcases:['','}']};
  const pick=(table,key)=>Object.hasOwn(table,key)?table[key]:undefined;
  function styled(c,font){
    const table=pick(TEX_FONTS,font);if(!table)return c;
    const hole=pick(TEX_FONT_HOLES,font)?.[c];if(hole)return hole;
    const code=c.codePointAt(0),from=(start,first)=>String.fromCodePoint(start+code-first);
    if(c>='A'&&c<='Z')return from(table[0],65);
    if(c>='a'&&c<='z')return from(table[1],97);
    if(c>='0'&&c<='9'&&table[2])return from(table[2],48);
    if(table[3]&&code>=0x391&&code<=0x3A9)return from(table[3],0x391);
    if(table[4]&&code>=0x3B1&&code<=0x3C9)return from(table[4],0x3B1);
    return c;}
  function texParse(src){
    let pos=0,font='';
    const fail=()=>{throw new Error('TEX_UNSUPPORTED');};
    const skip=()=>{while(pos<src.length&&/\s/.test(src[pos]))pos++;};
    const at=name=>src.startsWith('\\'+name,pos)&&!/[A-Za-z]/.test(src[pos+name.length+1]||'');
    const row=items=>items.length===1?items[0]:mml('mrow',items);
    const fence=d=>d?mml('mo',d,{stretchy:'true',symmetric:'true'}):null;
    const withFont=(next,read)=>{const saved=font;font=next;try{return read();}finally{font=saved;}};
    function word(){const re=/[A-Za-z]+/y;re.lastIndex=pos;const m=re.exec(src);if(m)pos+=m[0].length;return m?m[0]:'';}
    function raw(){skip();if(src[pos]!=='{')fail();let depth=0;const start=++pos;
      for(;pos<src.length;pos++){const c=src[pos];if(c==='\\'){pos++;continue;}if(c==='{')depth++;else if(c==='}'){if(!depth)break;depth--;}}
      if(pos>=src.length)fail();return src.slice(start,pos++);}
    function group(){skip();if(src[pos]!=='{')fail();pos++;const saved=font;const items=seq();font=saved;if(src[pos]!=='}')fail();pos++;return row(items);}
    function arg(){skip();const c=src[pos];if(c===undefined)fail();if(c==='{')return group();if(c==='\\')return command()??mml('mrow');pos++;return symbol(c);}
    function letter(c){return font==='rm'?mml('mi',c,{mathvariant:'normal'}):mml('mi',styled(c,font));}
    function greek(c){return mml('mi',styled(c,font),/[Α-Ω]/.test(c)&&!font?{mathvariant:'normal'}:{});}
    function symbol(c){
      if(/[0-9]/.test(c))return mml('mn',styled(c,font));
      if(/[A-Za-z]/.test(c))return letter(c);
      if(/[Α-Ωα-ω]/.test(c))return greek(c);
      if(c==="'")return mml('mo','′');
      if(c==='~')return mml('mspace',[],{width:'0.25em'});
      if('()[]|'.includes(c))return mml('mo',c,{stretchy:'false'});
      if(c==='.'||c==='/')return mml('mo',c,{lspace:'0',rspace:'0'});
      if(/[\p{L}]/u.test(c))return mml('mtext',c);
      return mml('mo',c==='-'?'−':c==='*'?'∗':c);}
    function delimiter(){skip();const c=src[pos];if(c===undefined)fail();pos++;
      if(c!=='\\')return c==='.'?'':c==='<'?'⟨':c==='>'?'⟩':c;
      const name=word();if(!name){const d=src[pos++];return d==='|'?'‖':d||fail();}
      return pick(TEX_MO,name)??fail();}
    function scripts(base){
      let sub=null,sup=null,primes=0;
      for(;;){skip();const c=src[pos];
        if(c==="'"){pos++;primes++;continue;}
        if(c==='^'){if(sup)fail();pos++;sup=arg();continue;}
        if(c==='_'){if(sub)fail();pos++;sub=arg();continue;}
        break;}
      if(primes){const mark=mml('mo',['′','″','‴','⁗'][Math.min(primes,4)-1]);sup=sup?mml('mrow',[mark,sup]):mark;}
      if(!sub&&!sup)return base;
      const limits=base.leoLimits;
      if(sub&&sup)return mml(limits?'munderover':'msubsup',[base,sub,sup]);
      return mml(limits?(sub?'munder':'mover'):(sub?'msub':'msup'),[base,sub||sup]);}
    function seq(){
      const items=[];
      for(;;){skip();const c=src[pos];
        if(c===undefined||c==='}'||c==='&'||src.startsWith('\\\\',pos)||at('right')||at('middle')||at('end'))return items;
        let node;
        if(/[0-9]/.test(c)){const m=/[0-9]+(?:\.[0-9]+)?/y;m.lastIndex=pos;const digits=m.exec(src)[0];pos+=digits.length;
          node=mml('mn',[...digits].map(d=>styled(d,font)).join(''));}
        else node=c==='{'?group():c==='\\'?command():(pos++,symbol(c));
        if(node===null)continue;
        const fn=node.leoFn;node=scripts(node);
        // A sign right after an operator (or first) is a sign, not a subtraction: no spacing around it.
        if(node.localName==='mo'&&/^[−+±∓]$/.test(node.textContent)){const prev=items.at(-1);
          if(!prev||(prev.localName==='mo'&&!/[)\]}|‖⟩]/.test(prev.textContent)))node.setAttribute('form','prefix');}
        items.push(node);
        if(fn){skip();if(src[pos]!=='('&&!at('left'))items.push(mml('mspace',[],{width:'0.1667em'}));}}}
    function table(){
      const grid=[[]];
      for(;;){grid.at(-1).push(seq());skip();
        if(src[pos]==='&'){pos++;continue;}
        if(src.startsWith('\\\\',pos)){pos+=2;skip();if(src[pos]==='['){const end=src.indexOf(']',pos);if(end<0)fail();pos=end+1;}grid.push([]);continue;}
        const last=grid.at(-1);return grid.length>1&&last.length===1&&!last[0].length?grid.slice(0,-1):grid;}}
    function mtable(grid,kind,aligns){
      const t=mml('mtable',grid.map(cells=>mml('mtr',cells.map((cell,k)=>{
        const d=mml('mtd',[row(cell)]);
        // Edge centres a cell's formula as a block; only the -webkit- values move a block sideways.
        const align=aligns?.[k]||(kind==='align'?(k%2?'left':'right'):kind==='cases'?'left':'');
        let style=align&&align!=='center'?'text-align:-webkit-'+align+';':'';
        if(kind==='align')style+=k%2?'padding-left:0;':(k?'padding-left:1.5em;':'')+'padding-right:0;';
        if(kind==='cases')style+=k?'padding-left:1em;':'padding-left:0;';
        if(style)d.setAttribute('style',style);return d;}))));
      if(kind==='align'||kind==='center')t.setAttribute('displaystyle','true');
      return t;}
    function environment(name){
      const base=name.replace(/\*$/,'');let aligns=null;
      if(base==='array'||base==='subarray'){aligns=[...raw().replace(/[^lcr]/g,'')].map(c=>({l:'left',c:'center',r:'right'})[c]);}
      else if(base==='alignat')raw();
      const grid=table();if(!at('end'))fail();pos+=4;if(raw()!==name)fail();
      const kind=/^(align|aligned|split|alignat|alignedat|eqnarray)$/.test(base)?'align':/cases$/.test(base)?'cases':/matrix$|^array$|^subarray$/.test(base)?'matrix':'center';
      const body=kind!=='matrix'&&kind!=='cases'&&grid.length===1&&grid[0].length===1?row(grid[0][0]):mtable(grid,kind,aligns);
      const [open,close]=pick(TEX_FENCES,base)||['',''];
      return open||close?mml('mrow',[fence(open),body,fence(close)].filter(Boolean)):body;}
    function command(){
      pos++;let name=word();
      if(!name){name=src[pos++];if(name===undefined)fail();
        if(pick(TEX_SPACE,name))return mml('mspace',[],{width:TEX_SPACE[name]});
        if(name==='!'||name==='/')return null;
        if(name==='{'||name==='}')return mml('mo',name,{stretchy:'false'});
        if(name==='|')return mml('mo','‖',{stretchy:'false'});
        return mml('mo',name);}
      if(name==='operatorname'&&src[pos]==='*'){pos++;name='operatorname*';}
      if(pick(TEX_SPACE,name))return mml('mspace',[],{width:TEX_SPACE[name]});
      if(pick(TEX_GREEK,name))return greek(TEX_GREEK[name]);
      if(pick(TEX_MI,name))return mml('mi',TEX_MI[name]);
      if(pick(TEX_MO,name))return mml('mo',TEX_MO[name],TEX_DELIMS.has(name)?{stretchy:'false'}:{});
      if(pick(TEX_BIG,name)){const node=mml('mo',TEX_BIG[name],{largeop:'true'});node.leoLimits=!/int$/.test(name);skip();
        if(at('limits')){pos+=7;node.leoLimits=true;}else if(at('nolimits')){pos+=9;node.leoLimits=false;}
        if(!node.leoLimits)node.setAttribute('movablelimits','false');return node;}
      if(TEX_FUNCS.has(name)){const node=mml('mi',name,{mathvariant:'normal'});node.leoFn=true;return node;}
      if(pick(TEX_LIMITS,name)||name==='operatorname*'){
        const node=mml('mo',pick(TEX_LIMITS,name)??raw().replace(/\\[,;: ]/g,' '),{movablelimits:'true',form:'prefix',lspace:'0',rspace:'0.1667em'});
        node.leoLimits=true;return node;}
      if(pick(TEX_FONT_COMMANDS,name))return withFont(TEX_FONT_COMMANDS[name],arg);
      if(pick(TEX_FONT_SWITCHES,name)){font=TEX_FONT_SWITCHES[name];return null;}
      if(pick(TEX_ACCENTS,name)){const [mark,wide]=TEX_ACCENTS[name];return mml('mover',[arg(),mml('mo',mark,{stretchy:wide?'true':'false'})],{accent:'true'});}
      switch(name){
        case 'frac':case 'dfrac':case 'tfrac':case 'cfrac':{const top=arg(),bottom=arg(),f=mml('mfrac',[top,bottom]);
          return name==='tfrac'?mml('mstyle',[f],{displaystyle:'false'}):name==='frac'?f:mml('mstyle',[f],{displaystyle:'true'});}
        case 'binom':case 'dbinom':case 'tbinom':{const top=arg(),bottom=arg();
          return mml('mrow',[mml('mo','('),mml('mfrac',[top,bottom],{linethickness:'0'}),mml('mo',')')]);}
        case 'sqrt':{skip();if(src[pos]!=='[')return mml('msqrt',[arg()]);
          const end=src.indexOf(']',pos);if(end<0)fail();const index=texParse(src.slice(pos+1,end));pos=end+1;return mml('mroot',[arg(),index]);}
        case 'left':{const open=delimiter(),items=seq();
          while(at('middle')){pos+=7;items.push(fence(delimiter()));items.push(...seq());}
          if(!at('right'))fail();pos+=6;const close=delimiter();return mml('mrow',[fence(open),...items,fence(close)].filter(Boolean));}
        case 'big':case 'Big':case 'bigg':case 'Bigg':case 'bigl':case 'Bigl':case 'biggl':case 'Biggl':case 'bigr':case 'Bigr':case 'biggr':case 'Biggr':
        case 'bigm':case 'Bigm':case 'biggm':case 'Biggm':{const size={big:'1.2em',Big:'1.623em',bigg:'2.047em',Bigg:'2.470em'}[name.replace(/[lrm]$/,'')];
          const d=delimiter();return d?mml('mo',d,{stretchy:'true',symmetric:'true',minsize:size,maxsize:size}):null;}
        case 'text':case 'textrm':case 'textnormal':case 'textup':case 'textsf':case 'texttt':case 'textmd':case 'mbox':case 'hbox':case 'textbf':case 'textit':case 'emph':{
          const node=mml('mtext',raw().replace(/\\([{}$%&#_ ])/g,'$1').replace(/~/g,'\u00a0'));
          if(name==='textbf')node.setAttribute('style','font-weight:bold');if(name==='textit'||name==='emph')node.setAttribute('style','font-style:italic');return node;}
        case 'operatorname':{const node=mml('mi',raw().replace(/\\[,;: ]/g,' ').replace(/[{}\\]/g,''),{mathvariant:'normal'});node.leoFn=true;return node;}
        case 'overset':case 'stackrel':{const over=arg(),node=mml('mover',[arg(),over]);node.leoLimits=true;return node;}
        case 'underset':{const under=arg(),node=mml('munder',[arg(),under]);node.leoLimits=true;return node;}
        case 'overbrace':{const node=mml('mover',[arg(),mml('mo','⏞',{stretchy:'true'})]);node.leoLimits=true;return node;}
        case 'underbrace':{const node=mml('munder',[arg(),mml('mo','⏟',{stretchy:'true'})]);node.leoLimits=true;return node;}
        case 'underline':return mml('munder',[arg(),mml('mo','_',{stretchy:'true'})],{accentunder:'true'});
        case 'xrightarrow':case 'xleftarrow':{skip();if(src[pos]==='['){const end=src.indexOf(']',pos);if(end<0)fail();pos=end+1;}
          return mml('mover',[mml('mo',name==='xrightarrow'?'→':'←',{stretchy:'true',minsize:'2em'}),arg()]);}
        case 'not':{const next=arg();if(next.localName==='mo')next.textContent+='\u0338';return next;}
        case 'pmod':{const inner=arg();return mml('mrow',[mml('mspace',[],{width:'0.4em'}),mml('mo','(',{stretchy:'false'}),
          mml('mi','mod',{mathvariant:'normal'}),mml('mspace',[],{width:'0.3333em'}),inner,mml('mo',')',{stretchy:'false'})]);}
        case 'boxed':case 'fbox':{const node=mml('mrow',[name==='fbox'?mml('mtext',raw()):arg()]);node.setAttribute('class','tex-boxed');return node;}
        case 'phantom':case 'hphantom':case 'vphantom':return mml('mphantom',[arg()]);
        case 'textcolor':{const color=raw().trim(),node=mml('mrow',[arg()]);if(/^#?[A-Za-z0-9]+$/.test(color))node.setAttribute('style','color:'+color);return node;}
        case 'cancel':case 'bcancel':case 'xcancel':case 'displaylines':return arg();
        case 'color':case 'label':case 'hspace':case 'vspace':raw();return null;
        case 'tag':skip();if(src[pos]==='*')pos++;return mml('mtext','\u2003('+raw()+')');
        case 'begin':return environment(raw());
        case 'displaystyle':case 'textstyle':case 'scriptstyle':case 'scriptscriptstyle':case 'limits':case 'nolimits':case 'nonumber':
        case 'notag':case 'hline':case 'centering':case 'strut':case 'relax':case 'allowbreak':case 'nobreak':return null;
        default:{const node=mml('mtext','\\'+name);node.setAttribute('class','tex-unknown');return node;}}}
    const grid=table();skip();if(pos<src.length)fail();
    return grid.length===1&&grid[0].length===1?row(grid[0][0]):mtable(grid,grid.some(cells=>cells.length>1)?'align':'center');}
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
  function messageRow(m){const row=el('article',undefined,'message '+m.role+(m.failure?' failure':''));row.append(el('header',m.role==='assistant'?'LEO AI':'你'));messageContent(row,m.content,m.role!=='assistant');if(m.failure)row.append(el('p','本次调用未完成'+(m.failure.request_id?' · 支持 ID：'+m.failure.request_id:''),'muted'));row.append(actionBar(m,row));return row;}
  /* 3.2.9 · The local model's search is one fixed cell written by its relay; show it as a search, not as
     code. Returns the query ('' when the title was cut before it), or null for any other step. */
  function localSearchStep(g){const t=String(g?.title||'');if(g?.kind!=='code'||!t.startsWith('_r = host.web_search('))return null;
    const m=t.match(/^_r = host\.web_search\(("(?:[^"\\]|\\.)*"), num_results=5\)/);try{return m?String(JSON.parse(m[1])):'';}catch(e){return '';}}
  const CELL_NARRATION=/^(我已经准备好一个 .{1,12} Cell，正在执行|这个 Cell 已)/;
  function processBlock(notes,steps,running,thoughts=[]){
    // A turn that only searched: the daemon's generic 「Python Cell」 remarks say nothing the search step doesn't.
    if(steps.length&&steps.every(g=>localSearchStep(g)!==null))notes=notes.filter(m=>!CELL_NARRATION.test(String(m.content||'').trim()));
    const box=el('details',undefined,'process'+(running?' running':''));if(running)box.open=true;
    box.append(el('summary',(running?'正在思考与执行':'思考与步骤')+' · '+(notes.length+steps.length+thoughts.length)+' 项'));
    if(thoughts.length){box.append(el('p','模型思考 · 原文，未经核实','process-label'));box.append(thoughtList(thoughts));}
    if(notes.length){box.append(el('p','过程说明','process-label'));const list=el('ol',undefined,'process-notes');for(const m of notes){const li=el('li');messageContent(li,m.content);list.append(li);}box.append(list);}
    if(steps.length){box.append(el('p','执行步骤','process-label'));const list=el('ol',undefined,'process-steps');
      for(const g of steps){const [label,kind]=STEP_STATUS[g.status]||['',''];const li=el('li',undefined,'process-step'+(kind?' '+kind:''));
        const searched=localSearchStep(g);
        if(searched!==null){li.append(el('span',label||'—','step-status'),el('span',searched?'联网搜索：「'+searched+'」':'联网搜索','step-title'));
          const view=el('button','查看结果','quiet step-link');view.type='button';view.onclick=e=>{e.preventDefault();openSide('web');};li.append(view);list.append(li);continue;}
        li.append(el('span',label||'—','step-status'),el('span',(STEP_KIND[g.kind]||'步骤')+'：'+(g.kind==='native_tools'&&g.names?.length?g.names.join('、'):(g.title||'')),'step-title'));
        const perm=permissionText(g.permission);if(perm)li.append(el('span',perm,'step-perm'));list.append(li);}
      box.append(list);}
    return box;}
  function bigrams(text){const s=String(text||'').toLowerCase().replace(/[\s\p{P}\p{S}_]+/gu,'');const out=new Map();
    for(let i=0;i<s.length-1;i++){const g=s.slice(i,i+2);out.set(g,(out.get(g)||0)+1);}return [out,Math.max(0,s.length-1)];}
  function sameAnswer(a,b){const [x,nx]=bigrams(a),[y,ny]=bigrams(b);if(nx<10||ny<10)return false;
    let common=0;for(const [g,c] of x)common+=Math.min(c,y.get(g)||0);return 2*common/(nx+ny)>=0.75;}
  /* 3.2.15 · DeepSeek may also write a full, formatted answer as a remark and then submit a short plain-text
     digest of it (the owner's 「什么是PDE的特征线」: 1340 characters with formulas, then 440). Then the full one is
     the answer: it is at least 200 characters and 1.5× longer, and ≥ 60% of the digest's character pairs are in
     it (that pair: 0.67; a related but different remark: 0.54; ordinary remarks under 0.2). */
  function fullerAnswer(remark,answer){const [x,nx]=bigrams(remark),[y,ny]=bigrams(answer);if(nx<200||ny<10||nx<1.5*ny)return false;
    let common=0;for(const [g,c] of y)common+=Math.min(c,x.get(g)||0);return common/ny>=0.6;}
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
      // 3.2.14 · DeepSeek often writes its answer as a remark and then submits it again, reworded; that remark
      // is not shown in the fold a second time (character-bigram similarity ≥ 0.75 to the answer).
      const final=answer>=0?turn.replies[answer]:null;
      const fuller=final?turn.replies.slice(0,answer).reverse().find(m=>!m.failure&&fullerAnswer(m.content,final.content))||null:null;
      const notes=turn.replies.filter((m,k)=>!m.failure&&(running||k<answer)&&m!==fuller&&!(final&&sameAnswer(m.content,final.content)));
      // The fuller remark is shown as the answer in its own place; the digest after it is not shown again.
      const hidden=turn.replies.filter((m,k)=>!m.failure&&k<answer&&m!==fuller&&!notes.includes(m)).concat(fuller?[final]:[]);
      if(notes.length||steps.length||thoughts.length)area.append(processBlock(notes,steps,running,thoughts));
      for(const m of turn.replies)if(!notes.includes(m)&&!hidden.includes(m))area.append(messageRow(m));
    });
    if(scroll||atEnd)scroller.scrollTop=scroller.scrollHeight;}
  async function refreshTimeline(fid,force){if(!force&&Date.now()-(state.timelineAt||0)<15000)return;state.timelineAt=Date.now();
    // The stored reasoning is re-read whole each time, so while a turn runs it is fetched at most every 5 s.
    const wantThoughts=Date.now()-(state.thoughtsAt||0)>=5000;if(wantThoughts)state.thoughtsAt=Date.now();
    try{const [d,t]=await Promise.all([request('timeline',{frameId:fid}),wantThoughts?request('thoughts',{frameId:fid}).catch(()=>null):null]);if(state.frame?.id!==fid)return;const next=d.groups||[];
      const thoughts=t?(t.thoughts||[]):(state.thoughts||[]);
      if(JSON.stringify(next)!==JSON.stringify(state.timeline||[])||JSON.stringify(thoughts)!==JSON.stringify(state.thoughts||[])){state.timeline=next;state.thoughts=thoughts;renderMessages();}}catch(_){}}
  function running(execution){state.execution=execution;const active=!!execution;$('working').hidden=!active;$('stop').hidden=!active;$('send').hidden=active;$('model-select').disabled=active;$('effort-select').disabled=active;$('elapsed').textContent=active&&openedAt?' · '+Math.max(0,Math.floor((Date.now()-openedAt)/1000))+' 秒':'';}
  async function refreshChat(epoch=state.epoch){const fid=state.frame?.id;if(!fid||epoch!==state.epoch)return;const [data,queue]=await Promise.all([request('messages',{frameId:fid}),request('execution',{frameId:fid})]);if(epoch!==state.epoch)return;const seen=new Map(state.messages.map(m=>[m.message_id||m.seq,m]));for(const m of data.messages||[])seen.set(m.message_id||m.seq,m);const next=[...seen.values()];const changed=JSON.stringify(next)!==JSON.stringify(state.messages);state.messages=next;if(state.before===null){state.before=data.next_before_seq;$('earlier-messages').hidden=!data.has_earlier;}if(changed)renderMessages();const owner=queue.owner||queue.queue?.[0]||null;running(owner);refreshApprovals(fid);(changed?state.thoughtsAt=0:0,refreshTimeline(fid,changed||!!owner));clearTimeout(poll);poll=setTimeout(()=>refreshChat(epoch).catch(e=>{notice(e.message);poll=setTimeout(()=>refreshChat(epoch).catch(e=>notice(e.message)),5000);}),owner?1700:6000);}
  async function openFrame(frame,fresh=false){setTimeout(renderAttachments,0);if(side.open&&side.frame!==frame.id){resetSide(frame.id);setTimeout(()=>{renderSide();act(refreshSide)();},0);}keepDraft();state.epoch++;nb.epoch++;clearTimeout(poll);state.frame=frame;state.project=frame.project_id;state.messages=[];state.timeline=[];state.thoughts=[];state.thoughtsAt=0;state.timelineAt=0;state.before=null;state.binding=null;openedAt=0;$('message-input').value=drafts.get(frame.id)||'';show('chat-view');$('earlier-messages').hidden=true;$('project-select').value=state.project;updateHeader();renderHistory();renderMessages();state.feedback={};request('feedback',{frameId:frame.id}).then(d=>{if(state.frame?.id===frame.id){state.feedback=d.feedback||{};renderMessages();}}).catch(()=>{});await Promise.all([refreshModels(fresh),refreshChat(),loadMode(frame)]);}
  async function send(){if(state.sending||!state.frame)return;const input=$('message-input');const value=input.value.trim();const fid0=state.frame.id;const files=readyAttachments(fid0);if(!value&&!files.length)return;if(attachmentsBusy(fid0)){notice('文件还在上传，请稍候再发送。');return;}const text=(value||'请查看我添加的文件。')+(files.length?'\n\n[附件，已放入工作目录] '+files.join('、'):'');state.sending=true;$('send').disabled=true;const originalFrame=state.frame;const fid=originalFrame.id;try{const selection=await prepareMessage(fid,state.binding);await request('send',{frameId:fid,text,...selection});$('notice').hidden=true;clearAttachments(fid);if(state.frame?.id===fid){input.value='';drafts.delete(fid);openedAt=Date.now();await refreshChat();}const name=(value||files[0]||'').slice(0,60);if(!originalFrame.name&&name){await request('rename',{frameId:fid,name});if(state.frame?.id===fid)state.frame.name=name;updateHeader();}await loadFrames();}finally{state.sending=false;$('send').disabled=false;}}
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
      if(c.origin==='user')head.append(chip(c.terminalRun?'你在终端执行':c.pythonRun?'你在 Python 面板执行':'你执行','trust-exploratory'));
      head.append(el('span',typeof c.cpuSeconds==='number'?'CPU '+c.cpuSeconds.toFixed(2)+' 秒':'','nb-meta'));
      card.append(head,el('pre',c.terminalRun?'$ '+c.command:(c.source||'（空单元）'),'nb-code'));
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
    notebookChrome(true);$('nb-title').textContent=title(nb.frame);$('nb-subtitle').textContent='这个对话中实际执行的代码、输出与产物，Leo 执行的和你在「终端」里执行的都在这里。记录只读，每一步保留原样。';
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
  function confirmAction(title,description,permanent=false){const d=$('confirm-dialog');$('confirm-title').textContent=title;$('confirm-description').textContent=description;$('confirm-label').hidden=!permanent;$('confirm-accept').className=permanent?'danger-button':'primary';$('confirm-value').value='';$('confirm-accept').disabled=permanent;$('confirm-value').oninput=()=>{$('confirm-accept').disabled=permanent&&$('confirm-value').value!=='彻底删除';};d.returnValue='';d.showModal();return new Promise(resolve=>d.addEventListener('close',()=>resolve(d.returnValue==='confirm'&&(!permanent||$('confirm-value').value==='彻底删除')),{once:true}));}
  const manageAct=fn=>async()=>{try{$('manage-status').textContent='';await fn();}catch(e){$('manage-status').textContent=errorText[e.message]||e.message;}};
  async function manageItems(){if(!$('manage-dialog').open)$('manage-dialog').showModal();await renderManager();}
  async function renderManager(){await readEntities();allProjects=(await request('projects')).projects||[];const kind=$('manage-kind').value||'session',filter=$('manage-state').value||'active';let rows;
    if(filter==='active'){rows=kind==='project'?allProjects.filter(p=>!hiddenIds.has(p.id||p.project_id)).map(p=>({entity_type:kind,entity_id:p.id||p.project_id,title:p.name})): (await allFrames()).filter(f=>!hiddenIds.has(f.id)&&!hiddenIds.has(f.project_id)).map(f=>({entity_type:kind,entity_id:f.id,title:title(f)}));}
    else rows=entities.filter(r=>r.entity_type===kind&&r.state===filter);
    const area=$('manage-list');area.replaceChildren();if(!rows.length)area.append(el('p','这里暂时没有内容。','muted'));
    for(const item of rows){const row=el('div',undefined,'manage-row');row.append(el('strong',item.title||'未命名'));const actions=el('div',undefined,'row-actions');
      const button=(label,fn)=>{const b=el('button',label,'quiet'+(label==='彻底删除'?' danger-outline':''));b.onclick=manageAct(async()=>{b.disabled=true;try{await fn();await reloadWorkspace();await renderManager();}finally{b.disabled=false}});actions.append(b);};
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
  // 3.2.6 · One set of names for every model: DeepSeek and the local model offer the same four levels.
  const EFFORT_NAMES={default:'默认',low:'低',mid:'中',high:'高',xhigh:'较高',extra:'很高',ultra:'最高'};
  function renderEffort(){const select=$('effort-select'),key=effortKey();let chosen=effortMemory.get(key);if(!chosen){try{chosen=localStorage.getItem('leo-effort:'+key);}catch(_){}}const choices=state.binding?.reasoning?.choices||[];if(!choices.some(c=>c.id===chosen&&c.available))chosen='default';select.replaceChildren();for(const c of choices.filter(c=>c.available)){const o=el('option','思考强度 · '+(EFFORT_NAMES[c.id]||c.label||c.id));o.value=c.id;o.title=c.semantics||'';select.append(o);}if(!choices.length){const o=el('option','思考强度 · 默认');o.value='default';select.append(o);}select.value=chosen;select.disabled=!!state.execution;effortMemory.set(key,chosen);}
  $('effort-select').onchange=()=>{const key=effortKey(),value=$('effort-select').value;effortMemory.set(key,value);try{localStorage.setItem('leo-effort:'+key,value);}catch(_){}};

  function editModel(id){const p=(shellState.profiles||[]).find(p=>p.id===id);$('wb-profile').value=p?.id||'';$('wb-name').value=p?.name||'';$('wb-preset').value=p?.preset||shellState.presets?.[0]?.id||'';const preset=(shellState.presets||[]).find(x=>x.id===$('wb-preset').value)||{};$('wb-model').value=p?.model||preset.model||'';$('wb-base').value=p?.base_url||preset.base_url||'';$('wb-key').value='';$('wb-delete').disabled=!p;syncWorkbenchPreset(false);}
  function syncWorkbenchPreset(reset){const p=(shellState.presets||[]).find(x=>x.id===$('wb-preset').value)||{};if(reset){$('wb-model').value=p.model||'';$('wb-base').value=p.base_url||'';}const local=p.id==='local-qwen';if(local&&!$('wb-name').value)$('wb-name').value='本地模型';$('wb-model').readOnly=local;$('wb-base').readOnly=local||p.editable_base_url===false;$('wb-key-label').hidden=local;}
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
  function selectSettingsTab(tab){for(const b of document.querySelectorAll('[data-settings-tab]'))b.setAttribute('aria-selected',String(b.dataset.settingsTab===tab));for(const p of document.querySelectorAll('[data-settings-pane]'))p.hidden=p.dataset.settingsPane!==tab;if(tab==='appearance')act(loadAppearance)();if(tab==='plugins')act(loadPlugins)();$('settings-dialog').scrollTop=0;}
  for(const b of document.querySelectorAll('[data-settings-tab]'))b.onclick=()=>selectSettingsTab(b.dataset.settingsTab);
  async function loadAppearance(){try{shellState=await native('get_state');await refreshPreferences();$('appearance-mode').value=preferences.mode;const select=$('appearance-theme');select.replaceChildren();for(const [id,label]of [['ink-autumn','淡墨浓秋'],['plain-white','素白'],['deep-sea-molten-orange','深海熔橙'],['amethyst-teal','紫晶青绿']]){const o=el('option',label);o.value=id;select.append(o);}if(preferences.theme){const o=el('option',preferences.theme.name+'（自定义）');o.value='custom';select.append(o);}select.value=preferences.theme?'custom':shellState.appearance?.theme||'ink-autumn';$('appearance-status').textContent='';}catch(e){$('appearance-status').textContent=errorText[e.message]||e.message;}}
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
  function openMenu(g){closeMenus();g.querySelector('[role=menu]').hidden=false;g.firstElementChild.setAttribute('aria-expanded','true');const editable=editTarget&&!editTarget.disabled&&!editTarget.readOnly&&typeof editSelection?.start==='number';for(const b of g.querySelectorAll('[data-edit]')){const op=b.dataset.edit;b.disabled=!editable&&op!=='copy';if(['copy','cut'].includes(op))b.disabled=editTarget?.type==='password'||!(editSelection?.end>editSelection?.start||window.getSelection()?.toString());}for(const b of g.querySelectorAll('[data-command=export],[data-command=knowledge-tree]'))b.toggleAttribute('disabled',!state.frame);}
  for(const g of menuGroups){const trigger=g.firstElementChild;trigger.onpointerdown=e=>{captureEdit();e.preventDefault();};trigger.onclick=()=>g.querySelector('[role=menu]').hidden?openMenu(g):closeMenus();trigger.onkeydown=e=>{if(['ArrowDown','Enter',' '].includes(e.key)){e.preventDefault();captureEdit();openMenu(g);g.querySelector('[role=menu] button:not(:disabled)')?.focus();}};}
  document.addEventListener('pointerdown',e=>{if(!e.target.closest('.desktop-menu'))closeMenus();});
  document.querySelector('.desktop-menu').addEventListener('keydown',e=>{const g=e.target.closest('.menu-group');if(!g)return;if(e.key==='Escape'){closeMenus();g.firstElementChild.focus();e.preventDefault();}else if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)&&e.target.closest('[role=menu]')){const items=[...g.querySelectorAll('[role=menu] button:not(:disabled)')],i=items.indexOf(e.target);items[e.key==='Home'?0:e.key==='End'?items.length-1:(i+(e.key==='ArrowDown'?1:-1)+items.length)%items.length]?.focus();e.preventDefault();}else if(['ArrowLeft','ArrowRight'].includes(e.key)){const next=menuGroups[(menuGroups.indexOf(g)+(e.key==='ArrowRight'?1:-1)+menuGroups.length)%menuGroups.length];openMenu(next);next.querySelector('[role=menu] button:not(:disabled)')?.focus();e.preventDefault();}});
  for(const b of document.querySelectorAll('[data-edit]'))b.onclick=act(async()=>{const operation=b.dataset.edit,target=editTarget,range=editSelection;const selected=target&&range?target.value.slice(range.start,range.end):window.getSelection()?.toString()||'';closeMenus();if(operation==='copy'){if(target?.type!=='password')await copyText(selected);return;}if(!target||target.disabled||target.readOnly||typeof range?.start!=='number')return;if(target.value!==range.value)throw Error('输入内容已变化，请重新选择。');target.focus();target.setSelectionRange(range.start,range.end);if(operation==='selectAll'){target.select();return;}if(operation==='paste'){const r=await native('paste_text');if(target.value!==range.value)throw Error('输入内容已变化，请重新粘贴。');target.focus();target.setSelectionRange(range.start,range.end);document.execCommand('insertText',false,r.text||'');}else if(operation==='cut'){if(target.type==='password')return;await copyText(selected);if(target.value!==range.value)throw Error('输入内容已变化，请重新选择。');target.focus();target.setSelectionRange(range.start,range.end);document.execCommand('delete');}else document.execCommand(operation);});
  function toggleSidebar(){document.body.classList.toggle('sidebar-collapsed');$('sidebar-toggle').setAttribute('aria-expanded',String(!document.body.classList.contains('sidebar-collapsed')));}
  $('sidebar-toggle').onclick=toggleSidebar;
  // Every stored message of a conversation, oldest first (shared by both exports).
  async function allMessages(frame){let before=null,messages=[],seen=new Set();do{const r=await request('messages',{frameId:frame.id,...(before?{before}:{})});messages.push(...r.messages||[]);if(!r.has_earlier)break;before=r.next_before_seq;if(before===null||before===undefined||seen.has(before))throw Error('消息分页未完成，请重试。');seen.add(before);}while(true);return [...new Map(messages.map(m=>[m.message_id||m.seq,m])).values()].sort((a,b)=>a.seq-b.seq);}
  async function exportConversation(){const frame=state.frame;if(!frame)throw Error('请先打开一个对话。');const unique=await allMessages(frame);const text='# '+title(frame)+'\n\n'+displayMessages(unique).filter(m=>['user','assistant'].includes(m.role)).map(m=>'## '+(m.role==='user'?'你':'Leo AI')+'\n\n'+plainText(m.content)).join('\n\n');download('leo-conversation.md',text,'text/markdown;charset=utf-8');}
  // 整理成知识树 / 导出到 LeoTree (3.2.16). The export of 2026-09-07 lived in the removed injection layer
  // (stage/leo-inject.js, deleted 2026-09-26); this is the same mapping on the workbench's own message reader.
  // Pure mapping to Leo Tree's v3 single-tree import envelope: no model call, no inferred mastery, no attachments.
  // LEO-TREE-EXPORT:BEGIN
  function treeChunks(content){
    const chunks=[];let lines=[],heading='',fence=null;
    const flush=()=>{if(lines.join('\n').trim())chunks.push({heading,content:lines.join('\n')});lines=[];};
    for(const line of String(content||'').split(/\r?\n/)){
      const marker=line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
      if(fence){lines.push(line);if(marker&&marker[1][0]===fence.character&&marker[1].length>=fence.length&&!marker[2].trim())fence=null;continue;}
      if(marker){fence={character:marker[1][0],length:marker[1].length};lines.push(line);continue;}
      const match=line.match(/^ {0,3}#{1,6}\s+(.+?)\s*#*$/);
      if(match){flush();heading=match[1];}
      lines.push(line);
    }
    flush();return chunks;
  }
  function serializeTreeDraft(draft){
    const tree=draft?.tree;
    if(draft?.schemaVersion!==3||!tree?.title?.trim()||!Array.isArray(tree.nodes)||!tree.nodes.length||tree.nodes.some(node=>!node.title?.trim()||typeof node.note!=='string'))throw Error('TREE_INVALID');
    const json=JSON.stringify(draft,null,2);
    if(tree.nodes.length>500||new TextEncoder().encode(json).byteLength>4*1024*1024)throw Error('TREE_TOO_LARGE');
    return json;
  }
  function treeDraft(frame,messages,now=new Date().toISOString(),uuid=()=>crypto.randomUUID()){
    const prefix=`leo-${uuid()}`;
    const sections=[{id:`${prefix}-questions`,title:'问题与目标',description:'',order:0},{id:`${prefix}-knowledge`,title:'知识与推导',description:'',order:1}];
    const nodes=[];let sourceMessageCount=0;
    for(const [messageIndex,message] of messages.entries()){
      if(!['user','assistant'].includes(message?.role))continue;
      const content=typeof message.content==='string'?message.content:'';
      if(!content.trim())continue;
      sourceMessageCount+=1;
      const sectionId=sections[message.role==='user'?0:1].id;
      for(const chunk of treeChunks(content)){
        const raw=(chunk.heading||chunk.content.split('\n').find(line=>line.trim())||'').replace(/^[>*\-#\s]+/,'').trim().slice(0,120).trim();
        nodes.push({id:`${prefix}-node-${nodes.length+1}`,sectionId,title:raw||'待整理内容',hint:'对话整理草稿，请核对后再学。',status:'todo',priority:1,note:chunk.content,tags:['Leo AI'],order:nodes.filter(node=>node.sectionId===sectionId).length,createdAt:now,updatedAt:now,statusChangedAt:null,statusHistory:[],firstSeenDoingAt:null,firstDoneAt:null,firstDoneExact:false,parentId:null,prerequisiteIds:[],relatedNodeIds:[],attachments:[],leoSource:{messageIndex:messageIndex+1,role:message.role,messageId:typeof message.message_id==='string'?message.message_id:null,sequence:Number.isSafeInteger(message.seq)?message.seq:null}});
      }
    }
    if(!nodes.length)throw Error('TREE_EMPTY');
    const name=String(frame?.name||frame?.task_summary||'').trim();
    const draft={schemaVersion:3,tree:{id:prefix,title:(name||'对话知识树').slice(0,160),description:'从 Leo AI 对话整理；内容未经自动事实核验。',createdAt:now,updatedAt:now,templateId:null,sections,nodes,logs:[],reviews:{},settings:{leoSource:{application:'Leo AI',format:'leo-tree-v3',sessionId:String(frame?.id||''),sessionTitle:name,capturedAt:now,exportedAt:now,conversationComplete:true,sourceMessageCount,sourceNodeCount:nodes.length,exportedNodeCount:nodes.length,attachmentsIncluded:false}},learningHistory:[],historyComplete:false,historyCompleteSince:null}};
    serializeTreeDraft(draft);return draft;
  }
  function treeFileName(title){return String(title).replace(/[<>:"/\\|?*\x00-\x1f]/g,'_').trim().slice(0,100)+'-LeoTree.json';}
  // LEO-TREE-EXPORT:END
  const treeErrors={TREE_RUNNING:'这个对话还在生成，请等回答完成或先停止，再整理成知识树。',TREE_EMPTY:'这个对话还没有可整理的文字消息。',TREE_TOO_LARGE:'内容超过 500 个节点或 4 MB，请取消一部分节点或缩短笔记后再保存。',TREE_INVALID:'请填写知识树名称和每个节点的标题，并至少保留一个节点。'};
  async function openKnowledgeTree(){
    const frame=state.frame;if(!frame)throw Error('请先打开一个对话。');
    const dialog=$('tree-dialog'),outline=$('tree-outline'),status=$('tree-status'),summary=$('tree-summary'),name=$('tree-title'),save=$('tree-save');
    outline.replaceChildren();summary.textContent='';name.value='';save.disabled=true;status.textContent='正在读取当前对话…';dialog.showModal();
    try{
      if(state.execution)throw Error('TREE_RUNNING');
      const messages=displayMessages(await allMessages(frame));
      if(state.frame?.id!==frame.id||!dialog.open)return;
      if(state.execution)throw Error('TREE_RUNNING');
      const draft=treeDraft(frame,messages),initialTitle=draft.tree.title,rows=[];
      name.value=draft.tree.title;
      for(const section of draft.tree.sections){
        outline.append(el('h3',section.title,'tree-section'));
        for(const node of draft.tree.nodes.filter(item=>item.sectionId===section.id)){
          const row=el('div','','tree-node'),pick=el('label','','tree-pick'),keep=el('input'),label=el('input'),note=el('textarea');
          keep.type='checkbox';keep.checked=true;pick.append(keep,document.createTextNode(`保留 · 第 ${node.leoSource.messageIndex} 条 · ${node.leoSource.role==='user'?'我的问题':'Leo AI 回答'}`));
          label.value=node.title;label.maxLength=120;label.setAttribute('aria-label','节点标题');
          note.value=node.note;note.rows=4;note.setAttribute('aria-label','节点笔记');
          row.append(pick,label,note);outline.append(row);rows.push({node,keep,label,note});
        }
      }
      const count=()=>{summary.textContent=`${draft.tree.settings.leoSource.sourceMessageCount} 条文字消息 · 保留 ${rows.filter(row=>row.keep.checked).length} / ${rows.length} 个节点`;};
      rows.forEach(row=>row.keep.addEventListener('change',count));count();
      status.textContent='';save.disabled=false;
      save.onclick=()=>{
        const nowSaved=new Date().toISOString(),kept=rows.filter(row=>row.keep.checked);
        const out=structuredClone(draft);
        out.tree.title=name.value.trim();
        out.tree.nodes=kept.map(row=>({...structuredClone(row.node),title:row.label.value.trim(),note:row.note.value,updatedAt:nowSaved}));
        for(const section of out.tree.sections)out.tree.nodes.filter(node=>node.sectionId===section.id).forEach((node,index)=>{node.order=index;});
        out.tree.updatedAt=nowSaved;
        Object.assign(out.tree.settings.leoSource,{exportedAt:nowSaved,exportedNodeCount:out.tree.nodes.length,edited:out.tree.title!==initialTitle||rows.some(row=>row.label.value!==row.node.title||row.note.value!==row.node.note),selectionChanged:kept.length!==rows.length});
        let json;try{json=serializeTreeDraft(out);}catch(error){status.textContent=treeErrors[error.message]||'无法生成文件，请重试。';return;}
        const file=treeFileName(out.tree.title);download(file,json,'application/json;charset=utf-8');
        status.textContent=`已发起保存「${file}」（${out.tree.nodes.length} 个节点）。在保存窗口选好位置保存，然后在 Leo Tree 点「导入」，选择这个文件，预览后确认「作为新树导入」。`;
      };
    }catch(error){if(dialog.open)status.textContent=treeErrors[error.message]||error.message||'无法读取这个对话，请稍后重试；原对话没有改动。';}
  }
  const commands={new:()=>newFrame(),project:()=>$('new-project').click(),export:exportConversation,'knowledge-tree':openKnowledgeTree,'import-theme':async()=>{await settings();selectSettingsTab('appearance');$('custom-theme-file').click();},home:()=>$('return-start').click(),search:()=>{document.body.classList.remove('sidebar-collapsed');$('sidebar-toggle').setAttribute('aria-expanded','true');$('history-search').focus();},sidebar:toggleSidebar,'zoom-in':()=>setTextScale(textScale+.1),'zoom-out':()=>setTextScale(textScale-.1),'zoom-reset':()=>setTextScale(1),appearance:async()=>{await settings();selectSettingsTab('appearance');},about:async()=>{await settings();selectSettingsTab('about');},guide:()=>$('help-dialog').showModal()};
  for(const b of document.querySelectorAll('[data-command]'))b.onclick=act(async()=>{closeMenus();await commands[b.dataset.command]();});
  $('help-close').onclick=()=>$('help-dialog').close();
  $('artifact-close').onclick=()=>$('artifact-dialog').close();
  $('tree-close').onclick=$('tree-cancel').onclick=()=>$('tree-dialog').close();

  /* 2.2.7 · Approval mode per conversation, and the tool calls the daemon is waiting on.
     The daemon gates tool calls; Leo shows each pending request and answers it. Research
     confirmations are native dialogs and never pass through here. */
  Object.assign(errorText,{WORKBENCH_SCHEDULE_TIME_PASSED:'这个时间已经过去了，请选一个将来的时间。',WORKBENCH_SCHEDULE_TIME_INVALID:'请填写有效的日期和时间。',
    WORKBENCH_SCHEDULE_TEXT_INVALID:'请填写到点要发送的消息（不超过 8000 字）。',WORKBENCH_SCHEDULE_LIMIT:'定时任务已达上限（100 个），请先删除不用的任务。',
    WORKBENCH_INVALID_REQUEST:'请求内容无效，请检查后重试。',WORKBENCH_UPLOAD_TOO_LARGE:'文件超过 25 MB。',WORKBENCH_LINK_INVALID:'这个链接不是公开网页地址，Leo 不会打开它。'});
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
  /* 3.2.11 · 「用量」 (owner, 2026-09-30): the conversation model's temperature (one per model, from the next
     message on), how full its context is, and the tokens and cache hits of its calls. Token counts come from
     the daemon's own call records; the parts are exact for the local model (its relay counts them) and the
     daemon's estimate otherwise. Only the local model's latest request can be read in full. */
  const usage={temps:null,context:null,request:null,epoch:0};
  const USAGE_COLORS=['#7F77DD','#1D9E75','#EF9F27','#D4537E','#378ADD','#888780','#5DCAA5','#F0997B'];
  function currentModel(){return (state.models||[]).find(m=>m.id===state.binding?.native_profile_id)||null;}
  function usageModelId(m){return m?(m.local?'local-qwen3-4b':m.model):null;}
  function tokens(n){return n==null?'—':n>=1e6?(n/1e6).toFixed(n%1e6?1:0)+'M':n>=10000?(n/1000).toFixed(1)+'k':String(n);}
  /* 3.2.12 · The daemon's capability table has one row per provider, and DeepSeek and the local model both
     go through its OpenAI-compatible provider, so /context reported OpenAI's 272k for both. Leo supplies
     the limits it knows: DeepSeek V4 from DeepSeek's pricing page (1M, checked 2026-09-30), the local model
     from its relay's own record. Thinking mode ignores temperature (DeepSeek thinking-mode guide), and V4
     thinks by default with no switch in Leo, so its temperature is not offered. */
  const KNOWN_CONTEXT={'deepseek-v4-pro':1e6,'deepseek-v4-flash':1e6};
  function noTemperature(id){return /^deepseek-v4/.test(id||'');}
  function usageCalls(){return (state.timeline||[]).filter(g=>g.usage&&typeof g.usage.input==='number');}
  function closeUsagePop(){$('usage-pop').hidden=true;$('usage-button').setAttribute('aria-expanded','false');}
  function renderUsage(){const m=currentModel(),id=usageModelId(m);$('usage-model').textContent=m?(m.local?'本地模型':m.name+' · '+m.model):'未选择模型';
    const t=usage.temps,slider=$('usage-temp');const set=t&&id&&t.temperatures[id]!=null;const value=set?t.temperatures[id]:(t?.default??0.7);
    const fixed=noTemperature(id);slider.value=String(value);slider.disabled=!id||!t||fixed;
    $('usage-temp-value').textContent=fixed?'不适用':Number(value).toFixed(1)+(set?'':' · 默认');$('usage-temp-reset').hidden=!set||fixed;
    $('usage-temp-note').textContent=!id?'先为这个对话选择模型。':fixed?'DeepSeek V4 默认开启思考；按 DeepSeek 官方说明，思考模式下温度不起作用，所以这里不能调。':'只影响这个模型，从下一条消息起生效。';
    // 3.2.13 · 「本轮」 is the latest call of the model now chosen; the conversation total covers every model.
    const calls=usageCalls(),mine=calls.filter(g=>g.model===id),last=mine[mine.length-1]?.usage||null,req=m?.local?usage.request:null;
    // The daemon's own limit is kept only for models Leo has no figure for, and marked as such.
    const limit=m?.local?(req?.context||null):(KNOWN_CONTEXT[m?.model]||usage.context?.limit||null);const guessed=!m?.local&&!KNOWN_CONTEXT[m?.model]&&limit;
    const used=last?.input??usage.context?.estimate??null;
    $('usage-context-text').textContent=used==null?'—':tokens(used)+(limit?' / '+tokens(limit)+' · '+Math.round(used*100/limit)+'%':(m?.local?' / 上限在下一条消息后显示':''))+(last?'':'（估算）')+(guessed?'（上限为底层默认值，可能不准）':'');
    let parts=[];if(req&&req.parts)parts=[['系统提示',req.parts.system],['对话历史',req.parts.history],['本轮提问',req.parts.question]].filter(p=>p[1]);
    else parts=(usage.context?.layers||[]).map(l=>[l.label,l.tokens]);
    const sum=parts.reduce((a,p)=>a+p[1],0)||1,scale=used&&limit?Math.min(1,used/limit):0;const bar=$('usage-bar'),legend=$('usage-legend');bar.replaceChildren();legend.replaceChildren();
    parts.forEach(([label,n],i)=>{const seg=el('i');seg.style.width=(scale*100*n/sum).toFixed(2)+'%';seg.style.background=USAGE_COLORS[i%USAGE_COLORS.length];bar.append(seg);
      const key=el('span',label+' '+tokens(n));key.style.setProperty('--key',USAGE_COLORS[i%USAGE_COLORS.length]);legend.append(key);});
    if(parts.length)legend.append(el('small',req?'本地模型最近一次请求的实际分项':'分项为底层估算'));
    $('usage-fulltext').hidden=!(m?.local&&req&&req.text);
    const hit=u=>u&&u.input?Math.round((u.cacheRead||0)*100/u.input)+'%':'—';
    $('usage-in').textContent=last?tokens(last.input):'—';$('usage-out').textContent=last?tokens(last.output):'—';$('usage-hit').textContent=hit(last);
    const total=calls.reduce((a,g)=>({input:a.input+g.usage.input,output:a.output+(g.usage.output||0),cacheRead:a.cacheRead+(g.usage.cacheRead||0)}),{input:0,output:0,cacheRead:0});
    $('usage-total').textContent=calls.length?'本对话合计 · '+calls.length+' 次调用 · 输入 '+tokens(total.input)+' · 输出 '+tokens(total.output)+' · 命中 '+hit(total)+((state.timeline||[]).length>=300?'（最近 300 步）':'')+(calls.length&&!mine.length?' · 当前模型在这个对话里还没有调用过，「本轮」为空':''):'这个对话还没有模型调用记录。';}
  async function loadUsage(){const fid=state.frame?.id,epoch=++usage.epoch,m=currentModel();$('usage-status').textContent='正在读取…';renderUsage();
    const lastIn=usageCalls().filter(g=>g.model===usageModelId(m)).at(-1)?.usage?.input;
    const [temps,context,latest]=await Promise.all([request('model_temperatures').catch(()=>null),fid?request('context',{frameId:fid}).catch(()=>null):null,
      m?.local?request('local_last_request',{promptTokens:lastIn}).then(r=>r.request).catch(()=>null):null]);
    if(epoch!==usage.epoch||state.frame?.id!==fid)return;usage.temps=temps;usage.context=context;usage.request=latest;
    $('usage-status').textContent=temps?'':'温度设置暂时读不到。';renderUsage();}
  async function setTemperature(value){const id=usageModelId(currentModel());if(!id)return;$('usage-status').textContent='正在保存…';
    usage.temps=await request('model_temperature_set',{model:id,value});$('usage-status').textContent=value==null?'已恢复默认温度。':'已保存，下一条消息起生效。';renderUsage();}
  function openFullText(){const r=usage.request;if(!r)return;const calls=usageCalls(),last=calls[calls.length-1]?.usage;
    const same=last&&r.promptTokens!=null&&Math.abs(last.input-r.promptTokens)<=8;
    $('fulltext-meta').textContent=(r.at?new Date(r.at*1000).toLocaleString():'')+' · '+tokens(r.promptTokens)+' tokens（上下文 '+tokens(r.context)+'）'+
      (same?' · 就是这个对话最近一次调用':' · 这是最近一次发给本地模型的请求，可能来自另一个对话')+(r.truncated?' · 过长，只显示前一部分':'');
    $('fulltext-text').textContent=r.text;$('fulltext-dialog').showModal();}
  function confirmAuto(){const d=$('auto-dialog');$('auto-understood').checked=false;$('auto-accept').disabled=true;d.returnValue='';d.showModal();
    return new Promise(resolve=>d.addEventListener('close',()=>resolve(d.returnValue==='confirm'),{once:true}));}
  async function chooseMode(mode){closeApprovalPop();if(!state.frame||mode===approval.mode)return;if(mode==='auto'&&!await confirmAuto())return;
    const fid=state.frame.id;const r=await request('approval_set_mode',{frameId:fid,mode});if(state.frame?.id===fid){approval.mode=r.mode;renderMode();}}
  function standingPattern(r){const c=(r.patterns||[]).filter(p=>p&&p!=='*');const exact=c.filter(p=>!/[*?]/.test(p));
    if(exact.length)return exact[0];if(!c.length)return r.target&&r.target!=='*'?r.target:'';
    const wild=s=>(s.match(/[*?]/g)||[]).length;return c.slice().sort((a,b)=>wild(a)-wild(b)||b.length-a.length)[0];}
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
      const pattern=standingPattern(r);const always=el('button','本对话内都允许同类操作','quiet');always.title=pattern?('允许范围：'+pattern):'没有更窄的范围，这次只允许这一次';always.onclick=act(()=>decide(r,true,'conversation'));
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
  /* 3.1.0 · 「网页」: which pages the AI searched and read in this conversation, beside the chat.
     3.2.1 · 「终端」 is the person's own shell (WSL, started in this conversation's working directory):
     what is typed runs as typed, not through the AI and not through approvals. The commands the AI ran
     stay readable under 「Leo 执行过的命令」. 「Python」 runs the person's code as a cell in the
     conversation's kernel, next to the cells Leo ran there. */
  const side={open:false,tab:'terminal',mode:'shell',frame:null,steps:null,userCells:null,timer:null,busy:false};
  function randomRunId(){const bytes=new Uint8Array(8);if(globalThis.crypto?.getRandomValues)crypto.getRandomValues(bytes);else for(let i=0;i<8;i++)bytes[i]=Math.floor(Math.random()*256);
    return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}
  function sideChip(text,kind){return el('span',text,'trust-chip '+kind);}
  function resetSide(fid){side.frame=fid;side.steps=null;side.userCells=null;termReset(fid);pyReset(fid);}
  function openSide(tab){if(!state.frame)return;if(side.frame!==state.frame.id)resetSide(state.frame.id);
    side.open=true;selectSideTab(tab);$('side-panel').hidden=false;document.body?.classList.add('side-open');renderSide();act(refreshSide)();
    if(tab==='terminal'&&side.mode==='shell')$('term-input').focus();else if(tab==='python')$('py-input').focus();}
  function closeSide(){side.open=false;clearTimeout(side.timer);clearTimeout(term.timer);clearTimeout(py.timer);$('side-panel').hidden=true;document.body?.classList.remove('side-open');}
  function selectSideTab(tab){side.tab=tab;for(const b of document.querySelectorAll('[data-side-tab]'))b.setAttribute('aria-selected',String(b.dataset.sideTab===tab));
    $('side-terminal').hidden=tab!=='terminal';$('side-python').hidden=tab!=='python';$('side-web').hidden=tab!=='web';}
  function selectTermMode(mode){side.mode=mode;$('term-mode-shell').setAttribute('aria-pressed',String(mode==='shell'));$('term-mode-log').setAttribute('aria-pressed',String(mode==='log'));
    $('term-shell').hidden=mode!=='shell';$('term-leo').hidden=mode!=='log';}
  // The steps say which commands the AI ran and which pages it read; the notebook says which old
  // (3.1.0) terminal cells were typed by the person, so those keep their 「你」.
  async function refreshSide(force){
    if(!side.open||!state.frame)return;
    if(side.tab==='terminal'&&side.mode==='shell')return termStart();
    if(side.tab==='python')return pyRefresh();
    if(side.busy)return;const fid=state.frame.id;side.busy=true;clearTimeout(side.timer);
    try{const [steps,log]=await Promise.all([request('steps',{frameId:fid}),force===true||!side.userCells?request('notebook',{frameId:fid}).catch(()=>null):null]);
      if(!side.open||state.frame?.id!==fid)return;side.steps=steps;
      if(log)side.userCells=(log.entries||[]).filter(c=>c.origin==='user'&&c.terminalRun);
      renderSide();
    }finally{side.busy=false;}
    // Poll while the conversation's own run is going.
    if(side.open&&state.execution&&(side.tab==='web'||side.mode==='log'))side.timer=setTimeout(()=>act(refreshSide)(),2500);}
  function renderSide(){if(side.tab==='terminal'){if(side.mode==='shell'){termPaint(true);termStatus();}else renderTerminal();}else if(side.tab==='python')renderPython(true);else renderWeb();}
  // Step status is running / done / error / warning; a refused or failed command has no exit code.
  function exitChip(c){if(c.status==='running')return sideChip('运行中','trust-compute');
    if(c.exitCode==null)return sideChip(c.error||c.status==='error'?'未执行':'已结束','trust-blocked');
    return c.exitCode===0?sideChip('成功','trust-verified'):sideChip('退出码 '+c.exitCode,'trust-failed');}
  function seconds(ms){return typeof ms==='number'?(ms<1000?ms+' 毫秒':(ms/1000).toFixed(ms<10000?1:0)+' 秒'):'';}
  function commandRow(c,run){
    const row=el('article',undefined,'term-entry'+(run?' mine':''));const head=el('div',undefined,'term-head');
    head.append(el('span',run?'你':'Leo','term-who'),el('code','$ '+c.command,'term-cmd'));
    const meta=el('div',undefined,'term-meta');meta.append(exitChip(c));if(c.durationMs!=null)meta.append(el('span',seconds(c.durationMs)));
    row.append(head,meta);
    const out=run?.cell?[run.cell.stdout,run.cell.stderr]:[c.stdout,c.stderr];
    if(out[0])row.append(el('pre',out[0],'term-out'));if(out[1])row.append(el('pre',out[1],'term-out stderr'));
    if(c.error)row.append(el('pre',c.error,'term-out error'));
    if(!run?.cell&&(c.stdoutTruncated||c.stderrTruncated))row.append(el('p','这里只显示输出的一段预览；完整结果以计算记录为准。','term-note'));
    if(c.changed?.length){const files=el('div',undefined,'term-files');files.append(el('small','改动的文件'));for(const n of c.changed)files.append(el('span',n));row.append(files);}
    return row;}
  function renderTerminal(){
    const host=$('term-log');const stick=host.scrollHeight-host.scrollTop-host.clientHeight<40;host.replaceChildren();
    const commands=side.steps?.commands||[];
    if(!side.steps){host.append(el('p','正在读取…','term-empty'));return;}
    if(side.steps.capped)host.append(el('p','这个对话的步骤很多，只列出最早 800 步里的命令。','term-note'));
    if(!commands.length)host.append(el('p','AI 在这个对话里还没有执行过命令。','term-empty'));
    const usedCells=new Set();
    for(const c of commands){const cell=(side.userCells||[]).find(u=>!usedCells.has(u.terminalRun)&&u.command===c.command)||null;if(cell)usedCells.add(cell.terminalRun);
      host.append(commandRow(c,cell?{cell}:null));}
    if(stick)host.scrollTop=host.scrollHeight;}
  function webLink(text,url,cls){if(!url)return el('span',text,cls);const a=el('a',text,'web-link '+cls);return clickable(a,url,()=>request('open_link',{url}));}
  function renderWeb(){
    // The daemon records host.web_search calls made inside cells too (the local model's searches), so
    // this list is complete; 3.2.9 also listed them from the notebook, which showed each search twice.
    const host=$('web-log');host.replaceChildren();const items=[...(side.steps?.web||[])].reverse();
    if(!side.steps){host.append(el('p','正在读取…','term-empty'));return;}
    if(!items.length){host.append(el('p','AI 还没有在这个对话里搜索或读取网页。','term-empty'));return;}
    for(const w of items){const card=el('article',undefined,'web-entry');
      if(w.type==='search'){card.append(el('p',(w.database?'在 '+w.database+' 中搜索':'搜索')+'「'+w.query+'」'+(w.source?' · '+w.source:''),'web-kind'));
        const list=el('ol',undefined,'web-results');for(const r of w.results||[]){const li=el('li');li.append(webLink(r.title||r.url||'（无标题）',r.url,'web-title'));
          if(r.url)li.append(el('small',r.url,'web-url'));if(r.snippet)li.append(el('p',r.snippet,'web-snippet'));list.append(li);}
        if(!(w.results||[]).length)card.append(el('p',w.error||'没有结果。','web-snippet'));else card.append(list);}
      else{card.append(el('p',w.download?'下载文件':'读取网页','web-kind'));const url=w.finalUrl||w.url;card.append(webLink(url||'（地址不可用）',url,'web-title'));
        if(w.error)card.append(el('p',w.error,'web-snippet'));
        else if(w.excerpt){const more=el('details',undefined,'web-excerpt');more.append(el('summary','摘录（'+w.chars+' 字，只作文字显示）'),el('pre',w.excerpt));card.append(more);}}
      host.append(card);}}

  /* 3.2.1 · The terminal screen: lines of styled characters and a cursor, fed by what the shell prints.
     It understands what a line-mode shell sends (colours, carriage return, backspace, erase line or
     screen, cursor moves, wrapping at the width it told the shell); anything else is dropped. Output is
     polled from Leo, quickly while something is printing and more slowly when the shell is idle. */
  const TERM_LINES=5000;
  const TERM_PALETTE=['#5c5f66','#e06c6c','#8fbf6a','#e0b45c','#6f9fd8','#c08fc0','#5fb3b3','#cfcfcf','#7d8087','#f08a8a','#a8d58a','#f0cf7a','#8fb8ea','#d9a6d6','#85cfcf','#f5f5f5'];
  const termStyles=new Map();
  function termColor(n){if(n<16)return TERM_PALETTE[n];if(n>=232){const v=8+(n-232)*10;return 'rgb('+v+','+v+','+v+')';}
    n-=16;return 'rgb('+[Math.floor(n/36),Math.floor(n/6)%6,n%6].map(v=>v?55+v*40:0).join(',')+')';}
  function termStyle(a){const key=[a.fg||'',a.bg||'',a.b?1:0,a.d?1:0,a.i?1:0,a.u?1:0,a.r?1:0].join('|');let s=termStyles.get(key);
    if(!s){let fg=a.fg||'',bg=a.bg||'';if(a.r){const f=fg;fg=bg||'var(--rail)';bg=f||'var(--rail-ink)';}
      s={fg,bg,cls:[a.b&&'t-b',a.d&&'t-d',a.i&&'t-i',a.u&&'t-u'].filter(Boolean).join(' ')};termStyles.set(key,s);}
    return s;}
  const TERM_PLAIN=termStyle({});
  const term={frame:null,gen:0,history:[],hpos:0,draft:'',lastTab:false,resizeTimer:null};
  function termReset(fid){clearTimeout(term.timer);Object.assign(term,{frame:fid,gen:term.gen+1,next:0,started:false,opened:false,alive:false,busy:false,idle:0,timer:null,
    lines:[[]],row:0,col:0,attr:{},style:TERM_PLAIN,carry:'',saved:null,alt:false,cwd:'',error:'',exitCode:null,dirty:0,full:true,dropped:0,cursorRow:0,hpos:term.history.length});}
  termReset(null);
  function termLine(){while(term.lines.length<=term.row)term.lines.push([]);return term.lines[term.row];}
  function termMark(){termLine();term.dirty=Math.min(term.dirty,term.row);}
  function termTop(){return Math.max(0,term.lines.length-(term.rows||30));}
  function termClearAll(){term.lines=[[]];term.row=0;term.col=0;term.full=true;term.dropped=0;term.dirty=0;term.cursorRow=0;}
  function termWide(cp){return cp>=0x1100&&(cp<=0x115f||(cp>=0x2e80&&cp<=0xa4cf&&cp!==0x303f)||(cp>=0xac00&&cp<=0xd7a3)||(cp>=0xf900&&cp<=0xfaff)||(cp>=0xfe30&&cp<=0xfe4f)||(cp>=0xff00&&cp<=0xff60)||(cp>=0xffe0&&cp<=0xffe6)||(cp>=0x1f300&&cp<=0x1faff)||(cp>=0x20000&&cp<=0x3fffd));}
  // Wrapping waits for the next character, as xterm does, so "text at the last column, then \r" stays on one line.
  function termPut(ch,cp){const w=termWide(cp)?2:1;if(term.cols&&term.col+w>term.cols){term.row++;term.col=0;}
    const line=termLine();while(line.length<term.col)line.push([' ',TERM_PLAIN]);
    line[term.col]=[ch,term.style];if(w===2)line[term.col+1]=null;term.col+=w;termMark();}
  function termSgr(p){const a={...term.attr};
    for(let i=0;i<p.length;i++){const n=p[i];
      if(n===0)for(const k of Object.keys(a))delete a[k];
      else if(n===1)a.b=1;else if(n===2)a.d=1;else if(n===3)a.i=1;else if(n===4)a.u=1;else if(n===7)a.r=1;
      else if(n===22){delete a.b;delete a.d;}else if(n===23)delete a.i;else if(n===24)delete a.u;else if(n===27)delete a.r;
      else if(n>=30&&n<=37)a.fg=termColor(n-30);else if(n>=90&&n<=97)a.fg=termColor(n-82);else if(n===39)delete a.fg;
      else if(n>=40&&n<=47)a.bg=termColor(n-40);else if(n>=100&&n<=107)a.bg=termColor(n-92);else if(n===49)delete a.bg;
      else if(n===38||n===48){const k=n===38?'fg':'bg';
        if(p[i+1]===5&&p[i+2]!=null){a[k]=termColor(Math.min(255,p[i+2]));i+=2;}
        else if(p[i+1]===2&&p[i+4]!=null){a[k]='rgb('+[p[i+2],p[i+3],p[i+4]].map(v=>Math.min(255,v)).join(',')+')';i+=4;}}}
    term.attr=a;term.style=termStyle(a);}
  function termCsi(params,final){
    if(/^[?>=]/.test(params)){
      // Full-screen programs (vim, top) switch to the alternate screen; say that they will not look right here.
      if((final==='h'||final==='l')&&params.slice(1).split(';').some(v=>v==='1049'||v==='1047'||v==='47')){term.alt=final==='h';termStatus();}
      return;}
    const p=params.split(';').map(v=>{const n=parseInt(v,10);return isNaN(n)?null:n;});const a=(k,d)=>p[k]==null?d:p[k];
    switch(final){
      case 'm':termSgr(p.map(v=>v??0));return;
      case 'A':term.row=Math.max(termTop(),term.row-a(0,1));break;
      case 'B':term.row+=a(0,1);break;
      case 'C':term.col+=a(0,1);if(term.cols)term.col=Math.min(term.cols-1,term.col);break;
      case 'D':term.col=Math.max(0,term.col-a(0,1));break;
      case 'G':term.col=Math.max(0,a(0,1)-1);break;
      case 'H':case 'f':term.row=termTop()+Math.max(0,a(0,1)-1);term.col=Math.max(0,a(1,1)-1);break;
      case 'K':{const l=termLine(),m=a(0,0);if(m===0)l.length=Math.min(l.length,term.col);else if(m===1){for(let c=0;c<=term.col&&c<l.length;c++)l[c]=[' ',TERM_PLAIN];}else l.length=0;break;}
      case 'J':{const m=a(0,0);if(m===2||m===3){termClearAll();return;}
        if(m===0){const l=termLine();l.length=Math.min(l.length,term.col);term.lines.length=term.row+1;}
        else{const top=termTop();for(let r=top;r<term.row;r++)term.lines[r]=[];term.dirty=Math.min(term.dirty,top);}break;}
      case 'P':termLine().splice(term.col,a(0,1));break;
      case '@':{const l=termLine();if(term.col<l.length)l.splice(term.col,0,...Array.from({length:Math.min(500,a(0,1))},()=>[' ',TERM_PLAIN]));break;}
      case 'X':{const l=termLine();for(let c=term.col;c<term.col+a(0,1)&&c<l.length;c++)l[c]=[' ',TERM_PLAIN];break;}
      default:return;}
    termMark();}
  function termWrite(text){const s=term.carry+text;term.carry='';const n=s.length;let i=0;
    while(i<n){const ch=s[i];
      if(ch==='\x1b'){
        if(i+1>=n){term.carry=s.slice(i);break;}const k=s[i+1];
        if(k==='['){let j=i+2;while(j<n&&s[j]>='0'&&s[j]<='?')j++;while(j<n&&s[j]>=' '&&s[j]<='/')j++;
          if(j>=n){term.carry=s.slice(i);break;}termCsi(s.slice(i+2,j),s[j]);i=j+1;continue;}
        if(k===']'||k==='P'||k==='_'||k==='^'){let j=i+2,end=-1;
          while(j<n){if(s[j]==='\x07'){end=j+1;break;}if(s[j]==='\x1b'&&s[j+1]==='\\'){end=j+2;break;}j++;}
          if(end<0){if(n-i<4096)term.carry=s.slice(i);i=n;break;}i=end;continue;}
        if('()*+#'.includes(k)){if(i+2>=n){term.carry=s.slice(i);break;}i+=3;continue;}
        if(k==='7')term.saved=[term.row,term.col];else if(k==='8'&&term.saved){[term.row,term.col]=term.saved;termMark();}
        else if(k==='M'){term.row=Math.max(termTop(),term.row-1);termMark();}else if(k==='c')termClearAll();
        i+=2;continue;}
      const code=ch.charCodeAt(0);
      if(code<32||code===127){
        if(ch==='\r')term.col=0;else if(ch==='\n')term.row++;else if(ch==='\b')term.col=Math.max(0,term.col-1);
        else if(ch==='\t')term.col=Math.min(term.cols?term.cols-1:1e6,(Math.floor(term.col/8)+1)*8);
        termMark();i++;continue;}
      const cp=s.codePointAt(i);const len=cp>0xffff?2:1;termPut(s.slice(i,i+len),cp);i+=len;}
    if(term.lines.length>TERM_LINES){const d=term.lines.length-TERM_LINES;term.lines.splice(0,d);term.row=Math.max(0,term.row-d);
      term.dropped+=d;term.dirty=Math.max(0,term.dirty-d);term.cursorRow=Math.max(0,term.cursorRow-d);if(term.saved)term.saved[0]=Math.max(0,term.saved[0]-d);}}
  function termRenderLine(line,cursorCol){const div=el('div',undefined,'t-line');let text='',style=null;
    const flush=()=>{if(!text)return;const s=el('span',text,style.cls);if(style.fg)s.style.color=style.fg;if(style.bg)s.style.background=style.bg;div.append(s);text='';};
    const n=Math.max(line.length,cursorCol+1);
    for(let c=0;c<n;c++){const cell=c<line.length?line[c]:[' ',TERM_PLAIN];
      if(c===cursorCol){flush();style=null;div.append(el('span',cell?cell[0]:' ','t-cursor'));continue;}
      if(cell===null)continue;if(cell[1]!==style){flush();style=cell[1];}text+=cell[0];}
    flush();return div;}
  // Only the lines that changed since the last paint are rebuilt (plus the old and new cursor lines).
  function termPaint(full){const box=$('term-screen');const showCursor=term.alive&&!term.error;
    const stick=box.scrollHeight-box.scrollTop-box.clientHeight<40;
    if(full||term.full){box.replaceChildren();term.full=false;term.dropped=0;term.dirty=0;}
    for(;term.dropped>0&&box.firstChild;term.dropped--)box.firstChild.remove();term.dropped=0;
    while(box.children.length>term.lines.length)box.lastChild.remove();
    const from=Math.min(term.dirty,term.cursorRow,box.children.length);
    for(let i=from;i<term.lines.length;i++){const node=termRenderLine(term.lines[i],showCursor&&i===term.row?term.col:-1);
      if(i<box.children.length)box.children[i].replaceWith(node);else box.append(node);}
    term.dirty=Infinity;term.cursorRow=term.row;
    if(stick||full)box.scrollTop=box.scrollHeight;
    termSecret();}
  // A password prompt on the cursor line switches the input to hidden characters until it is answered.
  function termSecret(){const text=(term.lines[term.row]||[]).map(c=>c?c[0]:'').join('');const input=$('term-input');
    const secret=/(password|passphrase|密码)[^:：\n]{0,60}[:：]\s*$/i.test(text);const want=secret?'password':'text';
    if(input.type!==want){input.type=want;input.placeholder=secret?'输入密码（不会显示），回车确认':'输入命令，回车执行；C:\\ 这样的 Windows 路径也能用';}}
  function termStatus(){const s=$('term-cwd');if(!s)return;s.classList.toggle('error',!!term.error);s.title=term.cwd||'';
    s.textContent=term.error||(term.alt?'全屏程序在这里显示不正常：按 Ctrl+C 或输入 q 退出':term.alive?'运行中 · 起点是本对话的工作目录':
      !term.started?'':!term.opened?'正在启动…':'已结束'+(term.exitCode!=null?'（退出码 '+term.exitCode+'）':'')+' · 输入命令会重新打开');}
  function termVisible(){return side.open&&side.tab==='terminal'&&side.mode==='shell'&&state.frame?.id===term.frame;}
  function termSize(){const box=$('term-screen');if(!box||box.clientWidth<120)return {cols:term.cols||100,rows:term.rows||30};
    const probe=el('span','MMMMMMMMMM','t-probe');box.append(probe);const r=probe.getBoundingClientRect();probe.remove();
    const w=r.width/10||7.5,h=r.height||19;term.cols=Math.max(20,Math.min(500,Math.floor((box.clientWidth-22)/w)));term.rows=Math.max(5,Math.min(500,Math.floor((box.clientHeight-16)/h)));
    return {cols:term.cols,rows:term.rows};}
  function termErrorText(code){return code==='WORKBENCH_UNAVAILABLE'?'终端需要新版运行环境：请重新启动 Leo AI 后再试。':
    code==='TERMINAL_START_FAILED'?'终端没有启动：请确认 WSL 可以使用，然后点「重新开始」。':
    code==='TERMINAL_NOT_RUNNING'?'终端已经结束：输入命令或点「重新开始」会打开一个新的终端。':
    code==='TERMINAL_FRAME_INVALID'?'这个对话的工作目录不可用。':(errorText[code]||code);}
  function termApply(r){
    if(r.truncated&&r.text){termWrite('\x1b[2m[更早的输出超出了保留范围，已省略]\x1b[0m\r\n');}
    if(r.text)termWrite(r.text);term.next=typeof r.next==='number'?r.next:term.next;
    term.alive=r.alive===true;if(term.alive)term.opened=true;term.exitCode=r.exitCode??null;term.cwd=r.cwd||term.cwd;
    term.error=r.error?termErrorText(r.error):'';term.idle=r.text?0:term.idle+1;
    termPaint();termStatus();return r.more===true;}
  async function termCall(op,extra){const gen=term.gen,fid=term.frame;if(!fid)return;term.busy=true;clearTimeout(term.timer);let more=false;
    try{const r=await request(op,{frameId:fid,...extra});if(gen!==term.gen)return;more=termApply(r);}
    catch(e){if(gen!==term.gen)return;term.error=termErrorText(e.message);term.alive=false;if(op!=='terminal_read')term.started=false;termPaint();termStatus();}
    finally{if(gen===term.gen)term.busy=false;}
    termSchedule(more);}
  function termSchedule(more){clearTimeout(term.timer);if(!termVisible()||!term.alive)return;
    term.timer=setTimeout(()=>act(termPoll)(),more?0:Math.min(1000,120+term.idle*90));}
  async function termPoll(){if(!termVisible()||term.busy||!term.alive)return;await termCall('terminal_read',{after:term.next});}
  // A shell is opened the first time the tab is shown for a conversation and kept while Leo runs;
  // coming back to the conversation replays what it printed (up to the kept amount).
  async function termStart(){if(!state.frame)return;if(term.frame!==state.frame.id)termReset(state.frame.id);
    termPaint(true);termStatus();
    if(term.started){if(term.alive&&!term.busy)await termPoll();return;}
    term.started=true;termStatus();await termCall('terminal_open',{after:0,...termSize()});}
  async function termSend(data){if(!state.frame)return;if(term.frame!==state.frame.id)termReset(state.frame.id);
    if(!term.alive){term.started=true;term.error='';await termCall('terminal_open',{after:0,...termSize()});if(!term.alive)return;}
    try{await request('terminal_input',{frameId:term.frame,data});}catch(e){term.error=termErrorText(e.message);term.alive=false;termStatus();return;}
    term.idle=0;if(!term.busy){clearTimeout(term.timer);term.timer=setTimeout(()=>act(termPoll)(),40);}}
  async function termRestart(){if(!state.frame)return;termReset(state.frame.id);term.started=true;termPaint(true);termStatus();
    await termCall('terminal_restart',{after:0,...termSize()});$('term-input').focus();}
  function termClear(){term.lines=[(term.lines[term.row]||[])];term.row=0;term.saved=null;termPaint(true);$('term-input').focus();}
  // Both kinds of path work (owner, 2026-09-29): a Windows path typed here (C:\Users\… or C:/…, quoted or
  // not) is sent as its WSL form /mnt/c/Users/…, so the screen shows what bash actually ran. WSL paths
  // pass unchanged, and so does a line that calls a Windows program (x.exe, cmd, powershell), which
  // expects Windows paths.
  function termPaths(line){
    if(/\.exe\b|^\s*(cmd|powershell|pwsh|wslpath)\b/i.test(line))return line;
    const wsl=(d,rest)=>'/mnt/'+d.toLowerCase()+(rest||'').replace(/\\/g,'/');
    // A backslash before ; | & $ ` and the other shell metacharacters is an escape.
    // Turning that backslash into a slash would run the character. Leave the token.
    const meta=/[;&|<>`$(){}[\]*?!~#]/;
    const safe=(rest,full,end)=>!/\\[;&|<>`$(){}[\]*?!~#]/.test(rest)&&!(rest.endsWith('\\')&&end<full.length&&meta.test(full[end]));
    return line.replace(/(^|[\s=(])(["'])([A-Za-z]):((?:[\\/](?:(?!\2).)*)?)\2/g,(m,pre,q,d,rest,offset,full)=>
        safe(rest,full,offset+m.length)?pre+q+wsl(d,rest)+q:m)
      .replace(/(^|[\s=(])([A-Za-z]):([\\/][^\s"';&|<>`$(){}[\]*?!~#]*)/g,(m,pre,d,rest,offset,full)=>
        safe(rest,full,offset+m.length)?pre+wsl(d,rest):m);}
  function termEnter(){const input=$('term-input');const value=input.value;const secret=input.type==='password';
    if(value.trim()&&!secret&&term.history[term.history.length-1]!==value){term.history.push(value);if(term.history.length>200)term.history.shift();}
    term.hpos=term.history.length;term.draft='';input.value='';act(()=>termSend((secret?value:termPaths(value))+'\r'))();}
  // Enter sends the line; Ctrl+C (with nothing selected) interrupts; Tab asks the shell to complete what is
  // typed so far; Backspace on an empty box deletes in the shell's own line; ↑/↓ recall earlier commands.
  function termKey(e){const input=e.target;if(e.isComposing)return;const tab=e.key==='Tab'&&!e.shiftKey&&!e.ctrlKey&&!e.altKey;
    if(e.key==='Enter'){e.preventDefault();term.lastTab=false;termEnter();return;}
    if(e.ctrlKey&&!e.shiftKey&&!e.altKey&&(e.key==='c'||e.key==='C')&&input.selectionStart===input.selectionEnd){e.preventDefault();input.value='';act(()=>termSend('\x03'))();return;}
    if(e.ctrlKey&&(e.key==='d'||e.key==='D')&&!input.value){e.preventDefault();act(()=>termSend('\x04'))();return;}
    if(e.ctrlKey&&(e.key==='l'||e.key==='L')){e.preventDefault();termClear();return;}
    if(tab&&(input.value||term.lastTab)){e.preventDefault();const v=input.value;input.value='';term.lastTab=true;act(()=>termSend(termPaths(v)+'\t'))();return;}
    if(!tab)term.lastTab=false;
    if(e.key==='Backspace'&&!input.value){e.preventDefault();act(()=>termSend('\x7f'))();return;}
    if((e.key==='ArrowUp'||e.key==='ArrowDown')&&term.history.length){e.preventDefault();if(term.hpos===term.history.length)term.draft=input.value;
      term.hpos=Math.max(0,Math.min(term.history.length,term.hpos+(e.key==='ArrowUp'?-1:1)));
      input.value=term.hpos===term.history.length?term.draft:term.history[term.hpos];}}
  function termResizeSoon(){clearTimeout(term.resizeTimer);term.resizeTimer=setTimeout(()=>{if(!termVisible()||!term.alive)return;const old=term.cols+'x'+term.rows;
    const size=termSize();if(size.cols+'x'+size.rows!==old)request('terminal_resize',{frameId:term.frame,...size}).catch(()=>{});},300);}

  /* 3.2.1 · 「Python」: the person's code runs as one cell in this conversation's kernel (the same
     kernel as Leo's cells, so variables carry over both ways); the log shows Leo's cells and yours. */
  const py={frame:null,history:[],hpos:0,draft:''};
  function pyReset(fid){clearTimeout(py.timer);Object.assign(py,{frame:fid,runs:[],cells:null,omitted:0,timer:null,busy:false,hidden:0,arts:null,figs:0,images:new Map(),chain:Promise.resolve(),sig:'',stick:true,autoTop:0,hpos:py.history.length});}
  pyReset(null);
  async function pyRefresh(){if(!state.frame)return;if(py.frame!==state.frame.id)pyReset(state.frame.id);if(py.busy)return;
    const fid=py.frame;py.busy=true;clearTimeout(py.timer);
    try{const log=await request('notebook',{frameId:fid});if(py.frame!==fid)return;py.cells=log.entries||[];py.omitted=log.omitted||0;
      for(const run of py.runs){const cell=py.cells.find(c=>c.pythonRun===run.runId);if(cell){run.cell=cell;run.done=cell.status!=='running'&&cell.status!=='queued';}}
      const figs=py.cells.reduce((n,c)=>n+(c.figures?.length||0),0);
      if(figs&&figs!==py.figs){py.figs=figs;try{const a=await request('artifacts',{frameId:fid});if(py.frame!==fid)return;py.arts=a.artifacts||[];}catch(_){py.arts=py.arts||[];}}
      if(side.open&&side.tab==='python')renderPython();
    }finally{if(py.frame===fid)py.busy=false;}
    const waiting=py.runs.some(r=>!r.done)||(py.cells||[]).some(c=>c.status==='running'||c.status==='queued');
    if(side.open&&side.tab==='python'&&(waiting||state.execution))py.timer=setTimeout(()=>act(pyRefresh)(),waiting?1200:2500);}
  function pyFigures(names){const box=el('div',undefined,'nb-figures');const arts=py.arts||[];
    for(const name of names){const fig=el('figure');const base=String(name).split('/').pop();
      const art=arts.find(a=>a.filename===name)||arts.find(a=>(a.filename||'').split('/').pop()===base);
      if(!art){fig.append(el('figcaption',name+' · 未在本对话的产物中找到'));box.append(fig);continue;}
      const img=el('img');img.alt=name;fig.append(img,el('figcaption',name));box.append(fig);
      let shown=py.images.get(art.id);const fid=py.frame;
      // One figure at a time, each read once: previews are base64 round trips through the native bridge.
      if(!shown){shown=py.chain=py.chain.then(async()=>{if(py.frame!==fid)return '';try{const p=await request('artifact_preview',{frameId:fid,artifactId:art.id});return p.kind==='image'?p.dataUri:'';}catch(_){return '';}});py.images.set(art.id,shown);}
      shown.then(uri=>{if(uri){img.onload=pyFollow;img.src=uri;}else{img.hidden=true;fig.append(el('small','图片无法显示','muted'));}});}
    return box;}
  function pyCell(c){const mine=c.origin==='user'||!!c.pythonRun;const row=el('article',undefined,'py-entry'+(mine?' mine':''));const head=el('div',undefined,'term-head');
    const [cls,label]=cellStatus[c.status]||['trust-blocked',c.status||'未知'];
    head.append(el('span',mine?'你':'Leo','term-who'),el('span','单元 '+(c.cellIndex??c.ordinal),'py-index'),sideChip(label,cls));
    if(typeof c.cpuSeconds==='number')head.append(el('span','CPU '+c.cpuSeconds.toFixed(2)+' 秒','py-index'));
    row.append(head);const code=c.terminalRun?'$ '+c.command:(c.source||'（空单元）');
    if(mine)row.append(el('pre',code,'py-code'));
    else{const more=el('details',undefined,'py-more');more.append(el('summary','Leo 运行的代码（'+code.split('\n').length+' 行）'),el('pre',code,'py-code'));row.append(more);}
    if(c.stdout)row.append(el('pre',c.stdout,'term-out'));if(c.stderr)row.append(el('pre',c.stderr,'term-out stderr'));if(c.error)row.append(el('pre',c.error,'term-out error'));
    if(c.figures?.length)row.append(pyFigures(c.figures));
    if(c.truncated)row.append(el('p','输出较长，只显示前 64 KB；完整结果在「笔记本与计算」。','term-note'));
    return row;}
  function pyPending(run){const row=el('article',undefined,'py-entry mine pending');const head=el('div',undefined,'term-head');head.append(el('span','你','term-who'));
    if(run.error)head.append(sideChip('没有提交','trust-failed'));else if(run.stopping)head.append(sideChip('正在停止','trust-blocked'));
    else head.append(sideChip(run.queue?'排队中（前面还有 '+run.queue+' 个）':'运行中','trust-compute'));
    row.append(head,el('pre',run.code,'py-code'));if(run.error)row.append(el('p',run.error,'term-note'));
    else if(!run.stopping)row.append(el('p','如果代码里调用了系统命令，可能需要在左侧对话里审批。','term-note'));
    return row;}
  function renderPython(force){const host=$('py-log');
    const cells=(py.cells||[]).filter(c=>c.ordinal>py.hidden);const pending=py.runs.filter(r=>!r.cell);
    const busy=py.runs.some(r=>!r.done&&!r.error);$('py-stop').hidden=!busy;$('py-state').textContent=busy?'运行中…':'在本对话的沙箱内核里运行 · 不联网';
    const sig=JSON.stringify([cells,pending,py.omitted,py.hidden,py.arts?.length??-1,!!py.cells]);if(!force&&sig===py.sig)return;py.sig=sig;
    const stick=force||py.stick;host.replaceChildren();
    if(!py.cells&&!pending.length){host.append(el('p','正在读取…','term-empty'));return;}
    if(py.hidden)host.append(el('p','已清屏。之前的单元仍在「笔记本与计算」里。','term-note'));
    else if(py.omitted)host.append(el('p','较早的 '+py.omitted+' 个单元未显示；完整记录在「笔记本与计算」。','term-note'));
    if(!cells.length&&!pending.length)host.append(el('p','在下面写 Python 代码，Ctrl+Enter 运行。Leo 在这个对话里运行的代码也会列在这里。','term-empty'));
    for(const c of cells)host.append(pyCell(c));
    for(const run of pending)host.append(pyPending(run));
    if(stick)pyBottom();}
  async function pyRun(event){event?.preventDefault?.();const input=$('py-input');const code=input.value;if(!code.trim()||!state.frame)return;
    if(code.length>100000){notice('代码太长：一次最多 10 万个字符。');return;}
    if(py.frame!==state.frame.id)pyReset(state.frame.id);const fid=py.frame;
    const run={runId:randomRunId(),code,done:false,cell:null,error:'',queue:null,stopping:false};py.runs.push(run);
    if(py.history[py.history.length-1]!==code){py.history.push(code);if(py.history.length>100)py.history.shift();}py.hpos=py.history.length;py.draft='';
    input.value='';pyGrow();renderPython(true);
    try{const r=await request('python_run',{frameId:fid,runId:run.runId,code});run.queue=r.queuePosition||null;}
    catch(e){run.error=e.message==='WORKBENCH_UNAVAILABLE'?'Python 需要新版运行环境：请重新启动 Leo AI 后再试。':(errorText[e.message]||e.message);run.done=true;}
    if(py.frame===fid){renderPython(true);refreshChat(state.epoch).catch(()=>{});setTimeout(()=>act(pyRefresh)(),500);}}
  async function pyStop(){const fid=py.frame;
    for(const run of py.runs)if(!run.done&&!run.error&&!run.stopping){run.stopping=true;renderPython(true);
      try{await request('python_interrupt',{frameId:fid,runId:run.runId});}catch(e){run.stopping=false;renderPython(true);
        if(e.message==='PYTHON_INTERRUPT_REFUSED'){notice('没有停下：这个单元可能还在排队，或者已经结束。');continue;}throw e;}}
    setTimeout(()=>act(pyRefresh)(),600);}
  function pyClear(){py.hidden=Math.max(py.hidden,...(py.cells||[]).map(c=>c.ordinal));py.runs=py.runs.filter(r=>!r.done);renderPython(true);$('py-input').focus();}
  // The log follows new output (and figures as they arrive) unless the person has scrolled up to read.
  // Only a scroll above where Leo last put the log counts as the person scrolling away.
  function pyBottom(){const h=$('py-log');h.scrollTop=h.scrollHeight;py.autoTop=h.scrollTop;}
  function pyFollow(){if(py.stick)pyBottom();}
  function pyGrow(){const box=$('py-input');box.style.height='auto';box.style.height=Math.min(260,Math.max(84,box.scrollHeight))+'px';}
  // Ctrl+Enter runs; Tab indents with four spaces (Esc first to move on with Tab); Ctrl+↑/↓ recall earlier code.
  function pyKey(e){const box=e.target;if(e.isComposing)return;
    if(e.key==='Escape'){py.escaped=true;return;}
    if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();act(pyRun)();return;}
    if(e.key==='Tab'&&!e.shiftKey&&!e.ctrlKey&&!e.altKey&&!py.escaped){e.preventDefault();const a=box.selectionStart,b=box.selectionEnd;
      box.value=box.value.slice(0,a)+'    '+box.value.slice(b);box.selectionStart=box.selectionEnd=a+4;return;}
    py.escaped=false;
    if(e.ctrlKey&&(e.key==='ArrowUp'||e.key==='ArrowDown')&&py.history.length){e.preventDefault();if(py.hpos===py.history.length)py.draft=box.value;
      py.hpos=Math.max(0,Math.min(py.history.length,py.hpos+(e.key==='ArrowUp'?-1:1)));box.value=py.hpos===py.history.length?py.draft:py.history[py.hpos];pyGrow();}}
  /* 3.1.0 · Files for the AI. Each file goes to this conversation's working directory as soon as it
     is added (📎, dragged in or pasted), where the AI opens it by name; the next message lists them.
     A name already used here is saved under a new name rather than silently replacing that file. */
  const attach={frame:null,items:[],seq:0};
  const UPLOAD_LIMIT=25*1024*1024;
  function uploadName(name){const base=String(name||'').split(/[\\/]/).pop().trim();const dot=base.lastIndexOf('.');
    let stem=dot>0?base.slice(0,dot):base,ext=dot>0?base.slice(dot+1):'';
    stem=stem.replace(/[^\p{L}\p{N}\p{M}_.-]+/gu,'_').replace(/^[._]+|[._]+$/g,'').slice(0,100)||'file';ext=ext.replace(/[^A-Za-z0-9]+/g,'').slice(0,12);
    return stem+(ext?'.'+ext:'');}
  function freeName(name,taken){if(!taken.has(name))return name;const dot=name.lastIndexOf('.');const stem=dot>0?name.slice(0,dot):name,ext=dot>0?name.slice(dot):'';
    for(let n=2;n<1000;n++){const next=stem+'-'+n+ext;if(!taken.has(next))return next;}return stem+'-'+Date.now()+ext;}
  function fileSize(n){return n<1024?n+' B':n<1048576?(n/1024).toFixed(n<10240?1:0)+' KB':(n/1048576).toFixed(1)+' MB';}
  function readyAttachments(fid){return attach.frame===fid?attach.items.filter(i=>i.status==='ready').map(i=>i.name):[];}
  function attachmentsBusy(fid){return attach.frame===fid&&attach.items.some(i=>i.status==='uploading');}
  function clearAttachments(fid){if(attach.frame===fid){attach.items=attach.items.filter(i=>i.status==='uploading');renderAttachments();}}
  function renderAttachments(){const host=$('attachments');host.replaceChildren();const items=attach.frame===state.frame?.id?attach.items:[];host.hidden=!items.length;
    for(const item of items){const chip=el('span',undefined,'attachment '+item.status);
      chip.append(el('span',item.status==='uploading'?'上传中':item.status==='error'?'没有添加':'已添加','attachment-state'),el('strong',item.name),el('small',item.error||fileSize(item.size)));
      if(item.status!=='uploading'){const x=el('button','×','attachment-remove');x.type='button';x.title=item.status==='ready'?'不在下一条消息里提到这个文件（文件仍在工作目录里）':'移除';x.setAttribute('aria-label','移除 '+item.name);
        x.onclick=()=>{attach.items=attach.items.filter(i=>i!==item);renderAttachments();};chip.append(x);}
      host.append(chip);}}
  function readBase64(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]||'');reader.onerror=()=>reject(new Error('读取文件失败。'));reader.readAsDataURL(file);});}
  async function addFiles(list){const files=Array.from(list||[]);if(!files.length||!state.frame)return;const fid=state.frame.id;
    if(state.execution){notice('对话正在运行，结束后再添加文件。');return;}
    if(attach.frame!==fid){attach.frame=fid;attach.items=[];}
    let taken=new Set();try{taken=new Set(((await request('artifacts',{frameId:fid})).artifacts||[]).map(a=>a.filename));}catch(_){}
    for(const i of attach.items)taken.add(i.name);
    for(const file of files){const name=freeName(uploadName(file.name),taken);taken.add(name);
      const item={key:++attach.seq,name,size:file.size,status:'uploading',error:''};attach.items.push(item);renderAttachments();
      if(file.size>UPLOAD_LIMIT){item.status='error';item.error='超过 25 MB';renderAttachments();continue;}
      try{const saved=await request('upload',{frameId:fid,filename:name,data:await readBase64(file)});item.name=saved.filename||name;item.status='ready';}
      catch(e){item.status='error';item.error=e.message==='WORKBENCH_CONFLICT'?'对话正在运行':(errorText[e.message]||e.message);}
      if(attach.frame===fid)renderAttachments();}}
  /* 3.1.0 · 「插件」: the daemon's skills, and connectors Leo has checked. The page never sees or sends a
     connector's launch command; adding one names an entry Leo knows, and a failed test says only that. */
  const plugins={skills:[],connectors:[],available:[],limit:60};
  function toggle(checked,label,onChange){const box=el('label',undefined,'switch');box.title=label;const input=el('input');input.type='checkbox';input.checked=checked;
    input.setAttribute('aria-label',label);input.onchange=act(async()=>{input.disabled=true;try{await onChange(input.checked);}catch(e){input.checked=!input.checked;throw e;}finally{input.disabled=false;}});
    box.append(input,el('span',undefined,'switch-track'));return box;}
  async function loadPlugins(){$('skill-status').textContent='正在读取技能…';$('connector-status').textContent='正在读取连接器…';
    const [skills,connectors]=await Promise.all([request('skills').catch(e=>({error:e})),request('connectors').catch(e=>({error:e}))]);
    if(skills.error){plugins.skills=[];$('skill-status').textContent='技能列表暂时读不到：'+(errorText[skills.error.message]||skills.error.message);}
    else{plugins.skills=skills.skills||[];$('skill-status').textContent='';}
    if(connectors.error){plugins.connectors=[];plugins.available=[];$('connector-status').textContent='连接器列表暂时读不到：'+(errorText[connectors.error.message]||connectors.error.message);}
    else{plugins.connectors=connectors.connectors||[];plugins.available=connectors.available||[];$('connector-status').textContent='';}
    renderSkills();renderConnectors();act(loadSearchKey)();}
  /* 3.2.9 · 联网搜索: without a key Leo scrapes Bing and other free engines, which from mainland China often
     find nothing or the wrong thing. A Tavily key is sent once to the daemon's own search setting; the page
     never reads it back, only whether one is set. */
  function searchKeyStatus(configured,note){$('search-key-status').textContent=(configured?'已配置搜索 API Key。':'未配置：使用免费网页搜索（国内常搜不到）。')+(note?' '+note:'');
    $('search-key-clear').hidden=!configured;}
  async function loadSearchKey(){$('search-key-status').textContent='正在读取…';
    try{const r=await request('search_config');searchKeyStatus(r.configured);}catch(e){$('search-key-status').textContent='暂时读不到：'+(errorText[e.message]||e.message);}}
  $('search-key-save').onclick=act(async()=>{const input=$('search-key');const key=input.value.trim();
    if(!key||/\s/.test(key)){$('search-key-status').textContent='请粘贴完整的 API Key（不含空格）。';return;}
    const r=await request('search_key_save',{apiKey:key});input.value='';searchKeyStatus(r.configured,'已保存，立即生效。');});
  $('search-key-clear').onclick=act(async()=>{if(!await confirmAction('清除搜索 API Key','清除后联网搜索改用免费网页搜索。'))return;
    const r=await request('search_key_clear');searchKeyStatus(r.configured,'已清除。');});
  /* 3.2.3 · A bundled collection (bioSkills: 561 recipes) is one row with one switch; Leo sets every member.
     Its members show only when searched for. Biology is off by default (Leo switches it off once). */
  const SKILL_COLLECTIONS={bioskills:{title:'生物学技能合集',text:'Open4S 的 bioSkills：基因组、转录组、单细胞、结构生物学等生物信息学方法。默认关闭。'}};
  function collectionTitle(id){return SKILL_COLLECTIONS[id]?.title||id;}
  function collectionRow(id,members){const on=members.filter(s=>s.enabled).length;const row=el('div',undefined,'plugin-row plugin-collection');
    const text=el('div',undefined,'plugin-text');const title=el('div',undefined,'plugin-title');title.append(el('strong',collectionTitle(id)),el('code',id));text.append(title);
    if(SKILL_COLLECTIONS[id])text.append(el('p',SKILL_COLLECTIONS[id].text));
    const tags=el('div',undefined,'plugin-tags');tags.append(el('span','内置','plugin-tag'),el('span',members.length+' 个技能','plugin-tag'),
      el('span',on===0?'已关闭':on===members.length?'已打开':'部分打开（'+on+' 个）','plugin-tag'+(on&&on<members.length?' warn':'')));text.append(tags);
    const actions=el('div',undefined,'plugin-actions');
    actions.append(toggle(on===members.length,(on===members.length?'关闭':'打开')+'整组 '+collectionTitle(id),async v=>{
      $('skill-status').textContent=(v?'正在打开':'正在关闭')+'「'+collectionTitle(id)+'」的 '+members.length+' 个技能，请稍候…';
      try{await request('skill_collection_toggle',{collection:id,enabled:v});}finally{$('skill-status').textContent='';}
      await loadPlugins();}));
    row.append(text,actions);return row;}
  function renderSkills(){const host=$('skill-list');host.replaceChildren();const q=$('skill-search').value.trim().toLowerCase();
    const mine=s=>s.scope!=='bundled'?0:1;
    const groups=new Map();for(const s of plugins.skills)if(s.collection){if(!groups.has(s.collection))groups.set(s.collection,[]);groups.get(s.collection).push(s);}
    const found=plugins.skills.filter(s=>q?(s.title+' '+s.name+' '+s.description).toLowerCase().includes(q):!s.collection).sort((a,b)=>mine(a)-mine(b)||a.title.localeCompare(b.title,'zh'));
    if(!q)for(const [id,members] of groups)host.append(collectionRow(id,members));
    if(!plugins.skills.length&&!$('skill-status').textContent)host.append(el('p','没有找到技能。','muted'));
    else if(q&&!found.length)host.append(el('p','没有名称或说明包含「'+$('skill-search').value.trim()+'」的技能。','muted'));
    for(const skill of found.slice(0,plugins.limit)){const row=el('div',undefined,'plugin-row');const text=el('div',undefined,'plugin-text');
      const title=el('div',undefined,'plugin-title');title.append(el('strong',skill.title),el('code',skill.name));
      const tags=el('div',undefined,'plugin-tags');tags.append(el('span',skill.scope==='bundled'?'内置':skill.scope==='project'?'项目':'你导入的','plugin-tag'));
      if(skill.collection)tags.append(el('span','属于「'+collectionTitle(skill.collection)+'」','plugin-tag'));
      if(skill.ready==='needs_setup')tags.append(el('span','这台电脑缺少：'+(skill.missing.join('、')||'运行条件'),'plugin-tag warn'));
      text.append(title);if(skill.description)text.append(el('p',skill.description));text.append(tags);
      const actions=el('div',undefined,'plugin-actions');
      if(skill.editable&&skill.scope!=='bundled'){const del=el('button','删除','quiet danger-outline');del.type='button';
        del.onclick=act(async()=>{if(!await confirmAction('删除技能','删除你导入的技能「'+skill.title+'」。内置技能不受影响。'))return;await request('skill_delete',{name:skill.name});await loadPlugins();});actions.append(del);}
      actions.append(toggle(skill.enabled,(skill.enabled?'关闭':'打开')+'技能 '+skill.title,async on=>{await request('skill_toggle',{name:skill.name,enabled:on});skill.enabled=on;}));
      row.append(text,actions);host.append(row);}
    if(found.length>plugins.limit){const more=el('button','再显示 '+Math.min(60,found.length-plugins.limit)+' 个（共 '+found.length+' 个）','quiet plugin-more');more.type='button';
      more.onclick=()=>{plugins.limit+=60;renderSkills();};host.append(more);}}
  function renderConnectors(){const host=$('connector-list');host.replaceChildren();
    for(const c of plugins.connectors){const row=el('div',undefined,'plugin-row');const text=el('div',undefined,'plugin-text');
      const title=el('div',undefined,'plugin-title');title.append(el('strong',c.name),el('code',c.id));text.append(title);if(c.description)text.append(el('p',c.description));
      const tags=el('div',undefined,'plugin-tags');tags.append(el('span',c.leoChecked?'Leo 已检查':'不是 Leo 提供的','plugin-tag'+(c.leoChecked?'':' warn')));
      if(c.hasCredentials)tags.append(el('span','带有凭据','plugin-tag'));if(c.managed)tags.append(el('span','由上游托管','plugin-tag'));
      const result=el('span','','plugin-probe');tags.append(result);text.append(tags);
      const actions=el('div',undefined,'plugin-actions');
      if(!c.managed){const test=el('button','测试','quiet');test.type='button';test.title='启动一次这个连接器并列出它提供的工具';
        test.onclick=act(async()=>{test.disabled=true;result.className='plugin-probe';result.textContent='测试中…';
          try{const r=await request('connector_probe',{id:c.id});result.className='plugin-probe '+(r.ok?'ok':'bad');
            result.textContent=r.ok?'可用 · '+r.count+' 个工具'+(r.tools.length?'：'+r.tools.slice(0,6).join('、')+(r.count>6?' 等':''):''):'没有连上。可以关掉它，或移除后重新添加。';}
          finally{test.disabled=false;}});
        const del=el('button','移除','quiet danger-outline');del.type='button';
        del.onclick=act(async()=>{if(!await confirmAction('移除连接器','移除「'+c.name+'」。所有对话都不能再使用它提供的工具。'))return;await request('connector_delete',{id:c.id});await loadPlugins();});
        actions.append(test,del);}
      actions.append(toggle(c.enabled,(c.enabled?'关闭':'打开')+'连接器 '+c.name,async on=>{await request('connector_toggle',{id:c.id,enabled:on});c.enabled=on;}));
      row.append(text,actions);host.append(row);}
    for(const a of plugins.available){const row=el('div',undefined,'plugin-row available');const text=el('div',undefined,'plugin-text');
      const title=el('div',undefined,'plugin-title');title.append(el('strong',a.name),el('code',a.id));text.append(title,el('p',a.description));
      const add=el('button','添加','secondary');add.type='button';add.onclick=act(async()=>{add.disabled=true;try{await request('connector_add',{id:a.id});await loadPlugins();}finally{add.disabled=false;}});
      const actions=el('div',undefined,'plugin-actions');actions.append(add);row.append(text,actions);host.append(row);}
    if(!plugins.connectors.length&&!plugins.available.length&&!$('connector-status').textContent)host.append(el('p','没有连接器。','muted'));}
  async function importSkill(file){if(!file)return;if(file.size>1024*1024)throw new Error('SKILL.md 超过 1 MB。');
    $('skill-status').textContent='正在导入…';
    try{await request('skill_import',{content:await file.text()});}
    catch(e){$('skill-status').textContent='导入没有成功：请确认文件是 SKILL.md（开头写有 name 和 description），并且名字没有和已有技能重复。';return;}
    await loadPlugins();$('skill-status').textContent='已导入「'+file.name+'」。';}
  const REPEAT_TEXT={once:'仅一次',daily:'每天',weekdays:'每个工作日',weekly:'每周'};
  const RUN_STATUS={sent:['已完成','ok'],sent_late:['已补发','ok'],missed:['已错过','miss'],failed:['发送失败','bad'],sending:['发送中',''],dismissed:['已忽略','']};
  const pad=n=>String(n).padStart(2,'0');
  function localDate(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
  function whenParts(stamp,repeat){if(!stamp)return ['—',REPEAT_TEXT[repeat]||''];const d=new Date(stamp);const today=new Date();today.setHours(0,0,0,0);
    const day=new Date(d);day.setHours(0,0,0,0);const diff=Math.round((day-today)/864e5);
    const dayText=diff===0?'今天':diff===1?'明天':diff===-1?'昨天':(d.getMonth()+1)+'月'+d.getDate()+'日';
    const repeatText=repeat==='weekly'?'每周'+'日一二三四五六'[d.getDay()]:REPEAT_TEXT[repeat]||'';
    return [pad(d.getHours())+':'+pad(d.getMinutes()),repeat?dayText+' · '+repeatText:dayText];}
  // 3.1.0 · Renamed: a second `chip` in the same scope silently replaced the notebook's own chip.
  function schedChip(text,kind){return el('span',text,'sched-chip'+(kind?' '+kind:''));}
  function scheduleRow(item){const row=el('div',undefined,'sched-item'+(item.enabled?'':' paused'));
    const [clock,sub]=whenParts(item.nextRun||item.date+'T'+item.time,item.repeat);const when=el('div',undefined,'sched-when');when.append(el('b',clock),el('small',item.enabled?sub:(item.repeat==='weekly'?'每周'+'日一二三四五六'[new Date(item.date+'T00:00').getDay()]:REPEAT_TEXT[item.repeat])));
    const what=el('div',undefined,'sched-what');what.append(el('strong',item.frameName),el('p','「'+item.text+'」'));
    const meta=el('div',undefined,'sched-meta');meta.append(schedChip(item.enabled?'已启用':'已暂停',item.enabled?'ok':''),schedChip('发往：'+item.frameName));what.append(meta);
    const ops=el('div',undefined,'sched-ops');
    const toggle=el('button',item.enabled?'暂停':'继续','quiet');toggle.onclick=act(async()=>{await request('schedule_toggle',{id:item.id,enabled:!item.enabled});await loadSchedules();});
    const edit=el('button','编辑','quiet');edit.onclick=act(()=>openScheduleDialog(item));
    const del=el('button','删除','quiet deny');del.onclick=act(async()=>{if(!await confirmAction('删除定时任务','「'+item.frameName+'」的这个定时任务将被删除，已发送的消息不受影响。'))return;await request('schedule_delete',{id:item.id});await loadSchedules();});
    ops.append(toggle,edit,del);row.append(when,what,ops);return row;}
  function historyRow(h){const [label,kind]=RUN_STATUS[h.status]||[h.status,''];const row=el('div',undefined,'sched-item'+(h.status==='missed'?' missed':h.status==='failed'?' failed':''));
    const [clock,sub]=whenParts(h.due);const when=el('div',undefined,'sched-when');when.append(el('b',clock),el('small',sub));
    const what=el('div',undefined,'sched-what');what.append(el('strong',h.frameName));
    // 3.1.0 · A reason already ends in its own full stop; it follows a colon instead of being bracketed.
    const reason=h.detail?String(errorText[h.detail]||h.detail).replace(/[。.]?$/,'。'):'';
    const text={missed:'Leo 当时没有打开，这一次没有发送。',failed:reason?'没有发出：'+reason:'没有发出。',sent:'已发送。',sent_late:'已由你手动补发。',sending:'正在发送。',dismissed:'已忽略这一次。'}[h.status]||'';
    what.append(el('p',text));const meta=el('div',undefined,'sched-meta');meta.append(schedChip(label,kind));what.append(meta);
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
  $('terminal-button').onclick=()=>side.open&&side.tab==='terminal'?closeSide():openSide('terminal');
  $('python-button').onclick=()=>side.open&&side.tab==='python'?closeSide():openSide('python');
  $('web-button').onclick=()=>side.open&&side.tab==='web'?closeSide():openSide('web');
  $('side-close').onclick=closeSide;$('side-refresh').onclick=act(()=>refreshSide(true));
  for(const b of document.querySelectorAll('[data-side-tab]'))b.onclick=()=>{selectSideTab(b.dataset.sideTab);renderSide();act(refreshSide)();};
  $('term-mode-shell').onclick=()=>{selectTermMode('shell');renderSide();act(refreshSide)();$('term-input').focus();};
  $('term-mode-log').onclick=()=>{selectTermMode('log');renderSide();act(refreshSide)();};
  $('term-form').onsubmit=e=>{e.preventDefault();termEnter();};
  $('term-input').onkeydown=termKey;
  $('term-ctrlc').onclick=()=>{act(()=>termSend('\x03'))();$('term-input').focus();};
  $('term-clear').onclick=termClear;$('term-restart').onclick=act(termRestart);
  $('term-screen').onmouseup=()=>{if(!String(globalThis.getSelection?.()||''))$('term-input').focus();};
  globalThis.addEventListener?.('resize',termResizeSoon);
  $('py-form').onsubmit=act(pyRun);$('py-input').onkeydown=pyKey;$('py-input').oninput=pyGrow;
  $('py-stop').onclick=act(pyStop);$('py-clear').onclick=pyClear;
  $('py-log').onscroll=()=>{const h=$('py-log');if(h.scrollTop<(py.autoTop||0)-4)py.stick=false;else if(h.scrollHeight-h.scrollTop-h.clientHeight<40)py.stick=true;};
  $('nb-refresh').onclick=act(()=>loadNotebook());$('nb-open-chat').onclick=act(()=>nb.frame&&openFrame(nb.frame));$('nb-switch').onclick=act(()=>openNotebook(null));
  $('skill-search').oninput=()=>{plugins.limit=60;renderSkills();};$('skill-import').onclick=()=>$('skill-file').click();
  $('skill-file').onchange=act(async()=>{const input=$('skill-file');const file=input.files?.[0];input.value='';await importSkill(file);});
  $('attach').onclick=()=>$('attach-input').click();
  $('attach-input').onchange=act(async()=>{const input=$('attach-input');const files=Array.from(input.files||[]);input.value='';await addFiles(files);});
  $('message-input').addEventListener('paste',e=>{const files=Array.from(e.clipboardData?.files||[]);if(files.length){e.preventDefault();act(()=>addFiles(files))();}});
  // A file dropped anywhere else must never navigate the window; on the composer it is added.
  document.addEventListener('dragover',e=>{if(e.dataTransfer?.types?.includes?.('Files')){e.preventDefault();const over=!!e.target?.closest?.('.composer-wrap')&&current==='chat-view';e.dataTransfer.dropEffect=over?'copy':'none';document.body?.classList.toggle('drop-files',over);}});
  document.addEventListener('dragleave',e=>{if(!e.relatedTarget)document.body?.classList.remove('drop-files');});
  document.addEventListener('drop',e=>{if(!e.dataTransfer?.files?.length)return;e.preventDefault();document.body?.classList.remove('drop-files');if(e.target?.closest?.('.composer-wrap')&&current==='chat-view')act(()=>addFiles(e.dataTransfer.files))();});
  $('card-chat').onclick=act(newFrame);$('send').onclick=act(send);$('message-input').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();act(send)();}};
  $('stop').onclick=act(async()=>{const e=state.execution;const owner=e.owner||{kind:e.owner_kind||e.kind,id:e.owner_id||e.id};await request('cancel',{frameId:state.frame.id,executionId:e.execution_id,owner});await refreshChat();});
  $('approval-button').onclick=()=>{const pop=$('approval-pop');pop.hidden=!pop.hidden;$('approval-button').setAttribute('aria-expanded',String(!pop.hidden));};
  $('usage-button').onclick=()=>{const pop=$('usage-pop');pop.hidden=!pop.hidden;$('usage-button').setAttribute('aria-expanded',String(!pop.hidden));if(!pop.hidden)act(loadUsage)();};
  $('usage-temp').oninput=()=>{$('usage-temp-value').textContent=Number($('usage-temp').value).toFixed(1);};
  $('usage-temp').onchange=act(()=>setTemperature(Number($('usage-temp').value)));
  $('usage-temp-reset').onclick=act(()=>setTemperature(null));
  $('usage-fulltext').onclick=openFullText;$('fulltext-close').onclick=()=>$('fulltext-dialog').close();
  $('usage-pop').addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();closeUsagePop();$('usage-button').focus();}});
  document.addEventListener('pointerdown',e=>{if(!e.target?.closest?.('.usage-picker,#fulltext-dialog'))closeUsagePop();});
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
  // 3.1.0 · A dialog's sticky header draws its hairline only once the body has scrolled beneath it.
  document.addEventListener('scroll',e=>{const d=e.target;if(d?.classList?.contains('settings-dialog'))d.classList.toggle('is-scrolled',d.scrollTop>2);},true);
  window.LeoShell={openSettings:()=>act(settings)()};window.LeoWorkbench={request,session:()=>({frameId:state.frame?.id,projectId:state.project}),ready:true,math};
  window.setStatus=message=>notice(message);
  window.addEventListener('pywebviewready',start,{once:true});if(window.pywebview?.api)start();
  setTimeout(()=>{if(!started){notice('正在等待桌面连接。若长时间未连接，请重新打开 Leo AI Studio。');}},12000);
})();
