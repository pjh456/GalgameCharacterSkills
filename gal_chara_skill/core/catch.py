from __future__ import annotations

from functools import wraps
import inspect
from typing import Any, Callable, ParamSpec, TypeVar

from numpydoc_decorator import doc

from .result import Result

P = ParamSpec("P")
T = TypeVar("T")
ExceptionHandler = Callable[[BaseException, inspect.BoundArguments], Result[T]]


@doc(
    summary="将函数抛出的异常映射为 Result.failure(...)",
    parameters={
        "handlers": "按异常类型组织的处理函数映射，命中后返回对应失败结果",
        "default": "未命中特定异常类型时使用的兜底处理函数",
    },
    returns="可应用于普通函数的装饰器，包装后返回 Result",
)
def catch_result(
    *,
    handlers: dict[type[BaseException] | tuple[type[BaseException], ...], ExceptionHandler[T]],
    default: ExceptionHandler[T] | None = None,
) -> Callable[[Callable[P, T | Result[T]]], Callable[P, Result[T]]]:
    @doc(
        summary="为目标函数附加异常到 Result 的映射行为",
        parameters={"func": "需要被包装的原始函数"},
        returns="返回 Result 的包装后函数",
    )
    def decorator(func: Callable[P, T | Result[T]]) -> Callable[P, Result[T]]:
        signature = inspect.signature(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T]:
            bound = signature.bind_partial(*args, **kwargs)

            try:
                raw = func(*args, **kwargs)
                if isinstance(raw, Result):
                    return raw
                return Result.success(raw)
            except Exception as exc:
                for exception_types, handler in handlers.items():
                    if isinstance(exc, exception_types):
                        return handler(exc, bound)

                if default is not None:
                    return default(exc, bound)
                raise

        return wrapper

    return decorator


__all__ = ["catch_result"]
