from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, cast, overload

from numpydoc_decorator import doc

T = TypeVar("T")
U = TypeVar("U")
_MISSING = object()


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
            "cls": "结果对象所属的类",
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
            "cls": "结果对象所属的类",
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

    @overload
    @classmethod
    def failure_from(
        cls,
        result: "Result[T]",
        *,
        error: Optional[str] = None,
        code: Optional[str] = None,
        **data: Any,
    ) -> "Result[T]": ...

    @overload
    @classmethod
    def failure_from(
        cls,
        result: "Result[Any]",
        *,
        error: Optional[str] = None,
        code: Optional[str] = None,
        value: Optional[U],
        **data: Any,
    ) -> "Result[U]": ...

    @classmethod
    @doc(
        summary="基于已有失败结果构造新的失败结果",
        parameters={
            "cls": "结果对象所属的类",
            "result": "作为来源的失败结果对象",
            "error": "可选的新错误信息，未提供时继承来源错误信息",
            "code": "可选的新错误码，未提供时继承来源错误码",
            "value": "可选的新结果值；未提供时继承来源值",
            "data": "需要补充或覆盖的附加信息",
        },
        returns="一个继承来源失败信息并允许局部覆写的新失败结果对象",
        raises={"ValueError": "来源结果不是失败状态时抛出"},
    )
    def failure_from(
        cls,
        result: "Result[Any]",
        *,
        error: Optional[str] = None,
        code: Optional[str] = None,
        value: object = _MISSING,
        **data: Any,
    ) -> "Result[Any]":
        if result.ok:
            raise ValueError("failure_from 只能用于失败结果")

        merged_data = dict(result.data)
        merged_data.update(data)

        return cls(
            ok=False,
            value=cast(Optional[Any], result.value if value is _MISSING else value),
            error=error if error is not None else result.error,
            code=code if code is not None else result.code,
            data=merged_data,
        )

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


__all__ = ["Result"]
