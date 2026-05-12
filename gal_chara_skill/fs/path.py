from __future__ import annotations

from pathlib import Path

from numpydoc_decorator import doc

from ..conf.result import Result
from .models import FilePath


@doc(
    summary="将输入路径统一解析为 Path 对象",
    parameters={"path": "需要解析的路径"},
    returns="规范化后的 Path 对象",
)
def resolve(path: FilePath) -> Path:
    return Path(path)


@doc(
    summary="检查目标路径是否存在",
    parameters={"path": "需要检查的路径"},
    returns="路径当前是否存在",
)
def exists(path: FilePath) -> bool:
    return resolve(path).exists()


@doc(
    summary="检查目标路径是否为文件",
    parameters={"path": "需要检查的路径"},
    returns="路径当前是否指向一个文件",
)
def is_file(path: FilePath) -> bool:
    return resolve(path).is_file()


@doc(
    summary="检查目标路径是否为目录",
    parameters={"path": "需要检查的路径"},
    returns="路径当前是否指向一个目录",
)
def is_dir(path: FilePath) -> bool:
    return resolve(path).is_dir()


@doc(
    summary="确保目标目录存在",
    parameters={"path": "需要确保存在的目录路径"},
    returns="表示执行结果的显式结果对象",
)
def ensure_dir(path: FilePath) -> Result[Path]:
    directory = resolve(path)

    try:
        directory.mkdir(parents=True, exist_ok=True)
        return Result.success(directory)
    except Exception as exc:
        return Result.failure(
            "创建目录失败",
            code="fs_write_failed",
            path=str(directory),
            exception=str(exc),
        )


@doc(
    summary="确保目标文件的父目录存在",
    parameters={"path": "目标文件路径"},
    returns="表示执行结果的显式结果对象",
)
def ensure_parent_dir(path: FilePath) -> Result[Path]:
    file_path = resolve(path)
    parent = file_path.parent

    try:
        parent.mkdir(parents=True, exist_ok=True)
        return Result.success(parent)
    except Exception as exc:
        return Result.failure(
            "创建父目录失败",
            code="fs_write_failed",
            path=str(parent),
            exception=str(exc),
        )


__all__ = [
    "ensure_dir",
    "ensure_parent_dir",
    "exists",
    "is_dir",
    "is_file",
    "resolve",
]
