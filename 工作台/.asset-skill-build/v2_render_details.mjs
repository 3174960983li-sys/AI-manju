import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile}from '@oai/artifact-tool';
const dir='E:/AI漫剧/01_作品项目/保镖驾到/资产需求/清单试跑_V0.2_分组阅读版';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(dir+'/剧本资产需求清单.xlsx'));
for(const [i,[name,range]]of [['角色','A20:E30'],['场景','A13:E20'],['场景','A46:E61'],['道具','A13:E24'],['道具','A49:E53']].entries()){
 const img=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(dir+'/分组核验'+i+'.png',new Uint8Array(await img.arrayBuffer()));
}
