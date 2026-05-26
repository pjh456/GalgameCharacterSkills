from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, TypeAlias

from numpydoc_decorator import doc

from ..core.result import Result
from ..core.validate import FieldRule, validate_dict_fields

Role: TypeAlias = Literal["system", "user", "assistant"]


@doc(
    summary="一条 Chat Completion 消息",
    parameters={
        "role": "消息角色",
        "content": "消息文本内容",
    },
)
@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}

    @classmethod
    @validate_dict_fields(
        error="ChatMessage 格式错误",
        code="llm_parse_failed",
        role=FieldRule(str, error="消息角色格式错误", literal={"system", "user", "assistant"}),
        content=FieldRule(str, error="消息内容格式错误", non_empty=True),
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
    summary="模型返回的一条回复",
    parameters={
        "message": "回复消息",
        "finish_reason": "结束原因",
        "index": "回复在 choices 列表中的序号",
    },
)
@dataclass(frozen=True)
class ChatChoice:
    message: ChatMessage
    finish_reason: Optional[str] = None
    index: int = 0

    @classmethod
    @validate_dict_fields(
        error="ChatChoice 格式错误",
        code="llm_parse_failed",
        index=FieldRule(int, required=False, default=0, validator=lambda v: v >= 0 or "必须大于或等于 0"),
        message=FieldRule(dict, error="回复消息格式错误", transform=ChatMessage.from_dict),
        finish_reason=FieldRule(str, required=False, default=None, allow_none=True),
    )
    def from_dict(cls, data: Any) -> Result[ChatChoice]:
        return Result.success(cls(**data))


@doc(
    summary="一次完整的 Chat Completion 响应",
    parameters={
        "id": "响应唯一标识",
        "choices": "模型回复列表",
        "usage": "token 用量统计",
        "model": "实际使用的模型名",
        "created": "响应创建时间戳",
        "data": "响应中未映射到标准字段的额外数据",
    },
)
@dataclass(frozen=True)
class ChatCompletion:
    id: str
    choices: list[ChatChoice]
    usage: TokenUsage
    model: str = ""
    created: int = 0
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    @validate_dict_fields(
        error="ChatCompletion 格式错误",
        code="llm_parse_failed",
        id=FieldRule(str, error="响应 ID 格式错误", non_empty=True),
        choices=FieldRule(
            list,
            error="回复列表格式错误",
            item_type=dict,
            item_transform=ChatChoice.from_dict,
            non_empty=True,
        ),
        usage=FieldRule(dict, error="token 用量格式错误", required=False, transform=TokenUsage.from_dict),
        model=FieldRule(str, required=False, default=""),
        created=FieldRule(int, required=False, default=0, validator=lambda v: v >= 0 or "必须大于或等于 0"),
        data=FieldRule(dict, error="额外数据格式错误", required=False, default={}),
    )
    def from_dict(cls, data: Any) -> Result[ChatCompletion]:
        return Result.success(cls(**data))

    @classmethod
    @doc(
        summary="从 JsonResponse 的 data 字段恢复 ChatCompletion",
        parameters={
            "cls": "ChatCompletion 类型",
            "data": "JsonResponse.data 原始字典",
            "url": "本次请求的目标地址，用于错误上下文",
        },
        returns="成功时 value 为 ChatCompletion，失败时返回解析错误",
    )
    def from_json_response(cls, data: Any, *, url: str = "") -> Result[ChatCompletion]:
        if not isinstance(data, dict):
            return Result.failure(
                "LLM 响应 JSON 解析失败",
                code="llm_parse_failed",
                url=url,
                exception=str(TypeError("响应体不是 JSON 对象")),
            )
        result = cls.from_dict(data)
        if not result.ok:
            return Result.failure_from(result, url=url)
        return result


@doc(
    summary="一次 Chat Completion 请求",
    parameters={
        "model": "使用的模型名",
        "messages": "对话消息列表",
        "temperature": "模型采样温度",
        "max_tokens": "单次输出允许的最大 token 数",
        "extra": "追加到请求体中的额外字段",
    },
)
@dataclass(frozen=True, kw_only=True)
class ChatCompletionRequest:
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [message.to_dict() for message in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        body.update(self.extra)
        return body


__all__ = [
    "ChatChoice",
    "ChatCompletion",
    "ChatCompletionRequest",
    "ChatMessage",
    "Role",
    "TokenUsage",
]
