from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,sys,copy,re,hashlib,importlib.util
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).parent
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OUT=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\原剧第1—10集_资产拆解_V3')
sys.path.insert(0,str(ROOT/'scripts'))
from check_data import check
from merge_data import merge
from extract_docx import extract
d=json.loads((OUT/'资产数据_V3.json').read_text(encoding='utf-8'))
source={r['id']:r for r in d['source_records']};allnodes={r['id']:r for rows in d['assets'].values()for r in rows}
tests=[]
def ensure(x,msg='验证失败'):
 if not x:raise AssertionError(msg)
def case(label,f):f();tests.append(label)
case('V3结构、来源与逐集记录有效',lambda:ensure(not check(d)))
def source_compare():
 fresh=extract(d['meta']['source_path'])
 ensure(fresh['sha256']==d['meta']['source_sha256'])
 ensure(fresh['records']==d['source_records'])
 ensure(len(fresh['records'])==501)
case('原Word重新提取501段逐字一致且文件未变',source_compare)
def source_coverage():
 heads={r['scene']:r['id']for r in d['source_records']if re.match(r'^\d+-\d+\s',r['text'].strip())}
 ensure(len(heads)==23)
 ensure({r['scene']for r in d['scene_audit']}==set(heads))
 for entry in d['scene_audit']:
  ensure(entry['heading_id']==heads[entry['scene']]);ensure(all(x in allnodes for x in entry['spaces']))
case('10集23场空间覆盖全部有对应',source_coverage)
def ep(key,modes=None):return sorted({e['episode']for e in allnodes[key]['events']if e['mode']in (modes or ['现场','画外音','闪回'])})
expect={'R01':list(range(1,11)),'R02':list(range(1,11)),'R03':[3,4,5,6,9,10],'R21':[2,3,8],'R22':[9,10],'R05':[9,10],'R25':[1],'R09':[4],'R10':[4],'R11':[3,6,8],'R27':[4],'R28':[2,3],'R29':[6,7],'R30':[6],'R31-04':[3],'R32-01':[9]}
case('主要角色全部出现集数逐项复核',lambda:ensure(all(ep(k)==v for k,v in expect.items()),str({k:ep(k)for k in expect})))
case('老高7集只提及不伪算再次发声',lambda:ensure(ep('R25',['画外音'])==[1]and ep('R25',['仅提及'])==[7]))
case('未来小传角色没有虚构当前出场',lambda:ensure(all(not ep(x)for x in ['R04','R06','R07','R23','R24','R34'])))
case('睡衣7—8集、黑衣红手套9—10、黑袍4集',lambda:ensure(ep('R02-02')==[7,8]and ep('R05-01')==[9,10]and ep('R27-01')==[4]))
case('候选服装无实际出场、伤势与穿着关联有效',lambda:ensure(sum(x['candidate']for x in allnodes.values())==6 and all(not x['events'] for x in allnodes.values()if x['candidate'])and allnodes['R02-02-01']['outfit_id']=='R02-02'))
case('张阎王伤势与艾薇重伤各按明确集数',lambda:ensure(ep('R03-02')==[5]and ep('R03-01')==[6]and ep('R22-02')==[10]))
case('院子清理、卧室日夜和阳台层级正确',lambda:ensure(allnodes['S01-10-01']['parent_id']=='S01-10'and ep('S01-08-01')==[8]and ep('S01-10-02')==[7,8]))
for label,change in [
 ('候选伪造实际出场被拒绝',lambda x:x['assets']['角色'][4].update({'candidate':True,'events':[{'episode':1,'scene':'1-1','mode':'现场','source_id':'P064'}]})),
 ('孤儿与拆组被拒绝',lambda x:x['assets']['角色'].append(x['assets']['角色'].pop(1))),
 ('错配集数被拒绝',lambda x:x['assets']['角色'][0]['events'][0].update({'episode':9})),
 ('缺失原文来源被拒绝',lambda x:x['assets']['角色'][0].update({'source_ids':['NO']}))]:
 q=copy.deepcopy(d);change(q);case(label,lambda q=q:ensure(bool(check(q))))
def merge_test():
 q=copy.deepcopy(d);q['assets']['角色'][0]['user_notes']='保留批注'
 item=copy.deepcopy(q['assets']['角色'][1]);item.update({'id':'R01-06','name':'新增测试状态'})
 out=merge(q,{'schema_version':3,'assets':{'角色':[item]}})
 ids=[x['id']for x in out['assets']['角色']]
 ensure(ids.index('R01-06')<ids.index('R02'));ensure(out['assets']['角色'][0]['user_notes']=='保留批注');ensure(out['assets']['场景']==q['assets']['场景'])
 try:merge(q,{'source_records':[dict(q['source_records'][0],text='改写原文')]})
 except ValueError:pass
 else:raise AssertionError('来源被静默修改')
 q['assets']['角色'][0]['review']='已确认'
 try:merge(q,{'assets':{'角色':[{'id':'R01','description':'覆盖'}]}})
 except ValueError:pass
 else:raise AssertionError('确认内容被覆盖')
case('增补组内插入、批注保留、源目录和确认内容保护',merge_test)
NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def verify_xlsx(file,data,layout):
 sources={r['id']:r for r in data['source_records']};raw_count=0
 with ZipFile(file)as z:
  ensure(z.testzip()is None)
  wb=ET.fromstring(z.read('xl/workbook.xml'))
  ensure([x.attrib['name']for x in wb.find('x:sheets',NS)]==['角色','场景','道具'])
  names=[(x.attrib.get('name'),x.attrib.get('localSheetId'))for x in wb.find('x:definedNames',NS)]
  ensure(len(names)==len(set(names)))
  strings=[]
  if 'xl/sharedStrings.xml'in z.namelist():
   strings=[''.join(t.text or ''for t in n.findall('.//x:t',NS))for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  def value(c):
   if c is None:return ''
   if c.attrib.get('t')=='s':return strings[int(c.find('x:v',NS).text)]
   if c.attrib.get('t')=='inlineStr':return ''.join(t.text or ''for t in c.findall('.//x:t',NS))
   v=c.find('x:v',NS);return v.text if v is not None else ''
  for i,sheet in enumerate(layout['sheets'],1):
   root=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'));rowmap={int(x.attrib['r']):x for x in root.findall('x:sheetData/x:row',NS)}
   cells={c.attrib['r']:c for c in root.findall('.//x:c',NS)}
   ensure(root.find('.//x:pane',NS).attrib['topLeftCell']=='C6')
   ensure(root.find('x:autoFilter',NS)is not None)
   ensure(root.find('x:mergeCells',NS)is None)
   ensure(root.find('x:sheetPr/x:outlinePr',NS).attrib['summaryBelow']=='0')
   ensure(root.find('x:pageSetup',NS).attrib['paperSize']=='8')
   ensure([value(cells.get(c+'5'))for c in 'ABCDE']==['编号','名称','资产描述','完整原文','出现集数'])
   ensure(not any(c.attrib.get('t')=='e'for c in cells.values()))
   for node,asset in zip(data['assets'][sheet['name']],sheet['assets']):
    master=asset['master'];ensure(value(cells['A'+str(master)])==node['id'])
    ensure(rowmap[master].attrib.get('hidden')!='1')
    actual={q:[]for q in node['source_ids']}
    for raw in asset['raw']:
     r=raw['row'];ensure(rowmap[r].attrib.get('hidden')=='1'and rowmap[r].attrib.get('outlineLevel')=='1')
     ensure(value(cells.get('A'+str(r)))=='')
     text=value(cells.get('D'+str(r)));ensure(text==raw['text'],'原文单元格不一致 '+node['id']+' '+raw['source_id'])
     actual[raw['source_id']].append((raw['part'],text));raw_count+=1
     ensure(float(rowmap[r].attrib.get('ht',15))<=409)
    for q,parts in actual.items():ensure(''.join(t for _,t in sorted(parts))==sources[q]['text'],'段落拼接与源不一致 '+q)
   ensure(len(sheet['assets'])==len(data['assets'][sheet['name']]))
 return raw_count
layout=json.loads((OUT/'版面与原文索引.json').read_text(encoding='utf-8'))
case('真实输出868段附属行逐字对照及原生折叠/打印结构',lambda:ensure(verify_xlsx(OUT/'剧本资产需求清单.xlsx',d,layout)==868))
for folder,file in [('blank','blank-data.json'),('sample','sample-data.json')]:
 q=json.loads((ROOT/'assets'/file).read_text(encoding='utf-8'));p=BASE/folder
 l=json.loads((p/'版面与原文索引.json').read_text(encoding='utf-8'))
 case(folder+'模板三表五列及原文输出',lambda q=q,p=p,l=l:verify_xlsx(p/'剧本资产需求清单.xlsx',q,l))
stress=json.loads((BASE/'stress-data.json').read_text(encoding='utf-8'));sl=json.loads((BASE/'stress/版面与原文索引.json').read_text(encoding='utf-8'))
case('超过单格上限的长段、等号、制表/换行、空格和emoji逐字无损',lambda:ensure(verify_xlsx(BASE/'stress/剧本资产需求清单.xlsx',stress,sl)>100))
text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
case('Skill元数据与引用完整',lambda:ensure(text.startswith('---\nname: script-asset-breakdown\n')and all((ROOT/q).exists()for q in re.findall(r'\]\(([^)]+)\)',text))))
case('V2短摘数据拒绝冒充V3完整原文',lambda:ensure(bool(check({'schema_version':2}))))
result={'passed':len(tests),'cases':tests,'source_paragraphs':501,'source_scenes':23,'verbatim_raw_rows':868,'raw_text_changed':False,'candidates':6,'primary_assets':{k:len(v)for k,v in d['assets'].items()}}
(OUT/'验证结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
