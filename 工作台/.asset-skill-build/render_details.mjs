import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile}from '@oai/artifact-tool';
const dir='E:/AI漫剧/04_项目管理/02_任务记录/剧本资产拆解_首轮小样/样稿';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(dir+'/剧本资产需求清单.xlsx'));
const views=[['角色基础','G4:R11'],['角色服装与状态','G4:S12'],['场景基础','G4:P5'],['场景状态','G4:R7'],['道具需求','G4:T6'],['出现与变化明细','G4:U24'],['出现与变化明细','A10:F24']];
for(const [i,[name,range]]of views.entries()){
 const img=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(dir+'/明细检查'+i+'.png',new Uint8Array(await img.arrayBuffer()));
}
