from pathlib import Path
import json,shutil,zipfile,hashlib
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OUT=Path(r'E:\AI漫剧\04_项目管理\02_任务记录\剧本资产拆解_首轮小样')
WORK=Path(r'E:\MoveFile\File\ChatGPT\AI漫剧SOP、SKILL与提示词迭代')
for src,dst in [('空白模板','剧本资产清单_空白模板.xlsx'),('样稿','剧本资产清单_边界案例.xlsx')]:shutil.copy2(OUT/src/'剧本资产需求清单.xlsx',ROOT/'assets'/dst)

p=ROOT/'references/workbook.md'
text=p.read_text(encoding='utf-8').replace('依赖@oai/artifact-tool；','依赖@oai/artifact-tool与Python标准库；原生内部链接由scripts/add_links.py补充，因为当前生成引擎不支持HYPERLINK公式。可通过环境变量ASSET_PYTHON指定已配置的Python可执行文件。动态命名引用按稳定编号查找，排序后不依赖旧行号。')
text += '\n随包提供 `assets/剧本资产清单_空白模板.xlsx` 与 `assets/剧本资产清单_边界案例.xlsx`。案例待用户审阅，不等同于正式作品资产清单。\n'
p.write_text(text,encoding='utf-8')
usage='''# 剧本资产拆解怎么用

用途：拿到剧本后，提取角色、群众、服装状态、场景状态和道具，整理为七张Excel工作表。

状态：V1.0首轮实现，合成案例和本机Excel检查通过，样稿待你审阅，尚未全局安装。按总库“先小样再定稿”的约定保存在研发候选区；没有把自动校验当作用户审核通过。

- [完整Skill入口](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/SKILL.md)
- [先看Excel小样](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/assets/剧本资产清单_边界案例.xlsx)
- [空白模板](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/assets/剧本资产清单_空白模板.xlsx)
- [识别规则](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/references/identification.md)
- [表格字段与更新规则](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/references/workbook.md)

## 给Codex的指令

请读取 `E:\\AI漫剧\\02_制作方法\\02_专业技能\\研发候选\\script-asset-breakdown\\SKILL.md`，用“剧本资产拆解”方法处理【剧本完整路径】，本次只处理【集/场范围】，输出Excel到【指定目录】。按剧本先初拆，身份不清、服装和状态缺失时标缺口并给候选；家具陈设归入场景，群众也提取，不生成图像或视频。

后续更新：把当前Excel和已确认的导演/分镜方案一并交给Codex，说明变化范围。保留现有编号、确认内容与用户批注，另存新版本。清单编号不是平台素材编号。

## 看小样的顺序

先看“使用说明与总览”，再看“角色基础→角色服装与状态”“场景基础→场景状态”“道具需求”。想知道某项从哪来、在哪场用、发生什么变化，就看“出现与变化明细”，按资产编号筛选。

小样是《诊室夜变》合成剧本，不属于你的现有作品。它展示阿宁/宁姐归并、双胞胎分开、群众人数拆分、湿伤与局部变形、家具堵门破损、同款两枚铜印分别追踪，以及画外钟声不要求可见设计。
'''
(WORK/'02_Skill/剧本资产拆解.md').write_text(usage,encoding='utf-8')
index=WORK/'00_使用说明.md';text=index.read_text(encoding='utf-8');needle='| 让 AI 按固定方法做任务 |'
line='| 从剧本提取角色、场景、道具及状态 | [剧本资产拆解](02_Skill/剧本资产拆解.md) | 七表Excel清单；V1.0小样待审，按路径调用 |\n'
if '[剧本资产拆解]' not in text:
    start=text.index(needle);text=text[:start]+line+text[start:];index.write_text(text,encoding='utf-8')
mapping=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\Skill目录与安装映射.md')
text=mapping.read_text(encoding='utf-8');heading='## 剧本资产拆解 V1.0 首轮实现'
if heading not in text:
    text+='\n'+heading+'\n\n按用户批准方案实现。[完整候选包](研发候选/script-asset-breakdown/SKILL.md)含七表Excel模板、合成案例、字段规范、生成/校验/保留式JSON增补脚本。13组结构与更新检查通过，另有Excel原生排序定位与新增行统计验证。用户样稿审阅未完成，尚未移入自研Skill发布区，未全局安装。不是新的强制生产阶段。\n'
    mapping.write_text(text,encoding='utf-8')
report='''# 剧本资产拆解 首轮交付与验证

## 完成内容
按已批准方案实现独立Skill script-asset-breakdown V1.0，七表Excel字段及空白模板、识别规则、更新与交接规范、边界案例、可复用生成和校验脚本。工作台新增中文使用入口，没有修改其他生产Skill，也没有批量拆解作品。

七表为：使用说明与总览、角色基础、角色服装与状态、场景基础、场景状态、道具需求、出现与变化明细。家具陈设归场景、群众按群组提取且关键者单列；事实/推断/候选与确认状态分别表达。

## 小样
原创合成剧本《诊室夜变》V1，范围S01—S03/P01—P06。登记7条角色、8条外观组合、1个空间、3条空间状态、2条道具设计、20条出现记录。角色条数不等于人数，道具设计条数不等于实物数量。小样不属于任何真实项目，D02仅用于独立更新测试。

## 已验证
- 13组结构与更新检查通过，具体见“结构与更新验证.json”：重复编号、数量为零、父键错配、无来源、停用引用、基准成环、道具错配、改名保号、批注保留、确认冲突保护等。
- XLSX导出后检查七表、过滤表、双向冻结、枚举验证、无合并数据单元格、来源与引用、统计缓存及原生内部链接。
- 本机Microsoft Excel COM在一次性副本上打开、重算与排序：各表有效条数7/8/1/3/2/20；CHR-0001动态目标由A5移至A11仍指向同一编号；新增角色表行后角色统计由7变8。交付文件未作此测试修改。
- 七表预览与右侧证据/状态明细已检查，修正HYPERLINK公式在生成引擎中显示内部提示的问题，改用原生内部超链接与动态命名引用；明确开启Excel表的筛选按钮。

## 限制与状态
官方quick_validate.py因运行时缺少PyYAML未运行完成；未宣称通过，改做入口frontmatter、显示元数据、相对链接与未完成占位符的替代检查。没有安装新依赖。
脚本结构校验不证明自然语言理解正确，本轮是手工语义复核的合成案例，没有声称真实长剧已全量验证，也没有生成媒体。Excel生成器只建新表；merge_data.py只合并JSON，不能保留Excel中未回读的后来修改。已有Excel的更新须先读取并保留式编辑。

新Skill保存在研发候选区，符合根AGENTS.md“未通过审核的草案仍留在研发候选区”及本轮“先小样再定稿”的约定。批准设计方案与用户审阅实际样稿分开记录；无需为本次已授权实现重新申请许可。可立即按完整路径调用试用，待小样审阅后按项目约定发布到自研Skill，不自动修改全局记忆或安装目录。
'''
(OUT/'交付与验证说明.md').write_text(report,encoding='utf-8')

dest=OUT/'剧本资产拆解_script-asset-breakdown_V1.0_完整包.zip'
files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,Path('script-asset-breakdown')/p.relative_to(ROOT))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(OUT/'完整包文件校验.json').write_text(json.dumps({'zip':str(dest),'zip_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'skill':str(ROOT),'zip':str(dest),'files':len(files),'xlsx':[str(ROOT/'assets/剧本资产清单_边界案例.xlsx'),str(ROOT/'assets/剧本资产清单_空白模板.xlsx')]},ensure_ascii=False))
