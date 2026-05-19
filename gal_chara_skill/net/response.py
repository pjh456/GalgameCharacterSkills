from __future__ import annotations

from collections.abc import Iterable
from typing import Optional, Protocol

from numpydoc_decorator import doc

from ..core.catch import catch_result
from ..core.result import Result
from .errors import NetErrors
from .models import HttpResponse, JsonResponse


class RawHeadersLike(Protocol):
    def items(self) -> Iterable[tuple[str, str]]: ...


class RawHttpResponseLike(Protocol):
    status: int
    headers: RawHeadersLike

    def geturl(self) -> str: ...
    def read(self) -> bytes: ...


@doc(summary="负责 HTTP 响应模型转换与 JSON 解析的无状态工具类")
class ResponseParser:
    @staticmethod
    @doc(
        summary="把底层响应对象转换为项目内部的 HTTP 响应模型",
        parameters={"response": "底层 HTTP 客户端返回的响应对象"},
        returns="统一的 HTTP 响应模型",
    )
    @catch_result(
        handlers={
            (
                AttributeError,
                TypeError,
                ValueError,
            ): NetErrors.handle_response_build_failed,
        }
    )
    def from_raw(response: RawHttpResponseLike) -> HttpResponse:
        headers = {key: value for key, value in response.headers.items()}
        return HttpResponse(
            status_code=int(response.status),
            url=str(response.geturl()),
            headers=headers,
            body=response.read(),
        )

    @staticmethod
    @doc(
        summary="把 HTTP 响应解析为包含 JSON 数据的结果对象",
        parameters={"response": "需要解析的 HTTP 响应"},
        returns="成功时 value 为 JSON 响应对象，失败时返回 JSON 解析错误",
    )
    def parse_json(response: HttpResponse) -> Result[JsonResponse]:
        json_result = response.json()
        if not json_result.ok:
            return Result.failure_from(
                json_result,
                error=json_result.error or "响应 JSON 解析失败",
                code=json_result.code,
                value=JsonResponse(response=response, data=None),
            )

        return Result.success(JsonResponse(response=response, data=json_result.unwrap()))

    @staticmethod
    @doc(
        summary="为失败的 JSON 请求结果构造占位值",
        parameters={"response": "失败结果里可能附带的 HTTP 响应"},
        returns="若存在原始响应则返回不带数据的 JSON 响应对象，否则返回 None",
    )
    def json_value(response: Optional[HttpResponse]) -> Optional[JsonResponse]:
        if response is None:
            return None
        return JsonResponse(response=response, data=None)


__all__ = [
    "RawHeadersLike",
    "RawHttpResponseLike",
    "ResponseParser",
]
