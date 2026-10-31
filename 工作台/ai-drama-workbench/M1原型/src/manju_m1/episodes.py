"""Episode planning and explicit script assignment, without altering source scripts."""
import json
import sqlite3
from uuid import uuid4

from .service import _now


class EpisodeService:
    def __init__(self, database):
        self.db = database

    def list_episodes(self, project_id):
        with self.db.connection() as c:
            return [dict(r) for r in c.execute(
                "SELECT e.*, count(b.script_id) AS script_count FROM episodes e "
                "LEFT JOIN script_episodes b ON b.episode_id=e.id "
                "WHERE e.project_id=? GROUP BY e.id ORDER BY e.number", (project_id,))]

    def save(self, project_id, number, title, outline='', target_seconds=0, episode_id=None, expected_version=None):
        if type(number) is not int or not 1 <= number <= 9999:
            raise ValueError('集数须为1—9999的整数。')
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise ValueError('单集名称须为1—120字。')
        if not isinstance(outline, str) or len(outline) > 20000:
            raise ValueError('单集梗概不能超过2万字。')
        if type(target_seconds) is not int or not 0 <= target_seconds <= 86400:
            raise ValueError('目标时长须为0—86400秒，0表示待定。')
        now = _now()
        try:
            with self.db.connection() as c:
                c.execute('BEGIN IMMEDIATE')
                if not c.execute('SELECT 1 FROM projects WHERE id=?', (project_id,)).fetchone():
                    raise ValueError('项目不存在。')
                if episode_id:
                    old = c.execute('SELECT * FROM episodes WHERE id=? AND project_id=?', (episode_id, project_id)).fetchone()
                    if not old:
                        raise ValueError('单集不存在或不属于当前项目。')
                    if expected_version != old['version']:
                        raise ValueError('单集已被更新，请刷新后再保存。')
                    if number != old['number']:
                        raise ValueError('已建立的集数编号不可修改，请保留稳定标识。')
                    version = old['version'] + 1
                    c.execute('UPDATE episodes SET title=?,outline=?,target_seconds=?,version=?,updated_at=? WHERE id=?',
                              (title.strip(), outline.strip(), target_seconds, version, now, episode_id))
                else:
                    episode_id, version = str(uuid4()), 1
                    c.execute('INSERT INTO episodes VALUES(?,?,?,?,?,?,?,?,?)',
                              (episode_id, project_id, number, title.strip(), outline.strip(), target_seconds, version, now, now))
                snapshot = dict(c.execute('SELECT * FROM episodes WHERE id=?', (episode_id,)).fetchone())
                c.execute('INSERT INTO episode_events VALUES(?,?,?,?,?)',
                          (str(uuid4()), episode_id, version, json.dumps(snapshot, ensure_ascii=False), now))
        except sqlite3.IntegrityError as exc:
            raise ValueError('同一项目的集数编号不能重复。') from exc
        return episode_id

    def assignment(self, project_id, script_id):
        with self.db.connection() as c:
            r = c.execute('SELECT e.* FROM script_episodes b JOIN episodes e ON e.id=b.episode_id '
                          'WHERE b.project_id=? AND b.script_id=?', (project_id, script_id)).fetchone()
            return dict(r) if r else None

    def assign(self, project_id, script_id, episode_id, expected_episode_id, note):
        if not isinstance(note, str) or not 1 <= len(note.strip()) <= 2000:
            raise ValueError('请填写1—2000字的归属调整说明。')
        with self.db.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            if not c.execute('SELECT 1 FROM scripts WHERE id=? AND project_id=?', (script_id, project_id)).fetchone():
                raise ValueError('剧本不存在或不属于当前项目。')
            if episode_id and not c.execute('SELECT 1 FROM episodes WHERE id=? AND project_id=?', (episode_id, project_id)).fetchone():
                raise ValueError('单集不存在或不属于当前项目。')
            old = c.execute('SELECT episode_id FROM script_episodes WHERE script_id=?', (script_id,)).fetchone()
            old_id = old['episode_id'] if old else None
            if old_id != expected_episode_id:
                raise ValueError('剧本归属已改变，请刷新后重新确认。')
            if old_id == episode_id:
                return
            c.execute('DELETE FROM script_episodes WHERE script_id=?', (script_id,))
            if episode_id:
                c.execute('INSERT INTO script_episodes VALUES(?,?,?)', (script_id, project_id, episode_id))
            c.execute('INSERT INTO script_episode_events VALUES(?,?,?,?,?,?)',
                      (str(uuid4()), project_id, script_id, episode_id, note.strip(), _now()))

    def export(self, project_id):
        if not self.db.get_project(project_id):
            raise ValueError('项目不存在。')
        with self.db.connection() as c:
            assignments = [dict(r) for r in c.execute(
                'SELECT b.script_id,b.episode_id,s.filename FROM script_episodes b '
                'JOIN scripts s ON s.id=b.script_id WHERE b.project_id=?', (project_id,))]
        return json.dumps({'schema_version': 1, 'project_id': project_id,
                           'status': '规划记录，未作剧本或成片采用确认',
                           'episodes': self.list_episodes(project_id), 'script_assignments': assignments}, ensure_ascii=False, indent=2)
