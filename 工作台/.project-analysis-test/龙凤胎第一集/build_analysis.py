from pathlib import Path
import hashlib, zipfile
from lxml import etree
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

src=Path(r'E:\AI漫剧\作品集\龙凤胎长出蛇尾\龙凤胎长出蛇尾前十集_208928.docx')
out=src.parent/'第一集项目剧本分析与导演本_讨论稿_V0.1.docx'
assert out.name == '第一集项目剧本分析与导演本_讨论稿_V0.1.docx'
initial_hash=hashlib.sha256(src.read_bytes()).hexdigest()
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(src) as z:
    a=[''.join(x.xpath('.//w:t/text()',namespaces=ns)) for x in etree.fromstring(z.read('word/document.xml')).xpath('//w:body//w:p',namespaces=ns)]
doc=Document(); sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.68);sec.bottom_margin=Inches(.65)
sec.left_margin=sec.right_margin=Inches(.76)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
    st=doc.styles[name];st.font.name='Microsoft YaHei';st.font.color.rgb=RGBColor(0,0,0)
    st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'微软雅黑')
doc.styles['Normal'].font.size=Pt(11)
doc.styles['Normal'].paragraph_format.line_spacing=1.18
doc.styles['Normal'].paragraph_format.space_after=Pt(6)
doc.styles['Title'].font.size=Pt(22)
doc.styles['Heading 1'].font.size=Pt(16)
doc.styles['Heading 2'].font.size=Pt(12)
for name in ['Heading 1','Heading 2']:
    doc.styles[name].paragraph_format.space_before=Pt(9)
    doc.styles[name].paragraph_format.space_after=Pt(5)
    doc.styles[name].paragraph_format.keep_with_next=True
source_style=doc.styles.add_style('SourceText',1)
source_style.base_style=doc.styles['Normal'];source_style.font.size=Pt(10.5)
source_style.paragraph_format.space_after=Pt(2)
source_style.paragraph_format.line_spacing=1.08
header=sec.header.paragraphs[0];header.text='龙凤胎长出蛇尾  第一集  项目剧本分析讨论稿'
header.runs[0].font.size=Pt(8)
footer=sec.footer.paragraphs[0];footer.alignment=2
r=footer.add_run('第 ');r.font.size=Pt(9)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
footer.add_run(' 页').font.size=Pt(9)

def p(s,bold_prefix=None):
    par=doc.add_paragraph()
    if bold_prefix and s.startswith(bold_prefix):
        par.add_run(bold_prefix).bold=True;par.add_run(s[len(bold_prefix):])
    else:par.add_run(s)
    return par
def h(s):doc.add_heading(s,2)
def page(title):
    par=doc.add_heading(title,1);par.paragraph_format.page_break_before=True
def table(headers,rows,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Inches(w)
    for i,x in enumerate(headers):t.rows[0].cells[i].text=x
    for row in rows:
        cells=t.add_row().cells
        for c,s in zip(cells,row):c.text=s
    for ri,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr()
        if ri==0:trpr.append(OxmlElement('w:tblHeader'))
        for ci,cell in enumerate(row.cells):
            cell.width=Inches(widths[ci]);pr=cell._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            pr.append(borders)
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E6ECF2' if ri==0 else ('FFFFFF' if ri%2 else 'F4F6F8'));pr.append(sh)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),'80');e.set(qn('w:type'),'dxa');margins.append(e)
            pr.append(margins)
            va=OxmlElement('w:vAlign');va.set(qn('w:val'),'center');pr.append(va)
            for par in cell.paragraphs:
                par.paragraph_format.space_after=Pt(3);par.paragraph_format.line_spacing=1.08
                for run in par.runs:run.font.size=Pt(10);run.bold=(ri==0)
    return t

doc.add_paragraph('龙凤胎长出蛇尾',style='Title')
doc.add_paragraph('第一集项目剧本分析与导演本讨论稿',style='Subtitle')
p('2026年10月27日  V0.1  使用项目剧本分析 Skill V1.5')
h('本轮结论')
p('第一集的任务是让受宠的新母亲第一次遭遇无法解释的身体异变：先建立一家人对双胎的珍视，再由凌灵长出蛇尾打破安全感。护子悬疑的起点是母亲发现异常；本集尚未进入逃亡、争夺或身份审判。')
p('制作范围仅为第一集1-1与1-2。男婴显尾、女主误认生父、林疏影逼门及洗礼冲突均不提前加入。原文完整保留于本稿逐场章节，分析和候选不会替换原文。')
h('已经确认的要求')
p('AI仿真人竖屏短剧；单集目标90—150秒；护子悬疑为主，受压后逐步反击；观众跟随苏浅浅疑惧，暂不确认生父与蛇尾真相；快节奏、强情绪。具体竖屏比例、平台、预算和成片参考尚未锁定。')
h('这次怎样分析')
p('先核第一集的事件与结束位置，再区分人物知道什么和观众得到什么，随后提取两场的表达义务与连续性条件，最后整理资产和验证任务。下面给出依据、判断及制作影响，不将第一轮分析冒称导演或分镜已完成。')
h('本轮完成与下一阶段')
p('已完成第一集原文核对、故事与人物分析、两场拆解、时长条件检查及制作准备清单。导演处理仍是待深化方向；没有逐镜表、站位图、图片或视频提示词。本稿是可批注的分析讨论稿，后续选定内容继续更新同一导演本。')

page('故事人物与观众信息')
h('第一集的因果链')
p('双胎满月受到珍视→太御夫人交玉牌、凌云表达信任→封印异动使凌云离开→入夜月光照到摇篮→凌灵哭泣→苏浅浅检查襁褓→看见女婴小腿融合并生出雪白鳞片→惊恐后退。封印异动与孩子异变在本集只形成叙事关联，尚不能断言存在因果。')
table(['角色','原资料与本集状态','本集作用及边界'],[
('苏浅浅','人物资料25岁；本集为双胎满月的母亲','接受家人珍视，听哭声检查孩子，发现异常。恐惧不等于已决定抛弃孩子。'),
('凌云','人物资料28岁；天剑宗宗主','温柔照顾妻子，因封印异动离开。此集没有仇蛇宣言或怀疑妻子。'),
('太御夫人','人物资料80岁；凌云祖母','赠玉牌、认可苏浅浅。不能提前写成识破血脉的知情人。'),
('凌昭','男婴，当前满月','第一场在摇篮睡眠；第二场列为在场。本集未写显尾。'),
('凌灵','女婴，当前满月','第二场哭泣并出现蛇尾，是本集异常载体。未来两岁设定不用于当前外形。')],[.85,2.0,4.13])
h('观众应该知道什么')
p('应明确：一家人珍视两个孩子；苏浅浅原本处在安全关系中；凌云有离开的理由；异常发生在女婴身上；母亲此前没有预料。应保留未知：异变原因、血缘真相、蛇妖是否介入。不能用本集没有的台词、声音或影像先替观众确认答案。')
h('世界与时代的边界')
p('原文支持架空仙侠宗门，不对应某个已确定历史朝代。月光与异变同场出现，但本集不足以单独证明所有触发、遮光恢复和阵法规则。后续背景仅用于提醒不能泄露真相，不将其加进本集画面。')

page('第一场原文与分析')
p('原场号1-1，日，内，静心苑寝殿。角色：苏浅浅、凌云、太御夫人和双胎婴儿。原文P022—P035；P序为本轮段落定位。')
h('原剧本')
doc.add_paragraph(a[20],style='SourceText')
for text in a[21:36]:
    if text.strip():doc.add_paragraph(text,style='SourceText')
h('本场必须完成的表达')
p('长命锁、两只摇篮、赠玉牌和拢披衣共同建立珍视与接纳，不能只留下大量背景装饰，却让观众未理解苏浅浅得到的信任。巡山令蓝光与钟声触发离开；凌云说赶在洗礼前回来，形成短期回归期待。')
p('空间与状态：原文当前观察中男婴在左、女婴在右，换观察方向后不把画面左右机械当作世界位置。长命锁放在摇篮上方红绸处，不自动改成婴儿佩戴；玉牌从太御夫人转入苏浅浅掌心。')
p('处理要点候选：优先保住交付、照顾、受命离开的关系动作，再决定装饰信息取舍。此处不指定镜数、焦段或逐镜秒数。')

page('第二场原文与分析')
p('原场号1-2  夜  内  静心苑寝殿。出场：苏浅浅、凌昭与凌灵婴儿。关键对象：月光、雕花窗棂、摇篮、襁褓被褥、凌灵变化中的腿与鳞片。定位：源文档P037—P044。')
h('原剧本')
for text in a[36:45]:
    if text.strip():doc.add_paragraph(text,style='SourceText')
h('本场必须完成的表达')
p('先由哭声引起检查，再由母亲解开襁褓看到真实变化。若仅出现已经完成的蛇尾，原文正在变化的冲击会减弱；若变化早于母亲检查就被清楚展示，观众与母亲的发现顺序会改变，须由导演阶段说明取舍。')
p('变形应能读清是同一个女婴身体的变化：上身、面孔和襁褓关系连续，小腿融合，雪白鳞片上延到腰腹。不能把尾巴做成靠近孩子的另一条独立蛇，也不能误让男婴一起变化。')
p('母亲的恐惧对象首先是无法解释的异常。本集没有认定奸夫、生父或杀害孩子的台词，不能补入这些心理定论。原文只要求惊恐与后退，不自动加尖叫、丢弃孩子或放大伤害。')
h('空间与环境连续性')
p('月光从窗进入并落到摇篮，是本场可见条件；不为了让环境运动而添加暴风、蛇影或妖气。苏浅浅解开襁褓时在摇篮边，后退两步需有空间，不让她仍抱着孩子却瞬间出现在远处。原文没写抱起，不能默认发生了抱起再放下。')
h('本集结束边界')
p('结束于苏浅浅惊恐后退。可以让观众带着异常原因的疑问离开，但不提前接入第二集的男婴尾尖、过去记忆、逃走决定或敲门压力。凌灵本集是雪白色蛇尾，不能因后续其他尾色而混用。')

page('制作需求与时长检查')
table(['需要准备','本集依据与状态','优先验证内容'],[
('五个角色基准','苏浅浅、凌云、太御夫人及两个满月婴儿；婴儿与未来两岁版本分开','双胎身份可区分，成人和婴儿跨画面身份不漂移'),
('寝殿昼夜两态','同一地点，日景接夜景；两摇篮、窗与通路关系需核','昼夜变化不把布局重建，母亲靠近与后退可成立'),
('交互道具','玉牌、巡山令、红绸与长命锁、披衣、襁褓','交付与亮光节点清楚，锁的位置和持物归属不混乱'),
('女婴变形状态','正常腿→变化中→蛇尾与雪白鳞片；具体终态另待设计','上身身份保持、腿尾关系连续；未测试不能报工具可实现'),
('声音与字幕','原文六句对白117字符含标点，另有钟声、婴儿哭声及原有字幕','对白可辨，哭声先触发检查；字幕不遮盖关键身体变化')],[1.05,3.05,2.88])
h('时长不能由字数直接决定')
p('第一集正文683字符，含人物表、动作与字幕等；对白提取后117字符，含标点，不含说话者和表演提示，非实测发声时长。内容短不证明90秒一定不足，变形、互动与理解反应也需要时间；同样不能为凑150秒循环哭声、反应或空镜。')
p('下一阶段先试读六句对白，再分别预演赠牌/照顾、受命离开、检查襁褓、变形与反应的成立时间；叠加或省略关系需要明确。合计后对照90—150秒，目标时长不自动等于每集必须150秒。此处不编造精确测时。')
h('风险对应什么问题')
p('最优先验证凌灵正常状态到蛇尾的连续变化，其次是母亲开襁褓与后退的接触/空间，再是双摇篮与三名成人的竖屏可读性。先写清成功条件，再决定需哪些图片、合成或生成测试，不在本轮直接调用媒体或报成本。')

page('候选方向与导演交接')
h('画面方向的两个候选')
p('候选A：温暖的仙门日常转入清冷但仍真实可辨的月夜。第一场人物与材质亲近，第二场靠色温、光源和身体异常形成变化。优点是幸福与异常的落差明确，符合已选护子悬疑；风险是夜景过暗会遮住核心变化。推荐作为后续讨论起点，未锁定具体影调。')
p('候选B：两场维持清晰明亮的仙侠质感，主要依靠行为与身体变化制造不安。优点是竖屏信息易读，风险是两场气氛落差较弱，需要导演更准确组织发现过程。两者都是本剧原创候选，不声称已查证当前平台的主流成片风格。')
h('制作路线的条件候选')
p('可先建立人物、寝殿与道具一致性，再验证关键变形样段；变形可以比较直接动态生成与分状态素材加合成的可行性。选择依据是实际结果能否保持女婴身份、腿尾连续、襁褓接触与观察过程，而不是预设某个平台一定成功。未指定平台时先交设计条件，不虚构接口参数。')
h('交给导演的有效内容')
p('范围固定为第一集1-1与1-2，依据当前原稿，未采用任何剧情修补。已确认护子悬疑、跟随母亲疑惧、AI仿真人竖屏、90—150秒和快节奏强情绪。必须保住受宠与信任、凌云有因离开、母亲检查后发现女婴变化，以及未知原因的结束状态。')
p('可变手段包括未锁的表演细化、空间组织、观看顺序、声音与节奏，但不能暗改事件、人物知识、原对白或本集结束边界。具体镜数、机位、运镜、焦距、图稿和提示词均属于后续任务。本轮没有调用导演或镜头语言Skill。')
h('第一项Skill的测试结果')
p('本次可核查的成果是第一集项目理解、五名角色当前状态、两场原文与表达义务、资产及验证需求，以及带采用状态的导演交接。已读后续内容不倒灌为本集事件。原稿未修改；文件排版检查与源文覆盖核对另行完成，不将分析文字当成实际拍摄或生成成功。')
p('来源：用户提供的龙凤胎长出蛇尾前十集_208928.docx；第一集原始段落P021—P045。人物年龄等作者资料位于P010—P017，第一集婴儿当前年龄以本集满月事实优先。用户于2026年10月27日确认上述定位和制作范围。')

doc.core_properties.title='龙凤胎长出蛇尾 第一集项目剧本分析与导演本讨论稿'
doc.core_properties.subject='仅第一集 项目剧本分析V1.5实作'
doc.core_properties.author='项目制作讨论'
for st in doc.styles:
    for border in list(st.element.xpath('.//w:pBdr')):
        border.getparent().remove(border)
for par in doc.paragraphs:
    for border in list(par._p.xpath('.//w:pBdr')):
        border.getparent().remove(border)
doc.styles['Title'].font.underline=False
doc.styles['Subtitle'].font.italic=False
doc.save(out)
check=Document(out);full=[x.text for x in check.paragraphs]
for t in a[20:45]:
    if t.strip():assert t in full, f'Missing original paragraph: {t}'
assert hashlib.sha256(src.read_bytes()).hexdigest()==initial_hash
print(str(out))
print('First-episode source paragraphs preserved; original DOCX unchanged')
