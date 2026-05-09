from __future__ import annotations

from dataclasses import dataclass

from numpydoc_decorator import doc

from .context import TaskContext
from .task import TaskConfig


@doc(
    summary="保存任务恢复所需的检查点",
    parameters={
        "task_config": "对应任务的静态输入配置",
        "task_context": "任务当前的运行时状态",
    },
)
@dataclass
class CheckpointData:
    task_config: TaskConfig
    task_context: TaskContext
