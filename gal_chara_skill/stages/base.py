from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from ..conf.task import TaskConfig
from ..core.result import Result

_C = TypeVar("_C", bound=TaskConfig)

if TYPE_CHECKING:
    from ..conf.stage import StageContext

from numpydoc_decorator import doc


@doc(summary="阶段处理器泛型基类，子类声明接受的 TaskConfig 子类型并覆写 execute")
class StageHandler(ABC, Generic[_C]):
    @abstractmethod
    async def execute(
        self,
        ctx: "StageContext",
        config: _C,
    ) -> Result[None]:
        ...


__all__ = ["StageHandler"]
