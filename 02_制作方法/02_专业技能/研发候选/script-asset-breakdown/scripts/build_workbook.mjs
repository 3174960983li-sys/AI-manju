import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath}from 'node:url';
import {spawnSync}from 'node:child_process';
import {Workbook,SpreadsheetFile}from '@oai/artifact-tool';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const [input,outdir,...flags]=process.argv.slice(2);
if(!input||!outdir)throw Error('用法：node build_workbook.mjs input.json 新输出目录 [--render]');
const data=JSON.parse(await fs.readFile(input,'utf8'));
const python=process.env.ASSET_PYTHON||'python';
const valid=spawnSync(python,[path.join(base,'scripts/check_data.py'),input],{encoding:'utf8'});
if(valid.status!==0)throw Error(valid.stdout+valid.stderr);
const source=new Map(data.source_records.map(r=>[r.id,r]));
const output=path.join(outdir,'剧本资产需求清单.xlsx');
try{await fs.access(output);throw Error('拒绝覆盖已有输出：请另存新版本');}catch(e){if(e.code!=='ENOENT')throw e;}
await fs.mkdir(outdir,{recursive:true});
const wb=Workbook.create(),layout={version:3,sheets:[]};
const columns=['编号','名称','资产描述','完整原文','出现集数'];const widths=[14,28,58,66,30];
const safe=v=>typeof v==='string'&&/^[=+@]/.test(v)?"'"+v:v;
const eps=arr=>{
 const a=[...new Set(arr)].sort((x,y)=>x-y);if(!a.length)return'无';
 const out=[];let i=0;while(i<a.length){let j=i;while(j+1<a.length&&a[j+1]===a[j]+1)j++;out.push(j>i?`${a[i]}—${a[j]}`:String(a[i]));i=j+1;}return'第'+out.join('、')+'集';
};
const episodeText=row=>{
 if(row.candidate)return'设计候选，未作为实际出现统计'+(row.planned_episodes?.length?'\n拟适用：'+eps(row.planned_episodes):'');
 const real=row.events.filter(e=>e.mode!=='仅提及'),appeared=[...new Set(real.map(e=>e.episode))].sort((a,b)=>a-b);
 const mentions=row.events.filter(e=>e.mode==='仅提及').map(e=>e.episode);
 let t=appeared.length?`首次：第${appeared[0]}集\n出现：${eps(appeared)}\n末次：第${appeared.at(-1)}集〔范围内〕`:'首次／末次：本范围未出场';
 if(!appeared.length&&!mentions.length)t+='\n仅小传／大纲登记';
 if(mentions.length)t+='\n仅提及：'+eps(mentions);
 for(const [mode,label]of [['画外音','画外音'],['闪回','闪回']]){
  const e=real.filter(x=>x.mode===mode).map(x=>x.episode);if(e.length)t+='\n'+label+'：'+eps(e);
 }
 return t;
};
const weight=t=>[...String(t)].reduce((n,c)=>n+(c.charCodeAt(0)>255?2:1),0);
const rowHeight=(vals,raw=false)=>Math.max(raw?32:46,...vals.map((s,j)=>String(s).split('\n').reduce((n,l)=>n+Math.max(1,Math.ceil(weight(l)/(widths[j]-5))),0)*16+10));
// Split only to meet cell/row-height limits. Parts concatenate exactly, without inserted newlines.
const split=t=>{
 const a=[];let buf='',units=0,lines=0;
 for(const c of t){let u=c.charCodeAt(0)>255?2:1;if(buf&&(buf.length>=8000||units+u>520||lines>=12)){a.push(buf);buf='';units=0;lines=0;}buf+=c;units+=u;if(c==='\n')lines++;}
 if(buf||!a.length)a.push(buf);return a;
};
for(const name of ['角色','场景','道具']){
 const sheet=wb.worksheets.add(name),nodes=data.assets[name],cells=[],map=[],groups=[];
 let n=6;
 for(const node of nodes){
  const depth=node.id.split('-').length-1,master=n;
  const main=[node.id,'　'.repeat(depth)+node.name,node.description,`展开本行下方原文（${node.source_ids.length}段）`,episodeText(node)];
  cells.push(main.map(safe));n++;
  const first=n,raw=[];
  for(const id of node.source_ids){
   const p=source.get(id),parts=split(p.text);
   for(const [k,part]of parts.entries()){
    const location=(node.candidate?'需求依据（非服装外观原文）\n':'')+`${p.file||data.meta.source_name}\n${p.episode?'第'+p.episode+'集':'小传／大纲'}${p.scene?' · '+p.scene:''} · ${id}`;
    cells.push(['',`原文 ${id}${parts.length>1?'（'+(k+1)+'/'+parts.length+'）':''}`,location,part,p.episode?'第'+p.episode+'集':'小传／大纲'].map(safe));
    raw.push({row:n,source_id:id,part:k,parts:parts.length,text:part});n++;
   }
  }
  if(n>first)groups.push({master,first,last:n-1,id:node.id});
  map.push({id:node.id,kind:node.kind,parent_id:node.parent_id,master,raw});
 }
 const last=Math.max(6,n-1);sheet.showGridLines=false;
 for(let j=0;j<5;j++)sheet.getRange(`${String.fromCharCode(65+j)}1:${String.fromCharCode(65+j)}${last}`).format.columnWidth=widths[j];
 sheet.getRange(`A1:E${last}`).format.font={name:'Microsoft YaHei',size:11,color:'#253349'};
 sheet.getRange('A1').values=[[data.meta.project+' · '+name]];sheet.getRange('A1').format.font={size:15,bold:true};
 sheet.getRange('A2').values=[['范围：第'+data.meta.scope[0]+'—'+data.meta.scope[1]+'集；末次仅限本轮，服装候选不计实际出现。']];
 sheet.getRange('A3').values=[['使用：点击左侧“＋”展开完整原文；服装、状态及子场景始终可见。']];
 sheet.getRange('A4').values=[['来源：'+data.meta.source_name]];
 sheet.getRange('A1:E1').format.rowHeight=30;sheet.getRange('A2:E4').format.rowHeight=23;
 sheet.getRange('A5:E5').values=[columns];
 sheet.getRange('A5:E5').format={fill:'#304B6A',font:{name:'Microsoft YaHei',size:11,color:'#FFFFFF',bold:true},horizontalAlignment:'center',wrapText:true,rowHeight:30};
 if(cells.length)sheet.getRange(`A6:E${n-1}`).values=cells;
 sheet.getRange(`A6:E${last}`).format.wrapText=true;sheet.getRange(`A6:E${last}`).format.verticalAlignment='top';
 sheet.getRange(`A6:E${last}`).format.rowHeight=32;
 for(const [i,entry]of map.entries()){
  const node=nodes[i],main=cells[entry.master-6],height=rowHeight(main);
  if(height>390)throw Error(`资产描述过长请合理分项，不得截断：${node.id}`);
  const r=sheet.getRange(`A${entry.master}:E${entry.master}`);r.format.rowHeight=height;
  if(!node.parent_id){r.format.fill='#EAF0F7';sheet.getRange(`A${entry.master}:B${entry.master}`).format.font.bold=true;}
  else if(['子场景','服装','成员','载具子空间'].includes(node.kind))sheet.getRange(`A${entry.master}:B${entry.master}`).format.font.bold=true;
  r.format.borders={bottom:{style:'thin',color:'#DCE3EB'}};
  if(node.candidate)sheet.getRange(`B${entry.master}`).format.font.color='#815C14';
  for(const item of entry.raw){
   const vals=cells[item.row-6],h=rowHeight(vals,true);
   if(h>390)throw Error('原文行需进一步分段而非截断 '+item.source_id);
   sheet.getRange(`A${item.row}:E${item.row}`).format.rowHeight=h;
   sheet.getRange(`A${item.row}:E${item.row}`).format.fill='#F7F8FA';
   sheet.getRange(`B${item.row}:C${item.row}`).format.font.color='#586575';
  }
 }
 sheet.freezePanes.freezeRows(5);sheet.freezePanes.freezeColumns(2);
 // Render a compact master-only view in a separate temporary workbook without changing the deliverable.
 layout.sheets.push({name,last_row:last,groups,assets:map});
}
wb.recalculate();
await fs.writeFile(path.join(outdir,'版面与原文索引.json'),JSON.stringify(layout,null,2));
await(await SpreadsheetFile.exportXlsx(wb)).save(output);
const patch=spawnSync(python,[path.join(base,'scripts/patch_layout.py'),output,path.join(outdir,'版面与原文索引.json')],{encoding:'utf8'});
if(patch.status!==0)throw Error(patch.stdout+patch.stderr);
if(flags.includes('--excel-print')){
 if(process.platform!=='win32')throw Error('--excel-print需要Windows及本机Microsoft Excel');
 const native=spawnSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(base,'scripts/finalize_excel_print.ps1'),'-WorkbookPath',output],{encoding:'utf8'});
 if(native.status!==0)throw Error('Excel打印设置未完成：'+native.stdout+native.stderr);
}

if(flags.includes('--render')){
 const preview=Workbook.create();
 for(const name of ['角色','场景','道具']){
  const sh=preview.worksheets.add(name);sh.showGridLines=false;
  const rows=data.assets[name].slice(0,Math.min(7,data.assets[name].length));
  sh.getRange('A1:E1').values=[columns];
  sh.getRange('A1:E1').format={fill:'#304B6A',font:{name:'Microsoft YaHei',size:11,bold:true,color:'#FFFFFF'},rowHeight:30};
  if(rows.length)sh.getRange(`A2:E${rows.length+1}`).values=rows.map(x=>[x.id,'　'.repeat(x.id.split('-').length-1)+x.name,x.description,'完整原文默认收起，原文件可展开',episodeText(x)]);
  for(let j=0;j<5;j++)sh.getRange(`${String.fromCharCode(65+j)}1:${String.fromCharCode(65+j)}${rows.length+1}`).format.columnWidth=widths[j];
  if(rows.length){sh.getRange(`A2:E${rows.length+1}`).format.font={name:'Microsoft YaHei',size:11,color:'#253349'};sh.getRange(`A2:E${rows.length+1}`).format.wrapText=true;sh.getRange(`A2:E${rows.length+1}`).format.verticalAlignment='top';}
  rows.forEach((x,i)=>{const h=rowHeight([x.id,x.name,x.description,'',episodeText(x)]);sh.getRange(`A${i+2}:E${i+2}`).format.rowHeight=h;if(!x.parent_id){sh.getRange(`A${i+2}:E${i+2}`).format.fill='#EAF0F7';sh.getRange(`A${i+2}:B${i+2}`).format.font.bold=true;}});
 }
 preview.recalculate();
 for(const name of ['角色','场景','道具']){
  const img=await preview.render({sheetName:name,range:'A1:E'+(Math.min(7,data.assets[name].length)+1),scale:1,format:'png'});
  await fs.writeFile(path.join(outdir,name+'主行预览.png'),new Uint8Array(await img.arrayBuffer()));
 }
}
console.log(JSON.stringify({output,assets:Object.fromEntries(Object.entries(data.assets).map(([k,v])=>[k,v.length])),rawRows:layout.sheets.reduce((n,s)=>n+s.groups.reduce((a,g)=>a+g.last-g.first+1,0),0)}));
