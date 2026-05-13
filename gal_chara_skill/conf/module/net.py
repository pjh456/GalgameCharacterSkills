from __future__ import annotations

from dataclasses import dataclass

from numpydoc_decorator import doc


@doc(
    summary="网络请求模块使用的运行配置",
    parameters={
        "timeout": "单次请求超时时间",
        "max_retries": "单次请求最大重试次数",
    },
)
@dataclass(frozen=True)
class NetConfig:
    timeout: int = 60
    max_retries: int = 3


__all__ = ["NetConfig"]
