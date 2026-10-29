"""All fixtures live in TemporaryDirectory; never move real project files."""
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location('filecheck', Path(__file__).with_name('定时文件检查.py'))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.work = Path(self.temp.name) / 'work'
        self.root.mkdir()
        self.work.mkdir()

    def file(self, relative, text='正文'):
        p = self.root / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def scan(self):
        rows, errors, _ = app.inventory([self.root, self.work], set())
        self.assertEqual(errors, [])
        found, errors, _ = app.assess(rows, {}, self.root, self.work)
        self.assertEqual(errors, [])
        return rows, found

    def test_old_active_is_not_retired(self):
        p = self.file('02_制作方法/01_流程规范/旧版_待审.md', '状态：当前采用。')
        os.utime(p, (1, 1))
        _, found = self.scan()
        self.assertFalse(any(f['kind'] == '明确停用待复核' for f in found))

    def test_status_not_prose_or_policy(self):
        self.assertTrue(app.explicit_retired('状态：已停用。\n替代：新流程.md'))
        self.assertFalse(app.explicit_retired('如果状态是已停用则检查。'))
        self.assertFalse(app.explicit_retired('| 状态：已停用 | 示例 |'))

    def test_retired_and_inbound_dependency(self):
        p = self.file('02_制作方法/01_流程规范/旧流程.md', '状态：已停用。')
        self.file('02_制作方法/01_流程规范/当前流程.md', '[依赖](旧流程.md)')
        _, found = self.scan()
        item = next(f for f in found if f['kind'] == '明确停用待复核')
        self.assertIn(str(p), item['paths'])
        self.assertEqual(len(item['inbound']), 1)
        self.assertTrue(item['recent'])
        self.assertFalse(item['auto_move'])

    def test_protected_assets(self):
        for name in ['01_作品项目/甲/剧本.md', '03_参考资料/01_书籍教程/参考.txt', '02_制作方法/01_流程规范/截图.png',
                     '02_制作方法/02_专业技能/自研Skill/a/references/r.md']:
            p = self.file(name)
            self.assertTrue(app.protected(p, self.root, self.work))
        p = self.file('02_制作方法/01_流程规范/流程.md')
        self.assertFalse(app.protected(p, self.root, self.work))

    def test_duplicates_are_only_suggestions(self):
        self.file('02_制作方法/01_流程规范/a.md', '相同内容')
        self.file('02_制作方法/01_流程规范/b.md', '相同内容')
        _, found = self.scan()
        item = next(f for f in found if f['kind'] == '相同内容待判断')
        self.assertIn('不自动', item['reason'])

    def test_broken_link_and_historical_link(self):
        self.file('02_制作方法/01_流程规范/a.md', '[缺失](不存在.md)')
        self.file('05_文件整理/03_停用归档/历史.md', '[过去的链接](过去.md)')
        _, found = self.scan()
        self.assertEqual(sum(f['kind'] == '失效链接' for f in found), 1)

    def test_backup_navigation_is_not_current_navigation(self):
        self.file('04_项目管理/02_任务记录/案例验证/管理记录备份_继续执行/旧导航.md', '[旧目标](不存在.md)')
        _, found = self.scan()
        self.assertFalse(any(f['kind'] == '失效链接' for f in found))

    def test_legacy_text_encoding_is_read_without_rewrite(self):
        p = self.file('03_参考资料/01_书籍教程/旧书.txt')
        p.write_bytes('旧书原文及参考材料。'.encode('gb18030'))
        value = app.digest(p)
        rows, _ = self.scan()
        self.assertEqual(rows[str(p)]['text_encoding'], 'gb18030')
        self.assertEqual(app.digest(p), value)

    def test_journal_does_not_repeat_and_keeps_unresolved_on_error(self):
        f = app.issue('待确认', ['a'], '原因')
        records = {}
        self.assertEqual(len(app.journal_issue(records, [f], [])), 1)
        self.assertEqual(app.journal_issue(records, [f], []), [])
        app.journal_issue(records, [], ['扫描失败'])
        self.assertEqual(records[f['id']]['status'], '待判断')
        app.journal_issue(records, [], [])
        self.assertEqual(records[f['id']]['status'], '已解决')

    def test_no_overwrite_move_restore_and_repeat(self):
        p = self.file('02_制作方法/01_流程规范/a.md')
        archive = self.root / app.ARCHIVE_NAME
        dest = archive / '02_制作方法/01_流程规范/a.md'
        value = app.digest(p)
        record = app.reviewed_move(p, dest, self.root, archive, value)
        self.assertFalse(p.exists())
        with self.assertRaises(ValueError):
            app.reviewed_move(p, dest, self.root, archive, value)
        app.restore_move(record, self.root, archive)
        self.assertEqual(app.digest(p), value)
        self.assertFalse(dest.exists())
        dest.write_text('已有内容', encoding='utf-8')
        with self.assertRaises(ValueError):
            app.reviewed_move(p, dest, self.root, archive, value)
        self.assertEqual(dest.read_text(encoding='utf-8'), '已有内容')

    def test_changed_source_and_escape_blocked(self):
        p = self.file('02_制作方法/01_流程规范/a.md')
        archive = self.root / app.ARCHIVE_NAME
        for dest, value in [(archive/'a.md', '错误校验值'), (self.work/'a.md', app.digest(p))]:
            with self.assertRaises(ValueError):
                app.reviewed_move(p, dest, self.root, archive, value)
        self.assertTrue(p.exists())

    def test_failed_move_verification_rolls_back(self):
        p = self.file('02_制作方法/01_流程规范/a.md')
        archive = self.root / app.ARCHIVE_NAME
        dest = archive / 'a.md'
        value = app.digest(p)
        with patch.object(app, 'digest', side_effect=[value, '不一致']):
            with self.assertRaises(OSError):
                app.reviewed_move(p, dest, self.root, archive, value)
        self.assertTrue(p.exists())
        self.assertFalse(dest.exists())

    def test_overlapping_run_is_blocked(self):
        p = self.root/'run.lock'
        with app.lock(p):
            with self.assertRaises(FileExistsError):
                with app.lock(p):
                    self.fail('不能重入')
        self.assertFalse(p.exists())

    def test_directory_symlink_is_not_followed(self):
        outside = Path(self.temp.name)/'outside'
        outside.mkdir()
        (outside/'external.md').write_text('不要扫描外部', encoding='utf-8')
        link = self.root/'外部联接'
        try:
            os.symlink(outside, link, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f'系统不允许创建测试符号链接: {exc}')
        rows, errors, skipped = app.inventory([self.root, self.work], set())
        self.assertEqual(rows, {})
        self.assertEqual(errors, [])
        self.assertIn(str(link), skipped)

    def test_repeated_cli_is_quiet_and_history_is_bounded(self):
        self.file('02_制作方法/01_流程规范/a.md', '[缺失](missing.md)')
        output = self.root/'04_项目管理/02_任务记录/文件整理记录'
        results = []
        for _ in range(13):
            capture = io.StringIO()
            with patch.object(sys, 'argv', ['scan', '--root', str(self.root), '--workbench', str(self.work), '--output', str(output)]):
                with contextlib.redirect_stdout(capture):
                    app.main()
            results.append(json.loads(capture.getvalue()))
        state = json.loads((output/'定时检查状态.json').read_text(encoding='utf-8'))
        self.assertTrue(results[0]['notification_needed'])
        self.assertFalse(results[-1]['notification_needed'])
        self.assertEqual(results[-1]['new_hashes'], 0)
        self.assertEqual(len(state['history']), 12)
        self.assertEqual(len(state['issues']), 1)
        self.assertTrue((output/'定时检查记录.md').exists())


if __name__ == '__main__':
    unittest.main()
