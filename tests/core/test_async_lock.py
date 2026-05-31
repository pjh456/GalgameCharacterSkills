from __future__ import annotations

import asyncio

import pytest

from gal_chara_skill.core.async_lock import AsyncLock


@pytest.mark.asyncio
async def test_async_lock_acquire_no_timeout_returns_self() -> None:
    lock = AsyncLock()
    assert lock.acquire() is lock
    assert lock.acquire(timeout=None) is lock


@pytest.mark.asyncio
async def test_async_lock_serializes_writers() -> None:
    """Verify AsyncLock mutual exclusion and timeout protection."""
    lock = AsyncLock()
    shared: list[int] = []

    async def writer(n: int) -> None:
        async with lock:
            shared.append(n)
            await asyncio.sleep(0.01)
            shared.append(n)

    await asyncio.gather(writer(1), writer(2))
    assert shared in ([1, 1, 2, 2], [2, 2, 1, 1])

    held = asyncio.Event()

    async def holder() -> None:
        async with lock:
            held.set()
            await asyncio.sleep(1)

    async def timed_acquirer() -> None:
        await held.wait()
        with pytest.raises(asyncio.TimeoutError):
            async with lock.acquire(timeout=0.1):
                pass

    await asyncio.gather(holder(), timed_acquirer())


@pytest.mark.asyncio
async def test_async_lock_acquire_timeout_release_guard() -> None:
    """Verify _AcquireContext.__aexit__ skips release when _acquired is False."""
    lock = AsyncLock()
    ctx = lock._AcquireContext(lock, timeout=0.05)
    assert ctx._acquired is False
    await ctx.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_async_lock_acquire_with_timeout_succeeds() -> None:
    """Verify acquire(timeout) succeeds when lock is free, covering release path."""
    lock = AsyncLock()
    async with lock.acquire(timeout=5.0):
        pass
