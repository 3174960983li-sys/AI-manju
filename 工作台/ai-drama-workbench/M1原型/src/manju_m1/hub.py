"""Project-wide workflow skeleton. Records are manual, not automated execution."""
import json
from uuid import uuid4

from .service import _now
from .workflow import STAGES, STAGE_IDS

STATES = {"任务": ["未开始", "进行中", "待接收", "已接收", "需返工"], "交付物": ["候选", "采用", "已替代"], "确认": ["待确认", "通过", "限定通过", "退回", "暂缓", "终止"]}
PROGRESS = ["未开始", "进行中", "待确认", "已完成"]
GATES = {"项目立项": "02", "整剧创作基准": "03", "首批创作方向": "05", "生产基准": "06", "本批开工": "08", "单集成片采用": "11", "最终交付验收": "12"}
INPUTS = {
 "01": "初步想法、创作动机、期望体验。", "02": "创意提案、市场证据及资源边界。", "03": "立项依据、制作约束与整剧规划。", "04": "采用剧本、研究问题及可访问参考。", "05": "采用剧本、作品研究及风格候选。", "06": "导演方案、制作需求及最小临时资产。", "07": "生产基准、核心资产需求及设计方向。", "08": "本批剧本、导演方案、核心资产与声音依据。", "09": "有效分镜、资产版本与镜头状态。", "10": "本批开工依据、镜头输入与资源范围。", "11": "采用素材、有效时间线及声音特效成果。", "12": "逐集采用依据、完成版和交付规格。",
}
CAPABILITIES = {
 "01": "创意提案／制作统筹", "02": "市场与可行性分析", "03": "剧本开发／项目剧本分析", "04": "作品研究／导演参考", "05": "导演方案／表演与场面设计", "06": "制作统筹／样段验证", "07": "美术设计／场景空间设计", "08": "分镜／声音读演／预演剪辑", "09": "关键图／资产补齐", "10": "视频执行／持续剪辑", "11": "声音／特效／后期完成", "12": "审查／交付／归档",
}


class HubService:
    def __init__(self, database):
        self.db = database

    def _scope(self, project_id, stage_id):
        if stage_id not in STAGE_IDS or not self.db.get_project(project_id):
            raise ValueError("项目或阶段不存在。")

    def list_items(self, project_id, stage_id=None, kind=None):
        if not self.db.get_project(project_id):
            raise ValueError("项目不存在。")
        query, values = "SELECT * FROM work_items WHERE project_id=?", [project_id]
        if stage_id:
            query += " AND stage_id=?"
            values.append(stage_id)
        if kind:
            query += " AND kind=?"
            values.append(kind)
        with self.db.connection() as connection:
            return [dict(r) for r in connection.execute(query + " ORDER BY created_at DESC,id", values)]

    def save_item(self, project_id, stage_id, kind, title, state, owner, scope_ref, input_ref, output_ref, criteria, note, *, item_id=None, expected_version=None, confirmed=False):
        self._scope(project_id, stage_id)
        if kind not in STATES or state not in STATES[kind]:
            raise ValueError("记录类型或状态无效。")
        fields = dict(title=title, owner=owner, scope_ref=scope_ref, input_ref=input_ref, output_ref=output_ref, criteria=criteria, note=note)
        if any(not isinstance(v, str) or len(v) > 100000 for v in fields.values()):
            raise ValueError("字段格式或长度无效。")
        fields = {k: v.strip() for k, v in fields.items()}
        if not fields["title"] or len(fields["title"]) > 120:
            raise ValueError("标题须为1—120字。")
        if kind == "确认":
            if title not in GATES or GATES[title] != stage_id:
                raise ValueError("确认关口与对应阶段不一致。")
            if not fields["scope_ref"]:
                raise ValueError("请说明确认的整剧、批次或单集及具体版本。")
            if state != "待确认" and (not confirmed or not fields["note"]):
                raise ValueError("请明确勾选本人决定，并填写依据、范围或限制。")
        if kind == "任务" and state == "已接收" and (not fields["output_ref"] or not fields["criteria"]):
            raise ValueError("记录接收前需填写实际成果与检查依据。")
        if kind == "交付物" and state == "采用" and (not confirmed or not fields["output_ref"] or not fields["scope_ref"]):
            raise ValueError("采用交付物需填写实际位置、版本范围并勾选本人决定。")
        with self.db.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            old = connection.execute("SELECT * FROM work_items WHERE id=? AND project_id=?", (item_id, project_id)).fetchone() if item_id else None
            if item_id and (not old or old["kind"] != kind or old["stage_id"] != stage_id):
                raise ValueError("记录不存在、类型或阶段不匹配。")
            if old and old["version"] != expected_version:
                raise ValueError("记录已有更新，请刷新后重试。")
            item_id = item_id or str(uuid4())
            version, time = (old["version"] + 1) if old else 1, _now()
            values = [fields[k] for k in ("title", "owner", "scope_ref", "input_ref", "output_ref", "criteria", "note")]
            if old:
                connection.execute("UPDATE work_items SET title=?,owner=?,scope_ref=?,input_ref=?,output_ref=?,criteria=?,note=?,state=?,version=?,updated_at=? WHERE id=?", (*values, state, version, time, item_id))
            else:
                connection.execute("INSERT INTO work_items(id,project_id,stage_id,kind,title,owner,scope_ref,input_ref,output_ref,criteria,note,state,version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (item_id, project_id, stage_id, kind, *values, state, version, time, time))
            snapshot = dict(connection.execute("SELECT * FROM work_items WHERE id=?", (item_id,)).fetchone())
            connection.execute("INSERT INTO work_item_events VALUES (?,?,?,?,?)", (str(uuid4()), item_id, version, json.dumps(snapshot, ensure_ascii=False), time))
        return item_id

    def history(self, project_id, item_id):
        with self.db.connection() as connection:
            return [dict(r) for r in connection.execute("SELECT e.* FROM work_item_events e JOIN work_items i ON i.id=e.item_id WHERE i.project_id=? AND i.id=? ORDER BY e.version DESC", (project_id, item_id))]

    def save_progress(self, project_id, stage_id, state, note):
        self._scope(project_id, stage_id)
        if state not in PROGRESS or not isinstance(note, str) or not note.strip():
            raise ValueError("请选择进度并填写范围说明。")
        with self.db.connection() as connection:
            time = _now()
            connection.execute("INSERT INTO stage_progress VALUES (?,?,?,?,?) ON CONFLICT(project_id,stage_id) DO UPDATE SET state=excluded.state,note=excluded.note,updated_at=excluded.updated_at", (project_id, stage_id, state, note, time))
            connection.execute("INSERT INTO progress_events VALUES (?,?,?,?,?,?)", (str(uuid4()), project_id, stage_id, state, note, time))

    def overview(self, project_id):
        items = self.list_items(project_id)
        with self.db.connection() as connection:
            progress = {r["stage_id"]: dict(r) for r in connection.execute("SELECT * FROM stage_progress WHERE project_id=?", (project_id,))}
        return [{"阶段": s[0], "名称": s[1], "进度": progress.get(s[0], {}).get("state", "未开始"), "任务": sum(i["stage_id"] == s[0] and i["kind"] == "任务" for i in items), "交付物": sum(i["stage_id"] == s[0] and i["kind"] == "交付物" for i in items), "待确认": sum(i["stage_id"] == s[0] and i["kind"] == "确认" and i["state"] == "待确认" for i in items)} for s in STAGES]