from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

from numpydoc_decorator import doc

from ..core.result import Result
from ..core.validate import FieldRule, validate_dict_fields

Role: TypeAlias = Literal["system", "user", "assistant", "tool"]


@doc(
    summary="模型返回的一次工具调用",
    parameters={
        "id": "工具调用唯一标识",
        "type": "工具类型，固定为 function",
        "function_name": "被调用的函数名",
        "function_arguments": "函数参数的 JSON 字符串",
    },
)
@dataclass(frozen=True)
class ToolCall:
    id: str
    function_name: str
    function_arguments: str = ""
    type: str = "function"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "function": {
                "name": self.function_name,
                "arguments": self.function_arguments,
            },
        }

    @classmethod
    @validate_dict_fields(
        error="ToolCall 格式错误",
        code="llm_parse_failed",
        id=FieldRule(str, error="工具调用 ID 格式错误", non_empty=True),
        type=FieldRule(str, required=False, default="function"),
        function=FieldRule(dict, error="函数信息格式错误"),
    )
    def from_dict(cls, data: Any) -> Result[ToolCall]:
        func = data.get("function", {})
        return Result.success(
            cls(
                id=data["id"],
                type=data.get("type", "function"),
                function_name=func.get("name", ""),
                function_arguments=func.get("arguments", ""),
            )
        )


@doc(
    summary="一条 Chat Completion 消息",
    parameters={
        "role": "消息角色",
        "content": "消息文本内容，assistant 发出 tool_calls 时可为空",
        "tool_calls": "assistant 消息携带的工具调用列表",
        "tool_call_id": "tool 角色消息对应的工具调用 ID",
        "name": "可选的消息发送者名称",
    },
)
@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str = ""
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        msg: dict[str, Any] = {"role": self.role}
        if self.tool_calls:
            msg["content"] = self.content or None
            msg["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        else:
            msg["content"] = self.content
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.name:
            msg["name"] = self.name
        return msg

    @classmethod
    @validate_dict_fields(
        error="ChatMessage 格式错误",
        code="llm_parse_failed",
        role=FieldRule(str, error="消息角色格式错误", literal={"system", "user", "assistant", "tool"}),
        content=FieldRule(
            (str, type(None)),
            error="消息内容格式错误",
            required=False,
            default="",
            transform=lambda v: v or "",
        ),
        tool_calls=FieldRule(
            list,
            required=False,
            default=[],
            item_type=dict,
            item_transform=ToolCall.from_dict,
        ),
        tool_call_id=FieldRule(str, required=False, default=""),
        name=FieldRule(str, required=False, default=""),
    )
    def from_dict(cls, data: Any) -> Result[ChatMessage]:
        return Result.success(cls(**data))


@doc(
    summary="一次请求的 token 用量统计",
    parameters={
        "prompt_tokens": "提示词消耗的 token 数",
        "completion_tokens": "回复消耗的 token 数",
        "total_tokens": "总 token 数",
    },
)
@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    @validate_dict_fields(
        error="TokenUsage 格式错误",
        code="llm_parse_failed",
        prompt_tokens=FieldRule(int, error="prompt_tokens 格式错误", validator=lambda v: v >= 0 or "必须大于或等于 0"),
        completion_tokens=FieldRule(int, error="completion_tokens 格式错误", validator=lambda v: v >= 0 or "必须大于或等于 0"),
        total_tokens=FieldRule(int, error="total_tokens 格式错误", validator=lambda v: v >= 0 or "必须大于或等于 0"),
    )
    def from_dict(cls, data: Any) -> Result[TokenUsage]:
        return Result.success(cls(**data))


@doc(
    summary="一次完整的 Chat Completion 响应，provider 无关的内部模型",
    parameters={
        "message": "模型回复消息",
        "finish_reason": "模型停止原因",
        "id": "响应唯一标识",
        "usage": "token 用量统计",
        "model": "实际使用的模型名",
        "created": "响应创建时间戳",
        "data": "响应中未映射到标准字段的额外数据",
    },
)
@dataclass(frozen=True)
class ChatCompletion:
    message: ChatMessage
    finish_reason: str = ""
    id: str = ""
    usage: TokenUsage = field(default_factory=lambda: TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0))
    model: str = ""
    created: int = 0
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    @validate_dict_fields(
        error="ChatCompletion 格式错误",
        code="llm_parse_failed",
        message=FieldRule(dict, error="回复消息格式错误", transform=ChatMessage.from_dict),
        finish_reason=FieldRule(str, required=False, default=""),
        id=FieldRule(str, error="响应 ID 格式错误", required=False, default=""),
        usage=FieldRule(dict, error="token 用量格式错误", required=False, transform=TokenUsage.from_dict),
        model=FieldRule(str, required=False, default=""),
        created=FieldRule(int, required=False, default=0, validator=lambda v: v >= 0 or "必须大于或等于 0"),
        data=FieldRule(dict, error="额外数据格式错误", required=False, default={}),
    )
    def from_dict(cls, data: Any) -> Result[ChatCompletion]:
        return Result.success(cls(**data))


@doc(
    summary="一次 Chat Completion 请求",
    parameters={
        "model": "使用的模型名",
        "messages": "对话消息列表",
        "temperature": "模型采样温度",
        "max_tokens": "单次输出允许的最大 token 数",
        "tools": "可选的工具定义列表",
        "tool_choice": "工具选择策略",
        "extra": "追加到请求体中的额外字段",
    },
)
@dataclass(frozen=True, kw_only=True)
class ChatCompletionRequest:
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str = "auto"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.tools:
            body["tools"] = self.tools
            body["tool_choice"] = self.tool_choice
        body.update(self.extra)
        return body


__all__ = [
    "ChatCompletion",
    "ChatCompletionRequest",
    "ChatMessage",
    "Role",
    "ToolCall",
    "TokenUsage",
]
