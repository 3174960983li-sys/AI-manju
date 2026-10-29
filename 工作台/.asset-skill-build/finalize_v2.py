from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,hashlib,shutil
ROOT=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\研发候选\script-asset-breakdown')
OUT=Path(r'E:\AI漫剧\01_作品项目\保镖驾到\资产需求\清单试跑_V0.2_分组阅读版')
WORK=Path(r'E:\MoveFile\File\ChatGPT\AI漫剧SOP、SKILL与提示词迭代')
REPORT=Path(r'E:\AI漫剧\04_项目管理\02_任务记录')
for src,name in [(Path('.asset-skill-build/v2-blank/剧本资产需求清单.xlsx'),'剧本资产清单_空白模板.xlsx'),(Path('.asset-skill-build/v2-sample/剧本资产需求清单.xlsx'),'剧本资产清单_边界案例.xlsx')]:shutil.copy2(src,ROOT/'assets'/name)
report='''# 《保镖驾到》三表五列复测 V0.2

## 打开方式
先打开同目录《剧本资产需求清单.xlsx》。只有角色、场景、道具三表，每表五列：编号、名称、简洁描述、原文内容、出现集数。母项浅底色，下属行缩进。清除筛选可恢复完整分组，不要独立按名称排序拆散父子组。

## 按你的要求改了什么
- 角色的服装/状态紧接角色，不再放另一张表。本材料没有明确服装方案，所以不编服装，仅列有依据的少年形态、面具摘戴、受伤护理、阴玉融合。
- 场景按母场景→子场景→该空间的状态排列。苏家别墅下有客厅、餐厅、书房、两间卧室、走廊楼梯、阳台、院子、大门；白天、夜间和订婚布置挂在院子下。
- 删除全未知的重复“基准外观/基准空间状态”行，管理字段不进入Excel。原文与出处直接在原文内容列，出现集数只保留有依据的范围，子空间具体分配未知时说明未细分。
- 角色简介只写有依据的信息，没有性格小传就不编。动物单列角色并标动物；三类载具在道具表末尾标载具。特效留在相关描述，不当成实体道具凑行。

## 本轮登记口径
|工作表|组成|总行数|
|---|---|---:|
|角色|20项身份/群体/动物＋5条外观状态|25|
|场景|14个母场景分组＋36条子空间＋1处独立野外＋5条状态|56|
|道具|36项道具/内容母项＋9条组内差异＋3类载具|48|
这些是阅读条目，不等于出图数。模板分组不一定是独立出镜建筑；反派密室暂分三条需求，不冒称已证实三个不同房间；至尊令破碎形态归属真/假哪枚仍待原剧。

## 输入限制
仍使用用户提供的《全60集场景与道具精简整合清单》，已核原Word未变，非其引用的60集/96分场原剧本。角色是否完整、全部换装与伤势演变、逐场出入状态仍未验证。“原文内容”是所提供清单的摘句，不宣称原剧事实已核。没有补写人物性格、衣服样式、虚构集数、台词或屏幕正文。

## 验证
16组结构/更新/语义检查通过：重复号、孤儿、拆组、跨表父项、来源缺失、旧JSON误套用、新子项组内插入、改名保号、批注与确认内容保护、母子空间、动物/载具分类、导出三表五列、空模板无假资产、原文未变等。Microsoft Excel已只读打开实际文件，核对三表、五列、25/56/48行、筛选与角色子项紧跟母项。视图按实际内容换行和行高检查，细节见核验资料。
完整Skill旧版已备份，原七表试跑仍保留。V2同步更新了入口、字段规范、识别/迁移/交接规则、校验/增补/生成脚本、空模板和合成示例；未全局安装。
官方quick_validate依赖PyYAML在当前运行时缺失，本次采用元数据/引用/行为检查，没有宣称官方校验器通过。
'''
(OUT/'这次改了什么与测试说明.md').write_text(report,encoding='utf-8')
entry='''# 剧本资产拆解怎么用

当前版本：V2.0分组阅读版，按用户确认的格式维护。只有角色、场景、道具三张表，每张表五列：编号、名称、简洁描述、原文内容、出现集数。服装和状态紧跟角色，子场景和状态紧跟对应场景。

- [完整Skill入口](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/SKILL.md)
- [保镖驾到最新试跑Excel](E:/AI漫剧/01_作品项目/保镖驾到/资产需求/清单试跑_V0.2_分组阅读版/剧本资产需求清单.xlsx)
- [空白模板](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/assets/剧本资产清单_空白模板.xlsx)
- [更新与测试说明](E:/AI漫剧/01_作品项目/保镖驾到/资产需求/清单试跑_V0.2_分组阅读版/这次改了什么与测试说明.md)

调用：请读取上述SKILL.md，用“剧本资产拆解”处理【剧本完整路径】，本次范围【集数/场次】，输出三表五列Excel到【目录】，服装、状态与子场景放在所属资产下面。保留原文与集数，未知不编造。

更新已有表时一并提供当前Excel及已采用的新方案，按编号保留修改与批注，另存新版本，不用旧JSON覆盖后来修改。当前维护包在研发候选位置，未全局安装，可按路径使用。保镖驾到输入是精简清单，尚未完成原剧逐场完整性验证。
'''
(WORK/'02_Skill/剧本资产拆解.md').write_text(entry,encoding='utf-8')
mapping=Path(r'E:\AI漫剧\02_制作方法\02_专业技能\Skill目录与安装映射.md')
text=mapping.read_text(encoding='utf-8')
if '## 剧本资产拆解 V2.0 分组阅读版' not in text:
 text+='\n## 剧本资产拆解 V2.0 分组阅读版\n\n当前维护原件仍为[完整Skill](研发候选/script-asset-breakdown/SKILL.md)，V2替代原七表输出：三表五列，服装/状态归同资产，母场景下有子场景。脚本、模板和案例同步更新；旧版完整包已备份。已用《保镖驾到》精简清单复测并核对Excel，逐场原剧完整性未验证。未全局安装。V1段落为历史记录。\n'
 mapping.write_text(text,encoding='utf-8')
idx=WORK/'00_使用说明.md';text=idx.read_text(encoding='utf-8').replace('七表Excel清单；V1.0小样待审，按路径调用','三表五列；状态、服装和子场景按资产成组，按路径调用');idx.write_text(text,encoding='utf-8')
archive=REPORT/'剧本资产拆解_script-asset-breakdown_V2.0_完整包.zip'
files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__'not in p.parts and p.suffix!='.pyc']
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
 for p in files:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
with ZipFile(archive) as z:assert z.testzip()is None
(REPORT/'剧本资产拆解_V2_更新与复测.md').write_text('# 剧本资产拆解V2更新与复测\n\n[最新Excel](E:/AI漫剧/01_作品项目/保镖驾到/资产需求/清单试跑_V0.2_分组阅读版/剧本资产需求清单.xlsx) · [修改与测试说明](E:/AI漫剧/01_作品项目/保镖驾到/资产需求/清单试跑_V0.2_分组阅读版/这次改了什么与测试说明.md)\n\n按用户确认的三表五列格式更新完整Skill，16组检查与Excel原生验证通过。旧版已备份，旧试跑保留；没有把二手清单当逐场原剧。完整包：'+str(archive)+'\n',encoding='utf-8')
(OUT/'完整包校验.json').write_text(json.dumps({'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(files)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'skill_version':'2.0','skill_files':len(files),'zip':str(archive),'xlsx':str(OUT/'剧本资产需求清单.xlsx')},ensure_ascii=False))
