"""Human scene revisions and exports. Original script/scenes remain immutable."""
import csv
import io
import json
import re
from uuid import uuid4

from .db import Database
from .service import _now

EDITABLE = ("heading", "interior_exterior", "location", "time_of_day", "characters", "summary")


def normalize_scenes(rows):
    result = []
    for row in rows:
        item = dict(row)
        item["characters"] = json.loads(item.pop("characters_json"))
        result.append(item)
    return result


def validate_revision(original, edited):
    if not isinstance(edited, list) or len(edited) != len(original):
        raise ValueError("本版只修改场次字段，不增删或重排场次。")
    result = []
    for source, changed in zip(original, edited):
        if not isinstance(changed, dict) or changed.get("id") != source["id"]:
            raise ValueError("场次ID或顺序不匹配。")
        for field in ("ordinal", "source_start", "source_end", "source_text"):
            if field in changed and changed[field] != source[field]:
                raise ValueError("原文、定位与场次顺序不可改写。")
        item = dict(source)
        for field in EDITABLE:
            if field not in changed:
                raise ValueError(f"缺少场次字段：{field}")
            value = changed[field]
            if field == "characters":
                if isinstance(value, str):
                    value = [x.strip() for x in re.split(r"[、,，\n]", value) if x.strip()]
                if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() or len(x) > 100 for x in value):
                    raise ValueError("人物须为有效名称列表。")
                value = list(dict.fromkeys(x.strip() for x in value))
            else:
                if not isinstance(value, str) or not value.strip() or len(value) > (10000 if field == "summary" else 500):
                    raise ValueError(f"字段不能为空或超出长度：{field}")
                value = value.strip()
            item[field] = value
        if item["interior_exterior"] not in {"内景", "外景", "内外景", "未标注"}:
            raise ValueError("内外景选项无效。")
        result.append(item)
    return result


class RevisionService:
    def __init__(self, database: Database):
        self.db = database

    def _run(self, project_id, run_id, connection):
        row = connection.execute(
            "SELECT r.*,t.filename,t.project_id FROM scene_runs r JOIN scripts t ON t.id=r.script_id WHERE r.id=? AND t.project_id=?",
            (run_id, project_id),
        ).fetchone()
        if not row:
            raise ValueError("拆分记录不存在或不属于当前项目。")
        return dict(row)

    def list_revisions(self, project_id, run_id):
        with self.db.connection() as connection:
            self._run(project_id, run_id, connection)
            return [dict(row) for row in connection.execute(
                "SELECT id,base_revision_id,revision_number,note,created_at FROM scene_revisions WHERE run_id=? ORDER BY revision_number DESC", (run_id,),
            )]

    def get_view(self, project_id, run_id, revision_id=None):
        with self.db.connection() as connection:
            run = self._run(project_id, run_id, connection)
            if revision_id:
                row = connection.execute("SELECT * FROM scene_revisions WHERE id=? AND run_id=?", (revision_id, run_id)).fetchone()
                if not row:
                    raise ValueError("修订不属于当前拆分记录。")
                scenes = json.loads(row["scenes_json"])
                revision = {k: row[k] for k in ("id", "revision_number", "base_revision_id", "note", "created_at")}
            else:
                scenes = normalize_scenes(connection.execute("SELECT * FROM scenes WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall())
                revision = None
            return {"schema_version": 1, "project_id": project_id, "script_id": run["script_id"], "filename": run["filename"], "run_id": run_id,
                    "source_sha256": run["source_sha256"], "provider": run["provider"], "generation_mode": run["mode"],
                    "review_status": "待人工核对／未作采用确认", "revision": revision, "scenes": scenes}

    def save_revision(self, project_id, run_id, edited, note, *, base_revision_id=None, expected_latest_id=None):
        if not isinstance(note, str) or not note.strip() or len(note) > 2000:
            raise ValueError("请填写1—2000字的修订说明。")
        with self.db.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._run(project_id, run_id, connection)
            latest = connection.execute("SELECT id,revision_number FROM scene_revisions WHERE run_id=? ORDER BY revision_number DESC LIMIT 1", (run_id,)).fetchone()
            if (latest["id"] if latest else None) != expected_latest_id:
                raise ValueError("已有新修订，请刷新并核对后重试，避免覆盖他人修改。")
            if base_revision_id and not connection.execute("SELECT id FROM scene_revisions WHERE id=? AND run_id=?", (base_revision_id, run_id)).fetchone():
                raise ValueError("所选历史版本不属于本次拆分。")
            original = normalize_scenes(connection.execute("SELECT * FROM scenes WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall())
            scenes = validate_revision(original, edited)
            revision_id = str(uuid4())
            connection.execute("INSERT INTO scene_revisions VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (revision_id, run_id, base_revision_id, (latest["revision_number"] + 1) if latest else 1, note.strip(), json.dumps(scenes, ensure_ascii=False), _now()))
        return revision_id


def export_json(view):
    return json.dumps(view, ensure_ascii=False, indent=2).encode("utf-8")


def _csv_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r")) else text


def export_csv(view):
    output = io.StringIO(newline="")
    fields = ["project_id", "script_id", "run_id", "revision_id", "generation_mode", "review_status", "source_sha256", "scene_id", "ordinal", *EDITABLE, "source_start", "source_end", "source_text"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for scene in view["scenes"]:
        row = {k: scene.get(k, "") for k in ["ordinal", *EDITABLE, "source_start", "source_end", "source_text"]}
        row.update({k: view[k] for k in ["project_id", "script_id", "run_id", "generation_mode", "review_status", "source_sha256"]})
        row["scene_id"] = scene["id"]
        row["revision_id"] = view["revision"]["id"] if view["revision"] else "original"
        row["characters"] = "、".join(scene["characters"])
        writer.writerow({k: _csv_safe(v) for k, v in row.items()})
    return output.getvalue().encode("utf-8-sig")