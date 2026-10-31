import json
import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from manju_m1.db import Database
from manju_m1.service import ProjectService
from manju_m1.episodes import EpisodeService
from manju_m1.scene_service import SceneService
from manju_m1.hub import HubService
from manju_m1.production import ProductionService, FIELDS, STATES
from manju_m1.ui_production import WORKSPACES


def payload(kind, **changes):
    result = {key: ([] if key.endswith('_ids') else 1 if key=='target_version' else 0.0 if key in ('duration','estimate','cap','actual') and kind in ('镜头','资源') else '') for key in FIELDS[kind]}
    result.update(changes)
    return result


@pytest.fixture
def setup(tmp_path):
    db=Database(tmp_path/'production.sqlite3')
    db.initialize()
    p=ProjectService(db)
    a,b=p.create_project('甲'),p.create_project('乙')
    eid=EpisodeService(db).save(a,1,'开局')
    sid,_=p.import_script(a,'第一集.txt','第一场 内景 门厅 夜\n甲：谁？'.encode())
    EpisodeService(db).assign(a,sid,eid,None,'确认归属')
    run=SceneService(db).split(a,sid)
    scene=db.get_scenes(a,run)[0]['id']
    return db,a,b,eid,scene,ProductionService(db)


def gate(db,pid,title,scope='第一集v1'):
    stage='08' if title=='本批开工' else '12'
    return HubService(db).save_item(pid,stage,'确认',title,'通过','本人',scope,'依据v1','完成版v1','人工核对','确认本范围',confirmed=True)


def test_shot_asset_scope_history_and_stale_edit(setup):
    db,a,b,eid,scene,s=setup
    asset=s.save(a,'资产','门厅','需求',payload('资产',spec='固定空间锚点'))
    shot_payload=payload('镜头',scene_id=scene,intent='观察门后反应',asset_ids=[asset],duration=3)
    shot=s.save(a,'镜头','反应镜头','计划',shot_payload)
    s.save(a,'镜头','反应镜头修订','待制作',shot_payload,shot,1)
    with pytest.raises(ValueError,match='新版本'):
        s.save(a,'镜头','旧页','计划',shot_payload,shot,1)
    assert [x['version'] for x in s.history(a,shot)]==[2,1]
    s.save(a,'资产','门厅v2','设计中',payload('资产'),asset,1)
    latest_shot = next(r for r in s.list(a) if r['id']==shot)
    assert latest_shot['payload']['_reference_versions'][asset]==1
    assert s.history(b,shot)==[]
    assert s.list(b)==[]
    with pytest.raises(ValueError,match='场次'):
        s.save(b,'镜头','跨项目','计划',payload('镜头',scene_id=scene,intent='测试'))
    with pytest.raises(ValueError,match='资产'):
        s.save(b,'镜头','跨资产','计划',shot_payload)
    assert s.scenes(a)[0]['episode_id']==eid


def test_batch_and_delivery_require_matching_gate_type(setup):
    db,a,b,eid,scene,s=setup
    bp=payload('批次',episode_ids=[eid])
    with pytest.raises(ValueError,match='开工'):
        s.save(a,'批次','首批','制作中（人工记录）',bp)
    bp['gate']=gate(db,a,'本批开工')
    batch=s.save(a,'批次','首批','制作中（人工记录）',bp)
    assert s.list(a)[0]['id']==batch
    dp=payload('交付',episode_ids=[eid],gate=bp['gate'],output='成片v1',manifest='file.mp4 sha256:待核对')
    with pytest.raises(ValueError,match='类型不匹配'):
        s.save(a,'交付','交付包','已交付（人工记录）',dp)
    dp['gate']=gate(db,a,'最终交付验收')
    with pytest.raises(ValueError,match='恢复验证'):
        s.save(a,'交付','交付包','已归档（人工记录）',dp)
    dp['restore']='工程依赖清单与本次恢复记录'
    s.save(a,'交付','交付包','已归档（人工记录）',dp)
    with pytest.raises(ValueError,match='单集'):
        s.save(b,'批次','跨集','筹备',bp)


def test_review_evidence_and_exact_historical_version(setup):
    db,a,b,eid,scene,s=setup
    asset=s.save(a,'资产','空间母版','需求',payload('资产'))
    qp=payload('质检',target_id=asset,target_version=1)
    with pytest.raises(ValueError,match='范围'):
        s.save(a,'质检','检查','本次范围未发现问题',qp)
    qp.update(scope='只检查门窗位置',criteria='锚点清单',evidence='参考图v1#A',findings='此范围未发现问题')
    review=s.save(a,'质检','检查','本次范围未发现问题',qp)
    s.save(a,'资产','空间v2','设计中',payload('资产'),asset,1)
    assert next(r for r in s.list(a) if r['id']==review)['payload']['target_version']==1
    assert next(r for r in s.list(a) if r['id']==asset)['state']=='设计中'
    qp['target_version']=999
    with pytest.raises(ValueError,match='版本不存在'):
        s.save(a,'质检','错误版本','待检查',qp)
    qp['target_version']=1
    with pytest.raises(ValueError,match='本项目'):
        s.save(b,'质检','跨项目','待检查',qp)


@pytest.mark.parametrize('value',[-1,float('nan'),float('inf'),True])
def test_invalid_resource_numbers_rejected(setup,value):
    db,a,b,eid,scene,s=setup
    with pytest.raises(ValueError,match='非负有限'):
        s.save(a,'资源','费用','估算',payload('资源',actual=value))
    assert not s.list(a)


def test_v5_upgrade_and_scoped_export(setup):
    db,a,b,eid,scene,s=setup
    with db.connection() as c:
        c.execute('DROP TABLE production_events')
        c.execute('DROP TABLE production_records')
        c.execute('PRAGMA user_version=5')
    db.initialize()
    with sqlite3.connect(db.path.with_suffix('.before-v6.sqlite3')) as c:
        assert c.execute('PRAGMA user_version').fetchone()[0]==5
        assert c.execute('SELECT count(*) FROM scripts').fetchone()[0]==1
    s.save(a,'变更','调整计划','提议',payload('变更',scope='单集v1',reason='工期变化'))
    assert json.loads(s.export(a))['records'][0]['kind']=='变更'
    assert json.loads(s.export(b))['records']==[]
    with db.connection() as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_all_workspace_forms_and_save_asset(setup,monkeypatch):
    db,a,b,eid,scene,s=setup
    monkeypatch.setenv('MANJU_M1_DB_PATH',str(db.path))
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=20)
    next(x for x in app.selectbox if x.label=='当前项目').select(a).run()
    for workspace in WORKSPACES:
        next(x for x in app.radio if x.label=='工作区').set_value(workspace).run()
        assert not app.exception, workspace
    next(x for x in app.radio if x.label=='工作区').set_value('共享资产').run()
    next(x for x in app.text_input if x.label=='记录名称').set_value('门厅母版')
    next(x for x in app.checkbox if x.label.startswith('我已核对')).check()
    next(x for x in app.button if x.label=='保存资产记录').click().run()
    assert not app.exception
    assert s.list(a,'资产')[0]['title']=='门厅母版'
