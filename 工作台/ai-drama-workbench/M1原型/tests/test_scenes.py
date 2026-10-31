import json
import sqlite3

import pytest

from manju_m1.db import Database, SCHEMA
from manju_m1.scenes import MockSceneProvider, validate_scene_response
from manju_m1.scene_service import SceneService
from manju_m1.service import ProjectService

SCRIPT = "故事梗概\n第一场 内景 门厅 夜\n林禾：谁在外面？\n第二场 外景 街道 日\n阿川：等一下。\n"


@pytest.fixture
def prepared(tmp_path):
    db = Database(tmp_path / "scene-test.sqlite3")
    db.initialize()
    service = ProjectService(db)
    pid = service.create_project("场次测试")
    sid, _ = service.import_script(pid, "剧本.txt", SCRIPT.encode())
    return db, service, pid, sid


def test_mock_preserves_full_source_and_metadata():
    scenes = validate_scene_response(MockSceneProvider().generate(SCRIPT), SCRIPT)
    assert len(scenes) == 2
    assert "".join(s["source_text"] for s in scenes) == SCRIPT
    assert scenes[0]["location"] == "门厅"
    assert scenes[0]["interior_exterior"] == "内景"
    assert scenes[0]["characters"] == ["林禾"]
    assert scenes[1]["time_of_day"] == "日"


def test_no_heading_falls_back_without_invention():
    source = "林禾站在门口。\n她没有说话。"
    scenes = validate_scene_response(MockSceneProvider().generate(source), source)
    assert len(scenes) == 1
    assert scenes[0]["location"] == "未标注"
    assert scenes[0]["characters"] == []
    assert scenes[0]["source_text"] == source


@pytest.mark.parametrize("field,value", [("source_end", 999999), ("source_text", "捏造原文"), ("characters", "林禾"), ("ordinal", True), ("heading", "")])
def test_bad_response_is_rejected(field, value):
    data = json.loads(MockSceneProvider().generate(SCRIPT))
    data["scenes"][0][field] = value
    with pytest.raises(ValueError):
        validate_scene_response(json.dumps(data), SCRIPT)


def test_saved_runs_are_independent_and_project_scoped(prepared):
    db, service, pid, sid = prepared
    run1 = SceneService(db).split(pid, sid)
    run2 = SceneService(db).split(pid, sid)
    assert run1 != run2
    assert len(db.list_scene_runs(pid, sid)) == 2
    assert len(db.get_scenes(pid, run1)) == 2
    second = service.create_project("另一项目")
    assert db.get_scenes(second, run1) == []
    assert db.list_scene_runs(second, sid) == []
    with pytest.raises(ValueError, match="不属于"):
        SceneService(db).split(second, sid)
    reopened = Database(db.path)
    reopened.initialize()
    assert len(reopened.get_scenes(pid, run1)) == 2
    assert reopened.get_script(pid, sid)["content"] == SCRIPT


def test_bad_json_and_timeout_leave_no_results(prepared):
    db, _, pid, sid = prepared
    class Bad:
        name, mode = "bad-mock", "mock"
        def generate(self, script):
            return "not json"
    with pytest.raises(ValueError, match="有效JSON"):
        SceneService(db).split(pid, sid, Bad())
    class Slow(Bad):
        def generate(self, script):
            raise TimeoutError()
    with pytest.raises(ValueError, match="超时"):
        SceneService(db).split(pid, sid, Slow())
    assert db.list_scene_runs(pid, sid) == []


def test_non_mock_provider_is_not_executed(prepared):
    db, _, pid, sid = prepared
    class Real:
        name, mode = "not-allowed", "live"
        def generate(self, script):
            pytest.fail("Live provider must never run")
    with pytest.raises(ValueError, match="仅允许模拟"):
        SceneService(db).split(pid, sid, Real())


def test_transaction_failure_does_not_leave_partial_run(prepared):
    db, _, pid, sid = prepared
    with db.connection() as connection:
        connection.execute("CREATE TRIGGER reject_second BEFORE INSERT ON scenes WHEN NEW.ordinal=2 BEGIN SELECT RAISE(ABORT,'test rejection'); END")
    with pytest.raises(sqlite3.IntegrityError):
        SceneService(db).split(pid, sid)
    assert db.list_scene_runs(pid, sid) == []
    with db.connection() as connection:
        assert connection.execute("SELECT count(*) FROM scenes").fetchone()[0] == 0


def test_v1_migration_backs_up_and_preserves_original(tmp_path):
    path = tmp_path / "original.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute("PRAGMA user_version=1")
        connection.execute("INSERT INTO projects VALUES (?, ?, ?, ?)", ("p1", "旧项目", "原简介", "today"))
        connection.execute("INSERT INTO scripts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("s1", "p1", "旧稿.txt", "txt", "utf-8-sig", "旧稿正文", b"original", "sha", "", "today"))
    db = Database(path)
    db.initialize()
    assert db.get_script("p1", "s1")["original_bytes"] == b"original"
    with sqlite3.connect(path.with_suffix(".before-v2.sqlite3")) as backup:
        assert backup.execute("PRAGMA user_version").fetchone()[0] == 1
        assert backup.execute("SELECT content FROM scripts").fetchone()[0] == "旧稿正文"
    service = ProjectService(db)
    service.save_stage_notes("p1", "01", "原始构想")
    db.initialize()
    assert db.get_stage_notes("p1", "01") == "原始构想"
    assert db.get_stage_notes("p1", "02") == ""
    with pytest.raises(ValueError):
        service.save_stage_notes("p1", "99", "无效")