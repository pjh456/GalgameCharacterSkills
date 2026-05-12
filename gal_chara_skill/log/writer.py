from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from numpydoc_decorator import doc

from ..core.paths import LOGS_DIR
from ..conf.module.log import LogConfig
from ..core.result import Result
from .models import LogRecord


@doc(
    summary="负责写入日志文件",
    parameters={"config": "日志写入时使用的全局配置"},
)
class LogWriter:
    def __init__(self, config: LogConfig) -> None:
        self.config = config

    @doc(
        summary="获取指定任务对应的日志文件路径",
        parameters={"task_id": "可选的任务 id"},
        returns="对应日志文件的完整路径",
    )
    def get_log_file_path(self, task_id: Optional[str] = None) -> Path:
        if task_id:
            return LOGS_DIR / f"{task_id}.log"
        return LOGS_DIR / self.config.default_file_name

    @doc(
        summary="写入一条日志记录",
        parameters={"record": "需要写入的日志记录"},
        returns="表示写入结果的显式结果对象",
    )
    def write(self, record: LogRecord) -> Result[None]:
        if not self.config.write_to_file:
            return Result.success()

        log_file = self.get_log_file_path(record.task_id)

        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(self.format_record(record))
                fh.write("\n")
            return Result.success()
        except Exception as exc:
            return Result.failure(
                "写入日志失败",
                code="log_write_failed",
                path=str(log_file),
                exception=str(exc),
            )

    @doc(
        summary="将日志记录格式化为可写入文件的文本",
        parameters={"record": "需要格式化的日志记录"},
        returns="格式化后的单行日志文本",
    )
    def format_record(self, record: LogRecord) -> str:
        parts = [
            record.timestamp.isoformat(timespec="seconds"),
            record.level.upper(),
        ]

        if record.module:
            parts.append(record.module)
        if record.task_id:
            parts.append(f"task={record.task_id}")

        prefix = " | ".join(parts)

        if record.data:
            data_text = json.dumps(record.data, ensure_ascii=False, sort_keys=True)
            return f"{prefix} | {record.message} | data={data_text}"
        return f"{prefix} | {record.message}"


__all__ = ["LogWriter"]
