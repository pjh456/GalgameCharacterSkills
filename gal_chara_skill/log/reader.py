from __future__ import annotations

from pathlib import Path
from typing import Optional

from numpydoc_decorator import doc

from ..conf.module.log import LogLevel, LogPathConfig
from ..core.result import Result
from ..fs import LogIO
from .models import LogRecord


@doc(
    summary="负责读取与查询日志文件",
    parameters={"path_config": "日志读取时使用的路径配置"},
)
class LogReader:
    def __init__(self, path_config: LogPathConfig) -> None:
        self.path_config = path_config

    @doc(
        summary="获取指定任务对应的结构化日志文件路径",
        parameters={"task_id": "可选的任务 id"},
        returns="对应结构化日志文件的完整路径",
    )
    def get_log_file_path(self, task_id: Optional[str] = None) -> Path:
        if task_id:
            return self.path_config.root_dir / f"{task_id}.jsonl"

        stem = Path(self.path_config.default_file_name).stem
        return self.path_config.root_dir / f"{stem}.jsonl"

    @doc(
        summary="读取指定日志文件中的全部日志记录",
        parameters={"task_id": "可选的任务 id"},
        returns="成功时 value 为日志记录列表，文件不存在时返回空列表，格式错误时返回失败结果",
    )
    def read(self, task_id: Optional[str] = None) -> Result[list[LogRecord]]:
        log_file = self.get_log_file_path(task_id)
        read_result = LogIO.read(log_file)

        if not read_result.ok:
            if read_result.code == "fs_not_found":
                return Result.success([])

            data = dict(read_result.data)
            data["path"] = str(log_file)
            return Result.failure(
                read_result.error or "读取日志失败",
                code=read_result.code,
                **data,
            )

        records: list[LogRecord] = []
        for index, item in enumerate(read_result.unwrap()):
            record_result = LogRecord.from_dict(item)
            if not record_result.ok:
                data = dict(record_result.data)
                data["path"] = str(log_file)
                data["index"] = index
                return Result.failure(
                    record_result.error or "日志记录恢复失败",
                    code=record_result.code,
                    **data,
                )
            records.append(record_result.unwrap())

        return Result.success(records)

    @doc(
        summary="按条件查询日志记录",
        parameters={
            "task_id": "可选的任务 id",
            "level": "可选的日志级别过滤条件",
            "module": "可选的来源模块过滤条件",
        },
        returns="成功时 value 为满足条件的日志记录列表，读取失败时返回失败结果",
    )
    def query(
        self,
        *,
        task_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        module: Optional[str] = None,
    ) -> Result[list[LogRecord]]:
        read_result = self.read(task_id)
        if not read_result.ok:
            return read_result

        records = [
            record
            for record in read_result.unwrap()
            if (level is None or record.level == level)
            and (module is None or record.module == module)
        ]

        return Result.success(records)


__all__ = ["LogReader"]
