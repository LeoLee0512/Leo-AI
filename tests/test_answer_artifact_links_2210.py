"""2.2.10: a link to a file in an answer is a button that previews the file, never a raw Markdown string."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest


def test_artifact_links_in_an_answer_open_a_preview_through_the_gateway():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    harness = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
class Element {
  addEventListener(){}
  constructor(){this.children=[];this.value='';this.hidden=false;this.classList={add(){},remove(){}};this.lastChild={};}
  append(...items){this.children.push(...items)} replaceChildren(...items){this.children=[...items]}
  querySelector(){return this.child||(this.child=new Element())} focus(){} setAttribute(){}
  showModal(){this.open=true} close(){this.open=false}
}
const flush=async()=>{for(let i=0;i<20;i++)await new Promise(r=>setImmediate(r));};
const text=n=>(n.textContent||'')+(n.children||[]).map(text).join('');
const walk=(n,out=[])=>{if(n.className==='artifact-link')out.push(n);for(const c of n.children||[])walk(c,out);return out;};
(async()=>{
  const nodes=new Map(), calls=[];
  const el=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id)};
  const frame={id:'f-link',project_id:'p-link',name:'Files'};
  const content='结果见 [out/fig.png](/api/artifacts/a-fig000000001) 和 [data\\[1\\].csv](/api/artifacts/a-csv000000002)。\n'+
    '版本链接 [r.csv](/api/v1/artifacts/versions/v-abc123)，缺失 [ghost.txt](/api/artifacts/nothere)，外链 [站点](https://example.com/x)。';
  const listed=[{id:'a-fig000000001',filename:'out/fig.png',contentType:'image/png',size:10,versionId:''},
    {id:'a-csv000000002',filename:'data[1].csv',contentType:'text/csv',size:20,versionId:''},
    {id:'a-ver000000003',filename:'r.csv',contentType:'text/csv',size:5,versionId:'v-abc123'}];
  const api={get_state:async()=>({profiles:[]}),list_entity_states:async()=>({entities:[]}),
    list_session_models:async()=>({binding:null,models:[]}),
    workbench_request:async p=>{calls.push(p);return {data:{projects:{projects:[{id:'p-link',name:'P'}]},frames:{frames:[frame]},
      messages:{messages:[{seq:1,message_id:'u-1',role:'user',content:'画图'},{seq:2,message_id:'a-2',role:'assistant',content}],has_earlier:false},
      execution:{owner:null},feedback:{feedback:{}},artifacts:{artifacts:listed},
      artifact_preview:p.artifactId==='a-fig000000001'?{id:p.artifactId,kind:'image',dataUri:'data:image/png;base64,AAAA'}
        :{id:p.artifactId,kind:'text',text:'x,y',truncated:false}}[p.operation]};}};
  const ctx=vm.createContext({window:{pywebview:{api},addEventListener(){}},
    document:{getElementById:el,createElement:()=>new Element(),createTextNode:t=>({textContent:t}),addEventListener(){},querySelectorAll(){return []},
      querySelector(selector){return selector===".desktop-menu"?new Element():null}},setTimeout:()=>1,clearTimeout(){}});
  vm.runInContext(source,ctx);await flush();
  await el('history').children.find(c=>String(c.className).includes('history-row')).children[0].onclick();await flush();
  const links=walk(el('messages'));
  assert.deepEqual(links.map(b=>b.textContent),['out/fig.png','data[1].csv','r.csv','ghost.txt']);
  const shown=text(el('messages'));
  assert.ok(!shown.includes('/api/artifacts/'),'no raw artifact address is left in the text');
  assert.ok(shown.includes('[站点](https://example.com/x)'),'an external link is left as plain text, never opened');
  // Reading the conversation's files is the first request; the preview asks for the listed id only.
  await links[0].onclick();await flush();
  assert.equal(el('artifact-dialog').open,true);
  assert.equal(el('artifact-dialog-title').textContent,'out/fig.png');
  assert.equal(el('artifact-dialog-body').children[0].src,'data:image/png;base64,AAAA');
  await links[1].onclick();await flush();
  assert.equal(el('artifact-dialog-body').children[0].textContent,'x,y');
  assert.equal(calls.filter(c=>c.operation==='artifacts').length,1,'the file list is read once, not per click');
  await links[2].onclick();await flush();
  assert.equal(calls.filter(c=>c.operation==='artifact_preview').at(-1).artifactId,'a-ver000000003');
  // A file that is not in this conversation is never requested.
  const before=calls.filter(c=>c.operation==='artifact_preview').length;
  await links[3].onclick();await flush();
  assert.match(el('artifact-dialog-body').children[0].textContent,/不在本对话的产物中/);
  assert.equal(calls.filter(c=>c.operation==='artifact_preview').length,before);
  assert.ok(calls.filter(c=>c.operation==='artifact_preview').every(c=>c.frameId==='f-link'));
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result = subprocess.run([node, '-e', harness], input=json.dumps(source), encoding='utf-8', capture_output=True)
    assert result.returncode == 0, result.stderr
