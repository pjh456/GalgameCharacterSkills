from __future__ import annotations

from gal_chara_skill.net.models import HttpResponse
from gal_chara_skill.net.response import RawHeadersLike, ResponseParser


def test_http_response_text_and_json() -> None:
    """验证 HttpResponse 可以按声明编码读取文本并解析 JSON"""
    response = HttpResponse(
        status_code=200,
        url="https://example.com/api",
        headers={"Content-Type": "application/json; charset=utf-8"},
        body=b'{"ok": true}',
    )

    json_result = response.json()

    assert response.encoding == "utf-8"
    assert response.text == '{"ok": true}'
    assert json_result.ok is True
    assert json_result.unwrap() == {"ok": True}


def test_http_response_json_parse_failure() -> None:
    """验证 HttpResponse 在响应体不是合法 JSON 时返回失败结果"""
    response = HttpResponse(
        status_code=200,
        url="https://example.com/api",
        headers={"Content-Type": "application/json"},
        body=b"{broken}",
    )

    result = response.json()

    assert result.ok is False
    assert result.data["status_code"] == 200


def test_http_response_decode_failure() -> None:
    """验证 HttpResponse 在声明错误编码时返回解码失败结果"""
    response = HttpResponse(
        status_code=200,
        url="https://example.com/api",
        headers={"Content-Type": "application/json; charset=ascii"},
        body=b'{"name":"Alice","city":"Montr\xc3\xa9al"}',
    )

    result = response.json()

    assert result.ok is False
    assert result.data["status_code"] == 200


def test_http_response_get_header_case_insensitive() -> None:
    """验证读取响应头时不区分大小写"""
    response = HttpResponse(
        status_code=200,
        url="https://example.com/api",
        headers={"Content-Type": "text/plain"},
        body=b"ok",
    )

    assert response.get_header("content-type") == "text/plain"
    assert response.get_header("Content-Type") == "text/plain"


class BrokenHeaders:
    def items(self) -> list[tuple[str, str]]:
        raise ValueError("broken headers")


class BrokenResponse:
    status: int
    headers: RawHeadersLike

    def __init__(self) -> None:
        self.status = 200
        self.headers = BrokenHeaders()

    def geturl(self) -> str:
        return "https://example.com/api"

    def read(self) -> bytes:
        return b"ok"


def test_from_raw_failure() -> None:
    """验证 ResponseParser.from_raw 会把坏响应对象转换为失败结果"""
    result = ResponseParser.from_raw(BrokenResponse())

    assert result.ok is False


def test_json_value_none() -> None:
    """验证 ResponseParser.json_value 在没有原始响应时返回 None"""
    assert ResponseParser.json_value(None) is None
