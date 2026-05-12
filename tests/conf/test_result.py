from __future__ import annotations

import pytest

from gal_chara_skill.conf.result import Result


def test_success_result_ok() -> None:
    """验证 Result.success 会标记结果为成功"""
    result = Result.success(42)

    assert result.ok is True


def test_success_result_value() -> None:
    """验证 Result.success 会保存结果值"""
    result = Result.success(42)

    assert result.value == 42


def test_success_result_error() -> None:
    """验证 Result.success 默认无错误信息"""
    result = Result.success(42)

    assert result.error is None


def test_success_result_code() -> None:
    """验证 Result.success 默认无错误码"""
    result = Result.success(42)

    assert result.code is None


def test_success_result_data() -> None:
    """验证 Result.success 会保存附加数据"""
    result = Result.success(42, source="unit-test")

    assert result.data == {"source": "unit-test"}


def test_failure_result_ok() -> None:
    """验证 Result.failure 会标记结果为失败"""
    result = Result.failure("boom")

    assert result.ok is False


def test_failure_result_value() -> None:
    """验证 Result.failure 默认不携带结果值"""
    result = Result.failure("boom")

    assert result.value is None


def test_failure_result_error() -> None:
    """验证 Result.failure 会保存错误信息"""
    result = Result.failure("boom")

    assert result.error == "boom"


def test_failure_result_code() -> None:
    """验证 Result.failure 会保存错误码"""
    result = Result.failure("boom", code="E_BANG")

    assert result.code == "E_BANG"


def test_failure_result_data() -> None:
    """验证 Result.failure 会保存附加数据"""
    result = Result.failure("boom", retryable=True)

    assert result.data == {"retryable": True}


def test_failure_result_value_override() -> None:
    """验证 Result.failure 允许携带额外结果值"""
    result = Result.failure("boom", value=0)

    assert result.value == 0


def test_unwrap_success() -> None:
    """验证 unwrap 在成功结果上会返回保存的值"""
    result = Result.success("ok")

    assert result.unwrap() == "ok"


def test_unwrap_zero_value() -> None:
    """验证 unwrap 不会将 0 误判为缺失值"""
    result = Result.success(0)

    assert result.unwrap() == 0


def test_unwrap_false_value() -> None:
    """验证 unwrap 不会将 False 误判为缺失值"""
    result = Result.success(False)

    assert result.unwrap() is False


def test_unwrap_failure() -> None:
    """验证 unwrap 在失败结果上会抛出异常"""
    result = Result.failure("failed")

    with pytest.raises(RuntimeError, match="failed"):
        result.unwrap()


def test_unwrap_none() -> None:
    """验证 unwrap 在成功但值为 None 时会抛出异常"""
    result = Result.success()

    with pytest.raises(RuntimeError, match="值为 None"):
        result.unwrap()


def test_expect_success() -> None:
    """验证 expect 在成功结果上会返回保存的值"""
    result = Result.success("ok")

    assert result.expect("outer message") == "ok"


def test_expect_failure() -> None:
    """验证 expect 在失败结果上会拼接自定义错误前缀"""
    result = Result.failure("inner error")

    with pytest.raises(RuntimeError, match="outer message: inner error"):
        result.expect("outer message")


def test_expect_unknown_error() -> None:
    """验证 expect 在错误信息缺失时会使用未知错误提示"""
    result = Result(ok=False, error=None)

    with pytest.raises(RuntimeError, match="outer message: 未知错误"):
        result.expect("outer message")


def test_expect_none() -> None:
    """验证 expect 在成功但值为 None 时会说明缺失值"""
    result = Result.success()

    with pytest.raises(RuntimeError, match="outer message: 值为 None"):
        result.expect("outer message")
