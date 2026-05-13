from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional, cast

from numpydoc_decorator import doc

from ..core.result import Result
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
        summary="将切片状态转换为可写入 JSON 的字典",
        returns="可被 JSON 模块写入的切片状态字典",
    )
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    @doc(
        summary="从字典恢复切片状态",
        parameters={
            "cls": "切片状态类型",
            "data": "从 checkpoint 中读取出的切片状态字典",
        },
        returns="成功时 value 为切片状态，失败时返回 checkpoint 格式错误",
    )
    def from_dict(cls, data: Any) -> Result["SliceState"]:
        if not isinstance(data, dict):
            return Result.failure("切片状态格式错误", code="checkpoint_invalid")

        try:
            return Result.success(cls(**data))
        except (TypeError, ValueError) as exc:
            return Result.failure(
                "切片状态恢复失败",
                code="checkpoint_invalid",
                exception=str(exc),
            )


@doc(
    summary="保存单个任务的运行时状态",
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
class TaskState:
    task_id: str
    status: TaskStatus = "pending"
    current_stage: TaskStage = "pending"
    completed_slices: list[int] = field(default_factory=list)
    slice_states: list[SliceState] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    @doc(
        summary="将任务状态转换为可写入 JSON 的字典",
        returns="可被 JSON 模块写入的任务状态字典",
    )
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["slice_states"] = [
            slice_state.to_dict() for slice_state in self.slice_states
        ]
        return data

    @classmethod
    @doc(
        summary="从字典恢复任务状态",
        parameters={
            "cls": "任务状态类型",
            "data": "从 checkpoint 中读取出的任务状态字典",
        },
        returns="成功时 value 为任务状态，失败时返回 checkpoint 格式错误",
    )
    def from_dict(cls, data: Any) -> Result["TaskState"]:
        if not isinstance(data, dict):
            return Result.failure("任务状态格式错误", code="checkpoint_invalid")

        try:
            slice_states: list[SliceState] = []
            for slice_state_data in data.get("slice_states", []):
                slice_state_result = SliceState.from_dict(slice_state_data)
                if not slice_state_result.ok:
                    return Result.failure(
                        slice_state_result.error or "切片状态恢复失败",
                        code=slice_state_result.code,
                        **slice_state_result.data,
                    )
                slice_states.append(slice_state_result.unwrap())

            return Result.success(
                cls(
                    task_id=cast(str, data["task_id"]),
                    status=cast(Any, data.get("status", "pending")),
                    current_stage=cast(Any, data.get("current_stage", "pending")),
                    completed_slices=list(cast(list[int], data.get("completed_slices", []))),
                    slice_states=slice_states,
                    metadata=dict(cast(dict[str, Any], data.get("metadata", {}))),
                    error_message=cast(str | None, data.get("error_message")),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            return Result.failure(
                "任务状态恢复失败",
                code="checkpoint_invalid",
                exception=str(exc),
            )


__all__ = [
    "TaskStage",
    "SliceState",
    "TaskState",
]
