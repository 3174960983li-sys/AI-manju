"""Mock-only scene provider and strict source-grounded response validation."""
import json
import re
from typing import Protocol


class SceneProvider(Protocol):
    name: str
    mode: str

    def generate(self, script: str) -> str: ...


HEADING = re.compile(
    r"(?m)^[ \t]*(?:第[零〇一二三四五六七八九十百千两\d]+场[^\n]*|\d+[-－]\d+[ \t]+[^\n]+|(?:INT\.|EXT\.|INT/EXT\.)[^\n]+)[ \t]*$",
    re.IGNORECASE,
)


class MockSceneProvider:
    name = "mock-rules-v1"
    mode = "mock"

    def generate(self, script: str) -> str:
        matches = list(HEADING.finditer(script))
        if len(matches) > 2000:
            raise ValueError("模拟拆分超过2000场，请先拆分剧本。")
        starts = [0] + [m.start() for m in matches[1:]] if matches else [0]
        scenes = []
        for i, start in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else len(script)
            source = script[start:end]
            heading = matches[i].group().strip() if matches else "未识别场次标题：全文暂作一个片段"
            inner = "内景" if re.search(r"内景|\bINT\.", heading, re.I) else "外景" if re.search(r"外景|\bEXT\.", heading, re.I) else "未标注"
            if "内外景" in heading or "INT/EXT." in heading.upper():
                inner = "内外景"
            remainder = re.sub(r"^(?:第[零〇一二三四五六七八九十百千两\d]+场|\d+[-－]\d+|INT/EXT\.|INT\.|EXT\.)", "", heading, flags=re.I).strip()
            remainder = re.sub(r"^(?:内外景|内景|外景)[ \t]*", "", remainder).strip()
            parts = remainder.split()
            time = parts[-1] if parts and parts[-1] in {"日", "夜", "晨", "清晨", "黄昏", "傍晚", "白天", "晚上", "深夜", "黎明", "上午", "下午"} else "未标注"
            location = " ".join(parts[:-1] if time != "未标注" else parts) if matches else "未标注"
            actors = list(dict.fromkeys(re.findall(r"(?m)^[ \t]*([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9· ]{0,19})[：:]", source)))
            scenes.append({"ordinal": i + 1, "heading": heading, "interior_exterior": inner,
                           "location": location or "未标注", "time_of_day": time,
                           "characters": actors, "summary": source.strip()[:120],
                           "source_start": start, "source_end": end, "source_text": source})
        return json.dumps({"scenes": scenes}, ensure_ascii=False)


def validate_scene_response(raw: str, script: str) -> list[dict]:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("拆分响应不是有效JSON，未保存任何场次。") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
        raise ValueError("拆分响应缺少scenes列表。")
    scenes = payload["scenes"]
    if not 1 <= len(scenes) <= 2000:
        raise ValueError("场次数须在1—2000之间。")
    cursor = 0
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError("每个场次必须是对象。")
        for key in ["heading", "interior_exterior", "location", "time_of_day", "summary", "source_text"]:
            if not isinstance(scene.get(key), str) or not scene[key].strip():
                raise ValueError(f"场次缺少有效字段：{key}")
        if type(scene.get("ordinal")) is not int or scene["ordinal"] != index + 1:
            raise ValueError("场次序号必须连续。")
        start, end = scene.get("source_start"), scene.get("source_end")
        if type(start) is not int or type(end) is not int or start != cursor or not start < end <= len(script):
            raise ValueError("场次原文范围不连续或越界。")
        if scene["source_text"] != script[start:end]:
            raise ValueError("场次原文与导入剧本不一致。")
        if scene["interior_exterior"] not in {"内景", "外景", "内外景", "未标注"}:
            raise ValueError("内外景字段无效。")
        actors = scene.get("characters")
        if not isinstance(actors, list) or any(not isinstance(x, str) or not x.strip() for x in actors):
            raise ValueError("人物字段必须是字符串列表。")
        cursor = end
    if cursor != len(script):
        raise ValueError("拆分结果遗漏原文末尾。")
    return scenes