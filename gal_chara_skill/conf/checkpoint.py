from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result
from ..core.validate import FieldRule, validate_dict_fields
from .state import TaskState
from .task import BaseTaskConfig, TaskConfig


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
        summary="将任务检查点转换为可写入 JSON 的字典",
        returns="可被 JSON 模块写入的字典",
    )
    def to_dict(self) -> dict[str, Any]:
        return {
            "task_config": self.task_config.to_dict(),
            "task_state": self.task_state.to_dict(),
        }

    @classmethod
    @validate_dict_fields(
        error="Checkpoint 数据格式错误",
        code="checkpoint_invalid",
        keep_unknown=False,
        task_config=FieldRule(dict, error="任务配置格式错误", transform=BaseTaskConfig.from_dict),
        task_state=FieldRule(dict, error="任务状态格式错误", transform=TaskState.from_dict),
    )
    @doc(
        summary="从字典恢复任务检查点",
        parameters={
            "cls": "任务检查点类型",
            "data": "从 JSON 读取出的原始字典",
        },
        returns="表示恢复结果的显式结果对象",
    )
    def from_dict(cls, data: Any) -> Result["TaskCheckpoint"]:
        return Result.success(cls(**data))

__all__ = [
    "TaskCheckpoint",
]
