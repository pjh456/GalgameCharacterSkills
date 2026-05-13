from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

from numpydoc_decorator import doc

from .. import fs
from ..core.paths import WorkspacePaths
from ..core.result import Result
from .state import SliceState, TaskState
from .task import GenerationTaskConfig, SliceConfig, SliceSummaryTaskConfig, TaskConfig


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
            "task_config": _task_config_to_dict(self.task_config),
            "task_state": _task_state_to_dict(self.task_state),
        }

    @classmethod
    @doc(
        summary="从字典恢复任务检查点",
        parameters={
            "cls": "任务检查点类型",
            "data": "从 JSON 读取出的原始字典",
        },
        returns="表示恢复结果的显式结果对象",
    )
    def from_dict(cls, data: Any) -> Result["TaskCheckpoint"]:
        if not isinstance(data, dict):
            return Result.failure("Checkpoint 数据格式错误", code="checkpoint_invalid")

        task_config_result = _task_config_from_dict(data.get("task_config"))
        if not task_config_result.ok:
            return Result.failure(
                task_config_result.error or "任务配置恢复失败",
                code=task_config_result.code,
                **task_config_result.data,
            )

        task_state_result = _task_state_from_dict(data.get("task_state"))
        if not task_state_result.ok:
            return Result.failure(
                task_state_result.error or "任务状态恢复失败",
                code=task_state_result.code,
                **task_state_result.data,
            )

        return Result.success(
            cls(
                task_config=task_config_result.unwrap(),
                task_state=task_state_result.unwrap(),
            )
        )


@doc(
    summary="负责在指定工作区读写任务检查点",
    parameters={"workspace_paths": "本次运行使用的工作区路径布局"},
)
class CheckpointStore:
    def __init__(self, workspace_paths: WorkspacePaths) -> None:
        self.workspace_paths = workspace_paths

    @doc(
        summary="根据任务编号推导 checkpoint 文件路径",
        parameters={"task_id": "任务唯一标识"},
        returns="对应任务 checkpoint 文件的完整路径",
    )
    def get_path(self, task_id: str) -> Path:
        return self.workspace_paths.checkpoints_dir / f"{task_id}.json"

    @doc(
        summary="保存任务检查点到工作区",
        parameters={"checkpoint": "需要保存的任务检查点"},
        returns="成功时 value 为写入的 checkpoint 文件路径，失败时返回显式错误",
    )
    def save(self, checkpoint: TaskCheckpoint) -> Result[Path]:
        path = self.get_path(checkpoint.task_state.task_id)
        write_result = fs.json.write(path, checkpoint.to_dict())

        if not write_result.ok:
            data = dict(write_result.data)
            data["checkpoint_path"] = str(path)
            return Result.failure(
                write_result.error or "保存 checkpoint 失败",
                code=write_result.code,
                **data,
            )

        return Result.success(path)

    @doc(
        summary="从工作区读取任务检查点",
        parameters={"task_id": "任务唯一标识"},
        returns="成功时 value 为任务检查点，失败时返回显式错误",
    )
    def load(self, task_id: str) -> Result[TaskCheckpoint]:
        path = self.get_path(task_id)
        read_result = fs.json.read(path)

        if not read_result.ok:
            data = dict(read_result.data)
            data["checkpoint_path"] = str(path)
            return Result.failure(
                read_result.error or "读取 checkpoint 失败",
                code=read_result.code,
                **data,
            )

        checkpoint_result = TaskCheckpoint.from_dict(read_result.value)
        if not checkpoint_result.ok:
            data = dict(checkpoint_result.data)
            data["checkpoint_path"] = str(path)
            return Result.failure(
                checkpoint_result.error or "恢复 checkpoint 失败",
                code=checkpoint_result.code,
                **data,
            )

        return checkpoint_result


@doc(
    summary="将任务配置转换为可写入 JSON 的字典",
    parameters={"task_config": "需要转换的任务配置"},
    returns="可被 JSON 模块写入的任务配置字典",
)
def _task_config_to_dict(task_config: TaskConfig) -> dict[str, Any]:
    data = asdict(task_config)

    if isinstance(task_config, SliceSummaryTaskConfig):
        data["input_files"] = list(task_config.input_files)

    return data


@doc(
    summary="从字典恢复任务配置",
    parameters={"data": "从 checkpoint 中读取出的任务配置字典"},
    returns="成功时 value 为具体任务配置，失败时返回 checkpoint 格式错误",
)
def _task_config_from_dict(data: Any) -> Result[TaskConfig]:
    if not isinstance(data, dict):
        return Result.failure("任务配置格式错误", code="checkpoint_invalid")

    kind = data.get("kind")

    try:
        if kind == "summarize":
            slice_config_data = data.get("slice_config", {})
            if not isinstance(slice_config_data, dict):
                return Result.failure("切片配置格式错误", code="checkpoint_invalid")

            return Result.success(
                SliceSummaryTaskConfig(
                    role_name=cast(str, data["role_name"]),
                    system_prompt=cast(str, data.get("system_prompt", "")),
                    extra_instruction=cast(str, data.get("extra_instruction", "")),
                    use_vndb=cast(bool, data.get("use_vndb", False)),
                    temperature=cast(float, data.get("temperature", 0.7)),
                    max_output_tokens=cast(int, data.get("max_output_tokens", 4096)),
                    input_files=tuple(cast(list[str], data["input_files"])),
                    slice_config=SliceConfig(**slice_config_data),
                )
            )

        if kind in {"skills", "chara_card"}:
            return Result.success(
                GenerationTaskConfig(
                    role_name=cast(str, data["role_name"]),
                    system_prompt=cast(str, data.get("system_prompt", "")),
                    extra_instruction=cast(str, data.get("extra_instruction", "")),
                    use_vndb=cast(bool, data.get("use_vndb", False)),
                    temperature=cast(float, data.get("temperature", 0.7)),
                    max_output_tokens=cast(int, data.get("max_output_tokens", 4096)),
                    kind=cast(Any, kind),
                    summary_task_id=cast(str, data["summary_task_id"]),
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        return Result.failure(
            "任务配置恢复失败",
            code="checkpoint_invalid",
            exception=str(exc),
        )

    return Result.failure(
        "未知任务类型",
        code="checkpoint_unknown_task_kind",
        kind=kind,
    )


@doc(
    summary="将任务状态转换为可写入 JSON 的字典",
    parameters={"task_state": "需要转换的任务状态"},
    returns="可被 JSON 模块写入的任务状态字典",
)
def _task_state_to_dict(task_state: TaskState) -> dict[str, Any]:
    return asdict(task_state)


@doc(
    summary="从字典恢复任务状态",
    parameters={"data": "从 checkpoint 中读取出的任务状态字典"},
    returns="成功时 value 为任务状态，失败时返回 checkpoint 格式错误",
)
def _task_state_from_dict(data: Any) -> Result[TaskState]:
    if not isinstance(data, dict):
        return Result.failure("任务状态格式错误", code="checkpoint_invalid")

    try:
        slice_states = [
            SliceState(**slice_state_data)
            for slice_state_data in data.get("slice_states", [])
        ]

        return Result.success(
            TaskState(
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
    "CheckpointStore",
    "TaskCheckpoint",
]
