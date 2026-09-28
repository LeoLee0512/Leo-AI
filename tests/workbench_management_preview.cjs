/* Isolated regression; never connects to real accounts or user workspaces.
 * node tests/workbench_management_preview.cjs workbench.html shell.html output-dir
 */
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
const {pathToFileURL}=require('url');
(async()=>{
  const [workbench,shell,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:960},reducedMotion:'reduce'}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(()=>{
      const profile={id:'m1',name:'Fixture model',preset:'deepseek',model:'deepseek-v4-pro',base_url:'https://api.deepseek.com',has_key:true};
      const projects=[{id:'p1',name:'研究项目'},{id:'p2',name:'第二项目'}],frames=[{id:'f1',name:'测试对话',project_id:'p1'},{id:'f2',name:'另一对话',project_id:'p2'}];
      const binding={profile_id:'mp1',revision:1,native_profile_id:'m1',credential_ready:true,reasoning:{revision:'cap1',choices:[{id:'default',available:true},{id:'low',available:true,native_value:'low'},{id:'mid',available:false},{id:'ultra',available:true,native_value:'max'}]}};
      window.fixture={calls:[],entities:[],revision:0,failPurge:false,account:null};
      const api={
        get_state:async()=>({profiles:[profile],active_profile_id:'m1',appearance:{theme:'ink-autumn',locale:'zh'},themes:[],settings:profile,presets:[{id:'deepseek',label:'DeepSeek',model:profile.model,base_url:profile.base_url,editable_base_url:true}]}),
        get_runtime_state:async()=>({status:'ready',mode:'cloud'}),
        list_entity_states:async()=>({entities:structuredClone(fixture.entities),next_offset:null}),
        mark_entity:async p=>{fixture.entities=fixture.entities.filter(r=>r.entity_id!==p.entity_id);const r={...p,revision:++fixture.revision};fixture.entities.push(r);fixture.calls.push(['mark',p]);return {ok:true,entity:r}},
        restore_entity:async p=>{fixture.entities=fixture.entities.filter(r=>r.entity_id!==p.entity_id);return {ok:true}},
        purge_entity:async p=>{fixture.calls.push(['purge',p]);if(fixture.failPurge)return {ok:false,message:'WORKBENCH_UNAVAILABLE'};fixture.entities=fixture.entities.filter(r=>r.entity_id!==p.entity_id);if(p.entity_type==='session')frames.splice(frames.findIndex(f=>f.id===p.entity_id),1);else{projects.splice(projects.findIndex(f=>f.id===p.entity_id),1);for(let i=frames.length-1;i>=0;i--)if(frames[i].project_id===p.entity_id)frames.splice(i,1);}return {ok:true}},
        list_session_models:async()=>({binding,models:[{...profile,available:true}]}),
        select_session_model:async()=>({binding}),
        save_profile:async p=>{fixture.calls.push(['save_profile',p]);return {ok:true}},
        return_to_start:async()=>{fixture.calls.push(['return']);return {ok:true}},
        open_model_settings:async()=>{throw Error('Unexpected start-page navigation')},
        account_request:async p=>{fixture.calls.push(['account',p.operation]);if(p.operation==='state')return {ok:true,account:fixture.account};if(p.operation==='logout'){fixture.account=null;return {ok:true,account:null}}fixture.account={email:p.email,local:true};return {ok:true,account:fixture.account,...(['register','reset'].includes(p.operation)?{recovery_code:'fixture-recovery-code'}:{})}},
        workbench_request:async p=>{fixture.calls.push([p.operation,p]);let data={};if(p.operation==='projects')data={projects};if(p.operation==='frames')data={frames:frames.filter(f=>p.projectId==='all'||f.project_id===p.projectId)};if(p.operation==='messages')data={messages:[]};if(p.operation==='execution')data={owner:null};if(p.operation==='feedback')data={feedback:{}};return {ok:true,data}},
      };window.pywebview={api};addEventListener('DOMContentLoaded',()=>dispatchEvent(new Event('pywebviewready')));
    });
    await page.goto(pathToFileURL(workbench).href);await page.locator('#history .history-item').first().click();
    await page.locator('#message-input').fill('保留草稿');
    await page.locator('#settings-button').click();await page.locator('#configure-models').click();
    assert.equal(await page.locator('#model-editor').isVisible(),true);
    await page.locator('#wb-name').fill('Edited model');await page.locator('#wb-model-form button[type=submit]').click();
    await page.waitForFunction(()=>document.querySelector('#settings-status').textContent.includes('已保存'));
    assert.equal(await page.evaluate(()=>fixture.calls.find(c=>c[0]==='save_profile')[1].activate),false);
    assert.equal(await page.locator('#message-input').inputValue(),'保留草稿');
    await page.screenshot({path:path.join(out,'inline-model-settings.png')});
    await page.locator('#close-settings').click();await page.locator('#effort-select').selectOption('ultra');
    assert.equal(await page.locator('#effort-select option[value=mid]').count(),0);
    await page.screenshot({path:path.join(out,'effort.png')});await page.locator('#send').click();
    await page.waitForFunction(()=>fixture.calls.some(c=>c[0]==='send'));
    assert.equal(await page.evaluate(()=>fixture.calls.find(c=>c[0]==='send')[1].reasoningSelection.choice),'ultra');
    await page.reload();await page.locator('#history .history-item').first().click();assert.equal(await page.locator('#effort-select').inputValue(),'ultra');
    await page.locator('#manage-items').click();await page.locator('#manage-list button').filter({hasText:'归档'}).first().click();
    await page.waitForFunction(()=>document.querySelector('#history-count').textContent==='0');
    await page.locator('#manage-state').selectOption('archived');await page.locator('#manage-list button').filter({hasText:'恢复'}).click();
    await page.waitForFunction(()=>document.querySelector('#history-count').textContent==='1');
    await page.locator('#manage-state').selectOption('active');await page.locator('#manage-list button').filter({hasText:'移入回收站'}).first().click();await page.locator('#confirm-accept').click();
    await page.locator('#manage-state').selectOption('trashed');await page.locator('#manage-list button').filter({hasText:'彻底删除'}).click();
    assert.equal(await page.locator('#confirm-accept').isDisabled(),true);await page.locator('#confirm-dialog button[value=cancel]').click();
    assert.equal(await page.evaluate(()=>fixture.calls.filter(c=>c[0]==='purge').length),0);
    await page.evaluate(()=>fixture.failPurge=true);await page.locator('#manage-list button').filter({hasText:'彻底删除'}).click();await page.locator('#confirm-value').fill('彻底删除');await page.locator('#confirm-accept').click();
    await page.waitForFunction(()=>document.querySelector('#manage-status').textContent.length>0);assert.equal(await page.locator('#manage-list .manage-row').count(),1);
    await page.evaluate(()=>fixture.failPurge=false);await page.locator('#manage-list button').filter({hasText:'彻底删除'}).click();await page.locator('#confirm-value').fill('彻底删除');await page.locator('#confirm-accept').click();
    await page.waitForFunction(()=>document.querySelectorAll('#manage-list .manage-row').length===0);
    await page.locator('#manage-kind').selectOption('project');await page.locator('#manage-state').selectOption('active');await page.locator('#manage-list button').filter({hasText:'归档'}).last().click();
    await page.locator('#manage-state').selectOption('archived');await page.screenshot({path:path.join(out,'archive-project.png')});
    assert.equal(await page.evaluate(()=>fixture.entities.find(r=>r.entity_type==='project').snapshot.member_session_ids[0]),'f2');
    await page.locator('#manage-list button').filter({hasText:'移入回收站'}).click();await page.locator('#confirm-accept').click();await page.locator('#manage-state').selectOption('trashed');
    await page.locator('#manage-list button').filter({hasText:'彻底删除'}).click();await page.locator('#confirm-value').fill('彻底删除');await page.locator('#confirm-accept').click();await page.waitForFunction(()=>document.querySelectorAll('#manage-list .manage-row').length===0);
    await page.locator('#manage-close').click();await page.locator('#return-start').click();assert.equal(await page.evaluate(()=>fixture.calls.filter(c=>c[0]==='return').length),1);
    await page.goto(pathToFileURL(shell).href);await page.waitForFunction(()=>document.body.classList.contains('ready'));
    await page.locator('#settings-top').click();assert.equal(await page.locator('#settings.open').count(),1);await page.locator('#settings-close').click();
    await page.locator('#account-register').click();await page.locator('#account-email').fill('preview@example.com');await page.locator('#account-password').fill('fixture-password');await page.locator('#account-confirm').fill('fixture-password');await page.locator('#account-submit').click();
    await page.waitForFunction(()=>document.querySelector('#account-issued-recovery').textContent.includes('fixture-recovery-code'));await page.screenshot({path:path.join(out,'local-account.png')});
    await page.locator('#account-logout').click();await page.waitForFunction(()=>document.querySelector('#account-form').hidden===false);assert.equal(await page.locator('#account-issued-recovery').textContent(),'');
    assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'management-checks.json'),JSON.stringify({passed:true,checks:['inline settings preserve draft','effort sent and retained','archive restore','recycle cancel and failure','session purge','project cascade','explicit return home','guest settings','local registration adapter'],page_errors:errors},null,2));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
