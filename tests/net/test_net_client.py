from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.net.client import NetClient
from gal_chara_skill.net.models import HttpResponse


class FakeHeaders:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def items(self) -> list[tuple[str, str]]:
        return list(self._values.items())


class FakeResponse:
    def __init__(
        self,
        *,
        url: str,
        status: int = 200,
        headers: Optional[dict[str, str]] = None,
        body: bytes = b"",
    ) -> None:
        self.status = status
        self.headers = FakeHeaders(headers or {})
        self._body = body
        self._url = url

    def read(self) -> bytes:
        return self._body

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        del exc_type, exc, tb
        return False


@dataclass
class Capture:
    url: str
    method: str
    headers: dict[str, str]
    data: Optional[bytes]


@dataclass
class UrlopenStub:
    responses: list[object]
    captures: list[Capture] = field(default_factory=list)

    def __call__(self, request: Request, timeout: float) -> object:
        del timeout
        self.captures.append(
            Capture(
                url=request.full_url,
                method=request.get_method(),
                headers=dict(request.header_items()),
                data=request.data,
            )
        )

        outcome = self.responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def build_http_error(
    *,
    url: str,
    status: int,
    body: bytes = b"",
    headers: Optional[dict[str, str]] = None,
) -> HTTPError:
    return HTTPError(
        url=url,
        code=status,
        msg="HTTP error",
        hdrs=FakeHeaders(headers or {}),
        fp=BytesIO(body),
    )


def test_request_success_with_json_and_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request 会拼接查询参数、合并请求头并写入原始请求体"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api?q=alice",
                headers={"Content-Type": "application/json"},
                body=b'{"ok": true}',
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(
        NetConfig(max_retries=0),
        default_headers={"Authorization": "Bearer token"},
    )

    result = client.request(
        "POST",
        "https://example.com/api",
        params={"q": "alice"},
        headers={"X-Test": "yes"},
        body='{"name": "alice"}',
        body_encoding="utf-8",
    )

    assert result.ok is True
    response = result.unwrap()
    assert response.status_code == 200
    assert response.json().unwrap() == {"ok": True}
    assert stub.captures[0].url == "https://example.com/api?q=alice"
    assert stub.captures[0].method == "POST"
    assert stub.captures[0].headers["Authorization"] == "Bearer token"
    assert stub.captures[0].headers["X-test"] == "yes"
    assert stub.captures[0].data == b'{"name": "alice"}'


def test_request_http_error_preserves_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request 在收到 HTTP 错误时返回失败结果并保留原始响应"""
    stub = UrlopenStub(
        [
            build_http_error(
                url="https://example.com/api",
                status=429,
                body=b'{"error":"busy"}',
                headers={"Content-Type": "application/json"},
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = client.request("GET", "https://example.com/api")

    assert result.ok is False
    assert result.data["status_code"] == 429
    assert isinstance(result.value, HttpResponse)
    assert result.value.text == '{"error":"busy"}'


def test_request_http_error_invalid_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 request 在无法从 HTTPError 恢复响应时返回解析失败结果"""
    broken_error = HTTPError(
        url="https://example.com/api",
        code=503,
        msg="HTTP error",
        hdrs=None,
        fp=None,
    )
    monkeypatch.setattr(
        "gal_chara_skill.net.executor.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(broken_error),
    )
    client = NetClient(NetConfig(max_retries=0))

    result = client.request("GET", "https://example.com/api")

    assert result.ok is False
    assert "exception" in result.data


def test_request_retries_connect_failure_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request 会对连接失败执行重试并在成功后停止"""
    stub = UrlopenStub(
        [
            URLError("temporary failure"),
            FakeResponse(url="https://example.com/api", body=b"ok"),
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    monkeypatch.setattr("gal_chara_skill.net.executor.time.sleep", lambda _: None)
    client = NetClient(NetConfig(max_retries=1, retry_backoff_seconds=0.0))

    result = client.request("GET", "https://example.com/api")

    assert result.ok is True
    assert result.unwrap().text == "ok"
    assert len(stub.captures) == 2


def test_request_retry_exhausted_returns_explicit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证可重试错误在耗尽重试次数后返回专用错误码"""
    stub = UrlopenStub(
        [
            URLError("temporary failure"),
            URLError("temporary failure"),
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    monkeypatch.setattr("gal_chara_skill.net.executor.time.sleep", lambda _: None)
    client = NetClient(NetConfig(max_retries=1, retry_backoff_seconds=0.0))

    result = client.request("GET", "https://example.com/api")

    assert result.ok is False
    assert result.data["url"] == "https://example.com/api"
    assert len(stub.captures) == 2


def test_request_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request 会把超时异常转换为统一失败结果"""
    monkeypatch.setattr(
        "gal_chara_skill.net.executor.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(TimeoutError("slow")),
    )
    client = NetClient(NetConfig(max_retries=0))

    result = client.request("GET", "https://example.com/api")

    assert result.ok is False
    assert result.data["url"] == "https://example.com/api"


def test_request_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 request 会把未分类异常转换为统一请求失败结果"""
    monkeypatch.setattr(
        "gal_chara_skill.net.executor.urlopen",
        lambda request, timeout: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    client = NetClient(NetConfig(max_retries=0))

    result = client.request("GET", "https://example.com/api")

    assert result.ok is False
    assert result.data["url"] == "https://example.com/api"


def test_request_json_parse_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request_json 在响应体不是合法 JSON 时返回失败结果"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api",
                headers={"Content-Type": "application/json"},
                body=b"{broken}",
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = client.request_json("GET", "https://example.com/api")

    assert result.ok is False
    assert result.value is not None
    assert result.value.response.status_code == 200


def test_request_json_decode_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request_json 在响应体编码不匹配时返回解码失败结果"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api",
                headers={"Content-Type": "application/json; charset=ascii"},
                body=b'{"name":"Alice","note":"\xc3\xa9"}',
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = client.request_json("GET", "https://example.com/api")

    assert result.ok is False
    assert result.value is not None
    assert result.value.response.status_code == 200


def test_request_json_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 request_json 在 HTTP 失败时会保留 JSON 响应占位值"""
    stub = UrlopenStub(
        [
            build_http_error(
                url="https://example.com/api",
                status=429,
                body=b'{"error":"busy"}',
                headers={"Content-Type": "application/json"},
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = client.request_json("GET", "https://example.com/api")

    assert result.ok is False
    assert result.value is not None
    assert result.value.response.status_code == 429
    assert result.value.data is None


def test_request_json_build_failure() -> None:
    """验证 request_json 在请求体不可序列化时返回请求阶段失败结果"""
    client = NetClient(NetConfig(max_retries=0))

    result = client.request_json(
        "POST",
        "https://example.com/api",
        json_data={"items": {1, 2, 3}},
    )

    assert result.ok is False
    assert result.data["url"] == "https://example.com/api"
    assert result.value is None


def test_request_string_body_requires_explicit_encoding() -> None:
    """验证 request 在字符串请求体未声明编码时返回失败结果"""
    client = NetClient(NetConfig(max_retries=0))

    result = client.request(
        "POST",
        "https://example.com/api",
        body="hello",
    )

    assert result.ok is False


def test_request_json_sets_content_type_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 request_json 在未显式提供时会自动补上 JSON Content-Type"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api",
                headers={"Content-Type": "application/json"},
                body=b'{"ok": true}',
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = client.request_json(
        "POST",
        "https://example.com/api",
        json_data={"ok": True},
    )

    assert result.ok is True
    assert stub.captures[0].headers["Content-type"] == "application/json"
    assert stub.captures[0].data == b'{"ok": true}'


def test_request_json_preserves_content_type_case_insensitively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 request_json 不会因请求头大小写不同而重复补 Content-Type"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api",
                headers={"Content-Type": "application/json"},
                body=b'{"ok": true}',
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(
        NetConfig(max_retries=0),
        default_headers={"content-type": "application/problem+json"},
    )

    result = client.request_json(
        "POST",
        "https://example.com/api",
        headers={"CONTENT-TYPE": "application/json; charset=utf-8"},
        json_data={"ok": True},
    )

    assert result.ok is True
    assert stub.captures[0].headers["Content-type"] == "application/json; charset=utf-8"
    assert len(stub.captures[0].headers) == 1


def test_request_merges_query_params_without_breaking_fragment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 request 会保留原始 query 与 fragment 并追加新参数"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api?existing=1&q=alice#frag",
                body=b"ok",
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = client.request(
        "GET",
        "https://example.com/api?existing=1#frag",
        params={"q": "alice"},
    )

    assert result.ok is True
    assert stub.captures[0].url == "https://example.com/api?existing=1&q=alice#frag"


def test_arequest_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 arequest 会复用同步请求逻辑并返回成功结果"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api",
                headers={"Content-Type": "application/json"},
                body=b'{"ok": true}',
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = asyncio.run(client.arequest("GET", "https://example.com/api"))

    assert result.ok is True
    assert result.unwrap().json().unwrap() == {"ok": True}


def test_arequest_retry_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 arequest 在可重试失败耗尽后返回专用错误码"""
    stub = UrlopenStub(
        [
            URLError("temporary failure"),
            URLError("temporary failure"),
        ]
    )

    async def skip_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    monkeypatch.setattr("gal_chara_skill.net.executor.asyncio.sleep", skip_sleep)
    client = NetClient(NetConfig(max_retries=1, retry_backoff_seconds=0.0))

    result = asyncio.run(client.arequest("GET", "https://example.com/api"))

    assert result.ok is False
    assert result.data["url"] == "https://example.com/api"
    assert len(stub.captures) == 2


def test_arequest_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 arequest_json 会返回解析后的 JSON 数据"""
    stub = UrlopenStub(
        [
            FakeResponse(
                url="https://example.com/api",
                headers={"Content-Type": "application/json"},
                body=b'{"ok": true}',
            )
        ]
    )
    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", stub)
    client = NetClient(NetConfig(max_retries=0))

    result = asyncio.run(client.arequest_json("GET", "https://example.com/api"))

    assert result.ok is True
    assert result.unwrap().data == {"ok": True}


def test_arequest_json_build_failure() -> None:
    """验证 arequest_json 在请求体不可序列化时返回请求阶段失败结果"""
    client = NetClient(NetConfig(max_retries=0))

    result = asyncio.run(
        client.arequest_json(
            "POST",
            "https://example.com/api",
            json_data={"items": {1, 2, 3}},
        )
    )

    assert result.ok is False
    assert result.data["url"] == "https://example.com/api"
    assert result.value is None


def test_request_does_not_swallow_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 request 不会把中断类异常包装成业务失败结果"""
    stub = UrlopenStub([])

    def raise_interrupt(request: Request, timeout: float) -> object:
        del request, timeout
        raise KeyboardInterrupt("stop")

    monkeypatch.setattr("gal_chara_skill.net.executor.urlopen", raise_interrupt)
    client = NetClient(NetConfig(max_retries=0))

    with pytest.raises(KeyboardInterrupt):
        client.request("GET", "https://example.com/api")
