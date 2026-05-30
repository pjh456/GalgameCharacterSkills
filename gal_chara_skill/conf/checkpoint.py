from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from numpydoc_decorator import doc

from ..core.paths import WorkspacePaths
from ..core.result import Result
from ..core.validate import FieldRule, validate_dict_fields
from ..fs.json import JsonIO
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


@doc(summary="检查点持久化工具，负责 TaskCheckpoint 的序列化与反序列化")
class CheckpointStore:
    @doc(
        summary="将检查点保存为 JSON 文件",
        parameters={
            "checkpoint": "需要保存的任务检查点",
            "workspace": "工作区路径布局",
        },
        returns="表示保存结果的显式结果对象",
    )
    def save(
        self,
        checkpoint: TaskCheckpoint,
        workspace: WorkspacePaths,
    ) -> Result[None]:
        path = workspace.checkpoints_dir / f"{checkpoint.task_state.task_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return JsonIO.write(path, checkpoint.to_dict())

    @doc(
        summary="从 JSON 文件加载检查点",
        parameters={
            "task_id": "任务唯一标识",
            "workspace": "工作区路径布局",
        },
        returns="成功时 value 为 TaskCheckpoint，文件不存在时为 None，格式错误时返回失败结果",
    )
    def load(
        self,
        task_id: str,
        workspace: WorkspacePaths,
    ) -> Result[Any]:
        path = workspace.checkpoints_dir / f"{task_id}.json"
        read_result = JsonIO.read(path)
        if not read_result.ok:
            if read_result.code == "fs_not_found":
                return Result.success(None)
            return Result.failure_from(read_result)
        return TaskCheckpoint.from_dict(read_result.unwrap())


__all__ = [
    "CheckpointStore",
    "TaskCheckpoint",
]
