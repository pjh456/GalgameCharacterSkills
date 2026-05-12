from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Protocol

from numpydoc_decorator import doc

from ..conf.module.log import LOG_LEVEL_ORDER, LogConfig, LogLevel
from ..core.result import Result
from .models import LogRecord
from .writer import LogWriter


class LogWriterLike(Protocol):
    def write(self, record: LogRecord) -> Result[None]:
        ...

    def format_record(self, record: LogRecord) -> str:
        ...


@doc(
    summary="负责级别过滤的统一日志接口",
    parameters={
        "config": "使用的全局配置",
        "writer": "可选的日志写入器实例",
    },
)
class Logger:
    def __init__(self, config: LogConfig, writer: Optional[LogWriterLike] = None) -> None:
        self.config = config
        self.writer = writer or LogWriter(config)

    @doc(
        summary="尝试记录一条 debug 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="表示写入结果的显式结果对象",
    )
    def try_debug(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[None]:
        return self.try_log("debug", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 debug 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def debug(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> None:
        self.log("debug", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试记录一条 info 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="表示写入结果的显式结果对象",
    )
    def try_info(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[None]:
        return self.try_log("info", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 info 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def info(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> None:
        self.log("info", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试记录一条 warning 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="表示写入结果的显式结果对象",
    )
    def try_warning(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[None]:
        return self.try_log("warning", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 warning 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def warning(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> None:
        self.log("warning", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试记录一条 error 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="表示写入结果的显式结果对象",
    )
    def try_error(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[None]:
        return self.try_log("error", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 error 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def error(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> None:
        self.log("error", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试按指定级别记录一条日志",
        parameters={
            "level": "当前日志级别",
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="表示写入结果的显式结果对象",
    )
    def try_log(
        self,
        level: LogLevel,
        message: str,
        *,
        module: Optional[str] = None,
        task_id: Optional[str] = None,
        **data: Any,
    ) -> Result[None]:
        if not self.should_log(level):
            return Result.success()

        record = LogRecord(
            level=level,
            message=message,
            timestamp=datetime.now(),
            module=module,
            task_id=task_id,
            data=data,
        )

        if self.config.write_to_console:
            print(self.writer.format_record(record))

        return self._write_with_retry(record)

    @doc(
        summary="按指定级别记录一条必须写入的日志",
        parameters={
            "level": "当前日志级别",
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        raises={"RuntimeError": "日志写入失败且重试耗尽时抛出"},
    )
    def log(
        self,
        level: LogLevel,
        message: str,
        *,
        module: Optional[str] = None,
        task_id: Optional[str] = None,
        **data: Any,
    ) -> None:
        result = self.try_log(level, message, module=module, task_id=task_id, **data)
        if not result.ok:
            raise RuntimeError(result.error or "日志写入失败")
        return None

    @doc(
        summary="按配置重试写入日志记录",
        parameters={"record": "需要写入的日志记录"},
        returns="表示写入结果的显式结果对象",
    )
    def _write_with_retry(self, record: LogRecord) -> Result[None]:
        attempts = max(1, self.config.max_write_attempts)
        last_result: Optional[Result[None]] = None

        for attempt in range(1, attempts + 1):
            last_result = self.writer.write(record)
            if last_result.ok:
                return last_result

        if last_result is None:
            return Result.failure("日志写入失败", code="log_write_failed")
        return last_result

    @doc(
        summary="判断指定日志级别是否应该被记录",
        parameters={"level": "需要判断的日志级别"},
        returns="当前日志级别是否满足记录条件",
    )
    def should_log(self, level: LogLevel) -> bool:
        return LOG_LEVEL_ORDER[level] >= LOG_LEVEL_ORDER[self.config.level]


__all__ = ["Logger"]
