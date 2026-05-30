from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from ..conf.task import TaskConfig
from ..core.result import Result

_C = TypeVar("_C", bound=TaskConfig)

if TYPE_CHECKING:
    from ..conf.stage import StageContext

from numpydoc_decorator import doc


@doc(summary="阶段处理器抽象基类")
class StageHandler(ABC, Generic[_C]):
    @doc(
        summary="执行当前 stage 的处理逻辑",
        parameters={
            "ctx": "阶段执行的共享上下文",
            "config": "当前阶段对应的任务配置",
        },
        returns="成功时返回空 Result，失败时返回错误结果",
    )
    @abstractmethod
    async def execute(
        self,
        ctx: "StageContext",
        config: _C,
    ) -> Result[None]:
        ...


__all__ = ["StageHandler"]
