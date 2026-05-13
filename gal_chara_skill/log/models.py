from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from numpydoc_decorator import doc

from ..conf.module.log import LogLevel
from ..core.result import Result


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

    @doc(
        summary="将日志记录转换为可写入 JSONL 的字典",
        returns="可被 JSONL 模块写入的日志记录字典",
    )
    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "task_id": self.task_id,
            "data": self.data,
        }

    @classmethod
    @doc(
        summary="从字典恢复日志记录",
        parameters={
            "cls": "日志记录类型",
            "data": "从 JSONL 中读取出的日志记录字典",
        },
        returns="成功时 value 为日志记录，失败时返回日志格式错误",
    )
    def from_dict(cls, data: Any) -> Result["LogRecord"]:
        if not isinstance(data, dict):
            return Result.failure("日志记录格式错误", code="log_parse_failed")

        try:
            record_data = data.get("data", {})
            if not isinstance(record_data, dict):
                return Result.failure("日志记录附加数据格式错误", code="log_parse_failed")

            return Result.success(
                cls(
                    level=data["level"],
                    message=data["message"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    module=data.get("module"),
                    task_id=data.get("task_id"),
                    data=record_data,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            return Result.failure(
                "日志记录恢复失败",
                code="log_parse_failed",
                exception=str(exc),
            )


__all__ = ["LogRecord"]
