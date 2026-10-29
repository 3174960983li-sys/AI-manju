"""Add row outlines, native filter and print setup absent from the authoring surface.
Patches layout in a new export and restores raw cells as literal inline strings.
This avoids writer escape prefixes changing paragraphs starting with '='.
"""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,sys
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ET.register_namespace('',NS);ET.register_namespace('r',R)
def tag(x):return '{'+NS+'}'+x
def patch(file,layout):
 file=Path(file)
 with ZipFile(file)as z:infos=z.infolist();parts={i.filename:z.read(i.filename) for i in infos}
 book=ET.fromstring(parts['xl/workbook.xml']);defined=book.find(tag('definedNames'))
 if defined is None:
  defined=ET.Element(tag('definedNames'));calc=book.find(tag('calcPr'));book.insert(list(book).index(calc) if calc is not None else len(book),defined)
 for i,s in enumerate(layout['sheets']):
  name=f'xl/worksheets/sheet{i+1}.xml';root=ET.fromstring(parts[name])
  pr=root.find(tag('sheetPr'))
  if pr is None:pr=ET.Element(tag('sheetPr'));root.insert(0,pr)
  op=pr.find(tag('outlinePr'))
  if op is None:op=ET.SubElement(pr,tag('outlinePr'))
  op.set('summaryBelow','0');op.set('summaryRight','1');op.set('showOutlineSymbols','1')
  pp=pr.find(tag('pageSetUpPr'))
  if pp is None:pp=ET.SubElement(pr,tag('pageSetUpPr'))
  pp.set('fitToPage','1')
  for v in root.findall('.//'+tag('sheetView')):v.set('showOutlineSymbols','1')
  fmt=root.find(tag('sheetFormatPr'))
  if fmt is not None:fmt.set('outlineLevelRow','1')
  rows={int(r.attrib['r']):r for r in root.find(tag('sheetData'))}
  for asset in s['assets']:
   for item in asset['raw']:
    cell=next(c for c in rows[item['row']] if c.attrib.get('r')=='D'+str(item['row']))
    for child in list(cell):cell.remove(child)
    cell.set('t','inlineStr');inline=ET.SubElement(cell,tag('is'));t=ET.SubElement(inline,tag('t'))
    t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=item['text']
  for group in s['groups']:
   rows[group['master']].set('collapsed','1')
   for n in range(group['first'],group['last']+1):
    rows[n].set('hidden','1');rows[n].set('outlineLevel','1')
  # Insert worksheet children in OOXML order, before page layout and after the data.
  filt=root.find(tag('autoFilter'))
  if filt is None:
   filt=ET.Element(tag('autoFilter'));idx=list(root).index(root.find(tag('sheetData')))+1;root.insert(idx,filt)
  filt.set('ref',f'A5:E{s["last_row"]}')
  for t in ['printOptions','pageMargins','pageSetup','headerFooter']:
   old=root.find(tag(t))
   if old is not None:root.remove(old)
  ET.SubElement(root,tag('printOptions'),{'horizontalCentered':'1'})
  ET.SubElement(root,tag('pageMargins'),{'left':'0.25','right':'0.25','top':'0.35','bottom':'0.35','header':'0.15','footer':'0.15'})
  ET.SubElement(root,tag('pageSetup'),{'paperSize':'8','orientation':'landscape','fitToWidth':'1','fitToHeight':'0','usePrinterDefaults':'0'})
  hf=ET.SubElement(root,tag('headerFooter'));ET.SubElement(hf,tag('oddFooter')).text='&C第 &P 页 / 共 &N 页'
  quoted="'"+s['name'].replace("'","''")+"'"
  for old in list(defined):
   if old.attrib.get('localSheetId')==str(i) and old.attrib.get('name') in ['_xlnm.Print_Area','_xlnm.Print_Titles']:defined.remove(old)
  ET.SubElement(defined,tag('definedName'),{'name':'_xlnm.Print_Area','localSheetId':str(i)}).text=f'{quoted}!$A$1:$E${s["last_row"]}'
  ET.SubElement(defined,tag('definedName'),{'name':'_xlnm.Print_Titles','localSheetId':str(i)}).text=f'{quoted}!$1:$5'
  parts[name]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 parts['xl/workbook.xml']=ET.tostring(book,encoding='utf-8',xml_declaration=True)
 tmp=file.with_suffix('.layout.tmp')
 with ZipFile(tmp,'w')as z:
  for inf in infos:z.writestr(inf,parts[inf.filename])
 tmp.replace(file)
if __name__=='__main__':patch(sys.argv[1],json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))
