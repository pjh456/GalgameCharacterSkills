from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Protocol

from numpydoc_decorator import doc

from ..conf.module.log import LOG_LEVEL_ORDER, LogLevel, LogPolicy
from ..core.result import Result
from .models import LogRecord


class LogWriterLike(Protocol):
    def write(self, record: LogRecord) -> Result[None]:
        ...

    def format_record(self, record: LogRecord) -> str:
        ...


@doc(
    summary="负责级别过滤的统一日志接口",
    parameters={
        "policy": "使用的日志记录行为配置",
        "writer": "日志写入器实例",
    },
)
class Logger:
    def __init__(self, policy: LogPolicy, writer: LogWriterLike) -> None:
        self.policy = policy
        self.writer = writer

    @doc(
        summary="尝试记录一条 debug 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="显式结果对象：成功记录时 value 为日志记录，成功过滤时 value 为 None，写入失败时返回失败结果",
    )
    def try_debug(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[Optional[LogRecord]]:
        return self.try_log("debug", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 debug 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="成功记录时返回日志记录，日志级别被过滤时返回 None",
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def debug(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Optional[LogRecord]:
        return self.log("debug", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试记录一条 info 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="显式结果对象：成功记录时 value 为日志记录，成功过滤时 value 为 None，写入失败时返回失败结果",
    )
    def try_info(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[Optional[LogRecord]]:
        return self.try_log("info", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 info 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="成功记录时返回日志记录，日志级别被过滤时返回 None",
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def info(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Optional[LogRecord]:
        return self.log("info", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试记录一条 warning 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="显式结果对象：成功记录时 value 为日志记录，成功过滤时 value 为 None，写入失败时返回失败结果",
    )
    def try_warning(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[Optional[LogRecord]]:
        return self.try_log("warning", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 warning 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="成功记录时返回日志记录，日志级别被过滤时返回 None",
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def warning(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Optional[LogRecord]:
        return self.log("warning", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试记录一条 error 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="显式结果对象：成功记录时 value 为日志记录，成功过滤时 value 为 None，写入失败时返回失败结果",
    )
    def try_error(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Result[Optional[LogRecord]]:
        return self.try_log("error", message, module=module, task_id=task_id, **data)

    @doc(
        summary="记录一条 error 级别日志",
        parameters={
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="成功记录时返回日志记录，日志级别被过滤时返回 None",
        raises={"RuntimeError": "日志写入失败且本次调用要求必须写入时抛出"},
    )
    def error(self, message: str, *, module: Optional[str] = None, task_id: Optional[str] = None, **data: Any) -> Optional[LogRecord]:
        return self.log("error", message, module=module, task_id=task_id, **data)

    @doc(
        summary="尝试按指定级别记录一条日志",
        parameters={
            "level": "当前日志级别",
            "message": "日志正文",
            "module": "可选的来源模块名",
            "task_id": "可选的关联任务 id",
            "data": "需要附带记录的额外信息",
        },
        returns="显式结果对象：成功记录时 value 为日志记录，成功过滤时 value 为 None，写入失败时返回失败结果",
    )
    def try_log(
        self,
        level: LogLevel,
        message: str,
        *,
        module: Optional[str] = None,
        task_id: Optional[str] = None,
        **data: Any,
    ) -> Result[Optional[LogRecord]]:
        if not self.should_log(level):
            return Result.success(None)

        record = LogRecord(
            level=level,
            message=message,
            timestamp=datetime.now(),
            module=module,
            task_id=task_id,
            data=data,
        )

        if self.policy.write_to_console:
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
        returns="成功记录时返回日志记录，日志级别被过滤时返回 None",
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
    ) -> Optional[LogRecord]:
        result = self.try_log(level, message, module=module, task_id=task_id, **data)
        if not result.ok:
            raise RuntimeError(result.error or "日志写入失败")
        return result.value

    @doc(
        summary="按配置重试写入日志记录",
        parameters={"record": "需要写入的日志记录"},
        returns="显式结果对象：写入成功时 value 为日志记录，写入失败时 value 为尝试写入的日志记录",
    )
    def _write_with_retry(self, record: LogRecord) -> Result[Optional[LogRecord]]:
        attempts = max(1, self.policy.max_write_attempts)
        last_result: Optional[Result[None]] = None

        for attempt in range(1, attempts + 1):
            last_result = self.writer.write(record)
            if last_result.ok:
                return Result.success(record, **last_result.data)

        if last_result is None:
            return Result.failure("日志写入失败", code="log_write_failed")
        return Result.failure(
            last_result.error or "日志写入失败",
            code=last_result.code,
            value=record,
            **last_result.data,
        )

    @doc(
        summary="判断指定日志级别是否应该被记录",
        parameters={"level": "需要判断的日志级别"},
        returns="当前日志级别是否满足记录条件",
    )
    def should_log(self, level: LogLevel) -> bool:
        return LOG_LEVEL_ORDER[level] >= LOG_LEVEL_ORDER[self.policy.level]


__all__ = ["Logger"]
