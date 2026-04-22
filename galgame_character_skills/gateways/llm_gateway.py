"""LLM 网关模块，负责创建和提供默认的 LLM 交互客户端。"""

from typing import Any

from ..utils.llm_factory import build_llm_client
from ..llm import LLMInteraction


class LLMGateway:
    def create_client(self, config: dict[str, Any] | None = None) -> Any:
        """创建 LLM 客户端。

        Args:
            config: LLM 配置。

        Returns:
            Any: LLM 客户端实例。

        Raises:
            NotImplementedError: 子类未实现时抛出。
        """
        raise NotImplementedError

    def set_total_requests(self, total: int) -> None:
        """设置任务总请求数。

        Args:
            total: 总请求数。

        Returns:
            None

        Raises:
            NotImplementedError: 子类未实现时抛出。
        """
        raise NotImplementedError


class DefaultLLMGateway(LLMGateway):
    def create_client(self, config: dict[str, Any] | None = None) -> Any:
        """创建默认 LLM 客户端。

        Args:
            config: LLM 配置。

        Returns:
            Any: LLM 客户端实例。

        Raises:
            Exception: 客户端创建失败时向上抛出。
        """
        return build_llm_client(config)

    def set_total_requests(self, total: int) -> None:
        """设置全局总请求数。

        Args:
            total: 总请求数。

        Returns:
            None

        Raises:
            Exception: 请求数设置失败时向上抛出。
        """
        LLMInteraction.set_total_requests(total)


__all__ = ["LLMGateway", "DefaultLLMGateway"]
