from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from numpydoc_decorator import doc

from ..core.paths import WorkspacePaths
from .module.llm import LlmConfig
from .module.log import LogPathConfig, LogPolicy
from .module.net import NetConfig


@doc(
    summary="保存一次运行共享的基础配置",
    parameters={
        "llm_config": "LLM 调用模块使用的运行配置",
        "net_config": "网络请求模块使用的运行配置",
        "log_policy": "日志模块使用的记录行为配置",
        "log_path_config": "日志模块使用的路径配置",
        "workspace_paths": "本次运行使用的工作区路径布局",
    },
)
@dataclass(frozen=True)
class RuntimeConfig:
    llm_config: LlmConfig
    net_config: NetConfig
    workspace_paths: WorkspacePaths
    log_policy: LogPolicy = field(default_factory=LogPolicy)
    log_path_config: Optional[LogPathConfig] = None

    def __post_init__(self) -> None:
        if self.log_path_config is None:
            object.__setattr__(
                self,
                "log_path_config",
                LogPathConfig(root_dir=self.workspace_paths.logs_dir),
            )


__all__ = ["RuntimeConfig"]
