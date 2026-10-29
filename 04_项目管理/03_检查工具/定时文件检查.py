"""Local inventory and review aid. scan never moves/deletes production files.

Stdlib only. Move/restore helpers are for reviewed actions and isolated tests;
there is deliberately no delete command or unattended apply CLI.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
from urllib.parse import unquote

TZ = timezone(timedelta(hours=8))
ROOT = Path(r'E:\AI漫剧')
WORK = Path(r'E:\MoveFile\File\ChatGPT\AI漫剧SOP、SKILL与提示词迭代')
ARCHIVE_NAME = '05_文件整理/03_停用归档'
TEXT = {'.md', '.txt', '.json', '.csv', '.yaml', '.yml', '.py', '.ps1', '.toml', '.html'}
PROTECTED_AREAS = {'01_作品项目', '03_参考资料'}
ALLOWED_AREAS = {'02_制作方法', '04_项目管理'}
HISTORY_WORDS = {'历史版本', '管理入口历史', '盘点快照', '文件整理记录', '旧版'}


def now():
    return datetime.now(TZ).isoformat(timespec='seconds')


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def reparse(p):
    return p.is_symlink() or bool(getattr(p.lstat(), 'st_file_attributes', 0) & 1024)


def contained(p, parent):
    return p.resolve().is_relative_to(parent.resolve())


def protected(p, root, work):
    base = work if contained(p, work) else root
    if not contained(p, base):
        return True
    rel = p.relative_to(base)
    if base == root and rel.parts[0] in PROTECTED_AREAS:
        return True
    if base == root and rel.parts[:2] == ('02_制作方法', '02_专业技能'):
        return True
    if p.suffix.lower() not in {'.md', '.txt'} or p.name in {'AGENTS.md', 'SKILL.md'}:
        return True
    if base == root and rel.parts[0] not in ALLOWED_AREAS:
        return True
    return any((parent / 'SKILL.md').exists() for parent in [p.parent, *p.parents] if contained(parent, base))


def historical(p):
    return ('03_停用归档' in p.parts or '99_停用与待确认' in p.parts or bool(set(p.parts) & HISTORY_WORDS)
            or any(part.startswith('管理记录备份') for part in p.parts))


def explicit_retired(text):
    # A status line, not a filename, age, prose example, or generic policy table.
    return bool(re.search(r'^(?:状态|使用状态)[：:]\s*(?:已停用|已废弃|已退役|已被[^\n]{1,60}替代)(?:[。；，\s]|$)', text[:2000], re.M))


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, json.dumps({'pid': os.getpid(), 'started': now()}).encode())
        yield
    finally:
        os.close(fd)
        path.unlink()


def atomic_json(path, data):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


def inventory(roots, excluded):
    rows, errors, skipped = {}, [], []
    for root in roots:
        if not root.is_dir() or reparse(root):
            errors.append(f'根目录不可扫描或为联接: {root}')
            continue
        def onerror(exc):
            errors.append(str(exc))
        for base, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
            for name in list(dirs):
                p = Path(base) / name
                try:
                    if reparse(p):
                        dirs.remove(name)
                        skipped.append(str(p))
                except OSError as exc:
                    dirs.remove(name)
                    errors.append(str(exc))
            for name in files:
                p = Path(base) / name
                if str(p) in excluded:
                    continue
                try:
                    if reparse(p):
                        skipped.append(str(p))
                        continue
                    s = p.stat()
                    rows[str(p)] = {'size': s.st_size, 'mtime_ns': s.st_mtime_ns,
                                    'protected': protected(p, roots[0], roots[1]),
                                    'historical': historical(p)}
                except OSError as exc:
                    errors.append(f'{p}: {exc}')
    return rows, errors, skipped


def shortcuts(paths):
    if not paths:
        return {}, []
    if os.name != 'nt':
        return {}, ['非 Windows 环境未核对 .lnk']
    script = r'''[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$items = [Console]::In.ReadToEnd() | ConvertFrom-Json
$shell = New-Object -ComObject WScript.Shell
$result = @()
foreach ($p in $items) {
  try { $s = $shell.CreateShortcut($p); $result += @{path=$p;target=$s.TargetPath;error=''} }
  catch { $result += @{path=$p;target='';error=$_.Exception.Message} }
}
ConvertTo-Json -InputObject $result -Compress
'''
    try:
        proc = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script],
                              input=json.dumps(paths).encode('ascii'), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=90, check=True)
        values = json.loads(proc.stdout.decode('utf-8-sig'))
        return {v['path']: v['target'] for v in values if not v['error']}, [v['error'] for v in values if v['error']]
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {}, [f'快捷方式检查失败: {exc}']


def issue(kind, paths, reason, **extra):
    paths = [os.path.normpath(p) if p and Path(p).is_absolute() else p for p in paths]
    key = hashlib.sha256((kind + '\n' + '\n'.join(sorted(paths))).encode()).hexdigest()[:16]
    return {'id': key, 'kind': kind, 'paths': paths, 'reason': reason, **extra}


def assess(rows, previous, root, work):
    texts, errors, findings = {}, [], []
    hash_count = 0
    for name, row in rows.items():
        p = Path(name)
        cached = previous.get(name, {})
        same = all(cached.get(k) == row[k] for k in ['size', 'mtime_ns'])
        if same and cached.get('sha256'):
            row['sha256'] = cached['sha256']
        if p.suffix.lower() in TEXT and row['size'] <= 2_000_000:
            try:
                data = p.read_bytes()
                if p.stat().st_mtime_ns != row['mtime_ns']:
                    raise OSError('读取时文件发生变化')
                try:
                    texts[name] = data.decode('utf-8-sig')
                    row['text_encoding'] = 'utf-8-sig'
                except UnicodeError:
                    # Old Chinese text books are common; decode without rewriting originals.
                    if p.suffix.lower() != '.txt':
                        raise
                    texts[name] = data.decode('gb18030')
                    row['text_encoding'] = 'gb18030'
                if not row.get('sha256'):
                    row['sha256'] = hashlib.sha256(data).hexdigest()
                    hash_count += 1
            except UnicodeError:
                errors.append(f'非 UTF-8 文本未解析，不能据此证明无依赖: {name}')
            except OSError as exc:
                errors.append(f'{name}: {exc}')
        if row['size'] == 0 and not row['historical']:
            findings.append(issue('空文件待判断', [name], '零字节不等于无用；只建议，不删除。'))

    targets, shortcut_errors = shortcuts([n for n in rows if n.lower().endswith('.lnk')])
    errors.extend(shortcut_errors)
    checked_links = 0
    for name, text in texts.items():
        if historical(Path(name)):
            continue  # Historical content is not current navigation.
        if Path(name).suffix.lower() != '.md':
            continue
        # Skip fenced examples to avoid treating example paths as live navigation.
        live = re.sub(r'```.*?```', '', text, flags=re.S)
        for target in re.findall(r'\]\(([^\n)]+)\)', live):
            target = unquote(target.strip().strip('<>'))
            if target.startswith('#') or re.match(r'^(?:https?|mailto|codex|plugin|app):', target):
                continue
            target = target.split('#', 1)[0]
            if not target:
                continue
            q = Path(target)
            if not q.is_absolute():
                q = Path(name).parent / q
            checked_links += 1
            if not q.exists():
                findings.append(issue('失效链接', [name, str(q)], '本地链接目标不存在；不能据此判废源文档。'))
    for name, target in targets.items():
        if historical(Path(name)):
            continue
        checked_links += 1
        if not target or not Path(target).exists():
            findings.append(issue('失效快捷方式', [name, target], '目标为空或不存在；只报告，不猜测替代位置。'))

    for name, text in texts.items():
        p, row = Path(name), rows[name]
        if row['historical'] or not explicit_retired(text):
            continue
        inbound = [source for source, body in texts.items()
                   if source != name and not historical(Path(source)) and
                   (p.name in unquote(body) or str(p) in unquote(body))]
        inbound += [source for source, target in targets.items()
                    if not historical(Path(source)) and target and Path(target) == p]
        recent = time.time_ns() - row['mtime_ns'] < 48 * 3600 * 10**9
        findings.append(issue('明确停用待复核', [name], '正文状态明确停用；仍需核对替代依据、未解析依赖及占用情况。',
                              protected=row['protected'], recent=recent, inbound=inbound,
                              auto_move=False))

    groups = defaultdict(list)
    for name, row in rows.items():
        if row['size'] > 0 and not row['historical']:
            groups[row['size']].append(name)
    # Same size is only a suspicion. Cap large-file I/O per run at 256 MiB.
    budget, deferred = 256 * 1024**2, 0
    for size, names in sorted(groups.items()):
        if len(names) < 2:
            continue
        hashes = defaultdict(list)
        for name in names:
            row = rows[name]
            if not row.get('sha256'):
                if size > budget:
                    deferred += 1
                    continue
                try:
                    value = digest(Path(name))
                    s = Path(name).stat()
                    if s.st_size != size or s.st_mtime_ns != row['mtime_ns']:
                        raise OSError('校验时文件发生变化')
                    row['sha256'] = value
                    budget -= size
                    hash_count += 1
                except OSError as exc:
                    errors.append(f'{name}: {exc}')
                    continue
            hashes[row['sha256']].append(name)
        for value, matches in hashes.items():
            if len(matches) > 1:
                findings.append(issue('相同内容待判断', matches, 'SHA-256 一致；可能是快照、备份或安装配套，不自动合并或删除。',
                                      sha256=value, size_each=size,
                                      protected=any(rows[n]['protected'] for n in matches)))
    return findings, errors, {'checked_links': checked_links, 'new_hashes': hash_count,
                               'deferred_hash_files': deferred}


def journal_issue(records, findings, errors):
    current = {f['id']: f for f in findings}
    new = []
    for key, finding in current.items():
        if key not in records or records[key].get('status') == '已解决':
            new.append(key)
        item = records.setdefault(key, {'first_seen': now()})
        item.update(finding, status='待判断', last_seen=now())
    if not errors:
        for key, item in records.items():
            if key not in current:
                item['status'] = '已解决'
    return new


def reviewed_move(source, destination, source_root, archive_root, expected_hash):
    """Primitive only; caller must prove status/dependencies and get any required approval."""
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if not contained(source, source_root) or not contained(destination, archive_root):
        raise ValueError('路径越界')
    for p in [source, *source.parents, destination.parent, *destination.parent.parents]:
        if p.exists() and reparse(p):
            raise ValueError('拒绝符号链接或目录联接')
    if not source.is_file() or destination.exists():
        raise ValueError('源文件不存在或目标已存在；禁止覆盖')
    if digest(source) != expected_hash:
        raise ValueError('源内容变化')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Windows rename refuses overwrite; use a hard link for atomic no-clobber on POSIX.
    if os.name == 'nt':
        source.rename(destination)
    else:
        os.link(source, destination)
        source.unlink()
    try:
        if digest(destination) != expected_hash:
            raise OSError('收纳后内容不一致')
    except Exception:
        if not source.exists():
            destination.rename(source)
        raise
    return {'source': str(source), 'destination': str(destination), 'sha256': expected_hash, 'time': now()}


def restore_move(record, source_root, archive_root):
    return reviewed_move(record['destination'], record['source'], archive_root, source_root, record['sha256'])


def report(path, state, summary):
    pending = [v for v in state['issues'].values() if v['status'] == '待判断']
    lines = ['# 定时文件检查记录', '', f'最近检查：{summary["time"]}（北京时间）', '',
             f'状态：{summary["phase"]}；本程序不搬动、修复或删除生产文件。定时任务启用状态以任务配置为准。', '',
             f'扫描 {summary["files"]} 个文件，约 {summary["bytes"] / 1024**3:.2f} GiB；核对 {summary["checked_links"]} 个本地链接。',
             f'现存待判断 {len(pending)} 项，新增 {len(summary["new_issues"])} 项；本次移动 0，释放空间 0 字节。', '',
             '说明：扫描是元数据、文本引用与内容校验，不是全库正文审阅。“相同内容”不等于“可删除”。', '',
             '## 待判断事项', '']
    links_by_source = defaultdict(list)
    for item in pending:
        if item['kind'] == '失效链接':
            links_by_source[item['paths'][0]].append(item)
    if links_by_source:
        lines += ['### 失效链接（按来源合并）', '',
                  '以下计数是不存在的链接目标，不代表源文件无用；完整路径与问题ID保存在同目录状态JSON中。', '']
        for source, items in sorted(links_by_source.items(), key=lambda x: -len(x[1])):
            lines += [f'- `{source}`：{len(items)} 项。']
            lines += [f'  - 示例目标：`{i["paths"][1]}`' for i in items[:2]]
        lines += ['']
    for item in sorted(pending, key=lambda x: (x['kind'], x['id'])):
        if item['kind'] == '失效链接':
            continue
        lines += [f'### {item["kind"]} · {item["id"]}', '', item['reason'], '']
        lines += [f'- `{p}`' for p in item['paths']]
        if 'inbound' in item:
            lines += [f'- 保护：{item["protected"]}；48小时内变动：{item["recent"]}；已发现引用数：{len(item["inbound"])}。']
        lines += ['']
    if not pending:
        lines += ['本轮未发现符合机器规则的待判断事项；不代表所有内容已经人工确认有效。', '']
    lines += ['## 未完成检查与异常', ''] + (summary['errors'] or ['无扫描异常。'])
    lines += ['', f'跳过联接或符号链接：{summary["skipped_links"]}；因 I/O 预算推迟校验：{summary["deferred_hash_files"]} 个文件。',
              '', '## 最近12次检查摘要', '', '| 时间 | 文件数 | 新待办 | 异常 |', '|---|---:|---:|---:|']
    lines += [f'| {s["time"]} | {s["files"]} | {len(s["new_issues"])} | {len(s["errors"])} |' for s in state['history']]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--workbench', type=Path, default=WORK)
    parser.add_argument('--output', type=Path, default=ROOT / '04_项目管理/02_任务记录/文件整理记录')
    parser.add_argument('--phase', choices=['只读试查', '每周检查'], default='只读试查')
    args = parser.parse_args()
    args.root, args.workbench = args.root.absolute(), args.workbench.absolute()
    args.output.mkdir(parents=True, exist_ok=True)
    statefile = args.output / '定时检查状态.json'
    reportfile = args.output / '定时检查记录.md'
    lockfile = args.output / '定时检查.lock'
    if lockfile.exists():
        print(json.dumps({'status': 'skipped', 'reason': '已有运行锁；可能是运行中或异常遗留，需检查后处理。'}, ensure_ascii=True))
        return
    try:
        with lock(lockfile):
            state = json.loads(statefile.read_text(encoding='utf-8')) if statefile.exists() else {'inventory': {}, 'issues': {}, 'history': [], 'moves': []}
            excluded = {str(p) for p in [statefile, reportfile, lockfile, statefile.with_suffix('.json.tmp'),
                                         args.output / '任务执行.lock']}
            rows, errors, skipped = inventory([args.root, args.workbench], excluded)
            findings, read_errors, details = assess(rows, state['inventory'], args.root, args.workbench)
            errors += read_errors
            new = journal_issue(state['issues'], findings, errors)
            old = state['inventory']
            summary = {'time': now(), 'phase': args.phase, 'files': len(rows), 'bytes': sum(x['size'] for x in rows.values()),
                       'new_issues': new, 'errors': errors, 'skipped_links': len(skipped),
                       'added': len(rows.keys() - old.keys()), 'missing': len(old.keys() - rows.keys()),
                       'changed': sum(any(rows[k][f] != old[k][f] for f in ['size', 'mtime_ns']) for k in rows.keys() & old.keys()),
                       **details}
            state['inventory'] = rows
            state['history'] = (state['history'] + [summary])[-12:]
            atomic_json(statefile, state)
            report(reportfile, state, summary)
            print(json.dumps({**summary, 'new_issues': len(new), 'errors': errors,
                              'notification_needed': bool(new or errors), 'report': str(reportfile)}, ensure_ascii=True))
    except FileExistsError:
        print(json.dumps({'status': 'skipped', 'reason': '另一实例已开始运行。'}, ensure_ascii=True))


if __name__ == '__main__':
    main()
