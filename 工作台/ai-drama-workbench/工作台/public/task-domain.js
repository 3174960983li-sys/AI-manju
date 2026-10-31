export const taskStates=['待开始','进行中','待接收','已接收','需返工'];
export function taskTargets(p){return [{type:'project',id:p.id,label:'整剧 · '+p.title},...['episodes','scenes','shots','assets','batches'].flatMap(key=>(p[key]||[]).map(x=>({type:{episodes:'episode',scenes:'scene',shots:'shot',assets:'asset',batches:'batch'}[key],id:x.id,label:x.code+' · '+(x.title||x.name)})))];}
export function taskSnapshot(p,t){return {title:t.title,stage:t.stage,targetType:t.targetType,targetId:t.targetId,owner:t.owner,inputs:t.inputs,acceptance:t.acceptance,output:t.output,check:t.check,limitations:t.limitations,dependencies:t.dependencies.map(id=>({id,receiptId:p.tasks.find(x=>x.id===id)?.receipt?.id||null}))};}
export function taskStatus(p,t,visiting=new Set()){
 if(t.status!=='已接收')return t.status;
 if(visiting.has(t.id))return '待复核';const path=new Set(visiting);path.add(t.id);
 if(t.dependencies.some(id=>{const d=p.tasks.find(x=>x.id===id);return !d||taskStatus(p,d,path)!=='已接收';}))return '待复核';
 return JSON.stringify(t.receipt?.snapshot)===JSON.stringify(taskSnapshot(p,t))?'已接收':'待复核';
}
export function pendingDependencies(p,t){return t.dependencies.map(id=>p.tasks.find(x=>x.id===id)).filter(x=>!x||taskStatus(p,x)!=='已接收');}
export function transitionTask(p,t,next,note=''){
 if(!taskStates.includes(next))throw Error('任务状态无效');
 if(['进行中','待接收','已接收'].includes(next)&&pendingDependencies(p,t).length)throw Error('依赖任务尚未接收，请先完成依赖或调整任务范围。');
 if(next==='进行中'&&(!t.inputs.trim()||!t.acceptance.trim()))throw Error('开始前请填写输入依据与验收条件。');
 if(next==='待接收'&&(t.status!=='进行中'&&t.status!=='需返工'))throw Error('请先开始执行，再提交接收。');
 if(next==='待接收'&&(!t.output.trim()||!t.check.trim()))throw Error('提交前请填写实际成果与自检证据。');
 if(next==='已接收'&&t.status!=='待接收')throw Error('只有待接收任务可以记录接收。');
 if(next==='需返工'&&!note.trim())throw Error('退回需说明问题与期望修正。');
 const time=new Date().toISOString(),snapshot=taskSnapshot(p,t),record={id:crypto.randomUUID(),time,action:next,note,snapshot};
 t.status=next;t.updatedAt=time;t.history.push(record);if(next==='已接收')t.receipt={id:record.id,time,snapshot};return t;
}
export function validateTasks(p){
 if(p.tasks===undefined)return;if(!Array.isArray(p.tasks)||p.tasks.length>2000)throw Error('任务列表无效或超过2000条');
 const tasks=p.tasks,ids=new Set(),codes=new Set(),otherIds=new Set(['episodes','scenes','shots','assets','batches'].flatMap(k=>(p[k]||[]).map(x=>x.id)));
 const text=(x,k,max=100000)=>{if(typeof x[k]!=='string'||x[k].length>max)throw Error('任务字段无效：'+k);};
 const targets=taskTargets(p);
 for(const t of tasks){if(!t||typeof t.id!=='string'||!t.id||ids.has(t.id)||otherIds.has(t.id)||typeof t.code!=='string'||!t.code||codes.has(t.code))throw Error('任务编号无效或重复');ids.add(t.id);codes.add(t.code);
  for(const k of ['title','stage','targetType','targetId','owner','inputs','acceptance','output','check','limitations'])text(t,k,k==='title'?120:100000);
  if(!t.title.trim()||!/^\d{2}$/.test(t.stage)||Number(t.stage)<1||Number(t.stage)>12||!taskStates.includes(t.status))throw Error('任务名称、阶段或状态无效');
  if(!targets.some(x=>x.type===t.targetType&&x.id===t.targetId))throw Error('任务关联对象不存在');
  if(!Array.isArray(t.dependencies)||new Set(t.dependencies).size!==t.dependencies.length)throw Error('任务依赖无效');
  if(!Array.isArray(t.history)||t.history.length>1000)throw Error('任务历史无效');
  for(const h of t.history){for(const k of ['id','time','action','note'])text(h,k);if(!h.snapshot||typeof h.snapshot!=='object')throw Error('任务历史缺少快照');}
  if(t.receipt&&(!t.receipt.snapshot||typeof t.receipt.id!=='string'))throw Error('任务接收快照无效');
 }
 const outgoing=new Map(tasks.map(t=>[t.id,[]])),degree=new Map();
 for(const t of tasks){for(const id of t.dependencies){if(!ids.has(id)||id===t.id)throw Error('任务依赖不存在或引用自身');outgoing.get(id).push(t.id);}degree.set(t.id,t.dependencies.length);}
 const ready=tasks.filter(t=>!degree.get(t.id)).map(t=>t.id);let count=0;for(let i=0;i<ready.length;i++){count++;for(const id of outgoing.get(ready[i])){degree.set(id,degree.get(id)-1);if(!degree.get(id))ready.push(id);}}if(count!==tasks.length)throw Error('任务依赖不能形成循环');
}