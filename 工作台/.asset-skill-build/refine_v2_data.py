from pathlib import Path
import json
OUT=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.2_分组阅读版')
OLD=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.1')
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
data=json.loads((OUT/'资产分组数据.json').read_text(encoding='utf-8'))
src=json.loads((OLD/'核验资料/来源定位与原文抽取.json').read_text(encoding='utf-8'))
raw={r['id']:r for r in src['records']}
def ref(loc):
 r=raw[loc]
 if 'text'in r:text=r['text']
 else:
  cells=r['cells']
  if loc.startswith('T2R'):indices=[0,2,3]
  elif loc.startswith(('T3R','T4R','T7R')):indices=[0,2]
  elif loc.startswith('T8R'):indices=[0,len(cells)-1]
  else:indices=list(range(len(cells)))
  text='；'.join(cells[i] for i in indices if i<len(cells))
 text=text if len(text)<=120 else text[:117]+'…'
 if loc.startswith('T'):
  a,b=loc[1:].split('R');label=f'源表{int(a)}第{int(b)}行'
 else:label=f'源段{int(loc[1:])}'
 return text+'\n〔'+label+'〕'
for rows in data['sheets'].values():
 for r in rows:
  if r['id'] in ['S01-01','S01-02','S01-04','S01-05','S01-07']:
   r['source_refs']=[{'S01-01':'T6R004','S01-02':'T6R005','S01-04':'T6R006','S01-05':'T6R006','S01-07':'T5R002'}[r['id']]]
  if r['id']=='S01-03':r['description']='别墅书房；结构与陈设待原剧补充。'
  if r['id'] in ['S01','S03','S04']:
   extra={'S01':'T5R002','S03':'T5R005','S04':'T5R006'}[r['id']]
   if extra not in r['source_refs']:r['source_refs'].append(extra)
  r['original']='\n'.join(ref(k) for k in r['source_refs'])
  if r['kind']=='子场景':
   if r['id'].startswith('S01-'):r['episodes']='第3集起相关；子场景集数未细分'
   elif r['id'].startswith('S12-'):r['episodes']='第22、29、53集；对应未列'
   elif '（子空间分配未列）' not in r['episodes']:r['episodes']=r['episodes']+'（子空间分配未列）'
(OUT/'资产分组数据.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'assets/sample-script.md';t=p.read_text(encoding='utf-8');p.write_text(t.replace('CHR-0001','R01'),encoding='utf-8')
