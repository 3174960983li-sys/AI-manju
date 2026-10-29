from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,re,hashlib,sys
NS='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def cn(s):
 if s.isdigit():return int(s)
 digits={'零':0,'〇':0,'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9};n=0;v=0
 for c in s:
  if c in digits:v=digits[c]
  elif c in ['十','百']:n+=(v or 1)*({'十':10,'百':100}[c]);v=0
 return n+v
def extract(path):
 path=Path(path)
 with ZipFile(path)as z:root=ET.fromstring(z.read('word/document.xml'))
 records=[];episode=None;scene=None
 for i,p in enumerate(root.find('{'+NS+'}body').iter('{'+NS+'}p'),1):
  parts=[]
  for x in p.iter():
   k=x.tag.rsplit('}',1)[-1]
   if k=='t':parts.append(x.text or '')
   elif k=='tab':parts.append('\t')
   elif k in ['br','cr']:parts.append('\n')
  text=''.join(parts);m=re.fullmatch('第([零〇一二两三四五六七八九十百0-9]+)集',text.strip())
  if m:episode=cn(m[1]);scene=None
  m=re.match(r'^(\d+-\d+)\s+',text.strip())
  if m:scene=m[1]
  records.append({'id':f'P{i:03}','text':text,'episode':episode,'scene':scene})
 return {'file':str(path),'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':records}
if __name__=='__main__':
 out=Path(sys.argv[2])
 if out.exists():raise SystemExit('拒绝覆盖已有来源目录')
 out.write_text(json.dumps(extract(sys.argv[1]),ensure_ascii=False,indent=2),encoding='utf-8')
