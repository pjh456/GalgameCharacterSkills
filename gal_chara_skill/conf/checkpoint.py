from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from numpydoc_decorator import doc

from ..core.paths import WorkspacePaths
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


@doc(
    summary="根据任务编号推导 checkpoint 文件路径",
    parameters={
        "task_id": "任务唯一标识",
        "workspace_paths": "本次运行使用的工作区路径布局",
    },
    returns="对应任务 checkpoint 文件的完整路径",
)
def get_checkpoint_path(task_id: str, workspace_paths: WorkspacePaths) -> Path:
    return workspace_paths.checkpoints_dir / f"{task_id}.json"


__all__ = ["TaskCheckpoint", "get_checkpoint_path"]
