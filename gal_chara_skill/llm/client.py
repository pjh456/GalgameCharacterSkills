from __future__ import annotations

from typing import Any, Callable, Optional

from numpydoc_decorator import doc

from ..conf.module.llm import LlmConfig
from ..core.executors import Executors
from ..core.result import Result
from ..net.client import NetClient
from .errors import LlmErrors
from .models import ChatCompletion, ChatCompletionRequest, ChatMessage, ToolCall
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
            "tools": "可选的工具定义列表",
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
        tools: Optional[list[dict[str, Any]]] = None,
        extra_body: Optional[dict[str, Any]] = None,
    ) -> Result[ChatCompletion]:
        request = ChatCompletionRequest(
            model=self.config.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools or [],
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
        summary="发送最小请求验证 LLM 连接可用",
        returns="成功时返回空，失败时返回错误原因",
    )
    def check(self) -> Result[None]:
        result = self.complete(
            [ChatMessage(role="user", content="Hi")],
            max_tokens=5,
        )
        if not result.ok:
            return Result.failure_from(result)
        return Result.success(None)

    @doc(
        summary="多轮 tool-calling 对话循环，原地修改 messages 直到无工具调用或超迭代",
        parameters={
            "messages": "对话历史列表，原地修改，完成后包含完整的 assistant + tool 多轮消息",
            "tools": "OpenAI 格式的工具定义列表",
            "tool_handler": "ToolCall → ChatMessage 的处理函数，由调用方提供执行逻辑",
            "temperature": "模型采样温度",
            "max_tokens": "单次输出最大 token 数",
            "max_iterations": "最大工具调用轮数上限",
        },
        returns="成功时返回空，失败时返回错误原因",
    )
    def complete_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]],
        *,
        tool_handler: Callable[[ToolCall], ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_iterations: int = 20,
    ) -> Result[None]:
        for _ in range(max_iterations):
            result = self.complete(
                messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if not result.ok:
                return Result.failure_from(result)

            message = result.unwrap().message
            messages.append(message)

            if not message.tool_calls:
                break

            for tc in message.tool_calls:
                messages.append(tool_handler(tc))

        return Result.success(None)

    @doc(
        summary="异步发起一次 Chat Completion 请求",
        parameters={
            "messages": "对话消息列表",
            "temperature": "模型采样温度",
            "max_tokens": "单次输出允许的最大 token 数",
            "tools": "可选的工具定义列表",
            "extra_body": "追加到请求体中的额外字段",
        },
        returns="成功时 value 为 ChatCompletion，失败时返回网络、HTTP 或解析错误",
    )
    @Executors.to_async
    def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict[str, Any]]] = None,
        extra_body: Optional[dict[str, Any]] = None,
    ) -> Result[ChatCompletion]:
        return self.complete(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            extra_body=extra_body,
        )

    @doc(
        summary="complete_with_tools 的异步版本，由 Executors.to_async 映射到线程池执行",
        parameters={
            "messages": "对话历史列表，原地修改",
            "tools": "OpenAI 格式的工具定义列表",
            "tool_handler": "ToolCall → ChatMessage 的处理函数",
            "temperature": "模型采样温度",
            "max_tokens": "单次输出最大 token 数",
            "max_iterations": "最大工具调用轮数上限",
        },
        returns="成功时返回空，失败时返回错误原因",
    )
    @Executors.to_async
    def acomplete_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]],
        *,
        tool_handler: Callable[[ToolCall], ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_iterations: int = 20,
    ) -> Result[None]:
        return self.complete_with_tools(
            messages,
            tools=tools,
            tool_handler=tool_handler,
            temperature=temperature,
            max_tokens=max_tokens,
            max_iterations=max_iterations,
        )


__all__ = ["LlmClient"]
