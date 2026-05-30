from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Mapping, Optional, TypeAlias

from numpydoc_decorator import doc

from ..core.catch import catch_result
from .errors import NetErrors

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
JsonPrimitive: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


@doc(
    summary="描述一次 HTTP 响应",
    parameters={
        "status_code": "HTTP 状态码",
        "url": "最终请求到的 URL",
        "headers": "响应头键值对",
        "body": "响应体原始字节串",
    },
)
@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    url: str
    headers: Mapping[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode(self.encoding)

    @property
    def encoding(self) -> str:
        content_type = self.get_header("content-type")
        if not content_type:
            return "utf-8"

        for part in content_type.split(";"):
            segment = part.strip()
            if segment.lower().startswith("charset="):
                charset = segment.split("=", 1)[1].strip()
                if charset:
                    return charset

        return "utf-8"

    @doc(
        summary="读取指定响应头",
        parameters={"name": "响应头名称"},
        returns="响应头值，不存在时返回 None",
    )
    def get_header(self, name: str) -> Optional[str]:
        lowered = name.lower()
        for key, value in self.headers.items():
            if key.lower() == lowered:
                return value
        return None

    @doc(
        summary="把响应体解析为 JSON 数据",
        returns="成功时 value 为解析后的 Python 对象，失败时返回解析错误",
    )
    @catch_result(
        handlers={
            (LookupError, UnicodeDecodeError): NetErrors.handle_response_decode_failed,
            json.JSONDecodeError: NetErrors.handle_response_json_parse_failed,
        }
    )
    def json(self) -> JsonValue:
        return json.loads(self.text)


@doc(
    summary="描述一次成功解析 JSON 的 HTTP 响应",
    parameters={
        "response": "原始 HTTP 响应",
        "data": "解析后的 JSON 数据",
    },
)
@dataclass(frozen=True)
class JsonResponse:
    response: HttpResponse
    data: JsonValue


__all__ = [
    "HttpMethod",
    "JsonPrimitive",
    "JsonValue",
    "HttpResponse",
    "JsonResponse",
]
