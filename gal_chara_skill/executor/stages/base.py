from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from ...conf.task import TaskConfig
from ...core.result import Result

_C = TypeVar("_C", bound=TaskConfig)

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor

from numpydoc_decorator import doc


@doc(summary="阶段处理器泛型基类，子类声明接受的 TaskConfig 子类型并覆写 execute")
class StageHandler(Generic[_C]):
    async def execute(
        self,
        executor: "TaskExecutor",
        config: _C,
    ) -> Result[None]:
        raise NotImplementedError


__all__ = ["StageHandler"]
