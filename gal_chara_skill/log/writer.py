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
            write_result = LogIO.append(
                log_file,
                structured_log_file,
                line,
                record_data,
            )

        if not write_result.ok:
            return self._map_write_error(
                write_result,
                text_path=log_file,
                structured_path=structured_log_file,
            )

        return Result.success()

    @staticmethod
    @doc(
        summary="将底层日志文件写入错误映射为日志模块对外错误语义",
        parameters={
            "result": "底层日志文件写入返回的结果对象",
            "text_path": "文本日志文件路径",
            "structured_path": "结构化日志文件路径",
        },
        returns="映射后的日志写入失败结果",
    )
    def _map_write_error(
        result: Result[None],
        *,
        text_path: Path,
        structured_path: Path,
    ) -> Result[None]:
        data = dict(result.data)
        path = data.get("path")

        if path == str(structured_path):
            error = result.error or "写入结构化日志失败"
        else:
            error = result.error or "写入日志失败"
            data["path"] = str(text_path)

        return Result.failure(
            error,
            code=result.code,
            **data,
        )

    @classmethod
    def _get_lock(cls, path: Path) -> threading.Lock:
        with cls._lock_table_guard:
            lock = cls._locks_by_path.get(path)
            if lock is None:
                lock = threading.Lock()
                cls._locks_by_path[path] = lock
            return lock


__all__ = ["LogWriter"]
