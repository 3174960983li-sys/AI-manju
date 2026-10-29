from pathlib import Path
import re,json
import pypdfium2 as pdfium
from PIL import Image,ImageOps,ImageDraw
p=Path(__file__).parent/'render'
pdf=pdfium.PdfDocument(p/'storyboard-day-v02.pdf')
thumbs=[]
for i,page in enumerate(pdf):
    im=page.render(scale=1.5).to_pil().convert('RGB');im.save(p/f'v02-page-{i+1}.png')
    thumb=im.copy();thumb.thumbnail((510,700));canvas=Image.new('RGB',(530,730),'#dddddd');canvas.paste(thumb,(10,20));ImageDraw.Draw(canvas).text((10,5),str(i+1),fill='black');thumbs.append(canvas)
contact=Image.new('RGB',(530*4,730*2),'white')
for i,im in enumerate(thumbs):contact.paste(im,((i%4)*530,(i//4)*730))
contact.save(p/'v02-contact.png')
skill=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\自研Skill\shot-language-design')
broken=[];count=0
for file in skill.rglob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8-sig')):
        if '://' in link or link.startswith('#'):continue
        link=link.split('#')[0]
        if not link:continue
        count+=1
        if not (file.parent/link).exists():broken.append([str(file),link])
assert not broken,broken
entry=(skill/'SKILL.md').read_text(encoding='utf-8-sig')
assert entry.startswith('---\nname: shot-language-design\n')
assert 'V0.11' in entry
print(json.dumps({'pages':len(pdf),'local_links_checked':count,'broken_links':broken,'metadata_checked':True},ensure_ascii=False))
