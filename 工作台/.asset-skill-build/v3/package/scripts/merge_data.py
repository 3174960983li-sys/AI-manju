import json,copy,sys
from pathlib import Path
from check_data import check
def merge(old,delta):
 if old.get('schema_version')!=3 or delta.get('schema_version',3)!=3:raise ValueError('需要V3；不能将短摘自动升级')
 out=copy.deepcopy(old);catalog={p['id']:p for p in out['source_records']}
 for p in delta.get('source_records',[]):
  if p['id']in catalog:
   if p!=catalog[p['id']]:raise ValueError('原文目录冲突：'+p['id'])
  else:out['source_records'].append(copy.deepcopy(p));catalog[p['id']]=p
 for sheet,patches in delta.get('assets',{}).items():
  if sheet not in out['assets']:raise ValueError('未知分类')
  rows=out['assets'][sheet];seen=set()
  for patch in patches:
   key=patch['id']
   if key in seen:raise ValueError('增补重复号')
   seen.add(key);current=next((r for r in rows if r['id']==key),None)
   if current:
    for k,v in patch.items():
     if current.get(k)==v:continue
     if k in ['id','parent_id','review','candidate'] or k=='user_notes' and current.get(k) or current.get('review')=='已确认':raise ValueError('受保护内容冲突：'+key+' '+k)
     current[k]=copy.deepcopy(v)
   else:
    parent=patch.get('parent_id','')
    if not parent:rows.append(copy.deepcopy(patch));continue
    at=next((i for i,r in enumerate(rows)if r['id']==parent),None)
    if at is None:raise ValueError('缺少父项')
    at+=1
    while at<len(rows)and rows[at]['id'].startswith(parent+'-'):at+=1
    rows.insert(at,copy.deepcopy(patch))
 errors=check(out)
 if errors:raise ValueError('\n'.join(errors))
 return out
if __name__=='__main__':
 a,b,c=map(Path,sys.argv[1:4])
 if c.exists():raise SystemExit('拒绝覆盖输出')
 c.write_text(json.dumps(merge(json.loads(a.read_text(encoding='utf-8-sig')),json.loads(b.read_text(encoding='utf-8-sig'))),ensure_ascii=False,indent=2),encoding='utf-8')
