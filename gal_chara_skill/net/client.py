from __future__ import annotations

from typing import Any, Mapping, Optional

import aiohttp
from numpydoc_decorator import doc

from ..conf.module.net import NetConfig
from ..core.result import Result
from .errors import NetErrors
from .executor import JsonRequestExecutor, RawRequestExecutor
from .models import HttpMethod, HttpResponse, JsonResponse, JsonValue
from .response import ResponseParser


@doc(
    summary="网络请求客户端门面，负责持有配置并转发执行",
    parameters={
        "config": "网络请求配置",
        "default_headers": "每次请求默认携带的请求头",
    },
)
class NetClient:
    def __init__(
        self,
        config: NetConfig,
        *,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.config = config
        self.default_headers = dict(default_headers or {})
        self._session: aiohttp.ClientSession | None = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    @doc(
        summary="发起一次同步 HTTP 请求",
        parameters={
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
        self,
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[str | bytes] = None,
        body_encoding: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        return RawRequestExecutor.request(
            self.config,
            self.default_headers,
            method,
            url,
            headers=headers,
            params=params,
            body=body,
            body_encoding=body_encoding,
            timeout=timeout,
        )

    @doc(
        summary="发起一次异步 HTTP 请求",
        parameters={
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
        self,
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[str | bytes] = None,
        body_encoding: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Result[HttpResponse]:
        return await RawRequestExecutor.arequest(
            self.config,
            self.default_headers,
            method,
            url,
            headers=headers,
            params=params,
            body=body,
            body_encoding=body_encoding,
            timeout=timeout,
            session=self._get_session(),
        )

    @doc(
        summary="发起一次同步 HTTP 请求并解析 JSON 响应体",
        parameters={
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "json_data": "按 JSON 序列化后写入请求体的数据",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为包含原始响应与解析结果的对象，失败时返回网络或 JSON 解析错误",
    )
    def request_json(
        self,
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        json_data: JsonValue = None,
        timeout: Optional[float] = None,
    ) -> Result[JsonResponse]:
        response_result = JsonRequestExecutor.request(
            self.config,
            self.default_headers,
            method,
            url,
            headers=headers,
            params=params,
            json_data=json_data,
            timeout=timeout,
        )
        if not response_result.ok:
            return NetErrors.json_request_failed(response_result)
        return ResponseParser.parse_json(response_result.unwrap())

    @doc(
        summary="发起一次异步 HTTP 请求并解析 JSON 响应体",
        parameters={
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "本次请求额外携带的请求头",
            "params": "追加到查询字符串中的参数",
            "json_data": "按 JSON 序列化后写入请求体的数据",
            "timeout": "本次请求覆盖默认配置的超时时间",
        },
        returns="成功时 value 为包含原始响应与解析结果的对象，失败时返回网络或 JSON 解析错误",
    )
    async def arequest_json(
        self,
        method: HttpMethod,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        json_data: JsonValue = None,
        timeout: Optional[float] = None,
    ) -> Result[JsonResponse]:
        response_result = await JsonRequestExecutor.arequest(
            self.config,
            self.default_headers,
            method,
            url,
            headers=headers,
            params=params,
            json_data=json_data,
            timeout=timeout,
            session=self._get_session(),
        )
        if not response_result.ok:
            return NetErrors.json_request_failed(response_result)
        return ResponseParser.parse_json(response_result.unwrap())

__all__ = ["NetClient"]
