"""Forms for the remaining manual production framework."""
import sqlite3
import streamlit as st

from .episodes import EpisodeService
from .production import ProductionService, FIELDS, STATES

WORKSPACES = {'镜头与分镜':'镜头', '共享资产':'资产', '制作批次':'批次', '质量检查':'质检',
              '交付与归档':'交付', '预算与工时':'资源', '变更与恢复':'变更'}


def render_production(db, project_id, kind):
    service = ProductionService(db)
    all_rows = service.list(project_id)
    rows = [r for r in all_rows if r['kind'] == kind]
    st.markdown('### ' + next(k for k,v in WORKSPACES.items() if v == kind))
    st.info('这里管理人工计划、版本与证据，不执行媒体生成。质量检查、成果采用、开工确认和阶段进度分别记录，不互相替代。')
    st.dataframe([{'ID':r['id'],'名称':r['title'],'状态':r['state'],'版本':r['version']} for r in rows], hide_index=True)
    mapping = {r['id']:r for r in rows}
    selected = st.selectbox('新建或编辑'+kind, ['new', *mapping],
                            format_func=lambda x:'＋ 新建' if x=='new' else mapping[x]['title'], key=f'prod_{project_id}_{kind}')
    row = mapping.get(selected, {})
    old = row.get('payload', {})
    episodes = {x['id']: f"第{x['number']}集 · {x['title']}" for x in EpisodeService(db).list_episodes(project_id)}
    scenes = {x['id']: f"{x['filename']} · {x['heading']} · {x['id']}" for x in service.scenes(project_id)}
    assets = {x['id']:f"{x['title']} · v{x['version']}" for x in all_rows if x['kind']=='资产'}
    targets = {x['id']:f"{x['kind']} · {x['title']} · 当前v{x['version']}" for x in all_rows if x['kind'] in ('资产','镜头','批次','交付')}
    st.caption('批次、交付的确认ID来自“确认中心”。关联后仍需你核对实际单集、版本和限定条件；不会自动生成批准。')
    st.caption('保存时记录关联单集、资产和确认记录的当前版本；之后它们更新不会改写本记录历史。再次保存前请核对是否采用新的关联版本。')
    with st.form(f'prod_form_{project_id}_{kind}_{selected}_{row.get("version",0)}'):
        title = st.text_input('记录名称', value=row.get('title',''), max_chars=120)
        state = st.selectbox('记录状态', STATES[kind], index=STATES[kind].index(row['state']) if row else 0)
        payload = {}
        for key,label in FIELDS[kind].items():
            if key in ('episode_ids','asset_ids'):
                options = episodes if key == 'episode_ids' else assets
                payload[key] = st.multiselect(label, list(options), default=old.get(key,[]), format_func=lambda x:options[x])
            elif key in ('scene_id','target_id'):
                options = scenes if key=='scene_id' else targets
                ids = ['', *options]
                payload[key] = st.selectbox(label, ids, index=ids.index(old.get(key,'')), format_func=lambda x:options.get(x,'请选择'))
            elif key in ('duration','estimate','cap','actual') and kind in ('镜头','资源'):
                payload[key] = st.number_input(label, min_value=0.0, value=float(old.get(key,0)), step=1.0)
            elif key=='target_version':
                payload[key] = st.number_input(label, min_value=1, value=old.get(key,1), step=1)
            else:
                payload[key] = st.text_area(label, value=old.get(key,''), max_chars=20000, height=80)
        acknowledge = st.checkbox('我已核对本次状态的对象、版本、证据及相关确认范围')
        save = st.form_submit_button('保存'+kind+'记录')
    if save:
        try:
            if not acknowledge:
                raise ValueError('请先核对本次记录范围。')
            service.save(project_id, kind, title, state, payload, row.get('id'), row.get('version'))
            st.session_state['flash'] = kind+'记录已保存；未改变其他记录的采用或确认状态。'
            st.rerun()
        except (ValueError, sqlite3.Error, OSError) as exc:
            st.error(str(exc))
    if row:
        with st.expander('完整记录与修订历史（只读）'):
            for item in service.history(project_id,row['id']):
                st.json(item, expanded=False)
    st.download_button('导出本项目制作框架JSON', service.export(project_id).encode('utf-8'),
                       file_name=f'production-{project_id}.json', mime='application/json')
