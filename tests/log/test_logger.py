from __future__ import annotations

import pytest

from gal_chara_skill.conf.module.log import LogConfig
from gal_chara_skill.conf.result import Result
from gal_chara_skill.log.logger import Logger
from gal_chara_skill.log.models import LogRecord


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
    logger = Logger(LogConfig(level="warning"), writer=StubWriter([Result.success()]))

    assert logger.should_log("error") is True
    assert logger.should_log("warning") is True
    assert logger.should_log("info") is False
    assert logger.should_log("debug") is False


def test_try_log_filtered() -> None:
    """验证被过滤的日志级别会直接成功返回且不会写入底层 writer"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(level="error"), writer=writer)

    result = logger.try_info("skip me")

    assert result.ok is True
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
    logger = Logger(LogConfig(max_write_attempts=2), writer=writer)

    result = logger.try_error("must retry")

    assert result.ok is False
    assert result.error == error_message
    assert len(writer.records) == 2


def test_try_log_retry_success() -> None:
    """验证 try_log 在某次重试成功后会返回成功并停止继续写入"""
    writer = StubWriter(
        [
            Result.failure("first fail"),
            Result.success(),
        ]
    )
    logger = Logger(LogConfig(max_write_attempts=3), writer=writer)

    result = logger.try_warning("retry once")

    assert result.ok is True
    assert len(writer.records) == 2


def test_try_log_zero_max_attempts() -> None:
    """验证最大写入次数为 0 时仍会至少尝试一次"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(max_write_attempts=0), writer=writer)

    logger.try_info("once")

    assert len(writer.records) == 1


def test_try_log_preserves_record_fields() -> None:
    """验证 try_log 会保留模块名、任务编号与附加数据"""
    writer = StubWriter([Result.success(), Result.success(), Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.try_info("hello", module="fs")
    logger.try_info("hello", task_id="task-001")
    logger.try_info("hello", count=2)

    assert writer.records[0].module == "fs"
    assert writer.records[1].task_id == "task-001"
    assert writer.records[2].data == {"count": 2}


def test_log() -> None:
    """验证 log 在失败时抛异常，在成功时不抛异常"""
    error_message = "cannot write"
    failure_writer = StubWriter([Result.failure(error_message)])
    success_writer = StubWriter([Result.success()])
    failure_logger = Logger(LogConfig(max_write_attempts=1), writer=failure_writer)
    success_logger = Logger(LogConfig(max_write_attempts=1), writer=success_writer)

    with pytest.raises(RuntimeError) as exc_info:
        failure_logger.error("must raise")

    success_logger.info("ok")

    assert error_message in str(exc_info.value)


def test_try_log_console_output(capsys: pytest.CaptureFixture[str]) -> None:
    """验证开启控制台输出时，无论写入成功还是失败都会先打印格式化日志"""
    success_writer = StubWriter([Result.success()])
    failure_writer = StubWriter([Result.failure("cannot write")])
    success_logger = Logger(LogConfig(write_to_console=True), writer=success_writer)
    failure_logger = Logger(LogConfig(write_to_console=True, max_write_attempts=1), writer=failure_writer)

    success_logger.try_info("success line", module="fs")
    failure_logger.try_info("failure line")

    captured = capsys.readouterr()

    assert "success line" in captured.out
    assert "failure line" in captured.out


def test_log_level_methods() -> None:
    """验证各级别日志方法会写入对应级别，并返回预期结果"""
    writer = StubWriter([Result.success(), Result.success(), Result.success(), Result.success(), Result.success()])
    logger = Logger(LogConfig(level="debug"), writer=writer)

    logger.debug("hello")
    logger.info("hello")
    logger.warning("hello")
    logger.error("hello")
    result = logger.try_debug("hello")

    assert writer.records[0].level == "debug"
    assert writer.records[1].level == "info"
    assert writer.records[2].level == "warning"
    assert writer.records[3].level == "error"
    assert writer.records[4].level == "debug"
    assert result.ok is True
