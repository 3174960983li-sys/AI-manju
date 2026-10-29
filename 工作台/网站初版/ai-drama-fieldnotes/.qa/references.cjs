const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path=require('node:path');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
for(const [name,url] of [['magic','https://magic-portfolio-demo.vercel.app'],['brittany','https://brittanychiang.com'],['fuwari','https://fuwari.vercel.app'],['quartz','https://quartz.jzhao.xyz']]){try{await page.goto(url,{waitUntil:'domcontentloaded',timeout:25000});await page.waitForTimeout(1400);await page.screenshot({path:path.join(__dirname,name+'.png')});console.log(name+': '+await page.title());}catch(e){console.log(name+': '+e.message.split('\n')[0])}}
await browser.close();})();
