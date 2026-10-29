from pathlib import Path
import json,re,hashlib,zipfile
from lxml import etree
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
w=Path(__file__).parent;p=w/'render'
data=json.loads((w/'校验与镜头数据.json').read_text(encoding='utf-8'))
pdf=pdfium.PdfDocument(p/'episode1.pdf');thumbs=[];texts=[]
for i,page in enumerate(pdf):
    t=page.get_textpage().get_text_range();texts.append(t)
    im=page.render(scale=1.4).to_pil().convert('RGB');im.save(p/f'page-{i+1}.png')
    small=im.copy();small.thumbnail((400,570));thumb=Image.new('RGB',(420,600),'#eeeeee');thumb.paste(small,(10,20));ImageDraw.Draw(thumb).text((10,5),str(i+1),fill='black');thumbs.append(thumb)
for group in range((len(thumbs)+7)//8):
    contact=Image.new('RGB',(420*4,600*2),'white')
    for j,im in enumerate(thumbs[group*8:(group+1)*8]):contact.paste(im,((j%4)*420,(j//4)*600))
    contact.save(p/f'contact-{group+1}.png')
def norm(x):return re.sub(r'\s+','',x)
joined=norm(''.join(texts))
for i in range(1,26):assert f'E01-S{i:02}' in joined
assert all(len(norm(t))>70 for t in texts)
with zipfile.ZipFile(data['files'][0]) as z:
    root=etree.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    content=norm(''.join(root.xpath('//w:t/text()',namespaces=ns)))
for line in Path(data['files'][1]).read_text(encoding='utf-8').splitlines():
    if line.startswith('|'):
        cells=[x.strip() for x in line.strip('|').split('|')]
        if set(''.join(cells))=={'-'}:continue
        # Skip header/overview formatting; seven-field body cells should all be present.
        if len(cells)==7 and cells[0].startswith('E01-'):
            for v in cells[1:]:assert norm(v) in content,v
assert ''.join(data['dialogue_original'])==''.join(data['dialogue_fragments'])
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in data['all_original_files_unchanged'].items())
qa={'pages':len(pdf),'page_chars':[len(norm(x)) for x in texts],'all_25_shots_rendered':True,'all_seven_field_body_cells_preserved':True,'all_six_dialogue_utterances_exact':True,'protected_files_unchanged':True,'visual_review':'pending'}
(w/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False))
