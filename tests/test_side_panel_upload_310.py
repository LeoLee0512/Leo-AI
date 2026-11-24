"""3.1.0: 「网页」 and adding files; 3.2.1: 「终端」 (the person's own shell) and 「Python」, exercised
against the owned workbench document."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

HARNESS = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  constructor(tag){this.localName=tag;this.children=[];this.attrs={};this.style={};this.dataset={};this.value='';this.hidden=false;
    this.classList={add(){},remove(){},toggle(){}};this.scrollTop=0;this.scrollHeight=0;this.clientHeight=0;this.clientWidth=0;}
  addEventListener(type,fn){(this.listeners||(this.listeners={}))[type]=fn;}
  append(...items){for(const i of items){const n=typeof i==='string'?{textContent:i}:i;n.parent=this;this.children.push(n);}}
  replaceChildren(...items){this.children=[];this.append(...items)} querySelector(){return this.child||(this.child=new Element('div'))}
  get firstChild(){return this.children[0]||null} get lastChild(){return this.children.at(-1)||this._last||(this._last={})}
  remove(){if(this.parent)this.parent.children.splice(this.parent.children.indexOf(this),1);this.parent=null;}
  replaceWith(n){const p=this.parent;p.children[p.children.indexOf(this)]=n;n.parent=p;this.parent=null;}
  focus(){} setAttribute(k,v){this.attrs[k]=String(v)} showModal(){this.open=true} close(){this.open=false}
  get textContent(){return this._text??this.children.map(c=>c.textContent).join('')} set textContent(v){this._text=String(v);this.children=[];}
}
const flush=async()=>{for(let i=0;i<30;i++)await new Promise(r=>setImmediate(r));};
const all=(n,out=[])=>{out.push(n);for(const c of n.children||[])all(c,out);return out;};
const find=(n,test)=>all(n).filter(x=>x instanceof Element&&test(x));
(async()=>{
  const nodes=new Map(),calls=[];const el=id=>{if(!nodes.has(id))nodes.set(id,new Element('div'));return nodes.get(id)};
  const frame={id:'f-t',project_id:'p',name:'Term'};let pyDone=false;
  const binding={profile_id:'mp',revision:1,native_profile_id:'np',credential_ready:true,reasoning:{revision:'r1',choices:[{id:'default',available:true}]}};
  const steps=()=>({commands:[{seq:1,status:'done',command:'whoami',exitCode:0,durationMs:3,stdout:'preview-only',stderr:'',changed:[],error:''},
      {seq:2,status:'done',command:'ls',exitCode:0,durationMs:5,stdout:'a\nb\n',stderr:'',stdoutTruncated:false,stderrTruncated:false,changed:[],error:''},
      {seq:3,status:'error',command:'rm x',exitCode:null,durationMs:null,stdout:'',stderr:'',changed:[],error:'Permission denied'}],
    web:[{seq:4,type:'search',query:'pinn',source:'ddg',results:[{title:'Paper',url:'https://doi.org/10.1/x',snippet:'s'}]},
         {seq:5,type:'fetch',url:'https://arxiv.org/abs/1',finalUrl:null,download:false,excerpt:'<script>alert(1)</script>',chars:25,error:''}],
    capped:false,lastSeq:5});
  // What the shell printed: a window title, bracketed-paste mode, a progress line rewritten in place, a coloured prompt.
  const shell={text:'\x1b]0;leo@box: ~\x07loading 10%\rloading 100%\r\n\x1b[?2004h\x1b[01;32mleo@box\x1b[00m:~$ ',next:3,truncated:false,
    alive:true,exitCode:null,cwd:'/home/leo/.local/share/leo-ai-studio/data/agent-workspaces/f-t',error:null,more:false};
  const api={get_state:async()=>({profiles:[]}),list_entity_states:async()=>({entities:[]}),list_session_models:async()=>({binding,models:[{id:'np-local',name:'随便起的名字',model:'local-qwen3-4b',local:true,has_key:false},
      {id:'np',name:'DeepSeek',model:'deepseek-v4-pro',local:false,has_key:true}]}),
    workbench_request:async p=>{calls.push(p);const data={projects:{projects:[{id:'p',name:'P'}]},frames:{frames:[frame]},
      messages:{messages:[{seq:1,message_id:'u1',role:'user',content:'hi'}],has_earlier:false},execution:{owner:null},feedback:{feedback:{}},
      steps:steps(),terminal_open:shell,terminal_input:{ok:true},python_run:{accepted:true,queuePosition:null},python_interrupt:{ok:true},
      notebook:{entries:[{ordinal:1,origin:'user',terminalRun:'aaaaaaaaaaaaaaaa',command:'whoami',status:'ok',stdout:'leo\n\n[exit 0]\n',stderr:'',error:''},
        {ordinal:2,origin:'agent',source:'import numpy as np\nx = np.arange(3)',status:'ok',stdout:'',stderr:'',error:''},
        ...(pyDone?[{ordinal:3,origin:'user',pythonRun:calls.find(c=>c.operation==='python_run').runId,source:'print(x.sum())',status:'ok',stdout:'3\n',stderr:'',error:''}]:[])]},
      artifacts:{artifacts:[{id:'a1',filename:'data.csv'}]},upload:{id:'a2',filename:p.filename},open_link:{opened:false},send:{status:'accepted'},
      approvals:{requests:[],autoApproved:[]},approval_mode:{mode:'smart'},timeline:{groups:[]},thoughts:{thoughts:[]}}[p.operation];
      return {data};}};
  class FileReader{readAsDataURL(file){this.result='data:application/octet-stream;base64,'+file.b64;setImmediate(()=>this.onload());}}
  const ctx=vm.createContext({window:{pywebview:{api},addEventListener(){}},FileReader,
    document:{getElementById:el,createElement:t=>new Element(t),createElementNS:(ns,t)=>new Element(t),createTextNode:t=>({textContent:t}),
      addEventListener(type,fn){(ctx.docListeners||(ctx.docListeners={}))[type]=fn;},querySelectorAll(){return []},querySelector(s){return s==='.desktop-menu'?new Element('div'):null}},
    setTimeout:()=>1,clearTimeout(){}});
  vm.runInContext(source,ctx);await flush();
  await el('history').children.find(c=>String(c.className).includes('history-row')).children[0].onclick();await flush();
  // 3.2.2 · The chat's model list names the local model 「本地模型」, whatever its profile is called.
  const modelNames=el('model-select').children.map(o=>o.textContent);
  assert.ok(modelNames.includes('本地模型')&&modelNames.includes('DeepSeek · deepseek-v4-pro'),modelNames.join('|'));
  // 「终端」: the person's own shell for this conversation. Opening the tab starts it; what is typed goes to it
  // as typed (never as an AI step or a kernel cell), and what it prints is drawn, escape sequences interpreted.
  el('terminal-button').onclick();await flush();
  assert.equal(el('side-panel').hidden,false);
  const open=calls.find(c=>c.operation==='terminal_open');
  assert.deepEqual([open.frameId,open.after],['f-t',0]);
  const screen=el('term-screen').textContent;
  assert.ok(screen.includes('loading 100%')&&screen.includes('leo@box:~$ '),screen);
  assert.ok(!screen.includes('loading 10%l')&&!screen.includes('\x1b')&&!screen.includes('leo@box: ~'),'titles and escapes are not text');
  const prompt=find(el('term-screen'),n=>n.textContent==='leo@box'&&n.style.color)[0];
  assert.ok(prompt&&prompt.className.includes('t-b'),'the coloured, bold part of the prompt keeps its style');
  assert.ok(find(el('term-screen'),n=>n.className==='t-cursor').length===1,'one cursor');
  el('term-input').value='ls -la';el('term-form').onsubmit({preventDefault(){}});await flush();
  el('term-ctrlc').onclick();await flush();
  assert.deepEqual(calls.filter(c=>c.operation==='terminal_input').map(c=>c.data),['ls -la\r','\x03']);
  assert.equal(el('term-input').value,'');
  // Both kinds of path work: Windows paths become their WSL form; WSL paths, URLs and Windows programs stay as typed.
  for(const line of ['cd "C:\\Users\\leo\\数学 建模"','ls D:/data/x.csv C:\\tmp',"cp 'E:\\a b\\c.txt' .",'cd /home/leo',
      'explorer.exe C:\\Users','curl http://x.org/a:b','echo C:\\foo\\;id','echo C:\\$(id)','ls C:\\temp\\|curl evil'])
    {el('term-input').value=line;el('term-form').onsubmit({preventDefault(){}});await flush();}
  assert.deepEqual(calls.filter(c=>c.operation==='terminal_input').map(c=>c.data).slice(2),
    ['cd "/mnt/c/Users/leo/数学 建模"\r','ls /mnt/d/data/x.csv /mnt/c/tmp\r',"cp '/mnt/e/a b/c.txt' .\r",'cd /home/leo\r',
     'explorer.exe C:\\Users\r','curl http://x.org/a:b\r','echo C:\\foo\\;id\r','echo C:\\$(id)\r','ls C:\\temp\\|curl evil\r']);
  assert.ok(!calls.some(c=>['terminal_run','python_run','send'].includes(c.operation)),'the terminal never goes through the AI');
  // 「Leo 执行过的命令」: what the AI ran, labelled; a command typed in the 3.1.0 terminal is still yours.
  el('term-mode-log').onclick();await flush();
  assert.equal(el('term-shell').hidden,true);assert.equal(el('term-leo').hidden,false);
  assert.ok(calls.some(c=>c.operation==='steps'&&c.frameId==='f-t'));
  let rows=find(el('term-log'),n=>String(n.className).startsWith('term-entry'));
  assert.deepEqual(rows.map(r=>find(r,n=>n.className==='term-cmd')[0].textContent),['$ whoami','$ ls','$ rm x']);
  assert.ok(rows[0].className.includes('mine')&&rows[0].textContent.includes('你')&&rows[0].textContent.includes('leo'));
  assert.ok(!rows[1].className.includes('mine'),'an AI command is labelled Leo');
  assert.ok(rows[2].textContent.includes('未执行')&&rows[2].textContent.includes('Permission denied'));
  el('term-mode-shell').onclick();await flush();
  assert.equal(calls.filter(c=>c.operation==='terminal_open').length,1,'coming back reuses the same shell');
  // 「Python」: the person's code runs as one cell in the conversation's kernel, beside Leo's cells.
  el('python-button').onclick();await flush();
  assert.equal(el('side-python').hidden,false);assert.equal(el('side-terminal').hidden,true);
  let cells=find(el('py-log'),n=>String(n.className).startsWith('py-entry'));
  assert.ok(cells.some(c=>!c.className.includes('mine')&&c.textContent.includes('Leo')&&c.textContent.includes('import numpy')));
  el('py-input').value='print(x.sum())';await el('py-form').onsubmit({preventDefault(){}});await flush();
  const pyRun=calls.find(c=>c.operation==='python_run');
  assert.match(pyRun.runId,/^[0-9a-f]{16}$/);assert.equal(pyRun.code,'print(x.sum())');assert.equal(pyRun.frameId,'f-t');
  assert.equal(el('py-input').value,'');assert.equal(el('py-stop').hidden,false,'a running cell can be stopped');
  cells=find(el('py-log'),n=>String(n.className).startsWith('py-entry'));
  assert.ok(cells.at(-1).className.includes('pending')&&cells.at(-1).textContent.includes('print(x.sum())'));
  await el('py-stop').onclick();await flush();
  assert.deepEqual(calls.filter(c=>c.operation==='python_interrupt').map(c=>c.runId),[pyRun.runId]);
  pyDone=true;await el('side-refresh').onclick();await flush();
  cells=find(el('py-log'),n=>String(n.className).startsWith('py-entry'));
  const mine=cells.at(-1);
  assert.ok(mine.className.includes('mine')&&!mine.className.includes('pending')&&mine.textContent.includes('你')&&mine.textContent.includes('3\n'));
  assert.equal(el('py-stop').hidden,true);
  // 「网页」: searches and page reads; a title asks Leo to open it; fetched text stays text.
  el('web-button').onclick();await flush();
  assert.equal(el('side-web').hidden,false);
  const links=find(el('web-log'),n=>String(n.className).includes('web-link'));
  assert.deepEqual(links.map(n=>n.textContent),['https://arxiv.org/abs/1','Paper'],'newest first');
  const link=links[1];assert.equal(link.href,undefined);
  await link.onclick();await flush();
  assert.deepEqual(calls.filter(c=>c.operation==='open_link').map(c=>c.url),['https://doi.org/10.1/x']);
  assert.ok(find(el('web-log'),n=>n.localName==='pre')[0].textContent==='<script>alert(1)</script>');
  assert.ok(!find(el('web-log'),n=>n.localName==='script').length);
  el('side-close').onclick();assert.equal(el('side-panel').hidden,true);
  // Adding a file: a name already used is saved as a new name; the next message lists it.
  el('attach-input').files=[{name:'data.csv',size:4,b64:'eCx5'},{name:'big.bin',size:26*1024*1024,b64:''}];
  await el('attach-input').onchange();await flush();
  const up=calls.filter(c=>c.operation==='upload');
  assert.equal(up.length,1,'a file over 25 MB is never sent');assert.deepEqual([up[0].filename,up[0].data],['data-2.csv','eCx5']);
  assert.ok(el('attachments').textContent.includes('超过 25 MB'));
  el('message-input').value='汇总一下';await el('send').onclick();await flush();
  const sent=calls.find(c=>c.operation==='send');
  assert.equal(sent.text,'汇总一下\n\n[附件，已放入工作目录] data-2.csv');
  assert.ok(!el('attachments').textContent.includes('data-2.csv'),'sent files leave the tray');
  // Dropping a file outside the composer never navigates the window.
  let prevented=false;ctx.docListeners.drop({dataTransfer:{files:[{name:'x'}]},target:{closest:()=>null},preventDefault(){prevented=true;}});
  assert.equal(prevented,true);
})().catch(e=>{console.error(e);process.exitCode=1});
'''


def test_terminal_web_and_upload_in_the_owned_workbench():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    result = subprocess.run([node, '-e', HARNESS], input=json.dumps(source), encoding='utf-8', capture_output=True)
    assert result.returncode == 0, result.stderr
