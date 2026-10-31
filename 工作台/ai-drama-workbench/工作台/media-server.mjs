import fs from 'node:fs/promises';
import {createReadStream,createWriteStream} from 'node:fs';
import path from 'node:path';
import {randomUUID,createHash} from 'node:crypto';
import {Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
const types={'.png':['image/png','image'],'.jpg':['image/jpeg','image'],'.jpeg':['image/jpeg','image'],'.webp':['image/webp','image'],'.gif':['image/gif','image'],'.mp4':['video/mp4','video'],'.webm':['video/webm','video'],'.mp3':['audio/mpeg','audio'],'.wav':['audio/wav','audio'],'.m4a':['audio/mp4','audio'],'.pdf':['application/pdf','document'],'.txt':['text/plain; charset=utf-8','document'],'.md':['text/plain; charset=utf-8','document'],'.docx':['application/vnd.openxmlformats-officedocument.wordprocessingml.document','document'],'.xlsx':['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','document']};
function signature(ext,b){const ascii=(start,end)=>b.subarray(start,end).toString('ascii');switch(ext){case '.png':return b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]));case '.jpg':case '.jpeg':return b[0]===255&&b[1]===216&&b[2]===255;case '.gif':return ['GIF87a','GIF89a'].includes(ascii(0,6));case '.webp':return ascii(0,4)==='RIFF'&&ascii(8,12)==='WEBP';case '.wav':return ascii(0,4)==='RIFF'&&ascii(8,12)==='WAVE';case '.mp4':case '.m4a':return ascii(4,8)==='ftyp';case '.webm':return b.subarray(0,4).equals(Buffer.from([26,69,223,163]));case '.mp3':return ascii(0,3)==='ID3'||(b[0]===255&&(b[1]&224)===224);case '.pdf':return ascii(0,5)==='%PDF-';case '.docx':case '.xlsx':return b[0]===80&&b[1]===75&&b[2]===3&&b[3]===4;default:return !b.includes(0);}}
export function parseRange(value,size){if(!value)return null;const m=/^bytes=(\d*)-(\d*)$/.exec(value);if(!m||(!m[1]&&!m[2])||size<=0)throw Error('range');let start,end;if(!m[1]){const suffix=Number(m[2]);if(!Number.isSafeInteger(suffix)||suffix<=0)throw Error('range');start=Math.max(0,size-suffix);end=size-1;}else{start=Number(m[1]);end=m[2]?Number(m[2]):size-1;if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>=size||end<start)throw Error('range');end=Math.min(end,size-1);}return {start,end};}
export function createMediaHandler({directory,readData,respond,maxBytes=100*1024*1024}){
 const validId=id=>/^[0-9a-f]{8}-[0-9a-f-]{27}$/i.test(id);
 async function projectExists(id){return (await readData()).projects.some(p=>p.id===id);}
 async function load(id){if(!validId(id))return null;try{const meta=JSON.parse(await fs.readFile(path.join(directory,id+'.json'),'utf8'));if(meta.id!==id||!types[path.extname(meta.blobName)]||meta.blobName!==id+path.extname(meta.blobName))return null;return meta;}catch(e){if(e.code==='ENOENT')return null;throw e;}}
 return async function handle(req,res,url){
  if(url.pathname!=='/api/media'&&!url.pathname.startsWith('/api/media/'))return false;
  if(url.pathname==='/api/media'&&req.method==='GET'){
   const projectId=url.searchParams.get('projectId');if(!await projectExists(projectId)){respond(res,404,{error:'项目不存在'});return true;}
   let names=[];try{names=await fs.readdir(directory);}catch(e){if(e.code!=='ENOENT')throw e;}
   const items=(await Promise.all(names.filter(x=>x.endsWith('.json')).map(x=>load(x.slice(0,-5))))).filter(x=>x&&x.projectId===projectId).sort((a,b)=>b.uploadedAt.localeCompare(a.uploadedAt));respond(res,200,items);return true;
  }
  if(url.pathname==='/api/media'&&req.method==='POST'){
   const projectId=url.searchParams.get('projectId'),name=url.searchParams.get('name')||'',ext=path.extname(name).toLowerCase();
   if(!await projectExists(projectId)){respond(res,404,{error:'项目不存在'});return true;}
   if(!name||name.length>240||/[\x00-\x1f\\/]/.test(name)||!Object.hasOwn(types,ext)){req.resume();respond(res,400,{error:'不支持的文件类型或文件名。支持常用图片、MP4/WebM、音频、PDF、TXT/MD和DOCX/XLSX。'});return true;}
   if(!req.headers['content-type']?.startsWith('application/octet-stream')){req.resume();respond(res,415,{error:'需要二进制文件内容'});return true;}
   if(Number(req.headers['content-length'])>maxBytes){req.resume();respond(res,413,{error:'单文件超过上传限制（默认100MB）'});return true;}
   await fs.mkdir(directory,{recursive:true});const id=randomUUID(),blobName=id+ext,temp=path.join(directory,id+'.tmp'),dest=path.join(directory,blobName);let size=0,head=Buffer.alloc(0);const hash=createHash('sha256');
   try{
    const meter=new Transform({transform(chunk,encoding,done){size+=chunk.length;if(size>maxBytes)return done(Error('文件超过上传限制'));hash.update(chunk);if(head.length<512)head=Buffer.concat([head,chunk.subarray(0,512-head.length)]);done(null,chunk);}});
    await pipeline(req,meter,createWriteStream(temp,{flags:'wx'}));if(!size||!signature(ext,head))throw Error('文件为空或内容与扩展名不匹配');await fs.rename(temp,dest);
    const [mime,kind]=types[ext],meta={id,projectId,name,size,mime,kind,sha256:hash.digest('hex'),uploadedAt:new Date().toISOString(),blobName};
    try{await fs.writeFile(path.join(directory,id+'.json'),JSON.stringify(meta,null,2),{flag:'wx'});}catch(e){await fs.rm(dest,{force:true});throw e;}
    respond(res,201,meta);return true;
   }catch(e){await fs.rm(temp,{force:true});if(!res.destroyed)respond(res,400,{error:e.message});return true;}
  }
  const match=/^\/api\/media\/([^/]+)\/file$/.exec(url.pathname);
  if(match&&['GET','HEAD'].includes(req.method)){
   const meta=await load(match[1]);if(!meta||!await projectExists(meta.projectId)){respond(res,404,{error:'素材不存在或不属于当前项目库'});return true;}
   const file=path.join(directory,meta.blobName);let stat;try{stat=await fs.stat(file);}catch(e){if(e.code==='ENOENT'){respond(res,404,{error:'素材文件缺失，请检查备份'});return true;}throw e;}
   let range;try{range=parseRange(req.headers.range,stat.size);}catch{res.writeHead(416,{'Content-Range':`bytes */${stat.size}`});res.end();return true;}
   const inline=meta.kind!=='document'&&url.searchParams.get('download')!=='1';const headers={'Content-Type':meta.mime,'Accept-Ranges':'bytes','X-Content-Type-Options':'nosniff','Cache-Control':'no-store','Content-Disposition':`${inline?'inline':'attachment'}; filename="asset${path.extname(meta.blobName)}"; filename*=UTF-8''${encodeURIComponent(meta.name)}`,'Content-Security-Policy':"default-src 'none'; sandbox"};
   if(range){headers['Content-Range']=`bytes ${range.start}-${range.end}/${stat.size}`;headers['Content-Length']=range.end-range.start+1;}else headers['Content-Length']=stat.size;
   res.writeHead(range?206:200,headers);if(req.method==='HEAD'){res.end();return true;}
   try{await pipeline(createReadStream(file,range||{}),res);}catch(e){if(!res.destroyed)res.destroy(e);}return true;
  }
  respond(res,404,{error:'素材操作不存在'});return true;
 };
}