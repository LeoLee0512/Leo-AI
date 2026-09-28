/* Isolated rendering regression; no real pywebview, credentials or daemon.
 * Usage: node tests/shell_settings_preview.cjs before.html after.html output-dir
 * Requires Playwright in NODE_PATH and a locally installed Edge/Chrome.
 */
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const {pathToFileURL} = require('url');

(async () => {
  const [before, after, output] = process.argv.slice(2);
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({channel:'msedge', headless:true});
  const evidence = [];
  try {
    for (const variant of ['before', 'after']) {
      for (const scenario of [
        {name:'light', width:1280, height:800, colorScheme:'light'},
        {name:'dark', width:1280, height:800, colorScheme:'dark'},
        {name:'narrow', width:640, height:640, colorScheme:'light'},
        {name:'animated', width:1280, height:800, colorScheme:'light', reducedMotion:'no-preference'},
      ]) {
        const page = await browser.newPage({viewport:{width:scenario.width,height:scenario.height}, colorScheme:scenario.colorScheme, reducedMotion:scenario.reducedMotion||'reduce'});
        const errors=[];
        page.on('pageerror', e=>errors.push(e.message));
        await page.addInitScript(variant => {
          window.__previewLocale = 'zh';
          const failure = variant==='before' ? 'MODEL_CONNECTION_FAILED' : 'APP_PACKAGE_INCOMPLETE';
          window.pywebview = {api:{
            get_state:async()=>({appearance:{theme:'ink-autumn',locale:window.__previewLocale},
              themes:[{id:'ink-autumn',label:'Ink Autumn'}], profiles:[], active_profile_id:null,
              presets:[{id:'deepseek',label:'DeepSeek',requires_key:true,model:'deepseek-v4-flash',base_url:'https://api.deepseek.com'}],
              settings:{preset:'deepseek',model:'deepseek-v4-flash',base_url:'https://api.deepseek.com'}}),
            enter_studio:async()=>({ok:false,message:failure}),
            connect_keyless:async()=>({ok:false,message:failure}),
          }};
          addEventListener('DOMContentLoaded',()=>dispatchEvent(new Event('pywebviewready')));
        },variant);
        await page.goto(pathToFileURL(variant==='before'?before:after).href);
        await page.waitForFunction(()=>document.body.classList.contains('ready'));
        await page.locator('#settings-top').click();
        await page.locator('#settings.open').waitFor();
        await page.waitForFunction(()=>{
          const drawer=getComputedStyle(document.querySelector('.drawer'));
          return ['none','matrix(1, 0, 0, 1, 0, 0)'].includes(drawer.transform) &&
            getComputedStyle(document.querySelector('#settings')).opacity==='1' &&
            getComputedStyle(document.querySelector('#home')).opacity==='1';
        });
        await page.screenshot({path:path.join(output,`${variant}-${scenario.name}-settings.png`)});
        // The drawer artwork must never paint onto the dimmed home area.
        const rect = await page.locator('.drawer').boundingBox();
        const clip = {x:0,y:72,width:Math.max(1,Math.floor(rect.x)-4),height:scenario.height-72};
        const visible = await page.screenshot({clip});
        const hide = await page.addStyleTag({content:'.drawer::before{visibility:hidden!important}'});
        const hidden = await page.screenshot({clip});
        const leaks = !visible.equals(hidden);
        await hide.evaluate(el=>el.remove());
        if(variant==='after') assert.equal(leaks,false,`${scenario.name}: drawer art leaked onto home`);
        // Scroll and reopen: both paths used to change the pseudo-element's containing block.
        await page.locator('.drawer').evaluate(el=>{el.scrollTop=el.scrollHeight});
        assert.equal(await page.locator('.drawer').evaluate(el=>el.scrollTop>0),true);
        await page.evaluate(()=>window.LeoShell.closeSettings());
        await page.locator('#settings-top').click();
        await page.locator('.drawer').evaluate(el=>{el.scrollTop=0});
        await page.locator('#settings-close').click();
        assert.equal(await page.locator('#settings').evaluate(el=>el.classList.contains('open')),false);
        for (const locale of ['zh','en']) {
          await page.evaluate(locale=>{window.__previewLocale=locale;dispatchEvent(new Event('pywebviewready'))},locale);
          await page.waitForFunction(locale=>document.documentElement.lang===locale,locale);
          for(const button of ['#enter-studio','#browse-keyless']) {
            await page.locator(button).click();
            if(variant==='after') {
              const note=await page.locator('#hero-note').innerText();
              assert.match(note,locale==='zh'?/缺少工作台启动文件/:/missing workbench files/);
              assert.doesNotMatch(note,/APP_PACKAGE_INCOMPLETE|模型连接失败/);
              assert.equal(await page.locator('#enter-studio').isEnabled(),true);
              assert.equal(await page.locator('#browse-keyless').isEnabled(),true);
            }
          }
        }
        if(scenario.name==='light') {
          await page.evaluate(()=>{window.__previewLocale='zh';dispatchEvent(new Event('pywebviewready'))});
          await page.waitForFunction(()=>document.documentElement.lang==='zh');
          await page.locator('#enter-studio').click();
          await page.screenshot({path:path.join(output,`${variant}-entry-error.png`)});
        }
        assert.deepEqual(errors,[]);
        evidence.push({variant,scenario:scenario.name,artwork_leaks_onto_home:leaks,page_errors:errors});
        await page.close();
      }
    }
    assert.equal(evidence.find(x=>x.variant==='before'&&x.scenario==='light').artwork_leaks_onto_home,true,'Before preview must reproduce the reported defect');
    fs.writeFileSync(path.join(output,'browser-checks.json'),JSON.stringify(evidence,null,2));
    console.log(JSON.stringify(evidence,null,2));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
