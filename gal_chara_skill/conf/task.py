from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union

TaskKind = Literal["summarize", "skills", "chara_card"]
TaskStatus = Literal[
    "pending",
    "running",
    "paused",
    "failed",
    "completed",
]
GenerationKind = Literal["skills", "chara_card"]


@dataclass(frozen=True, kw_only=True)
class BaseTaskConfig:
    """任务共享的静态输入配置"""

    role_name: str  # 需要处理的角色名
    system_prompt: str = ""  # 系统提示词
    extra_instruction: str = ""  # 额外指令
    use_vndb: bool = False  # 是否启用 VNDB 信息增强
    temperature: float = 0.7  # 模型采样温度
    max_output_tokens: int = 4096  # 单次输出允许的最大 token 数


@dataclass(frozen=True)
class SliceConfig:
    """文本输入 LLM 前的切片参数"""

    max_tokens: int = 12000  # 单个切片允许的最大 token 数
    parallelism: int = 4  # 切片任务允许的并发数


@dataclass(frozen=True, kw_only=True)
class SliceSummaryTaskConfig(BaseTaskConfig):
    """切片总结任务的静态输入配置"""

    input_files: tuple[str, ...]  # 任务要读取的输入文件名
    kind: Literal["summarize"] = "summarize"  # 任务类型固定为 summarize
    slice_config: SliceConfig = field(default_factory=SliceConfig)  # 文本切片策略


@dataclass(frozen=True, kw_only=True)
class GenerationTaskConfig(BaseTaskConfig):
    """基于切片总结生成最终产物的静态输入配置"""

    kind: GenerationKind  # 当前生成任务的类型
    summary_task_id: str  # 提供切片总结结果的上游任务 id


TaskConfig = Union[SliceSummaryTaskConfig, GenerationTaskConfig]
