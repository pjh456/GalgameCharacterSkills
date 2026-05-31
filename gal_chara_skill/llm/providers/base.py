from __future__ import annotations

from typing import Any, Protocol

from ...conf.module.llm import LlmConfig
from ...core.result import Result
from ..models import ChatCompletion, ChatCompletionRequest, ToolDef


class BaseProvider(Protocol):
    """Provider 协议：每种 API 实现一组翻译规则

    每个具体 Provider 实现以下五个方法，将项目内部模型与外部 API 格式双向转换。
    """

    def chat_path(self, config: LlmConfig) -> str: ...
    def chat_headers(self, config: LlmConfig) -> dict[str, str]: ...
    def build_chat_request(self, request: ChatCompletionRequest) -> dict[str, Any]: ...
    def parse_chat_response(self, data: Any, *, url: str) -> Result[ChatCompletion]: ...
    def build_tool_request(self, tool_def: ToolDef) -> dict[str, Any]: ...


__all__ = ["BaseProvider"]
