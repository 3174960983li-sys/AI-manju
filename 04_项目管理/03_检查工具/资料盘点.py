"""只读扫描项目资料，生成独立快照；不移动或改写源文件。Python 标准库即可运行。"""
from pathlib import Path
import csv
import hashlib
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '04_项目管理' / '02_任务记录' / '盘点快照'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f')
    rows, errors = [], []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or OUT in path.parents:
            continue
        try:
            stat = path.stat()
            rel = path.relative_to(ROOT).as_posix()
            # 小型文本做内容校验；其他文件仅检测元数据变化，不能证明内容相同。
            digest = ''
            if path.suffix.lower() in {'.md', '.txt', '.csv', '.json', '.py'} and stat.st_size <= 2_000_000:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(dict(path=rel, area=rel.split('/')[0], extension=path.suffix.lower(),
                             size_bytes=stat.st_size, mtime_ns=stat.st_mtime_ns, sha256=digest))
        except OSError as exc:
            errors.append({'path': str(path), 'error': str(exc)})
    previous = sorted(OUT.glob('*_文件清单.csv'))
    old = {}
    if previous:
        with previous[-1].open(encoding='utf-8-sig', newline='') as stream:
            old = {row['path']: row for row in csv.DictReader(stream)}
    new = {row['path']: row for row in rows}
    changed = []
    for key in new.keys() & old.keys():
        a, b = old[key], new[key]
        if any(str(a.get(field, '')) != str(b.get(field, '')) for field in ('size_bytes', 'mtime_ns', 'sha256')):
            changed.append(key)
    summary = dict(scanned_at=datetime.now().astimezone().isoformat(), root=str(ROOT),
                   excluded='04_项目管理/02_任务记录/盘点快照/', file_count=len(rows),
                   total_bytes=sum(row['size_bytes'] for row in rows),
                   previous_snapshot=previous[-1].name if previous else None,
                   added=sorted(new.keys() - old.keys()),
                   missing=sorted(old.keys() - new.keys()), changed=sorted(changed), errors=errors,
                   notes='首次快照全部列为新增。missing 只表示本轮未扫描到；不推断删除原因。元数据扫描不等于正文阅读或质量验收。')
    counts = {}
    for row in rows:
        counts[row['area']] = counts.get(row['area'], 0) + 1
    summary['areas'] = counts
    target = OUT / f'{stamp}_文件清单.csv'
    with target.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['path', 'area', 'extension', 'size_bytes', 'mtime_ns', 'sha256'])
        writer.writeheader()
        writer.writerows(rows)
    (OUT / f'{stamp}_变化摘要.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(snapshot=str(target), file_count=len(rows), areas=counts,
                          changed_count=len(changed), missing_count=len(summary['missing']), errors=errors), ensure_ascii=False))


if __name__ == '__main__':
    main()
