from __future__ import annotations

from pathlib import Path

from numpydoc_decorator import doc

from ..core.catch import catch_result
from ..core.executors import Executors
from ..core.result import Result
from .errors import FsErrors
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


@catch_result(handlers={Exception: FsErrors.io_fail("fs_write_failed", "创建目录失败")})
@doc(
    summary="确保目标目录存在",
    parameters={"path": "需要确保存在的目录路径"},
    returns="表示执行结果的显式结果对象",
)
def ensure_dir(path: FilePath) -> Result[Path]:
    directory = resolve(path)
    directory.mkdir(parents=True, exist_ok=True)
    return Result.success(directory)


@catch_result(handlers={Exception: FsErrors.handle_ensure_parent_fail})
@doc(
    summary="确保目标文件的父目录存在",
    parameters={"path": "目标文件路径"},
    returns="表示执行结果的显式结果对象",
)
def ensure_parent_dir(path: FilePath) -> Result[Path]:
    file_path = resolve(path)
    parent = file_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    return Result.success(parent)


@Executors.to_async
def aensure_dir(path: FilePath) -> Result[Path]:
    return ensure_dir(path)


@Executors.to_async
def aensure_parent_dir(path: FilePath) -> Result[Path]:
    return ensure_parent_dir(path)


__all__ = [
    "aensure_dir",
    "aensure_parent_dir",
    "ensure_dir",
    "ensure_parent_dir",
    "exists",
    "is_dir",
    "is_file",
    "resolve",
]
