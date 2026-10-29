from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,shutil,uuid,sys
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
BASE=Path(__file__).parent
archive=Path(r'E:\AI漫剧\05_文件整理\03_停用归档\Skill历史版本')
archive.mkdir(parents=True,exist_ok=True)
backup=archive/('script-asset-breakdown_V2_更新前_2026-10-28_'+uuid.uuid4().hex[:8]+'.zip')
with ZipFile(backup,'w',ZIP_DEFLATED)as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and '__pycache__'not in p.parts:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
with ZipFile(backup)as z:assert z.testzip()is None
def put(name,text):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')
put('SKILL.md','''
---
name: script-asset-breakdown
description: 从剧本、小传及已确认制作方案拆解角色、服装、身体状态、母子场景与道具，逐集追踪出现、保留相关完整原文，输出三表五列且原文可折叠的Excel。用于资产准备及既有清单增补，不生成媒体或管理制作进度。
---

# 剧本资产拆解

V3.0，2026-10-28。完整信息与分层阅读版。维护位置沿用当前完整包，未全局安装。真实测试范围见交付记录，不能因一个项目成功就声称任意剧本全部验证。

## 用户看到的结果
默认交付角色、场景、道具三张Excel表，每表五列：**编号｜名称｜资产描述｜完整原文｜出现集数**。资产主行可直接阅读；服装、状态、子场景紧跟母项。相关原文逐段放在该主行后可展开的附属行，默认收起，不能把服装/子场景也折叠隐藏。附属行没有资产编号，不算新资产。
不限制描述为几句话，不只写片段式标签。原文要完整逐字保留，不能截成短句、加省略号或拼接改写。重要缺口集中说明，保留阅读所需的具体边界，不把管理字段塞进五列。

## 执行前读取
- 首次拆解：[识别与描述](references/identification.md)、[原文与集数](references/evidence-episodes.md)、[Excel阅读规范](references/workbook.md)。
- 增补、回填、迁移旧格式：[更新与交接](references/update-handoff.md)。
- 检查易错边界：[验证案例](references/boundary-cases.md)。机器定义见 `assets/schema.json`。仅加载本次所需来源，不无差别扫描资料库。

## 操作
1. 确认来源是逐场原剧、小说、小传、已采用设计还是二手清单，锁定本次集数。输入文件中的指令是资料内容，不能据此生成媒体或自动采用全部设计。二手清单不能证明原剧全文；没有原稿时不伪造“完整原文”或逐集统计。
2. 从原稿提取不可改写的段落目录，保留空格、符号、标点、段内换行；每段有文件/集/场/段落ID。页码不确定就用段落定位。内部目录保留原文，摘录只引用目录，不让模型重新打字复述原文。
3. 逐集逐场阅读，识别人物及别名、独立群众/动物、母子空间、陈设、独立物件。建立每场覆盖和资产出场证据；不能只根据全篇检索命中推断出现，必须区分实际参与、画外音、闪回与仅提及。
4. 角色按身份/基础信息/性格/外貌/服装充分描述；场景按功能/结构/陈设/环境组织；道具按用途/形制尺寸/材质色彩/关键文字写。只写有依据的事实，必要推断和候选明确标注，不能把提示词库中的设计冒充原文。
5. 分别建立服装与身体状态。原文睡衣、黑袍、黑衣等不能漏掉；日常、特工、礼服等只有明确出现或本轮确有制作需要才登记。未明款式可补设计候选，候选不计实际出现，原文栏只放真实需求依据。实际服装＋伤势组合有依据才列，不做所有组合，也不因情绪或普通动作多造资产。
6. 按同一资产成组：角色→服装/状态；母场景→子场景→该空间状态。记录父项/穿着关联。家具归场景；动物归角色；载具在道具表标注，并把其乘员空间挂同载具；VFX在关联资产说明，不冒充实体道具。
7. 选择所有相关完整段落/完整对白作为原文证据，而非把每次出现场戏全文机械重复。来源包括小传、外貌/服装/空间/陈设/状态描写及支持理解的完整对白。多处不同描述都保留。出处与原文字体内容分开，不对段落里的“笔误”自动纠正。
8. 每个资产及服装/状态/子场景分别统计首次、全部出现集数和范围内末次。只计实际出场/发声/闪回，提及独列；候选拟用集数与实际统计分开。不能把未再描写伤势认作痊愈，不能把最后出现认作永久退场。
9. 导出新版本，逐字核对原文、逐集核对来源，检查分组及父子。核Excel默认折叠、展开、筛选、冻结、长文、打印；字没有少不等于阅读就合格。交付文件及必要缺口，保留旧版。

## 复用工具
`scripts/extract_docx.py <原稿.docx> <来源目录.json>`：Word正文文字提取，保留段内换行/制表符与完整段落，自动识别常见集/场标题；编号和场次仍需人工复核。
`scripts/check_data.py <V3数据.json>`：检查分组、来源与逐集证据，不代替身份/遗漏的语义审查。
`node scripts/build_workbook.mjs <V3数据.json> <新输出目录> [--render]`：用已配置@oai/artifact-tool创建三表，原生折叠/筛选/打印由Python标准库补齐。通过ASSET_PYTHON指定环境运行时；无新依赖下载。只创建新表，不编辑现有Excel。--render为主行示意，实际折叠/打印仍应在Excel核验。
`scripts/merge_data.py`只按稳定编号增补内部数据，不回读Excel后来修改。更新已有Excel必须先读取当前文件，不可用陈旧JSON覆盖用户批注或采纳内容。

## 流程位置
项目剧本分析提供理解和证据，本Skill负责资产细化；只把已采用导演/分镜需求回填，不新增强制阶段，不自动调用下游。资产编号不等于真实素材或平台绑定。当前范围之外的小传人物可登记“未出场”，不能为其虚构本轮服装和出场。
''')
put('references/identification.md','''
# 识别与充分描述 V3

## 身份与层次
身份不按名字数量拆。本名/昵称/明确马甲归同人；双胞胎、替身、同名者分别识别。没有同人证据的黑袍人、面具女性或组织人物不能凭题材猜身份。人物表与正文都读，名单省略但有对白或动作的角色也要登记。
群众以实际场景/群体组织。独立对白/关键动作的人单列或挂群体成员；总量与成员不能重复相加。跨时间打手不默认同一批。组织名称不等于出现了一批穿制服的人。动物是角色，普通动作不拆多个身份。

## 服装不等于身体状态
先认衣物，再认穿着时的身体/妆发/物理状态。日常服、行动服、礼服、睡衣、制服、黑袍等是不同衣着需求；伤口、红肿、湿透、血污、衰老、变形是不同维度。只出现面具摘戴不代表已经提取了全部服装。
明确穿睡衣就记录睡衣，包括领口扣子等已写结构；未写颜色、材质和长短不能补成事实。未写换装不推定换装；连续段可有必要继承推断，但说明依据。情绪、笑、转头等不建立资产变体。一次性结构改变也可能需要变化设计，不能因不持续而忽略。
衣着未写且制作需要时，提出少量有目的的候选：具体款式与适用任务写清楚，名字标“设计候选”。候选原文行只允许真实需求依据，并明确那不是服装描写；拟适用集数不作已出现。候选未采纳，不挂成已证实服装下面的身体状态。范围没有宴会/正式场合时，不为凑“礼服”名目强造需求。
实际服装和伤势组合必须有依据才挂载；状态可挂角色或对应服装；不做服装×年龄×伤势全部组合。

## 描述必须足够支撑制作
角色：身份/人物关系与任务；年龄等基本信息；小传明确性格与正文行为表现分清；外貌辨识点；服装/配件已写特征。原文没有发色五官就不按称号、国籍、阶级填完整形象。缺项不靠提示词库“补成原文”，也不把人物骂人台词当客观外貌。
场景：叙事/使用功能；空间分区、出入口、连通和视线关系；主要家具陈设、固定锚点；时间/天气/光照与物理变化。母项说整体、子项说自身。未写尺寸布局可标设计缺口，但不能只留“某某场景”三个字。
道具：谁使用/为何重要；外形、尺寸、材质、颜色中明确部分；可读文字逐字保留；数量与实物实例；初末态及与手/空间接触。颜色不等于材质，银色面具不自动是纯银。
描述用分项换行，不受固定句数限制。未知集中说明，同时保留影响制作判断的具体缺口。事实/推断/候选在相关句中区分，不用额外管理列淹没读者。

## 场景与物件
母场景→实际子空间→具体状态。同房间反打不变新场景，不同房间不因同栋建筑合并一张图；同审美模板不等于同屋。院子订婚/夜战状态挂院子，不挂客厅。
源标题“卧室和阳台”要结合正文辨认内外空间；源标题室内也可能含看院子、走到院外的可见段落，不能只按标题漏子空间。未确认两个室内区同屋时可暂分或作为制作整合建议，明确不把建议冒充原文几何。
家具、门窗、固定设施和普通场景餐具归场景。茶杯破碎按所属空间状态记录；有独立关键交互的小物另列。灯与容器分件，真/假令分实物，状态不等于另一件物体。载具的内外结构与乘员区域要对应，不把换车当场景状态。
''')
put('references/evidence-episodes.md','''
# 完整原文与逐集追踪

## 原文单元
输入Word用正文顺序生成段落ID，保存原字词、标点、▲符号、空格、段内换行和制表符。不Unicode归一化、不纠错、不删括号、不加省略号；来源段落是不可变目录。图片中的文字/OCR另标未核，不能当作逐字已验证。
资产只保存关联段落ID，从目录原样写出。收录相关的小传段、外貌/服装/空间/陈设/状态完整段落和支持判断的完整对白，多处描述都保留，不用一句概括替代原文。不是每次出现都复制整场全部无关对白；覆盖判断要回查所有场次。
一个段落涉及多人或多件物品，可以被不同资产完整引用，不能为了只留名字切碎段落。候选需求引用的真实段落需在出处区标“需求依据，非服装外观原文”。出处写文件、集数、场次、段落ID，放C列；D列只有原文，不插任何自制标签。
超长段落分到连续原文行/单元格，保留每部分边界索引；按顺序拼回必须逐字符等于来源，不插拼接换行。原段内换行仍保留。不得为了视觉整齐合并段落、截尾或固定最大字数。
源内容以等号等特殊字符开头时，必须保留文字数据类型，不通过新增可见字符逃避公式解析；导出后比对真实单元格值，不能只看屏幕显示。

## 出场记录
每个记录有集数、场次、出场方式和来源段落。现场参与、明确VO、闪回属于出场；仅被提到与小传/大纲不属于本轮出场。人物表、动作、对白与指代结合核对，不能全文搜到名字就计出场。
手机只通电话但设备未写明时，区分相关通话和明确手机入画；第7集江辰叫老高找人，不意味着老高发声；第10集结尾江辰VO不是又多一个“影”角色。不同载具/群体不能因同类型混成同一实例。
资产的衣服/状态/子场景独立统计，母项可以取实有子项并集，候选拟用不能传播进母项实际记录。仅提及日期独列。

## 五列中的集数单元格
首次：第X集\n出现：第X、Y—Z集\n末次：第Z集〔范围内〕
必要时另起“画外音：…”“闪回：…”“仅提及：…”。未出现写“首次／末次：本范围未出场”，仅小传者补“仅小传／大纲登记”。候选写“设计候选，未作为实际出现统计；拟适用…”，没有虚构首次末次。
首末仅限已读范围，不等于出生/死亡/全剧结束。未再描写伤势不等于恢复；最后一次明确受伤状态与其可能延续分开说明。不要把母场景第3集起扩成每个房间之后每集都出现。
''')
put('references/workbook.md','''
# 五列与可展开原文的排版

三表：角色、场景、道具。五列：编号/名称/资产描述/完整原文/出现集数。正文11pt、标题15pt，中文可读字体。起始列宽14/28/58/66/30，按渲染检查调整。冻结前5行和前2列；正文左上对齐、分项换行，数据区不合并。不要把来源/状态/确认等管理字段另开十几列。

## 每项的物理行
1. 资产主行：编号、缩进名称、充分描述、展开提示、首末/全部集数。基础/母项浅蓝底和粗体，子项通过缩进与适度加粗区分，细分隔线即可。
2. 紧接该主行的原文附属行：A空白，不分资产号；B标段落ID/分段序号；C写来源文件/集/场/段落定位，候选标明需求依据；D保留该段原字；E注明该段所属集或小传。多段逐段放，不塞进一个巨格。
3. 只把这些原文附属行原生分组并默认收起，主行作为上方摘要行。服装、状态、子场景主行不能被隐藏。所有原文块用独立的同级outline组，不能按资产树把子资产也折叠掉。无原文的空模板不产生假编号和假分组。

母项及所有子项保持连续，原文块插在各项之后。重排按树遍历，不能随意全表按名称排序拆组。筛选可能隐藏附属行，阅读原文前先清除筛选；不要承诺任意过滤后都能自动保留整组。

## 原文与行高
原文可展开后复制，且C来源信息与D原文字不混合。自动换行与行高按内容计算，不设截尾。超过Excel行高/单元格上限时拆成连续部分，索引记录part/parts，拼接逐字不变。源以等号等字符开头时也保持原文字面值，不能变成公式或多一个引号。
默认列宽只是起点，检查完整角色组、服装和一个多子空间场景后再完成全表；不可只凭导出成功宣布版式通过。--render输出是主行示意，实际默认折叠需要Excel检查。

## 打印
默认A3横向、宽1页高自动、重复顶部1—5行，窄页边距和页码。默认收起原文时打印主项，展开后原文参与打印。用户指定A4等时另按纸张调整，不能缩到不可读。核验打印导出的PDF与页面尺寸/内容，PDF渲染是文档核验，不是生成故事板或媒体。

## 内部接口
schema_version=3；assets包含三类树序数组；source_records存不可变完整段落；source_ids引用来源；events逐条指向episode/scene/mode/source_id，附candidate/planned_episodes/outfit_id。source ID多文件时使用文件/版本命名空间，不能把不同版本P001误合并。布局索引记录每个主行及原文片段行，供字符核验和原生折叠补齐。
脚本只创建新Excel，原生outline/筛选/打印设置由标准库XML补齐，不改变来源文字。不能把所有物理行数当资产数。资产计数排除原文行、候选可单列，不直接当出图数量。
''')
put('references/update-handoff.md','''
# V3更新与交接

先读用户当前Excel及批注/采用信息，另存新版本，保留旧版。稳定编号与父关系尽量复用；更改归属需保留前后映射。不要用旧JSON重新生成覆盖用户在Excel里的后来修改。候选采纳需依据用户明确采用记录，不由脚本标成已采用。

## V2迁移
V2短摘句不能“自动恢复”完整原文；集数范围也不能还原每一集出现。必须回原稿提取段落并逐集核对。已有描述可作待核线索，删除空基准重复不能删除真实衣着或有效批注。
拆出实际服装与身体状态，保留所属角色/穿着关联，必要子空间重新挂载，记录旧新编号。源范围变小，不把范围外资产宣布不存在或删除旧稿；明确本轮不纳入。只有小传的未来角色可登记未出场，不补出本轮服装。

## 内部增补
V3源目录不可悄悄改字，同ID同版本正文不同应报冲突；新版本/文件换来源命名空间。新增子项插到本组结尾，不散落到表尾。merge_data.py仅合并V3内部数据，保留未提交字段、已有批注与确认内容；冲突拒绝静默覆盖。它不是Excel编辑器，也不验证自然语言判断。

分析提供身份与故事证据；本Skill资产细化；已采用导演/镜头需求才回填，不自动运行下游。美术从同组读基础、服装与状态；提示词阶段再核真实素材、平台绑定和当前首末态。本清单不代表素材已制作或平台效果已验证。
''')
put('references/boundary-cases.md','''
# V3核验案例

真实复测使用《保镖驾到》原剧1—10集＋小传，不能把60集精简清单和角色提示词当原稿。
- 睡衣：第7—8集明确，胸前扣子、次晨未换应提取；黑衣右手红手套第9—10集、黑袍闪回第4集也不能漏。
- 衣着候选：江辰特工/日常服等有任务依据但无款式原文，标候选，拟用不计实际集数；礼服不因未来订婚而塞进本轮。
- 老高：第1集VO，第7集仅被江辰叫名字打电话，没有老高回应，不能计再次发声。
- 江辰多身份/少年同一人；父母在第4集闪回确实出现，不能沿用旧清单把他们仅记为墓碑提及。
- 张阎王第5集掉两颗牙，第6集红肿冷敷；艾薇第10集胸口受伤但未写血和死，不能加造型事实。
- 第9集短信原文“血手来B市了。”逐字保留；第1集攻击光影载体不明，不能借后文硬币/匕首倒填。
- 卧室/阳台/院子、母场景功能与真实视线分别挂载；第8集院子整洁是明确状态，不自动补清理工出镜。
- 全部完整段落拼接与原稿目录逐字相等；出处标签不混进原文；多行段落保留换行。测试超长段落和以等号开头的原文。
- 原文行默认隐藏且可展开，下一服装/子空间仍可见；三表五列、冻结、筛选与原生打印核验。
随包合成示例只用于结构与边界演示，不是另一真实作品，也不替代实际原剧语义审查。
''')
put('agents/openai.yaml','''
interface:
  display_name: "剧本资产拆解"
  short_description: "完整提取服装与状态、逐集追踪出场，生成原文可展开的三表五列Excel"
  default_prompt: "使用 $script-asset-breakdown 分析我提供的剧本及小传，充分描述资产，逐字保留相关完整原文，并输出服装、状态、子场景同组的Excel。"
''')
schema={'schema_version':3,'columns':['编号','名称','资产描述','完整原文','出现集数'],'sheets':['角色','场景','道具'],'paragraph_fields':['id','text','episode','scene'],'node_fields':['id','name','description','parent_id','kind','source_ids','events','candidate','planned_episodes','outfit_id','review','user_notes'],'event_fields':['episode','scene','mode','source_id','inferred'],'event_modes':['现场','画外音','闪回','仅提及'],'source_contract':'原文目录不可改写；V2短摘不构成V3来源；多文件/版本ID需命名空间','scope_contract':'实际出场与候选拟用、仅提及分开，首末只限本轮'}
put('assets/schema.json',json.dumps(schema,ensure_ascii=False,indent=2))
for f in ['build_workbook.mjs','check_data.py','patch_layout.py']:shutil.copy2(BASE/f,ROOT/'scripts'/f)

extract='''from pathlib import Path
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
   elif k=='tab':parts.append('\\t')
   elif k in ['br','cr']:parts.append('\\n')
  text=''.join(parts);m=re.fullmatch('第([零〇一二两三四五六七八九十百0-9]+)集',text.strip())
  if m:episode=cn(m[1]);scene=None
  m=re.match(r'^(\\d+-\\d+)\\s+',text.strip())
  if m:scene=m[1]
  records.append({'id':f'P{i:03}','text':text,'episode':episode,'scene':scene})
 return {'file':str(path),'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':records}
if __name__=='__main__':
 out=Path(sys.argv[2])
 if out.exists():raise SystemExit('拒绝覆盖已有来源目录')
 out.write_text(json.dumps(extract(sys.argv[1]),ensure_ascii=False,indent=2),encoding='utf-8')
'''
put('scripts/extract_docx.py',extract)
merge='''import json,copy,sys
from pathlib import Path
from check_data import check
def merge(old,delta):
 if old.get('schema_version')!=3 or delta.get('schema_version',3)!=3:raise ValueError('需要V3；不能将短摘自动升级')
 out=copy.deepcopy(old);catalog={p['id']:p for p in out['source_records']}
 for p in delta.get('source_records',[]):
  if p['id']in catalog:
   if p!=catalog[p['id']]:raise ValueError('原文目录冲突：'+p['id'])
  else:out['source_records'].append(copy.deepcopy(p));catalog[p['id']]=p
 for sheet,patches in delta.get('assets',{}).items():
  if sheet not in out['assets']:raise ValueError('未知分类')
  rows=out['assets'][sheet];seen=set()
  for patch in patches:
   key=patch['id']
   if key in seen:raise ValueError('增补重复号')
   seen.add(key);current=next((r for r in rows if r['id']==key),None)
   if current:
    for k,v in patch.items():
     if current.get(k)==v:continue
     if k in ['id','parent_id','review','candidate'] or k=='user_notes' and current.get(k) or current.get('review')=='已确认':raise ValueError('受保护内容冲突：'+key+' '+k)
     current[k]=copy.deepcopy(v)
   else:
    parent=patch.get('parent_id','')
    if not parent:rows.append(copy.deepcopy(patch));continue
    at=next((i for i,r in enumerate(rows)if r['id']==parent),None)
    if at is None:raise ValueError('缺少父项')
    at+=1
    while at<len(rows)and rows[at]['id'].startswith(parent+'-'):at+=1
    rows.insert(at,copy.deepcopy(patch))
 errors=check(out)
 if errors:raise ValueError('\\n'.join(errors))
 return out
if __name__=='__main__':
 a,b,c=map(Path,sys.argv[1:4])
 if c.exists():raise SystemExit('拒绝覆盖输出')
 c.write_text(json.dumps(merge(json.loads(a.read_text(encoding='utf-8-sig')),json.loads(b.read_text(encoding='utf-8-sig'))),ensure_ascii=False,indent=2),encoding='utf-8')
'''
put('scripts/merge_data.py',merge)
blank={'schema_version':3,'meta':{'project':'资产需求清单','scope':[1,10],'source_name':'待填写来源','source_type':'待填写','date':'2026-10-28'},'source_records':[],'assets':{'角色':[],'场景':[],'道具':[]}}
put('assets/blank-data.json',json.dumps(blank,ensure_ascii=False,indent=2))
# Self-authored portable example with exact source paragraphs and a genuine outfit/state hierarchy.
sampletext='''合成边界案例：不属于任何真实作品。
第一集
1-1 夜 内 东村诊所
阿宁，28岁，诊所医师。性格沉着、谨慎，黑色短发。村民称她宁姐。
▲阿宁穿灰色日常外套站在靠窗木桌旁，门旁是药柜。
第二集
2-1 夜 内 东村诊所
▲阿宁换上白色工作服，右袖被雨打湿，右前臂出现一道划伤。
第三集
3-1 日 内 东村诊所
▲阿宁仍穿白色工作服，袖口已干，右前臂缠着纱布。
▲木桌已移到门前堵门，桌面裂开一道缝。
▲她拿出铜印，上面刻着“东”字。
'''
put('assets/sample-script.md',sampletext)
records=[];ep=None;scene=None
for i,line in enumerate(sampletext.strip().splitlines(),1):
 if line in ['第一集','第二集','第三集']:ep=['第一集','第二集','第三集'].index(line)+1;scene=None
 if len(line)>2 and line[0].isdigit()and '-'in line:scene=line.split()[0]
 records.append({'id':f'P{i:03}','text':line,'episode':ep,'scene':scene})
sample=json.loads(json.dumps(blank));sample['meta'].update({'project':'合成分层阅读示例','scope':[1,3],'source_name':'sample-script.md','source_type':'自编演示材料'})
sample['source_records']=records
def sample_node(sheet,key,name,desc,p,events=None,parent='',kind='资产',candidate=False,planned=None,outfit=''):
 refs=[f'P{x:03}'for x in p];events=events or []
 sample['assets'][sheet].append({'id':key,'name':name,'description':desc,'parent_id':parent,'kind':kind,'source_ids':refs,'events':[{'episode':records[x-1]['episode'],'scene':records[x-1]['scene'],'mode':'现场','source_id':f'P{x:03}','inferred':False}for x in events],'candidate':candidate,'planned_episodes':planned or [],'outfit_id':outfit,'review':'待确认'if candidate else'不适用','user_notes':''})
sample_node('角色','R01','阿宁（宁姐）','身份：诊所医师，28岁。\n性格：沉着、谨慎。\n外貌：黑色短发。\n服装：灰色日常外套，后换白色工作服。',[4,5,8,11],[5,8,11])
sample_node('角色','R01-01','灰色日常外套','原文明示：灰色日常外套，第1集出现。',[5],[5],'R01','服装')
sample_node('角色','R01-02','白色工作服','原文明示：第2集换上，第三集仍穿。',[8,11],[8,11],'R01','服装')
sample_node('角色','R01-02-01','湿袖／划伤','第2集右袖被雨打湿，右前臂有划伤。',[8],[8],'R01-02','状态',outfit='R01-02')
sample_node('角色','R01-02-02','干袖／包扎','第3集袖口已干，右前臂缠纱布。',[11],[11],'R01-02','状态',outfit='R01-02')
sample_node('场景','S01','东村诊所','功能：诊所中的连续事件。\n结构与陈设：靠窗木桌、门旁药柜。',[3,5,7,10,12],[5,8,11])
sample_node('场景','S01-01','木桌堵门状态','第3集木桌移到门前、桌面裂缝。',[12],[12],'S01','状态')
sample_node('道具','P01','东字铜印','用途：独立手持道具。\n关键文字：东；具体形制未写。',[13],[13])
put('assets/sample-data.json',json.dumps(sample,ensure_ascii=False,indent=2))
(BASE/'skill-backup.json').write_text(json.dumps({'backup':str(backup)},ensure_ascii=False),encoding='utf-8')
scratch=BASE/'package';shutil.copytree(ROOT,scratch,dirs_exist_ok=True)
print(str(backup))
