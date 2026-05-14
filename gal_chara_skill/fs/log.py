from __future__ import annotations

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
        summary="同时向文本日志与结构化日志追加一条记录",
        parameters={
            "text_path": "文本日志文件路径",
            "structured_path": "结构化日志文件路径",
            "line": "需要写入文本日志的一行内容，不含换行符",
            "record": "需要写入结构化日志的一条记录",
            "encoding": "写入时使用的文本编码",
            "ensure_ascii": "写入 JSONL 时是否转义非 ASCII 字符",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def append(
        text_path: FilePath,
        structured_path: FilePath,
        line: str,
        record: Any,
        *,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        create_parent: bool = True,
    ) -> Result[None]:
        text_result = LogIO._append_text_line(
            text_path,
            line,
            encoding=encoding,
            create_parent=create_parent,
        )
        if not text_result.ok:
            return text_result

        structured_result = LogIO._append_structured_record(
            structured_path,
            record,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            create_parent=create_parent,
        )
        if not structured_result.ok:
            return structured_result

        return Result.success()

    @staticmethod
    @doc(
        summary="向文本日志文件追加单行内容",
        parameters={
            "path": "文本日志文件路径",
            "line": "需要写入的一行内容，不含换行符",
            "encoding": "写入时使用的文本编码",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def _append_text_line(
        path: FilePath,
        line: str,
        *,
        encoding: str,
        create_parent: bool,
    ) -> Result[None]:
        return TextIO.append(
            path,
            f"{line}\n",
            encoding=encoding,
            create_parent=create_parent,
        )

    @staticmethod
    @doc(
        summary="向结构化日志文件追加单条 JSONL 记录",
        parameters={
            "path": "结构化日志文件路径",
            "record": "需要写入的一条记录",
            "encoding": "写入时使用的文本编码",
            "ensure_ascii": "是否转义非 ASCII 字符",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def _append_structured_record(
        path: FilePath,
        record: Any,
        *,
        encoding: str,
        ensure_ascii: bool,
        create_parent: bool,
    ) -> Result[None]:
        return JsonlIO.append(
            path,
            record,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            create_parent=create_parent,
        )


__all__ = ["LogIO"]
