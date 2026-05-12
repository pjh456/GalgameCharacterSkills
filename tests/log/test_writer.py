from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import IO, Any

import pytest
from gal_chara_skill.conf.constants import LOGS_DIR, OUTPUT_DIR
from gal_chara_skill.conf.module.log import LogConfig
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter


def test_get_log_file_path_default_file_name() -> None:
    """验证未传入任务编号时会使用默认日志文件名"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))

    assert writer.get_log_file_path() == LOGS_DIR / "test.log"


def test_get_log_file_path_task_id() -> None:
    """验证传入任务编号时会生成对应任务日志路径"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))

    assert writer.get_log_file_path("task-001") == LOGS_DIR / "task-001.log"


def test_format_record_timestamp() -> None:
    """验证 format_record 会输出时间戳前缀"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    text = writer.format_record(record)

    assert text.startswith("2026-05-12T10:30:45 | INFO")


def test_format_record_level() -> None:
    """验证 format_record 会将日志级别转换为大写"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="warning",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    text = writer.format_record(record)

    assert "WARNING" in text


def test_format_record_module() -> None:
    """验证 format_record 会在存在时写入模块名"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="fs",
    )

    text = writer.format_record(record)

    assert " | fs | " in text


def test_format_record_task_id() -> None:
    """验证 format_record 会在存在时写入任务编号"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        task_id="task-001",
    )

    text = writer.format_record(record)

    assert "task=task-001" in text


def test_format_record_data() -> None:
    """验证 format_record 会在存在时写入结构化数据"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        data={"count": 2},
    )

    text = writer.format_record(record)

    assert 'data={"count": 2}' in text


def test_format_record_sorted_data_keys() -> None:
    """验证 format_record 会按键排序输出结构化数据"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        data={"b": 2, "a": 1},
    )

    text = writer.format_record(record)

    assert 'data={"a": 1, "b": 2}' in text


def test_format_record_without_optional_fields() -> None:
    """验证 format_record 在无可选字段时仅输出基础内容"""
    writer = LogWriter(LogConfig())
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    text = writer.format_record(record)

    assert text == "2026-05-12T10:30:45 | INFO | hello"


def test_write_disabled_file_output(project_root: Path) -> None:
    """验证关闭文件输出后不会创建输出目录"""
    writer = LogWriter(LogConfig(write_to_file=False))
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    result = writer.write(record)

    assert result.ok is True
    assert not (project_root / OUTPUT_DIR).exists()


def test_write_default_file_success(project_root: Path) -> None:
    """验证 write 会写入默认日志文件"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="warning",
        message="persist me",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="log",
    )

    result = writer.write(record)

    assert result.ok is True
    assert (project_root / writer.get_log_file_path()).exists()


def test_write_default_file_content(project_root: Path) -> None:
    """验证 write 会将日志内容写入默认日志文件"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="warning",
        message="persist me",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="log",
    )

    writer.write(record)

    content = (project_root / writer.get_log_file_path()).read_text(encoding="utf-8")

    assert "WARNING | log | persist me" in content


def test_write_task_file_success(project_root: Path) -> None:
    """验证 write 会写入任务专属日志文件"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="info",
        message="task log",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        task_id="task-001",
    )

    result = writer.write(record)

    assert result.ok is True
    assert (project_root / writer.get_log_file_path(record.task_id)).exists()


def test_write_task_file_not_default_file(project_root: Path) -> None:
    """验证写入任务日志时不会创建默认日志文件"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="info",
        message="task log",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        task_id="task-001",
    )

    writer.write(record)

    assert not (project_root / writer.get_log_file_path()).exists()


def test_write_open_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证打开日志文件抛出 OSError 时会返回失败结果"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", raise_open)

    result = writer.write(record)

    assert result.ok is False


def test_write_open_failure_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证打开日志文件失败时会返回固定错误码"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", raise_open)

    result = writer.write(record)

    assert result.code == "log_write_failed"


def test_write_open_failure_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证打开日志文件失败时会返回固定错误信息"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", raise_open)

    result = writer.write(record)

    assert result.error == "写入日志失败"


def test_write_open_failure_exception_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证打开日志文件失败时会返回异常文本"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", raise_open)

    result = writer.write(record)

    assert result.data["exception"] == "disk full"


def test_write_mkdir_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证创建日志目录失败时会返回失败结果"""
    writer = LogWriter(LogConfig(default_file_name="test.log"))
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = writer.write(record)

    assert result.ok is False
