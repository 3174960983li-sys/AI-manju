import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile}from '@oai/artifact-tool';
const dir='E:/AI漫剧/01_作品项目/保镖驾到/资产需求/清单试跑_V0.1';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(dir+'/剧本资产需求清单.xlsx'));
for(const [i,[name,range]]of [['使用说明与总览','A27:F43'],['角色基础','A13:F16'],['角色服装与状态','G23:S26'],['场景基础','A32:G37'],['场景状态','G42:R48'],['道具需求','A5:H12'],['出现与变化明细','G100:U109']].entries()){
 const img=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(dir+'/补充预览'+i+'.png',new Uint8Array(await img.arrayBuffer()));
}
