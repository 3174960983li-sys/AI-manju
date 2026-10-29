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
def extract(path,episode_range=None):
 path=Path(path)
 with ZipFile(path)as z:root=ET.fromstring(z.read('word/document.xml'))
 records=[];episode=None;scene=None;stopped_at=None
 if episode_range is not None:
  start,end=episode_range
  if start<1 or end<start:raise ValueError('集数范围无效')
 for i,p in enumerate(root.find('{'+NS+'}body').iter('{'+NS+'}p'),1):
  parts=[]
  for x in p.iter():
   k=x.tag.rsplit('}',1)[-1]
   if k=='t':parts.append(x.text or '')
   elif k=='tab':parts.append('\t')
   elif k in ['br','cr']:parts.append('\n')
  text=''.join(parts);m=re.fullmatch('第([零〇一二两三四五六七八九十百0-9]+)集',text.strip())
  if m:
   episode=cn(m[1]);scene=None
   if episode_range is not None and episode>end:
    stopped_at=episode;break
  if episode_range is not None and (episode is None or not start<=episode<=end):continue
  m=re.match(r'^(\d+-\d+)(?=\s|日|夜|早|晚|晨|内|外)',text.strip())
  if m:scene=m[1]
  records.append({'id':f'P{i:03}','text':text,'episode':episode,'scene':scene})
 result={'file':str(path),'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':records}
 if episode_range is not None:
  found=sorted({r['episode'] for r in records})
  missing=sorted(set(range(start,end+1))-set(found))
  if missing:raise ValueError('未找到范围内集数：'+str(missing))
  result['scope']={'episodes':[start,end],'preamble_included':False,'stopped_at_episode_header':stopped_at,'found_episodes':found}
 return result
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');parser.add_argument('--episodes',nargs=2,type=int)
 args=parser.parse_args();out=Path(args.output)
 if out.exists():raise SystemExit('拒绝覆盖已有来源目录')
 out.write_text(json.dumps(extract(args.source,args.episodes),ensure_ascii=False,indent=2),encoding='utf-8')
