from pathlib import Path
import re,json,zipfile
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
from lxml import etree
work=Path(__file__).parent;render=work/'render'
manifest=json.loads((work/'manual-manifest.json').read_text(encoding='utf-8'))
def normalize(t):return re.sub(r'\s+','',t)
qa=[]
for idx,m in enumerate(manifest,1):
    name=Path(m['docx']).stem;pdf=pdfium.PdfDocument(render/(name+'.pdf'))
    thumbs=[];pagetext=[]
    for i,p in enumerate(pdf):
        text=p.get_textpage().get_text_range();pagetext.append(text)
        im=p.render(scale=1.5).to_pil().convert('RGB');im.save(render/f'm{idx}-p{i+1}.png')
        small=im.copy();small.thumbnail((425,600));thumb=Image.new('RGB',(445,630),'#dddddd');thumb.paste(small,(10,20));ImageDraw.Draw(thumb).text((10,4),f'{idx}-{i+1}',fill='black');thumbs.append(thumb)
    contact=Image.new('RGB',(445*4,630*2),'white')
    for i,thumb in enumerate(thumbs):contact.paste(thumb,((i%4)*445,(i//4)*630))
    contact.save(render/f'm{idx}-contact.png')
    with zipfile.ZipFile(m['docx']) as z:
        tree=etree.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        doctext=normalize(''.join(tree.xpath('//w:t/text()',namespaces=ns)))
    missing=[]
    for line in Path(m['source']).read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or re.match(r'^\|\s*:?-',line):continue
        units=[x.strip() for x in line.strip('|').split('|')] if line.startswith('|') else [re.sub(r'^(?:#{1,3}\s+|\d+\.\s+|-\s+)','',line)]
        for u in units:
            u=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',u).replace('**','').replace('`','')
            if normalize(u) not in doctext:missing.append(u)
    assert not missing,(m['title'],missing)
    assert all(len(normalize(t))>60 for t in pagetext), 'Blank or nearly empty unexpected page'
    headings=re.findall(r'^## (.+)$',Path(m['source']).read_text(encoding='utf-8'),re.M)
    pdftext=normalize(''.join(pagetext))
    assert all(normalize(h) in pdftext for h in headings), 'Heading not rendered'
    qa.append({'title':m['title'],'pages':len(pdf),'all_source_units_in_docx':True,'all_major_headings_in_pdf':True,'page_character_counts':[len(normalize(t)) for t in pagetext],'visual_review':'pending'})
(work/'manual-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False))
