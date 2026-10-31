"""Typed manual production records; never execute media or infer approval."""
import json
from uuid import uuid4

from .service import _now

SCHEMA = """
CREATE TABLE IF NOT EXISTS production_records (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), kind TEXT NOT NULL,
 title TEXT NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL,
 version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS production_events (
 id TEXT PRIMARY KEY, record_id TEXT NOT NULL REFERENCES production_records(id),
 version INTEGER NOT NULL, snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(record_id,version)
);
"""

# Field descriptions are shared by the form and business validation.
FIELDS = {
 '镜头': {'scene_id': '来源场次ID', 'intent': '镜头意图与人物行动', 'method': '景别、机位、运镜与声画切点', 'duration': '计划时长（秒）', 'asset_ids': '使用资产', 'output': '候选素材位置与版本', 'note': '连续性与限制'},
 '资产': {'category': '类别（角色／造型／空间／道具／声音）', 'spec': '身份、状态与一致性要求', 'output': '文件位置与版本', 'rights': '来源与使用权限依据', 'note': '适用范围与限制'},
 '批次': {'episode_ids': '所含单集', 'inputs': '本批输入版本与准备条件', 'owner': '负责人', 'schedule': '计划起止与工期', 'cap': '资源上限说明', 'gate': '开工确认记录ID', 'note': '未决问题与依赖'},
 '质检': {'target_id': '被检查对象', 'target_version': '实际检查版本号', 'scope': '实际看听或测量范围', 'criteria': '检查标准', 'evidence': '证据位置与时间码', 'findings': '问题、严重度与返修建议', 'note': '未检查范围与限制'},
 '交付': {'episode_ids': '所含单集', 'spec': '输出规格与命名', 'output': '完成版或归档包位置与版本', 'manifest': '文件清单与校验值', 'restore': '工程依赖与恢复验证', 'gate': '交付验收记录ID', 'note': '缺失项与限制'},
 '资源': {'scope': '预算或工时对象与版本', 'unit': '单位（元／小时等）', 'estimate': '预计投入', 'cap': '批准上限', 'actual': '实际投入', 'evidence': '账单或工时依据', 'note': '估算假设与差异'},
 '变更': {'scope': '变更对象与版本', 'reason': '触发原因', 'impact': '受影响成果、成本与排期', 'plan': '执行与回退方案', 'evidence': '决定依据与恢复检查', 'note': '未决事项'},
}
STATES = {
 '镜头': ['计划', '待制作', '候选待检查', '需返修'],
 '资产': ['需求', '设计中', '候选待检查', '需返修', '停用'],
 '批次': ['筹备', '待开工确认', '制作中（人工记录）', '待集中审看', '本批结束（人工记录）'],
 '质检': ['待检查', '检查中', '发现问题', '本次范围未发现问题', '需复核'],
 '交付': ['准备', '待验收', '已交付（人工记录）', '已归档（人工记录）'],
 '资源': ['估算', '跟踪中', '结算记录'],
 '变更': ['提议', '待决定', '执行中（人工记录）', '已复核（人工记录）', '暂缓'],
}


class ProductionService:
    def __init__(self, db):
        self.db = db

    def list(self, project_id, kind=None):
        if not self.db.get_project(project_id):
            raise ValueError('项目不存在。')
        with self.db.connection() as c:
            sql = 'SELECT * FROM production_records WHERE project_id=?'
            args = [project_id]
            if kind:
                sql += ' AND kind=?'
                args.append(kind)
            return [dict(r, payload=json.loads(r['payload_json'])) for r in c.execute(sql+' ORDER BY created_at,id', args)]

    def scenes(self, project_id):
        with self.db.connection() as c:
            return [dict(r) for r in c.execute(
                'SELECT s.id,s.heading,s.ordinal,r.id AS run_id,t.filename,b.episode_id FROM scenes s '
                'JOIN scene_runs r ON r.id=s.run_id JOIN scripts t ON t.id=r.script_id '
                'LEFT JOIN script_episodes b ON b.script_id=t.id WHERE t.project_id=?', (project_id,))]

    def save(self, project_id, kind, title, state, payload, record_id=None, expected_version=None):
        if kind not in FIELDS or state not in STATES[kind]:
            raise ValueError('类型或状态无效。')
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            raise ValueError('名称须为1—120字。')
        if not isinstance(payload, dict) or set(payload) != set(FIELDS[kind]):
            raise ValueError('记录字段不完整或包含未知字段。')
        p = dict(payload)
        for key, value in p.items():
            if key in ('episode_ids', 'asset_ids'):
                if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
                    raise ValueError('关联对象须为ID列表。')
                p[key] = list(dict.fromkeys(value))
            elif key in ('duration', 'estimate', 'cap', 'actual') and kind in ('镜头', '资源'):
                import math
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError('投入或时长必须为非负有限数字。')
            elif key == 'target_version':
                if type(value) is not int or value < 1:
                    raise ValueError('被检查版本须为正整数。')
            elif not isinstance(value, str) or len(value) > 20000:
                raise ValueError('文字字段格式或长度无效。')
        now = _now()
        with self.db.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            if not c.execute('SELECT 1 FROM projects WHERE id=?', (project_id,)).fetchone():
                raise ValueError('项目不存在。')
            old = c.execute('SELECT * FROM production_records WHERE id=? AND project_id=?', (record_id, project_id)).fetchone() if record_id else None
            if record_id and (not old or old['kind'] != kind):
                raise ValueError('记录不存在或不属于当前项目及类型。')
            if old and old['version'] != expected_version:
                raise ValueError('已有新版本，请刷新后重试。')
            for eid in p.get('episode_ids', []):
                if not c.execute('SELECT 1 FROM episodes WHERE project_id=? AND id=?', (project_id, eid)).fetchone():
                    raise ValueError('关联单集不属于当前项目。')
            linked_versions = {}
            for eid in p.get('episode_ids', []):
                linked_versions[eid] = c.execute('SELECT version FROM episodes WHERE id=?', (eid,)).fetchone()[0]
            for aid in p.get('asset_ids', []):
                if not c.execute("SELECT 1 FROM production_records WHERE project_id=? AND id=? AND kind='资产'", (project_id, aid)).fetchone():
                    raise ValueError('关联资产不属于当前项目。')
                linked_versions[aid] = c.execute('SELECT version FROM production_records WHERE id=?', (aid,)).fetchone()[0]
            if kind == '镜头':
                if p['scene_id'] not in {x['id'] for x in self.scenes(project_id)}:
                    raise ValueError('请选择本项目实际场次；先在03阶段保存场次。')
                if not p['intent'].strip():
                    raise ValueError('镜头需要明确意图与人物行动。')
            if kind in ('批次', '交付') and not p['episode_ids']:
                raise ValueError('请明确包含的单集。')
            if kind == '质检':
                target = c.execute('SELECT * FROM production_records WHERE id=? AND project_id=?', (p['target_id'], project_id)).fetchone()
                if not target or target['kind'] in ('质检', '资源', '变更'):
                    raise ValueError('请选择本项目镜头、资产、批次或交付对象。')
                snapshot = c.execute('SELECT 1 FROM production_events WHERE record_id=? AND version=?', (p['target_id'], p['target_version'])).fetchone()
                if not snapshot:
                    raise ValueError('被检查版本不存在。')
                if state not in ('待检查', '检查中') and any(not p[k].strip() for k in ('scope','criteria','evidence','findings')):
                    raise ValueError('检查结论必须包含实际范围、标准、证据与发现。')
            gate = p.get('gate', '').strip()
            if gate:
                wanted = '本批开工' if kind == '批次' else '最终交付验收'
                row = c.execute("SELECT * FROM work_items WHERE id=? AND project_id=? AND kind='确认' AND title=?", (gate, project_id, wanted)).fetchone()
                if not row:
                    raise ValueError('确认记录不存在或关口类型不匹配。')
                linked_versions[gate] = row['version']
            if kind == '批次' and state in ('制作中（人工记录）', '待集中审看', '本批结束（人工记录）'):
                if not gate or row['state'] not in ('通过', '限定通过'):
                    raise ValueError('本批制作状态需要关联已通过的开工记录；请人工核对其范围与版本。')
            if kind == '交付' and state in ('已交付（人工记录）', '已归档（人工记录）'):
                if not gate or row['state'] not in ('通过', '限定通过') or not p['output'].strip() or not p['manifest'].strip():
                    raise ValueError('交付记录需要验收依据、实际位置和文件清单。')
                if state == '已归档（人工记录）' and not p['restore'].strip():
                    raise ValueError('归档需要填写工程依赖与恢复验证记录。')
            # Snapshot references at save time; later asset/episode/gate edits do not rewrite history.
            p['_reference_versions'] = linked_versions
            record_id = record_id or str(uuid4())
            version = old['version'] + 1 if old else 1
            c.execute('INSERT INTO production_records VALUES(?,?,?,?,?,?,?,?,?) '
                      'ON CONFLICT(id) DO UPDATE SET title=excluded.title,state=excluded.state,payload_json=excluded.payload_json,version=excluded.version,updated_at=excluded.updated_at',
                      (record_id, project_id, kind, title.strip(), state, json.dumps(p, ensure_ascii=False), version, old['created_at'] if old else now, now))
            snapshot = dict(c.execute('SELECT * FROM production_records WHERE id=?', (record_id,)).fetchone())
            c.execute('INSERT INTO production_events VALUES(?,?,?,?,?)', (str(uuid4()), record_id, version, json.dumps(snapshot,ensure_ascii=False), now))
        return record_id

    def history(self, project_id, record_id):
        with self.db.connection() as c:
            return [json.loads(r[0]) for r in c.execute('SELECT e.snapshot_json FROM production_events e JOIN production_records r ON r.id=e.record_id WHERE r.project_id=? AND r.id=? ORDER BY e.version DESC', (project_id, record_id))]

    def export(self, project_id):
        return json.dumps({'schema_version':1, 'project_id':project_id, 'status':'人工制作记录，不代表自动执行或质量采用', 'records':self.list(project_id)}, ensure_ascii=False, indent=2)
