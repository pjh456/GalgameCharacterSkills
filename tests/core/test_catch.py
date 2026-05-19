from __future__ import annotations

from gal_chara_skill.core.catch import catch_result


@catch_result(
    handlers={
        ValueError: lambda exc, bound: __import__("gal_chara_skill.core.result", fromlist=["Result"]).Result.failure(
            "bad value",
            code="value_error",
            argument=bound.arguments["name"],
            exception=str(exc),
        )
    },
    default=lambda exc, bound: __import__("gal_chara_skill.core.result", fromlist=["Result"]).Result.failure(
        "unknown",
        code="unknown_error",
        argument=bound.arguments["name"],
        exception=str(exc),
    ),
)
def load_name(name: str) -> str:
    if name == "value":
        raise ValueError("boom")
    if name == "runtime":
        raise RuntimeError("oops")
    return name.upper()


def test_catch_result_success() -> None:
    """验证 catch_result 会把正常返回值包装成成功结果"""
    result = load_name("alice")

    assert result.ok is True
    assert result.unwrap() == "ALICE"


def test_catch_result_uses_specific_handler() -> None:
    """验证 catch_result 会优先命中特定异常处理函数"""
    result = load_name("value")

    assert result.ok is False
    assert result.code == "value_error"
    assert result.data["argument"] == "value"


def test_catch_result_uses_default_handler() -> None:
    """验证 catch_result 会在未命中特定异常时使用兜底处理函数"""
    result = load_name("runtime")

    assert result.ok is False
    assert result.code == "unknown_error"
    assert result.data["argument"] == "runtime"
