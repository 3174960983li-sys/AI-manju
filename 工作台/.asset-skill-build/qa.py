from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,sys,copy,importlib.util,re
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OUT=Path(r'E:\AI漫剧\04_项目管理\02_任务记录\剧本资产拆解_首轮小样')
sys.path.insert(0,str(ROOT/'scripts'))
from check_data import check
from merge_data import merge
schema=json.loads((ROOT/'assets/schema.json').read_text(encoding='utf-8'))
data=json.loads((ROOT/'assets/sample-data.json').read_text(encoding='utf-8'))
results=[]
def test(name,fn):
    fn();results.append({'case':name,'passed':True})
def assert_true(b,msg='assertion failed'):
    if not b:raise AssertionError(msg)
test('合成数据结构与全部关联',lambda:assert_true(not check(data,schema)))
def invalid(label,fn):
    d=copy.deepcopy(data);fn(d);test(label,lambda:assert_true(bool(check(d,schema))))
invalid('重复编号被拒绝',lambda d:d['sheets']['角色基础'].append(copy.deepcopy(d['sheets']['角色基础'][0])))
invalid('未知数量填零被拒绝',lambda d:d['sheets']['角色基础'][0].update({'人数':0}))
invalid('变体错配角色被拒绝',lambda d:d['sheets']['角色服装与状态'][0].update({'角色编号':'CHR-0002'}))
invalid('缺失来源被拒绝',lambda d:d['sheets']['道具需求'][0].update({'原文定位':''}))
invalid('停用对象仍被活动记录引用被拒绝',lambda d:d['sheets']['角色基础'][0].update({'记录状态':'已停用'}))
invalid('基准成环被拒绝',lambda d:d['sheets']['角色服装与状态'][0].update({'基准变体编号':'CHV-0004'}))
invalid('非本基准道具版本被拒绝',lambda d:d['sheets']['出现与变化明细'][7].update({'关联变体':'PRP-0002'}))

def update_test():
    new=copy.deepcopy(data['sheets']['角色服装与状态'][5]);new.update({'变体编号':'CHV-0009','基准变体编号':'CHV-0006','可见状态':'袖口湿润','原文定位':'独立更新测试 采用记录D02','原文摘录':'蒙面客叫顾川，增加其袖口湿润状态','证据性质':'设计候选','确认状态':'已确认','变更说明':'仅更新测试，不是V1原文事实'})
    delta={'sheets':{'角色基础':[{'角色编号':'CHR-0004','名称':'顾川','别名':'蒙面客','变更说明':'D02身份揭示，编号不变','原文定位':'合成V1 S01/P03；采用记录D02','原文摘录':'蒙面客；D02：蒙面客叫顾川'}], '角色服装与状态':[new]}}
    out=merge(data,delta,schema)
    assert_true(out['sheets']['角色基础'][3]['角色编号']=='CHR-0004')
    assert_true(out['sheets']['角色基础'][0]==data['sheets']['角色基础'][0])
    assert_true(out['sheets']['角色服装与状态'][-1]['变体编号']=='CHV-0009')
    assert_true(out['sheets']['道具需求']==data['sheets']['道具需求'])
    (OUT/'更新测试结果.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
test('改名编号不变、新变体追加、批注与无关行保留',update_test)
def conflict():
    d=copy.deepcopy(data);d['sheets']['角色基础'][0]['确认状态']='已确认'
    for patch in [{'角色编号':'CHR-0001','名称':'改名'},{'角色编号':'CHR-0001','用户批注':'覆盖'},{'角色编号':'CHR-0001','确认状态':'待确认'}]:
        try:merge(d,{'sheets':{'角色基础':[patch]}},schema)
        except ValueError:continue
        raise AssertionError('应拒绝受保护字段修改')
test('确认内容、确认状态、已有批注冲突均拒绝',conflict)

NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def inspect_xlsx(file,counts):
    with ZipFile(file) as z:
        assert_true(z.testzip() is None)
        book=ET.fromstring(z.read('xl/workbook.xml'))
        assert_true([s.attrib['name'] for s in book.find('x:sheets',NS)]==['使用说明与总览']+[s['name'] for s in schema['sheets']])
        assert_true(len(z.namelist())==len(set(z.namelist())))
        for name in z.namelist():
            if name.endswith('.xml'):ET.fromstring(z.read(name))
        for i,s in enumerate(schema['sheets'],2):
            r=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
            pane=r.find('.//x:pane',NS)
            assert_true(pane is not None and pane.attrib.get('xSplit')=='2' and pane.attrib.get('ySplit')=='4',str(pane.attrib if pane is not None else 'no pane'))
            assert_true(not r.findall('.//x:mergeCell',NS),'数据区域不应合并')
            assert_true(r.find('x:tableParts',NS) is not None)
            assert_true(r.find('x:dataValidations',NS) is not None)
            assert_true(r.find('x:hyperlinks',NS) is not None)
            assert_true(not [c for c in r.findall('.//x:c',NS) if c.attrib.get('t')=='e'],'存在公式错误')
        tables=[ET.fromstring(z.read(f'xl/tables/table{i}.xml')) for i in range(1,7)]
        for t,s in zip(tables,schema['sheets']):
            assert_true(t.attrib['name']=='Assets'+s['prefix'])
            assert_true(t.find('x:autoFilter',NS) is not None)
            actual=int(re.search(r'(\d+)$',t.attrib['ref']).group(1))-4
            assert_true(actual==max(1,counts[s['name']]))
        overview=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        for i,s in enumerate(schema['sheets'],11):
            c=overview.find(f'.//x:c[@r="B{i}"]',NS)
            assert_true(c.find('x:f',NS) is not None)
            assert_true(float(c.find('x:v',NS).text)==counts[s['name']])
        if counts['角色基础']:
            names=book.find('x:definedNames',NS)
            named={x.attrib['name']:x.text for x in names}
            assert_true('MATCH("CHR-0001",AssetsCHR[角色编号],0)' in named['asset_CHR_0001'])
test('样稿Excel七表、冻结、筛选、验证、原生跳转与动态统计',lambda:inspect_xlsx(OUT/'样稿/剧本资产需求清单.xlsx',{s['name']:len(data['sheets'][s['name']]) for s in schema['sheets']}))
test('空白Excel无假资产且统计为零',lambda:inspect_xlsx(OUT/'空白模板/剧本资产需求清单.xlsx',{s['name']:0 for s in schema['sheets']}))

def metadata():
    text=(ROOT/'SKILL.md').read_text(encoding='utf-8');front=text.split('---',2)[1]
    assert_true(re.search(r'^name: script-asset-breakdown$',front,re.M))
    assert_true(re.search(r'^description: .+',front,re.M))
    assert_true('TODO' not in text)
    for target in re.findall(r'\]\(([^)]+)\)',text):assert_true((ROOT/target).exists(),target)
    yaml=(ROOT/'agents/openai.yaml').read_text(encoding='utf-8')
    for line in yaml.splitlines()[1:]:
        if ':' in line:json.loads(line.split(':',1)[1].strip())
test('Skill元数据、引用与显示入口人工结构替代校验',metadata)
(OUT/'结构与更新验证.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(results),'cases':[x['case'] for x in results]},ensure_ascii=False,indent=2))
