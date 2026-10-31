import json
import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from manju_m1.db import Database
from manju_m1.episodes import EpisodeService
from manju_m1.scene_service import SceneService
from manju_m1.service import ProjectService


@pytest.fixture
def setup(tmp_path):
    db = Database(tmp_path / 'episodes.sqlite3')
    db.initialize()
    p = ProjectService(db)
    a, b = p.create_project('甲'), p.create_project('乙')
    return db, p, a, b, EpisodeService(db)


def test_plan_validation_history_and_conflict(setup):
    db, p, a, b, service = setup
    eid = service.save(a, 2, ' 第二集 ', '结构', 90)
    assert service.list_episodes(a)[0]['title'] == '第二集'
    assert service.list_episodes(b) == []
    with pytest.raises(ValueError, match='重复'):
        service.save(a, 2, '重复编号')
    with pytest.raises(ValueError, match='不属于'):
        service.save(b, 2, '跨项目', episode_id=eid, expected_version=1)
    with pytest.raises(ValueError, match='编号不可修改'):
        service.save(a, 3, '改号', episode_id=eid, expected_version=1)
    service.save(a, 2, '第二集修订', episode_id=eid, expected_version=1)
    with pytest.raises(ValueError, match='已被更新'):
        service.save(a, 2, '旧编辑页', episode_id=eid, expected_version=1)
    with db.connection() as c:
        snapshots = [json.loads(x[0]) for x in c.execute('SELECT snapshot_json FROM episode_events ORDER BY version')]
    assert [x['title'] for x in snapshots] == ['第二集', '第二集修订']


@pytest.mark.parametrize('number,title,seconds', [(0,'名称',0), (True,'名称',0), (1,' ',0), (1,'名称',-1)])
def test_invalid_plan_has_no_side_effects(setup, number, title, seconds):
    db, p, a, b, service = setup
    with pytest.raises(ValueError):
        service.save(a, number, title, target_seconds=seconds)
    assert not service.list_episodes(a)


def test_assignments_preserve_source_and_scene_history(setup):
    db, p, a, b, service = setup
    sid, _ = p.import_script(a, '第一集.txt', '第一场 内景 门厅 夜\n甲：谁？'.encode())
    original = db.get_script(a, sid)
    run = SceneService(db).split(a, sid)
    original_scenes = db.get_scenes(a, run)
    e1, e2 = service.save(a, 1, '开局'), service.save(a, 2, '升级')
    other = service.save(b, 1, '另一作品')
    for args in [(b, sid, other), (a, sid, other)]:
        with pytest.raises(ValueError, match='不属于'):
            service.assign(*args, None, '不应跨项目')
    service.assign(a, sid, e1, None, '确认第一集稿')
    assert service.assignment(a, sid)['id'] == e1
    with pytest.raises(ValueError, match='已改变'):
        service.assign(a, sid, e2, None, '旧归属状态')
    service.assign(a, sid, e2, e1, '人工调整归属')
    assert service.list_episodes(a)[1]['script_count'] == 1
    service.assign(a, sid, None, e2, '恢复为整剧稿')
    assert service.assignment(a, sid) is None
    assert db.get_script(a, sid) == original
    assert db.get_scenes(a, run) == original_scenes
    with db.connection() as c:
        assert c.execute('SELECT count(*) FROM script_episode_events').fetchone()[0] == 3


def test_v4_migration_backup_and_export(setup):
    db, p, a, b, service = setup
    sid, _ = p.import_script(a, '原稿.txt', b'original')
    with db.connection() as c:
        for table in ('script_episode_events', 'episode_events', 'script_episodes', 'episodes'):
            c.execute(f'DROP TABLE {table}')
        c.execute('PRAGMA user_version=4')
    db.initialize()
    backup = db.path.with_suffix('.before-v5.sqlite3')
    with sqlite3.connect(backup) as c:
        assert c.execute('PRAGMA user_version').fetchone()[0] == 4
        assert c.execute('SELECT original_bytes FROM scripts WHERE id=?', (sid,)).fetchone()[0] == b'original'
    eid = service.save(a, 1, '开篇')
    service.assign(a, sid, eid, None, '归属第一集')
    exported = json.loads(service.export(a))
    assert exported['script_assignments'][0]['episode_id'] == eid
    assert 'original_bytes' not in service.export(a)
    assert 'original' not in service.export(a)
    assert json.loads(service.export(b))['episodes'] == []
    with db.connection() as c:
        assert c.execute('PRAGMA user_version').fetchone()[0] == 6
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_ui_plan_assign_restart_and_scope(setup, monkeypatch):
    db, p, a, b, service = setup
    sid, _ = p.import_script(a, '单集.txt', '第一场 门厅 夜\n甲：谁？'.encode())
    monkeypatch.setenv('MANJU_M1_DB_PATH', str(db.path))
    app_path = Path(__file__).resolve().parents[1] / 'app.py'
    app = AppTest.from_file(str(app_path)).run(timeout=20)
    next(x for x in app.selectbox if x.label == '当前项目').select(a).run()
    next(x for x in app.radio if x.label == '工作区').set_value('整剧与单集').run()
    next(x for x in app.text_input if x.label == '单集名称').set_value('开局')
    next(x for x in app.button if x.label == '保存单集规划').click().run()
    assert not app.exception
    eid = service.list_episodes(a)[0]['id']
    next(x for x in app.radio if x.label == '工作区').set_value('阶段工作区').run()
    next(x for x in app.selectbox if x.label == '归属单集').select(eid)
    next(x for x in app.text_input if x.label == '归属调整说明').set_value('人工确认归属')
    next(x for x in app.checkbox if x.label.startswith('确认仅调整')).check()
    next(x for x in app.button if x.label == '保存剧本单集归属').click().run()
    assert not app.exception
    assert service.assignment(a, sid)['id'] == eid
    restarted = AppTest.from_file(str(app_path)).run(timeout=20)
    next(x for x in restarted.selectbox if x.label == '当前项目').select(a).run()
    assert not restarted.exception
    assert any('第1集 · 开局' in x.value for x in restarted.caption)
    next(x for x in restarted.selectbox if x.label == '当前项目').select(b).run()
    next(x for x in restarted.radio if x.label == '工作区').set_value('整剧与单集').run()
    assert next(x for x in restarted.text_input if x.label == '单集名称').value == ''
