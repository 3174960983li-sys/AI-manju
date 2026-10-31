import {transitionTask,validateTasks,taskSnapshot,taskStatus} from './public/task-domain.js';
import {stageGuides,guideHasContent} from './public/guides.js';
import {validateProduction,batchSnapshot,batchStatus,cutSnapshot,episodeStatus,nextCode} from './public/domain.js';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const base=path.dirname(fileURLToPath(import.meta.url));
test('project persistence, import validation, docs and request boundaries',async()=>{
 const tmp=await fs.mkdtemp(path.join(os.tmpdir(),'drama-workbench-'));
 const file=path.join(tmp,'projects.json'),port=14319;
 let child;
 async function start(){child=spawn(process.execPath,[path.join(base,'server.mjs')],{env:{...process.env,PORT:String(port),WORKBENCH_DATA_FILE:file},stdio:['ignore','pipe','pipe']});await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('server timeout')),5000);child.stdout.once('data',()=>{clearTimeout(t);resolve();});child.once('error',reject);child.once('exit',code=>{clearTimeout(t);reject(Error('server exited '+code));});});}
 async function stop(){if(child&&!child.killed){const done=new Promise(r=>child.once('exit',r));child.kill();await done;}}
 const url=`http://127.0.0.1:${port}`;
 const put=data=>fetch(url+'/api/projects',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 try{
  await start();assert.equal((await fetch(url)).status,200);
  assert.deepEqual(await (await fetch(url+'/api/projects')).json(),{schemaVersion:1,projects:[]});
  const data={schemaVersion:1,projects:[{id:'qa-project',title:'测试项目 <script>',genre:'悬疑',format:'竖屏',goal:'验证',audience:'测试',stages:{'01':{status:'已确认',notes:'第一版构想'}},decisions:[{id:'d1',stage:'01',time:new Date().toISOString(),result:'用户确认',note:'测试',snapshot:'第一版构想'}]}]};
  assert.equal((await put(data)).status,200);
  assert.deepEqual(JSON.parse(await fs.readFile(file,'utf8')),data);
  await stop();await start();assert.deepEqual(await (await fetch(url+'/api/projects')).json(),data);
  const bad=structuredClone(data);bad.projects.push(bad.projects[0]);assert.equal((await put(bad)).status,400);
  assert.deepEqual(await (await fetch(url+'/api/projects')).json(),data);
  assert.equal((await fetch(url+'/api/projects',{method:'PUT',headers:{'Content-Type':'application/json',Origin:'https://untrusted.example'},body:JSON.stringify(data)})).status,403);
  assert.equal((await fetch(url+'/server.mjs')).status,404);
  assert.equal((await fetch(url+'/api/docs/rules')).status,200);
  data.projects[0].stages['01'].guide={goal:'结构化目标'};data.projects[0].stages['01'].notes='修订';assert.equal((await put(data)).status,200);
  assert.equal(JSON.parse(await fs.readFile(file+'.bak','utf8')).projects[0].stages['01'].notes,'第一版构想');
 }finally{await stop();await fs.rm(tmp,{recursive:true,force:true});}
});
test('production hierarchy and version-bound review decisions',()=>{
 const p={episodes:[{id:'ep1',code:'EP001',title:'第一集',summary:'开场',cut:{version:'v1',location:'E:/cuts/ep1.mp4',notes:'完成版'},adoption:null}],scenes:[{id:'sc1',code:'SC001',episodeId:'ep1',title:'雨夜',notes:'建立悬念'}],assets:[{id:'as1',code:'AS001',name:'主角',type:'角色',version:'v1',state:'常态',location:'E:/assets/hero.png',notes:'身份参考'}],shots:[{id:'sh1',code:'SH001',sceneId:'sc1',title:'开门',notes:'手部动作',assetRefs:[{assetId:'as1',version:'v1',state:'常态'}]}],batches:[{id:'bt1',code:'BT001',title:'首批',episodeIds:['ep1'],scope:'本集镜头',resources:'已确认范围',risks:'无',status:'草拟',approval:null}],reviewLog:[]};
 assert.doesNotThrow(()=>validateProduction(p));
 const b=p.batches[0],e=p.episodes[0];b.status='已批准';b.approval={time:new Date().toISOString(),note:'批准',snapshot:batchSnapshot(p,b)};
 assert.equal(batchStatus(p,b),'已批准');b.scope='增加动作镜头';assert.equal(batchStatus(p,b),'待重新确认');
 e.adoption={time:new Date().toISOString(),note:'采用',snapshot:cutSnapshot(e)};assert.equal(episodeStatus(e),'已采用');e.cut.version='v2';assert.equal(episodeStatus(e),'待采用');
 p.assets[0].version='v2';assert.equal(p.shots[0].assetRefs[0].version,'v1');
 assert.equal(nextCode([{code:'EP001'},{code:'EP003'}],'EP'),'EP004');
 const orphan=structuredClone(p);orphan.shots[0].sceneId='missing';assert.throws(()=>validateProduction(orphan),/场次不存在/);
 const missingAsset=structuredClone(p);missingAsset.shots[0].assetRefs[0].assetId='missing';assert.throws(()=>validateProduction(missingAsset),/资产引用不存在/);
 const badBatch=structuredClone(p);badBatch.batches[0].episodeIds=['missing'];assert.throws(()=>validateProduction(badBatch),/批次单集引用无效/);
 const duplicate=structuredClone(p);duplicate.episodes.push({...duplicate.episodes[0],id:'ep2'});assert.throws(()=>validateProduction(duplicate),/编号无效或重复/);
});
test('task dependency lifecycle, rework and cyclic reference rejection',()=>{
 const make=(id,dependencies=[])=>({id,code:'TK'+id,title:'测试'+id,stage:'01',targetType:'project',targetId:'p1',owner:'我',inputs:'采用资料v1',acceptance:'成果可打开且匹配范围',output:'',check:'',limitations:'',dependencies,status:'待开始',history:[]});
 const a=make('a'),b=make('b',['a']),p={id:'p1',title:'测试',tasks:[a,b]};
 assert.doesNotThrow(()=>validateTasks(p));assert.throws(()=>transitionTask(p,b,'进行中'),/依赖任务尚未接收/);
 transitionTask(p,a,'进行中');assert.throws(()=>transitionTask(p,a,'待接收'),/实际成果/);
 a.output='成果位置';a.check='已打开检查';transitionTask(p,a,'待接收');transitionTask(p,a,'已接收','检查后接收');assert.equal(taskStatus(p,a),'已接收');
 transitionTask(p,b,'进行中');b.output='下游成果';b.check='检查记录';transitionTask(p,b,'待接收');transitionTask(p,b,'已接收','接收');assert.equal(taskStatus(p,b),'已接收');
 transitionTask(p,a,'需返工','输入改版，重新核对');assert.equal(taskStatus(p,b),'待复核');assert.equal(b.history.length,3);
 transitionTask(p,a,'进行中');a.output='修订成果';transitionTask(p,a,'待接收');transitionTask(p,a,'已接收','复核接收');assert.equal(taskStatus(p,b),'待复核');
 const cyclic=structuredClone(p);cyclic.tasks[0].dependencies=['b'];assert.throws(()=>validateTasks(cyclic),/循环/);
 const missing=structuredClone(p);missing.tasks[0].dependencies=['missing'];assert.throws(()=>validateTasks(missing),/不存在/);
 const wrong=structuredClone(p);wrong.tasks[0].targetId='absent';assert.throws(()=>validateTasks(wrong),/关联对象不存在/);
 assert.throws(()=>transitionTask(p,a,'需返工',''),/退回需说明/);
 assert.equal(taskSnapshot(p,b).dependencies[0].receiptId,a.receipt.id);
});
test('twelve guides preserve empty and structured-only stage distinctions',()=>{
 assert.equal(stageGuides.length,12);assert.ok(stageGuides.every(g=>g.fields.length===4));
 assert.equal(guideHasContent({notes:'',guide:{goal:''}}),false);
 assert.equal(guideHasContent({notes:'',guide:{goal:'真实构想'}}),true);
});