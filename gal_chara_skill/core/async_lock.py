from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Optional

from numpydoc_decorator import doc


@doc(summary="封装 asyncio.Lock 的异步锁工具类")
class AsyncLock:
    @doc(summary="创建 AsyncLock 实例")
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @doc(
        summary="无超时获取锁",
        returns="当前 AsyncLock 实例，支持 `async with lock:` 语法",
    )
    async def __aenter__(self) -> AsyncLock:
        await self._lock.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._lock.release()
        return None

    @doc(
        summary="根据超时参数返回对应的上下文管理器",
        parameters={"timeout": "超时秒数；None 表示无超时"},
        returns="self（无超时）或 _AcquireContext（带超时）",
    )
    def acquire(self, timeout: Optional[float] = None) -> AsyncLock | _AcquireContext:
        if timeout is None:
            return self
        return self._AcquireContext(self, timeout)

    @doc(
        summary="带超时保护的锁获取上下文管理器",
        parameters={
            "parent": "所属的 AsyncLock 实例",
            "timeout": "获取锁的超时秒数",
        },
    )
    class _AcquireContext:
        def __init__(self, parent: AsyncLock, timeout: float) -> None:
            self._parent = parent
            self._timeout = timeout
            self._acquired = False

        @doc(
            summary="在超时限制内获取锁",
            returns="所属 AsyncLock 实例",
            raises={"asyncio.TimeoutError": "指定超时内未能获取锁时抛出"},
        )
        async def __aenter__(self) -> AsyncLock:
            await asyncio.wait_for(self._parent._lock.acquire(), timeout=self._timeout)
            self._acquired = True
            return self._parent

        async def __aexit__(
            self,
            exc_type: Optional[type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> None:
            if self._acquired:
                self._parent._lock.release()
            return None


__all__ = ["AsyncLock"]
