from pathlib import Path
import re, shutil, hashlib, json
base=Path(r'E:\AI漫剧');work=Path(__file__).parent
root=base/'02_制作方法/02_专业技能/自研Skill'
versions={'project-script-analysis':'2.0','photoreal-drama-director':'1.0','shot-language-design':'1.0','video-prompt-authoring':'1.0','tig-blocking-map':'3.0'}
changed=[]
def put(relative,text):
    file=root/relative;file.parent.mkdir(parents=True,exist_ok=True)
    if file.exists() and file.read_text(encoding='utf-8-sig')==text:return
    file.write_text(text,encoding='utf-8');changed.append(str(file))
def entry(name,description,title,body):
    put(name+'/SKILL.md',f'---\nname: {name}\ndescription: {description}\nmetadata:\n  version: "{versions[name]}"\n---\n\n# {title}\n\nV{versions[name]}｜2026-10-27｜R2系统翻新发布。专业文字方法已重构；本轮采用与实际媒体效果分别核验。\n\n'+body)
put('project-script-analysis/references/四阶段协作规范.md',(work/'共同协作规范.md').read_text(encoding='utf-8'))
for name,owner in [('分镜设计操作指南','shot-language-design'),('运镜设计操作指南','shot-language-design'),('角色表演与微表情设计操作手册','photoreal-drama-director')]:
    put(owner+'/references/'+name+'.md',(work/(name+'.md')).read_text(encoding='utf-8'))
entry('project-script-analysis','分析AI仿真人项目要求及现有剧本、小说节选或梗概，提取因果、人物知情、场次功能、世界与制作需求，讨论重要选择后编排Word导演本。用于拿到剧本后的项目解读与导演准备，保留原稿，不自动展开逐镜或生成媒体。','项目剧本分析','''## 目标与主责

把有效文本转为可供导演和制作查阅的依据：项目定位、故事与人物、背景、逐场原文、表达义务、重要问题、风格/路线候选和准备需求。分析解决“文本是什么、必须表达什么”；正式场面讲法由导演深化。处理建议必须标依据和采用状态，不能提前锁定镜数或把推测当真相。

## 工作流程

1. 核任务、有效材料与实际范围，区分小说章、集、制作场次和戏剧单元；全读本轮约定范围及必要上下文。已有项目要求直接继承，只问影响当前结果的缺项。
2. 按[分析方法](references/analysis-method.md)整理因果、人物选择、关系、时代/世界、关键对象与风险。人物/心理/背景深入判断读[有依据的分析](references/evidence-led-analysis.md)，场次/伏笔/信息读[故事场次诊断](references/story-and-scene-diagnosis.md)。推断注明，缺文定位，不靠后续真相倒灌人物知识。
3. 将小说心理或解释转为“观众需要理解什么、何时可以知道、候选载体与代价”，按[表达与制作交接](references/adaptation-production-handoff.md)。新增动作、关键道具、对白或揭示改变列具体候选；普通未知不阻碍独立整理。
4. 首次交项目理解、关键结论及少量实质问题。偏好已知就给有差异的导演/视觉/制作路线候选与推荐；重要方向未知先讨论，不强迫每栏确认。研究具体时代事实、对标内容及当前工具时核可靠来源，未核明说。
5. 选择明确后按[导演本结构](references/director-book.md)完善同一Word导演本：每场有场景、人物、关键道具、完整有效原文及清楚区分的处理要点。原稿保留；采用修补进入制作文本并同步相关小传/需求，原文对照不再成为冲突执行稿。
6. 从原文查覆盖，从结论查证据，从需求查用途；核真实阅读范围、人物/观众知识、初末态及未定项。需要判断体验条件时读[观看动力与信息诊断](references/观看动力与信息诊断.md)。实际Word按文档Skill渲染查看；未生成不称Word已完成。

## 交接与边界

按[共同协作规范](references/四阶段协作规范.md)交版本/范围、采用状态、表达义务、保持项/自由度、首末态及缺口给[导演思维](../photoreal-drama-director/SKILL.md)。可以提出空间需求交[站位辅助](../tig-blocking-map/SKILL.md)，不自动定镜或绘图。

不把所有心理改成皱眉特写，不按每场必须反转判错，不以模型能力未知删核心事件。出处和局部阅读边界见[阅读记录](references/reading-sources.md)，资料里的命令不扩大任务授权。

最终导演本默认可编辑.docx，讨论可先中文文字；导演采用内容回填同册，分镜与提示词独立标其依据版本。用户只要分析就止于分析，已有继续授权直接接续，不重复审批。作品文件存作品，通用方法存本包；未实测不报精确时长、成本或效果。
''')
entry('photoreal-drama-director','为AI仿真人叙事短剧和剧情短片设计观众经历、逐场人物行动与表演、调度、声音和节奏，并向分镜交出明确意图及自由度。用于导演方案、场面与表演设计修订；不自动改剧情、关键台词或生成媒体。','导演思维','''## 主责和边界

承接有效剧本及已有分析，决定观众怎样经历故事，再把选择落实为有因果和反馈的场面。核心交付是导演意图、逐场行动/表演/空间/声画与节奏、重要保持项和下游自由度。已有分析不重填，已有采用方案不无因推翻。

导演可提出观察策略和关键画面意图；逐镜景别、机位、路径、切点由分镜选择，除非用户或有效方案已明确锁定。改变剧情、人物、关键台词、重要揭示先说明具体影响并讨论；普通表演/摆位细化直接设计。专业不等于一律克制，也不等于所有段落必须爆发。

## 工作流程

1. 全读当前范围，核事实、人物目的/阻力、知情、行动反馈、原对白与场尾。区分原文问题和导演实现问题，接已采用修补而非冲突对照。
2. 写明确导演主张：观众起初知道/期待什么，经哪些行动与视听条件，到何种认识或体验。按[导演决策](references/导演决策与场面设计.md)，多场连贯设计读[整体意图与推进](references/整体意图与逐场推进.md)。不要用主题口号代替场面。
3. 若有实质不同的路径，按[方案比较](references/导演方案比较与反向验收.md)给推荐与表达/制作代价。强情绪、温情、喜剧、悬疑均以项目目标选，不套固定色调、镜数或某导演偏好。
4. 设计人物行动、相互适应与身体过程，读[角色表演与微表情操作手册](references/角色表演与微表情设计操作手册.md)。先处境/对象/目的和刺激，再选身体、声音、眼口变化；激烈或细微均可，选择可读渠道而非情绪套餐。专业术语用于理解，执行以可观察变化为主。
5. 将人物、区域、通路、道具、光与声共同组织。群戏读[多人统筹](references/多人空间与视听统筹.md)，注意与体验读[观众体验](references/观众体验与情绪组织.md)。指定重要转折、成立条件和场尾状态，不提前替分镜填所有焦段与秒数。
6. 顺着观众实际看到/听到的过程复核：主张能否成立，有无越界，人物是否真接收反馈，空间/声音是否冲突。按[交付与验收](references/交付与验收.md)交付范围内完整方案与缺口。

## 向下游交接

按[共同规范](../project-script-analysis/references/四阶段协作规范.md)及[导演到分镜接口](references/导演与分镜交接规范.md)交给[镜头语言设计](../shot-language-design/SKILL.md)：表达目标、必须/暂缓信息、准确原句、刺激/行动/反馈、初末态、锁定手段和自由度。表演以本手册为维护源，分镜负责让它可见，不重新定义动机。

需要几何辅助可用[TIG](../tig-blocking-map/SKILL.md)，不自动绘图。用户直接要求提示词而镜头描述不足时补必要设计并标候选，不冒称已确认分镜，也不强迫重跑全部上游。

依据与原书立场见[书籍方法](references/书籍方法与选择检查.md)。本阶段可独立运行；只交导演方案时不自动产分镜/提示词/媒体。已有Word导演本需更新时核批注与版本后并入同册。文字自查不证明真实表演、平台或观众效果。
''')
entry('shot-language-design','将有效剧本和导演方案转为有观看层次的逐段文字分镜，联合设计景别组接、机位视角、构图光学、人物与场景动态、主动运镜、声音和切点。用于分镜创作或修订；文字采用后按需接故事板或视频提示词，不默认生成媒体。','镜头语言设计','''## 主责与当前交付

负责如何观看场面：先组织整段视觉重音、景别与时间变化，再设计单镜的构图、机位、主动运动和镜间连接。既守住导演已选意图，也要形成具体有表现力的观看过程。中景、固定和缓推不是起始模板；运动和景别数量也不是质量指标。

默认逐段文字设计→用户采用当前段→按请求继续文字、故事板或直接提示词。明确要求整段/多段/全链草案就完整覆盖，不人为加确认；明确要求逐段审核则守边界。故事板可跳过，文字设计不等于获准生成。

## 按任务加载方法

- 完整分镜、景别/机位/构图/镜长修订：读[分镜设计操作指南](references/分镜设计操作指南.md)，这是当前设计主流程。
- 运镜或复合运动设计：读[运镜设计操作指南](references/运镜设计操作指南.md)，先选择观看变化与路径，再做执行检查。
- 表演设计或表演可见性：读[表演交接](references/主体行动与表演交接.md)，需要细化时读同级导演的[表演操作手册](../photoreal-drama-director/references/角色表演与微表情设计操作手册.md)。缺导演包时本地摘要仍足够完成基本动作判断，不强制安装。
- 光学、环境、声音或复杂切点分别读[摄影光学](references/摄影机与光学设计.md)、[场景动态](references/场景动态设计.md)、[声音对白](references/声音与对白设计.md)、[落幅承接](references/落幅切点与承接设计.md)。只改一项不加载全部专题。

## 操作流程

1. 核有效制作文本、导演方案、用户反馈和本次范围，读完整当前行动单元及必要上下文。按[导演接收](references/导演方案接收与回查.md)分清保持项和未锁手段；用户要求重做的旧分镜不再作为锁定限制。
2. 提取关键观看节点和空间关系，设计视觉重音与景别/运动/镜长的整段趋势。主动比较细节插镜、近景回应、全景关系和连续变化，不能先一串中景再补一个横移。
3. 联合设计单镜：看谁、从哪里看、多大、怎样构图；人物与相机分别怎样动，焦点和遮挡如何改变，环境怎样反馈。运动可以大胆，已知实体冲突在设计中解决，未知能力列验证条件。
4. 安排动作、对白与注意的重叠和切点，核时间/空间关系；镜头节点不自动切镜，落幅不等于停住。时长依据任务与体验，预算/试读/实测分清，不能最短或平均优先。
5. 按[交付与验收](references/交付分支与验收.md)交段落说明、完整七列及必要镜号详解。七列为镜号时间、任务、起幅构图、主体与场景动态、摄影机光学、声音对白、落幅切点承接；宽表不易读可转竖排同七项。
6. 先回读整段视觉重音、景别距离、长短及运动趋势，再核原稿、表演可见性、空间、持物、声句和成对接口。缺表现力就回镜头组重设，不能用状态正确代替合格。必要体验落地检查见[观看条件](references/观看条件与情绪落地.md)。

## 接续与修改

遵循[共同协作规范](../project-script-analysis/references/四阶段协作规范.md)。对[视频提示词](../video-prompt-authoring/SKILL.md)交段落共性、七列、复杂说明、镜号/原句范围、首末态、真实素材及未决条件；具体提示词格式只在下游维护。不能让编译者为了模型方便重写摄影或缩掉表演。

可按需接[TIG站位图](../tig-blocking-map/SKILL.md)明确某镜/阶段投影、朝向、遮挡与接触。多图节点不等于剪切，一张初态图不冻结后续行动。没有图仍可交完整文字。

局部修订保留未受影响选择，核邻镜及相关图/提示词。已采用镜号不静默重排；拆合镜写映射。作品输出存作品，方法维护在本包。没有实片就不报运动、微表情、口型或节奏效果通过；历史试跑只证明当时实际覆盖。
''')
entry('video-prompt-authoring','将有效文字分镜或明确镜头描述编译为中文视频提示词，保留景别机位、主动与复合运镜、身体表演、声音和连续性，并组织生成任务与真实素材绑定。优先适配Seedance实际入口，不自动生成视频或替代导演分镜创作。','视频提示词制作','''## 输入与职责

接当前采用文字分镜或足够明确的镜头描述、导演保持项、原对白、真实素材及上下文。用户要求按某版出提示词已含指向稿采用和分支请求；若明确做草案则标草案。没有必要输入的部分补条件，不以小说全文冒充已确认镜头。

主责是编译和任务组织：保留源设计，去歧义，压缩重复，核实际素材与平台条件。不能因好生成把升降/弧绕改固定、复杂动作改摆拍或细微反应删掉；需要改变镜头、切点或锁定要求时回传具体取舍。

默认中文。平台确需或用户要求才转换描述语言，锁定角色台词不自动翻译。优先Seedance不代表已适配某版本；参数与能力按当前真实入口核对。

## 工作流程

1. 按[分镜接收与回传](references/分镜接收与回传.md)接段落共性、七列和复杂镜号说明，核版本、范围、采用状态与自由度，避免只复制表格漏掉共同条件。
2. 核真实文件/槽位及参考职责。按[平台适配](references/seedance-adaptation.md)核必要能力、时长、画幅和音频等；未知可交通用稿或待绑定稿，不编@标签，不强迫补图。
3. 组织镜号—生成任务映射，保持原镜头结构。一个任务多镜写真实切点；长镜分任务说明接续条件，不能暗加切镜或保证无缝。平台上限不决定镜头节奏。
4. 按[结构规范](references/structure-and-rules.md)编译六职责模块：素材边界、生成目标形式、空间初态视觉、逐镜执行、声音对白、结尾状态。可合并省略，完整规范只在此包维护。
5. 对运动保起点/触发/路线/速度转折/落点，对表演保对象/刺激/可见身体与脸部变化/反馈/末态。心理依据留块外，正文不堆AU码或肌肉论文；也不能精简成“紧张表情、电影运镜”。
6. 逐镜对照源稿，核事实、景别、机位、运动、可读细节、环境、对白、时间和切点。对跨镜/任务原句核实际发声字序及唯一范围，不能两块都说全文。交当前范围独立代码块与必要映射/缺口说明。

## 接口与修订

按[共同规范](../project-script-analysis/references/四阶段协作规范.md)与[镜头语言](../shot-language-design/SKILL.md)往返。编译丢项直接修，源设计冲突回分镜，角色动机/关键调度或揭示冲突回导演/分析，只改相关镜号/任务及邻态。

有[TIG图](../tig-blocking-map/SKILL.md)时接真实文件、身份键、镜号阶段、检查/采用/绑定状态与动作释放。颜色、逻辑别名不进入成片外观，也不是原生标签。图文关键冲突先处理，不保证文字必压过错误图。

专项情境与历史文字记录见[验收](references/acceptance-and-trial.md)。本包输出和平台适配、实际生成、用户采用、成片检验分别记录。写提示词不自动授权故事板、上传、付费或生成；作品已有主方法/格式优先，本包不覆盖其他项目默认。
''')
entry('tig-blocking-map','依据源画面或有效导演分镜，设计指定镜头与动作阶段的彩色轮廓角色站位图提示词、人物键和几何交接，按需检查真实图。用于多人位置朝向、遮挡裁切、接触和走位；图不替代分镜、不冻结后续行动，不默认生成上传。','角色站位图','''## 定位与来源

四阶段主链的可选几何辅助：导演推敲调度、分镜表达观察关系、提示词接入已核图稿。不是必经第五阶段，也不是世界精确平面图、成片关键帧或运动成功证据。

基于Tigran/TIG原版的本地适配，保留[原始附件](原始附件/tig-blocking-map.skill)与署名，不因放在自研目录而声称原方法原创。源图、制作文字及新增候选的依据要分开。

## 操作流程

1. 核本次要绘图提示词、实际出图、审图还是视频连接，核有效版本、场/镜号、动作阶段、采用状态与保持项。有源图必须实际查看才称提取。
2. 按[图稿设计](references/站位图设计与交付.md)读世界关系→相机观察→屏幕投影：人物位置、身体/头/目光方向、姿态、裁切、遮挡、持物及接触。未知身份和图外区域不猜造。
3. 选最少必要视图。运动镜头不只核首尾，还核重要遮挡、变向和显露节点；多节点不是切镜。相机升降/弧绕后重算投影，不能镜像旧图替代新视角或让人物为维持左右而移位。
4. 交完整工具中立绘图提示词与图外人物键。图内不同低饱和细轮廓区分，不画文字/字母，颜色不等于服装。A/B和MAP是逻辑名，不是原生槽位；以真实文件/绑定为准。
5. 初态图只约束对应阶段，行动发生后依有效分镜释放走位。环境/服装/身份按各自参考，辅助颜色、白底和线条不传入成片。单图不能证明路线净空、精确距离或所有角度可用。
6. 按[体系接口](references/体系接口与回查.md)回传来源/图版本、镜号阶段、真实文件状态、人物键、几何范围、释放条件、下节点及未核内容。图文关键冲突先解决；没有图也可采用充分文字完成下游。

## 联合工作与验收

[分析](../project-script-analysis/SKILL.md)交空间需求，[导演](../photoreal-drama-director/SKILL.md)交行动调度，[分镜](../shot-language-design/SKILL.md)选择具体视角/构图/运动阶段，[提示词](../video-prompt-authoring/SKILL.md)接真实几何用途与动作释放。采用、修改和证据按[共同规范](../project-script-analysis/references/四阶段协作规范.md)。

实际图查数量身份、朝向位置、裁切遮挡、接触及错误文字；真实视频另查路径、动作释放、外观污染与状态连续。只有提示词不叫出图完成，图合格不等于视频控制通过。局部改机位/站位/阶段后回查对应图和任务，不重做无关场。

保留当前任务边界，不因站位图能力自动补故事板、生成或上传，不新增费用，不要求安装别包。各包缺失时本地参考仍可独立用于该项文字工作。
''')

# Turn superseded operating summaries into precise routes, preserving source evidence.
redirects={
'shot-language-design/references/镜头设计方法.md':('分镜设计操作指南.md','总体设计流程已集中在操作指南，不再并行维护旧的逐镜决策顺序。按整段重音与距离节奏构思，再联查单镜和接口。'),
'shot-language-design/references/景别组接与段落节奏.md':('分镜设计操作指南.md','景别、镜头组、时间和整段验收读第2、3、8、9、12节。短信息镜头是主动选择，不能仅作为中景读不清后的补救。'),
'shot-language-design/references/运镜设计与执行检查.md':('运镜设计操作指南.md','基础/特殊/复合运动、路径速度和执行检查统一在本指南维护，旧层层追加的规则已被此流程替代。'),
'shot-language-design/references/分镜决策与连续性.md':('分镜设计操作指南.md','按观看任务、空间、镜头组、单镜和声画接口联合检查，先看表现力是否成立。连续性支持设计，不应成为默认固定覆盖的理由。'),
'shot-language-design/references/主体行动与表演交接.md':('../../photoreal-drama-director/references/角色表演与微表情设计操作手册.md','导演维护动机、策略和身体/面部方法，分镜负责可见渠道与镜间状态。缺同级包时仍依下述摘要完成基本设计。'),
'photoreal-drama-director/references/主体行动与角色表演设计.md':('角色表演与微表情设计操作手册.md','行动、交流、身体反馈、微表情和肌肉关系改由操作手册统一维护；旧资料的阅读范围保留在下方，不能据此称本轮重读全书。')}
for rel,(target,summary) in redirects.items():
    old=(root/rel).read_text(encoding='utf-8-sig');title=old.splitlines()[0]
    suffix=''
    for marker in ['## 来源与采用边界','## 来源与实际范围']:
        if marker in old:suffix='\n\n## 既有来源记录\n\n'+old.split(marker,1)[1].strip()+'\n';break
    extra=''
    if '主体行动与表演交接' in rel:
        extra='\n\n基本接收：人物知情、对象/目的、刺激、可见行动与身体反馈、结果及首末态。全景靠重心/方向/身体，近景可读头肩与呼吸，特写才依赖局部眼口；画外对象保位置/声源。行动列写变化，声音列写原句和聆听窗口，落幅列接持物/动作/情绪余留。只改表演时保持未受影响选择，机位无法读清关键变化时明确关联修改。'
    put(rel,title+'\n\nR2兼容入口｜2026-10-27。当前专业维护源为['+target.split('/')[-1].replace('.md','')+']('+target+')。\n\n'+summary+extra+suffix)

put('shot-language-design/references/时间与场景动态.md','''# 时间与场景动态

R2专题接口｜2026-10-27。镜长流程见[分镜操作指南](分镜设计操作指南.md)第9节，环境流程见[场景动态](场景动态设计.md)。本页不再维护“先找最短可读”的另一套优先顺序。

区分故事时间、镜头时长、生成任务和成片位置。先安排阅读、动作、台词、反馈、运动和停留的顺序/重叠，以体验成立决定预算，再用试读、预演或媒体校准。既不平均分配，也不最短优先；长短变化应形成段落节奏。只有实际测过才称实测。

持续动态、接触反馈、视差/反射变化与剧情异变分开；保住必要后果，不要求静室人为添风雨。镜头移动不是物件自行滑动，环境真实也不等于所有背景都动。
''')

# Targeted corrections in still-useful specialist references, avoiding rule stacks.
rep={
'shot-language-design/references/观看条件与情绪落地.md':[
('读不清时先调整条件，不默认增加特写或延长全段。','读不清时主动比较特写/近景、改变角度、清晰范围、停留和声音载体，选择能读到且符合节奏的实现，不把保持当前中景当优先条件。')],
'shot-language-design/references/交付分支与验收.md':[
('V0.11另核整段观看层次：','R2整段验收：'),
('## 四、行为验收情境（原清单，执行范围另见试跑记录）','## 四 行为验收情境和记录边界')],
'shot-language-design/references/导演方案接收与回查.md':[
('V0.9执行摘要，接导演—分镜接口V1.2及四阶段协作接口V1.0。','R2接收摘要，接共同协作规范V2.0与本次导演—分镜接口。')],
'video-prompt-authoring/references/分镜接收与回传.md':[
('锁定固定/连续观看须保留，不以模板替换既定机位','锁定的静态/主动运动/连续观看均须保留，不以模板或易生成偏好替换既定摄影')],
'video-prompt-authoring/references/structure-and-rules.md':[
('## 5. 推荐正文结构：六个模块','## 1 推荐正文结构 六个模块'),('### 5.1','### 1.1'),('### 5.2','### 1.2'),('## 6. 制作流程及每步的完成物','## 2 制作流程及完成物'),('## 7. 编写规范','## 3 编写规范'),
('**运镜。** 写真实可执行路径、触发、保持对象与终点，不堆推拉摇移术语。','**运镜。** 保留源稿起止景别、观看位置、真实路径、触发、速度转折和落点；升降、弧绕、希区柯克变焦或复合节点不能被简化成固定/缓推。不堆推拉摇移术语。'),
('**表演。** 可见行为与人物当下目的、刺激和反馈对应。','**表演。** 保住可见对象、刺激、行动与身体/面部变化、反馈和末态；心理依据留块外，动作和肌肉知识转为可见效果。')],
'photoreal-drama-director/references/导演与分镜交接规范.md':[
('接口V1.2｜2026-10-26。','接口R2｜2026-10-27。')],
'tig-blocking-map/references/体系接口与回查.md':[
('接口V1.0｜2026-10-26。','接口R2｜2026-10-27。')]
}
for rel,pairs in rep.items():
    text=(root/rel).read_text(encoding='utf-8-sig')
    for a,b in pairs:
        assert a in text,(rel,a);text=text.replace(a,b)
    put(rel,text)

# Ensure necessary dynamic checks are not hidden behind the entrypoint alone.
rel='tig-blocking-map/references/站位图设计与交付.md'
text=(root/rel).read_text(encoding='utf-8-sig')
text=text.replace('一图约束当前镜头/阶段；动作开始后按脚本推进，不用位置锁压过已确认行动。','一图约束当前镜头/阶段；动作开始后按脚本推进，不用位置锁压过已确认行动。复合运动还核中途遮挡、显露、转向及观察侧变化；起末图正确不证明中间路径成立。')
put(rel,text)

# Single current operating source for high-level strategy; older cases stay historical.
for rel in ['photoreal-drama-director/references/导演决策与场面设计.md','photoreal-drama-director/references/整体意图与逐场推进.md','photoreal-drama-director/references/多人空间与视听统筹.md','photoreal-drama-director/references/导演方案比较与反向验收.md','photoreal-drama-director/references/交付与验收.md','photoreal-drama-director/references/观众体验与情绪组织.md','photoreal-drama-director/references/书籍方法与选择检查.md','shot-language-design/references/摄影机与光学设计.md','shot-language-design/references/场景动态设计.md','shot-language-design/references/声音与对白设计.md','shot-language-design/references/落幅切点与承接设计.md','shot-language-design/references/空间编排与教程校验.md','video-prompt-authoring/references/acceptance-and-trial.md']:
    text=(root/rel).read_text(encoding='utf-8-sig');first,rest=text.split('\n',1)
    note='R2适用说明｜2026-10-27。当前入口和共同协作规范确定职责/范围，专业细节以本次操作手册为主；下方版本号与阅读/试跑日期标识来源历史，不是并行运行的另一套系统。\n'
    if '/acceptance-and-trial.md' in rel:note='R2验收说明｜2026-10-27。下方V0.x为历史输入和当时检查，不自动证明当前版本通过；本次完整输出及冲突情境另见本包R2联合试跑。\n'
    put(rel,first+'\n\n'+note+rest.lstrip())

# Preserve optional historical report as a clearly local provenance link in packages.
trial=root/'shot-language-design/试跑/V0.11_景别组接与主动运镜重设计.md'
txt=trial.read_text(encoding='utf-8-sig').replace('../../../../../04_项目管理/02_任务记录/2026-10-27_镜头景别与运镜系统重修.md','E:/AI漫剧/04_项目管理/02_任务记录/2026-10-27_镜头景别与运镜系统重修.md')
txt+='\n该链接为可选本机历史记录；离开本机不影响当前Skill运行。\n';trial.write_text(txt,encoding='utf-8')

# Export the same MD to a human-facing manual folder, not independently maintained copies.
manualroot=base/'02_制作方法/04_通用模板/分镜运镜与表演操作手册'
(manualroot/'MD同版导出').mkdir(parents=True,exist_ok=True)
for title,owner in [('分镜设计操作指南','shot-language-design'),('运镜设计操作指南','shot-language-design'),('角色表演与微表情设计操作手册','photoreal-drama-director')]:
    shutil.copyfile(root/owner/'references'/(title+'.md'),manualroot/'MD同版导出'/(title+'_V1.0.md'))
(manualroot/'00_从这里开始.md').write_text('''# 分镜 运镜与表演手册怎么用

先看Word阅读版中的三份手册。做一场戏时先按分镜指南组织观看，再用运镜指南选路径，并用表演手册落实人物行动与身体/眼口变化；它们协同设计，不要求固定先后填三套表。

Word和MD同版导出来自完整Skill包里的专业维护原件。不要分别修改两套内容；收到Word批注后回原件修订再导出。当前V1.0是方法发布，不表示实际媒体已经验证或用户已认可所有新设计。
''',encoding='utf-8')
(work/'changed.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2),encoding='utf-8')
print('Updated canonical files:',len(changed));print('Manual source files exported:',3)
