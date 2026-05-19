from __future__ import annotations

from dataclasses import dataclass

from numpydoc_decorator import doc


@doc(
    summary="网络请求模块使用的运行配置",
    parameters={
        "timeout": "单次请求超时时间",
        "max_retries": "单次请求最大重试次数",
        "retry_backoff_seconds": "首次重试前的基础等待秒数",
        "retry_status_codes": "遇到这些状态码时允许自动重试",
    },
)
@dataclass(frozen=True)
class NetConfig:
    timeout: int = 60
    max_retries: int = 3
    retry_backoff_seconds: float = 0.5
    retry_status_codes: tuple[int, ...] = (408, 429, 500, 502, 503, 504)


__all__ = ["NetConfig"]
