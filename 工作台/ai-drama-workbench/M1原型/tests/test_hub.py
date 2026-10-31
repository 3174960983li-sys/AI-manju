import pytest
from manju_m1.db import Database
from manju_m1.service import ProjectService
from manju_m1.hub import HubService


@pytest.fixture
def ready(tmp_path):
    db = Database(tmp_path / "hub.sqlite3")
    db.initialize()
    pid = ProjectService(db).create_project("总览测试")
    return db, pid, HubService(db)


def save(hub, pid, **overrides):
    args = dict(project_id=pid, stage_id="01", kind="任务", title="整理创意提案", state="未开始", owner="我", scope_ref="整剧构想v1", input_ref="初步想法", output_ref="", criteria="目标与未知项分开", note="草拟")
    args.update(overrides)
    return hub.save_item(**args)


def test_twelve_stages_and_manual_progress(ready):
    _, pid, hub = ready
    assert len(hub.overview(pid)) == 12
    assert all(row["进度"] == "未开始" for row in hub.overview(pid))
    save(hub, pid)
    assert hub.overview(pid)[0]["任务"] == 1
    assert hub.overview(pid)[0]["进度"] == "未开始"
    hub.save_progress(pid, "01", "进行中", "仅创意提案")
    assert hub.overview(pid)[0]["进度"] == "进行中"
    assert hub.overview(pid)[1]["进度"] == "未开始"


def test_item_history_and_project_isolation(ready):
    db, pid, hub = ready
    item_id = save(hub, pid)
    save(hub, pid, item_id=item_id, expected_version=1, state="进行中", note="开始整理")
    assert hub.list_items(pid)[0]["version"] == 2
    assert len(hub.history(pid, item_id)) == 2
    other = ProjectService(db).create_project("其他项目")
    assert hub.list_items(other) == []
    assert hub.history(other, item_id) == []
    with pytest.raises(ValueError):
        save(hub, other, item_id=item_id, expected_version=2)
    with pytest.raises(ValueError, match="已有更新"):
        save(hub, pid, item_id=item_id, expected_version=1)


def test_decision_requires_user_scope_and_basis(ready):
    _, pid, hub = ready
    with pytest.raises(ValueError, match="本人决定"):
        save(hub, pid, stage_id="02", kind="确认", title="项目立项", state="通过")
    item_id = save(hub, pid, stage_id="02", kind="确认", title="项目立项", state="限定通过", confirmed=True, note="仅允许首批开发")
    assert hub.list_items(pid, kind="确认")[0]["id"] == item_id
    assert hub.overview(pid)[1]["进度"] == "未开始"
    with pytest.raises(ValueError, match="对应阶段"):
        save(hub, pid, stage_id="01", kind="确认", title="项目立项", state="待确认")


def test_deliverable_and_receipt_require_evidence(ready):
    _, pid, hub = ready
    with pytest.raises(ValueError, match="实际成果"):
        save(hub, pid, state="已接收")
    with pytest.raises(ValueError, match="交付物"):
        save(hub, pid, kind="交付物", state="采用")
    save(hub, pid, kind="交付物", state="采用", confirmed=True, output_ref="文件路径与版本")
    assert hub.overview(pid)[0]["交付物"] == 1


def test_framework_survives_reopen(ready):
    db, pid, hub = ready
    save(hub, pid)
    hub.save_progress(pid, "01", "待确认", "等确认创作意向")
    reopened = Database(db.path)
    reopened.initialize()
    assert HubService(reopened).overview(pid)[0]["进度"] == "待确认"
    assert len(HubService(reopened).list_items(pid)) == 1