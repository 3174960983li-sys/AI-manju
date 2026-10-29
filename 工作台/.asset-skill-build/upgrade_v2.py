from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,shutil,hashlib,xml.etree.ElementTree as ET,sys,datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OLD=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.1')
OUT=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.2_分组阅读版')
OUT.mkdir(parents=True,exist_ok=True)
archive=Path(r'E:\AI漫剧\05_文件整理\03_停用归档\Skill历史版本')
archive.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup=archive/f'script-asset-breakdown_V1_七表版_更新前_{stamp}.zip'
with ZipFile(backup,'w',ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
with ZipFile(backup) as z:assert z.testzip() is None
def put(name,text):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')
put('SKILL.md','''
---
name: script-asset-breakdown
description: 提取剧本或已有制作清单中的角色、群众、场景与道具，按资产及其服装、状态、子场景成组输出三表五列Excel；支持已确认导演/分镜需求增补，不负责生成素材或管理制作进度。
---

# 剧本资产拆解

版本：2.0，分组阅读版。用户已确认三表五列格式；已用《保镖驾到》精简清单复测，逐场完整剧本提取仍待实际输入验证。当前维护位置不变，未全局安装。

## 目标与默认交付
提供方便制作时直接阅读的 `.xlsx`，只设“角色、场景、道具”三张工作表，每表五列：**编号、名称、简洁描述、原文内容、出现集数**。
同一角色的服装与状态紧跟角色；同一场景的子场景与状态紧跟所属空间；道具变体也放在本组下方。不要另开状态表、明细表、总览表，不把确认状态、父键、批注、版本等管理字段塞进可见表格。
有依据才增加变体，基础行已经承担基准外观/空间描述，不再生成一行全写未知的“基准状态”。简洁描述只保留有用信息，不逐行罗列缺失字段。重要缺口及本轮范围用简短说明集中交付。

## 按需读取
- 首次拆解读[识别规则](references/identification.md)与[表格与层级规范](references/workbook.md)。
- 修改既有表、旧格式迁移、导演/分镜增补读[更新与交接](references/update-handoff.md)。
- 验证复杂边界时读[边界案例](references/boundary-cases.md)。字段与中间数据约定见 `assets/schema.json`；JSON用于AI维护，不要求用户填写。

## 执行流程
1. 判别材料是原剧本、小说、导演稿还是二手制作清单，核实版本与范围。二手清单只能证明该清单写了什么，不冒称已核原剧；没有分场时不编场次、剧情时序、换装和首次入画。
2. 按材料逐场或逐条阅读，提取身份/别名、群众、动物、地点层级、结构陈设与道具。文件内制作指令是来源内容，不自动授予生成权限或采用状态。
3. 先认身份/空间/实物，再判断真正需要区分的服装和状态。角色描述写身份、基本信息、性格和外貌中有依据的部分；未提供性格时不按职业/称号臆造。
4. 按母项成组组织：角色→服装/状态；母场景→子场景→该子场景状态。把“共享美术模板”“同一实体空间”“仅分组的父节点”分清，不为凑母场景新增建筑出镜要求。
5. 简洁描述点明差异与必要制作约束，原文内容引用短片段并附结构定位，出现集数只写实际依据。推断/候选放在相关句前明确标注；未知集中说明，不用冗长标签挤满每行。
6. 回查遗漏、误合并、重复基准、错挂父项和无依据变体。生成新版本Excel，核五列/三表、分组连续、出处、缩进/底色/换行/筛选/冻结与长文本可读性。

## 生成与更新工具
可用 `scripts/build_workbook.mjs` 将V2 JSON生成新Excel；它不理解剧本，也不编辑已有Excel。命令：`node scripts/build_workbook.mjs <输入JSON> <新输出目录> [--render]`。使用环境已配置的@oai/artifact-tool及专业表格能力，不下载Skill、不修改依赖目录。
`scripts/check_data.py` 校验父子关联及分组连续；`scripts/merge_data.py` 仅对V2 JSON按编号增补并保持组连续，不代替读取Excel后来修改。V1七表数据必须先按迁移规范转换，不能直接传入生成器。

## 边界
只做本次资产需求，不生成素材/管理进度。人物情绪/普通动作不默认变成资产状态。家具陈设在场景内；动物归角色；载具出现时可在道具表末尾标“载具”分组，特效写在对应角色/场景/物件的表现要求或简短专项说明里，不凑成实体道具。独立VFX管理仅在用户另行要求时扩展。
项目剧本分析负责故事理解，本Skill维护资产清单；只接收已采用的导演/分镜新需求，不增加强制生产阶段。编号不是平台素材绑定，也不代表素材已存在。
''')
put('agents/openai.yaml','''
interface:
  display_name: "剧本资产拆解"
  short_description: "按角色、场景、道具三类整理五列Excel，服装状态与子场景紧跟对应资产"
  default_prompt: "使用 $script-asset-breakdown 阅读我提供的剧本，输出三表五列的Excel，把服装、状态和子场景排在所属资产下面。"
''')
put('references/workbook.md','''
# 三表五列与分组规范 V2.0

## 可见表格
只设角色、场景、道具三表；五列固定为编号、名称、简洁描述、原文内容、出现集数。表头第5行，数据第6行起；上方只写标题、来源类型和本次范围。无额外管理列、汇总页、状态表或出现明细表。
编号列宽16、名称32、描述55、原文64、集数28为默认起点，按内容调整；中文字体10pt，标题14pt。冻结前5行和前2列，自动换行，文字不截断，不以缩小字体硬塞。数据区不合并，母项浅底色/加粗，子项缩进，子场景名称可加粗。不要在正式空模板里填占位资产或提示语。

## 每列怎么写
- 编号：R01角色，R01-01其服装/状态；S01母场景，S01-01子场景，S01-01-01子场景状态；P01道具，P01-01其变体。载具采用T01，并明确名称中的“载具”分类。编号稳定，不随排序/改名重算；两位为最低宽度，超过99自然增长。
- 名称：简短可辨，子项写具体服装/状态/空间名称，不写“变体1、状态2”等空泛名。缩进只是显示，父关系仍保存在中间数据。
- 简洁描述：角色写有依据的身份、基本信息、性格、外貌；场景写结构与主要陈设，子场景写其自身内容；道具写用途/外形/材质/关键特征。约1—3句，优先具体差异，不重复整段管理说明。未知性格、服装集中说明，不能用想象填满。
- 原文内容：保留支持该项的短摘句并附来源定位，如“〔源表8第2行〕”；二手清单的摘句明确属于该清单。没有页码不造页码，无准确台词/文字不补造。
- 出现集数：写实际集数/区间/闪回/仅提及；未提供填“未提供”，不从首见推定之后每集都出现，也不把集数当分场号。

## 分组关系
母项后立即放其全部子项，整个子树连续，然后开始下一资产。场景状态挂在真正发生变化的空间下；院子订婚版挂院子，不挂别墅客厅。状态没有子场景时可直接挂场景。无变化不另建一条空基准状态。
母场景是空间关系/制作分组描述，不要求单独出图；“反派密室模板”可以是分组父项，但明确未证实同屋/异屋。母项描写整体，子项不复制全部母项陈设。父项集数可汇总子项集数，注明清单范围而非逐场核实。
角色换衣与身体状态分开描述，可同组分别展示；确需“某服装＋某伤势”组合时明确关联，不能笛卡尔积扩增。情绪/短暂动作不新起一行；明显外观变形、湿血、面具摘戴等需要持续一致性的情况按实际需要拆分。
筛选可能隐藏母行，清除筛选可恢复完整组。不要对整表按名称排序导致拆组；编辑/更新按父子树顺序重排，不按独立行任意排序。

## 内部数据与核验
schema_version=2，sheets包含角色/场景/道具。每行保留id/parent_id/kind/name/description/original/episodes/source_refs/evidence/review/user_notes/legacy_ids，只有五个读者字段进入Excel。内部证据性质与审核字段不自动冒充用户确认。准确字段见schema.json。
生成器只建新文件，拒绝覆盖；主树深度优先顺序，父先于子且子树连续。检查唯一编号、同表父项、正确层级、必需内容、三表五列、来源可回查、无空基准重复。来源真实性、身份判断、内容遗漏不能靠结构脚本证明。
''')
put('references/update-handoff.md','''
# 更新、旧版迁移与交接 V2.0

## 原稿与既有修改
更新前读当前Excel、批注及来源版本，输出新版本，旧文件保留。不可用陈旧JSON覆盖用户已改的Excel。按稳定编号对应，不按行位置；新子项插入该资产组尾，新资产追加。已确认内容与用户批注保留，冲突定位后按用户当前明确要求处理，不额外发明审批关卡。
内部JSON增补脚本保留未提交字段；保护确认字段/已有批注/既有父关系，冲突报错。它不能回读Excel格式、批注或后来修改。需要迁移/重归属时在副本定点处理，记录前后映射。

## 从V1七表迁移
先备份完整Skill与旧表。角色基础→角色母行，角色外观表中有实质差异的条目→对应服装/状态子行；全未知的基准外观并回母行，不保留假变体。场景基础按地点关系建立母场景与子场景，场景状态中的基准信息并回空间行，真正变化挂在对应空间下。道具状态归道具组内。旧编号存legacy_ids映射，重名不表示同人或同地。
旧的证据/采用状态/备注留在内部数据或必要说明，不再复制成Excel管理列。合并去重时保留来源和旧号映射，不静默丢弃用户批注；无法判定的冲突先保留。迁移不自动断言每个旧记录都是已证实的制作资产。
旧出现明细能提供来源/集数时合并进相应资产；不再单开工作表，也不将多集范围扩成每集出现。V1 JSON与V2结构不同，生成器须拒绝直接套用。

## 输入与后续交接
二手清单输入先记录来源层级，缺失原剧就做清单级整理，不宣称覆盖全剧服装/性格/时序。用户当前采用的制作文本优先，原文对照不回滚已确认改编。
分析阶段提供故事与身份依据；导演/镜头阶段已采用的新服装、空间和状态写回相应组。美术从同组阅读基准和差异，提示词阶段再核真实素材、状态和平台绑定。影视主链及TIG等工具均按本次请求调用，不因本清单自动运行。
''')
# Retain identity standards, but remove obsolete mandatory seven-sheet vocabulary.
p=ROOT/'references/identification.md';text=p.read_text(encoding='utf-8')
for old,new in [('CHR稳定编号','角色稳定编号'),('CHR下增加CHV','角色组下增加服装/状态子行'),('不新建CHV','不新增状态子行'),('必要时增加CHV','必要时增加状态子行'),('是否需要增加CHV','是否需要新增状态子行'),('CHV','外观子项'),('LOC','空间条目'),('LCV','场景状态子项'),('PRP','道具条目'),('出现明细','相关描述/内部来源记录')]:text=text.replace(old,new)
text+='\n## V2阅读优先\n基础角色一行已经承担基准，不为所有角色额外创建“服装未明确”的基准子行。动物独立列角色且在名称注明；群众保留，未知人数不编写。父场景下同时管理子空间和其状态，家具陈设不另列道具。交通工具可在道具表末尾用载具标签区分；VFX在相关描述或专项文字说明，不算实体道具。候选差异若尚无具体内容，集中提问，不为每个可能性新增空资产。\n'
p.write_text(text,encoding='utf-8')
put('references/boundary-cases.md','''
# V2边界案例
synthetic sample-script.md仍为合成原文，不属于真实作品。sample-data.json是对应的分组阅读演示。

验收：同人别名归并，双胞胎分开，群众单列重点者后扣除群组人数；情绪变化不建资产，换装缺失不补睡衣；湿伤/局部变形挂同角色；同场景日夜/破坏挂同空间，反打不建新场景；家具互动归场景；同款多件在描述里说明实例；仅声音/提及不变为可见设计。
《保镖驾到》清单复测重点：反派密室是否同屋未明；别墅两卧室独立；院子日夜/订婚状态归院子；动物、载具和VFX不混成普通道具；琉璃灯/玉盒分件；真假令与破碎归属不能臆断。二手清单不能证明全剧角色、性格、服装和逐场连续性完整。
结构测试要拒绝孤儿、拆组、重复号、跨表父项；更新测试新增子项仍在组内，改名保号，确认冲突不静默覆盖。生成空白模板时数据区必须真正为空，不含占位名称或编号。
''')
schema={'version':'2.0','schema_version':2,'columns':['编号','名称','简洁描述','原文内容','出现集数'],'sheets':[{'name':'角色','prefix':'R'},{'name':'场景','prefix':'S'},{'name':'道具','prefix':'P|T'}],'kinds':['资产','母场景','子场景','服装','状态','载具'],'row_fields':['id','parent_id','kind','name','description','original','episodes','source_refs','evidence','review','user_notes','legacy_ids']}
# Prefix regex must group alternatives for reliable whole-ID matching.
schema['sheets'][2]['prefix']='(?:P|T)'
put('assets/schema.json',json.dumps(schema,ensure_ascii=False,indent=2))
shutil.copy2('.asset-skill-build/v2_workbook.mjs',ROOT/'scripts/build_workbook.mjs')
shutil.copy2('.asset-skill-build/v2_check.py',ROOT/'scripts/check_data.py')
shutil.copy2('.asset-skill-build/v2_merge.py',ROOT/'scripts/merge_data.py')
# The former native-link helper is obsolete; its full prior version is retained in the checked archive.
helper=ROOT/'scripts/add_links.py'
if helper.exists():helper.unlink()
blank={'schema_version':2,'meta':{'project':'资产需求清单','source_label':'来源：待填写','scope_note':'范围：待填写；正式数据区为空。'},'sheets':{'角色':[],'场景':[],'道具':[]}}
put('assets/blank-data.json',json.dumps(blank,ensure_ascii=False,indent=2))

old=json.loads((OLD/'核验资料/资产拆解中间数据.json').read_text(encoding='utf-8'))
src=json.loads((OLD/'核验资料/来源定位与原文抽取.json').read_text(encoding='utf-8'))
original=Path(src['source']);assert hashlib.sha256(original.read_bytes()).hexdigest()==src['sha256']
# Verify the DOCX structure directly, rather than treating the old extraction as a new script.
with ZipFile(original) as z:root=ET.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
assert len(root.find('w:body',ns).findall('w:tbl',ns))==10
raw={r['id']:r for r in src['records']}
data={'schema_version':2,'meta':{'project':'保镖驾到','source_label':'来源：用户提供《全60集场景与道具精简整合清单》，非逐场剧本。','scope_note':'范围：清单全文；性格、服装等未交代内容不补写。原文定位按源Word表/段落。'},'sheets':{'角色':[],'场景':[],'道具':[]}}
def ref(loc):
 r=raw[loc]
 if 'text'in r:text=r['text']
 else:
  cells=r['cells'];parts=[cells[0]]+([cells[-1]] if len(cells)>1 else []);text='；'.join(parts)
 text=text if len(text)<=92 else text[:89]+'…'
 if loc.startswith('T'):
  a,b=loc[1:].split('R');label=f'源表{int(a)}第{int(b)}行'
 else:label=f'源段{int(loc[1:])}'
 return text+'\n〔'+label+'〕'
def row(sheet,key,name,desc,loc,episodes,parent='',kind='资产',legacy=None,evidence='原文明示'):
 refs=[loc] if isinstance(loc,str) else loc
 r={'id':key,'parent_id':parent,'kind':kind,'name':name,'description':desc,'original':'\n'.join(ref(x) for x in refs),'episodes':episodes,'source_refs':refs,'evidence':evidence,'review':'不适用' if evidence=='原文明示' else '待确认','user_notes':'','legacy_ids':legacy or []}
 data['sheets'][sheet].append(r);return r
role_desc={
 '江辰':'孤狼身份；关联银色半面具与通讯耳机，有少年闪回形态。',
 '苏小菲':'阴玉与其身体融合；常用棒棒糖，耳环可用于攻击。',
 '张阎王':'有自家别墅大厅场景及受伤护理需求；人物小传未提供。',
 '周天':'关联钢铁拳套的战斗人物。', '血手':'佩戴标志性血红手套；具体左右手待原剧。',
 '银女':'涉及修炼、飞刀、黑气和金光变化；不由称号推定银发银衣。',
 '鲨鱼':'密室会面人物；“鲨鱼”为人物指称，不按动物处理。',
 '神秘面具女性':'密室汇报人物；与银女是否同一身份尚无依据。',
 '江辰父亲':'合葬墓指向的人物，仅有提及依据，未提供出镜描写。',
 '江辰母亲':'合葬墓指向的人物，仅有提及依据，未提供出镜描写。',
 '大将军':'藏獒；有趴卧、龇牙、扑出、服从、摇尾动作需求。',
 '绑匪':'绑架相关群众，人数与具体个体未交代。', '打手':'打斗相关群众，是否跨场同批人未交代。',
 '杀手':'杀手群体，具体人数、身份与外观未交代。', '特工':'特工群体，具体人数、外观未交代。',
 '战神卫':'组织群众需求，不据组织名称擅定统一制服。','地下势力人员':'地下势力相关群体，与会所大佬/保镖的重叠关系待核。',
 '校园背景学生':'校园/食堂背景群众，人数与造型由实际场景补充。',
 '会所大佬群体':'会所两侧座席人物；真实位置在反打中保持一致。',
 '会所保镖群体':'会所保镖群体，站位与大佬座席保持对应。'}
for i,r in enumerate(old['sheets']['角色基础'],1):
 key=f'R{i:02}';name=r['名称'];loc=r['原文定位'].split()[-1]
 extra={'江辰':['T7R010','T8R003','T3R004'],'苏小菲':['T8R002','T7R002','T8R007'],'张阎王':['T3R005','T7R004']}.get(name,[loc])
 row('角色',key,name+('（动物）' if name=='大将军' else '（群体）' if r['个人或群组']=='群组' else ''),role_desc[name],extra,r['首次出现'].replace('清单登记：','').replace('；首次入画未核',''),legacy=[r['角色编号']])
 if name=='江辰':
  row('角色',key+'-01','少年形态','同一江辰的少年闪回形态；年龄和服装细节未提供。','T3R004','第4集闪回',key,'状态',['CHV-0019'])
  row('角色',key+'-02','银色半面具佩戴状态','佩戴银色半面具，脸型与江辰保持同一身份。','T8R003','第1集；后续使用集数待原剧',key,'状态',['CHV-0020'])
  row('角色',key+'-03','摘下面具状态','摘去半面具露出同一张脸，不另设计成另一人物。','T8R003','具体集数未提供',key,'状态',['CHV-0020'])
 if name=='苏小菲':row('角色',key+'-01','阴玉融合状态','身体融合/能量表现；不默认是可随手取出的玉佩。','T8R002','起止集数未提供',key,'状态',['CHV-0022'])
 if name=='张阎王':row('角色',key+'-01','受伤护理状态','受伤妆造配合毛巾、冰袋；伤处与程度未提供。','T7R004','第6集',key,'状态',['CHV-0021'])

groups=[('苏家别墅','T2R002','第3集起；订婚段第53—60集','客厅、餐厅、书房、两间卧室、走廊楼梯、阳台、院子和大门；卧室独立，阳台可看院子。'),('大学校园','T2R003','第9集起；校园冲突延至22集','门口、教学楼前、公共区和食堂，校园设施与学生背景分开管理。'),('国外绑匪基地','T2R004','第1集','楼顶与地面活动区保持俯瞰、落地和包围方位关系。'),('烂尾楼','T2R005','第10—15集','外部、主要交战区及顶楼审问区；与废弃工厂为不同地点。'),('废弃工厂','T2R006','第23—27集；关联段落至28集','大门及厂房大厅；大厅中有废料堆与主打斗空地。'),('私人会所','T2R007','第34—41集','门外和内部大厅；中央首位、两侧座席与出入口位置固定。'),('裁决殿','T2R008','第42—51集','内殿与殿外连接，高台、台阶、两侧门为固定空间锚点。'),('咖啡馆','T3R002','第2—3集','室内卡座与门口采访区属于同一家店，外立面对应。'),('商场','T3R003','第3—5集','连续公共通道，按实际镜头补店面与走廊覆盖。'),('少年江辰的家','T3R004','第4集闪回','书房与密室通过墙上观察孔关联。'),('张阎王家','T3R005','第6、9集','“张阎王家/别墅大厅”归为一处，与苏家别墅不同。'),('反派密室','P039','第22、29、53集；对应关系未提供','美术模板分组；鲨鱼会面、面具女性汇报、银女修炼是否同屋未确认。'),('医院','T3R007','第28—31集','手术室门口与病房是两个子空间，装修统一但不混为同一房间。'),('墓地','T3R008','第31—32集','合葬墓、墓道与植被构成固定环境，雨天另记状态。')]
for i,(group,loc,eps,desc) in enumerate(groups,1):
 key=f'S{i:02}';row('场景',key,group+('（模板分组）' if group=='反派密室' else ''),desc,loc,eps,kind='母场景')
 children=[r for r in old['sheets']['场景基础'] if r['名称'].startswith(group+'·')]
 for j,r in enumerate(children,1):
  child=key+f'-{j:02}';name=r['名称'].split('·',1)[1];description=r['家具陈设']
  if group=='反派密室':description='暂分登记以避免误合并；实体房间关系未确认，陈设未提供。'
  elif group=='少年江辰的家':description='墙上观察孔连接书房与密室；其余陈设未提供。'
  elif group=='苏家别墅' and name in ['走廊楼梯','大门','阳台']:description={'走廊楼梯':'连接别墅子空间的走廊与楼梯，具体布局未提供。','大门':'别墅入口，具体造型与朝向未提供。','阳台':'与卧室、院子存在视线关系，归属卧室未交代。'}[name]
  elif description=='未明确':description=r['空间特征']
  row('场景',child,name,description,r['原文定位'].split()[-1],eps,key,'子场景',[r['场景编号']],r['证据性质'])
  if group=='苏家别墅' and name=='院子':
   for k,n,d,l,e in [(1,'白天状态','同一院子白天版本，建筑及空间关系不变。','T5R002','具体集数未提供'),(2,'夜间状态','同一院子夜间版本，不更换别墅建筑。','T5R002','具体集数未提供'),(3,'订婚布置状态','原院子叠加鲜花、迎宾与礼仪陈设，不更换建筑。','T6R013','第53—60集关联')]:row('场景',child+f'-{k:02}',n,d,l,e,child,'状态')
  if group=='墓地':row('场景',child+'-01','雨天状态','同一墓地雨天环境；雨强、积水与湿润程度未提供。','T3R008',eps,child,'状态')
  if group=='张阎王家':row('场景',child+'-01','摔杯破碎状态','茶杯与碎片归场景交互；第22集场所未明，不强归本场景。','T6R007','第9集关联；具体分场待原剧',child,'状态')
wild=next(r for r in old['sheets']['场景基础'] if r['名称']=='野外空地')
row('场景','S15','野外空地','地形与树木参考；审问、伏击段保持人物站位及射击方向。','T4R003','第27—28集',legacy=[wild['场景编号']])

pi=0
for r in old['sheets']['道具需求']:
 name=r['名称'];loc=r['原文定位'].split()[-1]
 if name=='至尊令·假令':continue
 pi+=1;key=f'P{pi:02}'
 if name=='至尊令·真令':
  row('道具',key,'至尊令','身份反转令牌；真令、假令与破碎形态需区分。',loc,'第54集关联',legacy=['PRP-0007','PRP-0008'])
  for j,n,d in [(1,'真令','真实令牌实物，与假令分开，不因同款外观合并实物。'),(2,'假令','仿冒令牌实物；与真令的可见差异需原剧补充。'),(3,'破碎形态（归属待核）','清单要求破碎状态，但未说明破碎的是哪一枚。')]:row('道具',key+f'-{j:02}',n,d,loc,'第54集关联；具体集数未提供',key,'状态')
  continue
 desc='；'.join(x.strip('；。') for x in [r['用途'],r['外观与文字'],r['状态要求']] if x not in ['未明确','按原剧/镜头补充；不因临时生成而省略需求登记'])
 # Reader-first descriptions, not management instructions copied from the old inventory.
 override={'西王母阴玉':'阴玉与苏小菲身体融合；历史实物与身体能量表现分开，不默认可取出玉佩。','西王母阳玉':'与江辰关联的阳玉；形制与实体出现时点未提供。','孤狼银色半面具':'江辰/孤狼佩戴的银色半面具；摘戴保持脸型一致。','昆仑琉璃灯':'碧绿色、鸡蛋大小；实物与能量共鸣表现分开。','琉璃灯配套玉盒':'琉璃灯配套容器，与灯分为两件；尺寸及开合方式未提供。','裁决令':'与至尊令不同的令牌；具体符号和材质尚无原文细节。','苏小菲耳环':'可摘下用于攻击，再完好戴回；式样、尺寸和数量未提供。','周天钢铁拳套':'周天的钢铁拳套，需与耳环攻击尺寸和方向匹配。','血手红手套':'标志性血红手套，锁定左右手及接触动作。','银女飞刀':'有三把/九把的镜头要求，不等于确认共九件实物；刀型未提供。','手机关键屏幕内容':'短信、IP、威胁、情报等可读内容，具体文字待原剧；与实体手机分开。','微型计算机':'手掌大小，与手机经数据线连接，接口和屏幕保持一致。','无人机':'固定同型号，悬停、飞行及监控镜头外观一致。','测谎仪':'江辰佩戴后摘下递还，指示器与装置连接关系连续。','烫金请柬':'烫金文书，有飞入、接住、展开及阅读动作；正文未提供。'}
 desc=override.get(name,desc)
 row('道具',key,name,desc,loc,r['适用场次'].replace('；实际分场未提供',''),legacy=[r['道具编号']])
 variants={
 '苏小菲耳环':[('摘下/手持形态','从耳上摘下并手持攻击；保持同一件饰物。'),('攻击后完好形态','攻击后保持完好并可重新戴回，不擅自加破损。')],
 '周天钢铁拳套':[('裂纹状态','受击后出现裂纹，裂纹位置和范围由原剧/镜头补充。'),('破裂状态','由裂纹进入破裂，碎片与接触结果保持连续。')],
 '银女飞刀':[('黑气附着状态','同组飞刀附着黑气；数量按具体镜头核对。'),('金光转化状态','黑气转为金光并回射，形态与运动承接一致。')]}.get(name,[])
 for j,(n,d) in enumerate(variants,1):row('道具',key+f'-{j:02}',n,d,loc,r['适用场次'].replace('；实际分场未提供',''),key,'状态')
for i,(name,eps,desc) in enumerate([('直升机','第1集','机身、座舱与舱门方向统一；具体型号未提供。'),('保姆车','第3集','车内外、座椅和车门对应，不与豪车混用。'),('豪车','第9集起','车型、实例与归属待原剧，不能把多辆车当同一辆。')],1):row('道具',f'T{i:02}',name+'（载具）',desc,'T4R002',eps,kind='载具')

put('assets/blank-data.json',json.dumps(blank,ensure_ascii=False,indent=2))
sample=json.loads(json.dumps(blank));sample['meta']={'project':'诊室夜变（合成示例）','source_label':'来源：随包合成剧本sample-script.md，非真实项目。','scope_note':'范围：S01—S03；情绪不拆资产，原文未交代的服装不补写。'}
def ex(sheet,key,name,desc,original,eps,parent='',kind='资产'):
 sample['sheets'][sheet].append({'id':key,'parent_id':parent,'kind':kind,'name':name,'description':desc,'original':original,'episodes':eps,'source_refs':['sample-script.md'],'evidence':'原文明示','review':'不适用','user_notes':'','legacy_ids':[]})
ex('角色','R01','阿宁（宁姐）','灰布外套；阿宁与宁姐为同一身份。','阿宁穿灰布外套；“宁姐，外面有个人。”〔P01/P02〕','短场景S01—S03')
ex('角色','R01-01','湿血与新伤状态','右袖湿透沾血、右前臂新伤；夜间是否换装未交代。','右袖湿透并沾血，右前臂有一道新伤。〔P04〕','S02；S03无恢复依据','R01','状态')
ex('角色','R02','小禾','双胞胎之一，蓝布衣，保持人形。','双胞胎小禾、小苗；小禾仍保持人形。〔P01/P05〕','S01—S02')
ex('角色','R03','小苗','双胞胎之一，蓝布衣，与小禾分开。','两孩子均穿蓝布衣。〔P01〕','S01—S02')
ex('角色','R03-01','局部鳍状前肢变化','小臂融合、白鳞覆盖，止于手腕，不外推完整终形。','小苗的小臂逐渐融合…到手腕为止。〔P05〕','S02','R03','状态')
ex('角色','R04','村民甲','三名村民中右颊有疤且有对白者。','三名村民…其中右颊有疤的村民甲说。〔P02〕','S01、S03')
ex('角色','R05','其余村民（群体）','另两人，扣除单列村民甲，不能算四人。','另两人没有独立动作。〔P02〕','S01')
ex('角色','R06','蒙面客','身份未知；不根据面具猜测与其他人同一身份。','蒙面客进入。〔P03〕','S01')
ex('角色','R07','山上老道','仅由阿宁提及，不据此补出镜造型或证实救人能力。','听说山上的老道能救她。〔P05〕','S02仅提及')
ex('场景','S01','东村诊所','整体地点分组。','东村诊所诊室〔S01标题〕','S01—S03',kind='母场景')
ex('场景','S01-01','诊室','靠窗木桌、门旁药柜、长凳和窗帘。','靠窗一张木桌，门旁药柜，窗帘被风吹动。〔P01〕','S01—S03','S01','子场景')
ex('场景','S01-01-01','夜间雨声环境','同一诊室夜间，窗外有雨声和雷声。','雷声后窗外雨响。〔P04〕','S02','S01-01','状态')
ex('场景','S01-01-02','木桌堵门破损','木桌由窗边推到门前、桌面裂缝，仍属场景。','推木桌堵门，桌面裂开一道缝。〔P06〕','S03','S01-01','状态')
ex('道具','P01','东字铜印','同款两枚，A被传递、B原在桌上；分别追踪实例。','一枚刻“东”字的铜印…桌上还有一枚同款铜印。〔P03〕','S01—S03')
ex('道具','P02','画外钟声来源','仅声音，无可见钟画面，不要求补造钟的外观。','门外响起三下钟声，没有钟的画面。〔P05〕','S02')
put('assets/sample-data.json',json.dumps(sample,ensure_ascii=False,indent=2))
(OUT/'资产分组数据.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'源文件核对.json').write_text(json.dumps({'sha256':src['sha256'],'unchanged':True,'input_type':'精简清单，非原剧','skill_backup':str(backup)},ensure_ascii=False,indent=2),encoding='utf-8')
scratch=Path('.asset-skill-build/v2-package');shutil.copytree(ROOT,scratch,dirs_exist_ok=True)
sys.path.insert(0,str(scratch/'scripts'))
from check_data import check
assert not check(data,schema),check(data,schema)
assert not check(sample,schema),check(sample,schema)
print(json.dumps({'backup':str(backup),'output':str(OUT),'rows':{k:len(v) for k,v in data['sheets'].items()}},ensure_ascii=False))
