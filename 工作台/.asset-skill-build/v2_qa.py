from pathlib import Path
from zipfile import ZipFile
import json,sys,copy,hashlib,xml.etree.ElementTree as ET,re
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OUT=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.2_分组阅读版')
sys.path.insert(0,str(ROOT/'scripts'))
from check_data import check
from merge_data import merge
schema=json.loads((ROOT/'assets/schema.json').read_text(encoding='utf-8'))
data=json.loads((OUT/'资产分组数据.json').read_text(encoding='utf-8'))
tests=[]
def assert_(x):
 if not x:raise AssertionError('check failed')
def case(name,fn):fn();tests.append(name)
case('三类数据与分组连续校验',lambda:assert_(not check(data,schema)))
for title,change in [
 ('重复编号拒绝',lambda d:d['sheets']['角色'].append(copy.deepcopy(d['sheets']['角色'][0]))),
 ('孤儿变体拒绝',lambda d:d['sheets']['角色'][1].update({'parent_id':'R99'})),
 ('拆组拒绝',lambda d:d['sheets']['角色'].append(d['sheets']['角色'].pop(1))),
 ('来源缺失拒绝',lambda d:d['sheets']['道具'][0].update({'source_refs':[]})),
 ('跨表父项拒绝',lambda d:d['sheets']['场景'][1].update({'parent_id':'R01'}))]:
 d=copy.deepcopy(data);change(d);case(title,lambda d=d:assert_(bool(check(d,schema))))
case('旧七表JSON拒绝直接套用',lambda:assert_(bool(check({'sheets':{}},schema))))
def add_child():
 d=copy.deepcopy(data);d['sheets']['角色'][0]['user_notes']='保留我的批注'
 new=copy.deepcopy(d['sheets']['角色'][1]);new.update({'id':'R01-04','name':'测试服装','kind':'服装'})
 out=merge(d,{'sheets':{'角色':[new]}},schema)
 ids=[r['id'] for r in out['sheets']['角色']]
 assert_(ids.index('R01-04')<ids.index('R02'))
 assert_(out['sheets']['角色'][0]['user_notes']=='保留我的批注')
 assert_(out['sheets']['场景']==d['sheets']['场景'])
case('追加服装保留组连续、批注和无关记录',add_child)
def rename():
 out=merge(data,{'sheets':{'角色':[{'id':'R01','name':'新显示名称'}]}},schema)
 assert_(out['sheets']['角色'][0]['id']=='R01')
 assert_(out['sheets']['角色'][1]['parent_id']=='R01')
case('角色改名保号与子项归属',rename)
def protected():
 d=copy.deepcopy(data);d['sheets']['角色'][0]['review']='已确认'
 try:merge(d,{'sheets':{'角色':[{'id':'R01','description':'覆盖'}]}},schema)
 except ValueError:return
 raise AssertionError('confirmed row was overwritten')
case('已确认内容冲突保护',protected)
def semantics():
 roles=data['sheets']['角色'];scenes=data['sheets']['场景'];props=data['sheets']['道具']
 assert_(len([r for r in roles if not r['parent_id']])==20)
 assert_(len([r for r in roles if r['parent_id']])==5)
 assert_(not any(r['kind']=='服装' for r in roles))
 assert_(len([r for r in scenes if r['kind']=='子场景'])==36)
 assert_(len([r for r in scenes if r['kind']=='状态'])==5)
 assert_(next(r for r in scenes if r['name']=='订婚布置状态')['parent_id']=='S01-08')
 assert_(len([r for r in scenes if '（暂分）'in r['name']])==3)
 assert_(any('动物' in r['name'] for r in roles))
 assert_(len([r for r in props if r['kind']=='载具'])==3)
 assert_(not any('基准' in r['name'] for rs in data['sheets'].values() for r in rs))
case('角色状态、母子空间、院子状态和资产分类语义复核',semantics)

ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def verify(file,expected):
 with ZipFile(file) as z:
  assert_(z.testzip() is None)
  wb=ET.fromstring(z.read('xl/workbook.xml'))
  assert_([s.attrib['name'] for s in wb.find('x:sheets',ns)]==['角色','场景','道具'])
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():strings=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  for i,kind in enumerate(['角色','场景','道具'],1):
   root=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
   assert_(root.find('.//x:pane',ns).attrib['topLeftCell']=='C6')
   assert_(root.find('x:mergeCells',ns) is None)
   assert_(not [c for c in root.findall('.//x:c',ns) if c.attrib.get('t')=='e'])
   table=ET.fromstring(z.read(f'xl/tables/table{i}.xml'))
   assert_(len(table.find('x:tableColumns',ns))==5)
   assert_(table.find('x:autoFilter',ns) is not None)
   for j,row in enumerate(expected[kind],6):
    cell=root.find(f'.//x:c[@r="A{j}"]',ns);v=cell.find('x:v',ns)
    val=strings[int(v.text)] if cell.attrib.get('t')=='s' else v.text if v is not None else ''.join(cell.itertext())
    assert_(val==row['id'])
   if not expected[kind]:
    assert_(not [c for c in root.findall('.//x:row',ns) if int(c.attrib['r'])>5 and any(ch.find('x:v',ns) is not None for ch in c)])
case('实际测试Excel三表五列、顺序、冻结与筛选',lambda:verify(OUT/'剧本资产需求清单.xlsx',data['sheets']))
case('空模板无占位资产',lambda:verify(Path('.asset-skill-build/v2-blank/剧本资产需求清单.xlsx'),{x:[] for x in data['sheets']}))
sample=json.loads((ROOT/'assets/sample-data.json').read_text(encoding='utf-8'))
case('合成示例分组与输出',lambda:verify(Path('.asset-skill-build/v2-sample/剧本资产需求清单.xlsx'),sample['sheets']))
def provenance():
 src=json.loads(Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.1\核验资料\来源定位与原文抽取.json').read_text(encoding='utf-8'))
 assert_(hashlib.sha256(Path(src['source']).read_bytes()).hexdigest()==src['sha256'])
 refs={r['id'] for r in src['records']}
 assert_(all(set(r['source_refs'])<=refs for rows in data['sheets'].values() for r in rows))
case('原文件不变且每条出处可回查',provenance)
text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
case('Skill入口元数据与相对链接',lambda:assert_(text.startswith('---\nname: script-asset-breakdown\n') and all((ROOT/p).exists() for p in re.findall(r'\]\(([^)]+)\)',text))))
(OUT/'验证记录.json').write_text(json.dumps({'passed':len(tests),'cases':tests},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(tests),'cases':tests},ensure_ascii=False,indent=2))
