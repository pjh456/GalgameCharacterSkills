from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, cast

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """统一的显式结果封装。"""

    ok: bool  # 当前操作是否成功
    value: Optional[T] = None  # 成功时返回的结果值
    error: Optional[str] = None  # 失败时返回的错误信息
    code: Optional[str] = None  # 可选的错误码
    data: dict[str, Any] = field(default_factory=dict)  # 附加信息

    @classmethod
    def success(cls, value: Optional[T] = None, **data: Any) -> "Result[T]":
        return cls(ok=True, value=value, data=data)

    @classmethod
    def failure(
        cls,
        error: str,
        *,
        code: Optional[str] = None,
        value: Optional[T] = None,
        **data: Any,
    ) -> "Result[T]":
        return cls(ok=False, value=value, error=error, code=code, data=data)

    def unwrap(self) -> T:
        if not self.ok:
            raise RuntimeError(self.error or "Result unwrap 失败.")
        if self.value is None:
            raise RuntimeError("Result unwrap 失败: 值为 None.")
        return cast(T, self.value)

    def expect(self, message: str) -> T:
        if not self.ok:
            detail = self.error or "未知错误"
            raise RuntimeError(f"{message}: {detail}")
        if self.value is None:
            raise RuntimeError(f"{message}: 值为 None.")
        return cast(T, self.value)
