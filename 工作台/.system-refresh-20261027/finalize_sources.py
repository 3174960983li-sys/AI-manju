from pathlib import Path
import re, shutil, json, hashlib
base=Path(r'E:\AI漫剧');work=Path(__file__).parent
root=base/'02_制作方法/02_专业技能/自研Skill'
backup=base/'05_文件整理/03_停用归档/Skill历史版本/2026-10-27_五Skill全面翻新前'
trial=(work/'R2联合文字试跑.md').read_text(encoding='utf-8').replace('沿台外侧横移收至双人中景','沿台外侧斜向前移收至双人中景').replace('摄影机沿台外侧横移并收至双人中景','摄影机沿台外侧斜向前移并收至双人中景')
(work/'R2联合文字试跑.md').write_text(trial,encoding='utf-8')
trialname='R2_五Skill联合文字试跑.md'
primary=root/'project-script-analysis/试跑'/trialname
primary.parent.mkdir(exist_ok=True);primary.write_text(trial,encoding='utf-8')
for name in ['photoreal-drama-director','shot-language-design','video-prompt-authoring','tig-blocking-map']:
    file=root/name/'试跑'/trialname
    file.parent.mkdir(exist_ok=True)
    file.write_text('# R2联合文字试跑入口\n\n2026-10-27。实际输入、各阶段完整输出、两任务提示词、TIG绘图提示词、局部修改和特殊运动检查统一见[五Skill联合文字试跑](../../project-script-analysis/试跑/'+trialname+')。本包参与范围以该文为准，不将历史测试自动计作当前媒体通过。\n',encoding='utf-8')
# Explicitly route current test from runtime references rather than leave an unreachable test.
f=root/'video-prompt-authoring/references/acceptance-and-trial.md'
t=f.read_text(encoding='utf-8');t=t.replace('本次完整输出及冲突情境另见本包R2联合试跑。','本次完整输出及冲突情境另见[本包R2联合试跑](../试跑/R2_五Skill联合文字试跑.md)。');f.write_text(t,encoding='utf-8')
mapping=base/'02_制作方法/02_专业技能/通用能力映射/AI仿真人Skill组合与适配_V0.1.md'
dst=backup/'其他维护记录/AI仿真人Skill组合与适配_V0.1.md';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(mapping,dst)
t=mapping.read_text(encoding='utf-8-sig');first,rest=t.split('\n',1)
section='''

## R2本项目专业链

2026-10-27。本项目当前明确选用的专业链为[项目剧本分析](../自研Skill/project-script-analysis/SKILL.md)→[导演思维](../自研Skill/photoreal-drama-director/SKILL.md)→[镜头语言设计](../自研Skill/shot-language-design/SKILL.md)→[视频提示词制作](../自研Skill/video-prompt-authoring/SKILL.md)，[TIG](../自研Skill/tig-blocking-map/SKILL.md)为可选几何支线。当前版本与旧体系接续见[系统映射](../../01_流程规范/AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md)。

下表为其他任务的能力候选，不是要求把director-agent、film-cinedance或其格式叠加到已选R2链中。其他作品自己的方法仍有效，不因本项目更新改变其默认。此处沿用文件名V0.1以兼容既有链接，R2补充只维护本链入口，未改其他Skill。
'''
mapping.write_text(first+section+rest,encoding='utf-8')
# Publication copies: only known source files, preserve any untracked installed extras.
sync=[]
for name in ['project-script-analysis','photoreal-drama-director','shot-language-design','video-prompt-authoring','tig-blocking-map']:
    installed=Path(r'C:\Users\Administrator\.codex\skills')/name
    if not installed.exists():continue
    old=backup/'安装副本'/name
    original=backup/'自研Skill'/name
    differences=[]
    for f in old.rglob('*'):
        if f.is_file():
            rel=f.relative_to(old)
            if (original/rel).exists() and f.read_bytes()!=(original/rel).read_bytes():differences.append(str(rel))
    assert not differences,('Unknown installed edits need preservation',name,differences)
    count=0
    for f in (root/name).rglob('*'):
        if f.is_file():
            target=installed/f.relative_to(root/name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
            assert f.read_bytes()==target.read_bytes();count+=1
    sync.append({'skill':name,'files_synchronized':count,'unknown_files_deleted':0})
(work/'installed-sync.json').write_text(json.dumps(sync,ensure_ascii=False,indent=2),encoding='utf-8')
print('Trial copied; installed synchronization:',json.dumps(sync,ensure_ascii=False))
