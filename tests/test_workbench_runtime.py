"""Execute the owned frontend with a restarted daemon's public model binding."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest


def test_chat_projects_one_answer_without_runtime_completion_checklists():
    """Exercise polling, reopening and copy against the actual owned document."""
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    harness = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  addEventListener(){}
  constructor(){this.children=[];this.value='';this.classList={add(){},remove(){}};this.lastChild={};}
  append(...items){this.children.push(...items)} replaceChildren(){this.children=[]}
  querySelector(){return this.child||(this.child=new Element())} focus(){} setAttribute(){} showModal(){} close(){}
}
const flush=async()=>{for(let i=0;i<10;i++)await new Promise(r=>setImmediate(r));};
const text=n=>(n.textContent||'')+(n.children||[]).map(text).join('');
async function scenario(messages,expected,expectedCopy=expected[0]){
  const original=JSON.stringify(messages),nodes=new Map(),copied=[];let timer;
  const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
  const frame={id:'f-chat',project_id:'p-chat',name:'Greeting'};
  const api={get_state:async()=>({profiles:[]}),list_entity_states:async()=>({entities:[]}),
    list_session_models:async()=>({binding:null,models:[]}),
    workbench_request:async p=>({data:{projects:{projects:[{id:'p-chat',name:'Project'}]},frames:{frames:[frame]},
      messages:{messages,has_earlier:false},execution:{owner:null},feedback:{feedback:{}}}[p.operation]})};
  const ctx=vm.createContext({window:{pywebview:{api},navigator:{clipboard:{writeText:async t=>copied.push(t)}},addEventListener(){}},
    document:{getElementById:el,createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},querySelector(selector){return selector===".desktop-menu"?new Element():null}},
    setTimeout:fn=>{timer=fn;return 1},clearTimeout(){}});
  vm.runInContext(source,ctx);await flush();
  const check=()=>assert.deepEqual(el('messages').children.filter(n=>n.className?.startsWith('message assistant'))
    .map(n=>n.children.filter(c=>c.className==='message-body').map(text).join('')),expected);
  await el('history').children[0].onclick();check();
  timer();await flush();check(); // The same persisted rows arrive again.
  await el('history').children[0].onclick();check(); // Reopen history.
  const answer=el('messages').children.find(n=>n.className==='message assistant');
  if(answer){await answer.children.at(-1).children[0].onclick();assert.equal(copied[0],expectedCopy);}
  assert.equal(JSON.stringify(messages),original,'rendering must not mutate stored messages');
}
const u=(seq,content='你好')=>({seq,message_id:'u-'+seq,role:'user',content});
const a=(seq,content,extra={})=>({seq,message_id:'a-'+seq,role:'assistant',content,...extra});
(async()=>{
  const answer='你好，我是Leo AI。有什么可以帮你的吗？';
  await scenario([u(1),a(2,answer),a(3,answer+'\n\n完成内容：\n- Answered the greeting')],[answer]);
  await scenario([u(1),a(2,answer),a(3,'完成内容：\n- Answered the greeting')],[answer]);
  await scenario([u(1),a(2,answer),a(3,answer)],[answer]);
  await scenario([u(1),a(2,'Hello\n\nCompleted work:\n- Answered the question')],['Hello']);
  await scenario([u(1),a(2,answer),u(3),a(4,answer)],[answer,answer]);
  await scenario([u(1),a(2,'第一步'),a(3,'不同的补充')],['第一步','不同的补充']);
  await scenario([u(1),a(2,'结果\n\n完成内容：\n- Computed the result\n\n限制与局限：\n尚未验证\n\n产物：\n- report.txt')],
    ['结果\n\n\n限制与局限：\n尚未验证\n\n产物：\n- report.txt']);
  await scenario([u(1),a(2,'> 完成内容：\n> - 用户引用的文字')],['> 完成内容：\n> - 用户引用的文字']);
  await scenario([u(1),a(2,answer),a(3,answer,{failure:{request_id:'failed-1'}})],[answer,answer]);
  await scenario([u(1),a(2,answer),a(3,answer,{review_status:'candidate'})],[answer,answer]);
  await scenario([u(1),a(2,answer),a(3,answer,{artifact_refs:[{id:'a-file'}]})],[answer,answer]);
  // The same words inside a fenced example remain visible (as a code block).
  await scenario([u(1),a(2,'Example\n```text\n完成内容：\n- A literal example\n```')],['Example\n'],'Example\n完成内容：\n- A literal example');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result = subprocess.run([node, '-e', harness], input=json.dumps(source), encoding='utf-8', capture_output=True)
    assert result.returncode == 0, result.stderr


def test_workbench_restores_credentials_and_freezes_every_turn():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    harness = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  addEventListener(){}
  constructor(){this.children=[];this.value='';this.classList={add(){},remove(){}};this.lastChild={};}
  append(...items){this.children.push(...items)} replaceChildren(){this.children=[]}
  querySelector(){return this.child||(this.child=new Element())} focus(){} showModal(){this.open=true} close(){this.open=false}
}
async function scenario(restoreFails=false,changed=false){
  const nodes=new Map(), calls=[];
  const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
  const frame={id:'f-test',project_id:'p-test',name:'Test'};
  const binding={profile_id:'mp-leo-test',revision:2,native_profile_id:'native-test',credential_ready:false,
    reasoning:{revision:'cap-v2',choices:[{id:'default',available:true}]}};
  let reads=0;
  const api={
    get_state:async function(){assert.equal(arguments.length,0);return {profiles:[{name:"Model",model:"model-test",has_key:true}]};},
    return_to_start:async function(){assert.equal(arguments.length,0);calls.push(["start"]);},
    open_model_settings:async function(){assert.equal(arguments.length,0);calls.push(["settings"]);},
    list_entity_states:async()=>({entities:[]}),
    list_session_models:async()=>({binding:{...binding,revision:changed&&++reads>1?3:2},models:[]}),
    select_session_model:async payload=>{calls.push(['restore',payload]);return restoreFails?{ok:false,message:'MODEL_KEY_UNAVAILABLE'}:{binding:{...binding,credential_ready:true}}},
    workbench_request:async payload=>{calls.push([payload.operation,payload]);const data={
      projects:{projects:[{id:'p-test',name:'Project'}]},frames:{frames:[frame]},messages:{messages:[]},execution:{owner:null,queue:[]},send:{job_id:'job-test'}
    }[payload.operation];return {data};}
  };
  const ctx=vm.createContext({window:{pywebview:{api},addEventListener(){}},document:{getElementById:el,
    createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},querySelector(selector){return selector===".desktop-menu"?new Element():null}},
    setTimeout:()=>1,clearTimeout(){}});
  vm.runInContext(source,ctx);
  await new Promise(r=>setImmediate(r));
  await el('settings-button').onclick();
  assert.equal(el('settings-dialog').open,true);
  await el('configure-models').onclick();
  // Editing models remains in the current document and keeps the dialog open.
  assert.equal(el('model-editor').hidden,false);
  assert.equal(el('settings-dialog').open,true);
  assert.equal(calls.find(c=>c[0]==='settings'),undefined);
  assert.equal(calls.find(c=>c[0]==='start'),undefined);
  await el('history').children[0].onclick();
  el('message-input').value='A real user question';
  await el('send').onclick();
  const sent=calls.find(c=>c[0]==='send');
  if(restoreFails||changed){assert.equal(sent,undefined);assert.equal(el('message-input').value,'A real user question');return;}
  assert.deepEqual(JSON.parse(JSON.stringify(calls.find(c=>c[0]==='restore')[1])),{
    frame_id:'f-test',native_profile_id:'native-test',expected_binding:{profile_id:'mp-leo-test',revision:2}});
  assert.deepEqual(JSON.parse(JSON.stringify(sent[1].modelBinding)),{profile_id:'mp-leo-test',revision:2});
  assert.deepEqual(JSON.parse(JSON.stringify(sent[1].reasoningSelection)),{choice:'default',capability_revision:'cap-v2'});
  assert.equal(el('message-input').value,'');
}
(async()=>{await scenario();await scenario(true);await scenario(false,true)})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result=subprocess.run([node,'-e',harness],input=json.dumps(source),text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_notebook_view_reads_only_through_the_gateway():
    """The notebook is Leo's own view: listed artifacts only, no upstream page, no execution."""
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    harness = r"""
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  addEventListener(){}
  constructor(){this.children=[];this.value='';this.hidden=false;this.classList={add(){},remove(){}};this.lastChild={};}
  append(...items){this.children.push(...items)} replaceChildren(...items){this.children=[...items]}
  querySelector(){return this.child||(this.child=new Element())} focus(){} showModal(){this.open=true} close(){this.open=false}
}
const flush=async()=>{for(let i=0;i<20;i++)await new Promise(r=>setImmediate(r));};
(async()=>{
  const nodes=new Map(), calls=[], methods=new Set();
  const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
  const frame={id:'f-nb',project_id:'p-nb',name:'Poisson'};
  const entries=[
    {ordinal:1,cellIndex:1,language:'python',status:'ok',source:'x=1',stdout:'1\n',stderr:'',error:'',figures:[],filesWritten:[],attempt:1,attemptCount:1,latest:true,stale:false,cpuSeconds:0.1},
    {ordinal:2,cellIndex:2,language:'python',status:'error',source:'plot()',stdout:'',stderr:'warn',error:'Boom',figures:['out/fig.png','ghost.png'],filesWritten:['out/fig.png'],attempt:2,attemptCount:2,latest:true,stale:true,cpuSeconds:null}];
  const listed=[{id:'a-fig000000001',filename:'out/fig.png',contentType:'image/png',size:10},{id:'a-csv000000002',filename:'data.csv',contentType:'text/csv',size:20}];
  const handler=new Proxy({
    list_entity_states:async()=>({entities:[]}),
    get_state:async function(){assert.equal(arguments.length,0);return {appearance:{theme:'ink-autumn'},profiles:[]};},
    workbench_request:async payload=>{calls.push(payload);const data={
      projects:{projects:[{id:'p-nb',name:'Project'}]},frames:{frames:[frame]},
      notebook:{entries,total:2,omitted:0},kernel:{state:'stopped',alive:false,generation:1},artifacts:{artifacts:listed},
      artifact_preview:payload.artifactId==='a-csv000000002'?{id:payload.artifactId,kind:'text',text:'x,y',truncated:false}:{id:payload.artifactId,kind:'image',dataUri:'data:image/png;base64,AAAA'}
    }[payload.operation];return {data};}
  },{get(target,name){methods.add(String(name));return target[name];}});
  const ctx=vm.createContext({window:{pywebview:{api:handler},addEventListener(){}},document:{getElementById:el,
    createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},querySelector(selector){return selector===".desktop-menu"?new Element():null}},
    setTimeout:()=>1,clearTimeout(){}});
  vm.runInContext(source,ctx);
  await flush();
  await el('nav-tools').onclick();
  assert.equal(el('notebook-view').hidden,false);
  assert.equal(el('home-view').hidden,true);
  const pick=el('nb-empty').children.find(c=>c.className==='nb-pick');
  assert.ok(pick,'picker lists conversations when none is open');
  await pick.children[0].onclick();
  await flush();
  const cells=el('nb-cells').children.filter(c=>c.className==='nb-cell');
  assert.equal(cells.length,2);
  // A figure is fetched by the listed artifact id; a name that is not listed is never requested.
  const previews=calls.filter(c=>c.operation==='artifact_preview');
  assert.deepEqual(previews.map(c=>c.artifactId),['a-fig000000001']);
  assert.ok(previews.every(c=>c.frameId==='f-nb'));
  const figures=cells[1].children.find(c=>c.className==='nb-figures');
  assert.equal(figures.children[0].children[0].src,'data:image/png;base64,AAAA');
  assert.match(figures.children[1].children[0].textContent,/未在本对话的产物中找到/);
  assert.equal(el('nb-kernel').textContent,'内核已停止');
  await el('nb-artifacts').children[1].onclick();
  assert.equal(el('nb-preview').hidden,false);
  assert.equal(el('nb-preview-body').children[0].textContent,'x,y');
  for(const name of ['open_computational_tools','return_to_workbench'])assert.ok(!methods.has(name),name);
  const ops=new Set(calls.map(c=>c.operation));
  for(const op of ops)assert.ok(['projects','frames','notebook','kernel','artifacts','artifact_preview'].includes(op),op);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result=subprocess.run([node,'-e',harness],input=json.dumps(source),text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_message_actions_copy_rate_and_forward_without_sending():
    """Copy takes the selection inside the message; ratings toggle; forwarding only fills an input box."""
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    harness = r"""
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  addEventListener(){}
  constructor(){this.children=[];this.value='';this.hidden=false;this.attrs={};this.classList={add(){},remove(){}};this.lastChild={};this.style={};}
  append(...items){this.children.push(...items)} replaceChildren(...items){this.children=[...items]}
  setAttribute(k,v){this.attrs[k]=v} contains(n){return n===this||this.children.some(c=>c.contains&&c.contains(n))}
  querySelector(){return this.child||(this.child=new Element())} focus(){} showModal(){this.open=true} close(){this.open=false}
}
const flush=async()=>{for(let i=0;i<20;i++)await new Promise(r=>setImmediate(r));};
const find=(node,pred)=>{if(pred(node))return node;for(const c of node.children||[]){const f=find(c,pred);if(f)return f;}return null;};
(async()=>{
  const nodes=new Map(), calls=[], copied=[];
  const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
  const frames=[{id:'f-a',project_id:'p',name:'A'},{id:'f-b',project_id:'p',name:'B'}];
  const messages={messages:[{message_id:'u-1',seq:0,role:'user',content:'What is **u**?'},{message_id:'m-2',seq:1,role:'assistant',content:'## Answer\n**u** solves it.'}]};
  let selection=null;
  const api={
    list_entity_states:async()=>({entities:[]}), get_state:async function(){return {profiles:[]};},
    list_session_models:async()=>({binding:null,models:[]}),
    workbench_request:async payload=>{calls.push(payload);const data={
      projects:{projects:[{id:'p',name:'P'}]},frames:{frames},messages,execution:{owner:null,queue:[]},
      feedback:{feedback:{'m-2':'down'}},set_feedback:{ok:true}}[payload.operation];return {data};}
  };
  const ctx=vm.createContext({window:{pywebview:{api},addEventListener(){},getSelection:()=>selection,
      navigator:{clipboard:{writeText:async t=>{copied.push(t)}}}},
    document:{getElementById:el,createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},querySelector(selector){return selector===".desktop-menu"?new Element():null}},
    setTimeout:()=>1,clearTimeout(){}});
  vm.runInContext(source,ctx);
  await flush();
  await el('history').children[0].onclick();
  await flush();
  const rows=el('messages').children.filter(c=>String(c.className).startsWith('message '));
  assert.equal(rows.length,2);
  const [question,reply]=rows;
  const button=(row,label)=>find(row,n=>n.className&&String(n.className).includes('msg-action')&&n.textContent===label);
  // The copy button briefly reads '已复制' after use; this harness's timers never restore it.
  const copyButton=row=>find(row,n=>String(n.className)==='msg-action'&&/复制/.test(n.textContent));
  assert.ok(!button(question,'赞'),'prompts are not rated');
  // stored rating is shown, and clicking it again clears it
  assert.equal(button(reply,'踩').attrs['aria-pressed'],'true');
  await button(reply,'踩').onclick();await flush();
  assert.deepEqual(JSON.parse(JSON.stringify(calls.filter(c=>c.operation==='set_feedback').pop())),{operation:'set_feedback',frameId:'f-a',key:'m-2',rating:null});
  const replyNow=el('messages').children.filter(c=>String(c.className).startsWith('message '))[1];
  await button(replyNow,'赞').onclick();await flush();
  assert.equal(calls.filter(c=>c.operation==='set_feedback').pop().rating,'up');
  // copy: whole message as displayed, or only a selection made inside it
  const current=el('messages').children.filter(c=>String(c.className).startsWith('message '))[1];
  await copyButton(current).onclick();
  assert.equal(copied.pop(),'Answer\nu solves it.');
  const inside=current.children[1];
  selection={isCollapsed:false,rangeCount:1,getRangeAt:()=>({commonAncestorContainer:inside}),toString:()=>'solves'};
  await copyButton(current).onclick();
  assert.equal(copied.pop(),'solves');
  selection={isCollapsed:false,rangeCount:1,getRangeAt:()=>({commonAncestorContainer:new Element()}),toString:()=>'elsewhere'};
  await copyButton(current).onclick();
  assert.equal(copied.pop(),'Answer\nu solves it.','a selection outside this message is ignored');
  // forward the prompt to another conversation: it lands in that input box and nothing is sent
  const q=el('messages').children.filter(c=>String(c.className).startsWith('message '))[0];
  await button(q,'转发').onclick();
  assert.equal(el('forward-dialog').open,true);
  const target=find(el('forward-targets'),n=>n.className==='forward-target'&&(n.children||[]).some(c=>c.textContent==='B'));
  assert.ok(target,'other conversations are offered');
  assert.ok(!find(el('forward-targets'),n=>n.className==='forward-target'&&(n.children||[]).some(c=>c.textContent==='A')),'not the conversation it came from');
  await target.onclick();await flush();
  assert.equal(el('message-input').value,'What is **u**?');
  assert.equal(el('page-title').textContent,'B');
  assert.ok(!calls.some(c=>c.operation==='send'),'forwarding never sends');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    result=subprocess.run([node,'-e',harness],input=json.dumps(source),text=True,capture_output=True)
    assert result.returncode==0,result.stderr
