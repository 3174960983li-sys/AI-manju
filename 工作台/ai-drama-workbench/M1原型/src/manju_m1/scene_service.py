"""Scene analysis orchestration. This release permits mock providers only."""
import json
from uuid import uuid4

from .db import Database
from .scenes import MockSceneProvider, SceneProvider, validate_scene_response
from .service import _now


class SceneService:
    def __init__(self, database: Database):
        self.db = database

    def split(self, project_id: str, script_id: str, provider: SceneProvider | None = None) -> str:
        script = self.db.get_script(project_id, script_id)
        if not script:
            raise ValueError("剧本不存在或不属于当前项目。")
        provider = provider or MockSceneProvider()
        if provider.mode != "mock":
            raise ValueError("本轮仅允许模拟接口，不允许真实API调用。")
        try:
            raw = provider.generate(script["content"])
        except TimeoutError as exc:
            raise ValueError("模拟接口超时，未保存场次，可稍后重试。") from exc
        scenes = validate_scene_response(raw, script["content"])
        run_id = str(uuid4())
        with self.db.connection() as connection:
            connection.execute(
                "INSERT INTO scene_runs(id, script_id, provider, mode, source_sha256, raw_response, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, script_id, provider.name, "mock", script["sha256"], raw, _now()),
            )
            for scene in scenes:
                connection.execute(
                    "INSERT INTO scenes(id, run_id, ordinal, heading, interior_exterior, location, time_of_day, characters_json, summary, source_start, source_end, source_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid4()), run_id, scene["ordinal"], scene["heading"], scene["interior_exterior"],
                     scene["location"], scene["time_of_day"], json.dumps(scene["characters"], ensure_ascii=False),
                     scene["summary"], scene["source_start"], scene["source_end"], scene["source_text"]),
                )
        return run_id