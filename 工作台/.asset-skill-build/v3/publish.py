from pathlib import Path
import json,shutil,zipfile,hashlib
BASE=Path.cwd()/'.asset-skill-build/v3'
ROOT=Path('E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown')
OUT=Path('E:/AI漫剧/01_作品项目/保镖驾到/资产需求/原剧第1—10集_资产拆解_V3')
AUD=OUT/'核验资料'
shutil.copy2(BASE/'blank/剧本资产需求清单.xlsx',ROOT/'assets/剧本资产清单_空白模板.xlsx')
shutil.copy2(BASE/'sample/剧本资产需求清单.xlsx',ROOT/'assets/剧本资产清单_边界案例.xlsx')
shutil.copy2(BASE/'finalize_excel_print.ps1',ROOT/'scripts/finalize_excel_print.ps1')
p=ROOT/'scripts/build_workbook.mjs'
s=p.read_text(encoding='utf-8')
needle="if(patch.status!==0)throw Error(patch.stdout+patch.stderr);"
addition="""
if(flags.includes('--excel-print')){
 if(process.platform!=='win32')throw Error('--excel-print需要Windows及本机Microsoft Excel');
 const native=spawnSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(base,'scripts/finalize_excel_print.ps1'),'-WorkbookPath',output],{encoding:'utf8'});
 if(native.status!==0)throw Error('Excel打印设置未完成：'+native.stdout+native.stderr);
}
"""
if "flags.includes('--excel-print')" not in s:s=s.replace(needle,needle+addition)
p.write_text(s,encoding='utf-8')
p=ROOT/'references/workbook.md'
s=p.read_text(encoding='utf-8')
s+='\n本机兼容性：2026-10-28实测，本机Excel打开仅含XML打印设置的导出时曾回落到A4纵向。已在交付表及模板中通过Excel原生另存修正，修正后重新核对原文和折叠。Windows且已安装Excel时，生成命令加`--excel-print`，或运行`powershell -NoProfile -File scripts/finalize_excel_print.ps1 -WorkbookPath <新表完整路径>`。此脚本只保存指定新表的打印设置；文件占用则报错，不关闭用户窗口。其他环境须如实记录尚未通过原生打印核验。\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'SKILL.md';s=p.read_text(encoding='utf-8');s=s.replace('[--render]`','[--render] [--excel-print]`');s=s.replace('--render为主行示意，实际折叠/打印仍应在Excel核验。','--render为主行示意；本机Windows/Excel可加--excel-print保存原生打印设置，实际折叠/打印仍应在Excel核验。');p.write_text(s,encoding='utf-8')
report='''# 这次改了什么与阅读说明

版本：V3.0，2026-10-28。本次只统计《保镖驾到，大小姐爱上了我一卡＋人物小传》第1—10集正文及人物小传；不是全60集统计。

## 先怎样看

打开同目录的“剧本资产需求清单.xlsx”，选择角色、场景或道具。五列依次是编号、名称、资产描述、完整原文、出现集数。

默认直接看资产主行：浅蓝行是基础角色或母场景；缩进行是其服装、身体状态或子空间。这些行始终显示。点击左侧“＋”可展开当前条目的原文，点击“－”收起。原文附属行不分新编号、不算新资产。展开后的C列是出处，D列才是可直接复制的完整原文。一次清除筛选后再读原文，避免筛选把附属行过滤掉；不要直接按名称排序拆散资产组。

出现集数逐项显示首次、全部出现与本范围末次。画外音和闪回注明方式，仅提及另列。“末次第10集”只说明本次范围，不能解读为死亡或永远退场。候选服装的拟用集数不计实际出现。

## 本轮实质修正

- 描述不再限制句数。角色写身份、基础信息、性格、外貌、服装；空间写功能、结构、陈设和环境；缺少的设定明确说明，不从提示词库借入。
- 服装与伤势分开：苏小菲睡衣明确在第7—8集；血手的黑衣、右手血红手套在第9—10集；黑袍人在第4集闪回穿黑袍。需要时再把身体状态挂在对应服装下面。
- 另列6项有本轮制作需求的服装设计候选。原文没有写出这些款式，因此不编造原文、实际集数。没有本轮正式礼服事件，不为凑分类另造礼服。
- 母场景下保留子空间与状态。苏家卧室、阳台、楼梯、院落、早餐用餐区分别登记；夜间交战和次晨院子清理后的状态分别追踪。张家沙发会客空间与明确命名的大厅暂不强行认定为同一房间。
- 江父江母在第4集闪回实际出现；老高第1集画外音，第7集只是江辰通话时称呼，没有对端台词，不算再次发声。
- 原文从源段落目录直接写入，不重新打字改写。段落过长时顺序分行，拼回后仍逐字相同；出处位于旁列，不能混入原文。

## 数据与验证范围

逐集读取501个Word段落、23场，覆盖正文第1—10集及小传。全篇梗概中的未来设定仅作人物背景，不伪造本轮出场；60集精简清单只辅助对照；人物提示词库不是本轮事实来源。

表中角色62条、场景33条、道具25条，均为包含子项、状态、候选等的主条目数量，不是演员数、建筑数或需要生成的图片数量。868条原文附属行是段落引用或长段片段，同一段可支持多项，不代表868个不同源段落。

21组数据与文件检查通过，涵盖源Word未改变、501段重新提取一致、23场覆盖、逐集记录、归属、候选隔离、稳定编号增补、批注保留，以及868条原文附属行逐字匹配。合成边界案例另外验证了超长段落、等号开头、换行、制表、空格和Unicode字符的无损存储。

真实Microsoft Excel验证了三表五列、默认收起、展开再收起、子项仍显示、C6冻结、原生筛选与A3横向打印。另实际应用“苏小菲”名称筛选，确认非匹配行被过滤，检查后未保存这次筛选。已检查默认收起的15页打印总览及角色原文展开的2页打印；正文保持11号字，标题15号，宽一页、高度自动。PDF是核验附件，不能替代Excel原生折叠使用。

本机Excel曾忽略仅写入XML的纸型，已通过原生保存修正交付表与模板，随后重新通过原文、分组检查；Skill新增可选原生打印保存脚本。未运行依赖PyYAML的官方Skill校验器，不将上述检查称为官方校验通过。

## 文件与保留

当前目录的Excel供你阅读使用；“核验资料”保存内部数据、原文与布局索引、检查结果和打印核验附件。内部JSON不是替代Excel后来批注的覆盖源。后续更新应读取当前Excel，保留用户批注及确认内容，另存新版。

旧版试跑目录保留，更新前完整Skill已备份到项目历史归档。本轮不生成图片或视频，未新增付费生成，未全局安装Skill。当前完整维护包仍在“02_制作方法/02_专业技能/研发候选/script-asset-breakdown”。
'''
(OUT/'这次改了什么与阅读说明.md').write_text(report,encoding='utf-8')
entry=Path.cwd()/'02_Skill/剧本资产拆解.md'
entry.write_text('''# 剧本资产拆解怎么用

当前版本：V3.0完整信息与分层阅读版。角色、场景、道具三张表，每表五列：编号、名称、资产描述、完整原文、出现集数。

- [完整Skill入口](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/SKILL.md)
- [保镖驾到第1—10集最新Excel](E:/AI漫剧/01_作品项目/保镖驾到/资产需求/原剧第1—10集_资产拆解_V3/剧本资产需求清单.xlsx)
- [新版空白模板](E:/AI漫剧/02_制作方法/02_专业技能/研发候选/script-asset-breakdown/assets/剧本资产清单_空白模板.xlsx)
- [修改与阅读说明](E:/AI漫剧/01_作品项目/保镖驾到/资产需求/原剧第1—10集_资产拆解_V3/这次改了什么与阅读说明.md)

主行充分描述资产；服装、身体状态、子场景紧跟母项并保持可见。点击左侧“＋”展开逐字原文，出处在旁列。首末及全部集数独立统计，仅提及与设计候选不计实际出现。使用原文前清除筛选，不直接按名称排序拆组。

调用：请读取上述SKILL.md，用“剧本资产拆解”处理【原剧完整路径】，本次范围【集数/场次】，输出三表五列Excel到【目录】。区分实际服装与身体状态；缺少但确有需要的设计另标候选；完整原文逐字保留、默认收起；统计首次、全部及范围内末次出现。未知不编造。

更新时同时提供当前Excel和已确认新方案，保留原编号、批注和确认内容，另存新版，不能用旧JSON覆盖后来修改。当前维护包未全局安装，按路径调用。第1—10集原剧与小传已完成本轮测试；不宣称覆盖全60集。V1、V2为历史版本。
''',encoding='utf-8')
p=Path.cwd()/'00_使用说明.md';s=p.read_text(encoding='utf-8');s=s.replace('三表五列；状态、服装和子场景按资产成组，按路径调用','三表五列；完整原文可展开，服装、状态和子场景直接可见，按路径调用');p.write_text(s,encoding='utf-8')
p=ROOT.parent.parent/'Skill目录与安装映射.md'
with p.open('a',encoding='utf-8')as f:f.write('''\n## 剧本资产拆解 V3.0 完整信息与分层阅读版（现行）

2026-10-28：[维护原件](研发候选/script-asset-breakdown/SKILL.md)。三表五列，完整原文独立折叠；服装、身体状态、子场景保持可见。来源逐字保存、按条目追踪首末与全部集数，候选不计实际出现。数据结构、规则、模板、脚本和边界案例同步更新。用《保镖驾到》原剧第1—10集及人物小传复测，范围不等于60集。21组结构/文字/增补检查及真实Excel折叠、筛选、冻结、打印核验通过。完整新版与空白模板已更新，旧版备份保留，仍未全局安装。V1/V2段落为历史记录。
''')
native=json.loads((AUD/'Excel原生验证.json').read_text(encoding='utf-8-sig'))
native['filterAppliedReadOnly']='角色名称=苏小菲，非匹配首行隐藏；未保存筛选'
native['visualReview']={'default_pages':15,'expanded_first_role_pages':2,'reviewed':'15页总览、角色组及场景组、默认首屏与展开原文首屏','printFinalizedInExcel':True}
(AUD/'Excel原生验证.json').write_text(json.dumps(native,ensure_ascii=False,indent=2),encoding='utf-8')
for f in ['资产数据_V3.json','版面与原文索引.json','验证结果.json','角色主行预览.png','场景主行预览.png','道具主行预览.png']:
 shutil.move(str(OUT/f),str(AUD/f))
backup=json.loads((BASE/'skill-backup.json').read_text(encoding='utf-8'))
(AUD/'旧版备份位置.json').write_text(json.dumps(backup,ensure_ascii=False,indent=2),encoding='utf-8')
dest=Path('E:/AI漫剧/04_项目管理/02_任务记录/剧本资产拆解_script-asset-breakdown_V3.0_完整包.zip')
if dest.exists():raise RuntimeError('已有同名交付包，拒绝覆盖')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted(ROOT.rglob('*')):
  if f.is_file() and '__pycache__'not in f.parts and f.suffix!='.pyc':z.write(f,str(Path(ROOT.name)/f.relative_to(ROOT)))
with zipfile.ZipFile(dest)as z:
 assert z.testzip()is None
 manifest={'zip':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':z.namelist()}
(AUD/'交付包核验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
record=dest.parent/'剧本资产拆解_V3_完成记录_2026-10-28.md'
record.write_text(f'''# 剧本资产拆解V3完成记录

实现用户批准的完整信息与分层阅读方案。测试输入为原剧第1—10集及人物小传，501段、23场，不是全60集。

- [测试Excel]({(OUT/'剧本资产需求清单.xlsx').as_posix()})
- [阅读与修改说明]({(OUT/'这次改了什么与阅读说明.md').as_posix()})
- [完整Skill包]({dest.as_posix()})
- [空白模板]({(ROOT/'assets/剧本资产清单_空白模板.xlsx').as_posix()})

21组检查通过，真实Excel原生折叠、展开、冻结、实际筛选和打印已验证。完整原文868条附属行逐字匹配，打印原生保存后重新验证仍一致。数据、测试结果和打印核验归档在测试目录“核验资料”。旧版保留，维护原件未全局安装。
''',encoding='utf-8')
print(json.dumps({'workbook':str(OUT/'剧本资产需求清单.xlsx'),'zip':str(dest),'package_files':len(manifest['files'])},ensure_ascii=False))
