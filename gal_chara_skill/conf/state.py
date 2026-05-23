from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

from numpydoc_decorator import doc

from ..core.result import Result
from ..core.validate import FieldRule, validate_dict_fields
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
    @validate_dict_fields(
        error="切片状态格式错误",
        code="checkpoint_invalid",
        keep_unknown=False,
        slice_index=FieldRule(int, error="切片编号格式错误", validator=lambda value: value >= 0 or "必须大于或等于 0"),
        source_file=FieldRule(str, error="源文件名格式错误", non_empty=True),
        source_slice_index=FieldRule(int, error="源切片编号格式错误", validator=lambda value: value >= 0 or "必须大于或等于 0"),
        status=FieldRule(
            str,
            error="切片执行状态格式错误",
            required=False,
            default="pending",
            literal={"pending", "running", "paused", "failed", "completed"},
        ),
        attempt_count=FieldRule(
            int,
            error="尝试次数格式错误",
            required=False,
            default=0,
            validator=lambda value: value >= 0 or "必须大于或等于 0",
        ),
        error_message=FieldRule(str, required=False, default=None, allow_none=True),
    )
    @doc(
        summary="从字典恢复切片状态",
        parameters={
            "cls": "切片状态类型",
            "data": "从 checkpoint 中读取出的切片状态字典",
        },
        returns="成功时 value 为切片状态，失败时返回 checkpoint 格式错误",
    )
    def from_dict(cls, data: Any) -> Result["SliceState"]:
        return Result.success(cls(**data))


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
    @validate_dict_fields(
        error="任务状态格式错误",
        code="checkpoint_invalid",
        keep_unknown=False,
        task_id=FieldRule(str, error="任务 ID 格式错误", non_empty=True),
        status=FieldRule(
            str,
            error="任务执行状态格式错误",
            required=False,
            default="pending",
            literal={"pending", "running", "paused", "failed", "completed"},
        ),
        current_stage=FieldRule(
            str,
            error="任务阶段格式错误",
            required=False,
            default="pending",
            literal={"pending", "preparing", "slicing", "summarizing", "generating", "finalizing", "cleaning"},
        ),
        completed_slices=FieldRule(
            list,
            error="已完成切片列表格式错误",
            required=False,
            default=[],
            item_type=int,
            validator=lambda values: all(value >= 0 for value in values) or "切片编号必须大于或等于 0",
        ),
        slice_states=FieldRule(
            list,
            error="切片状态格式错误",
            required=False,
            default=[],
            item_type=dict,
            item_transform=SliceState.from_dict,
        ),
        metadata=FieldRule(dict, error="任务元数据格式错误", required=False, default={}),
        error_message=FieldRule(str, required=False, default=None, allow_none=True),
    )
    @doc(
        summary="从字典恢复任务状态",
        parameters={
            "cls": "任务状态类型",
            "data": "从 checkpoint 中读取出的任务状态字典",
        },
        returns="成功时 value 为任务状态，失败时返回 checkpoint 格式错误",
    )
    def from_dict(cls, data: Any) -> Result["TaskState"]:
        return Result.success(
            cls(
                **{
                    **data,
                    "completed_slices": list(data["completed_slices"]),
                    "slice_states": list(data["slice_states"]),
                    "metadata": dict(data["metadata"]),
                }
            )
        )


__all__ = [
    "TaskStage",
    "SliceState",
    "TaskState",
]
