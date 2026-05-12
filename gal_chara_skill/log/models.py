from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from numpydoc_decorator import doc

from ..conf.module.log import LogLevel


@doc(
    summary="一条结构化日志记录",
    parameters={
        "level": "日志级别",
        "message": "正文",
        "timestamp": "产生时间",
        "module": "来源模块",
        "task_id": "关联任务 id",
        "data": "附加结构化信息",
    },
)
@dataclass(frozen=True)
class LogRecord:
    level: LogLevel
    message: str
    timestamp: datetime
    module: Optional[str] = None
    task_id: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


__all__ = ["LogRecord"]
