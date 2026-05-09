from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from numpydoc_decorator import doc

from .task import TaskStatus

TaskStage = Literal[
    "pending",
    "preparing",
    "slicing",
    "summarizing",
    "generating",
    "finalizing",
    "cleaning",
]


@doc(
    summary="切片总结任务运行时状态",
    parameters={
        "slice_index": "顺序编号",
        "source_file": "当前切片来源的输入文件名",
        "source_slice_index": "当前切片在源文件内的顺序编号",
        "status": "执行状态",
        "attempt_count": "已尝试执行的次数",
        "error_message": "最近一次错误信息",
    },
)
@dataclass
class SliceState:
    slice_index: int
    source_file: str
    source_slice_index: int
    status: TaskStatus = "pending"
    attempt_count: int = 0
    error_message: Optional[str] = None


@doc(
    summary="保存任务运行时状态",
    parameters={
        "task_id": "任务唯一标识",
        "status": "整体执行状态",
        "current_stage": "任务所处的执行阶段",
        "completed_slices": "已完成的切片编号列表",
        "slice_states": "所有切片的运行状态",
        "metadata": "扩展元数据",
        "error_message": "最近一次错误信息",
    },
)
@dataclass
class TaskContext:
    task_id: str
    status: TaskStatus = "pending"
    current_stage: TaskStage = "pending"
    completed_slices: list[int] = field(default_factory=list)
    slice_states: list[SliceState] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
