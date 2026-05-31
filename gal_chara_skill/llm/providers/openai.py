from __future__ import annotations

import json
from typing import Any

from numpydoc_decorator import doc

from ...conf.module.llm import LlmConfig
from ...core.result import Result
from ..models import ChatCompletion, ChatCompletionRequest, ToolDef
from .registry import register_provider


def _dedup_path(base_url: str, path: str, *, version_prefix: str) -> str:
    base = base_url.rstrip("/")
    if path.startswith(version_prefix) and base.endswith(version_prefix):
        base = base[: -len(version_prefix)]
    return f"{base}{path}"


@doc(summary="OpenAI Chat Completions API 的请求/响应格式")
@register_provider("openai")
class OpenAIProvider:
    def chat_path(self, config: LlmConfig) -> str:
        return _dedup_path(config.base_url, "/v1/chat/completions", version_prefix="/v1")

    def chat_headers(self, config: LlmConfig) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    def build_chat_request(self, request: ChatCompletionRequest) -> dict[str, Any]:
        return request.to_dict()

    def parse_chat_response(self, data: Any, *, url: str) -> Result[ChatCompletion]:
        if not isinstance(data, dict):
            return Result.failure(
                "LLM 响应 JSON 解析失败",
                code="llm_parse_failed",
                url=url,
                exception=str(TypeError("响应体不是 JSON 对象")),
            )

        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            return Result.failure(
                "LLM 响应缺少 choices 字段",
                code="llm_parse_failed",
                url=url,
            )

        choice = choices[0]

        msg = dict(choice.get("message", {}))
        if msg.get("content") is None:
            msg["content"] = ""
        raw_tool_calls = msg.pop("tool_calls", None) or []
        if raw_tool_calls:
            flat_tool_calls = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                flat_tool_calls.append({
                    "id": tc.get("id", ""),
                    "type": tc.get("type", "function"),
                    "name": func.get("name", ""),
                    "arguments": json.loads(func.get("arguments", "{}")),
                })
            msg["tool_calls"] = flat_tool_calls

        flat_data: dict[str, Any] = {
            "message": msg,
            "finish_reason": choice.get("finish_reason", ""),
            "id": data.get("id", ""),
            "model": data.get("model", ""),
            "created": data.get("created", 0),
            "data": {k: v for k, v in data.items() if k not in ("id", "choices", "usage", "model", "created", "object")},
        }
        if "usage" in data:
            flat_data["usage"] = data["usage"]

        result = ChatCompletion.from_dict(flat_data)
        if not result.ok:
            return Result.failure_from(result, url=url)
        return result

    def build_tool_request(self, tool_def: ToolDef) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        for p in tool_def.params:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum is not None:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


__all__ = ["OpenAIProvider", "_dedup_path"]
