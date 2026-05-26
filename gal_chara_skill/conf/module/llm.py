from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from numpydoc_decorator import doc


@doc(
    summary="LLM 调用模块使用的运行配置",
    parameters={
        "base_url": "API 服务地址",
        "api_key": "API 鉴权密钥",
        "model_name": "使用的模型名",
        "provider": "Provider 标识符，决定请求格式与响应解析方式",
        "provider_options": "传给 Provider 的自定义参数",
    },
)
@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model_name: str
    provider: str = "openai"
    provider_options: dict[str, Any] = field(default_factory=dict)


__all__ = ["LlmConfig"]
