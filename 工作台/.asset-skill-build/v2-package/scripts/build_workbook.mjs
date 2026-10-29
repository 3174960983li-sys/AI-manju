import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath}from 'node:url';
import {Workbook,SpreadsheetFile}from '@oai/artifact-tool';
const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const [input,outdir,...flags]=process.argv.slice(2);
if(!input||!outdir)throw Error('用法：node build_workbook.mjs input.json 新输出目录 [--render]');
const data=JSON.parse(await fs.readFile(input,'utf8'));
const schema=JSON.parse(await fs.readFile(path.join(base,'assets/schema.json'),'utf8'));
if(data.schema_version!==2)throw Error('需要V2分组数据；V1七表JSON请按迁移规则转换，禁止直接套用');
const errors=[],ids=new Set();
for(const spec of schema.sheets){
 const rows=data.sheets[spec.name];if(!Array.isArray(rows))throw Error('缺少分类 '+spec.name);
 const seen=new Map();let stack=[];
 for(const row of rows){
  if(ids.has(row.id)||!new RegExp('^'+spec.prefix+'\\d{2,}(-\\d{2,})*$').test(row.id))errors.push('重复或错误编号 '+row.id);ids.add(row.id);
  if(!row.name||!row.description||!row.original||!row.episodes||!row.source_refs?.length)errors.push('缺少必要字段 '+row.id);
  if(!schema.kinds.includes(row.kind))errors.push('类别错误 '+row.id);
  if(row.parent_id){
   if(!seen.has(row.parent_id)||!stack.includes(row.parent_id))errors.push('父项不存在或分组被打断 '+row.id);
   stack=stack.slice(0,stack.indexOf(row.parent_id)+1);
   if(!row.id.startsWith(row.parent_id+'-'))errors.push('层级编号与父项不一致 '+row.id);
  }else stack=[];
  stack.push(row.id);seen.set(row.id,row);
 }
}
if(errors.length)throw Error(errors.join('\n'));
await fs.mkdir(outdir,{recursive:true});const file=path.join(outdir,'剧本资产需求清单.xlsx');
try{await fs.access(file);throw Error('拒绝覆盖已有文件，请使用新版本目录');}catch(e){if(e.code!=='ENOENT')throw e;}
const wb=Workbook.create(),widths=[16,32,55,64,28],rendered=[];
const safe=v=>typeof v==='string'&&/^[=+@]/.test(v)?"'"+v:v;
for(const spec of schema.sheets){
 const sheet=wb.worksheets.add(spec.name),rows=data.sheets[spec.name],last=Math.max(6,rows.length+5);
 sheet.showGridLines=false;
 sheet.getRange(`A1:E${last}`).format.font={name:'Microsoft YaHei',size:10,color:'#253349'};
 sheet.getRange(`A1:E${last}`).format.verticalAlignment='center';
 for(let j=0;j<5;j++)sheet.getRange(`${String.fromCharCode(65+j)}1:${String.fromCharCode(65+j)}${last}`).format.columnWidth=widths[j];
 sheet.getRange('A1').values=[[`${data.meta.project} · ${spec.name}`]];sheet.getRange('A1').format.font={size:14,bold:true};
 sheet.getRange('A2').values=[[data.meta.source_label]];
 sheet.getRange('A3').values=[[data.meta.scope_note]];
 sheet.getRange('A4').values=[['按资产成组阅读；下属服装、状态与子场景缩进排列。']];
 sheet.getRange('A1:E1').format.rowHeight=28;sheet.getRange('A2:E4').format.rowHeight=20;
 sheet.getRange('A5:E5').values=[schema.columns];
 if(rows.length)sheet.getRange(`A6:E${last}`).values=rows.map(r=>[r.id,'　'.repeat(r.id.split('-').length-1)+r.name,r.description,r.original,r.episodes].map(safe));
 const table=sheet.tables.add(`A5:E${last}`,true,'Grouped'+({'角色':'Roles','场景':'Scenes','道具':'Props'}[spec.name]));table.showFilterButton=true;table.style='TableStyleLight9';
 sheet.getRange('A5:E5').format={fill:'#304B6A',font:{name:'Microsoft YaHei',bold:true,color:'#FFFFFF',size:10},horizontalAlignment:'center',wrapText:true,rowHeight:30};
 sheet.getRange(`A6:E${last}`).format.wrapText=true;sheet.getRange(`A6:E${last}`).format.verticalAlignment='top';
 for(const [i,r]of rows.entries()){
  const n=i+6,depth=r.id.split('-').length-1;
  if(!r.parent_id){sheet.getRange(`A${n}:E${n}`).format.fill='#EAF0F7';sheet.getRange(`A${n}:B${n}`).format.font.bold=true;}
  else if(r.kind==='子场景'){sheet.getRange(`A${n}:B${n}`).format.font.bold=true;}
  const vals=[r.id,'　'.repeat(depth)+r.name,r.description,r.original,r.episodes];
  const lines=Math.max(...vals.map((v,j)=>String(v).split('\n').reduce((t,l)=>t+Math.max(1,Math.ceil([...l].reduce((a,c)=>a+(c.charCodeAt(0)>255?2:1),0)/(widths[j]-4))),0)));
  sheet.getRange(`A${n}:E${n}`).format.rowHeight=Math.max(32,lines*14+8);
 }
 sheet.freezePanes.freezeRows(5);sheet.freezePanes.freezeColumns(2);
}
wb.recalculate();
const inspection=await wb.inspect({kind:'table',range:'角色!A5:E10',include:'values',tableMaxRows:6,tableMaxCols:5,maxChars:2000});
await fs.writeFile(path.join(outdir,'生成检查.json'),JSON.stringify({inspection:inspection.ndjson,rows:Object.fromEntries(schema.sheets.map(s=>[s.name,data.sheets[s.name].length]))},null,2));
if(flags.includes('--render'))for(const spec of schema.sheets){
 const img=await wb.render({sheetName:spec.name,range:'A1:E'+Math.min(15,Math.max(6,data.sheets[spec.name].length+5)),scale:1,format:'png'});
 await fs.writeFile(path.join(outdir,spec.name+'.png'),new Uint8Array(await img.arrayBuffer()));
}
await(await SpreadsheetFile.exportXlsx(wb)).save(file);
console.log(JSON.stringify({output:file,rows:Object.fromEntries(schema.sheets.map(s=>[s.name,data.sheets[s.name].length]))}));
