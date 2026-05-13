from __future__ import annotations

from typing import Any

import yaml
from numpydoc_decorator import doc

from ..core.result import Result
from .models import FilePath
from .path import resolve
from .text import write as write_text


@doc(summary="负责 YAML 文件读写的无状态 IO 工具")
class YamlIO:
    @staticmethod
    @doc(
        summary="读取 YAML 文件并解析为 Python 对象",
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
                return Result.success(yaml.safe_load(fh))
        except yaml.YAMLError as exc:
            return Result.failure(
                "YAML 解析失败",
                code="fs_parse_failed",
                path=str(file_path),
                exception=str(exc),
            )
        except Exception as exc:
            return Result.failure(
                "读取 YAML 文件失败",
                code="fs_read_failed",
                path=str(file_path),
                exception=str(exc),
            )

    @staticmethod
    @doc(
        summary="将 Python 对象写入 YAML 文件",
        parameters={
            "path": "目标文件路径",
            "data": "需要写入的 Python 对象",
            "encoding": "写入时使用的文本编码",
            "allow_unicode": "是否直接写入非 ASCII 字符",
            "sort_keys": "是否按键名排序输出字典",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def write(
        path: FilePath,
        data: Any,
        *,
        encoding: str = "utf-8",
        allow_unicode: bool = True,
        sort_keys: bool = False,
        create_parent: bool = True,
    ) -> Result[None]:
        try:
            text = yaml.safe_dump(
                data,
                allow_unicode=allow_unicode,
                sort_keys=sort_keys,
            )
        except yaml.YAMLError as exc:
            return Result.failure(
                "YAML 序列化失败",
                code="fs_parse_failed",
                exception=str(exc),
            )

        return write_text(
            path,
            text,
            encoding=encoding,
            create_parent=create_parent,
        )


__all__ = ["YamlIO"]
