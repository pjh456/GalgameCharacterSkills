from __future__ import annotations

import json
import re
from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result


@doc(
    summary="从 LLM 响应文本中提取 JSON，支持 3 种回退策略",
    parameters={"content": "LLM 返回的文本内容"},
    returns="成功时 value 为解析后的字典/列表，失败时返回解析错误",
)
def parse_llm_json_response(content: str) -> Result[Any]:
    if not content:
        return Result.failure("响应内容为空", code="llm_parse_failed")

    try:
        return Result.success(json.loads(content))
    except json.JSONDecodeError:
        pass

    try:
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            return Result.success(json.loads(json_match.group(1)))
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return Result.success(json.loads(json_match.group(0)))
    except (json.JSONDecodeError, AttributeError):
        pass

    return Result.failure("无法从响应中解析 JSON", code="llm_parse_failed")


__all__ = ["parse_llm_json_response"]
