from pathlib import Path
import json,hashlib,shutil,re,zipfile
from urllib.parse import unquote
base=Path(r'E:\AI漫剧');work=Path(__file__).parent
names=['project-script-analysis','photoreal-drama-director','shot-language-design','video-prompt-authoring','tig-blocking-map']
source=base/'02_制作方法/02_专业技能/自研Skill'
release=work/'交付内容';release.mkdir(exist_ok=True)
reportdir=base/'04_项目管理/02_任务记录';reportdir.mkdir(parents=True,exist_ok=True)
qa=json.loads((work/'manual-qa.json').read_text(encoding='utf-8'))
for item in qa:item['visual_review']='23页均已逐页查看，未见溢出、重叠、乱码或空白分页；已修正表格和镜头条目不当跨页'
(work/'manual-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
validation=json.loads((work/'source-validation.json').read_text(encoding='utf-8'))
sync=json.loads((work/'installed-sync.json').read_text(encoding='utf-8'))
assert not validation['broken'] and not validation['bridge_broken']
manuals=json.loads((work/'manual-manifest.json').read_text(encoding='utf-8'))
for m in manuals:assert hashlib.sha256(Path(m['source']).read_bytes()).hexdigest()==m['source_sha256'];assert Path(m['source']).read_bytes()==Path(m['md']).read_bytes()
# Complete canonical packages, including historical trial folders and original TIG attachment.
for name in names:
    target=release/'02_完整Skill'/name
    shutil.copytree(source/name,target,dirs_exist_ok=True)
for m in manuals:
    p=Path(m['docx']);dst=release/'01_给你阅读的Word手册'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    p=Path(m['md']);dst=release/'03_同版MD手册'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
systemdir=release/'04_系统架构与验证';systemdir.mkdir(exist_ok=True)
for filename in ['系统翻新与冲突修订报告.md','R2联合文字试跑.md']:
    shutil.copyfile(work/filename,systemdir/filename)
    shutil.copyfile(work/filename,reportdir/('2026-10-27_'+filename))
# Keep accompanying current SOP/Agent documents as reading material.
support=systemdir/'SOP与Agent配套';support.mkdir(exist_ok=True)
files=[
 base/'02_制作方法/01_流程规范/AI仿真人全流程/AI仿真人全流程SOP_通用母版_V0.2.md',
 base/'02_制作方法/01_流程规范/AI仿真人全流程/分镜与表演系统R2_使用与旧版映射.md',
 base/'02_制作方法/01_流程规范/共同基础/制作对象与交接契约_V0.1.md',
 base/'02_制作方法/02_专业技能/Agent职责与交接/AI仿真人总控Agent_V0.2.md',
 base/'02_制作方法/02_专业技能/Agent职责与交接/AI仿真人职能角色与交接_V0.2.md']
support_map={p.name:support/p.name for p in files}
# Reading exports rebase actual links to bundled files; external optional routes become explanatory text.
rebase=[]
for p in files:
    t=p.read_text(encoding='utf-8-sig')
    def relink(m):
        label,target=m.groups()
        if '://' in target or target.startswith('#'):return m.group(0)
        fn=Path(unquote(target.split('#')[0])).name
        if fn in support_map:new=fn
        elif fn=='00_从这里开始.md':
            new='../../00_先读我.md'
        elif fn=='SKILL.md':
            match=re.search(r'(project-script-analysis|photoreal-drama-director|shot-language-design|video-prompt-authoring|tig-blocking-map)',target)
            if match:new='../../02_完整Skill/'+match.group(1)+'/SKILL.md'
            else:rebase.append([p.name,target,'optional-local-source']);return label+'（可选本机来源，原路径 '+target+'）'
        else:rebase.append([p.name,target,'optional-local-source']);return label+'（可选本机来源，原路径 '+target+'）'
        rebase.append([p.name,target,new]);return '['+label+']('+new+')'
    (support/p.name).write_text(re.sub(r'\[([^\]]+)\]\(([^)]+)\)',relink,t),encoding='utf-8')
(systemdir/'配套阅读稿链接映射.json').write_text(json.dumps(rebase,ensure_ascii=False,indent=2),encoding='utf-8')
intro='''# 从这里开始

本包是2026年10月27日R2版分镜、运镜与表演系统交付，包含三份Word手册、同版MD、五个完整Skill及架构/冲突/试跑记录。

## 先看什么

1. 打开“01_给你阅读的Word手册”。先看分镜指南，再按正在设计的问题查运镜或表演手册。不是要求先填三套表。
2. 要知道为什么改，打开“04_系统架构与验证/系统翻新与冲突修订报告.md”，其中列14项冲突/缺口及处理。
3. 要看完整应用，读“04_系统架构与验证/R2联合文字试跑.md”，含同一场景的四阶段输出、TIG绘图提示词、两个视频提示词及特殊运动描述。
4. “02_完整Skill”是供AI读取的完整包，各包从SKILL.md进入，references是专业方法，试跑是历史与本轮证据；TIG原始附件只供来源追溯，使用入口是本地适配版SKILL.md。

## 版本和维护

项目剧本分析2.0、导演思维1.0、镜头语言设计1.0、视频提示词制作1.0、TIG3.0。保留四阶段主链，TIG按需使用，不新增必经审批。

专业原件在E:/AI漫剧/02_制作方法/02_专业技能/自研Skill。手册MD与Word由专业原件同版导出，不分别维护两套内容；收到Word批注先回原件再导出。系统更新不自动改造在制作品。

本轮只同步发现的既有项目剧本分析安装副本，其余四包未新安装。解压、保存和安装是不同操作；本包没有安装器，不会自动修改其他电脑。需要迁移时保留各包完整目录，同级放置可保持跨包相对导航。

## 文件与验证范围

本包不含作品集、原始书籍、视频、内部渲染PDF或检查PNG。Skill里指向E盘知识笔记的链接为可选本机来源，离开本机可能失效；运行所需专业方法已随包，不能把这些来源链接当必须先读的输入。

Word已实际渲染并逐页看图；方法已用完整文字链自查，未做真实平台、配音、动态视频和观众效果验证。手册质量和新版创作效果仍可继续通过项目反馈迭代，不能把本次结构检查称为成片通过。

详细文件清单与SHA256见交付文件清单.json，核查范围见04_系统架构与验证/交付验收记录.md。
'''
(release/'00_先读我.md').write_text(intro,encoding='utf-8')
audit='''# 交付验收记录

2026-10-27｜R2文字系统发布检查。相同作者执行内容自检，不称独立评审。

## 需求逐项核对

| 用户要求 | 当前实际证据 | 结论与范围 |
|---|---|---|
| 全面翻新旧/新系统并查冲突 | 五包当前入口与活动参考、SOP/Agent、共同规范V2.0、14项冲突报告、旧栏迁移说明 | 本次主链与相关旧规则已修订，旧只读历史原件保留；不冒称旧制片/资产46步全体已实测 |
| 分镜操作指南 | Word7页及同版MD；12节和来源说明；景别/机位/视角/主体/构图/光学/组接/时间/七列与完整例 | 实际文件存在、正文和表格内容对应、逐页视觉检查 |
| 运镜操作指南 | Word8页及同版MD；11节和来源说明；推拉摇移跟绕升降、特殊效果、希区柯克详解、复合节点与完整例 | 实际文件存在、正文和表格内容对应、逐页视觉检查 |
| 表演与微表情操作手册 | Word8页及同版MD；14节和来源说明；动机/刺激/反馈、身体支撑受力、呼吸眼口/肌肉、形成消退、笑哭与例 | 实际文件存在、机制边界有来源，未宣称FACS培训或模型控制验证 |
| 检查底层架构是否需改 | 共同规范和系统报告 | 保留四阶段，重构决策顺序、维护源、自由度与修改传播，未增自动Agent |
| 系统性优化相关Skill | 五完整目录的SKILL.md及references/既有agents/历史试跑/TIG附件 | 文件清单逐项比对源包，运行链接临时解包核对 |
| 优化结果与手册一起打包 | 本ZIP、文件清单、解包比较 | ZIP CRC及解包SHA256逐文件核对，具体结果另存包外校验记录 |

## 实际做了哪些检查

- 五包入口name/description/version格式及UTF-8读取；128处本地链接无断裂（绝对本机可选来源另列）。PyYAML缺失，未运行官方quick_validate.py，不将专项检查称作官方校验通过。
- 同一独立场景实际产出分析、导演、六镜七列表、TIG绘图提示词、G01/G02完整正文；人工核原句、未触状态、一次内部声、运动保真和末态。另写特殊运动和九项修改/冲突情境的具体处理。
- Word通过本机Microsoft Word导出，再渲染图像查看全部23页；修正表格/镜头条目不当跨页。正文与表格内容逐项对应MD，三手册MD导出与维护源字节一致。内部PDF/PNG不随包。
- 既有安装副本project-script-analysis同步12个已管理文件并逐项核字节；未删未知文件，未安装其他四包。
- 修改前五包59文件完整备份并校验，SOP/Agent同时备份。原书和作品未更改；三份旧知识MD只加历史状态说明，未把旧.doc文件冒称已更新。

## 分发检查与未验证范围

包内Skill完整文件与维护源逐字节一致。跨包运行链接在临时解包目录核对，不依赖原E盘；可选E盘来源明确排除于运行依赖。配套SOP/Agent是阅读导出，链接改为包内对应文件，未随包的可选本机来源改为说明；链接映射单列，不伪称这些导出与维护源字节相同。

结构、链接、哈希不能证明镜头好看；本次没有真实图像/视频、平台提交、语速实测、配音/口型听验和观众测试。后续实际结果按来源、表演/场面、摄影实现、编译、素材或剪辑定位，不能把所有失败都归为提示词。
'''
(systemdir/'交付验收记录.md').write_text(audit,encoding='utf-8')
shutil.copyfile(systemdir/'交付验收记录.md',reportdir/'2026-10-27_R2交付验收记录.md')
shutil.copyfile(source/'project-script-analysis/references/四阶段协作规范.md',systemdir/'四阶段协作规范_V2.0.md')
# Mechanism/content checks supplement, rather than substitute, the author's actual review.
trialtext=(work/'R2联合文字试跑.md').read_text(encoding='utf-8')
blocks=re.findall(r'```text\n(.*?)\n```',trialtext,re.S)
assert len(blocks)==2
assert '你听到了吗？' not in blocks[0] and blocks[1].count('你听到了吗？')==1 and blocks[1].count('我没碰它。')==1
assert all(x in blocks[1] for x in ['短推近','短横摇','后拉并小幅弧移','尚未接触'])
assert 'T-S01' in blocks[0] and 'T-S03' in blocks[0] and 'T-S04' in blocks[1] and 'T-S06' in blocks[1]
# Every relative link in complete Skills and accompanying exports must resolve after extraction.
broken=[];optional=[];linkcount=0
for f in release.rglob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8-sig')):
        t=unquote(target.strip('<>').split('#')[0])
        if not t or '://' in t:continue
        if re.match(r'^[A-Za-z]:[/\\]',t):optional.append({'file':str(f.relative_to(release)),'local_source':t});continue
        linkcount+=1
        if not (f.parent/t).exists():broken.append([str(f.relative_to(release)),t])
assert not broken,broken
(systemdir/'可选本机来源链接.json').write_text(json.dumps(optional,ensure_ascii=False,indent=2),encoding='utf-8')
# Explicit source/package identity for complete Skill folders.
skills_identical=0
for name in names:
    srcfiles={str(p.relative_to(source/name)):p.read_bytes() for p in (source/name).rglob('*') if p.is_file()}
    dstfiles={str(p.relative_to(release/'02_完整Skill'/name)):p.read_bytes() for p in (release/'02_完整Skill'/name).rglob('*') if p.is_file()}
    assert srcfiles==dstfiles;skills_identical+=len(srcfiles)
manifest={str(f.relative_to(release)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(release.rglob('*')) if f.is_file()}
(release/'交付文件清单.json').write_text(json.dumps({'release':'R2-2026-10-27','sha256':manifest,'complete_skill_files':skills_identical,'relative_links_resolved':linkcount,'optional_local_source_links':len(optional)},ensure_ascii=False,indent=2),encoding='utf-8')
zipout=reportdir/'2026-10-27_分镜运镜表演系统R2_完整交付.zip';assert not zipout.exists()
with zipfile.ZipFile(zipout,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
    for f in sorted(release.rglob('*')):
        if f.is_file():z.write(f,arcname='分镜运镜表演系统R2/'+str(f.relative_to(release)).replace('\\','/'))
unpack=work/'解包校验';unpack.mkdir(exist_ok=True)
with zipfile.ZipFile(zipout) as z:
    assert z.testzip() is None
    assert all('..' not in Path(n).parts and not Path(n).is_absolute() for n in z.namelist())
    z.extractall(unpack)
extracted=unpack/'分镜运镜表演系统R2'
packfiles={str(f.relative_to(release)):hashlib.sha256(f.read_bytes()).hexdigest() for f in release.rglob('*') if f.is_file()}
unpackedfiles={str(f.relative_to(extracted)):hashlib.sha256(f.read_bytes()).hexdigest() for f in extracted.rglob('*') if f.is_file()}
assert packfiles==unpackedfiles
for f in (extracted/'02_完整Skill').rglob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf-8-sig')):
        t=unquote(target.split('#')[0])
        if not t or '://' in t or re.match(r'^[A-Za-z]:',t):continue
        assert (f.parent/t).exists(),(str(f),t)
proof={'zip':str(zipout),'zip_sha256':hashlib.sha256(zipout.read_bytes()).hexdigest(),'bytes':zipout.stat().st_size,'files':len(packfiles),'skill_files_identical':skills_identical,'crc':'passed','extracted_sha256':'all matched','relative_links':linkcount,'optional_local_links':len(optional),'manual_pages':[q['pages'] for q in qa],'installed_sync':sync}
(work/'release-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
(reportdir/'2026-10-27_R2压缩包校验.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(proof,ensure_ascii=False,indent=2))
