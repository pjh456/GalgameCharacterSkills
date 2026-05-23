from __future__ import annotations

import pytest

from gal_chara_skill.core.result import Result


def test_success_result() -> None:
    """验证 Result.success 会构造带值、无错误且可解包的成功结果"""
    result = Result.success(42, source="unit-test")

    assert result.ok is True
    assert result.value == 42
    assert result.error is None
    assert result.data == {"source": "unit-test"}
    assert result.unwrap() == 42


def test_failure_result() -> None:
    """验证 Result.failure 会构造带错误、附加数据与可选值的失败结果"""
    result = Result.failure("boom", retryable=True)
    value_result = Result.failure("boom", value=0)

    assert result.ok is False
    assert result.value is None
    assert result.error == "boom"
    assert result.data == {"retryable": True}
    assert value_result.value == 0


def test_failure_from_inherits_failure_context() -> None:
    """验证 failure_from 会继承失败结果的值、错误码与附加上下文"""
    upstream = Result.failure(
        "boom",
        code="fs_read_failed",
        value=7,
        path="a.txt",
    )

    result = Result.failure_from(upstream, stage="read")

    assert result.ok is False
    assert result.value == 7
    assert result.error == "boom"
    assert result.code == "fs_read_failed"
    assert result.cause is upstream
    assert result.data == {"path": "a.txt", "stage": "read"}


def test_failure_from_can_override_fields() -> None:
    """验证 failure_from 支持覆盖错误信息、错误码、值与同名附加字段"""
    upstream = Result.failure(
        "boom",
        code="fs_read_failed",
        value=7,
        path="a.txt",
        stage="raw",
    )

    result = Result.failure_from(
        upstream,
        error="读取日志失败",
        code="log_read_failed",
        value=None,
        stage="read",
    )

    assert result.ok is False
    assert result.value is None
    assert result.error == "读取日志失败"
    assert result.code == "log_read_failed"
    assert result.cause is upstream
    assert result.data == {"path": "a.txt", "stage": "read"}


def test_failure_from_rejects_success_result() -> None:
    """验证 failure_from 不接受成功结果作为来源"""
    with pytest.raises(ValueError):
        Result.failure_from(Result.success("ok"))


def test_unwrap() -> None:
    """验证 unwrap 会返回合法值，并在失败或缺值时抛出异常"""
    assert Result.success("ok").unwrap() == "ok"
    assert Result.success(0).unwrap() == 0
    assert Result.success(False).unwrap() is False

    with pytest.raises(RuntimeError):
        Result.failure("failed").unwrap()

    with pytest.raises(RuntimeError):
        Result.success().unwrap()


def test_expect() -> None:
    """验证 expect 会返回合法值，并在异常场景中保留调用上下文"""
    assert Result.success("ok").expect("outer message") == "ok"

    with pytest.raises(RuntimeError) as failure_info:
        Result.failure("inner error").expect("outer message")

    with pytest.raises(RuntimeError) as unknown_error_info:
        Result(ok=False, error=None).expect("outer message")

    with pytest.raises(RuntimeError):
        Result.success().expect("outer message")

    assert "outer message" in str(failure_info.value)
    assert "inner error" in str(failure_info.value)
    assert "outer message" in str(unknown_error_info.value)
