from pathlib import Path
import re,json,hashlib
from urllib.parse import unquote
base=Path(r'E:\AI漫剧');root=base/'02_制作方法/02_专业技能/自研Skill';work=Path(__file__).parent
names=['project-script-analysis','photoreal-drama-director','shot-language-design','video-prompt-authoring','tig-blocking-map']
result={'files':0,'markdown':0,'links':0,'broken':[],'optional_absolute':[],'active_files':[]}
for name in names:
    entry=(root/name/'SKILL.md').read_text(encoding='utf-8-sig')
    assert entry.startswith('---\n')
    front=entry.split('---',2)[1]
    assert re.search(r'^name: '+name+r'$',front,re.M)
    assert re.search(r'^description: .+',front,re.M)
    assert re.search(r'  version: "[0-9]+\.[0-9]+"',front)
    for file in sorted((root/name).rglob('*')):
        if not file.is_file():continue
        result['files']+=1
        if file.suffix!='.md':continue
        result['markdown']+=1
        if '试跑' not in file.parts:result['active_files'].append(str(file))
        for label,target in re.findall(r'\[([^\]]*)\]\(([^)]+)\)',file.read_text(encoding='utf-8-sig')):
            t=unquote(target.strip('<>').split('#')[0])
            if not t or '://' in t:continue
            result['links']+=1
            if re.match(r'^[A-Za-z]:[/\\]',t):
                result['optional_absolute'].append({'file':str(file.relative_to(root)),'target':t,'exists':Path(t).exists()})
                continue
            if not (file.parent/t).exists():result['broken'].append({'file':str(file.relative_to(root)),'target':t})
# Validate R2 SOP and Agent links separately; old encoded archive links are not needed by package runtime.
result['bridge_broken']=[]
for f in list((base/'02_制作方法/01_流程规范').rglob('*V0.2.md'))+list((base/'02_制作方法/02_专业技能/Agent职责与交接').glob('*V0.2.md'))+[base/'02_制作方法/01_流程规范/AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md']:
    for t in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8-sig')):
        t=unquote(t.split('#')[0]);
        if not t or '://' in t or re.match(r'^[A-Za-z]:',t):continue
        if not (f.parent/t).exists():result['bridge_broken'].append([str(f),t])
(work/'source-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['active_files','optional_absolute']},ensure_ascii=False))
assert not result['broken'];assert not result['bridge_broken']
