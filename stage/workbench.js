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
  function date(value){const parsed=new Date(value);return Number.isNaN(+parsed)?'':parsed.toLocaleDateString('zh-CN',{month:'short',day:'numeric'});}
  function visibleFrames(){return state.frames.filter(f=>!hiddenIds.has(f.id)&&(!state.project||f.project_id===state.project));}

  /* One visible view at a time; the rail and the top bar follow it. */
  const views=['home-view','chat-view','notebook-view'];
  let current='home-view';
  function show(view){
    current=view;
    for(const id of views)$(id).hidden=id!==view;
    $('nav-home').classList[view==='home-view'?'add':'remove']('active');
    $('nav-tools').classList[view==='notebook-view'?'add':'remove']('active');
    $('notebook-button').hidden=view!=='chat-view';
    if(view!=='notebook-view')clearTimeout(nb.timer);
  }
  function updateHeader(){const project=state.projects.find(p=>(p.id||p.project_id)===state.project);$('project-name').textContent=project?.name||'科研空间';$('page-title').textContent=current==='notebook-view'?'笔记本与计算':state.frame?title(state.frame):'工作台';$('rename-chat').hidden=!state.frame||current!=='chat-view';}
  function home(){keepDraft();state.epoch++;nb.epoch++;state.frame=null;state.messages=[];state.execution=null;clearTimeout(poll);show('home-view');updateHeader();renderHistory();}
  function renderHistory(){const query=$('history-search').value.trim().toLowerCase();const frames=visibleFrames();$('history').replaceChildren();for(const f of frames.filter(f=>title(f).toLowerCase().includes(query))){const b=el('button',title(f),'history-item'+(state.frame?.id===f.id?' active':''));b.title=title(f);b.onclick=act(()=>openFrame(f));$('history').append(b);}$('history-count').textContent=String(frames.length);if(!frames.length)$('history').append(el('p','还没有对话。从一个问题开始。','muted'));$('recent-list').replaceChildren();for(const f of frames.slice(0,3)){const b=el('button',undefined,'recent-row');b.append(el('span','↳'),el('strong',title(f)),el('small',date(f.updated_at)),el('span','↗'));b.onclick=act(()=>openFrame(f));$('recent-list').append(b);}if(!frames.length)$('recent-list').append(el('p','开始对话后，可以从这里回到你的思路。','muted'));$('more-history').hidden=!state.cursor;}
  async function loadFrames(append=false){const data=await request('frames',{projectId:state.project||'all',...(append&&state.cursor?{cursor:state.cursor}:{})});state.frames=append?[...state.frames,...(data.frames||[])]:data.frames||[];state.cursor=data.next_cursor||null;renderHistory();}
  async function chooseName(label,value=''){const dialog=$('input-dialog');$('input-dialog-title').textContent=label;$('dialog-value').value=value;dialog.returnValue='';dialog.showModal();$('dialog-value').focus();return new Promise(resolve=>dialog.addEventListener('close',()=>resolve(dialog.returnValue==='save'?$('dialog-value').value.trim():null),{once:true}));}
  async function newFrame(){if(state.loading)return;state.loading=true;try{if(!state.project){const name=await chooseName('给你的第一个项目起个名字','我的研究');if(!name)return;const p=await request('create_project',{name});state.projects.push(p);state.project=p.id||p.project_id;renderProjects();}const f=await request('create_frame',{projectId:state.project});state.frames.unshift(f);await openFrame(f,true);$('message-input').focus();}finally{state.loading=false;}}
  function renderProjects(){const select=$('project-select');select.replaceChildren();for(const p of state.projects){const option=el('option',p.name||'未命名项目');option.value=p.id||p.project_id;select.append(option);}if(!state.projects.length){const option=el('option','新建一个科研项目');option.value='';select.append(option);}select.value=state.project||'';updateHeader();}
  async function refreshModels(fresh=false){const fid=state.frame?.id;if(!fid)return;const data=await native('list_session_models',{frame_id:fid});if(state.frame?.id!==fid)return;state.binding=data.binding;const select=$('model-select');select.replaceChildren();const empty=el('option','选择会话模型');empty.value='';select.append(empty);for(const m of data.models||[]){const o=el('option',m.name+' · '+m.model);o.value=m.id;o.disabled=!m.available;select.append(o);}select.value=data.binding?.native_profile_id||'';if(fresh&&data.active_native_profile_id){select.value=data.active_native_profile_id;await selectModel();}}
  async function selectModel(){const id=$('model-select').value,fid=state.frame?.id;if(!id||!fid)return;const binding=state.binding;const data=await native('select_session_model',{frame_id:fid,native_profile_id:id,expected_binding:{profile_id:binding.profile_id,revision:binding.revision}});if(state.frame?.id===fid)state.binding=data.binding;}
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
    const capability=binding.reasoning;
    if(!capability?.revision||!capability.choices?.some(c=>c.id==='default'&&c.available===true))throw new Error('REASONING_CAPABILITY_CHANGED');
    return {modelBinding:{profile_id:binding.profile_id,revision:binding.revision},reasoningSelection:{choice:'default',capability_revision:capability.revision}};
  }
  function messageContent(host,text){const parts=String(text||'').split(/```[^\n]*\n([\s\S]*?)```/g);parts.forEach((part,i)=>{if(i%2){const pre=el('pre');pre.append(el('code',part));host.append(pre);}else{const body=el('div',undefined,'message-body');for(const [index,line]of part.split('\n').entries()){if(index)body.append(document.createTextNode('\n'));if(/^#{1,3} /.test(line))body.append(el('strong',line.replace(/^#+ /,'')));else{line.split(/(\*\*[^*]+\*\*)/g).forEach(chunk=>body.append(chunk.startsWith('**')&&chunk.endsWith('**')?el('strong',chunk.slice(2,-2)):document.createTextNode(chunk)));}}host.append(body);}});}
  function renderMessages(scroll=false){const area=$('messages');const scroller=$('chat-scroll');const atEnd=scroller.scrollHeight-scroller.scrollTop-scroller.clientHeight<130;area.replaceChildren();if(!state.messages.length){const empty=el('div',undefined,'message-empty');empty.append(el('p','✦','eyebrow'),el('h2','一个好问题，是发现的开始。'),el('p','可以讨论一个原理，也可以整理一个真实研究任务。','muted'));area.append(empty);}for(const m of [...state.messages].sort((a,b)=>a.seq-b.seq)){if(!['assistant','user'].includes(m.role))continue;const row=el('article',undefined,'message '+m.role+(m.failure?' failure':''));row.append(el('header',m.role==='assistant'?'LEO AI':'你'));messageContent(row,m.content);if(m.failure)row.append(el('p','本次调用未完成'+(m.failure.request_id?' · 支持 ID：'+m.failure.request_id:''),'muted'));row.append(actionBar(m,row));area.append(row);}if(scroll||atEnd)scroller.scrollTop=scroller.scrollHeight;}
  function running(execution){state.execution=execution;const active=!!execution;$('working').hidden=!active;$('stop').hidden=!active;$('send').hidden=active;$('model-select').disabled=active;$('elapsed').textContent=active&&openedAt?' · '+Math.max(0,Math.floor((Date.now()-openedAt)/1000))+' 秒':'';}
  async function refreshChat(epoch=state.epoch){const fid=state.frame?.id;if(!fid||epoch!==state.epoch)return;const [data,queue]=await Promise.all([request('messages',{frameId:fid}),request('execution',{frameId:fid})]);if(epoch!==state.epoch)return;const seen=new Map(state.messages.map(m=>[m.message_id||m.seq,m]));for(const m of data.messages||[])seen.set(m.message_id||m.seq,m);const next=[...seen.values()];const changed=JSON.stringify(next)!==JSON.stringify(state.messages);state.messages=next;if(state.before===null){state.before=data.next_before_seq;$('earlier-messages').hidden=!data.has_earlier;}if(changed)renderMessages();const owner=queue.owner||queue.queue?.[0]||null;running(owner);clearTimeout(poll);poll=setTimeout(()=>refreshChat(epoch).catch(e=>{notice(e.message);poll=setTimeout(()=>refreshChat(epoch).catch(e=>notice(e.message)),5000);}),owner?1700:6000);}
  async function openFrame(frame,fresh=false){keepDraft();state.epoch++;nb.epoch++;clearTimeout(poll);state.frame=frame;state.project=frame.project_id;state.messages=[];state.before=null;state.binding=null;openedAt=0;$('message-input').value=drafts.get(frame.id)||'';show('chat-view');$('earlier-messages').hidden=true;$('project-select').value=state.project;updateHeader();renderHistory();renderMessages();state.feedback={};request('feedback',{frameId:frame.id}).then(d=>{if(state.frame?.id===frame.id){state.feedback=d.feedback||{};renderMessages();}}).catch(()=>{});await Promise.all([refreshModels(fresh),refreshChat()]);}
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
    host.append(el('span','⌁','card-icon hue-indigo'),el('h2','选择一个对话，查看它的计算记录'),el('p','笔记本如实记录计算过程；结论是否成立，以验证证据为准。','muted'));
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
    body.replaceChildren();
    if(p.kind==='image'){const img=el('img');img.alt=a.filename||'';img.src=p.dataUri;body.append(img);}
    else if(p.kind==='text'){body.append(el('pre',p.text));if(p.truncated)body.append(el('p','文件较大，只显示前 256 KB。','muted'));}
    else body.append(el('p','这种文件（'+(p.contentType||'未知类型')+(p.size!=null?'，'+size(p.size):'')+'）暂不能在这里预览。','muted'));
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
      empty.append(el('span','⌁','card-icon hue-indigo'),el('h2','这个对话还没有计算记录'),el('p','在对话里请 Leo 运行代码，代码单元、输出和图表会按顺序出现在这里。','muted'));
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

  async function settings(){shellState=await native('get_state');const area=$('settings-profiles');area.replaceChildren();for(const p of shellState.profiles||[]){const row=el('div',undefined,'settings-profile');row.append(el('strong',p.name),el('p',p.model+' · '+(p.has_key?'密钥已保存':'未配置密钥')));area.append(row);}if(!area.childElementCount)area.append(el('p','还没有模型配置。','muted'));$('settings-dialog').showModal();}
  async function applyAppearance(){
    // The start page saves the theme; the workbench follows it instead of keeping its own palette.
    try{const s=await native('get_state');const theme=s?.appearance?.theme;const root=document.documentElement;
      if(root&&typeof theme==='string'&&/^[a-z0-9-]{1,40}$/.test(theme))root.setAttribute('data-leo-theme',theme);}catch(e){}
  }
  async function start(){if(started)return;started=true;applyAppearance();try{const [projects,entities]=await Promise.all([request('projects'),native('list_entity_states',{})]);for(const r of entities.entities||[]){hiddenIds.add(r.entity_id);for(const id of r.snapshot?.member_session_ids||[])hiddenIds.add(id);}state.projects=(projects.projects||[]).filter(p=>!hiddenIds.has(p.id||p.project_id));state.project=state.projects.find(p=>!p.is_example)?.id||state.projects[0]?.id||null;renderProjects();await loadFrames();$('connection').lastChild.textContent=' 工作区已连接';}catch(e){started=false;$('connection').lastChild.textContent=' 连接未完成';notice(e.message);}}
  $('notice').querySelector('button').onclick=()=>{$('notice').hidden=true;};$('new-chat').onclick=act(newFrame);$('nav-home').onclick=home;$('brand-home').onclick=e=>{e.preventDefault();home();};$('home-button').onclick=home;
  for(const id of ['hero-research','card-research','nav-research','composer-research'])$(id).onclick=act(research);
  for(const id of ['card-tools','nav-tools'])$(id).onclick=act(()=>openNotebook());
  $('notebook-button').onclick=act(()=>openNotebook(state.frame));
  $('nb-refresh').onclick=act(()=>loadNotebook());$('nb-open-chat').onclick=act(()=>nb.frame&&openFrame(nb.frame));$('nb-switch').onclick=act(()=>openNotebook(null));
  $('card-chat').onclick=act(newFrame);$('send').onclick=act(send);$('message-input').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();act(send)();}};
  $('stop').onclick=act(async()=>{const e=state.execution;const owner=e.owner||{kind:e.owner_kind||e.kind,id:e.owner_id||e.id};await request('cancel',{frameId:state.frame.id,executionId:e.execution_id,owner});await refreshChat();});
  $('model-select').onchange=act(selectModel);$('history-search').oninput=renderHistory;$('more-history').onclick=act(()=>loadFrames(true));
  $('project-select').onchange=act(async()=>{state.project=$('project-select').value;home();await loadFrames();});
  $('new-project').onclick=act(async()=>{const name=await chooseName('新建项目');if(!name)return;const p=await request('create_project',{name});state.projects.push(p);state.project=p.id||p.project_id;home();renderProjects();await loadFrames();});
  $('rename-chat').onclick=act(async()=>{const name=await chooseName('重命名对话',title(state.frame));if(!name)return;const fid=state.frame.id;await request('rename',{frameId:fid,name});if(state.frame?.id===fid)state.frame.name=name;updateHeader();await loadFrames();});
  $('earlier-messages').onclick=act(async()=>{const epoch=state.epoch;const data=await request('messages',{frameId:state.frame.id,before:state.before});if(epoch!==state.epoch)return;state.before=data.next_before_seq;$('earlier-messages').hidden=!data.has_earlier;const seen=new Map(state.messages.map(m=>[m.message_id||m.seq,m]));for(const m of data.messages||[])seen.set(m.message_id||m.seq,m);state.messages=[...seen.values()];renderMessages();});
  $('forward-close').onclick=()=>$('forward-dialog').close();$('forward-copy').onclick=act(async()=>{if(!forwarding)return;await copyText(shareText(forwarding));flash($('forward-copy'),'已复制分享文本');});
  $('settings-button').onclick=act(settings);$('close-settings').onclick=()=>$('settings-dialog').close();$('configure-models').onclick=act(()=>native('open_model_settings'));
  document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='n'&&!document.querySelector('dialog[open]')){e.preventDefault();act(newFrame)();}});
  window.LeoShell={openSettings:()=>act(settings)()};window.LeoWorkbench={request,session:()=>({frameId:state.frame?.id,projectId:state.project}),ready:true};
  window.setStatus=message=>notice(message);
  window.addEventListener('pywebviewready',start,{once:true});if(window.pywebview?.api)start();
  setTimeout(()=>{if(!started){notice('正在等待桌面连接。若长时间未连接，请重新打开 Leo AI Studio。');}},12000);
})();
