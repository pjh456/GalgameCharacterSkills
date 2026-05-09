from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, cast

from numpydoc_decorator import doc

T = TypeVar("T")


@doc(
    summary="统一结果封装",
    parameters={
        "ok": "当前操作是否成功",
        "value": "成功时返回的结果值",
        "error": "失败时返回的错误信息",
        "code": "可选的错误码",
        "data": "附加信息",
    },
)
@dataclass
class Result(Generic[T]):
    ok: bool
    value: Optional[T] = None
    error: Optional[str] = None
    code: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    @doc(
        summary="构造一个成功结果",
        parameters={
            "value": "成功时返回的结果值",
            "data": "需要附带返回的额外信息",
        },
        returns="一个标记为成功的结果对象",
    )
    def success(cls, value: Optional[T] = None, **data: Any) -> "Result[T]":
        return cls(ok=True, value=value, data=data)

    @classmethod
    @doc(
        summary="构造一个失败结果",
        parameters={
            "error": "失败时返回的错误信息",
            "code": "可选的错误码",
            "value": "失败时仍希望携带的结果值",
            "data": "需要附带返回的额外信息",
        },
        returns="一个标记为失败的结果对象",
    )
    def failure(
        cls,
        error: str,
        *,
        code: Optional[str] = None,
        value: Optional[T] = None,
        **data: Any,
    ) -> "Result[T]":
        return cls(ok=False, value=value, error=error, code=code, data=data)

    @doc(
        summary="返回成功结果的值",
        returns="当前结果对象中携带的成功值",
        raises={"RuntimeError": "当前结果为失败状态或值为 None 时抛出"},
    )
    def unwrap(self) -> T:
        if not self.ok:
            raise RuntimeError(self.error or "Result unwrap 失败.")
        if self.value is None:
            raise RuntimeError("Result unwrap 失败: 值为 None.")
        return cast(T, self.value)

    @doc(
        summary="返回成功结果的值并在失败时附带自定义信息",
        parameters={"message": "失败时追加到异常中的自定义提示信息"},
        returns="当前结果对象中携带的成功值",
        raises={"RuntimeError": "当前结果为失败状态或值为 None 时抛出"},
    )
    def expect(self, message: str) -> T:
        if not self.ok:
            detail = self.error or "未知错误"
            raise RuntimeError(f"{message}: {detail}")
        if self.value is None:
            raise RuntimeError(f"{message}: 值为 None.")
        return cast(T, self.value)
