from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from numpydoc_decorator import doc

if TYPE_CHECKING:
    from .checkpoint import CheckpointStore
    from ..core.paths import WorkspacePaths
    from ..llm.client import LlmClient
    from ..log.logger import Logger
    from .module.executor import ExecutorConfig
    from .state import TaskState


@doc(
    summary="Stage 执行上下文，由 Engine 组装后注入各 Stage",
    parameters={
        "llm_client": "LLM 调用客户端，Stage 通过它发起模型请求",
        "logger": "日志记录器，Stage 通过它写入结构化日志",
        "state": "任务运行时状态，Stage 通过它读取/更新执行进度",
        "checkpoint_store": "检查点存储，Stage 通过它持久化/恢复任务状态",
        "workspace": "工作区路径布局，Stage 通过它确定输入输出文件位置",
        "executor_config": "执行器配置，Stage 通过它获取并行度等运行时参数",
    },
)
@dataclass
class StageContext:
    llm_client: LlmClient
    logger: Logger
    state: TaskState
    checkpoint_store: CheckpointStore
    workspace: WorkspacePaths
    executor_config: ExecutorConfig


__all__ = ["StageContext"]
