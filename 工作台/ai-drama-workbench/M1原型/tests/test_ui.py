from pathlib import Path

from streamlit.testing.v1 import AppTest

from manju_m1.db import Database

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_ui_create_upload_preview_restart(tmp_path, monkeypatch):
    db_path = tmp_path / "ui.sqlite3"
    monkeypatch.setenv("MANJU_M1_DB_PATH", str(db_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    app.text_input[0].set_value("界面验收项目")
    button(app, "创建项目").click().run()
    assert not app.exception
    assert len(Database(db_path).list_projects()) == 1
    app.file_uploader[0].upload("剧本.txt", "第一场 门厅 夜\n林禾推门。".encode("utf-8"), mime_type="text/plain").run()
    button(app, "读取并保存剧本").click().run()
    assert not app.exception
    preview = next(t for t in app.text_area if t.label == "已保存正文（只读）")
    assert "林禾推门" in preview.value
    assert preview.disabled
    button(app, "读取并保存剧本").click().run()
    pid = Database(db_path).list_projects()[0]["id"]
    assert len(Database(db_path).list_scripts(pid)) == 1
    restarted = AppTest.from_file(str(APP)).run(timeout=20)
    assert not restarted.exception
    assert any("林禾推门" in t.value for t in restarted.text_area)


def test_ui_empty_name_and_corrupt_upload(tmp_path, monkeypatch):
    db_path = tmp_path / "ui-errors.sqlite3"
    monkeypatch.setenv("MANJU_M1_DB_PATH", str(db_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    button(app, "创建项目").click().run()
    assert app.error
    app.text_input[0].set_value("坏文件测试")
    button(app, "创建项目").click().run()
    app.file_uploader[0].upload("bad.docx", b"not docx", mime_type="application/octet-stream").run()
    button(app, "读取并保存剧本").click().run()
    assert app.error and not app.exception
    pid = Database(db_path).list_projects()[0]["id"]
    assert Database(db_path).list_scripts(pid) == []

def test_ui_workflow_notes_and_mock_scenes(tmp_path, monkeypatch):
    db_path = tmp_path / "workflow-ui.sqlite3"
    monkeypatch.setenv("MANJU_M1_DB_PATH", str(db_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    app.text_input[0].set_value("流程验收")
    button(app, "创建项目").click().run()
    next(s for s in app.selectbox if s.label == "工作阶段").select("01").run()
    next(t for t in app.text_area if t.label == "阶段准备记录（不代表已通过）").set_value("题材与创作目标待分析")
    button(app, "保存阶段准备记录").click().run()
    pid = Database(db_path).list_projects()[0]["id"]
    assert Database(db_path).get_stage_notes(pid, "01") == "题材与创作目标待分析"
    assert not app.file_uploader
    next(s for s in app.selectbox if s.label == "工作阶段").select("03").run()
    app.file_uploader[0].upload("剧本.txt", "第一场 内景 门厅 夜\n林禾：谁？\n第二场 外景 街道 日\n无人回答。".encode(), mime_type="text/plain").run()
    button(app, "读取并保存剧本").click().run()
    button(app, "模拟拆分并保存场次").click().run()
    assert not app.exception
    sid = Database(db_path).list_scripts(pid)[0]["id"]
    runs = Database(db_path).list_scene_runs(pid, sid)
    assert len(runs) == 1 and runs[0]["scene_count"] == 2
    assert any("本地规则模拟" in warning.value for warning in app.warning)
    restarted = AppTest.from_file(str(APP)).run(timeout=20)
    assert not restarted.exception
    assert any(s.label == "查看拆分记录" for s in restarted.selectbox)

def test_ui_save_scene_revision_and_export_controls(tmp_path, monkeypatch):
    from manju_m1.revisions import RevisionService
    db_path = tmp_path / "edit-ui.sqlite3"
    monkeypatch.setenv("MANJU_M1_DB_PATH", str(db_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    app.text_input[0].set_value("编辑验收")
    button(app, "创建项目").click().run()
    app.file_uploader[0].upload("剧本.txt", "第一场 内景 门厅 夜\n林禾：谁？".encode(), mime_type="text/plain").run()
    button(app, "读取并保存剧本").click().run()
    button(app, "模拟拆分并保存场次").click().run()
    next(t for t in app.text_input if t.label == "地点").set_value("门厅入口")
    next(t for t in app.text_input if t.label == "本次修订说明").set_value("人工核对地点")
    button(app, "保存本场为新修订").click().run(timeout=20)
    assert not app.exception
    db = Database(db_path)
    pid = db.list_projects()[0]["id"]
    sid = db.list_scripts(pid)[0]["id"]
    run = db.list_scene_runs(pid, sid)[0]["id"]
    revision = RevisionService(db).list_revisions(pid, run)[0]["id"]
    assert RevisionService(db).get_view(pid, run, revision)["scenes"][0]["location"] == "门厅入口"
    assert any(s.label == "场次版本" for s in app.selectbox)
    restarted = AppTest.from_file(str(APP)).run(timeout=20)
    assert not restarted.exception
    assert next(t for t in restarted.text_input if t.label == "地点").value == "门厅入口"

def test_ui_framework_overview_and_task_record(tmp_path, monkeypatch):
    from manju_m1.hub import HubService
    db_path = tmp_path / "hub-ui.sqlite3"
    monkeypatch.setenv("MANJU_M1_DB_PATH", str(db_path))
    app = AppTest.from_file(str(APP)).run(timeout=20)
    app.text_input[0].set_value("框架验收")
    button(app, "创建项目").click().run()
    next(r for r in app.radio if r.label == "工作区").set_value("项目总览").run()
    assert not app.exception
    assert any(b.label == "01 创作意向与初步构想" for b in app.button)
    next(r for r in app.radio if r.label == "工作区").set_value("任务与交付").run()
    next(t for t in app.text_input if t.label == "记录标题").set_value("完成首批剧本提案")
    button(app, "保存记录").click().run(timeout=20)
    assert not app.exception
    db = Database(db_path)
    pid = db.list_projects()[0]["id"]
    assert HubService(db).list_items(pid)[0]["title"] == "完成首批剧本提案"
    next(r for r in app.radio if r.label == "工作区").set_value("确认中心").run()
    assert not app.exception
    assert any(s.label == "确认关口" for s in app.selectbox)
    next(r for r in app.radio if r.label == "工作区").set_value("规范索引").run()
    assert not app.exception