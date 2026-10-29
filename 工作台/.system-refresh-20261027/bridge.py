from pathlib import Path
import re,json
base=Path(r'E:\AI漫剧');work=Path(__file__).parent
flows=base/'02_制作方法/01_流程规范'
guide='''# R2系统使用与旧版映射

2026-10-27｜当前专业发布组合：project-script-analysis V2.0、photoreal-drama-director V1.0、shot-language-design V1.0、video-prompt-authoring V1.0、tig-blocking-map V3.0。发布不是媒体能力认证，也不自动升级进行中的作品。

## 当前怎么用

已有剧本先分析项目和原文；导演决定观众经历与场面；镜头语言选择景别组接、机位构图、主动运动、表演可见性和切点；提示词编译已选设计。TIG按需辅助某镜/阶段几何。只有本轮需要的阶段才运行，已有充分输入可直接从中间进入。

三份操作手册见[手册入口](../../04_通用模板/分镜运镜与表演操作手册/00_从这里开始.md)。专业方法原件在Skill的references中，Word/MD阅读稿按原件同版导出。用户批注回写原件后统一再导出，不在两边各改一套。

## 旧体系与本次体系哪里不同

| 对象 | 旧规则或易混点 | 当前采用方法 |
|---|---|---|
| S1—S6与四Skill | S2、S3拆整体导演和单场；S6同时含提示词与生成 | 当前四阶段是创作/编译主链，不取代素材、生成和后期全流程；按职责映射，不按阶段数争夺权威 |
| G/T/A管理 | 旧T09是该候选项目的G门记录，部分手册规定固定步骤数 | 仅明确采用旧契约的项目沿用，不能作为通用Skill开工条件；用户已授权的工作继续 |
| 同名七栏 | 旧第三列摄影、第五列场景光影；新第三列起幅构图、第五列摄影机光学 | 按语义拆映射，旧光影进入段落共性与本镜变化，不照列号覆盖 |
| 景别和运镜 | 旧检查多、正向构思弱；同镜/稳定可能先入为主 | 先设计观看距离、视觉重音和运动趋势，再完善执行；不能全部中景固定或全部缓推 |
| 时间 | 最短可读可被误当最高优先 | 时长由阅读、动作/对白重叠与节奏共同决定；预算与实测分开 |
| 表演 | 动机/行动已存在，身体和面部细化不够 | 同一主责手册负责行动、相互适应、支撑施力、呼吸眼口与可读性，其他阶段不重新发明心理 |
| 六模块提示词 | 容易被当成另一套导演设计 | 是编译结构，保留源稿摄影与表演，任务分组不改镜头身份 |
| 图稿 | 一张站位图容易被当成全场布局与动作锁 | 每镜每阶段重新计算投影，初态释放后按分镜行动，中途遮挡需核 |
| 旧试跑 | 历史验证文字与新版本并存 | 保留历史，不能证明R2已经验证；R2有单独输出与核查记录 |

## 旧字段迁移操作

保留原项目编号和采用版本，先核该项目是否真的切换本次体系。仅学习方法不必迁移文件。需要迁移时按当前共同协作规范映射故事事实、导演保持项、七栏、镜号任务、原句与初末态；核完相关范围才更新项目入口，不改旧稿历史身份。

四阶段规范是此链共同信息的维护源；通用SOP管生产阶段与授权/真实交付；专业手册管创作方法。若各自写了同一条且不同，回对应维护源修一次，不靠在每个包末尾追加更多例外。

旧S1—S6只读来源及原始附件仍保持原样，旧项目已采用结果继续有效。新系统没有迁移/删除作品，未改变其他项目主Skill，未进行媒体生成。
'''
# Relative destinations from AI仿真人全流程 need two parent steps to 制作方法.
bridge=flows/'AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md'
bridge.write_text(guide,encoding='utf-8')
old=flows/'AI仿真人全流程/AI仿真人全流程SOP_通用母版_V0.1.md'
text=old.read_text(encoding='utf-8-sig')
new=old.with_name(old.name.replace('V0.1','V0.2'))
assert not new.exists()
text=text.replace('版本：V0.1｜日期：2026-10-24','版本：V0.2｜日期：2026-10-27')
text=text.replace('配套[制作对象与交接契约]', '本次专业方法与旧体系接续见[系统R2使用与映射](分镜与表演系统R2_使用与旧版映射.md)。本轮更新镜头/表演的决策顺序与当前Skill组合，未宣称真实全流程或媒体效果已经通过。\n\n配套[制作对象与交接契约]',1)
text=text.replace('允许不反应、延迟反应和克制，只要契合人物目的。','强烈、克制、延迟或不反应都按人物目的和具体风格选择；角色身体和面部细化由表演手册维护。')
text=text.replace('3. 选择镜头职责、景别、构图、观察立场与摄影路径。固定机位有表达作用即可使用；不规定每段至少几镜，不把频繁切镜当高级。','3. 先组织整段视觉重音、景别距离、运动与长短节奏，再联合设计单镜职责、机位、构图、光学与摄影路径。主动比较推拉摇移、跟随、弧绕、升降与特殊/复合运动，稳定阅读是具体选择；不默认中景固定或缓推，也不按镜数/运动比例评质量。')
text=text.replace('AI仿真人总控Agent_V0.1.md','AI仿真人总控Agent_V0.2.md')
new.write_text(text,encoding='utf-8')
old.write_text('# 历史版本说明\n\n本文件为V0.1历史母版，当前方法请见[通用母版V0.2](AI仿真人全流程SOP_通用母版_V0.2.md)。原内容保留供已有版本引用，不能与新稿同时当当前入口。\n\n'+old.read_text(encoding='utf-8-sig'),encoding='utf-8')
agentroot=base/'02_制作方法/02_专业技能/Agent职责与交接'
for f in list(agentroot.glob('*_V0.1.md')):
    text=f.read_text(encoding='utf-8-sig')
    dst=f.with_name(f.name.replace('V0.1','V0.2'));assert not dst.exists()
    text=text.replace('V0.1','V0.2')
    # Capability mapping itself remains V0.1 until independently revised.
    text=text.replace('AI仿真人Skill组合与适配_V0.2.md','AI仿真人Skill组合与适配_V0.1.md')
    if '职能角色' in f.name:
        text=text.replace('## 重叠如何处理','## R2专业设计分工\n\n导演主责动机、场面和表演方法；分镜主责整段景别/机位构图/运动/时间与表演可见性；提示词主责保真编译和实际任务。三份操作手册维护专业规则，职能表不再复制一套参数或微动作规范。TIG按需辅助某镜阶段几何，不增加必经审批。\n\n## 重叠如何处理')
    else:
        text=text.replace('## 调度与交接','## 当前专业组合\n\n当前本链可选组合为项目分析V2.0、导演V1.0、镜头语言V1.0、提示词V1.0和TIG V3.0。详见[系统R2映射](../../01_流程规范/AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md)。这不是覆盖所有项目的默认选择，也不代表已经安装所有包。\n\n## 调度与交接')
    dst.write_text(text,encoding='utf-8')
    f.write_text('# 历史版本说明\n\n当前入口为['+dst.stem+']('+dst.name+')。下文保留旧版，不作为R2并行运行规则。\n\n'+f.read_text(encoding='utf-8-sig'),encoding='utf-8')
nav=flows/'SOP导航与版本状态.md'
t=nav.read_text(encoding='utf-8-sig').replace('AI仿真人全流程SOP_通用母版_V0.1.md','AI仿真人全流程SOP_通用母版_V0.2.md').replace('AI仿真人总控Agent_V0.1.md','AI仿真人总控Agent_V0.2.md').replace('AI仿真人职能角色与交接_V0.1.md','AI仿真人职能角色与交接_V0.2.md')
first,rest=t.split('\n',1)
nav.write_text(first+'\n\n当前R2专业发布与旧体系接续见[映射说明](AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md)。三份操作手册与五Skill已作本轮文字修订，真实媒体和用户采用另记。\n'+rest,encoding='utf-8')
# Mark dated knowledge drafts as dated; keep old text and .doc files intact.
oldnotes=base/'03_参考资料/02_知识笔记/03_导演与视听叙事/制作流程与分镜规范/MD维护稿'
for f in oldnotes.glob('*.md'):
    t=f.read_text(encoding='utf-8-sig');first,rest=t.split('\n',1)
    note='\n\n历史知识稿说明｜2026-10-27：下方提案状态/旧版本描述属于成文当时。当前专业方法以02_制作方法中的R2五Skill及三操作手册为准；不把“尚未写入Skill”等旧状态作为今天的结论。旧例子不强制成为新项目模板。\n'
    f.write_text(first+note+rest,encoding='utf-8')
print('New SOP V0.2, Agent V0.2, bridge and navigation written; legacy read-only source preserved')
