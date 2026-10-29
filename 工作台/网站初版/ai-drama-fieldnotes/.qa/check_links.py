from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,tarfile
root=Path(__file__).resolve().parents[1];dist=root/'dist'
class Page(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  if tag in ('a','link') and 'href' in a:self.links.append(a['href'])
  if tag=='script' and 'src' in a:self.links.append(a['src'])
pages={}
for p in dist.rglob('*.html'):
 doc=Page();doc.feed(p.read_text(encoding='utf-8'));pages[p]=doc
count=0
for p,doc in pages.items():
 for href in doc.links:
  u=urlsplit(href)
  if u.scheme or u.netloc:continue
  target=(dist/unquote(u.path).lstrip('/')) if u.path.startswith('/') else p.parent/unquote(u.path)
  if not u.path:target=p
  if target.is_dir():target=target/'index.html'
  assert target.exists(),f'{p.name}: missing {href}'
  if u.fragment and target in pages:assert unquote(u.fragment) in pages[target].ids,f'{p.name}: missing fragment {href}'
  count+=1
print(f'PASS: {len(pages)} pages, {count} internal links/assets/fragments.')
