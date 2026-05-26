from __future__ import annotations

from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result


@doc(summary="负责构造 llm 模块统一错误结果的无状态工具类")
class LlmErrors:
    @staticmethod
    @doc(
        summary="构造 ChatCompletion 数据模型恢复失败对应的失败结果",
        parameters={
            "url": "目标请求地址",
            "result": "ChatCompletion.from_dict 返回的失败结果",
        },
        returns="包装后的失败结果",
    )
    def completion_parse_failed(url: str, result: Result[Any]) -> Result[Any]:
        return Result.failure_from(
            result,
            error=result.error or "ChatCompletion 解析失败",
            code=result.code,
            url=url,
        )


__all__ = ["LlmErrors"]
