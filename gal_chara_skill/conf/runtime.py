from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from numpydoc_decorator import doc

from ..core.paths import DEFAULT_WORKSPACE_PATHS, WorkspacePaths
from .module.log import LogPathConfig, LogPolicy


@doc(
    summary="保存一次运行共享的基础配置",
    parameters={
        "base_url": "服务请求地址",
        "api_key": "服务鉴权密钥",
        "model_name": "默认使用的模型名",
        "request_timeout": "单次请求超时时间",
        "max_retries": "单次请求最大重试次数",
        "log_policy": "日志模块使用的记录行为配置",
        "log_path_config": "日志模块使用的路径配置",
        "workspace_paths": "本次运行使用的工作区路径布局",
    },
)
@dataclass(frozen=True)
class RuntimeConfig:
    base_url: str
    api_key: str
    model_name: str
    request_timeout: int = 60
    max_retries: int = 3
    log_policy: LogPolicy = field(default_factory=LogPolicy)
    workspace_paths: WorkspacePaths = field(default_factory=lambda: DEFAULT_WORKSPACE_PATHS)
    log_path_config: Optional[LogPathConfig] = None

    def __post_init__(self) -> None:
        if self.log_path_config is None:
            object.__setattr__(
                self,
                "log_path_config",
                LogPathConfig(root_dir=self.workspace_paths.logs_dir),
            )


__all__ = ["RuntimeConfig"]
