from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from numpydoc_decorator import doc

from ..conf.module.net import NetConfig
from ..core.catch import catch_result
from ..core.result import Result
from .errors import NetErrors
from .models import HttpMethod, HttpResponse, JsonValue
from .request import RequestBuilder
from .response import ResponseParser
from .retry import RetryPolicy


@doc(summary="负责底层 HTTP 请求流程的无状态基类工具")
class BaseRequestExecutor:
    @staticmethod
    @doc(
        summary="在同步请求路径中按配置执行重试",
        parameters={
            "config": "网络请求配置",
            "send_once": "单次请求发送函数，成功时返回 HTTP 响应，失败时返回错误结果",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回最后一次失败结果或重试耗尽结果",
    )
    def request_with_retry(
        config: NetConfig,
        send_once: Callable[[], Result[HttpResponse]],
    ) -> Result[HttpResponse]:
        attempts = config.max_retries + 1
        last_result: Optional[Result[HttpResponse]] = None

        for attempt in range(1, attempts + 1):
            result = send_once()
            if result.ok:
                return result

            last_result = result
            should_retry = RetryPolicy.matches_result(result, config.retry_status_codes)
            if not should_retry:
                return result
            if attempt >= attempts:
                if config.max_retries <= 0:
                    return result
                return NetErrors.retry_exhausted(last_result)

            time.sleep(RetryPolicy.delay(attempt, config.retry_backoff_seconds))

        return NetErrors.retry_exhausted(last_result)

    @staticmethod
    @doc(
        summary="在异步请求路径中按配置执行重试",
        parameters={
            "config": "网络请求配置",
            "send_once": "单次请求发送函数，成功时返回 HTTP 响应，失败时返回错误结果",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回最后一次失败结果或重试耗尽结果",
    )
    async def arequest_with_retry(
        config: NetConfig,
        send_once: Callable[[], Result[HttpResponse]],
    ) -> Result[HttpResponse]:
        attempts = config.max_retries + 1
        last_result: Optional[Result[HttpResponse]] = None

        for attempt in range(1, attempts + 1):
            result = await asyncio.to_thread(send_once)
            if result.ok:
                return result

            last_result = result
            should_retry = RetryPolicy.matches_result(result, config.retry_status_codes)
            if not should_retry:
                return result
            if attempt >= attempts:
                if config.max_retries <= 0:
                    return result
                return NetErrors.retry_exhausted(last_result)

            await asyncio.sleep(RetryPolicy.delay(attempt, config.retry_backoff_seconds))

        return NetErrors.retry_exhausted(last_result)

    @staticmethod
    @catch_result(
        handlers={
            HTTPError: NetErrors.handle_http_error,
            TimeoutError: NetErrors.handle_timeout,
            URLError: NetErrors.handle_url_error,
        },
        default=NetErrors.handle_request_failed,
    )
    @doc(
        summary="执行底层网络请求，并把底层异常映射为统一结果",
        parameters={
            "request": "已经装配完成的 urllib 请求对象",
            "timeout": "本次请求使用的超时时间",
            "target_url": "用于错误结果附带上下文的目标地址",
        },
        returns="成功时返回 HTTP 响应模型，异常时返回对应失败结果",
    )
    def perform_request(
        request: Request,
        *,
        timeout: float,
        target_url: str,
    ) -> Result[HttpResponse]:
        with urlopen(request, timeout=timeout) as response:
            raw_result = ResponseParser.from_raw(response)
            if not raw_result.ok:
                return Result.failure_from(
                    raw_result,
                    error=raw_result.error or "响应解析失败",
                    code=raw_result.code,
                    url=target_url,
                )
            return raw_result


@doc(summary="负责原始 HTTP 响应请求入口的无状态工具类")
class RawRequestExecutor:
    @staticmethod
    @doc(
        summary="执行一次同步 HTTP 请求",
        parameters={
            "config": "网络请求配置",
            "default_headers": "每次请求默认携带的请求头",
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "body": "直接写入请求体的原始文本或字节串",
            "body_encoding": "当请求体为字符串时使用的显式编码",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回网络、HTTP 或解析前错误",
    )
    def request(
        config: NetConfig,
        default_headers: Mapping[str, str],
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[str | bytes] = None,
        body_encoding: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        return BaseRequestExecutor.request_with_retry(
            config,
            lambda: RawRequestExecutor.send_once(
                config,
                default_headers,
                method,
                url,
                headers=headers,
                params=params,
                body=body,
                body_encoding=body_encoding,
                timeout=timeout,
            ),
        )

    @staticmethod
    @doc(
        summary="执行一次异步 HTTP 请求",
        parameters={
            "config": "网络请求配置",
            "default_headers": "每次请求默认携带的请求头",
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "body": "直接写入请求体的原始文本或字节串",
            "body_encoding": "当请求体为字符串时使用的显式编码",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回网络、HTTP 或解析前错误",
    )
    async def arequest(
        config: NetConfig,
        default_headers: Mapping[str, str],
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[str | bytes] = None,
        body_encoding: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        return await BaseRequestExecutor.arequest_with_retry(
            config,
            lambda: RawRequestExecutor.send_once(
                config,
                default_headers,
                method,
                url,
                headers=headers,
                params=params,
                body=body,
                body_encoding=body_encoding,
                timeout=timeout,
            ),
        )

    @staticmethod
    @doc(
        summary="执行单次原始 HTTP 请求的装配与发送流程",
        parameters={
            "config": "网络请求配置",
            "default_headers": "每次请求默认携带的请求头",
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "body": "直接写入请求体的原始文本或字节串",
            "body_encoding": "当请求体为字符串时使用的显式编码",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回请求装配、网络或 HTTP 错误",
    )
    def send_once(
        config: NetConfig,
        default_headers: Mapping[str, str],
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[str | bytes] = None,
        body_encoding: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        target_url = RequestBuilder.url(url, params=params)
        request_headers = RequestBuilder.headers(default_headers, headers)
        if isinstance(body, str):
            if body_encoding is None:
                return NetErrors.raw_body_encoding_missing(target_url)
            request_body = RequestBuilder.raw_body(body, encoding=body_encoding)
        else:
            request_body = body
        request = RequestBuilder.build(
            method,
            target_url,
            headers=request_headers,
            body=request_body,
        )
        request_timeout = float(timeout if timeout is not None else config.timeout)
        return BaseRequestExecutor.perform_request(
            request,
            timeout=request_timeout,
            target_url=target_url,
        )


@doc(summary="负责 JSON 请求入口的无状态工具类")
class JsonRequestExecutor:
    @staticmethod
    @doc(
        summary="执行一次同步 JSON HTTP 请求并返回原始响应",
        parameters={
            "config": "网络请求配置",
            "default_headers": "每次请求默认携带的请求头",
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "json_data": "按 JSON 序列化后写入请求体的数据",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回网络或请求 JSON 序列化错误",
    )
    def request(
        config: NetConfig,
        default_headers: Mapping[str, str],
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        json_data: JsonValue = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        return BaseRequestExecutor.request_with_retry(
            config,
            lambda: JsonRequestExecutor.send_once(
                config,
                default_headers,
                method,
                url,
                headers=headers,
                params=params,
                json_data=json_data,
                timeout=timeout,
            ),
        )

    @staticmethod
    @doc(
        summary="执行一次异步 JSON HTTP 请求并返回原始响应",
        parameters={
            "config": "网络请求配置",
            "default_headers": "每次请求默认携带的请求头",
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "json_data": "按 JSON 序列化后写入请求体的数据",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回网络或请求 JSON 序列化错误",
    )
    async def arequest(
        config: NetConfig,
        default_headers: Mapping[str, str],
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        json_data: JsonValue = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        return await BaseRequestExecutor.arequest_with_retry(
            config,
            lambda: JsonRequestExecutor.send_once(
                config,
                default_headers,
                method,
                url,
                headers=headers,
                params=params,
                json_data=json_data,
                timeout=timeout,
            ),
        )

    @staticmethod
    @doc(
        summary="执行单次 JSON HTTP 请求的装配与发送流程",
        parameters={
            "config": "网络请求配置",
            "default_headers": "每次请求默认携带的请求头",
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "json_data": "按 JSON 序列化后写入请求体的数据",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为 HTTP 响应，失败时返回请求装配、网络或 HTTP 错误",
    )
    def send_once(
        config: NetConfig,
        default_headers: Mapping[str, str],
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        json_data: JsonValue = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        target_url = RequestBuilder.url(url, params=params)
        payload_result = RequestBuilder.json_body(json_data)
        if not payload_result.ok:
            return NetErrors.request_json_build_failed(target_url, payload_result)

        request_headers = RequestBuilder.headers(default_headers, headers)
        if not RequestBuilder.has_header(request_headers, "Content-Type"):
            request_headers["Content-Type"] = "application/json"

        request = RequestBuilder.build(
            method,
            target_url,
            headers=request_headers,
            body=payload_result.unwrap(),
        )
        request_timeout = float(timeout if timeout is not None else config.timeout)
        return BaseRequestExecutor.perform_request(
            request,
            timeout=request_timeout,
            target_url=target_url,
        )


__all__ = ["BaseRequestExecutor", "RawRequestExecutor", "JsonRequestExecutor"]
