import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const base=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const [input,outdir,...flags]=process.argv.slice(2);
if(!input||!outdir)throw Error('用法：node build_workbook.mjs input.json 新输出目录 [--render]');
const data=JSON.parse(await fs.readFile(input,'utf8'));
const schema=JSON.parse(await fs.readFile(path.join(base,'assets/schema.json'),'utf8'));
// Data validation is implemented here as well so Python is not an export dependency.
const registry=new Map(),errors=[];
for(const spec of schema.sheets){
 if(!Array.isArray(data.sheets?.[spec.name]))throw Error('缺少表 '+spec.name);
 for(const row of data.sheets[spec.name]){
  const id=row[spec.key];
  if(!new RegExp('^'+spec.prefix+'-\\d{4,}$').test(id)||registry.has(id))errors.push('编号重复或错误 '+id);
  registry.set(id,{row,spec});
  if(Object.keys(row).sort().join()!==[...spec.columns].sort().join())errors.push('字段不符 '+id);
  for(const key of ['原文定位','原文摘录','待确认项'])if(!row[key])errors.push('缺少'+key+' '+id);
  for(const [col,values]of Object.entries(schema.enums))if(col in row&&!values.includes(row[col]))errors.push('枚举错误 '+id+' '+col);
  for(const col of ['人数','数量'])if(col in row&&!(row[col]==='未明确'||Number.isInteger(row[col])&&row[col]>0))errors.push('数量错误 '+id);
 }
}
for(const [id,{row,spec}]of registry){
 for(const [col,prefixes]of Object.entries({'角色编号':['CHR'],'场景编号':['LOC'],'资产编号':['CHR','LOC','PRP'],'关联变体':['CHV','LCV','PRP'],'基准变体编号':['CHV'],'基准状态编号':['LCV'],'基准道具编号':['PRP'],'合并至编号':[spec.prefix]})){
  if(col===spec.key)continue;
  if(row[col]&&(!registry.has(row[col])||!prefixes.includes(registry.get(row[col]).spec.prefix)))errors.push('无效引用 '+id+' '+col);
  if(row[col]&&row['记录状态']==='有效'&&registry.get(row[col])?.row['记录状态']!=='有效'&&col!=='合并至编号')errors.push('活动引用指向停用记录 '+id+' '+col);
 }
 const required=spec.prefix==='CHV'?'角色编号':spec.prefix==='LCV'?'场景编号':spec.prefix==='USE'?'资产编号':null;
 if(required&&!row[required])errors.push('缺少父资产 '+id);
 for(const field of ['基准变体编号','基准状态编号','基准道具编号']){
  let cur=row[field],seen=new Set([id]);
  while(cur){if(seen.has(cur)){errors.push('基准循环 '+id);break;}seen.add(cur);cur=registry.get(cur)?.row[field];}
 }
 for(const [field,parent]of [['基准变体编号','角色编号'],['基准状态编号','场景编号']]){
  if(row[field]&&registry.get(row[field])?.row[parent]!==row[parent])errors.push('基准父资产不同 '+id);
 }
 if(row['记录状态']==='已合并'&&(!row['合并至编号']||row['合并至编号']===id||registry.get(row['合并至编号'])?.row['记录状态']!=='有效'))errors.push('合并目标错误 '+id);
 if(row['记录状态']!=='已合并'&&row['合并至编号'])errors.push('非合并记录含合并目标 '+id);
 if(spec.prefix==='USE'&&(!row['集场编号']||!Number.isInteger(row['事件序号'])))errors.push('场次事件序号错误 '+id);
 if(row['证据性质']==='设计候选'&&row['确认状态']==='不适用')errors.push('候选缺少确认状态 '+id);
 if(spec.prefix==='USE'&&row['关联变体']){
  const v=registry.get(row['关联变体']);const parent=v?.row['角色编号']??v?.row['场景编号'];
  if(parent&&parent!==row['资产编号'])errors.push('变体归属不符 '+id);
  if(v?.spec.prefix==='PRP'){
   const chain=new Set();let cur=row['关联变体'];
   while(cur&&!chain.has(cur)){chain.add(cur);cur=registry.get(cur)?.row['基准道具编号'];}
   if(!chain.has(row['资产编号']))errors.push('道具版本归属错误 '+id);
  }
 }
}
if(errors.length)throw Error(errors.join('\n'));
for(const key of ['项目','输入版本','覆盖范围','更新日期','关键缺口'])if(!data.meta?.[key])throw Error('meta缺少 '+key);
const output=path.join(outdir,'剧本资产需求清单.xlsx');
try{await fs.access(output);throw Error('输出已存在，拒绝覆盖：'+output);}catch(e){if(e.code!=='ENOENT')throw e;}
await fs.mkdir(outdir,{recursive:true});
const wb=Workbook.create(),overview=wb.worksheets.add('使用说明与总览');
for(const spec of schema.sheets)wb.worksheets.add(spec.name);
const col=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const safe=v=>typeof v==='string'&&/^[=+@]/.test(v)?"'"+v:v;
const locations=new Map();
for(const spec of schema.sheets){data.sheets[spec.name].forEach((r,i)=>locations.set(r[spec.key],{sheet:spec.name,cell:'A'+(i+5)}));}
const q=s=>"'"+s.replaceAll("'","''")+"'";
const links=[];
for(const [index,spec]of schema.sheets.entries()){
 const sheet=wb.worksheets.getItem(spec.name),rows=data.sheets[spec.name],last=Math.max(5,rows.length+4),end=col(spec.columns.length-1);
 sheet.showGridLines=false;
 sheet.getRange(`A1:${end}${last}`).format.font={name:'Microsoft YaHei',size:10,color:'#243247'};
 sheet.getRange('A2').values=[[spec.name]];sheet.getRange('A2').format.font={size:14,bold:true};
 sheet.getRange('C2').values=[['返回总览']];links.push({sheet:spec.name,cell:'C2',location:"'使用说明与总览'!A1"});
 sheet.getRange(`A4:${end}4`).values=[spec.columns];
 sheet.getRange(`A4:${end}4`).format={fill:'#304B6A',font:{name:'Microsoft YaHei',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:38};
 if(rows.length)sheet.getRange(`A5:${end}${last}`).values=rows.map(r=>spec.columns.map(c=>safe(r[c]??'')));
 const body=sheet.getRange(`A5:${end}${last}`);body.format.wrapText=true;body.format.verticalAlignment='top';body.format.rowHeight=60;
 sheet.getRange(`A4:${end}${last}`).format.columnWidth=22;
 sheet.getRange(`A4:B${last}`).format.columnWidth=18;
 for(const [j,c]of spec.columns.entries()){
  if(['原文摘录','待确认项','变更说明','用户批注','交互与连续性','可见状态','物理变化','家具陈设','外观与文字','服装','关键布局','变化前后','与基准差异','外观依据','身份'].includes(c))sheet.getRange(`${col(j)}4:${col(j)}${last}`).format.columnWidth=32;
  if(['人数','数量','事件序号'].includes(c))sheet.getRange(`${col(j)}5:${col(j)}${last}`).setNumberFormat('0');
  if(schema.enums[c])sheet.getRange(`${col(j)}5:${col(j)}${Math.max(last+100,105)}`).dataValidation={rule:{type:'list',values:schema.enums[c]}};
 }
 
 for(const [ri,record]of rows.entries()){
  let maxLines=1;
  for(const [ci,key]of spec.columns.entries()){
   const broad=['原文摘录','待确认项','变更说明','用户批注','交互与连续性','可见状态','物理变化','家具陈设','外观与文字','服装','关键布局','变化前后','与基准差异','外观依据','身份'].includes(key);
   const width=broad?32:ci<2?18:22;
   const text=String(record[key]??'');const units=[...text].reduce((n,c)=>n+(c.charCodeAt(0)>255?2:1),0);
   maxLines=Math.max(maxLines,Math.ceil(units/Math.max(12,width-2)));
  }
  sheet.getRange(`A${ri+5}:${end}${ri+5}`).format.rowHeight=Math.max(48,maxLines*15+10);
 }

 const table=sheet.tables.add(`A4:${end}${last}`,true,'Assets'+spec.prefix);table.showFilterButton=true;table.style='TableStyleLight9';
 sheet.freezePanes.freezeRows(4);sheet.freezePanes.freezeColumns(2);
 const status=spec.columns.indexOf('确认状态'),gap=spec.columns.indexOf('待确认项');
 sheet.getRange(`${col(status)}5:${col(status)}${Math.max(last+100,105)}`).conditionalFormats.add('containsText',{text:'待确认',format:{fill:'#FFF1CE',font:{color:'#7D5200'}}});
 sheet.getRange(`${col(gap)}5:${col(gap)}${Math.max(last+100,105)}`).conditionalFormats.addCustom(`AND(${col(gap)}5<>"",${col(gap)}5<>"无新增缺口")`,{fill:'#FFF1CE'});
 for(const [i,r]of rows.entries())for(const [j,c]of spec.columns.entries()){
  if(c===spec.key)continue;const target=locations.get(r[c]);if(!target)continue;
  const targetSpec=registry.get(r[c]).spec;
  links.push({sheet:spec.name,cell:`${col(j)}${i+5}`,location:'asset_'+r[c].replaceAll('-','_'),definition:`INDEX(Assets${targetSpec.prefix}[${targetSpec.key}],MATCH("${r[c]}",Assets${targetSpec.prefix}[${targetSpec.key}],0))`});
  sheet.getRange(`${col(j)}${i+5}`).format.font.color='#245DA8';
 }
}
overview.showGridLines=false;overview.tabColor='#304B6A';
overview.getRange('A1:F36').format.font={name:'Microsoft YaHei',size:10,color:'#243247'};
overview.getRange('A1:F36').format.rowHeight=26;overview.getRange('A1:A36').format.columnWidth=22;overview.getRange('B1:B36').format.columnWidth=85;overview.getRange('C1:F36').format.columnWidth=22;
overview.getRange('A2').values=[['剧本资产需求清单']];overview.getRange('A2').format.font={size:15,bold:true};
const metakeys=['项目','输入版本','覆盖范围','更新日期','关键缺口'];
metakeys.forEach((key,i)=>{overview.getRange(`A${i+4}:B${i+4}`).values=[[key,safe(data.meta[key])]];});
overview.getRange('B4:B8').format.wrapText=true;overview.getRange('A8:B8').format.rowHeight=62;
overview.getRange('A10:C10').values=[['分类（点击进入）','有效登记条数','统计口径']];overview.getRange('A10:C10').format={fill:'#304B6A',font:{bold:true,color:'#FFFFFF'}};
schema.sheets.forEach((s,i)=>{
 const n=i+11;overview.getRange(`A${n}`).values=[[s.name]];links.push({sheet:'使用说明与总览',cell:`A${n}`,location:q(s.name)+'!A1'});
 overview.getRange(`B${n}`).formulas=[[`=COUNTIF(Assets${s.prefix}[记录状态],"有效")`]];
 overview.getRange(`C${n}`).values=[[(i===0?'含群众群组与仅提及角色':i===1?'含基准外观组合':i===4?'设计条数，非实物件数':'按有效记录计数')]];
});
overview.getRange('C10:C16').format.columnWidth=34;
const notes=[['如何阅读','先看角色/场景基础，再看服装与状态；最后用出现明细回查场次。'],['来源标识','事实、推断、候选分开；原文明示不等于用户已审阅。'],['数量与身份','群组一行不等于一个人；同款物件的实物数量及归属另记。'],['家具陈设','包含在场景，不重复列为道具；互动和破坏记录在场景状态。'],['当前状态','实际清单试跑待审；非原剧全文提取，实际入画与角色完整性未验证。'],['新增记录','在各分类Excel表末尾插入表行，统计自动扩展；保持编号唯一。'],['更新原则','保留已有编号、确认内容与用户批注，另存新版本；不用旧JSON覆盖新Excel。']];
notes.forEach((r,i)=>{overview.getRange(`A${i+19}:B${i+19}`).values=[r];});overview.getRange('B19:B25').format.wrapText=true;overview.getRange('A19:B25').format.rowHeight=38;

const special=JSON.parse(await fs.readFile(path.join(outdir,'专项需求.json'),'utf8'));
overview.getRange('A27').values=[['交通与特效专项需求（不计入普通道具）']];
overview.getRange('A29:F29').values=[['类别','名称','范围','要求','来源','核验状态']];
overview.getRange('A29:F29').format={fill:'#304B6A',font:{bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:32};
overview.getRange('C29:C50').format.columnWidth=34;
overview.getRange('D29:D50').format.columnWidth=55;
overview.getRange('E29:F50').format.columnWidth=24;
overview.getRange('A30:F'+(special.length+29)).values=special.map(r=>[r['类别'],r['名称'],r['范围'],r['要求'],r['来源'],'需求待原剧复核']);
overview.getRange('A30:F'+(special.length+29)).format.wrapText=true;
overview.getRange('A30:F'+(special.length+29)).format.rowHeight=58;
overview.getRange('A26').values=[['明细读取提醒']];overview.getRange('B26').values=[['明细列“集场编号”是源清单集数范围，不是96分场；事件序号只用于登记排序。']];
overview.getRange('B26').format.wrapText=true;overview.getRange('A26:B26').format.rowHeight=45;

wb.recalculate();
const inspection=await wb.inspect({kind:'table',range:'使用说明与总览!A10:C16',include:'values,formulas',tableMaxRows:7,tableMaxCols:3,maxChars:2200});
await fs.writeFile(path.join(outdir,'检查摘要.json'),JSON.stringify({overview:inspection.ndjson,counts:Object.fromEntries(schema.sheets.map(s=>[s.name,data.sheets[s.name].filter(r=>r['记录状态']==='有效').length])),hyperlinks:links.length},null,2));
if(flags.includes('--render'))for(const s of ['使用说明与总览',...schema.sheets.map(s=>s.name)]){
 const range=s==='使用说明与总览'?'A1:C25':'A2:F'+Math.min(9,Math.max(5,data.sheets[s].length+4));
 const img=await wb.render({sheetName:s,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(outdir,s+'.png'),new Uint8Array(await img.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(output);
const linkfile=path.join(outdir,'链接定义.json');await fs.writeFile(linkfile,JSON.stringify(links));
const patch=spawnSync(process.env.ASSET_PYTHON||'python',[path.join(base,'scripts/add_links.py'),output,linkfile],{encoding:'utf8'});
if(patch.status!==0)throw Error('原生链接补充失败：'+patch.stderr+patch.stdout);
console.log(JSON.stringify({output,counts:Object.fromEntries(schema.sheets.map(s=>[s.name,data.sheets[s.name].length]))}));
