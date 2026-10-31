"""Streamlit adapter for episode planning."""
import json
import sqlite3

import streamlit as st

from .episodes import EpisodeService


def render_episodes(database, project_id):
    service = EpisodeService(database)
    rows = service.list_episodes(project_id)
    st.markdown('### 整剧与单集规划')
    st.info('整剧先规划，单集分批开发。单集可关联多个剧本稿，场次由所属剧本定位；关联不代表采用，整剧稿和未分集稿可保持未分配。')
    st.dataframe([{'集数': x['number'], '名称': x['title'], '目标秒数（0待定）': x['target_seconds'],
                   '关联稿数': x['script_count'], '修订': x['version']} for x in rows], hide_index=True)
    mapping = {x['id']: x for x in rows}
    selected = st.selectbox('新建或编辑单集', ['new', *mapping],
                            format_func=lambda x: '＋ 新建单集' if x == 'new' else f"第{mapping[x]['number']}集 · {mapping[x]['title']}",
                            key=f'episode_select_{project_id}')
    row = mapping.get(selected, {})
    with st.form(f'episode_form_{project_id}_{selected}_{row.get("version", 0)}'):
        number = st.number_input('集数编号', min_value=1, max_value=9999, value=row.get('number', min(9999, max([x['number'] for x in rows], default=0) + 1)), disabled=bool(row))
        title = st.text_input('单集名称', value=row.get('title', ''), max_chars=120)
        outline = st.text_area('单集梗概与结构', value=row.get('outline', ''), max_chars=20000)
        seconds = st.number_input('目标时长（秒，0为待定）', min_value=0, max_value=86400, value=row.get('target_seconds', 0))
        save = st.form_submit_button('保存单集规划')
    if save:
        try:
            service.save(project_id, int(number), title, outline, int(seconds), row.get('id'), row.get('version'))
            st.session_state['flash'] = '单集规划已保存，未改变剧本或成片采用状态。'
            st.rerun()
        except (ValueError, OSError, sqlite3.Error) as exc:
            st.error(str(exc))
    st.download_button('导出整剧单集规划JSON', service.export(project_id).encode('utf-8'),
                       file_name=f'episode-plan-{project_id}.json', mime='application/json')
    st.caption('已有剧本可在03阶段“剧本单集归属”中关联；不自动切割整剧稿，不复制或改写正文。后续在镜头、共享资产与制作批次工作区登记执行需求。')
    if row:
        with st.expander('当前单集规划历史（只读）'):
            with database.connection() as c:
                history = c.execute('SELECT snapshot_json FROM episode_events WHERE episode_id=? ORDER BY version DESC', (row['id'],)).fetchall()
            for item in history:
                st.json(json.loads(item['snapshot_json']), expanded=False)


def render_script_assignment(database, project_id, script_id):
    service = EpisodeService(database)
    row = service.assignment(project_id, script_id)
    st.caption('剧本单集归属：' + (f"第{row['number']}集 · {row['title']}" if row else '未分配／整剧稿'))
    with st.expander('调整剧本单集归属'):
        episodes = {x['id']: x for x in service.list_episodes(project_id)}
        choices = [None, *episodes]
        with st.form(f'assign_{project_id}_{script_id}_{row["id"] if row else "none"}'):
            target = st.selectbox('归属单集', choices, index=choices.index(row['id']) if row else 0,
                                  format_func=lambda x: '未分配／整剧稿' if x is None else f"第{episodes[x]['number']}集 · {episodes[x]['title']}")
            note = st.text_input('归属调整说明', max_chars=2000)
            confirmed = st.checkbox('确认仅调整本剧本归属，其场次随剧本关联；不代表采用')
            save = st.form_submit_button('保存剧本单集归属')
        if save:
            try:
                if not confirmed:
                    raise ValueError('请先确认归属调整范围。')
                service.assign(project_id, script_id, target, row['id'] if row else None, note)
                st.session_state['flash'] = '剧本单集归属已保存。'
                st.rerun()
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(str(exc))
        with database.connection() as c:
            history = [dict(x) for x in c.execute('SELECT episode_id,note,created_at FROM script_episode_events WHERE project_id=? AND script_id=? ORDER BY created_at DESC', (project_id, script_id))]
        if history:
            st.dataframe(history, hide_index=True)
