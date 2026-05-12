from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from numpydoc_decorator import doc

LogLevel = Literal["debug", "info", "warning", "error"]

LOG_LEVEL_ORDER: dict[LogLevel, int] = {
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
}


@doc(
    summary="日志记录行为配置",
    parameters={
        "level": "最低记录级别",
        "write_to_console": "是否同步输出到控制台",
        "write_to_file": "是否写入日志文件",
        "max_write_attempts": "单次写日志允许的最大尝试次数",
    },
)
@dataclass(frozen=True)
class LogPolicy:
    level: LogLevel = "info"
    write_to_console: bool = False
    write_to_file: bool = True
    max_write_attempts: int = 3


@doc(
    summary="日志输出路径配置",
    parameters={
        "root_dir": "日志文件根目录",
        "default_file_name": "无任务上下文时写入的默认日志文件名",
    },
)
@dataclass(frozen=True)
class LogPathConfig:
    root_dir: Path
    default_file_name: str = "app.log"


__all__ = [
    "LogLevel",
    "LOG_LEVEL_ORDER",
    "LogPolicy",
    "LogPathConfig",
]
