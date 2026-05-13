from __future__ import annotations

import json
from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result
from .models import FilePath
from .path import resolve
from .text import write as write_text


@doc(summary="负责 JSON 文件读写的无状态 IO 工具")
class JsonIO:
    @staticmethod
    @doc(
        summary="读取 JSON 文件并解析为 Python 对象",
        parameters={
            "path": "目标文件路径",
            "encoding": "读取时使用的文本编码",
        },
        returns="表示执行结果的显式结果对象",
    )
    def read(path: FilePath, encoding: str = "utf-8") -> Result[Any]:
        file_path = resolve(path)

        if not file_path.exists():
            return Result.failure("文件不存在", code="fs_not_found", path=str(file_path))
        if not file_path.is_file():
            return Result.failure("目标路径不是文件", code="fs_not_file", path=str(file_path))

        try:
            with file_path.open("r", encoding=encoding) as fh:
                return Result.success(json.load(fh))
        except json.JSONDecodeError as exc:
            return Result.failure(
                "JSON 解析失败",
                code="fs_parse_failed",
                path=str(file_path),
                line=exc.lineno,
                column=exc.colno,
                exception=str(exc),
            )
        except Exception as exc:
            return Result.failure(
                "读取 JSON 文件失败",
                code="fs_read_failed",
                path=str(file_path),
                exception=str(exc),
            )

    @staticmethod
    @doc(
        summary="将 Python 对象写入 JSON 文件",
        parameters={
            "path": "目标文件路径",
            "data": "需要写入的 Python 对象",
            "encoding": "写入时使用的文本编码",
            "indent": "JSON 缩进空格数",
            "ensure_ascii": "是否将非 ASCII 字符转义",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def write(
        path: FilePath,
        data: Any,
        *,
        encoding: str = "utf-8",
        indent: int = 2,
        ensure_ascii: bool = False,
        create_parent: bool = True,
    ) -> Result[None]:
        try:
            text = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        except (TypeError, ValueError) as exc:
            return Result.failure(
                "JSON 序列化失败",
                code="fs_parse_failed",
                exception=str(exc),
            )

        return write_text(
            path,
            f"{text}\n",
            encoding=encoding,
            create_parent=create_parent,
        )


__all__ = ["JsonIO"]
