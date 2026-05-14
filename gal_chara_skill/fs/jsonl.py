from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from numpydoc_decorator import doc

from ..core.result import Result
from .models import FilePath
from .path import resolve
from .text import TextIO


@doc(summary="负责 JSONL 文件读写与追加的无状态 IO 工具")
class JsonlIO:
    @staticmethod
    @doc(
        summary="读取 JSONL 文件并解析为 Python 对象列表",
        parameters={
            "path": "目标文件路径",
            "encoding": "读取时使用的文本编码",
        },
        returns="表示执行结果的显式结果对象",
    )
    def read(path: FilePath, encoding: str = "utf-8") -> Result[list[Any]]:
        file_path = resolve(path)

        if not file_path.exists():
            return Result.failure("文件不存在", code="fs_not_found", path=str(file_path))
        if not file_path.is_file():
            return Result.failure("目标路径不是文件", code="fs_not_file", path=str(file_path))

        records: list[Any] = []

        try:
            with file_path.open("r", encoding=encoding) as fh:
                for line_number, raw_line in enumerate(fh, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue

                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        return Result.failure(
                            "JSONL 解析失败",
                            code="fs_parse_failed",
                            path=str(file_path),
                            line=line_number,
                            column=exc.colno,
                            exception=str(exc),
                        )

            return Result.success(records)
        except Exception as exc:
            return Result.failure(
                "读取 JSONL 文件失败",
                code="fs_read_failed",
                path=str(file_path),
                exception=str(exc),
            )

    @staticmethod
    @doc(
        summary="将多个 Python 对象写入 JSONL 文件",
        parameters={
            "path": "目标文件路径",
            "records": "需要逐行写入的 Python 对象",
            "encoding": "写入时使用的文本编码",
            "ensure_ascii": "是否将非 ASCII 字符转义",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def write(
        path: FilePath,
        records: Iterable[Any],
        *,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        create_parent: bool = True,
    ) -> Result[None]:
        lines_result = JsonlIO._serialize_lines(records, ensure_ascii=ensure_ascii)
        if not lines_result.ok:
            return Result.failure(
                lines_result.error or "JSONL 序列化失败",
                code=lines_result.code,
                **lines_result.data,
            )

        content = "".join(f"{line}\n" for line in lines_result.unwrap())

        return TextIO.write(
            path,
            content,
            encoding=encoding,
            create_parent=create_parent,
        )

    @staticmethod
    @doc(
        summary="向 JSONL 文件追加一个 Python 对象",
        parameters={
            "path": "目标文件路径",
            "record": "需要追加写入的 Python 对象",
            "encoding": "写入时使用的文本编码",
            "ensure_ascii": "是否将非 ASCII 字符转义",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def append(
        path: FilePath,
        record: Any,
        *,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        create_parent: bool = True,
    ) -> Result[None]:
        line_result = JsonlIO._serialize_record(record, ensure_ascii=ensure_ascii)
        if not line_result.ok:
            return Result.failure(
                line_result.error or "JSONL 序列化失败",
                code=line_result.code,
                **line_result.data,
            )

        return TextIO.append(
            path,
            f"{line_result.unwrap()}\n",
            encoding=encoding,
            create_parent=create_parent,
        )

    @staticmethod
    @doc(
        summary="将多个 Python 对象序列化为 JSONL 行",
        parameters={
            "records": "需要序列化的 Python 对象",
            "ensure_ascii": "是否将非 ASCII 字符转义",
        },
        returns="成功时 value 为不带换行符的 JSON 字符串列表，失败时返回序列化错误",
    )
    def _serialize_lines(records: Iterable[Any], *, ensure_ascii: bool) -> Result[list[str]]:
        lines: list[str] = []

        for index, record in enumerate(records):
            line_result = JsonlIO._serialize_record(record, ensure_ascii=ensure_ascii)
            if not line_result.ok:
                data = dict(line_result.data)
                data["index"] = index
                return Result.failure(
                    line_result.error or "JSONL 序列化失败",
                    code=line_result.code,
                    **data,
                )
            lines.append(line_result.unwrap())

        return Result.success(lines)

    @staticmethod
    @doc(
        summary="将单个 Python 对象序列化为 JSONL 行",
        parameters={
            "record": "需要序列化的 Python 对象",
            "ensure_ascii": "是否将非 ASCII 字符转义",
        },
        returns="成功时 value 为不带换行符的 JSON 字符串，失败时返回序列化错误",
    )
    def _serialize_record(record: Any, *, ensure_ascii: bool) -> Result[str]:
        try:
            return Result.success(json.dumps(record, ensure_ascii=ensure_ascii))
        except (TypeError, ValueError) as exc:
            return Result.failure(
                "JSONL 序列化失败",
                code="fs_parse_failed",
                exception=str(exc),
            )


__all__ = ["JsonlIO"]
