from __future__ import annotations

from gal_chara_skill.core.result import Result
from gal_chara_skill.net.retry import RetryPolicy


def test_matches_status() -> None:
    """验证状态码重试判定遵循配置集合"""
    retry_status_codes = (408, 429, 500)

    assert RetryPolicy.matches_status(429, retry_status_codes) is True
    assert RetryPolicy.matches_status(404, retry_status_codes) is False


def test_matches_result() -> None:
    """验证失败结果的重试判定会区分超时、连接失败与 HTTP 状态码"""
    retry_status_codes = (408, 429, 500)

    success_result = Result.success("ok")
    timeout_result = Result.failure("timeout", code="net_timeout")
    connect_result = Result.failure("connect", code="net_connect_failed")
    retryable_http_result = Result.failure(
        "http",
        code="net_http_error",
        status_code=429,
    )
    malformed_http_result = Result.failure(
        "http",
        code="net_http_error",
        status_code="429",
    )
    non_retryable_http_result = Result.failure(
        "http",
        code="net_http_error",
        status_code=404,
    )
    other_result = Result.failure("bad", code="net_parse_failed")

    assert RetryPolicy.matches_result(success_result, retry_status_codes) is False
    assert RetryPolicy.matches_result(timeout_result, retry_status_codes) is True
    assert RetryPolicy.matches_result(connect_result, retry_status_codes) is True
    assert RetryPolicy.matches_result(retryable_http_result, retry_status_codes) is True
    assert RetryPolicy.matches_result(malformed_http_result, retry_status_codes) is False
    assert RetryPolicy.matches_result(non_retryable_http_result, retry_status_codes) is False
    assert RetryPolicy.matches_result(other_result, retry_status_codes) is False


def test_delay() -> None:
    """验证重试等待时间按指数退避增长"""
    assert RetryPolicy.delay(0, 0.5) == 0.0
    assert RetryPolicy.delay(1, 0.5) == 0.5
    assert RetryPolicy.delay(2, 0.5) == 1.0
    assert RetryPolicy.delay(3, 0.5) == 2.0
