"""M1 UI: create project, import script, inspect persisted text."""
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))
from manju_m1.db import Database
from manju_m1.service import ProjectService
from manju_m1.scene_service import SceneService
from manju_m1.workflow import STAGES
from manju_m1.ui_scenes import render_scene_editor
from manju_m1.ui_hub import WORKSPACES, render_overview, render_register, render_stage_framework, render_library

st.set_page_config(page_title="AI-manju · M1流程与剧本", page_icon="🎬", layout="wide")
logger = logging.getLogger(__name__)


def main():
    database = Database(os.environ.get("MANJU_M1_DB_PATH", str(BASE_DIR / "data" / "manju_m1.sqlite3")))
    try:
        database.initialize()
    except (OSError, sqlite3.Error, ValueError):
        logger.exception("Database initialization failed")
        st.error("数据库无法初始化。请检查路径、写入权限和数据库版本，勿覆盖原数据库。")
        st.stop()
    service = ProjectService(database)
    st.title("AI短剧工作台 · M1")
    st.caption("按12阶段SOP组织准备记录；框架覆盖项目总览、12阶段、任务交付、确认与规范；03已有剧本处理，不调用真实模型。")

    with st.sidebar:
        st.header("项目")
        with st.form("create_project", clear_on_submit=True):
            name = st.text_input("项目名称", max_chars=120)
            description = st.text_area("项目简介", max_chars=5000)
            create = st.form_submit_button("创建项目")
        if create:
            try:
                project_id = service.create_project(name, description)
                st.session_state["active_project"] = project_id
                st.session_state["flash"] = "项目已创建，已保存到SQLite。"
            except ValueError as exc:
                st.error(str(exc))
            except (OSError, sqlite3.Error):
                logger.exception("Project creation failed")
                st.error("保存项目失败，请检查磁盘和数据库权限。")
        projects = database.list_projects()
        if not projects:
            st.info("请先创建一个项目。")
        else:
            project_map = {p["id"]: p for p in projects}
            if st.session_state.get("active_project") not in project_map:
                st.session_state["active_project"] = projects[0]["id"]
            st.selectbox("当前项目", options=list(project_map), format_func=lambda x: project_map[x]["name"], key="active_project")
        st.caption("数据库位置")
        st.code(str(database.path), language=None)
        st.info("SOP与SKILL原件保持只读。本程序不扫描、改写或执行SKILL。")

    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))
    if not projects:
        st.info("从左侧创建项目，然后上传你的剧本。")
        return
    project_id = st.session_state["active_project"]
    project = database.get_project(project_id)
    st.subheader(project["name"])
    if project["description"]:
        st.write(project["description"])
    stage_map = {stage[0]: stage for stage in STAGES}
    with st.sidebar:
        stage_id = st.selectbox("工作阶段", options=list(stage_map), index=2, format_func=lambda x: x + " " + stage_map[x][1], key=f"workflow_{project_id}")
        workspace = st.radio("工作区", WORKSPACES, key=f"workspace_{project_id}")
    if workspace == "项目总览":
        render_overview(database, project_id)
        return
    if workspace == "任务与交付":
        st.markdown("### 任务与交付")
        st.caption("当前可新增左侧所选阶段记录，也可编辑下方已有记录；不同项目独立保存。")
        render_register(database, project_id, stage_id, context="global", show_all=True)
        return
    if workspace == "确认中心":
        st.markdown("### 确认中心")
        st.info("确认由你本人记录。批次与单集模块尚未完整实现，本轮用明确的对象、范围和版本作人工记录，不自动放行生产。")
        render_register(database, project_id, stage_id, forced_kind="确认", context="gates", show_all=True)
        return
    if workspace == "规范索引":
        render_library()
        return
    stage = stage_map[stage_id]
    st.markdown(f"### {stage[0]} · {stage[1]}")
    st.write("本阶段关注：", stage[2])
    st.write("预期交付：", stage[3])
    with st.expander("12阶段框架与确认边界"):
        st.dataframe([{"阶段": s[0], "名称": s[1], "成果": s[3]} for s in STAGES], hide_index=True, width="stretch")
        st.info("项目立项、整剧创作基准、首批创作方向和生产基准由你确认；正式制作逐批开工、成片逐集采用。当前页面仅保存准备记录，不自动完成这些确认。")
        st.caption("整剧—单集—场次—镜头是已定结构；本M1只建立项目、剧本及场次，不表示单集和镜头模块已实现。")
    render_stage_framework(database, project_id, stage_id)
    with st.expander("阶段准备记录", expanded=stage_id != "03"):
        with st.form(f"stage_notes_{project_id}_{stage_id}"):
            notes = st.text_area("阶段准备记录（不代表已通过）", value=database.get_stage_notes(project_id, stage_id), max_chars=100000, height=160)
            save_notes = st.form_submit_button("保存阶段准备记录")
        if save_notes:
            try:
                service.save_stage_notes(project_id, stage_id, notes)
                st.success("阶段准备记录已保存；未改变采用或验收状态。")
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(f"阶段记录未保存：{exc}")
    if stage_id != "03":
        st.info("本阶段可登记任务、交付物、准备内容和进度。专业执行尚未接入；03阶段已有剧本导入、模拟拆分、人工修订和导出。")
        return
    st.markdown("### 1. 上传剧本")
    uploaded = st.file_uploader("选择TXT或DOCX剧本（最大5MB）", type=["txt", "docx"], key=f"upload_{project_id}")
    options = {"自动（UTF-8 / GB18030 / BOM）": None, "UTF-8": "utf-8-sig", "GB18030": "gb18030", "UTF-16（带BOM）": "utf-16"}
    encoding_label = st.selectbox("TXT编码（DOCX不使用此选项）", options=list(options), key=f"encoding_{project_id}")
    st.caption("读取DOCX正文段落和表格；文本框、修订、页眉页脚及图片文字不保证提取。原始文件字节与提取正文一起保存，便于核对。")
    if st.button("读取并保存剧本", type="primary", disabled=uploaded is None):
        try:
            script_id, created = service.import_script(project_id, uploaded.name, uploaded.getvalue(), options[encoding_label])
            st.session_state[f"script_{project_id}"] = script_id
            if created:
                st.success("剧本正文和原件已保存到SQLite。")
            else:
                st.info("该项目已导入相同原件，本次使用已有记录，没有重复写入。")
        except ValueError as exc:
            st.error(str(exc))
        except (OSError, sqlite3.Error):
            logger.exception("Script import failed")
            st.error("剧本保存失败，请检查磁盘和数据库权限；已有剧本未被覆盖。")

    st.markdown("### 2. 已保存剧本")
    scripts = database.list_scripts(project_id)
    if not scripts:
        st.info("该项目还没有已保存剧本。")
        return
    script_map = {s["id"]: s for s in scripts}
    key = f"script_{project_id}"
    if st.session_state.get(key) not in script_map:
        st.session_state[key] = scripts[0]["id"]
    script_id = st.selectbox("选择已保存剧本", options=list(script_map), format_func=lambda x: f"{script_map[x]['filename']} · {script_map[x]['char_count']}字 · {script_map[x]['created_at'][:19]} UTC", key=key)
    script = database.get_script(project_id, script_id)
    cols = st.columns(3)
    cols[0].metric("正文字符数", len(script["content"]))
    cols[1].metric("原件大小", f"{len(script['original_bytes']) / 1024:.1f} KB")
    cols[2].metric("读取格式", script["encoding"])
    if script["warning"]:
        st.warning(script["warning"])
    st.text_area("已保存正文（只读）", value=script["content"], height=420, disabled=True, key=f"preview_{script_id}")
    st.caption("原剧本保持只读；模拟结果可在下方另存人工修订，并导出指定版本。")
    st.markdown("### 3. 模拟场次拆分")
    st.warning("当前是本地规则模拟，不是大语言模型分析，不调用API、不计费。只用于验证场次字段、原文对应与保存流程，不能视为导演逐场分析或已采用分镜。")
    st.caption("优先识别“第一场 内景 门厅 夜”、带空格的“1-1 地点 时间”及INT./EXT.标题；无法识别时全文保存为一个待核对片段。人物只按对白冒号前的名称提取。")
    if st.button("模拟拆分并保存场次", type="primary"):
        try:
            run_id = SceneService(database).split(project_id, script_id)
            st.session_state[f"run_{script_id}"] = run_id
            st.success("模拟结果已校验并保存。请逐场对照原文；尚未作采用确认。")
        except ValueError as exc:
            st.error(str(exc))
        except (OSError, sqlite3.Error):
            logger.exception("Mock scene save failed")
            st.error("场次保存失败，已有剧本与旧拆分记录未被覆盖。")
    runs = database.list_scene_runs(project_id, script_id)
    if runs:
        run_map = {run["id"]: run for run in runs}
        run_key = f"run_{script_id}"
        if st.session_state.get(run_key) not in run_map:
            st.session_state[run_key] = runs[0]["id"]
        run_id = st.selectbox("查看拆分记录", options=list(run_map), format_func=lambda x: f"模拟 · {run_map[x]['scene_count']}场 · {run_map[x]['created_at'][:19]} UTC", key=run_key)
        scenes = database.get_scenes(project_id, run_id)
        st.caption(f"接口：{run_map[run_id]['provider']} · 状态：模拟结果／待人工核对 · 原件SHA-256：{run_map[run_id]['source_sha256']}")
        st.dataframe([{"场次": scene["ordinal"], "标题": scene["heading"], "内外景": scene["interior_exterior"], "地点": scene["location"], "时间": scene["time_of_day"], "人物": "、".join(json.loads(scene["characters_json"]))} for scene in scenes], hide_index=True, width="stretch")
        st.markdown("#### 原始模拟结果与原文（只读）")
        for scene in scenes:
            with st.expander(f"场次 {scene['ordinal']} · {scene['heading']}"):
                st.write("原文摘录（不是AI剧情概括）：", scene["summary"])
                st.caption(f"提取正文字符区间 [{scene['source_start']}, {scene['source_end']})；从0开始，右端不包含。DOCX定位对应提取正文，不对应Word页码。")
                st.text(scene["source_text"])
        try:
            render_scene_editor(database, project_id, run_id)
        except (ValueError, OSError, sqlite3.Error) as exc:
            st.error(f"修订或导出未完成：{exc}")
    else:
        st.info("当前剧本还没有拆分记录。每次模拟会保存独立记录，不覆盖旧结果。")
    with st.expander("原件校验信息"):
        st.write("剧本ID：", script["id"])
        st.write("SHA-256：", script["sha256"])


if __name__ == "__main__":
    main()