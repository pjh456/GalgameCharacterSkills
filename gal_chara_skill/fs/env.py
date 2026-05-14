from __future__ import annotations

from collections.abc import Mapping

from numpydoc_decorator import doc

from ..core.result import Result
from .models import FilePath
from .text import TextIO


@doc(summary="负责 .env 文件读写的无状态 IO 工具")
class EnvIO:
    @staticmethod
    @doc(
        summary="读取 .env 文件并解析为键值对字典",
        parameters={
            "path": "目标文件路径",
            "encoding": "读取时使用的文本编码",
        },
        returns="表示执行结果的显式结果对象",
    )
    def read(path: FilePath, encoding: str = "utf-8") -> Result[dict[str, str]]:
        text_result = TextIO.read(path, encoding=encoding)
        if not text_result.ok:
            data = dict(text_result.data)
            data["source"] = "env"
            return Result.failure(
                text_result.error or "读取文本文件失败",
                code=text_result.code,
                **data,
            )

        values: dict[str, str] = {}

        for line_number, raw_line in enumerate(text_result.unwrap().splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                return Result.failure(
                    "ENV 解析失败",
                    code="fs_parse_failed",
                    line=line_number,
                    content=raw_line,
                )

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key:
                return Result.failure(
                    "ENV 解析失败",
                    code="fs_parse_failed",
                    line=line_number,
                    content=raw_line,
                )

            values[key] = EnvIO._unescape_value(EnvIO._strip_quotes(value))

        return Result.success(values)

    @staticmethod
    @doc(
        summary="将键值对字典保存为 .env 文件",
        parameters={
            "path": "目标文件路径",
            "values": "需要保存的环境变量键值对",
            "encoding": "写入时使用的文本编码",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def write(
        path: FilePath,
        values: Mapping[str, str],
        *,
        encoding: str = "utf-8",
        create_parent: bool = True,
    ) -> Result[None]:
        lines = [f"{key}={EnvIO._quote_if_needed(value)}" for key, value in values.items()]
        content = "\n".join(lines)

        if content:
            content = f"{content}\n"

        return TextIO.write(
            path,
            content,
            encoding=encoding,
            create_parent=create_parent,
        )

    @staticmethod
    @doc(
        summary="移除 .env 值外层成对包裹的引号",
        parameters={"value": "待处理的原始值字符串"},
        returns="去除外层引号后的值字符串",
    )
    def _strip_quotes(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]
        return value

    @staticmethod
    @doc(
        summary="还原 .env 值中当前写入策略使用的转义序列",
        parameters={"value": "去除外层引号后的值字符串"},
        returns="按当前转义规则还原后的值字符串",
    )
    def _unescape_value(value: str) -> str:
        return value.replace('\\"', '"')

    @staticmethod
    @doc(
        summary="按 .env 写入需求为值补充必要引号",
        parameters={"value": "待序列化的环境变量值"},
        returns="适合直接写入 .env 文件的值字符串",
    )
    def _quote_if_needed(value: str) -> str:
        if not value:
            return '""'
        if any(char.isspace() for char in value) or "#" in value:
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value


__all__ = ["EnvIO"]
