from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, ClassVar, Coroutine, Optional, ParamSpec, TypeVar

from numpydoc_decorator import doc

_P = ParamSpec("_P")
_T = TypeVar("_T")


@doc(summary="线程池管理与同步到异步桥接的无状态工具类")
class Executors:
    _pool: ClassVar[Optional[ThreadPoolExecutor]] = None

    @staticmethod
    @doc(
        summary="返回当前共享的线程池，首次调用时懒初始化",
        returns="全局共享的 ThreadPoolExecutor 实例",
    )
    def get_pool() -> ThreadPoolExecutor:
        if Executors._pool is None:
            Executors._pool = ThreadPoolExecutor()
        return Executors._pool

    @staticmethod
    @doc(
        summary="替换当前共享的线程池",
        parameters={"pool": "需要注入的 ThreadPoolExecutor 实例"},
    )
    def configure_pool(pool: Optional[ThreadPoolExecutor]) -> None:
        Executors._pool = pool

    @staticmethod
    @doc(
        summary="在线程池中执行同步函数并返回其结果的协程",
        parameters={
            "fn": "需要在线程池中执行的同步函数",
            "args": "传递给 fn 的位置参数",
            "kwargs": "传递给 fn 的关键字参数",
        },
        returns="fn 执行完毕后包装为协程的返回值",
    )
    async def run_in_pool(
        fn: Callable[..., _T],
        *args: Any,
        **kwargs: Any,
    ) -> _T:
        return await asyncio.get_running_loop().run_in_executor(
            Executors.get_pool(),
            lambda: fn(*args, **kwargs),
        )

    @staticmethod
    @doc(
        summary="将同步函数包装为在线程池中执行的异步函数",
        parameters={"fn": "需要包装的同步函数"},
        returns="保持原始签名的异步包装函数",
    )
    def to_async(
        fn: Callable[_P, _T],
    ) -> Callable[_P, Coroutine[Any, Any, _T]]:
        @wraps(fn)
        async def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            return await Executors.run_in_pool(fn, *args, **kwargs)

        return wrapper


__all__ = ["Executors"]
