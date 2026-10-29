"""Validate structure and references, not script comprehension. Standard library only."""
import json, re, sys
from pathlib import Path

def check(data, schema):
    errors=[]; registry={}; bysheet={}
    for name in ['项目','输入版本','覆盖范围','更新日期','关键缺口']:
        if not data.get('meta',{}).get(name): errors.append(f'meta缺少{name}')
    expected={s['name'] for s in schema['sheets']}
    if set(data.get('sheets',{}))!=expected: errors.append('数据表名称必须与schema一致')
    for spec in schema['sheets']:
        rows=data.get('sheets',{}).get(spec['name'],[]); bysheet[spec['name']]={}
        for row in rows:
            key=row.get(spec['key'],''); label=f"{spec['name']} {key}"
            if not re.fullmatch(spec['prefix']+r'-\d{4,}',str(key)): errors.append(label+' 编号格式错误')
            if key in registry: errors.append(label+' 编号重复')
            registry[key]=(spec['name'],row); bysheet[spec['name']][key]=row
            if set(row)!=set(spec['columns']): errors.append(label+' 字段缺失或多余')
            for col,vals in schema['enums'].items():
                if col in row and row[col] not in vals: errors.append(label+f' {col}取值错误')
            for col in ['原文定位','原文摘录','待确认项']:
                if not row.get(col): errors.append(label+f' 缺少{col}')
            for col in ['人数','数量']:
                if col in row and not (row[col]=='未明确' or type(row[col]) is int and row[col]>0): errors.append(label+f' {col}须正整数或未明确')
            if row.get('证据性质')=='设计候选' and row.get('确认状态')=='不适用': errors.append(label+' 候选必须注明待确认或已确认')
    def ref(row,col,allowed,optional=False):
        key=row.get(col,'')
        if not key and optional:return
        if key not in registry or registry[key][0] not in allowed:errors.append(f'{col}={key} 关联不存在或类型不符')
    for key,(sheet,row) in registry.items():
        if sheet=='角色服装与状态':
            ref(row,'角色编号',{'角色基础'}); ref(row,'基准变体编号',{'角色服装与状态'},True)
            base=registry.get(row.get('基准变体编号'))
            if base and base[1].get('角色编号')!=row.get('角色编号'): errors.append(key+' 基准变体属于其他角色')
        if sheet=='场景状态':
            ref(row,'场景编号',{'场景基础'}); ref(row,'基准状态编号',{'场景状态'},True)
            base=registry.get(row.get('基准状态编号'))
            if base and base[1].get('场景编号')!=row.get('场景编号'):errors.append(key+' 基准状态属于其他空间')
        if sheet=='道具需求':ref(row,'基准道具编号',{'道具需求'},True)
        if sheet=='出现与变化明细':
            ref(row,'资产编号',{'角色基础','场景基础','道具需求'})
            ref(row,'关联变体',{'角色服装与状态','场景状态','道具需求'},True)
            v=registry.get(row.get('关联变体'))
            if v and v[0] in {'角色服装与状态','场景状态'}:
                parent=v[1].get('角色编号',v[1].get('场景编号'))
                if parent!=row.get('资产编号'):errors.append(key+' 变体父资产不一致')
            if v and v[0]=='道具需求':
                chain=set();cur=row['关联变体']
                while cur and cur not in chain:
                    chain.add(cur);cur=registry.get(cur,('',{}))[1].get('基准道具编号','')
                if row.get('资产编号') not in chain: errors.append(key+' 道具变体不属于该基准')
            if not row.get('集场编号') or type(row.get('事件序号')) is not int:errors.append(key+' 场次或事件序号无效')
        target=row.get('合并至编号','')
        if row.get('记录状态')=='已合并':
            ref(row,'合并至编号',{sheet})
            if target==key or registry.get(target,('',{}))[1].get('记录状态')!='有效':errors.append(key+' 合并目标须其他有效记录')
        elif target: errors.append(key+' 非合并记录不应有合并目标')
        for field in ['角色编号','场景编号','资产编号','关联变体','基准变体编号','基准状态编号','基准道具编号']:
            if field in row and row[field] in registry:
                if row['记录状态']=='有效' and registry[row[field]][1].get('记录状态')!='有效':errors.append(key+f' 活动引用{field}指向非有效记录')
        # Baseline chains must not loop.
        for field in ['基准变体编号','基准状态编号','基准道具编号']:
            seen={key};cur=row.get(field,'')
            while cur:
                if cur in seen: errors.append(key+' 基准关系成环'); break
                seen.add(cur);cur=registry.get(cur,('',{}))[1].get(field,'')
    return errors

if __name__=='__main__':
    data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    schema=json.loads((Path(__file__).parents[1]/'assets/schema.json').read_text(encoding='utf-8'))
    errors=check(data,schema)
    print(json.dumps({'valid':not errors,'errors':errors},ensure_ascii=False,indent=2));sys.exit(bool(errors))
