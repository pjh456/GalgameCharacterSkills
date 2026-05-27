from __future__ import annotations

from inspect import BoundArguments
import json
from pathlib import Path
from typing import Any, Callable

from numpydoc_decorator import doc

from ..core.result import Result


def _path_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


@doc(summary="负责构造 fs 模块统一错误结果的无状态工具类")
class FsErrors:
    @staticmethod
    @doc(
        summary="返回一个 catch_result handler，按错误码和消息构造 I/O 失败结果",
        parameters={
            "code": "错误码",
            "message": "错误消息",
        },
        returns="可传入 catch_result 的 handler 函数",
    )
    def io_fail(
        code: str,
        message: str,
    ) -> Callable[[BaseException, BoundArguments], Result[Any]]:
        def handler(exc: BaseException, bound: BoundArguments) -> Result[Any]:
            path = bound.arguments.get("path")
            return Result.failure(
                message,
                code=code,
                path=_path_str(path),
                exception=str(exc),
            )
        return handler

    @staticmethod
    @doc(
        summary="catch_result handler: JSON 解析失败，附带行列号",
        parameters={
            "exc": "JSONDecodeError 异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示 JSON 解析失败的结果",
    )
    def handle_json_parse_fail(exc: BaseException, bound: BoundArguments) -> Result[Any]:
        path = bound.arguments.get("path")
        lineno = exc.lineno if isinstance(exc, json.JSONDecodeError) and hasattr(exc, "lineno") else None
        colno = exc.colno if isinstance(exc, json.JSONDecodeError) and hasattr(exc, "colno") else None
        return Result.failure(
            "JSON 解析失败",
            code="fs_parse_failed",
            path=_path_str(path),
            line=lineno,
            column=colno,
            exception=str(exc),
        )

    @staticmethod
    @doc(
        summary="catch_result handler: YAML 解析失败",
        parameters={
            "exc": "YAMLError 异常",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示 YAML 解析失败的结果",
    )
    def handle_yaml_parse_fail(exc: BaseException, bound: BoundArguments) -> Result[Any]:
        path = bound.arguments.get("path")
        return Result.failure(
            "YAML 解析失败",
            code="fs_parse_failed",
            path=_path_str(path),
            exception=str(exc),
        )

    @staticmethod
    @doc(
        summary="catch_result handler: 父目录创建失败，path 取 parent",
        parameters={
            "exc": "异常对象",
            "bound": "装饰器绑定的调用参数",
        },
        returns="表示父目录创建失败的结果",
    )
    def handle_ensure_parent_fail(exc: BaseException, bound: BoundArguments) -> Result[Any]:
        path = bound.arguments.get("path")
        parent = str(Path(path).parent) if path is not None else ""
        return Result.failure(
            "创建父目录失败",
            code="fs_write_failed",
            path=parent,
            exception=str(exc),
        )


__all__ = ["FsErrors"]
