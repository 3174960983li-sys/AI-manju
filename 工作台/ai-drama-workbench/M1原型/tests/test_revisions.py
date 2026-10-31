import csv
import io
import json

import pytest

from manju_m1.db import Database
from manju_m1.service import ProjectService
from manju_m1.scene_service import SceneService
from manju_m1.revisions import RevisionService, export_csv, export_json


@pytest.fixture
def ready(tmp_path):
    db = Database(tmp_path / "revision.sqlite3")
    db.initialize()
    project = ProjectService(db)
    pid = project.create_project("修订测试")
    sid, _ = project.import_script(pid, "剧本.txt", "第一场 内景 门厅 夜\n林禾：谁？\n第二场 外景 街道 日\n风吹过。".encode())
    run = SceneService(db).split(pid, sid)
    return db, pid, sid, run, RevisionService(db)


def test_save_history_and_original_preserved(ready):
    db, pid, sid, run, service = ready
    original = service.get_view(pid, run)
    edited = json.loads(json.dumps(original["scenes"]))
    edited[0]["location"] = "门厅入口"
    edited[0]["characters"] = "林禾、阿川，林禾"
    revision = service.save_revision(pid, run, edited, "核对地点与人物")
    view = service.get_view(pid, run, revision)
    assert view["scenes"][0]["location"] == "门厅入口"
    assert view["scenes"][0]["characters"] == ["林禾", "阿川"]
    assert service.get_view(pid, run)["scenes"] == original["scenes"]
    assert db.get_script(pid, sid)["content"].startswith("第一场")
    db.initialize()
    assert service.list_revisions(pid, run)[0]["id"] == revision
    assert service.get_view(pid, run, revision)["revision"]["revision_number"] == 1
    with pytest.raises(ValueError, match="已有新修订"):
        service.save_revision(pid, run, edited, "过期保存")
    second = service.save_revision(pid, run, original["scenes"], "基于原始稿恢复字段", expected_latest_id=revision)
    assert service.get_view(pid, run, second)["revision"]["revision_number"] == 2
    assert service.get_view(pid, run, revision)["scenes"][0]["location"] == "门厅入口"


@pytest.mark.parametrize("key,value", [("heading", ""), ("interior_exterior", "无效"), ("source_text", "改写原文"), ("source_start", 9), ("id", "missing"), ("ordinal", 99)])
def test_invalid_edits_do_not_save(ready, key, value):
    _, pid, _, run, service = ready
    rows = service.get_view(pid, run)["scenes"]
    rows[0][key] = value
    with pytest.raises(ValueError):
        service.save_revision(pid, run, rows, "坏数据")
    assert service.list_revisions(pid, run) == []


def test_revision_project_isolation_and_export(ready):
    db, pid, _, run, service = ready
    original = service.get_view(pid, run)
    rows = original["scenes"]
    rows[0]["heading"] = '=HYPERLINK("bad")'
    revision = service.save_revision(pid, run, rows, "导出检查")
    p2 = ProjectService(db).create_project("其他项目")
    with pytest.raises(ValueError):
        service.get_view(p2, run, revision)
    view = service.get_view(pid, run, revision)
    data = json.loads(export_json(view))
    assert data["revision"]["id"] == revision
    assert data["scenes"][0]["heading"].startswith("=")
    assert data["generation_mode"] == "mock"
    csv_data = export_csv(view)
    assert csv_data.startswith(b"\xef\xbb\xbf")
    records = list(csv.DictReader(io.StringIO(csv_data.decode("utf-8-sig"))))
    assert records[0]["heading"].startswith("'=")
    assert records[0]["revision_id"] == revision
    assert records[0]["source_text"] == view["scenes"][0]["source_text"]


def test_scene_count_and_note_are_required(ready):
    _, pid, _, run, service = ready
    scenes = service.get_view(pid, run)["scenes"]
    with pytest.raises(ValueError):
        service.save_revision(pid, run, scenes[:1], "删行")
    with pytest.raises(ValueError):
        service.save_revision(pid, run, scenes, "")