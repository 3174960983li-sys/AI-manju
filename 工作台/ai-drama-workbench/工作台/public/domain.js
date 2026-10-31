import {validateTasks} from './task-domain.js';
// Shared browser/server rules. Existing v0.1 projects remain valid without these fields.
export function ensureProduction(p){for(const key of ['episodes','scenes','shots','assets','batches','reviewLog','tasks'])p[key]??=[];return p;}
export function nextCode(items,prefix){return prefix+String(items.reduce((max,x)=>Math.max(max,Number(String(x.code||'').replace(prefix,''))||0),0)+1).padStart(3,'0');}
export function batchSnapshot(p,b){return {title:b.title,episodeIds:[...b.episodeIds],scope:b.scope,resources:b.resources,risks:b.risks,episodes:b.episodeIds.map(id=>{const e=p.episodes.find(x=>x.id===id);return {id,title:e?.title,summary:e?.summary};})};}
export function cutSnapshot(e){return {version:e.cut?.version||'',location:e.cut?.location||'',notes:e.cut?.notes||'',...(e.cut?.mediaId?{mediaId:e.cut.mediaId}:{})};}
export function batchStatus(p,b){return b.status==='已批准'&&JSON.stringify(b.approval?.snapshot)!==JSON.stringify(batchSnapshot(p,b))?'待重新确认':b.status;}
export function episodeStatus(e){return e.adoption&&JSON.stringify(e.adoption.snapshot)===JSON.stringify(cutSnapshot(e))?'已采用':'待采用';}
export function validateProduction(p){
 validateTasks(p);
 const groups=['episodes','scenes','shots','assets','batches','reviewLog'];for(const key of groups)if(p[key]!==undefined&&(!Array.isArray(p[key])||p[key].length>20000))throw Error('制作资料列表无效：'+key);
 const episodes=p.episodes||[],scenes=p.scenes||[],shots=p.shots||[],assets=p.assets||[],batches=p.batches||[],log=p.reviewLog||[];
 const all=new Set();for(const list of [episodes,scenes,shots,assets,batches]){const codes=new Set();for(const x of list){if(!x||typeof x.id!=='string'||!x.id||all.has(x.id)||typeof x.code!=='string'||!x.code||codes.has(x.code))throw Error('制作对象编号无效或重复');all.add(x.id);codes.add(x.code);}}
 const ids=list=>new Set(list.map(x=>x.id)),eps=ids(episodes),scs=ids(scenes),ass=ids(assets);
 const text=(x,k,max=100000)=>{if(typeof x[k]!=='string'||x[k].length>max)throw Error('制作字段无效：'+k);};
 const title=x=>{text(x,'title',120);if(!x.title.trim())throw Error('标题不能为空');};
 const snapshot=(s,keys)=>{if(!s||typeof s!=='object'||Array.isArray(s))throw Error('缺少确认快照');for(const key of keys)text(s,key);};
 const mediaId=x=>{if(x?.mediaId!==undefined&&(typeof x.mediaId!=='string'||!/^([0-9a-f]{8}-[0-9a-f-]{27})$/i.test(x.mediaId)))throw Error('素材ID无效');};
 for(const e of episodes){mediaId(e.cut);title(e);text(e,'summary');if(e.cut!==undefined)snapshot(e.cut,['version','location','notes']);if(e.adoption){text(e.adoption,'time');text(e.adoption,'note');snapshot(e.adoption.snapshot,['version','location','notes']);}}
 for(const s of scenes){title(s);text(s,'notes');if(!eps.has(s.episodeId))throw Error('场次引用的单集不存在');}
 for(const s of shots){title(s);text(s,'notes');if(!scs.has(s.sceneId))throw Error('镜头引用的场次不存在');if(!Array.isArray(s.assetRefs))throw Error('镜头资产引用无效');const used=new Set();for(const ref of s.assetRefs){if(!ass.has(ref.assetId)||used.has(ref.assetId))throw Error('镜头资产引用不存在或重复');used.add(ref.assetId);text(ref,'version');text(ref,'state');}}
 for(const a of assets){mediaId(a);text(a,'name',120);if(!a.name.trim())throw Error('资产名称不能为空');for(const k of ['type','version','state','location','notes'])text(a,k);}
 for(const b of batches){title(b);for(const k of ['scope','resources','risks'])text(b,k);if(!Array.isArray(b.episodeIds)||new Set(b.episodeIds).size!==b.episodeIds.length||b.episodeIds.some(id=>!eps.has(id)))throw Error('批次单集引用无效');if(!['草拟','待确认','已批准','需修改'].includes(b.status))throw Error('批次状态无效');if(b.approval){text(b.approval,'time');text(b.approval,'note');if(!b.approval.snapshot||typeof b.approval.snapshot!=='object')throw Error('批次快照无效');}}
 for(const r of log){if(!r||typeof r.id!=='string'||!all.has(r.targetId))throw Error('审核记录对象不存在');for(const k of ['time','type','targetId','decision','note'])text(r,k);if(!r.snapshot||typeof r.snapshot!=='object')throw Error('审核快照无效');}
}