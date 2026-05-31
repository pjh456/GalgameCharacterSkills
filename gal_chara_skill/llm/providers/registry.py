from __future__ import annotations

from typing import Callable, TypeVar

from numpydoc_decorator import doc

from .base import BaseProvider

_P = TypeVar("_P", bound=BaseProvider)

_PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {}


class ProviderNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown provider: {name}")
        self.name = name


@doc(
    summary="将 Provider 类注册到全局注册表",
    parameters={"name": "Provider 标识符"},
    returns="接收 Provider 类的装饰器",
)
def register_provider(name: str) -> Callable[[type[_P]], type[_P]]:
    def decorator(cls: type[_P]) -> type[_P]:
        _PROVIDER_REGISTRY[name] = cls
        return cls

    return decorator


@doc(
    summary="根据名称解析 Provider 实例（懒初始化）",
    parameters={"name": "Provider 标识符"},
    returns="Provider 实例",
    raises={"ProviderNotFoundError": "未知 provider 名称时抛出"},
)
def resolve_provider(name: str) -> BaseProvider:
    cls = _PROVIDER_REGISTRY.get(name)
    if cls is None:
        raise ProviderNotFoundError(name)
    return cls()


@doc(
    summary="列出所有已注册的 Provider 名称",
    returns="已注册 provider 标识符列表",
)
def list_providers() -> list[str]:
    return list(_PROVIDER_REGISTRY.keys())


__all__ = [
    "ProviderNotFoundError",
    "register_provider",
    "resolve_provider",
    "list_providers",
]
