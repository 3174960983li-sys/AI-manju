"""Streamlit scene revision UI; business rules live in revisions.py."""
import streamlit as st

from .revisions import RevisionService, export_csv, export_json


def render_scene_editor(database, project_id, run_id):
    service = RevisionService(database)
    revisions = service.list_revisions(project_id, run_id)
    revision_map = {r["id"]: r for r in revisions}
    options = ["original", *revision_map]
    key = f"revision_{run_id}"
    pending = st.session_state.pop(f"pending_revision_{run_id}", None)
    if pending in options:
        st.session_state[key] = pending
    if st.session_state.get(key) not in options:
        st.session_state[key] = revisions[0]["id"] if revisions else "original"
    st.markdown("### 4. 人工修订与导出")
    selected = st.selectbox("场次版本", options=options, format_func=lambda x: "原始模拟结果" if x == "original" else f"人工修订 r{revision_map[x]['revision_number']} · {revision_map[x]['note']}", key=key)
    revision_id = None if selected == "original" else selected
    view = service.get_view(project_id, run_id, revision_id)
    scenes = view["scenes"]
    if view["revision"]:
        st.info(f"当前查看人工修订 r{view['revision']['revision_number']}；仍未作采用确认。")
    st.caption("可以基于原始或历史版本保存新的修订；所有旧版本保留。导出只包含当前选中的已保存版本，不包含表单中的未保存修改。")
    st.dataframe([{"序号": s["ordinal"], "标题": s["heading"], "内外景": s["interior_exterior"], "地点": s["location"], "时间": s["time_of_day"], "人物": "、".join(s["characters"]), "分析／备注": s["summary"]} for s in scenes], hide_index=True, width="stretch")
    scene_map = {s["id"]: s for s in scenes}
    scene_id = st.selectbox("选择要修改的场次", options=list(scene_map), format_func=lambda x: f"{scene_map[x]['ordinal']} · {scene_map[x]['heading']}", key=f"edit_scene_{run_id}_{selected}")
    scene = scene_map[scene_id]
    suffix = f"{run_id}_{selected}_{scene_id}"
    with st.form(f"scene_edit_{suffix}"):
        heading = st.text_input("场次标题", value=scene["heading"], max_chars=500)
        choices = ["内景", "外景", "内外景", "未标注"]
        interior = st.selectbox("内外景", options=choices, index=choices.index(scene["interior_exterior"]))
        location = st.text_input("地点", value=scene["location"], max_chars=500)
        time = st.text_input("时间", value=scene["time_of_day"], max_chars=500)
        characters = st.text_area("人物（用顿号或逗号分隔，可留空）", value="、".join(scene["characters"]))
        summary = st.text_area("场次分析／备注", value=scene["summary"], max_chars=10000)
        st.caption(f"原文定位只读：[{scene['source_start']}, {scene['source_end']})")
        st.text(scene["source_text"])
        note = st.text_input("本次修订说明", max_chars=2000)
        save = st.form_submit_button("保存本场为新修订")
    if save:
        edited = [dict(s) for s in scenes]
        changed = next(s for s in edited if s["id"] == scene_id)
        changed.update(heading=heading, interior_exterior=interior, location=location, time_of_day=time, characters=characters, summary=summary)
        try:
            saved = service.save_revision(project_id, run_id, edited, note, base_revision_id=revision_id, expected_latest_id=revisions[0]["id"] if revisions else None)
            st.session_state[f"pending_revision_{run_id}"] = saved
            st.session_state["revision_success"] = "人工修订已保存，原剧本和原始模拟结果保持不变。"
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    if st.session_state.get("revision_success"):
        st.success(st.session_state.pop("revision_success"))
    version = f"r{view['revision']['revision_number']}" if view["revision"] else "original"
    col1, col2 = st.columns(2)
    col1.download_button("导出当前版本JSON", data=export_json(view), file_name=f"scenes_{run_id[:8]}_{version}.json", mime="application/json", key=f"json_{run_id}_{selected}")
    col2.download_button("导出当前版本CSV", data=export_csv(view), file_name=f"scenes_{run_id[:8]}_{version}.csv", mime="text/csv", key=f"csv_{run_id}_{selected}")
    st.caption("CSV为UTF-8 BOM，便于Windows Excel打开；以公式符号开头的文本会加单引号保护。JSON保留原值和完整来源信息。")