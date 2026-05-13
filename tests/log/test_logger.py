from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.core.result import Result
from gal_chara_skill.log.logger import Logger
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter


class StubWriter:
    def __init__(self, results: list[Result[None]]) -> None:
        self.results = results
        self.records: list[LogRecord] = []

    def write(self, record: LogRecord) -> Result[None]:
        self.records.append(record)
        index = min(len(self.records) - 1, len(self.results) - 1)
        return self.results[index]

    def format_record(self, record: LogRecord) -> str:
        return f"{record.level}:{record.message}"


def test_should_log() -> None:
    """验证 should_log 会按阈值区分应记录与应过滤的级别"""
    logger = Logger(LogPolicy(level="warning"), writer=StubWriter([Result.success()]))

    assert logger.should_log("error") is True
    assert logger.should_log("warning") is True
    assert logger.should_log("info") is False
    assert logger.should_log("debug") is False


def test_try_log_filtered() -> None:
    """验证被过滤的日志级别会直接成功返回且不会写入底层 writer"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogPolicy(level="error"), writer=writer)

    result = logger.try_info("skip me")

    assert result.ok is True
    assert result.value is None
    assert writer.records == []


def test_try_log_retry_failure() -> None:
    """验证 try_log 在重试耗尽后会返回最后一次失败并停止于配置次数"""
    error_message = "second fail"
    writer = StubWriter(
        [
            Result.failure("first fail"),
            Result.failure(error_message),
        ]
    )
    logger = Logger(LogPolicy(max_write_attempts=2), writer=writer)

    result = logger.try_error("must retry")

    assert result.ok is False
    assert result.error == error_message
    assert result.value is writer.records[-1]
    assert len(writer.records) == 2


def test_try_log_retry_success() -> None:
    """验证 try_log 在某次重试成功后会返回成功并停止继续写入"""
    writer = StubWriter(
        [
            Result.failure("first fail"),
            Result.success(),
        ]
    )
    logger = Logger(LogPolicy(max_write_attempts=3), writer=writer)

    result = logger.try_warning("retry once")

    assert result.ok is True
    assert result.value is writer.records[-1]
    assert len(writer.records) == 2


def test_try_log_zero_max_attempts() -> None:
    """验证最大写入次数为 0 时仍会至少尝试一次"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogPolicy(max_write_attempts=0), writer=writer)

    logger.try_info("once")

    assert len(writer.records) == 1


def test_try_log_preserves_record_fields() -> None:
    """验证 try_log 会保留模块名、任务编号与附加数据"""
    writer = StubWriter([Result.success(), Result.success(), Result.success()])
    logger = Logger(LogPolicy(), writer=writer)

    logger.try_info("hello", module="fs")
    logger.try_info("hello", task_id="task-001")
    logger.try_info("hello", count=2)

    assert writer.records[0].module == "fs"
    assert writer.records[1].task_id == "task-001"
    assert writer.records[2].data == {"count": 2}


def test_log() -> None:
    """验证 log 在失败时抛异常，在成功时返回日志记录"""
    error_message = "cannot write"
    failure_writer = StubWriter([Result.failure(error_message)])
    success_writer = StubWriter([Result.success()])
    failure_logger = Logger(LogPolicy(max_write_attempts=1), writer=failure_writer)
    success_logger = Logger(LogPolicy(max_write_attempts=1), writer=success_writer)

    with pytest.raises(RuntimeError) as exc_info:
        failure_logger.error("must raise")

    record = success_logger.info("ok")

    assert error_message in str(exc_info.value)
    assert record is success_writer.records[0]


def test_log_filtered() -> None:
    """验证 log 在日志级别被过滤时返回 None 且不会写入底层 writer"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogPolicy(level="error"), writer=writer)

    record = logger.info("skip me")

    assert record is None
    assert writer.records == []


def test_try_log_console_output(capsys: pytest.CaptureFixture[str]) -> None:
    """验证开启控制台输出时，无论写入成功还是失败都会先打印格式化日志"""
    success_writer = StubWriter([Result.success()])
    failure_writer = StubWriter([Result.failure("cannot write")])
    success_logger = Logger(LogPolicy(write_to_console=True), writer=success_writer)
    failure_logger = Logger(LogPolicy(write_to_console=True, max_write_attempts=1), writer=failure_writer)

    success_logger.try_info("success line", module="fs")
    failure_logger.try_info("failure line")

    captured = capsys.readouterr()

    assert "success line" in captured.out
    assert "failure line" in captured.out


def test_log_level_methods() -> None:
    """验证各级别日志方法会写入对应级别，并返回预期结果"""
    writer = StubWriter([Result.success(), Result.success(), Result.success(), Result.success(), Result.success()])
    logger = Logger(LogPolicy(level="debug"), writer=writer)

    debug_record = logger.debug("hello")
    info_record = logger.info("hello")
    warning_record = logger.warning("hello")
    error_record = logger.error("hello")
    result = logger.try_debug("hello")

    assert writer.records[0].level == "debug"
    assert writer.records[1].level == "info"
    assert writer.records[2].level == "warning"
    assert writer.records[3].level == "error"
    assert writer.records[4].level == "debug"
    assert debug_record is writer.records[0]
    assert info_record is writer.records[1]
    assert warning_record is writer.records[2]
    assert error_record is writer.records[3]
    assert result.ok is True
    assert result.value is writer.records[4]


def test_logger_with_real_writer(project_root: Path) -> None:
    """验证 Logger 与真实 LogWriter 联动时会把日志写入目标文件"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("output/logs"), default_file_name="app.log"),
    )
    logger = Logger(LogPolicy(), writer=writer)

    logger.info("hello", module="log")

    log_file = project_root / "output/logs/app.log"
    content = log_file.read_text(encoding="utf-8")

    assert log_file.exists()
    assert "INFO" in content
    assert "hello" in content
