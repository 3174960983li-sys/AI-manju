"""Shared Streamlit shell for the twelve-stage production workflow."""
import json
from pathlib import Path

import streamlit as st

from .hub import HubService, STATES, PROGRESS, GATES, INPUTS, CAPABILITIES
from .workflow import STAGES

WORKSPACES = ["阶段工作区", "项目总览", "任务与交付", "确认中心", "规范索引", "整剧与单集", "镜头与分镜", "共享资产", "制作批次", "质量检查", "交付与归档", "预算与工时", "变更与恢复"]


def render_overview(database, project_id):
    from .production import ProductionService
    from .episodes import EpisodeService
    hub = HubService(database)
    rows = hub.overview(project_id)
    st.markdown("### 项目总览")
    counts = st.columns(3)
    counts[0].metric("手动记录已完成阶段", sum(r["进度"] == "已完成" for r in rows))
    counts[1].metric("任务与交付物", sum(r["任务"] + r["交付物"] for r in rows))
    counts[2].metric("待确认记录", sum(r["待确认"] for r in rows))
    st.dataframe(rows, hide_index=True, width="stretch")
    records = ProductionService(database).list(project_id)
    st.markdown('#### 内容与生产对象')
    st.dataframe([{'对象':'单集','数量':len(EpisodeService(database).list_episodes(project_id))}] +
                 [{'对象':kind,'数量':sum(x['kind']==kind for x in records)} for kind in ('镜头','资产','批次','质检','交付','资源','变更')], hide_index=True)
    st.info("按整剧规划后分批开发与制作。阶段进度、成果采用、质量检查和开工确认是不同结论，本页面不互相推导。")
    with st.expander("整体架构与模块接入状态"):
        st.markdown("**内容层级：整剧 → 单集 → 场次 → 镜头**；共享资产与制作任务跨层关联。批次是生产组织单位，不替代单集结构。")
        st.dataframe([
            {"模块": "项目／整剧", "状态": "已实现项目与阶段记录"},
            {"模块": "单集", "状态": "规划、剧本关联、历史与JSON导出已实现"},
            {"模块": "镜头", "状态": "关联实际场次，手工计划与素材位置记录已实现"},
            {"模块": "场次", "状态": "本地模拟、人工修订与导出已实现"},
            {"模块": "任务／交付／确认", "状态": "人工登记与历史已实现，依赖自动检查待完善"},
            {"模块": "共享资产／预算工时／批次／质检／交付／变更", "状态": "人工记录、关联、版本历史与导出已实现"},
            {"模块": "模型／视频平台", "状态": "未连接，不发生真实生成调用"},
        ], hide_index=True, width="stretch")
    st.markdown("#### 阶段入口")
    def go(stage_id):
        st.session_state[f"workflow_{project_id}"] = stage_id
        st.session_state[f"workspace_{project_id}"] = "阶段工作区"
    for offset in range(0, 12, 3):
        columns = st.columns(3)
        for col, stage in zip(columns, STAGES[offset:offset + 3]):
            col.button(stage[0] + " " + stage[1], key=f"go_{stage[0]}", on_click=go, args=(stage[0],), width="stretch")


def render_register(database, project_id, stage_id, forced_kind=None, context="global", show_all=False):
    hub = HubService(database)
    context = context + "_" + project_id
    kind = forced_kind or st.selectbox("记录类型", ["任务", "交付物"], key=f"kind_{context}")
    listed = hub.list_items(project_id, None if show_all else stage_id, kind)
    st.dataframe([{"阶段": x["stage_id"], "标题": x["title"], "状态": x["state"], "范围／版本": x["scope_ref"], "负责人": x["owner"], "成果位置": x["output_ref"], "修订": x["version"]} for x in listed], hide_index=True, width="stretch") if listed else st.info("尚无此类记录。请按实际任务或成果添加，不必一次填满全部阶段。")
    mapping = {x["id"]: x for x in listed}
    select_key = f"record_{context}_{kind}"
    pending = st.session_state.pop(f"pending_{select_key}", None)
    if pending in mapping:
        st.session_state[select_key] = pending
    if st.session_state.get(select_key) not in ["new", *mapping]:
        st.session_state[select_key] = "new"
    selected = st.selectbox("新增或编辑记录", ["new", *mapping], format_func=lambda x: "＋ 新增" if x == "new" else mapping[x]["stage_id"] + " · " + mapping[x]["title"], key=select_key)
    item = mapping.get(selected, {})
    stage_map = {s[0]: s for s in STAGES}
    if kind == "确认":
        title = st.selectbox("确认关口", list(GATES), index=list(GATES).index(item["title"]) if item else 0, disabled=bool(item), key=f"gate_{context}_{selected}")
        editing_stage = GATES[title]
        st.caption("对应阶段：" + editing_stage + " · 逐批开工／逐集采用需在范围中明确对象及版本，每个范围单独建记录。")
    else:
        editing_stage = item.get("stage_id", stage_id)
        st.caption("编辑对应阶段：" + editing_stage + " " + stage_map[editing_stage][1])
    with st.form(f"record_form_{context}_{kind}_{selected}"):
        if kind != "确认":
            title = st.text_input("记录标题", value=item.get("title", ""), max_chars=120)
        state = st.selectbox("记录状态", STATES[kind], index=STATES[kind].index(item["state"]) if item else 0)
        owner = st.text_input("负责人", value=item.get("owner", "我"))
        scope_ref = st.text_input("适用范围／具体版本", value=item.get("scope_ref", ""), help="例如整剧大纲v1、本批编号与范围、某集完成版v2。")
        input_ref = st.text_area("输入依据与版本", value=item.get("input_ref", ""))
        output_ref = st.text_input("实际成果位置", value=item.get("output_ref", ""))
        criteria = st.text_area("验收条件／检查依据", value=item.get("criteria", ""))
        note = st.text_area("说明、决定依据与限制", value=item.get("note", ""))
        confirmed = st.checkbox("我本人确认本次采用或决定及适用范围", value=False)
        save = st.form_submit_button("保存记录")
    if save:
        try:
            saved = hub.save_item(project_id, editing_stage, kind, title, state, owner, scope_ref, input_ref, output_ref, criteria, note, item_id=item.get("id"), expected_version=item.get("version"), confirmed=confirmed)
            st.session_state[f"pending_{select_key}"] = saved
            st.session_state["hub_saved"] = "记录已保存，历史版本保留。"
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    if st.session_state.get("hub_saved"):
        st.success(st.session_state.pop("hub_saved"))
    if item:
        with st.expander("记录历史与决定范围"):
            for event in hub.history(project_id, item["id"]):
                snapshot = json.loads(event["snapshot_json"])
                st.write(f"v{event['version']} · {event['created_at']} · {snapshot['state']}")
                st.json(snapshot, expanded=False)


def render_stage_framework(database, project_id, stage_id):
    st.write("建议输入：", INPUTS[stage_id])
    st.caption("专业能力映射：" + CAPABILITIES[stage_id] + "。这里只标明职责，不代表已连接或执行对应SKILL。")
    with st.expander("本阶段任务与交付物"):
        render_register(database, project_id, stage_id, context="stage_" + stage_id)
    with st.expander("手动记录阶段进度"):
        hub = HubService(database)
        row = next(x for x in hub.overview(project_id) if x["阶段"] == stage_id)
        with st.form(f"progress_{project_id}_{stage_id}"):
            state = st.selectbox("阶段进度", PROGRESS, index=PROGRESS.index(row["进度"]))
            note = st.text_area("本次进度范围说明")
            save = st.form_submit_button("保存阶段进度")
        if save:
            try:
                hub.save_progress(project_id, stage_id, state, note)
                st.success("进度已记录；不代表质量通过或开工授权。")
            except ValueError as exc:
                st.error(str(exc))


def render_library():
    st.markdown("### 规范与能力索引")
    st.caption("只读展示当前文件；候选资料不自动升级为正式规范。原SKILL不修改、不自动安装或执行。")
    root = Path(__file__).resolve().parents[3]
    sources = {"项目手册": "项目手册.md", "已确认整体架构": "体系规范/总体架构/整体协作架构.md", "公共规则（分项确认）": "体系规范/公共规则/公共规则.md"}
    selected = st.selectbox("查看规范", list(sources))
    path = root / sources[selected]
    if path.is_file():
        st.code(path.read_text(encoding="utf-8"), language="markdown")
    else:
        st.info("本机尚未提供该资料；不影响独立M1运行。")
    st.markdown("#### 专业能力职责映射")
    st.dataframe([{"阶段": s[0], "工作": s[1], "能力": CAPABILITIES[s[0]], "接入状态": "03仅本地模拟与人工编辑" if s[0] == "03" else "人工记录／待接入专业执行"} for s in STAGES], hide_index=True, width="stretch")
