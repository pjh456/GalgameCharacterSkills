from __future__ import annotations

from inspect import BoundArguments
from typing import TYPE_CHECKING

from numpydoc_decorator import doc

from ..core.result import Result

if TYPE_CHECKING:
    from .state import SliceState, TaskState
    from .task import SliceConfig, TaskConfig


@doc(summary="负责构造 conf 模块统一错误结果的无状态工具类")
class ConfErrors:
    @staticmethod
    @doc(
        summary="将任务配置恢复异常转换为 conf 模块失败结果",
        parameters={"exception": "捕获到的恢复异常", "bound": "装饰器绑定的调用参数"},
        returns="表示任务配置恢复失败的结果",
    )
    def handle_task_config_restore_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> "Result[TaskConfig]":
        return Result.failure(
            "任务配置恢复失败",
            code="checkpoint_invalid",
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="将切片配置恢复异常转换为 conf 模块失败结果",
        parameters={"exception": "捕获到的恢复异常", "bound": "装饰器绑定的调用参数"},
        returns="表示切片配置恢复失败的结果",
    )
    def handle_slice_config_restore_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> "Result[SliceConfig]":
        return Result.failure(
            "切片配置恢复失败",
            code="checkpoint_invalid",
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="将切片状态恢复异常转换为 conf 模块失败结果",
        parameters={"exception": "捕获到的恢复异常", "bound": "装饰器绑定的调用参数"},
        returns="表示切片状态恢复失败的结果",
    )
    def handle_slice_state_restore_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> "Result[SliceState]":
        return Result.failure(
            "切片状态恢复失败",
            code="checkpoint_invalid",
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="将任务状态恢复异常转换为 conf 模块失败结果",
        parameters={"exception": "捕获到的恢复异常", "bound": "装饰器绑定的调用参数"},
        returns="表示任务状态恢复失败的结果",
    )
    def handle_task_state_restore_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> "Result[TaskState]":
        return Result.failure(
            "任务状态恢复失败",
            code="checkpoint_invalid",
            exception=str(exception),
        )


__all__ = ["ConfErrors"]
