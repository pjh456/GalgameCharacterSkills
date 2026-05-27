from __future__ import annotations

import json
from typing import Any, Protocol

from numpydoc_decorator import doc

from ..conf.module.llm import LlmConfig
from ..core.result import Result
from .models import ChatCompletion, ChatCompletionRequest


@doc(
    summary="拼接请求地址，并避免 base_url 与 path 中的版本前缀重复",
    parameters={
        "base_url": "用户配置的 API 服务地址",
        "path": "Provider 声明的 API 路径，含版本前缀",
        "version_prefix": "当前 Provider 的 API 版本前缀",
    },
    returns="去除版本前缀重复后的完整请求地址",
)
def _dedup_path(base_url: str, path: str, *, version_prefix: str) -> str:
    base = base_url.rstrip("/")
    if path.startswith(version_prefix) and base.endswith(version_prefix):
        base = base[: -len(version_prefix)]
    return f"{base}{path}"


class BaseProvider(Protocol):
    """Provider 协议：每种 API 实现一组翻译规则

    每个具体 Provider 实现以下四个方法，将项目内部模型与外部 API 格式双向转换。
    """

    def chat_path(self, config: LlmConfig) -> str:
        """返回完整的 Chat Completion 请求地址，自行处理 base_url 与路径中版本前缀的去重"""
        ...

    def chat_headers(self, config: LlmConfig) -> dict[str, str]:
        """返回该 Provider 所需的 HTTP 请求头，至少包含鉴权与内容类型声明"""
        ...

    def build_chat_request(self, request: ChatCompletionRequest) -> dict[str, Any]:
        """将 ChatCompletionRequest 转换为该 API 格式的请求体字典"""
        ...

    def parse_chat_response(self, data: Any, *, url: str) -> Result[ChatCompletion]:
        """将 API 返回的 JSON 数据解析为 ChatCompletion，url 用于错误上下文"""
        ...


@doc(summary="OpenAI Chat Completions API 的请求/响应格式")
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


@doc(
    summary="根据 provider 名称解析对应的 Provider 实例",
    parameters={"name": "Provider 标识符"},
    returns="对应名称的 Provider 实例",
    raises={"ValueError": "传入未知的 provider 名称时抛出"},
)
def resolve_provider(name: str) -> BaseProvider:
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unknown provider: {name}")


__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "resolve_provider",
]
