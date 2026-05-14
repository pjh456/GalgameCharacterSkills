from __future__ import annotations

import threading
from pathlib import Path
from typing import ClassVar, Optional

from numpydoc_decorator import doc

from ..conf.module.log import LogPathConfig, LogPolicy
from ..core.result import Result
from ..fs import LogIO
from .models import LogRecord


@doc(
    summary="负责写入日志文件",
    parameters={
        "policy": "日志写入时使用的行为配置",
        "path_config": "日志写入时使用的路径配置",
    },
)
class LogWriter:
    _lock_table_guard: ClassVar[threading.Lock] = threading.Lock()
    _locks_by_path: ClassVar[dict[Path, threading.Lock]] = {}

    def __init__(self, policy: LogPolicy, path_config: LogPathConfig) -> None:
        self.policy = policy
        self.path_config = path_config

    @doc(
        summary="获取指定任务对应的文本日志文件路径",
        parameters={"task_id": "可选的任务 id"},
        returns="对应文本日志文件的完整路径",
    )
    def get_log_file_path(self, task_id: Optional[str] = None) -> Path:
        if task_id:
            return self.path_config.root_dir / f"{task_id}.log"
        return self.path_config.root_dir / self.path_config.default_file_name

    @doc(
        summary="获取指定任务对应的结构化日志文件路径",
        parameters={"task_id": "可选的任务 id"},
        returns="对应结构化日志文件的完整路径",
    )
    def get_structured_log_file_path(self, task_id: Optional[str] = None) -> Path:
        if task_id:
            return self.path_config.root_dir / f"{task_id}.jsonl"

        stem = Path(self.path_config.default_file_name).stem
        return self.path_config.root_dir / f"{stem}.jsonl"

    @doc(
        summary="写入一条日志记录",
        parameters={"record": "需要写入的日志记录"},
        returns="表示写入结果的显式结果对象",
    )
    def write(self, record: LogRecord) -> Result[None]:
        if not self.policy.write_to_file:
            return Result.success()

        log_file = self.get_log_file_path(record.task_id)
        structured_log_file = self.get_structured_log_file_path(record.task_id)
        file_lock = self._get_lock(log_file)
        line = record.to_text()
        record_data = record.to_dict()

        with file_lock:
            write_result = LogIO.append_record(
                structured_log_file,
                record_data,
            )
            if not write_result.ok:
                return self._map_write_error(
                    write_result,
                    path=structured_log_file,
                    default_error="写入结构化日志失败",
                )

            log_result = LogIO.append_log(log_file, line, encoding="utf-8")
            if log_result.ok:
                return Result.success()

            # 记录保存成功，若日志打印失败则根据记录重建日志
            rewrite_result = self._rewrite_log(log_file, structured_log_file)
            if rewrite_result.ok:
                return Result.success(
                    log_rebuilt=True,
                    log_append_error=log_result.error,
                    log_append_code=log_result.code,
                    log_append_data=dict(log_result.data),
                )

            return Result.success(
                log_view_degraded=True,
                log_append_error=log_result.error,
                log_append_code=log_result.code,
                log_append_data=dict(log_result.data),
                log_rewrite_error=rewrite_result.error,
                log_rewrite_code=rewrite_result.code,
                log_rewrite_data=dict(rewrite_result.data),
            )

    @staticmethod
    @doc(
        summary="将底层日志文件写入错误映射为日志模块对外错误语义",
        parameters={
            "result": "底层日志文件写入返回的结果对象",
            "path": "出错时应归属的目标路径",
            "default_error": "当底层未提供错误消息时使用的默认错误信息",
        },
        returns="映射后的日志写入失败结果",
    )
    def _map_write_error(
        result: Result[None],
        *,
        path: Path,
        default_error: str,
    ) -> Result[None]:
        data = dict(result.data)
        data["path"] = str(path)

        return Result.failure(
            result.error or default_error,
            code=result.code,
            **data,
        )

    @classmethod
    @doc(
        summary="根据结构化日志重建文本日志视图",
        parameters={
            "cls": "日志写入器类型",
            "log_path": "需要被重写的文本日志路径",
            "structured_log_path": "作为真相源读取的结构化日志路径",
        },
        returns="成功时表示文本日志已与结构化日志对齐，失败时返回读取、解析或重写阶段的错误信息",
    )
    def _rewrite_log(
        cls,
        log_path: Path,
        structured_log_path: Path,
    ) -> Result[None]:
        read_result = LogIO.read(structured_log_path)
        if not read_result.ok:
            return cls._map_write_error(
                read_result,
                path=structured_log_path,
                default_error="读取结构化日志失败",
            )

        logs: list[str] = []
        for index, item in enumerate(read_result.unwrap()):
            record_result = LogRecord.from_dict(item)
            if not record_result.ok:
                data = dict(record_result.data)
                data["path"] = str(structured_log_path)
                data["index"] = index
                return Result.failure(
                    record_result.error or "日志记录恢复失败",
                    code=record_result.code,
                    **data,
                )
            logs.append(record_result.unwrap().to_text())

        rewrite_result = LogIO.rewrite_log(log_path, logs, encoding="utf-8")
        if not rewrite_result.ok:
            return cls._map_write_error(
                rewrite_result,
                path=log_path,
                default_error="重建日志视图失败",
            )

        return Result.success()

    @classmethod
    @doc(
        summary="获取指定日志路径对应的共享互斥锁",
        parameters={
            "cls": "日志写入器类型",
            "path": "需要串行化写入的日志路径",
        },
        returns="同一路径在当前进程内共享的一把锁对象",
    )
    def _get_lock(cls, path: Path) -> threading.Lock:
        with cls._lock_table_guard:
            lock = cls._locks_by_path.get(path)
            if lock is None:
                lock = threading.Lock()
                cls._locks_by_path[path] = lock
            return lock


__all__ = ["LogWriter"]
