from __future__ import annotations

from typing import Any

from numpydoc_decorator import doc


@doc(
    summary="将角色卡字段字典转换为 SillyTavern V2 格式",
    parameters={
        "fields": "GenerateStage._generate_chara_card 收集的字段字典",
        "role_name": "角色名称",
    },
    returns="符合 chara_card_v2 spec 的字典，调用方负责 json.dumps",
)
def build_chara_card_v2(fields: dict[str, str], role_name: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": fields.get("name", role_name),
        "description": fields.get("description", ""),
        "personality": fields.get("personality", ""),
        "first_mes": fields.get("first_mes", ""),
        "mes_example": fields.get("mes_example", ""),
        "scenario": fields.get("scenario", ""),
        "system_prompt": fields.get("system_prompt", ""),
        "post_history_instructions": fields.get("post_history_instructions", ""),
    }

    depth_prompt = fields.get("depth_prompt", "")
    if depth_prompt:
        data["extensions"] = {"depth_prompt": depth_prompt}

    return {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": data,
    }


__all__ = ["build_chara_card_v2"]
