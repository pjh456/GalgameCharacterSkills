from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GlobalSettings:
    """全局共享运行配置"""

    base_url: str  # 服务请求地址
    api_key: str  # 服务鉴权密钥
    model_name: str  # 默认使用的模型名
    request_timeout: int = 60  # 单次请求超时时间
    max_retries: int = 3  # 单次请求最大重试次数


_settings_singleton: Optional[GlobalSettings] = None


def set_global_settings(settings: GlobalSettings) -> None:
    global _settings_singleton
    _settings_singleton = settings


def get_global_settings() -> GlobalSettings:
    if _settings_singleton is None:
        raise RuntimeError("全局设置尚未初始化")
    return _settings_singleton
