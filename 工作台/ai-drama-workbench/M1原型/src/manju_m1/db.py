"""SQLite persistence. Open one connection per operation; keep UI out of this module."""
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 120),
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    filename TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('txt', 'docx')),
    encoding TEXT NOT NULL,
    content TEXT NOT NULL,
    original_bytes BLOB NOT NULL,
    sha256 TEXT NOT NULL,
    warning TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE(project_id, sha256)
);
CREATE INDEX IF NOT EXISTS scripts_by_project ON scripts(project_id, created_at);
"""


WORKFLOW_SCHEMA = """
CREATE TABLE IF NOT EXISTS stage_notes (
    project_id TEXT NOT NULL REFERENCES projects(id),
    stage_id TEXT NOT NULL CHECK(stage_id BETWEEN '01' AND '12'),
    notes TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(project_id, stage_id)
);
CREATE TABLE IF NOT EXISTS scene_runs (
    id TEXT PRIMARY KEY,
    script_id TEXT NOT NULL REFERENCES scripts(id),
    provider TEXT NOT NULL,
    mode TEXT NOT NULL CHECK(mode = 'mock'),
    source_sha256 TEXT NOT NULL,
    raw_response TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES scene_runs(id),
    ordinal INTEGER NOT NULL,
    heading TEXT NOT NULL,
    interior_exterior TEXT NOT NULL,
    location TEXT NOT NULL,
    time_of_day TEXT NOT NULL,
    characters_json TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_start INTEGER NOT NULL,
    source_end INTEGER NOT NULL,
    source_text TEXT NOT NULL,
    UNIQUE(run_id, ordinal)
);
CREATE INDEX IF NOT EXISTS runs_by_script ON scene_runs(script_id, created_at);
"""

REVISION_SCHEMA = """
CREATE TABLE IF NOT EXISTS scene_revisions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES scene_runs(id),
    base_revision_id TEXT REFERENCES scene_revisions(id),
    revision_number INTEGER NOT NULL,
    note TEXT NOT NULL,
    scenes_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(run_id, revision_number)
);
"""
HUB_SCHEMA = """
CREATE TABLE IF NOT EXISTS work_items (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), stage_id TEXT NOT NULL,
 kind TEXT NOT NULL, title TEXT NOT NULL, owner TEXT NOT NULL, scope_ref TEXT NOT NULL,
 input_ref TEXT NOT NULL, output_ref TEXT NOT NULL, criteria TEXT NOT NULL, note TEXT NOT NULL,
 state TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS work_item_events (
 id TEXT PRIMARY KEY, item_id TEXT NOT NULL REFERENCES work_items(id), version INTEGER NOT NULL,
 snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id,version)
);
CREATE TABLE IF NOT EXISTS stage_progress (
 project_id TEXT NOT NULL REFERENCES projects(id), stage_id TEXT NOT NULL, state TEXT NOT NULL,
 note TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(project_id,stage_id)
);
CREATE TABLE IF NOT EXISTS progress_events (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), stage_id TEXT NOT NULL,
 state TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL
);
"""
class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path).resolve()

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection

    def initialize(self):
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, 3, 4):
                raise ValueError("数据库版本高于本程序，请使用匹配版本，勿覆盖数据库。")
            if version in (1, 2, 3):
                backup_path = self.path.with_suffix(f".before-v{version + 1}.sqlite3")
                if not backup_path.exists():
                    with closing(sqlite3.connect(backup_path)) as destination:
                        connection.backup(destination)
            connection.executescript(SCHEMA + WORKFLOW_SCHEMA + REVISION_SCHEMA + HUB_SCHEMA)
            connection.execute("PRAGMA user_version = 4")

    def list_projects(self):
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM projects ORDER BY created_at DESC, id")]

    def get_project(self, project_id):
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return dict(row) if row else None

    def list_scripts(self, project_id):
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id, filename, source_type, encoding, sha256, warning, created_at, length(content) AS char_count "
                "FROM scripts WHERE project_id = ? ORDER BY created_at DESC, id", (project_id,),
            )
            return [dict(row) for row in rows]

    def get_script(self, project_id, script_id):
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM scripts WHERE project_id = ? AND id = ?", (project_id, script_id),
            ).fetchone()
            return dict(row) if row else None
    def get_stage_notes(self, project_id, stage_id):
        with self.connection() as connection:
            row = connection.execute("SELECT notes FROM stage_notes WHERE project_id = ? AND stage_id = ?", (project_id, stage_id)).fetchone()
            return row["notes"] if row else ""

    def save_stage_notes(self, project_id, stage_id, notes, updated_at):
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO stage_notes(project_id, stage_id, notes, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(project_id, stage_id) DO UPDATE SET notes=excluded.notes, updated_at=excluded.updated_at",
                (project_id, stage_id, notes, updated_at),
            )

    def list_scene_runs(self, project_id, script_id):
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT r.id, r.provider, r.mode, r.source_sha256, r.created_at, count(s.id) AS scene_count "
                "FROM scene_runs r JOIN scripts t ON t.id=r.script_id LEFT JOIN scenes s ON s.run_id=r.id "
                "WHERE t.project_id=? AND t.id=? GROUP BY r.id ORDER BY r.created_at DESC, r.id",
                (project_id, script_id),
            )
            return [dict(row) for row in rows]

    def get_scenes(self, project_id, run_id):
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT s.* FROM scenes s JOIN scene_runs r ON r.id=s.run_id JOIN scripts t ON t.id=r.script_id "
                "WHERE t.project_id=? AND r.id=? ORDER BY s.ordinal", (project_id, run_id),
            )
            return [dict(row) for row in rows]