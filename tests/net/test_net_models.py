from __future__ import annotations

from gal_chara_skill.net.models import HttpResponse


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
    assert result.code == "net_parse_failed"
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
    assert result.code == "net_decode_failed"
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
