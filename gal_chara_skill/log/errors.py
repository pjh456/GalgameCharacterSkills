from __future__ import annotations

from inspect import BoundArguments
from typing import TYPE_CHECKING

from numpydoc_decorator import doc

from ..core.result import Result

if TYPE_CHECKING:
    from .models import LogRecord


@doc(summary="负责构造 log 模块统一错误结果的无状态工具类")
class LogErrors:
    @staticmethod
    @doc(
        summary="将日志记录恢复异常转换为 log 模块失败结果",
        parameters={
            "exception": "捕获到的恢复异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示日志记录恢复失败的结果",
    )
    def handle_record_restore_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> "Result[LogRecord]":
        del bound
        return Result.failure(
            "日志记录恢复失败",
            code="log_parse_failed",
            exception=str(exception),
        )


__all__ = ["LogErrors"]
