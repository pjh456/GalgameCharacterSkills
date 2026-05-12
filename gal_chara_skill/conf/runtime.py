from __future__ import annotations

from dataclasses import dataclass, field

from numpydoc_decorator import doc

from .module.log import LogConfig


@doc(
    summary="保存一次运行共享的基础配置",
    parameters={
        "base_url": "服务请求地址",
        "api_key": "服务鉴权密钥",
        "model_name": "默认使用的模型名",
        "request_timeout": "单次请求超时时间",
        "max_retries": "单次请求最大重试次数",
        "log_config": "日志模块使用的运行配置",
    },
)
@dataclass(frozen=True)
class RuntimeConfig:
    base_url: str
    api_key: str
    model_name: str
    request_timeout: int = 60
    max_retries: int = 3
    log_config: LogConfig = field(default_factory=LogConfig)


__all__ = ["RuntimeConfig"]
