import json,re,sys
from pathlib import Path
def check(data,schema):
 errors=[];ids=set()
 if data.get('schema_version')!=2:return ['仅接受V2分组数据，V1须先迁移']
 if set(data.get('sheets',{}))!={s['name'] for s in schema['sheets']}:errors.append('必须为角色、场景、道具三个分类')
 for spec in schema['sheets']:
  seen={};stack=[]
  for r in data.get('sheets',{}).get(spec['name'],[]):
   key=r.get('id','');parent=r.get('parent_id','')
   if key in ids or not re.fullmatch(spec['prefix']+r'\d{2,}(-\d{2,})*',key):errors.append('编号重复或格式错误 '+key)
   ids.add(key)
   for f in ['name','description','original','episodes','source_refs']:
    if not r.get(f):errors.append(key+' 缺少 '+f)
   if r.get('kind') not in schema['kinds']:errors.append(key+' 类型无效')
   if parent:
    if parent not in seen or parent not in stack:errors.append(key+' 父项不存在或组被打断')
    else:stack=stack[:stack.index(parent)+1]
    if not key.startswith(parent+'-'):errors.append(key+' 编号与父项不符')
    p=seen.get(parent,{})
    if spec['name']=='角色' and r.get('kind') not in ['服装','状态']:errors.append(key+' 角色下只挂服装或状态')
    if spec['name']=='场景' and r.get('kind')=='子场景' and p.get('kind') not in ['母场景','子场景']:errors.append(key+' 子空间归属错误')
   else:
    stack=[]
    if r.get('kind') in ['服装','状态','子场景']:errors.append(key+' 下属条目不能无父项')
   stack.append(key);seen[key]=r
 return errors
if __name__=='__main__':
 schema=json.loads((Path(__file__).parents[1]/'assets/schema.json').read_text(encoding='utf-8'))
 data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'));errors=check(data,schema)
 print(json.dumps({'valid':not errors,'errors':errors},ensure_ascii=False));sys.exit(bool(errors))
