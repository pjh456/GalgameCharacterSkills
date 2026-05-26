from __future__ import annotations

from typing import Generic, TypeVar

from ...conf.task import TaskConfig

_C = TypeVar("_C", bound=TaskConfig)

from numpydoc_decorator import doc


@doc(summary="阶段处理器泛型基类，子类声明接受的 TaskConfig 子类型")
class StageHandler(Generic[_C]):
    pass


__all__ = ["StageHandler"]
