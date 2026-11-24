"""3.1.0: answers render Markdown and formulas; model text never becomes HTML."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

HARNESS = r'''
const vm=require('node:vm'), assert=require('node:assert/strict');
const {source,withMath}=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
const created=new Set();
class Element {
  constructor(tag,ns){this.localName=tag;this.ns=ns;this.children=[];this.attrs={};this.style={};this.value='';this.classList={add(){},remove(){}};this.lastChild={};created.add(tag);}
  addEventListener(){} append(...items){for(const i of items)this.children.push(typeof i==='string'?{textContent:i}:i)}
  replaceChildren(...items){this.children=[...items]} querySelector(){return this.child||(this.child=new Element('div'))}
  focus(){} setAttribute(k,v){this.attrs[k]=String(v)} showModal(){} close(){}
  get textContent(){return this._text??this.children.map(c=>c.textContent).join('')} set textContent(v){this._text=String(v);this.children=[];}
}
const flush=async()=>{for(let i=0;i<20;i++)await new Promise(r=>setImmediate(r));};
const all=(n,out=[])=>{out.push(n);for(const c of n.children||[])all(c,out);return out;};
const find=(n,test)=>all(n).filter(x=>x instanceof Element&&test(x));
const tags=n=>(n.children||[]).filter(c=>c instanceof Element).map(c=>c.localName);
const answers=[
  '## 标题\n\n第一行\n第二行 `code` **粗** *斜* ~~删~~ snake_case_name 与 a_b，价格 $5 和 $10。\n\n- 一\n  - 一点一\n- 二\n\n3. 三\n4. 四\n\n> 引用\n\n---\n\n- [x] 完成\n- [ ] 未完成',
  '| 名 | 值 |\n|:--|--:|\n| a | $|x|$ |',
  '行内 $\\frac{a}{b}$，求和 $\\sum_{i=1}^{n} i$，积分 $\\int_0^1 f$，集合 $\\mathbb{R}^n$，坏的 $\\frac{a$，未知 $\\foo$。\n\n$$\nE=mc^2\n$$\n\n\\begin{aligned}\na &= b\\\\\nc &= d\n\\end{aligned}',
  '文件 [fig.png](/api/artifacts/a-1)，外链 [站点](https://example.com/x)，相对 [说明](docs/a.md)，<img src=x onerror=alert(1)><script>alert(2)</script>'];
(async()=>{
  const nodes=new Map(),calls=[];const el=id=>{if(!nodes.has(id))nodes.set(id,new Element('div'));return nodes.get(id)};
  const messages=[{seq:1,message_id:'u-1',role:'user',content:'**原样** $x$\n- 不是列表'}];
  answers.forEach((content,i)=>messages.push({seq:2*i+2,message_id:'q-'+i,role:'user',content:'问'},{seq:2*i+3,message_id:'a-'+i,role:'assistant',content}));
  const frame={id:'f',project_id:'p',name:'Render'};
  const api={get_state:async()=>({profiles:[]}),list_entity_states:async()=>({entities:[]}),list_session_models:async()=>({binding:null,models:[]}),
    workbench_request:async p=>{calls.push(p);return {data:{projects:{projects:[{id:'p',name:'P'}]},frames:{frames:[frame]},messages:{messages,has_earlier:false},
      execution:{owner:null},feedback:{feedback:{}},artifacts:{artifacts:[]}}[p.operation]};}};
  const globals={window:{pywebview:{api},addEventListener(){}},
    document:{getElementById:el,createElement:t=>new Element(t),createElementNS:(ns,t)=>new Element(t,ns),createTextNode:t=>({textContent:t}),
      addEventListener(){},querySelectorAll(){return []},querySelector(s){return s==='.desktop-menu'?new Element('div'):null}},
    setTimeout:()=>1,clearTimeout(){}};
  if(withMath)globals.MathMLElement=function(){};
  vm.runInContext(source,vm.createContext(globals));await flush();
  created.clear();
  await el('history').children.find(c=>String(c.className).includes('history-row')).children[0].onclick();await flush();
  const rows=el('messages').children.filter(n=>String(n.className).startsWith('message '));
  const body=row=>row.children.find(c=>c.className==='message-body');
  // A question is shown exactly as typed.
  const question=body(rows[0]);
  assert.equal(question.textContent,'**原样** $x$\n- 不是列表');assert.deepEqual(question.children,[]);
  const [md,table,maths,links]=rows.filter(r=>r.className==='message assistant').map(body);
  // Blocks.
  assert.deepEqual(tags(md),['h4','p','ul','ol','blockquote','hr','ul']);
  assert.equal(md.children[1].textContent,'第一行\n第二行 code 粗 斜 删 snake_case_name 与 a_b，价格 $5 和 $10。');
  assert.deepEqual(tags(md.children[1]),['code','strong','em','del']);
  assert.deepEqual(tags(md.children[2].children[0]),['p','ul'],'a nested list stays inside its item');
  assert.equal(md.children[3].start,3);
  assert.deepEqual(find(md.children[6],n=>n.className==='md-check').map(n=>n.textContent),['☑','☐']);
  // Tables: alignment, and a | inside a formula is not a column break.
  const cells=find(table,n=>n.localName==='td');
  assert.equal(cells.length,2);assert.deepEqual([cells[0].style.textAlign,cells[1].style.textAlign],['left','right']);
  // Formulas.
  const p=maths.children[0];
  if(withMath){
    const math=find(p,n=>n.localName==='math');
    assert.equal(math.length,5,'five formulas parse; the broken one does not');
    assert.deepEqual(tags(math[0]),['mfrac']);assert.deepEqual(tags(math[0].children[0]),['mi','mi']);
    assert.ok(find(math[1],n=>n.localName==='munderover').length===1,'a sum takes its limits above and below');
    assert.ok(find(math[2],n=>n.localName==='msubsup').length===1,'an integral takes its limits as scripts');
    assert.equal(find(math[3],n=>n.localName==='mi')[0].textContent,'ℝ');
    assert.equal(find(math[4],n=>n.attrs.class==='tex-unknown')[0].textContent,'\\foo','an unknown command stays visible');
    assert.deepEqual(find(p,n=>n.className==='tex-raw').map(n=>n.textContent),['\\frac{a'],'a formula that does not parse shows its source');
    const blocks=maths.children.slice(1);
    assert.deepEqual(blocks.map(b=>b.className),['md-math','md-math']);
    assert.equal(blocks[0].children[0].attrs.display,'block');
    const aligned=find(blocks[1],n=>n.localName==='mtd');
    assert.equal(aligned.length,4);assert.match(aligned[0].attrs.style,/-webkit-right/);assert.match(aligned[1].attrs.style,/-webkit-left/);
  }else{
    assert.equal(find(maths,n=>n.localName==='math').length,0);
    assert.deepEqual(find(p,n=>n.className==='tex-raw').map(n=>n.textContent),
      ['\\frac{a}{b}','\\sum_{i=1}^{n} i','\\int_0^1 f','\\mathbb{R}^n','\\frac{a','\\foo'],'without MathML every formula shows its source');
  }
  // Links: a file previews, a web link asks Leo, anything else is its words only. Tags stay text.
  const file=find(links,n=>n.className==='artifact-link')[0],web=find(links,n=>n.className==='web-link')[0];
  assert.equal(file.localName,'a');assert.equal(file.attrs.role,'button');assert.equal(file.tabIndex,0);assert.equal(file.href,undefined);
  assert.equal(web.textContent,'站点');assert.equal(web.title,'https://example.com/x');assert.equal(web.href,undefined);
  assert.ok(links.textContent.includes('相对 说明，<img src=x onerror=alert(1)><script>alert(2)</script>'));
  await web.onclick();await flush();
  assert.deepEqual(calls.filter(c=>c.operation==='open_link').map(c=>c.url),['https://example.com/x']);
  // Everything opening the conversation creates, the page's own chrome (h2, option) included.
  const allowed=new Set(['article','header','div','p','h2','h3','h4','h5','h6','option','ul','ol','li','blockquote','hr','table','thead','tbody','tr','th','td',
    'code','strong','em','del','span','a','button','section','details','summary','time','small','pre',
    'math','mrow','mi','mn','mo','mtext','mspace','msub','msup','msubsup','munder','mover','munderover','mfrac','msqrt','mroot','mtable','mtr','mtd','mstyle','mphantom']);
  assert.deepEqual([...created].filter(t=>!allowed.has(t)),[],'answers only ever create known elements');
})().catch(e=>{console.error(e);process.exitCode=1});
'''


@pytest.mark.parametrize('with_math', [True, False], ids=['mathml', 'no-mathml'])
def test_answers_render_markdown_and_formulas_as_nodes(with_math):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required for browser runtime regression')
    source = (Path(__file__).resolve().parents[1]/'stage/workbench.js').read_text(encoding='utf-8')
    result = subprocess.run([node, '-e', HARNESS], input=json.dumps({'source': source, 'withMath': with_math}),
                            encoding='utf-8', capture_output=True)
    assert result.returncode == 0, result.stderr
