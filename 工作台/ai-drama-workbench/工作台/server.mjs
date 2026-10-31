import {createMediaHandler} from './media-server.mjs';
import {validateProduction} from './public/domain.js';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
const base = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(base);
const publicDir = path.join(base,'public');
const port = Number(process.env.PORT || 4317);
const dataFile = process.env.WORKBENCH_DATA_FILE || path.join(root,'制作项目','工作台数据','projects.json');
const docs = {
 handbook: ['项目手册','项目手册.md'], architecture:['整体协作架构','体系规范/总体架构/整体协作架构.md'],
 rules:['公共规则','体系规范/公共规则/公共规则.md'], research:['作品研究SOP（旧编号草案）','体系规范/03_同类型作品分析与风格研究/SOP.md']
};
let queue = Promise.resolve();
async function readData(){try {return JSON.parse(await fs.readFile(dataFile,'utf8'));} catch(e){if(e.code==='ENOENT')return {schemaVersion:1,projects:[]};throw e;}}
function validate(data){
 if(!data || data.schemaVersion!==1 || !Array.isArray(data.projects) || data.projects.length>200)throw Error('数据格式不兼容');
 const ids=new Set();
 for(const p of data.projects){
  if(!p || typeof p.id!=='string'||!p.id||ids.has(p.id))throw Error('项目编号重复或无效'); ids.add(p.id);
  if(typeof p.title!=='string'||!p.title.trim()||p.title.length>120)throw Error('项目名称须为1—120字');
  if(!p.stages||typeof p.stages!=='object'||Array.isArray(p.stages))throw Error('缺少阶段内容');
  for(const [key,s] of Object.entries(p.stages)){
   if(!/^(0[1-9]|1[0-2])$/.test(key)||!s||!['未开始','进行中','待确认','已确认'].includes(s.status)||typeof s.notes!=='string'||s.notes.length>100000)throw Error('阶段数据无效');
   if(s.guide!==undefined&&(!s.guide||typeof s.guide!=='object'||Array.isArray(s.guide)||Object.keys(s.guide).length>50||Object.values(s.guide).some(v=>typeof v!=='string'||v.length>100000)))throw Error('阶段引导数据无效');
  }
  if(!Array.isArray(p.decisions)||p.decisions.length>10000)throw Error('确认记录格式无效');
  for(const d of p.decisions)if(!d||typeof d.id!=='string'||!/^\d{2}$/.test(d.stage)||typeof d.time!=='string'||typeof d.note!=='string'||typeof d.result!=='string')throw Error('确认记录无效');
  validateProduction(p);
  for(const k of ['genre','goal','audience','format'])if(p[k]!==undefined&&typeof p[k]!=='string')throw Error('项目字段无效');
 }
 return data;
}
async function save(data){ validate(data); await fs.mkdir(path.dirname(dataFile),{recursive:true}); const tmp=dataFile+'.'+randomUUID()+'.tmp'; await fs.writeFile(tmp,JSON.stringify(data,null,2),'utf8'); try {await fs.copyFile(dataFile,dataFile+'.bak');}catch(e){if(e.code!=='ENOENT')throw e;} await fs.rename(tmp,dataFile); }
async function body(req){let size=0,chunks=[];for await(const chunk of req){size+=chunk.length;if(size>8*1024*1024)throw Error('数据超过8MB限制');chunks.push(chunk);}return JSON.parse(Buffer.concat(chunks).toString('utf8'));}
function respond(res,status,value,type='application/json; charset=utf-8'){res.writeHead(status,{'Content-Type':type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; media-src 'self'; frame-ancestors 'none'"});res.end(type.startsWith('application/json')?JSON.stringify(value):value);}
const handleMedia=createMediaHandler({directory:path.join(path.dirname(dataFile),'media'),readData,respond,maxBytes:Number(process.env.WORKBENCH_UPLOAD_LIMIT||100*1024*1024)});
const server=http.createServer(async(req,res)=>{
 try{
  const hosts=[`127.0.0.1:${port}`,`localhost:${port}`];if(!hosts.includes(req.headers.host))return respond(res,403,{error:'仅允许本机访问'});
  if(req.headers.origin&&!hosts.some(h=>req.headers.origin===`http://${h}`))return respond(res,403,{error:'来源不允许'});
  const url=new URL(req.url,`http://127.0.0.1:${port}`);
  if(await handleMedia(req,res,url))return;
  if(url.pathname==='/api/projects'&&req.method==='GET'){await queue;return respond(res,200,await readData());}
  if(url.pathname==='/api/projects'&&req.method==='PUT'){
   if(!req.headers['content-type']?.startsWith('application/json'))return respond(res,415,{error:'需要JSON数据'});
   const data=validate(await body(req));const write=queue.then(()=>save(data));queue=write.catch(()=>{});await write;return respond(res,200,{ok:true});
  }
  if(url.pathname==='/api/docs'&&req.method==='GET')return respond(res,200,Object.entries(docs).map(([id,[title]])=>({id,title})));
  if(url.pathname.startsWith('/api/docs/')&&req.method==='GET'){
   const entry=docs[url.pathname.slice(10)];if(!entry)return respond(res,404,{error:'资料不存在'});return respond(res,200,{title:entry[0],content:await fs.readFile(path.join(root,entry[1]),'utf8')});
  }
  if(req.method!=='GET')return respond(res,405,{error:'不支持的操作'});
  const assets={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/domain.js':'domain.js','/production.js':'production.js','/tasks.js':'tasks.js','/task-domain.js':'task-domain.js','/guides.js':'guides.js','/media.js':'media.js'};
  const name=assets[url.pathname];if(!name)return respond(res,404,{error:'页面不存在'});
  const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
  respond(res,200,await fs.readFile(path.join(publicDir,name)),types[path.extname(name)]);
 }catch(e){console.error(e.message);respond(res,e.code==='ENOENT'?404:400,{error:e.code==='ENOENT'?'文件不存在':e.message});}
});
server.listen(port,'127.0.0.1',()=>console.log(`AI短剧工作台 http://127.0.0.1:${port}`));
server.on('error',e=>{console.error(e.message);process.exitCode=1;});