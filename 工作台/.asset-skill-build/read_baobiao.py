from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
p=Path(r'D:\File\WeiXin\xwechat_files\wxid_oy7fvymdeny722_5be2\msg\file\2026-10\保镖驾到_60集场景与道具精简整合清单.docx')
n={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(p) as z:r=ET.fromstring(z.read('word/document.xml'))
records=[];i=t=0
for x in r.find('w:body',n):
 if x.tag.endswith('}p'):
  i+=1;records.append({'id':f'P{i:03}','text':''.join(k.text or '' for k in x.findall('.//w:t',n))})
 elif x.tag.endswith('}tbl'):
  t+=1
  for j,row in enumerate(x.findall('w:tr',n),1):
   records.append({'id':f'T{t}R{j:03}','cells':[''.join(k.text or '' for k in cell.findall('.//w:t',n)) for cell in row.findall('w:tc',n)]})
out=Path('.asset-skill-build/baobiao-source.json');out.write_text(json.dumps({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'paragraphs':i,'tables':t,'records':records},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'paragraphs={i}, tables={t}')
for row in records:print(row['id']+': '+row.get('text',' | '.join(row.get('cells',[]))))
