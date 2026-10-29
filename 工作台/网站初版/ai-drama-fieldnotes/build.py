"""Build the personal site using only Python's standard library.
Content lives in content/library.json; assets live in assets/. No remote data at build time.
"""
from pathlib import Path
import json, html, re, shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
entries = json.loads((ROOT / 'content/library.json').read_text(encoding='utf-8'))
by_id = {e['id']: e for e in entries}
assert len(by_id) == len(entries), 'Duplicate content IDs'
for e in entries:
    assert re.fullmatch(r'[a-z0-9-]+', e['id'])
    assert all(i in by_id for i in e['related']), 'Broken related entry'

def esc(s): return html.escape(str(s), quote=True)
def url(e): return '/read/' + e['id'] + '.html'
def tagged(e): return ''.join(f'<span class="tag">{esc(t)}</span>' for t in e['tags'])
def flatten(e):
    return ' '.join(' '.join(v) if isinstance(v, list) else v for _, v in e['body'])
def minutes(e): return max(1, round(len(flatten(e))/400))

search_index = [{'title':e['title'], 'category':e['category'], 'summary':e['summary'], 'text':flatten(e), 'tags':e['tags'], 'url':url(e)} for e in entries]
search_json = json.dumps(search_index,ensure_ascii=False).replace('<',r'\u003c')
nav_items = [('home','/','首页'),('works','/works.html','作品'),('notes','/notes.html','手记'),('workflow','/workflow.html','制作 SOP'),('toolbox','/toolbox.html','工具箱'),('about','/about.html','关于')]

def shell(title, content, active='home', description='AI 短剧创作、制作流程与实践记录。', extra=''):
    nav = ''.join(f'<a href="{href}" '+('aria-current="page"' if key==active else '')+f'>{label}</a>' for key,href,label in nav_items)
    return f'''<!doctype html>
<html lang="zh-CN" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · 造片手记</title><meta name="description" content="{esc(description)}"><meta name="color-scheme" content="dark light"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/style.css"><script src="/theme.js"></script><script src="/app.js" defer></script>{extra}</head>
<body><a class="skip" href="#main">跳转到内容</a><header class="site-header"><div class="header-inner"><a class="brand" href="/" aria-label="造片手记首页"><span class="brand-mark" aria-hidden="true">f.</span><span>造片手记<small>FRAME & FIELDNOTES</small></span></a><nav aria-label="主导航">{nav}</nav><div class="header-actions"><button class="search-open" aria-label="搜索全站"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6.5"/><path d="m15 15 5 5"/></svg><span>搜索</span><kbd>/</kbd></button><button class="theme-toggle icon-button" aria-label="切换明暗主题" title="切换明暗主题">◐</button></div></div></header>
<main id="main">{content}</main><footer class="wrap footer"><div><a href="/" class="footer-brand">造片手记<span>↗</span></a><p>从一个镜头开始，留下每一次探索。</p></div><div><a href="/works.html">作品档案</a><a href="/notes.html">全部手记</a><a href="/about.html">关于本站</a><span>© 2026 · 个人创作档案</span></div></footer>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="search-head"><h2 id="search-title">搜索创作档案</h2><button data-close-search aria-label="关闭搜索">×</button></div><label class="search-field"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6.5"/><path d="m15 15 5 5"/></svg><input id="global-search" type="search" placeholder="搜索手记、SOP、Skill 或正文关键词" autocomplete="off" aria-label="全站搜索关键词"></label><p class="search-hint" id="search-count" role="status">在手记、制作 SOP 与工具箱中搜索</p><div id="search-results"></div><div class="search-foot">支持标题、标签与正文搜索 <span>ESC 关闭</span></div></dialog><div id="toast" role="status"></div><script id="search-index" type="application/json">{search_json}</script></body></html>'''

def heading(kicker,title,desc):
    return f'<div class="page-heading wrap"><div class="eyebrow">{kicker}</div><h1>{title}</h1><p>{desc}</p></div>'

def note_row(e):
    hay = ' '.join([e['title'],e['summary'],e['category'],*e['tags'],flatten(e)]).lower()
    return f'''<article class="note-row" data-category="{esc(e['category'])}" data-haystack="{esc(hay)}"><div class="note-date">{e['updated'].replace('-','.')}<span>示例手记</span></div><div class="note-main"><div class="entry-meta"><span>{esc(e['category'])}</span><i>·</i><span>约 {minutes(e)} 分钟</span></div><h3><a href="{url(e)}">{esc(e['title'])}<span>↗</span></a></h3><p>{esc(e['summary'])}</p><div class="tags">{tagged(e)}</div></div></article>'''

def resource_card(e):
    return f'''<article class="resource-card"><div class="resource-kicker"><span>{e['category'].upper()}</span><span>示例 / v0.1</span></div><div class="tool-glyph" aria-hidden="true">{'↳' if e['id']=='agent' else '✳' if e['id']=='skill' else '≡'}</div><h3><a href="{url(e)}">{esc(e['title'])}</a></h3><p>{esc(e['summary'])}</p><div class="tags">{tagged(e)}</div><a class="resource-bottom" href="{url(e)}">阅读与下载 <span>↗</span></a></article>'''

def process_list():
    stages=[e for e in entries if e['type']=='sop']
    descriptions=['故事、人物与场景','角色、场景与美术','调度、动作与连续性','节奏、声音与归档']
    return ''.join(f'<a class="process-row" href="{url(e)}"><span class="step-num">0{i+1}</span><div><h3>{esc(e["title"])}</h3><p>{descriptions[i] if i < len(descriptions) else esc(e["summary"])}</p></div><span>↗</span></a>' for i,e in enumerate(stages))

def write(path, content):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')

home='''<section class="home-intro wrap"><div class="eyebrow"><span class="status-dot"></span> 独立创作 · AI 短剧实践档案</div><div class="intro-columns"><h1>让想象成片，<br>让经验<span>有迹可循。</span></h1><div class="intro-side"><p>这里是一个创作者的工作现场。<br>收藏灵感，拆解方法，记录失败，<br>也分享那些终于完成的镜头。</p><a class="button button-fill" href="/notes.html">翻开创作手记 <span>↗</span></a></div></div></section>
<section class="cinema wrap" aria-label="工作室概念视觉，非个人作品"><div class="cinema-scene" aria-hidden="true"><div class="scene-orbit"></div><div class="scene-door"></div><div class="scene-light"></div><div class="scene-ground"></div><div class="scene-frame"></div></div><div class="cinema-top"><span>THE PROCESS BEHIND THE FRAME</span><span>概念视觉 / 非个人作品</span></div><div class="cinema-bottom"><div><span class="eyebrow">A WORK IN PROGRESS</span><h2>每个好镜头，<br>都有一段幕后。</h2></div><a href="/works.html" class="round-link" aria-label="进入作品档案">↗</a></div><div class="film-edge"><span>01 / IDEATE</span><span>02 / CREATE</span><span>03 / REFLECT</span><span>04 / REPEAT</span></div></section>
<div class="entry-paths wrap"><a href="/works.html"><span>01</span><strong>看作品</strong><small>成片与幕后过程</small><b>↗</b></a><a href="/notes.html"><span>02</span><strong>读手记</strong><small>学习与问题复盘</small><b>↗</b></a><a href="/workflow.html"><span>03</span><strong>找方法</strong><small>SOP 与可复用工具</small><b>↗</b></a></div>
<section class="wrap home-journal section"><div class="journal-main"><div class="section-heading"><div><span class="eyebrow">FIELD NOTES / 01</span><h2>创作中的思考</h2></div><a href="/notes.html" class="text-link">全部手记 ↗</a></div><p class="demo-note">以下为阅读结构示例，等待加入真实制作记录。</p>'''+''.join(note_row(e) for e in entries if e['type']=='note')+'''</div><aside class="process-aside"><span class="eyebrow">THE WORKFLOW / 02</span><h2>从故事到成片</h2><p>每一步，都有输入、输出和检查。</p>'''+process_list()+'''<a href="/workflow.html" class="text-link">打开制作 SOP ↗</a><div class="aside-note">一份持续修订的制作手册。<br>框架示例，随实践生长。</div></aside></section>
<section class="wrap section"><div class="section-heading"><div><span class="eyebrow">THE TOOLBOX / 03</span><h2>把方法变成可复用的工具</h2></div><a href="/toolbox.html" class="text-link">进入工具箱 ↗</a></div><div class="resource-grid">'''+''.join(resource_card(e) for e in entries if e['type']=='resource')+'''</div></section><section class="wrap closing"><span class="eyebrow">KEEP MAKING. KEEP LEARNING.</span><h2>完成一个作品，<br>也留下通往下一个作品的方法。</h2><a href="/about.html" class="text-link">关于这份创作档案 ↗</a></section>'''
write('index.html',shell('让想象成片，让经验有迹可循',home))

notes=heading('THE JOURNAL / 创作手记','在实践中，慢慢想明白。','学习笔记、制作经验与问题复盘。记录方法，也记录方法成立的条件。')+'''<section class="wrap library-layout"><aside class="library-aside"><div class="eyebrow">按内容浏览</div><div class="category-filter" role="group" aria-label="手记分类">'''+''.join(f'<button data-filter="{c}" aria-pressed="{str(c=="全部").lower()}">{c}<span>{3 if c=="全部" else 1}</span></button>' for c in ['全部','学习笔记','制作经验','问题复盘'])+'''</div><div class="aside-note"><strong>使用这份档案</strong><p>先读问题与判断，再看修订过程。文章末尾可继续查看关联的 SOP 和工具。</p></div><a class="text-link" href="/workflow.html">按制作阶段查找 ↗</a></aside><div><div class="list-toolbar"><label><span>⌕</span><input id="note-search" type="search" aria-label="搜索手记" placeholder="搜索标题、标签或正文…"></label><span id="note-count" role="status">3 篇示例手记</span></div><div class="note-list">'''+''.join(note_row(e) for e in entries if e['type']=='note')+'''</div><div class="empty-search" hidden><h3>还没有找到这条记录。</h3><p>换一个关键词，或清除当前筛选。</p><button class="button" id="reset-notes">清除筛选</button></div></div></section>'''
write('notes.html',shell('创作手记',notes,'notes'))

workflow=heading('THE WORKFLOW / 制作手册','让下一次创作，有路可循。','从故事开发到成片交付。每个环节写清输入、输出与检查标准。')+'''<section class="wrap workflow-layout"><aside><div class="eyebrow">制作顺序</div>'''+process_list()+'''<div class="aside-note">当前为流程框架示例。<br>进入实际项目后，再细化版本、资产与负责人。</div></aside><div>'''+''.join(f'''<article class="stage-card"><div class="stage-title"><span>0{i+1}</span><h2><a href="{url(e)}">{esc(e['title'])}</a></h2><a href="{url(e)}" aria-label="阅读{e['title']}">↗</a></div><dl><dt>输入</dt><dd>{esc(e['body'][1][1])}</dd><dt>输出</dt><dd>{esc(e['body'][3][1])}</dd><dt>检查</dt><dd>{esc(e['body'][5][1])}</dd></dl><a href="{url(e)}" class="text-link">阅读环节说明与交接模板 ↗</a></article>''' for i,e in enumerate([e for e in entries if e['type']=='sop']))+'''</div></section>'''
write('workflow.html',shell('制作 SOP',workflow,'workflow'))

toolbox=heading('THE TOOLBOX / 方法工具箱','把反复有效的方法，留在手边。','Agent 定义协作职责，Skill 承载专项方法，模板帮助你留下完整记录。')+'<section class="wrap"><div class="resource-grid">'+''.join(resource_card(e) for e in entries if e['type']=='resource')+'''</div><div class="toolbox-note"><span class="eyebrow">HOW TO USE</span><h2>先了解边界，再带入项目。</h2><div class="three-columns"><div><span>01</span><h3>阅读适用范围</h3><p>确认任务、输入材料与预期交付。</p></div><div><span>02</span><h3>下载并调整</h3><p>按当前项目改写模板与检查条件。</p></div><div><span>03</span><h3>留下验证记录</h3><p>记录结果与限制，再决定是否复用。</p></div></div><p class="muted">当前内容为设计与模板示例。Agent 尚未接入在线运行。</p></div></section>'''
write('toolbox.html',shell('Agent、Skill 与模板',toolbox,'toolbox'))

works=heading('THE WORK / 作品档案','一个成片，也是一段探索。','这里将收藏完成的作品，以及故事、镜头和制作选择背后的过程。')+'''<section class="wrap"><div class="work-empty"><div class="work-empty-art" aria-hidden="true"><div class="film-window">01<span>THE NEXT FRAME</span></div></div><div><span class="eyebrow">作品整理中</span><h2>为第一部作品，<br>留一个完整的位置。</h2><p>真实成片尚未导入。作品档案将同时展示视频、你的制作职责、关键方法与问题复盘。</p><a href="/read/project-template.html" class="button">查看作品归档模板 <span>↗</span></a></div></div><div class="section-heading section"><div><span class="eyebrow">BEYOND THE FINAL CUT</span><h2>一个作品档案会包含什么</h2></div></div><div class="three-columns case-structure"><div><span>01 / WATCH</span><h3>观看成果</h3><p>成片、封面、剧情简介与作品规格。</p></div><div><span>02 / UNDERSTAND</span><h3>了解过程</h3><p>制作职责、创作意图与关键决策。</p></div><div><span>03 / LEARN</span><h3>带走方法</h3><p>关联 SOP、工具与经过验证的复盘。</p></div></div></section>'''
write('works.html',shell('作品档案',works,'works'))

about=heading('BEHIND THE FRAMES / 关于','记录一个创作者的成长。','在 AI 短剧的制作现场，把一次次尝试积累成自己的方法。')+'''<section class="wrap about-layout"><div class="about-monogram" aria-hidden="true">造<br>片<span>FRAME & FIELDNOTES</span></div><div class="about-prose"><h2>这里，收藏作品与过程。</h2><p>这个网站用来积累 AI 短剧学习内容，整理 SOP、Agent 与 Skill，分享制作经验、遇到的问题和对应的解决办法。</p><p>希望每次制作留下的，不只有一个视频，还有下一次能用上的经验。网站以作品、手记与方法三条线组织内容，让结果与过程互相连接。</p><h2>从这里开始</h2><a class="about-link" href="/works.html">看成片与制作过程 <span>作品档案 ↗</span></a><a class="about-link" href="/notes.html">读学习记录与问题复盘 <span>创作手记 ↗</span></a><a class="about-link" href="/toolbox.html">找可复用的方法 <span>工具箱 ↗</span></a><div class="aside-note">「造片手记」为暂定站名。个人姓名、经历、照片与联系方式尚未填写；当前手记与方法内容已标明示例状态。</div></div></section>'''
write('about.html',shell('关于',about,'about'))

def md_content(e):
    s=f'# {e["title"]}\n\n{e["status"]}\n\n'
    for tag,value in e['body']:
        if tag=='h3': s+='## '+value+'\n\n'
        elif tag in ('ul','ol'):s+='\n'.join((f'{i+1}. ' if tag=='ol' else '- ')+v for i,v in enumerate(value))+'\n\n'
        elif tag=='pre':s+='```text\n'+value+'\n```\n\n'
        else:s+=value+'\n\n'
    return s

for e in entries:
    active={'note':'notes','sop':'workflow','resource':'toolbox','project':'works'}[e['type']]
    parent=next((u,l) for k,u,l in nav_items if k==active)
    body='';toc=[]
    for idx,(tag,value) in enumerate(e['body']):
        if tag=='h3':
            anchor=f'section-{idx}';toc.append((anchor,value));body+=f'<h2 id="{anchor}">{esc(value)}<a href="#{anchor}" class="heading-anchor" aria-label="链接到{esc(value)}">#</a></h2>'
        elif tag in ('ul','ol'):body+=f'<{tag}>'+''.join(f'<li>{esc(v)}</li>' for v in value)+f'</{tag}>'
        elif tag=='pre':body+=f'<div class="code-block"><div>可编辑模板<button class="copy-code">复制</button></div><pre><code>{esc(value)}</code></pre></div>'
        else:body+=f'<p>{esc(value)}</p>'
    relations=''.join(f'<a class="related-entry" href="{url(by_id[i])}"><small>{by_id[i]["category"]}</small><span>{esc(by_id[i]["title"])} ↗</span></a>' for i in e['related'])
    backlinks=[other for other in entries if e['id'] in other['related']]
    backlink_html=''.join(f'<a href="{url(other)}">{esc(other["title"])} ↗</a>' for other in backlinks)
    content=f'''<div class="reading-progress" aria-hidden="true"></div><div class="wrap breadcrumb"><a href="/">首页</a><span>/</span><a href="{parent[0]}">{parent[1]}</a><span>/</span><span>{esc(e['category'])}</span></div><div class="wrap reading-layout"><aside class="reading-nav"><a href="{parent[0]}" class="back-link">← 返回{parent[1]}</a><div class="reading-info"><span class="eyebrow">阅读档案</span><dl><dt>内容类型</dt><dd>{e['category']}</dd><dt>制作阶段</dt><dd>{e['stage']}</dd><dt>示例更新</dt><dd>{e['updated']}</dd><dt>预计阅读</dt><dd>约 {minutes(e)} 分钟</dd></dl><div class="tags">{tagged(e)}</div></div></aside><article class="reading-article"><div class="eyebrow">{e['category']} / FIELDNOTES</div><h1>{esc(e['title'])}</h1><p class="article-lead">{esc(e['summary'])}</p><div class="article-status"><span class="status-dot"></span>{esc(e['status'])}</div><div class="mobile-toc"><details><summary>本文目录</summary>{''.join(f'<a href="#{a}">{esc(t)}</a>' for a,t in toc)}</details></div><div class="prose">{body}</div><div class="article-actions"><a class="button button-fill" download href="/downloads/{e['id']}.md">下载 Markdown ↓</a><button class="button copy-link">复制文章链接</button></div><section class="related-section"><span class="eyebrow">CONTINUE EXPLORING</span><h2>沿着这个问题，继续阅读</h2><div>{relations}</div></section></article><aside class="reading-toc"><div class="sticky-toc"><span class="eyebrow">本文目录</span><nav aria-label="本文目录">{''.join(f'<a href="#{a}">{esc(t)}</a>' for a,t in toc)}</nav>{'<div class="backlinks"><span class="eyebrow">提到这篇内容</span>'+backlink_html+'</div>' if backlinks else ''}</div></aside></div>'''
    write('read/'+e['id']+'.html',shell(e['title'],content,active,e['summary']))
    write('downloads/'+e['id']+'.md',md_content(e))

write('404.html',shell('页面未找到',heading('404 / MISSING FRAME','这一帧，暂时不在这里。','可以返回首页，或搜索你要找的手记。')+'<div class="wrap"><a class="button button-fill" href="/">返回首页 ↗</a></div>'))
for asset in ['style.css','app.js','theme.js','favicon.svg']:
    shutil.copyfile(ROOT/'assets'/asset,OUT/asset)
print(f'Built {len(list(OUT.rglob("*.html")))} HTML pages, {len(entries)} content entries and Markdown downloads.')
