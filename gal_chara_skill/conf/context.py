from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

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


@dataclass
class SliceState:
    """切片总结任务运行时状态"""

    slice_index: int  # 顺序编号
    source_file: str  # 当前切片来源的输入文件名
    source_slice_index: int  # 当前切片在源文件内的顺序编号
    status: TaskStatus = "pending"  # 执行状态
    attempt_count: int = 0  # 已尝试执行的次数
    error_message: Optional[str] = None  # 最近一次错误信息


@dataclass
class TaskContext:
    """保存任务运行时状态"""

    task_id: str  # 任务唯一标识
    status: TaskStatus = "pending"  # 整体执行状态
    current_stage: TaskStage = "pending"  # 任务所处的执行阶段
    completed_slices: list[int] = field(default_factory=list)  # 已完成的切片编号列表
    slice_states: list[SliceState] = field(default_factory=list)  # 所有切片的运行状态
    metadata: dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    error_message: Optional[str] = None  #  最近一次错误信息
