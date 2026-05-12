from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union

from numpydoc_decorator import doc

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


TaskConfig = Union[SliceSummaryTaskConfig, GenerationTaskConfig]


__all__ = [
    "TaskKind",
    "TaskStatus",
    "GenerationKind",
    "BaseTaskConfig",
    "SliceConfig",
    "SliceSummaryTaskConfig",
    "GenerationTaskConfig",
    "TaskConfig",
]
