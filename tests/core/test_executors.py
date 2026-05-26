from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from gal_chara_skill.core.executors import configure_pool, get_pool, run_in_pool, to_async


def test_get_pool_lazy_init() -> None:
    configure_pool(None)
    pool = get_pool()
    assert isinstance(pool, ThreadPoolExecutor)
    assert get_pool() is pool


def test_configure_pool() -> None:
    old = get_pool()
    new = ThreadPoolExecutor(max_workers=2)
    configure_pool(new)
    assert get_pool() is new
    assert get_pool() is not old
    configure_pool(old)


def test_run_in_pool_returns_value() -> None:
    async def main() -> None:
        result = await run_in_pool(lambda a, b: a + b, 1, 2)
        assert result == 3

    asyncio.run(main())


def test_run_in_pool_propagates_exception() -> None:
    async def main() -> None:
        try:
            await run_in_pool(lambda: (_ for _ in ()).throw(ValueError("boom")))
            assert False
        except ValueError as exc:
            assert str(exc) == "boom"

    asyncio.run(main())


def test_to_async_preserves_metadata() -> None:
    @to_async
    def add(a: int, b: int) -> int:
        return a + b

    assert add.__name__ == "add"
    assert add.__doc__ is None

    @to_async
    def with_doc() -> None:
        return None

    assert with_doc.__name__ == "with_doc"


def test_to_async_returns_value() -> None:
    @to_async
    def multiply(x: int, y: int) -> int:
        return x * y

    async def main() -> None:
        result = await multiply(3, 4)
        assert result == 12

    asyncio.run(main())


def test_to_async_runs_in_thread_pool() -> None:
    main_thread = threading.current_thread()

    @to_async
    def get_thread_id() -> int:
        ident = threading.current_thread().ident
        assert ident is not None
        return ident

    async def main() -> None:
        thread_id = await get_thread_id()
        assert thread_id != main_thread.ident

    asyncio.run(main())


def test_to_async_propagates_exception() -> None:
    @to_async
    def fail() -> None:
        raise RuntimeError("fail")

    async def main() -> None:
        try:
            await fail()
            assert False
        except RuntimeError as exc:
            assert str(exc) == "fail"

    asyncio.run(main())
