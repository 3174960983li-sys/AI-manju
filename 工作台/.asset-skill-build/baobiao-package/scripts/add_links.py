"""Add missing native hyperlinks and dynamic names to a newly exported XLSX.
Artifact Tool creates all workbook data/styles/tables; this fills its hyperlink gap.
"""
from pathlib import Path
from zipfile import ZipFile
import json,sys,posixpath,xml.etree.ElementTree as ET
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('',NS);ET.register_namespace('r',R)
def tag(n):return '{'+NS+'}'+n
def add_links(file,links):
    file=Path(file)
    with ZipFile(file) as z:
        infos=z.infolist();parts={i.filename:z.read(i.filename) for i in infos}
    book=ET.fromstring(parts['xl/workbook.xml'])
    rel=ET.fromstring(parts['xl/_rels/workbook.xml.rels'])
    targets={r.attrib['Id']:r.attrib['Target'] for r in rel}
    sheetpaths={s.attrib['name']:posixpath.normpath(posixpath.join('xl',targets[s.attrib['{'+R+'}id']])) for s in book.find(tag('sheets'))}
    sheetpaths={k:v.lstrip('/') for k,v in sheetpaths.items()}
    names=book.find(tag('definedNames'))
    if names is None:
        names=ET.Element(tag('definedNames'));children=list(book)
        calc=book.find(tag('calcPr'));book.insert(children.index(calc) if calc is not None else len(children),names)
    existing={x.attrib['name']:x for x in names}
    roots={}
    for link in links:
        if link.get('definition') and link['location'] not in existing:
            node=ET.SubElement(names,tag('definedName'),{'name':link['location']});node.text=link['definition'];existing[link['location']]=node
        p=sheetpaths[link['sheet']]
        root=roots.setdefault(p,ET.fromstring(parts[p]))
        container=root.find(tag('hyperlinks'))
        if container is None:
            container=ET.Element(tag('hyperlinks'))
            # OOXML order: hyperlinks follow conditionalFormatting/dataValidations and precede print/drawings/tableParts.
            followers={'printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst'}
            index=next((i for i,x in enumerate(root) if x.tag.rsplit('}',1)[-1] in followers),len(root));root.insert(index,container)
        ET.SubElement(container,tag('hyperlink'),{'ref':link['cell'],'location':link['location']})
    for p,root in roots.items():parts[p]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    parts['xl/workbook.xml']=ET.tostring(book,encoding='utf-8',xml_declaration=True)
    tmp=file.with_suffix('.links.tmp')
    with ZipFile(tmp,'w') as z:
        for info in infos:z.writestr(info,parts[info.filename])
    tmp.replace(file)
if __name__=='__main__':add_links(sys.argv[1],json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))
