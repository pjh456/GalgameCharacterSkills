from __future__ import annotations

from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result


@doc(summary="负责重试判定与退避时间计算的无状态工具类")
class RetryPolicy:
    @staticmethod
    @doc(
        summary="判断某个 HTTP 状态码是否属于可重试范围",
        parameters={
            "status_code": "当前 HTTP 状态码",
            "status_codes": "允许触发重试的状态码集合",
        },
        returns="当前状态码是否属于可重试范围",
    )
    def matches_status(status_code: int, status_codes: tuple[int, ...]) -> bool:
        return status_code in status_codes

    @staticmethod
    @doc(
        summary="判断一次请求失败结果是否适合重试",
        parameters={
            "result": "一次请求返回的结果对象",
            "status_codes": "允许触发重试的状态码集合",
        },
        returns="当前失败结果是否适合重试",
    )
    def matches_result(result: Result[Any], status_codes: tuple[int, ...]) -> bool:
        if result.ok:
            return False

        if result.code in {"net_timeout", "net_connect_failed"}:
            return True

        if result.code != "net_http_error":
            return False

        status_code = result.data.get("status_code")
        if not isinstance(status_code, int):
            return False

        return RetryPolicy.matches_status(status_code, status_codes)

    @staticmethod
    @doc(
        summary="计算某次重试前应等待的秒数",
        parameters={
            "attempt": "从 1 开始的重试轮次",
            "base_delay": "第一次重试使用的基础等待秒数",
        },
        returns="当前轮次建议的等待秒数",
    )
    def delay(attempt: int, base_delay: float) -> float:
        # 指数退避
        if attempt <= 0:
            return 0.0
        return max(0.0, base_delay) * (2 ** (attempt - 1))


__all__ = [
    "RetryPolicy",
]
