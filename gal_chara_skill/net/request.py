from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request

from numpydoc_decorator import doc

from ..core.catch import catch_result
from .errors import NetErrors
from .models import HttpMethod, JsonValue


@doc(summary="负责 HTTP 请求装配的无状态工具类")
class RequestBuilder:
    @staticmethod
    @doc(
        summary="构造 JSON 请求体字节串",
        parameters={
            "json_data": "需要按 JSON 序列化后写入请求体的数据",
        },
        returns="成功时 value 为 JSON 请求体字节串，失败时返回 JSON 序列化错误",
    )
    @catch_result(
        handlers={
            (TypeError, ValueError): NetErrors.handle_request_json_parse_failed,
        }
    )
    def json_body(json_data: JsonValue) -> bytes:
        return json.dumps(json_data, ensure_ascii=False).encode("utf-8")

    @staticmethod
    @doc(
        summary="构造原始请求体字节串",
        parameters={
            "body": "直接写入请求体的原始文本或字节串",
            "encoding": "当请求体为字符串时使用的显式编码",
        },
        returns="编码后的原始请求体字节串",
    )
    def raw_body(body: str | bytes, *, encoding: str) -> bytes:
        if isinstance(body, str):
            return body.encode(encoding)
        return body

    @staticmethod
    @doc(
        summary="拼接带查询参数的请求地址",
        parameters={
            "url": "原始请求地址",
            "params": "要追加到查询字符串中的参数",
        },
        returns="拼接后的完整请求地址",
    )
    def url(url: str, *, params: Optional[Mapping[str, Any]]) -> str:
        if not params:
            return url

        url_parts = urlsplit(url)
        query_pairs: list[tuple[str, Any]] = list(
            parse_qsl(url_parts.query, keep_blank_values=True)
        )
        query_pairs.extend(RequestBuilder.query_items(params))
        query = urlencode(query_pairs, doseq=True)
        return urlunsplit(
            (
                url_parts.scheme,
                url_parts.netloc,
                url_parts.path,
                query,
                url_parts.fragment,
            )
        )

    @staticmethod
    @doc(
        summary="把查询参数映射展开为 urlencode 可接受的键值对序列",
        parameters={"params": "要追加到查询字符串中的参数"},
        returns="展开后的查询参数键值对序列",
    )
    def query_items(params: Mapping[str, Any]) -> list[tuple[str, Any]]:
        items: list[tuple[str, Any]] = []
        for key, value in params.items():
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                items.append((key, list(value)))
                continue
            items.append((key, value))
        return items

    @staticmethod
    @doc(
        summary="合并默认请求头与本次调用请求头",
        parameters={
            "default_headers": "客户端级默认请求头",
            "headers": "本次请求额外携带的请求头",
        },
        returns="合并后的请求头字典",
    )
    def headers(
        default_headers: Mapping[str, str],
        headers: Optional[Mapping[str, str]],
    ) -> dict[str, str]:
        merged: dict[str, str] = {}
        index: dict[str, str] = {}

        for source in (default_headers, headers or {}):
            for key, value in source.items():
                lowered = key.lower()
                previous = index.get(lowered)
                if previous is not None and previous != key:
                    del merged[previous]
                merged[key] = value
                index[lowered] = key
        return merged

    @staticmethod
    @doc(
        summary="判断请求头中是否已经存在指定名称",
        parameters={
            "headers": "请求头字典",
            "name": "要检查的请求头名称",
        },
        returns="请求头是否存在，不区分大小写",
    )
    def has_header(headers: Mapping[str, str], name: str) -> bool:
        lowered = name.lower()
        return any(key.lower() == lowered for key in headers)

    @staticmethod
    @doc(
        summary="构造 urllib 使用的请求对象",
        parameters={
            "method": "HTTP 方法",
            "url": "请求地址",
            "headers": "请求头字典",
            "body": "请求体字节串",
        },
        returns="可直接发送的请求对象",
    )
    def build(
        method: HttpMethod,
        url: str,
        *,
        headers: Mapping[str, str],
        body: Optional[bytes],
    ) -> Request:
        return Request(
            url=url,
            data=body,
            headers=dict(headers),
            method=method,
        )


__all__ = ["RequestBuilder"]
