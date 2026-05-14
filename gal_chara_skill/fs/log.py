from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result
from .jsonl import JsonlIO
from .models import FilePath
from .text import TextIO


@doc(summary="负责日志文件文本与结构化内容保存的无状态 IO 工具")
class LogIO:
    @staticmethod
    @doc(
        summary="读取结构化日志文件中的全部记录",
        parameters={
            "path": "结构化日志文件路径",
            "encoding": "读取时使用的文本编码",
        },
        returns="成功时 value 为日志记录字典列表，失败时返回底层文件或解析错误",
    )
    def read(path: FilePath, encoding: str = "utf-8") -> Result[list[Any]]:
        return JsonlIO.read(path, encoding=encoding)

    @staticmethod
    @doc(
        summary="向结构化日志文件追加一条记录",
        parameters={
            "record": "需要写入结构化日志的一条记录",
            "path": "结构化日志文件路径",
            "encoding": "写入时使用的文本编码",
            "ensure_ascii": "写入 JSONL 时是否转义非 ASCII 字符",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def append_record(
        path: FilePath,
        record: Any,
        *,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        create_parent: bool = True,
    ) -> Result[None]:
        return JsonlIO.append(
            path,
            record,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            create_parent=create_parent,
        )

    @staticmethod
    @doc(
        summary="向文本日志文件追加单行内容",
        parameters={
            "path": "文本日志文件路径",
            "log": "需要写入的一行日志，不含换行符",
            "encoding": "写入时使用的文本编码",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def append_log(
        path: FilePath,
        log: str,
        *,
        encoding: str,
        create_parent: bool = True,
    ) -> Result[None]:
        return TextIO.append(
            path,
            f"{log}\n",
            encoding=encoding,
            create_parent=create_parent,
        )

    @staticmethod
    @doc(
        summary="用完整内容重写文本日志文件",
        parameters={
            "path": "文本日志文件路径",
            "logs": "需要完整写入的多行日志，不含换行符",
            "encoding": "写入时使用的文本编码",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def rewrite_log(
        path: FilePath,
        logs: Iterable[str],
        *,
        encoding: str,
        create_parent: bool = True,
    ) -> Result[None]:
        content = "".join(f"{log}\n" for log in logs)
        return TextIO.write(
            path,
            content,
            encoding=encoding,
            create_parent=create_parent,
        )


__all__ = ["LogIO"]
