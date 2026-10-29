import json,re,sys,hashlib
from pathlib import Path
MODES={'现场','画外音','闪回','仅提及'}
KINDS={'资产','母场景','子场景','服装','状态','成员','载具','载具子空间','屏幕内容'}
def check(data):
 errors=[]
 if data.get('schema_version')!=3:return ['需要V3数据；短摘句和集数范围不能自动升级为完整原文及逐集记录']
 if set(data.get('assets',{}))!={'角色','场景','道具'}:errors.append('需要角色、场景、道具三类')
 source={r['id']:r for r in data.get('source_records',[])}
 if len(source)!=len(data.get('source_records',[])):errors.append('来源段落ID重复')
 scope=data.get('meta',{}).get('scope',[])
 if len(scope)!=2 or scope[0]>scope[1]:return errors+['缺少有效集数范围']
 for q in source.values():
  if q.get('episode') is not None and not scope[0]<=q['episode']<=scope[1]:errors.append('来源段落超出本轮范围 '+q['id'])
 allids=set()
 for sheet,rows in data.get('assets',{}).items():
  seen={};stack=[]
  pattern=({'角色':'R','场景':'S','道具':'(?:P|T)'}.get(sheet,'!'))+r'\d{2,}(?:-\d{2,})*'
  for row in rows:
   key=row.get('id','');parent=row.get('parent_id','')
   if key in allids or not re.fullmatch(pattern,key):errors.append('重复或无效编号 '+key)
   allids.add(key)
   if not row.get('name') or not row.get('description'):errors.append(key+' 名称或描述为空')
   if row.get('kind')not in KINDS:errors.append(key+' 类型错误')
   if parent:
    if parent not in seen or parent not in stack:errors.append(key+' 父项缺失、跨表或子树不连续')
    else:stack=stack[:stack.index(parent)+1]
    if not key.startswith(parent+'-'):errors.append(key+' 层级编号不对应')
   else:stack=[]
   stack.append(key);seen[key]=row
   if row.get('outfit_id') and row['outfit_id'] not in seen:errors.append(key+' 服装关联不存在或次序错误')
   if not row.get('source_ids'):errors.append(key+' 缺少来源段落')
   for q in row.get('source_ids',[]):
    if q not in source or not source[q]['text']:errors.append(key+' 来源无效 '+q)
   facts=row.get('appearance_facts',[])
   if not isinstance(facts,list):errors.append(key+' 外观事实应为数组');facts=[]
   for fact in facts:
    if not isinstance(fact,dict) or not isinstance(fact.get('text'),str) or not fact['text'].strip():
     errors.append(key+' 外观事实内容无效');continue
    refs=fact.get('source_ids')
    if not isinstance(refs,list) or not refs:errors.append(key+' 外观事实缺少出处');continue
    for q in refs:
     if q not in source or q not in row.get('source_ids',[]):errors.append(key+' 外观事实出处未纳入本项 '+str(q))
   gaps=row.get('appearance_gaps',[])
   if not isinstance(gaps,list) or any(not isinstance(g,str) or not g.strip() for g in gaps):errors.append(key+' 外观缺口应为非空文字数组')
   if row.get('candidate') and row.get('events'):errors.append(key+' 候选不得冒充原文出场')
   for e in row.get('events',[]):
    q=source.get(e.get('source_id'))
    if q is None or q.get('episode')!=e.get('episode') or q.get('scene')!=e.get('scene'):errors.append(key+' 集数或场次与出处不一致')
    if not scope[0]<=e.get('episode',0)<=scope[1]:errors.append(key+' 超出本轮范围')
    if e.get('mode')not in MODES:errors.append(key+' 出场方式错误')
 return errors
if __name__=='__main__':
 path=Path(sys.argv[1]);data=json.loads(path.read_text(encoding='utf-8-sig'));errors=check(data)
 print(json.dumps({'valid':not errors,'errors':errors},ensure_ascii=False));sys.exit(bool(errors))
