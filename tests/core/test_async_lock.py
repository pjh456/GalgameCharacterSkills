from __future__ import annotations

import asyncio

import pytest

from gal_chara_skill.core.async_lock import AsyncLock


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
