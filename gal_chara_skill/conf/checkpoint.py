from __future__ import annotations

from dataclasses import dataclass

from .context import TaskContext
from .task import TaskConfig


@dataclass
class CheckpointData:
    """保存任务恢复所需的检查点"""

    task_config: TaskConfig  # 对应任务的静态输入配置
    task_context: TaskContext  # 任务当前的运行时状态
