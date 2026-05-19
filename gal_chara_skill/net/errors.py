from __future__ import annotations

from inspect import BoundArguments
import socket
from typing import TYPE_CHECKING, Any, Optional, cast

from numpydoc_decorator import doc

from ..core.result import Result

if TYPE_CHECKING:
    from .models import HttpResponse, JsonResponse, JsonValue


@doc(summary="负责构造 net 模块统一错误结果的无状态工具类")
class NetErrors:
    @staticmethod
    @doc(
        summary="构造 HTTP 错误响应对应的失败结果",
        parameters={"response": "由 HTTPError 恢复出的 HTTP 响应"},
        returns="表示 HTTP 错误的失败结果",
    )
    def http_error(response: HttpResponse) -> Result[HttpResponse]:
        return Result.failure(
            "HTTP 请求失败",
            code="net_http_error",
            value=response,
            url=response.url,
            status_code=response.status_code,
        )

    @staticmethod
    @doc(
        summary="构造网络超时对应的失败结果",
        parameters={
            "target_url": "发生超时的目标地址",
            "exception": "原始异常对象",
        },
        returns="表示网络超时的失败结果",
    )
    def timeout(target_url: str, exception: BaseException) -> Result[HttpResponse]:
        return Result.failure(
            "网络请求超时",
            code="net_timeout",
            url=target_url,
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="构造网络连接失败对应的失败结果",
        parameters={
            "target_url": "发生连接失败的目标地址",
            "exception": "原始异常对象或其 reason",
        },
        returns="表示网络连接失败的失败结果",
    )
    def connect_failed(target_url: str, exception: object) -> Result[HttpResponse]:
        return Result.failure(
            "网络连接失败",
            code="net_connect_failed",
            url=target_url,
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="根据 URLError 构造网络层失败结果",
        parameters={
            "target_url": "发生请求失败的目标地址",
            "exception": "捕获到的 URLError 对象",
        },
        returns="超时场景返回超时结果，其余场景返回连接失败结果",
    )
    def url_error(target_url: str, exception: BaseException) -> Result[HttpResponse]:
        reason = getattr(exception, "reason", None)
        if isinstance(reason, socket.timeout):
            return NetErrors.timeout(target_url, reason)

        return NetErrors.connect_failed(target_url, reason or exception)

    @staticmethod
    @doc(
        summary="构造未分类请求失败对应的失败结果",
        parameters={
            "target_url": "发生请求失败的目标地址",
            "exception": "原始异常对象",
        },
        returns="表示未分类请求失败的失败结果",
    )
    def request_failed(target_url: str, exception: BaseException) -> Result[HttpResponse]:
        return Result.failure(
            "网络请求失败",
            code="net_request_failed",
            url=target_url,
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="构造请求 JSON 序列化失败对应的失败结果",
        parameters={
            "exception": "原始序列化异常对象",
        },
        returns="表示请求 JSON 序列化失败的失败结果",
    )
    def request_json_parse_failed(exception: BaseException) -> Result[bytes]:
        return Result.failure(
            "请求 JSON 序列化失败",
            code="net_parse_failed",
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="把请求 JSON 构造失败结果重包装为 HTTP 请求失败结果",
        parameters={
            "target_url": "原本打算请求的目标地址",
            "result": "JSON 构造阶段得到的失败结果",
        },
        returns="供 HTTP 请求入口直接返回的失败结果",
    )
    def request_json_build_failed(
        target_url: str,
        result: Result[Any],
    ) -> Result[HttpResponse]:
        return Result.failure(
            result.error or "请求 JSON 序列化失败",
            code=result.code,
            url=target_url,
            **result.data,
        )

    @staticmethod
    @doc(
        summary="构造原始请求体缺少编码参数对应的失败结果",
        parameters={"target_url": "原本打算请求的目标地址"},
        returns="表示原始字符串请求体缺少显式编码参数的失败结果",
    )
    def raw_body_encoding_missing(target_url: str) -> Result[HttpResponse]:
        return Result.failure(
            "原始请求体缺少编码参数",
            code="net_request_invalid",
            url=target_url,
        )

    @staticmethod
    @doc(
        summary="构造底层响应转换失败对应的失败结果",
        parameters={
            "exception": "原始响应转换异常对象",
        },
        returns="表示底层响应无法转换为 HTTP 响应模型的失败结果",
    )
    def response_build_failed(exception: BaseException) -> Result[HttpResponse]:
        return Result.failure(
            "响应对象转换失败",
            code="net_parse_failed",
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="构造响应 JSON 解析失败对应的失败结果",
        parameters={
            "response": "解析失败的原始 HTTP 响应",
            "exception": "原始解析异常对象",
        },
        returns="表示响应 JSON 解析失败的失败结果",
    )
    def response_json_parse_failed(
        response: HttpResponse,
        exception: BaseException,
    ) -> Result[JsonValue]:
        return Result.failure(
            "响应 JSON 解析失败",
            code="net_parse_failed",
            url=response.url,
            status_code=response.status_code,
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="构造响应体解码失败对应的失败结果",
        parameters={
            "response": "解码失败的原始 HTTP 响应",
            "exception": "原始解码异常对象",
        },
        returns="表示响应体解码失败的失败结果",
    )
    def response_decode_failed(
        response: HttpResponse,
        exception: BaseException,
    ) -> Result[JsonValue]:
        return Result.failure(
            "响应体解码失败",
            code="net_decode_failed",
            url=response.url,
            status_code=response.status_code,
            exception=str(exception),
        )

    @staticmethod
    @doc(
        summary="把 HTTP 请求失败结果重包装为 JSON 请求失败结果",
        parameters={"result": "原始 HTTP 请求失败结果"},
        returns="附带 JSON 响应占位值的失败结果",
    )
    def json_request_failed(result: Result[HttpResponse]) -> Result[JsonResponse]:
        from .response import ResponseParser

        return Result.failure(
            result.error or "请求失败",
            code=result.code,
            value=ResponseParser.json_value(result.value),
            **result.data,
        )

    @staticmethod
    @doc(
        summary="构造重试耗尽后的失败结果",
        parameters={"last_result": "最后一次请求得到的失败结果，允许为空"},
        returns="重试耗尽后的最终失败结果",
    )
    def retry_exhausted(last_result: Optional[Result[HttpResponse]]) -> Result[HttpResponse]:
        if last_result is None:
            return Result.failure("网络请求失败", code="net_request_failed")

        return Result.failure(
            last_result.error or "网络请求失败",
            code="net_retry_exhausted",
            value=last_result.value,
            last_code=last_result.code,
            **last_result.data,
        )

    @staticmethod
    @doc(
        summary="将 HTTPError 转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的 HTTPError",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示 HTTP 错误的失败结果",
    )
    def handle_http_error(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[HttpResponse]:
        del bound
        from .response import RawHttpResponseLike, ResponseParser

        response_result = ResponseParser.from_raw(cast(RawHttpResponseLike, exception))
        if not response_result.ok:
            return response_result
        return NetErrors.http_error(response_result.unwrap())

    @staticmethod
    @doc(
        summary="将超时异常转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的超时异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示网络超时的失败结果",
    )
    def handle_timeout(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[HttpResponse]:
        return NetErrors.timeout(str(bound.arguments["target_url"]), exception)

    @staticmethod
    @doc(
        summary="将 URLError 转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的 URLError",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示网络层失败的结果",
    )
    def handle_url_error(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[HttpResponse]:
        return NetErrors.url_error(str(bound.arguments["target_url"]), exception)

    @staticmethod
    @doc(
        summary="将未分类请求异常转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的异常对象",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示未分类请求失败的结果",
    )
    def handle_request_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[HttpResponse]:
        return NetErrors.request_failed(str(bound.arguments["target_url"]), exception)

    @staticmethod
    @doc(
        summary="将请求 JSON 序列化异常转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的 JSON 序列化异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示请求 JSON 序列化失败的结果",
    )
    def handle_request_json_parse_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[bytes]:
        del bound
        return NetErrors.request_json_parse_failed(exception)

    @staticmethod
    @doc(
        summary="将响应 JSON 解析异常转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的 JSON 解析异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示响应 JSON 解析失败的结果",
    )
    def handle_response_json_parse_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[JsonValue]:
        return NetErrors.response_json_parse_failed(bound.arguments["self"], exception)

    @staticmethod
    @doc(
        summary="将响应解码异常转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的响应解码异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示响应体解码失败的结果",
    )
    def handle_response_decode_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[JsonValue]:
        return NetErrors.response_decode_failed(bound.arguments["self"], exception)

    @staticmethod
    @doc(
        summary="将底层响应转换异常转换为 net 模块失败结果",
        parameters={
            "exception": "捕获到的响应转换异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示响应对象转换失败的结果",
    )
    def handle_response_build_failed(
        exception: BaseException,
        bound: BoundArguments,
    ) -> Result[HttpResponse]:
        del bound
        return NetErrors.response_build_failed(exception)


__all__ = [
    "NetErrors",
]
