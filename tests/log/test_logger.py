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


def test_should_log_error_threshold() -> None:
    """验证 should_log 会允许高于阈值的 error 级别"""
    logger = Logger(LogConfig(level="warning"), writer=StubWriter([Result.success()]))

    assert logger.should_log("error") is True


def test_should_log_warning_threshold() -> None:
    """验证 should_log 会允许等于阈值的 warning 级别"""
    logger = Logger(LogConfig(level="warning"), writer=StubWriter([Result.success()]))

    assert logger.should_log("warning") is True


def test_should_log_info_threshold() -> None:
    """验证 should_log 会过滤低于阈值的 info 级别"""
    logger = Logger(LogConfig(level="warning"), writer=StubWriter([Result.success()]))

    assert logger.should_log("info") is False


def test_should_log_debug_threshold() -> None:
    """验证 should_log 会过滤低于阈值的 debug 级别"""
    logger = Logger(LogConfig(level="warning"), writer=StubWriter([Result.success()]))

    assert logger.should_log("debug") is False


def test_try_log_filtered_level_result() -> None:
    """验证日志级别被过滤时 try_log 会直接返回成功结果"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(level="error"), writer=writer)

    result = logger.try_info("skip me")

    assert result.ok is True


def test_try_log_filtered_level_no_write() -> None:
    """验证日志级别被过滤时 try_log 不会调用 writer"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(level="error"), writer=writer)

    logger.try_info("skip me")

    assert writer.records == []


def test_try_log_retry_failure_result() -> None:
    """验证重试耗尽后 try_log 会返回失败结果"""
    writer = StubWriter(
        [
            Result.failure("first fail", code="log_write_failed"),
            Result.failure("second fail", code="log_write_failed"),
        ]
    )
    logger = Logger(LogConfig(max_write_attempts=2), writer=writer)

    result = logger.try_error("must retry")

    assert result.ok is False


def test_try_log_retry_failure_message() -> None:
    """验证重试耗尽后 try_log 会返回最后一次失败信息"""
    error_message = "second fail"
    writer = StubWriter(
        [
            Result.failure("first fail", code="log_write_failed"),
            Result.failure(error_message, code="log_write_failed"),
        ]
    )
    logger = Logger(LogConfig(max_write_attempts=2), writer=writer)

    result = logger.try_error("must retry")

    assert result.error == error_message


def test_try_log_retry_failure_attempts() -> None:
    """验证重试耗尽后 try_log 会按配置进行写入尝试"""
    writer = StubWriter(
        [
            Result.failure("first fail", code="log_write_failed"),
            Result.failure("second fail", code="log_write_failed"),
        ]
    )
    logger = Logger(LogConfig(max_write_attempts=2), writer=writer)

    logger.try_error("must retry")

    assert len(writer.records) == 2


def test_try_log_retry_success_result() -> None:
    """验证某次重试成功后 try_log 会返回成功结果"""
    writer = StubWriter(
        [
            Result.failure("first fail", code="log_write_failed"),
            Result.success(),
        ]
    )
    logger = Logger(LogConfig(max_write_attempts=3), writer=writer)

    result = logger.try_warning("retry once")

    assert result.ok is True


def test_try_log_retry_success_attempts() -> None:
    """验证某次重试成功后 try_log 会停止继续写入"""
    writer = StubWriter(
        [
            Result.failure("first fail", code="log_write_failed"),
            Result.success(),
        ]
    )
    logger = Logger(LogConfig(max_write_attempts=3), writer=writer)

    logger.try_warning("retry once")

    assert len(writer.records) == 2


def test_try_log_zero_max_attempts() -> None:
    """验证最大写入次数为 0 时仍会至少尝试一次"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(max_write_attempts=0), writer=writer)

    logger.try_info("once")

    assert len(writer.records) == 1


def test_try_log_preserves_module() -> None:
    """验证 try_log 会将模块名写入日志记录"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.try_info("hello", module="fs")

    assert writer.records[0].module == "fs"


def test_try_log_preserves_task_id() -> None:
    """验证 try_log 会将任务编号写入日志记录"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.try_info("hello", task_id="task-001")

    assert writer.records[0].task_id == "task-001"


def test_try_log_preserves_data() -> None:
    """验证 try_log 会将附加数据写入日志记录"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.try_info("hello", count=2)

    assert writer.records[0].data == {"count": 2}


def test_log_failure() -> None:
    """验证底层写入持续失败时 log 会抛出 RuntimeError"""
    error_message = "cannot write"
    writer = StubWriter([Result.failure(error_message, code="log_write_failed")])
    logger = Logger(LogConfig(max_write_attempts=1), writer=writer)

    with pytest.raises(RuntimeError) as exc_info:
        logger.error("must raise")

    assert error_message in str(exc_info.value)


def test_log_success() -> None:
    """验证底层写入成功时 log 不会抛出异常"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(max_write_attempts=1), writer=writer)

    logger.info("ok")


def test_try_log_console_output(capsys: pytest.CaptureFixture[str]) -> None:
    """验证开启控制台输出后 try_log 会打印格式化日志内容"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(write_to_console=True), writer=writer)
    message = "console line"

    logger.try_info(message, module="fs")

    captured = capsys.readouterr()

    assert message in captured.out


def test_try_log_console_output_before_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """验证控制台输出开启时即使写入失败也会先打印日志"""
    writer = StubWriter([Result.failure("cannot write", code="log_write_failed")])
    logger = Logger(LogConfig(write_to_console=True, max_write_attempts=1), writer=writer)
    message = "console line"

    logger.try_info(message)

    captured = capsys.readouterr()

    assert message in captured.out


def test_debug_uses_debug_level() -> None:
    """验证 debug 方法会写入 debug 级别日志"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(level="debug"), writer=writer)

    logger.debug("hello")

    assert writer.records[0].level == "debug"


def test_info_uses_info_level() -> None:
    """验证 info 方法会写入 info 级别日志"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.info("hello")

    assert writer.records[0].level == "info"


def test_warning_uses_warning_level() -> None:
    """验证 warning 方法会写入 warning 级别日志"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.warning("hello")

    assert writer.records[0].level == "warning"


def test_error_uses_error_level() -> None:
    """验证 error 方法会写入 error 级别日志"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(), writer=writer)

    logger.error("hello")

    assert writer.records[0].level == "error"


def test_try_debug_result() -> None:
    """验证 try_debug 会返回成功结果并写入 debug 级别日志"""
    writer = StubWriter([Result.success()])
    logger = Logger(LogConfig(level="debug"), writer=writer)

    result = logger.try_debug("hello")

    assert result.ok is True
    assert writer.records[0].level == "debug"
