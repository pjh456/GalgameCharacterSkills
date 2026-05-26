from __future__ import annotations

from typing import Any, Optional

from numpydoc_decorator import doc

from ..conf.module.llm import LlmConfig
from ..core.executors import Executors
from ..core.result import Result
from ..net.client import NetClient
from .errors import LlmErrors
from .models import ChatCompletion, ChatCompletionRequest, ChatMessage
from .providers import resolve_provider


@doc(
    summary="LLM 调用客户端，封装单次 Chat Completion 请求",
    parameters={
        "config": "LLM 调用配置",
        "net_client": "网络请求客户端实例",
    },
)
class LlmClient:
    def __init__(
        self,
        config: LlmConfig,
        *,
        net_client: NetClient,
    ) -> None:
        self.config = config
        self.net_client = net_client
        self._provider = resolve_provider(config.provider)

    @doc(
        summary="同步发起一次 Chat Completion 请求",
        parameters={
            "messages": "对话消息列表",
            "temperature": "模型采样温度",
            "max_tokens": "单次输出允许的最大 token 数",
            "extra_body": "追加到请求体中的额外字段",
        },
        returns="成功时 value 为 ChatCompletion，失败时返回网络、HTTP 或解析错误",
    )
    def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        extra_body: Optional[dict[str, Any]] = None,
    ) -> Result[ChatCompletion]:
        request = ChatCompletionRequest(
            model=self.config.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra=extra_body or {},
        )
        url = self._provider.chat_path(self.config)
        headers = self._provider.chat_headers(self.config)
        body = self._provider.build_chat_request(request)

        response_result = self.net_client.request_json("POST", url, headers=headers, json_data=body)
        if not response_result.ok:
            return LlmErrors.completion_parse_failed(url, response_result)

        return self._provider.parse_chat_response(response_result.unwrap().data, url=url)

    @doc(
        summary="异步发起一次 Chat Completion 请求",
        parameters={
            "messages": "对话消息列表",
            "temperature": "模型采样温度",
            "max_tokens": "单次输出允许的最大 token 数",
            "extra_body": "追加到请求体中的额外字段",
        },
        returns="成功时 value 为 ChatCompletion，失败时返回网络、HTTP 或解析错误",
    )
    async def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        extra_body: Optional[dict[str, Any]] = None,
    ) -> Result[ChatCompletion]:
        return await Executors.run_in_pool(
            self.complete,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )


__all__ = ["LlmClient"]
