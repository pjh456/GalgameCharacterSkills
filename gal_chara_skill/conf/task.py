from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Union, cast

from numpydoc_decorator import doc

from ..core.result import Result

TaskKind = Literal["summarize", "skills", "chara_card"]
TaskStatus = Literal[
    "pending",
    "running",
    "paused",
    "failed",
    "completed",
]
GenerationKind = Literal["skills", "chara_card"]


@doc(
    summary="任务共享的静态输入配置",
    parameters={
        "role_name": "需要处理的角色名",
        "system_prompt": "系统提示词",
        "extra_instruction": "额外指令",
        "use_vndb": "是否启用 VNDB 信息增强",
        "temperature": "模型采样温度",
        "max_output_tokens": "单次输出允许的最大 token 数",
    },
)
@dataclass(frozen=True, kw_only=True)
class BaseTaskConfig:
    role_name: str
    system_prompt: str = ""
    extra_instruction: str = ""
    use_vndb: bool = False
    temperature: float = 0.7
    max_output_tokens: int = 4096


@doc(
    summary="文本输入 LLM 前的切片参数",
    parameters={
        "max_tokens": "单个切片允许的最大 token 数",
        "parallelism": "切片任务允许的并发数",
    },
)
@dataclass(frozen=True)
class SliceConfig:
    max_tokens: int = 12000
    parallelism: int = 4


@doc(
    summary="切片总结任务的静态输入配置",
    parameters={
        "role_name": "需要处理的角色名",
        "system_prompt": "系统提示词",
        "extra_instruction": "额外指令",
        "use_vndb": "是否启用 VNDB 信息增强",
        "temperature": "模型采样温度",
        "max_output_tokens": "单次输出允许的最大 token 数",
        "input_files": "任务要读取的输入文件名",
        "kind": "任务类型固定为 summarize",
        "slice_config": "文本切片策略",
    },
)
@dataclass(frozen=True, kw_only=True)
class SliceSummaryTaskConfig(BaseTaskConfig):
    input_files: tuple[str, ...]
    kind: Literal["summarize"] = "summarize"
    slice_config: SliceConfig = field(default_factory=SliceConfig)

    @doc(
        summary="将切片总结任务配置转换为可写入 JSON 的字典",
        returns="可被 JSON 模块写入的任务配置字典",
    )
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["input_files"] = list(self.input_files)
        return data


@doc(
    summary="基于切片总结生成最终产物的静态输入配置",
    parameters={
        "role_name": "需要处理的角色名",
        "system_prompt": "系统提示词",
        "extra_instruction": "额外指令",
        "use_vndb": "是否启用 VNDB 信息增强",
        "temperature": "模型采样温度",
        "max_output_tokens": "单次输出允许的最大 token 数",
        "kind": "当前生成任务的类型",
        "summary_task_id": "提供切片总结结果的上游任务 id",
    },
)
@dataclass(frozen=True, kw_only=True)
class GenerationTaskConfig(BaseTaskConfig):
    kind: GenerationKind
    summary_task_id: str

    @doc(
        summary="将生成任务配置转换为可写入 JSON 的字典",
        returns="可被 JSON 模块写入的任务配置字典",
    )
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TaskConfig = Union[SliceSummaryTaskConfig, GenerationTaskConfig]


@doc(
    summary="从字典恢复任务配置",
    parameters={"data": "从 checkpoint 中读取出的任务配置字典"},
    returns="成功时 value 为具体任务配置，失败时返回 checkpoint 格式错误",
)
def task_config_from_dict(data: Any) -> Result[TaskConfig]:
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


__all__ = [
    "TaskKind",
    "TaskStatus",
    "GenerationKind",
    "BaseTaskConfig",
    "SliceConfig",
    "SliceSummaryTaskConfig",
    "GenerationTaskConfig",
    "TaskConfig",
    "task_config_from_dict",
]
