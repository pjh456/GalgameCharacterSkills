from __future__ import annotations

from dataclasses import dataclass

from numpydoc_decorator import doc

from .state import TaskState
from .task import TaskConfig


@doc(
    summary="保存任务恢复所需的检查点",
    parameters={
        "task_config": "对应任务的静态输入配置",
        "task_state": "任务当前的运行时状态",
    },
)
@dataclass
class TaskCheckpoint:
    task_config: TaskConfig
    task_state: TaskState


__all__ = ["TaskCheckpoint"]
