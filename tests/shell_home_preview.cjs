/* Isolated homepage regression. Usage: node tests/shell_home_preview.cjs before.html after.html output-dir */
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
(async()=>{
  const [before,after,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const results=[];
  try{for(const scenario of [
    {name:'desktop',width:1440,height:900,locale:'zh',scheme:'light'},
    {name:'dark',width:1280,height:800,locale:'zh',scheme:'dark'},
    {name:'mobile',width:390,height:844,locale:'zh',scheme:'light'},
    {name:'short',width:640,height:400,locale:'zh',scheme:'light'},
    {name:'english',width:1280,height:800,locale:'en',scheme:'light'}]){
    const page=await browser.newPage({viewport:{width:scenario.width,height:scenario.height},colorScheme:scenario.scheme,reducedMotion:'reduce'});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(locale=>{
      window.fixture={locale,status:'idle',mode:'keyless',entries:0,requests:[]};
      window.pywebview={api:{
        get_state:async()=>({appearance:{theme:'ink-autumn',locale:fixture.locale},themes:[{id:'ink-autumn',name:'Ink Autumn'}],profiles:[{id:'test',name:'Private profile',model:'deepseek-v4-pro',preset:'deepseek',has_key:true}],active_profile_id:'test',presets:[{id:'deepseek',label:'DeepSeek',requires_key:true,model:'deepseek-v4-pro',base_url:'https://api.deepseek.com'}],settings:{preset:'deepseek',model:'deepseek-v4-pro',base_url:'https://api.deepseek.com'}}),
        get_runtime_state:async()=>({status:fixture.status,mode:fixture.mode}),
        enter_studio:async()=>{fixture.entries++;return {ok:false,message:'APP_PACKAGE_INCOMPLETE'}},
        workbench_request:async request=>{fixture.requests.push(request);return {ok:true,data:{projects:[{name:'<img src=x onerror=alert(1)>',is_example:false},{name:'Hidden demo',is_example:true}]}}}
      }};
      addEventListener('DOMContentLoaded',()=>dispatchEvent(new Event('pywebviewready')));
    },scenario.locale);
    if(scenario.name==='desktop'){
      await page.goto(pathToFileURL(before).href);await page.waitForFunction(()=>document.body.classList.contains('ready'));
      await page.screenshot({path:path.join(out,'home-before.png')});
    }
    await page.goto(pathToFileURL(after).href);await page.waitForFunction(()=>document.body.classList.contains('ready'));
    assert.deepEqual(errors,[]);
    assert.equal(await page.locator('.hero-actions button').count(),2);
    assert.doesNotMatch(await page.locator('#hero-copy').innerText(),/deepseek|Private profile|\\n/);
    assert.match(await page.locator('.structure-card pre').innerText(),/\n/);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'horizontal overflow');
    assert.equal(await page.locator('#connection-status').evaluate(el=>el.classList.contains('connected')),false);
    await page.screenshot({path:path.join(out,`home-${scenario.name}.png`),fullPage:true});
    for(const [button,pane] of [['#nav-models','models'],['#nav-about','about'],['#settings-top','appearance']]){
      await page.locator(button).click();assert.equal(await page.locator(`[data-pane="${pane}"]`).evaluate(el=>el.classList.contains('active')),true);
      await page.locator('#settings-close').click();
    }
    await page.locator('#account-login').click();assert.equal(await page.locator('#account-email').isDisabled(),false);
    await page.locator('#register-tab').click();assert.equal(await page.locator('#account-confirm-field').isVisible(),true);
    assert.equal(await page.locator('#account-submit').isDisabled(),false);
    if(scenario.name==='desktop')await page.screenshot({path:path.join(out,'account-preview.png')});
    await page.locator('#login-tab').click();await page.locator('#account-forgot').click();assert.equal(await page.locator('#account-password-field').isVisible(),true);assert.equal(await page.locator('#account-recovery-field').isVisible(),true);
    await page.keyboard.press('Escape');assert.equal(await page.locator('#account-dialog').evaluate(el=>el.open),false);
    assert.deepEqual(await page.evaluate(()=>fixture.requests),[]);
    await page.locator('#nav-projects').click();await page.waitForFunction(()=>document.querySelectorAll('#project-list li').length===1);
    assert.equal(await page.locator('#project-list img').count(),0);
    await page.locator('#projects-enter').click();await page.waitForFunction(()=>!document.querySelector('#enter-studio').disabled);
    for(const button of ['#enter-studio','#nav-workbench']){await page.locator(button).click();await page.waitForFunction(()=>!document.querySelector('#enter-studio').disabled)}
    assert.equal(await page.evaluate(()=>fixture.entries),3);
    assert.doesNotMatch(await page.locator('#hero-note').innerText(),/MODEL_CONNECTION_FAILED|APP_PACKAGE_INCOMPLETE/);
    await page.evaluate(()=>{fixture.status='ready';fixture.mode='cloud';dispatchEvent(new Event('pywebviewready'))});
    await page.waitForFunction(()=>document.querySelector('#connection-status').classList.contains('connected'));
    assert.match(await page.locator('#connection-status').innerText(),/DeepSeek v4 Pro/);
    await page.locator('#research-example').click();assert.equal(await page.locator('#research-journey').isVisible(),true);
    await page.locator('#research-example').click();assert.equal(await page.locator('#research-journey').isVisible(),false);
    assert.deepEqual(errors,[]);results.push({scenario:scenario.name,passed:true});await page.close();
  }}finally{await browser.close()}
  fs.writeFileSync(path.join(out,'home-checks.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
})().catch(e=>{console.error(e);process.exitCode=1});
