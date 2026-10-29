# AI仿真人Skill组合与适配 V0.1

## R2本项目专业链

2026-10-27。本项目当前明确选用的专业链为[项目剧本分析](../自研Skill/project-script-analysis/SKILL.md)→[导演思维](../自研Skill/photoreal-drama-director/SKILL.md)→[镜头语言设计](../自研Skill/shot-language-design/SKILL.md)→[视频提示词制作](../自研Skill/video-prompt-authoring/SKILL.md)，[TIG](../自研Skill/tig-blocking-map/SKILL.md)为可选几何支线。当前版本与旧体系接续见[系统映射](../../01_流程规范/AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md)。

下表为其他任务的能力候选，不是要求把director-agent、film-cinedance或其格式叠加到已选R2链中。其他作品自己的方法仍有效，不因本项目更新改变其默认。此处沿用文件名V0.1以兼容既有链接，R2补充只维护本链入口，未改其他Skill。

本表是选用建议，不是全部安装依赖，也不意味着每个Skill都已通过生产验收。优先当前项目已确认的方法；本机Skill在 `C:\Users\Administrator\.codex\skills`，调用前读取当次实际SKILL.md。未提供相应能力时，按通用SOP完成可完成部分，不伪称调用。

当前新增候选：[ai-photoreal-drama-production](../研发候选/ai-photoreal-drama-production/SKILL.md)。它负责通用流程选择与交接，不覆盖下面的专业能力。

| 环节 | 可选能力 | 适配要求／边界 |
| --- | --- | --- |
| 原著与开发 | short-drama-novel-analyze；short-drama-develop | 原著分析与开发契约分开；只做剧情短片时按实际需要裁剪系列字段，不强制写完整长剧地图 |
| 剧本 | short-drama-write；film-screenplay | 选一个主流程，保留原文与有效版本；film系列的阶段路由前提须满足，不能无视其触发条件直接套用 |
| 导演与风格 | director-agent；style-cinematography-director | 以当前任务选择。纯风格提取不夹带新剧情、不自动生成图片；固定风格与可变光线、景深、构图分别记录 |
| 仿真人角色 | realistic-human-character-design | 正文已核读：其9:16四视图、新身份redesign、差异化数量等属于原Skill方法；不设为通用强制值。保留身份的修订不能调用成另造新人；按当前用户任务选择或适配，不能暗中改变原Skill |
| 分镜 | 当前作品已选Skill；否则按任务选适用导演分镜Skill | 五列、七栏、九宫格各有用途，不叠加输出；文字任务止于文字。现有项目特定默认保持独立，本表不覆盖 |
| 视频提示词 | film-cinedance 或当前项目已选专业Skill | film-cinedance正文已核读：以素材绑定、动作与镜头时间、音频为核心，只交提示词；其默认保存目录和阶段停点按当前项目授权处理，不迁移用户现有工程 |
| 实际视频制作 | produce-ai-video | 正文已核读：需要真实可播放输出及声画审查。其每段7—8有效镜头倾向不是通用底线；用户确认单镜头时保留，不以调用为名强改导演方案 |
| 原片审查／组接 | review-and-assemble；short-drama-review | 按实际输入契约和审查范围使用。片段选用、编辑计划和真实导出分开；无实际导出不宣称已完成成片 |
| 接收与路由 | 新候选总控；ai-film-router用于其film系列任务 | ai-film-router正文已核读：可从现有材料进入，覆盖自身阶段链；不把它的逐阶段停点和目录设为所有仿真人任务的统一要求 |

“正文已核读”表示本轮为解决具体冲突读取过实际入口，不是完成全包逐文件审查。其他行是能力候选，使用时仍需读实际规则；本轮没有逐一调用或证明其有效性。

## 冲突处理顺序

用户当前明确要求与有效授权 → 当前作品有效约定／确认输入 → 当次选定的专业方法 → 通用母版默认。先判断冲突是否只是适用范围不同，不把两套互斥格式混在一份产物里。若所选Skill无法满足任务且需改变其核心意图，改选合适方法或明确适配方案，不假装原样遵循。

## 维护方式

本表只维护能力、边界与选择理由；专业方法正文在其自身Skill中。新增通用规则先改权威SOP，候选Skill引用的发布快照再同步，避免同时维护两份不一致的正文。全局安装、原Skill修改和在制作品升级不属于本轮交付。
