from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,re,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
SOURCE=Path(r'D:\File\WeiXin\xwechat_files\wxid_oy7fvymdeny722_5be2\msg\file\2026-10\保镖驾到，大小姐爱上了我一卡+人物小传(1).docx')
OUT=Path('.asset-skill-build/v3');OUT.mkdir(exist_ok=True)
NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def text(p):
 parts=[]
 for n in p.iter():
  k=n.tag.rsplit('}',1)[-1]
  if k=='t':parts.append(n.text or '')
  elif k=='tab':parts.append('\t')
  elif k in ['br','cr']:parts.append('\n')
 return ''.join(parts)
with ZipFile(SOURCE) as z:root=ET.fromstring(z.read('word/document.xml'))
body=root.find('{'+NS+'}body');records=[];episode=None;scene=None
nums={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
for i,p in enumerate(body.iter('{'+NS+'}p'),1):
 s=text(p);m=re.fullmatch('第([一二三四五六七八九十0-9]+)集',s.strip())
 if m:episode=nums.get(m[1],int(m[1]) if m[1].isdigit() else None);scene=None
 m=re.match(r'^(\d+-\d+)\s+',s.strip())
 if m:scene=m[1]
 records.append({'id':f'P{i:03}','text':s,'episode':episode,'scene':scene})
data={'file':str(SOURCE),'name':SOURCE.name,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'records':records}
(OUT/'source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
start=int(sys.argv[1]) if len(sys.argv)>1 else 1;end=int(sys.argv[2]) if len(sys.argv)>2 else len(records)
for r in records[start-1:end]:print(f'{r["id"]} [E{r["episode"]}/{r["scene"]}] {r["text"]}')
print('TOTAL',len(records))
