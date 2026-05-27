from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional, Union

from numpydoc_decorator import doc

from ..core.result import Result
from ..core.validate import FieldRule, validate_dict_fields

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
        "vndb_data": "VNDB 角色数据字典，启用增强时注入 prompt",
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
    vndb_data: Optional[dict[str, str]] = None
    temperature: float = 0.7
    max_output_tokens: int = 4096

    @doc(
        summary="将任务配置转换为可写入 JSON 的字典",
        returns="可被 JSON 模块写入的任务配置字典",
    )
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    @validate_dict_fields(
        error="任务配置格式错误",
        code="checkpoint_invalid",
        kind=FieldRule(str, error="任务类型格式错误", non_empty=True),
        role_name=FieldRule(str, error="角色名格式错误", non_empty=True),
        system_prompt=FieldRule(str, required=False, default=""),
        extra_instruction=FieldRule(str, required=False, default=""),
        use_vndb=FieldRule(bool, required=False, default=False),
        vndb_data=FieldRule(dict, required=False, default=None, allow_none=True),
        temperature=FieldRule(
            (int, float),
            error="采样温度格式错误",
            required=False,
            default=0.7,
            transform=float,
            validator=lambda value: value >= 0 or "必须大于或等于 0",
        ),
        max_output_tokens=FieldRule(
            int,
            error="输出 token 上限格式错误",
            required=False,
            default=4096,
            validator=lambda value: value > 0 or "必须大于 0",
        ),
    )
    @doc(
        summary="从字典恢复具体任务配置",
        parameters={"data": "从 checkpoint 中读取出的任务配置字典"},
        returns="成功时 value 为具体任务配置，失败时返回 checkpoint 格式错误",
    )
    def from_dict(data: Any) -> "Result[TaskConfig]":
        kind = data.get("kind")

        if kind == "summarize":
            return BaseTaskConfig._build_slice_summary_task_config(data)

        if kind in {"skills", "chara_card"}:
            return BaseTaskConfig._build_generation_task_config(data)

        return Result.failure(
            "未知任务类型",
            code="checkpoint_unknown_task_kind",
            kind=kind,
        )

    @staticmethod
    @validate_dict_fields(
        error="任务配置格式错误",
        code="checkpoint_invalid",
        keep_unknown=False,
        kind=FieldRule(str, error="任务类型格式错误", non_empty=True),
        role_name=FieldRule(str, error="角色名格式错误", non_empty=True),
        system_prompt=FieldRule(str, required=False, default=""),
        extra_instruction=FieldRule(str, required=False, default=""),
        use_vndb=FieldRule(bool, required=False, default=False),
        vndb_data=FieldRule(dict, required=False, default=None, allow_none=True),
        temperature=FieldRule(
            (int, float),
            error="采样温度格式错误",
            required=False,
            default=0.7,
            transform=float,
            validator=lambda value: value >= 0 or "必须大于或等于 0",
        ),
        max_output_tokens=FieldRule(
            int,
            error="输出 token 上限格式错误",
            required=False,
            default=4096,
            validator=lambda value: value > 0 or "必须大于 0",
        ),
        input_files=FieldRule(list, error="输入文件列表格式错误", item_type=str, transform=tuple),
        slice_config=FieldRule(
            dict,
            error="切片配置格式错误",
            required=False,
            default={},
            transform=lambda value: SliceConfig.from_dict(value),
        ),
    )
    @doc(
        summary="恢复切片总结任务配置",
        parameters={"data": "已完成通用字段校验的任务配置字典"},
        returns="成功时 value 为切片总结任务配置，失败时返回格式或构造错误",
    )
    def _build_slice_summary_task_config(data: Any) -> "Result[TaskConfig]":
        return Result.success(SliceSummaryTaskConfig(**data))

    @staticmethod
    @validate_dict_fields(
        error="任务配置格式错误",
        code="checkpoint_invalid",
        keep_unknown=False,
        kind=FieldRule(str, error="任务类型格式错误", non_empty=True),
        role_name=FieldRule(str, error="角色名格式错误", non_empty=True),
        system_prompt=FieldRule(str, required=False, default=""),
        extra_instruction=FieldRule(str, required=False, default=""),
        use_vndb=FieldRule(bool, required=False, default=False),
        vndb_data=FieldRule(dict, required=False, default=None, allow_none=True),
        temperature=FieldRule(
            (int, float),
            error="采样温度格式错误",
            required=False,
            default=0.7,
            transform=float,
            validator=lambda value: value >= 0 or "必须大于或等于 0",
        ),
        max_output_tokens=FieldRule(
            int,
            error="输出 token 上限格式错误",
            required=False,
            default=4096,
            validator=lambda value: value > 0 or "必须大于 0",
        ),
        summary_task_id=FieldRule(str, error="总结任务 ID 格式错误", non_empty=True),
    )
    @doc(
        summary="恢复最终产物生成任务配置",
        parameters={"data": "已完成通用字段校验的任务配置字典"},
        returns="成功时 value 为生成任务配置，失败时返回格式错误",
    )
    def _build_generation_task_config(data: Any) -> "Result[TaskConfig]":
        return Result.success(GenerationTaskConfig(**data))


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

    @classmethod
    @validate_dict_fields(
        error="切片配置格式错误",
        code="checkpoint_invalid",
        keep_unknown=False,
        max_tokens=FieldRule(
            int,
            error="切片 token 上限格式错误",
            required=False,
            default=12000,
            validator=lambda value: value > 0 or "必须大于 0",
        ),
        parallelism=FieldRule(
            int,
            error="切片并发数格式错误",
            required=False,
            default=4,
            validator=lambda value: value > 0 or "必须大于 0",
        ),
    )
    @doc(
        summary="从字典恢复切片配置",
        parameters={"cls": "切片配置类型", "data": "从 checkpoint 中读取出的切片配置字典"},
        returns="成功时 value 为切片配置，失败时返回 checkpoint 格式错误",
    )
    def from_dict(cls, data: Any) -> Result["SliceConfig"]:
        return Result.success(cls(**data))


@doc(
    summary="切片总结任务的静态输入配置",
    parameters={
        "role_name": "需要处理的角色名",
        "system_prompt": "系统提示词",
        "extra_instruction": "额外指令",
        "use_vndb": "是否启用 VNDB 信息增强",
        "vndb_data": "VNDB 角色数据字典",
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
        data = super().to_dict()
        data["input_files"] = list(self.input_files)
        return data


@doc(
    summary="基于切片总结生成最终产物的静态输入配置",
    parameters={
        "role_name": "需要处理的角色名",
        "system_prompt": "系统提示词",
        "extra_instruction": "额外指令",
        "use_vndb": "是否启用 VNDB 信息增强",
        "vndb_data": "VNDB 角色数据字典",
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
