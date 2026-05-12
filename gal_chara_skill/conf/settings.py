from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from numpydoc_decorator import doc

from .module.log import LogConfig


@doc(
    summary="保存全局共享运行配置",
    parameters={
        "base_url": "服务请求地址",
        "api_key": "服务鉴权密钥",
        "model_name": "默认使用的模型名",
        "request_timeout": "单次请求超时时间",
        "max_retries": "单次请求最大重试次数",
        "log_config": "日志模块使用的全局配置",
    },
)
@dataclass(frozen=True)
class GlobalSettings:
    base_url: str
    api_key: str
    model_name: str
    request_timeout: int = 60
    max_retries: int = 3
    log_config: LogConfig = field(default_factory=LogConfig)


_settings_singleton: Optional[GlobalSettings] = None


@doc(
    summary="设置当前全局运行配置",
    parameters={"settings": "需要写入的全局配置对象"},
)
def set_global_settings(settings: GlobalSettings) -> None:
    global _settings_singleton
    _settings_singleton = settings


@doc(
    summary="获取当前全局运行配置",
    returns="当前已经初始化完成的全局配置对象",
    raises={"RuntimeError": "当全局配置尚未初始化时抛出"},
)
def get_global_settings() -> GlobalSettings:
    if _settings_singleton is None:
        raise RuntimeError("全局设置尚未初始化")
    return _settings_singleton
