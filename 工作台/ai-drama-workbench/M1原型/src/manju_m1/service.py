"""Application use cases, independent of Streamlit."""
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from .db import Database
from .scripts import display_filename, parse_script


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class ProjectService:
    def __init__(self, database: Database):
        self.db = database

    def create_project(self, name: str, description: str = "") -> str:
        name = name.strip()
        description = description.strip()
        if not name or len(name) > 120:
            raise ValueError("项目名称须为1—120个字符。")
        if len(description) > 5000:
            raise ValueError("项目简介不能超过5000字。")
        project_id = str(uuid4())
        with self.db.connection() as connection:
            connection.execute(
                "INSERT INTO projects(id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (project_id, name, description, _now()),
            )
        return project_id

    def import_script(self, project_id: str, filename: str, data: bytes, encoding: str | None = None):
        if not self.db.get_project(project_id):
            raise ValueError("项目不存在，请先创建或选择项目。")
        parsed = parse_script(filename, data, encoding)
        digest = sha256(data).hexdigest()
        script_id = str(uuid4())
        with self.db.connection() as connection:
            existing = connection.execute(
                "SELECT id, encoding FROM scripts WHERE project_id = ? AND sha256 = ?", (project_id, digest),
            ).fetchone()
            if existing:
                if existing["encoding"] != parsed.encoding:
                    raise ValueError("同一原件已按另一编码导入。本轮不覆盖原文，请先核对已有记录。")
                return existing["id"], False
            connection.execute(
                "INSERT INTO scripts(id, project_id, filename, source_type, encoding, content, original_bytes, sha256, warning, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (script_id, project_id, display_filename(filename), parsed.source_type, parsed.encoding,
                 parsed.text, data, digest, parsed.warning, _now()),
            )
        return script_id, True

    def save_stage_notes(self, project_id: str, stage_id: str, notes: str):
        from .workflow import STAGE_IDS
        if not self.db.get_project(project_id) or stage_id not in STAGE_IDS:
            raise ValueError('项目或阶段无效。')
        if len(notes) > 100000:
            raise ValueError('阶段记录不能超过10万字。')
        self.db.save_stage_notes(project_id, stage_id, notes, _now())
