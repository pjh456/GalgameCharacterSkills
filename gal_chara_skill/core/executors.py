from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar, Optional

from numpydoc_decorator import doc

_P = ParamSpec("_P")
_T = TypeVar("_T")

_pool: Optional[ThreadPoolExecutor] = None


@doc(
    summary="返回当前模块共享的线程池，首次调用时懒初始化",
    returns="全局共享的 ThreadPoolExecutor 实例",
)
def get_pool() -> ThreadPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ThreadPoolExecutor()
    return _pool


@doc(
    summary="替换当前模块共享的线程池",
    parameters={"pool": "需要注入的 ThreadPoolExecutor 实例"},
)
def configure_pool(pool: Optional[ThreadPoolExecutor]) -> None:
    global _pool
    _pool = pool


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
        get_pool(),
        lambda: fn(*args, **kwargs),
    )


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
        return await run_in_pool(fn, *args, **kwargs)

    return wrapper


__all__ = [
    "configure_pool",
    "get_pool",
    "run_in_pool",
    "to_async",
]
