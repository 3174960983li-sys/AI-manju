"""Merge JSON deltas by stable IDs; does not update or import existing XLSX."""
import copy,json,sys
from pathlib import Path
from check_data import check

def merge(old,delta,schema):
    out=copy.deepcopy(old); conflicts=[]
    allowed={s['name'] for s in schema['sheets']}
    if set(delta.get('sheets',{}))-allowed:raise ValueError('增补包含未知工作表，拒绝忽略字段')
    for k,v in delta.get('meta',{}).items():out['meta'][k]=v
    for spec in schema['sheets']:
        name,key=spec['name'],spec['key'];rows=out['sheets'][name];lookup={r[key]:r for r in rows}
        seen=set()
        for patch in delta.get('sheets',{}).get(name,[]):
            ident=patch[key]
            if ident in seen:raise ValueError(f'增补重复编号：{ident}')
            seen.add(ident)
            if set(patch)-set(spec['columns']):raise ValueError(f'{ident} 增补包含未知字段')
            if ident not in lookup:
                rows.append(copy.deepcopy(patch));lookup[ident]=rows[-1];continue
            current=lookup[ident]
            for col,value in patch.items():
                if col==key or current.get(col)==value:continue
                if col=='用户批注' and current.get(col):conflicts.append(f'{ident} 用户批注受保护');continue
                if col=='确认状态':conflicts.append(f'{ident} 确认状态变更须定点处理');continue
                if current.get('确认状态')=='已确认' and col not in {'变更说明','用户批注'}:
                    conflicts.append(f'{ident} 已确认字段冲突：{col}');continue
                current[col]=value
    if conflicts:raise ValueError('\n'.join(conflicts))
    errors=check(out,schema)
    if errors:raise ValueError('\n'.join(errors))
    return out

if __name__=='__main__':
    old,delta,dest=map(Path,sys.argv[1:4]);schema=json.loads((Path(__file__).parents[1]/'assets/schema.json').read_text(encoding='utf-8'))
    if dest.exists():raise SystemExit('拒绝覆盖已有输出，请指定新文件')
    result=merge(json.loads(old.read_text(encoding='utf-8-sig')),json.loads(delta.read_text(encoding='utf-8-sig')),schema)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
