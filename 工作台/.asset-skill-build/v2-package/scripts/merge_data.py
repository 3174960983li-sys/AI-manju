"""Merge V2 rows without losing IDs, notes or grouping. No XLSX editing."""
import json,copy,sys
from pathlib import Path
from check_data import check
def merge(old,delta,schema):
 out=copy.deepcopy(old)
 if delta.get('schema_version',2)!=2:raise ValueError('仅接受V2增补')
 if set(delta.get('sheets',{}))-{s['name'] for s in schema['sheets']}:raise ValueError('未知分类')
 for sheet,patches in delta.get('sheets',{}).items():
  rows=out['sheets'][sheet];seen=set()
  for patch in patches:
   key=patch['id']
   if key in seen:raise ValueError('增补重复编号 '+key)
   seen.add(key);current=next((r for r in rows if r['id']==key),None)
   if current:
    for col,value in patch.items():
     if current.get(col)==value:continue
     if col in ['id','parent_id','review'] or col=='user_notes' and current.get(col) or current.get('review')=='已确认':raise ValueError('受保护内容冲突 '+key+' '+col)
     current[col]=copy.deepcopy(value)
   else:
    parent=patch.get('parent_id','')
    if not parent:rows.append(copy.deepcopy(patch));continue
    pos=next((i for i,r in enumerate(rows) if r['id']==parent),None)
    if pos is None:raise ValueError('新条目缺少父项 '+key)
    end=pos+1
    while end<len(rows) and rows[end]['id'].startswith(parent+'-'):end+=1
    rows.insert(end,copy.deepcopy(patch))
 errors=check(out,schema)
 if errors:raise ValueError('\n'.join(errors))
 return out
if __name__=='__main__':
 old,delta,dest=map(Path,sys.argv[1:4])
 if dest.exists():raise SystemExit('拒绝覆盖已有输出')
 schema=json.loads((Path(__file__).parents[1]/'assets/schema.json').read_text(encoding='utf-8'))
 out=merge(json.loads(old.read_text(encoding='utf-8-sig')),json.loads(delta.read_text(encoding='utf-8-sig')),schema)
 dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
