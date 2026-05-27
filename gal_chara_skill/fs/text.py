from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from numpydoc_decorator import doc

from ..core.executors import Executors
from ..core.result import Result
from .models import FilePath
from .path import ensure_parent_dir, resolve


@doc(summary="负责文本文件读写与追加的无状态 IO 工具")
class TextIO:
    @staticmethod
    @doc(
        summary="读取文本文件内容",
        parameters={
            "path": "目标文件路径",
            "encoding": "读取时使用的文本编码",
        },
        returns="表示执行结果的显式结果对象",
    )
    def read(path: FilePath, encoding: str = "utf-8") -> Result[str]:
        file_path = resolve(path)

        if not file_path.exists():
            return Result.failure("文件不存在", code="fs_not_found", path=str(file_path))
        if not file_path.is_file():
            return Result.failure("目标路径不是文件", code="fs_not_file", path=str(file_path))

        try:
            return Result.success(file_path.read_text(encoding=encoding))
        except Exception as exc:
            return Result.failure(
                "读取文本文件失败",
                code="fs_read_failed",
                path=str(file_path),
                exception=str(exc),
            )

    @staticmethod
    @doc(
        summary="写入文本内容到指定文件",
        parameters={
            "path": "目标文件路径",
            "content": "需要写入的文本内容",
            "encoding": "写入时使用的文本编码",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def write(
        path: FilePath,
        content: str,
        *,
        encoding: str = "utf-8",
        create_parent: bool = True,
    ) -> Result[None]:
        file_path = resolve(path)

        if create_parent:
            parent_result = ensure_parent_dir(file_path)
            if not parent_result.ok:
                return Result.failure_from(
                    parent_result,
                    error=parent_result.error or "创建父目录失败",
                    code=parent_result.code,
                    target_path=str(file_path),
                )

        try:
            TextIO._atomic_write_text(file_path, content, encoding=encoding)
            return Result.success()
        except Exception as exc:
            return Result.failure(
                "写入文本文件失败",
                code="fs_write_failed",
                path=str(file_path),
                exception=str(exc),
            )

    @staticmethod
    @doc(
        summary="向指定文件末尾追加文本内容",
        parameters={
            "path": "目标文件路径",
            "content": "需要追加的文本内容",
            "encoding": "写入时使用的文本编码",
            "create_parent": "是否自动创建父目录",
        },
        returns="表示执行结果的显式结果对象",
    )
    def append(
        path: FilePath,
        content: str,
        *,
        encoding: str = "utf-8",
        create_parent: bool = True,
    ) -> Result[None]:
        file_path = resolve(path)

        if create_parent:
            parent_result = ensure_parent_dir(file_path)
            if not parent_result.ok:
                return Result.failure_from(
                    parent_result,
                    error=parent_result.error or "创建父目录失败",
                    code=parent_result.code,
                    target_path=str(file_path),
                )

        try:
            with file_path.open("a", encoding=encoding) as fh:
                fh.write(content)
            return Result.success()
        except Exception as exc:
            return Result.failure(
                "追加文本文件失败",
                code="fs_write_failed",
                path=str(file_path),
                exception=str(exc),
            )

    @staticmethod
    @doc(
        summary="以临时文件替换的方式原子写入文本文件",
        parameters={
            "path": "目标文件路径",
            "content": "需要写入的文本内容",
            "encoding": "写入时使用的文本编码",
        },
    )
    def _atomic_write_text(path: Path, content: str, *, encoding: str) -> None:
        temp_path: Optional[Path] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding=encoding,
                delete=False,
                dir=path.parent,
                prefix=f"{path.name}.tmp-",
            ) as temp_file:
                temp_file.write(content)
                temp_path = Path(temp_file.name)

            try:
                os.replace(temp_path, path)
            except OSError:
                import shutil
                shutil.copy2(temp_path, path)
            temp_path.unlink(missing_ok=True)
            temp_path = None
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    @staticmethod
    @doc(
        summary="依次按常见编码读取文件内容，返回首次成功的解码结果",
        parameters={
            "path": "目标文件路径",
        },
        returns="成功时 value 为文件文本内容，所有编码均失败时返回失败结果",
    )
    def read_auto_encodings(path: FilePath) -> Result[str]:
        for encoding in             ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "gb18030", "shift_jis", "euc_jp"):
            result = TextIO.read(path, encoding=encoding)
            if result.ok:
                return result
        return Result.failure(
            "无法以任何已知编码读取文件",
            code="fs_read_failed",
            path=str(resolve(path)),
        )

    @staticmethod
    @Executors.to_async
    def aread(path: FilePath, encoding: str = "utf-8") -> Result[str]:
        return TextIO.read(path, encoding)

    @staticmethod
    @Executors.to_async
    def awrite(
        path: FilePath,
        content: str,
        *,
        encoding: str = "utf-8",
        create_parent: bool = True,
    ) -> Result[None]:
        return TextIO.write(path, content, encoding=encoding, create_parent=create_parent)

    @staticmethod
    @Executors.to_async
    def aappend(
        path: FilePath,
        content: str,
        *,
        encoding: str = "utf-8",
        create_parent: bool = True,
    ) -> Result[None]:
        return TextIO.append(path, content, encoding=encoding, create_parent=create_parent)


__all__ = ["TextIO"]
