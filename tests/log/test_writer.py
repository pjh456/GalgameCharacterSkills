from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import IO, Any

import pytest
from gal_chara_skill.core.paths import OUTPUT_DIR
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter


def test_get_log_file_path() -> None:
    """验证 get_log_file_path 会根据是否提供任务编号返回对应路径"""
    path_config = LogPathConfig(root_dir=Path("logs"), default_file_name="test.log")
    writer = LogWriter(LogPolicy(), path_config)

    assert writer.get_log_file_path() == Path("logs") / "test.log"
    assert writer.get_log_file_path("task-001") == Path("logs") / "task-001.log"


def test_format_record() -> None:
    """验证 format_record 会输出基础字段、可选字段与排序后的结构化数据"""
    writer = LogWriter(LogPolicy(), LogPathConfig())
    base_record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )
    optional_record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="fs",
        task_id="task-001",
        data={"b": 2, "a": 1},
    )

    base_text = writer.format_record(base_record)
    optional_text = writer.format_record(optional_record)

    assert base_text == f"{base_record.timestamp.isoformat(timespec='seconds')} | {base_record.level.upper()} | {base_record.message}"
    assert optional_text.startswith(
        f"{optional_record.timestamp.isoformat(timespec='seconds')} | {optional_record.level.upper()}"
    )
    assert f" | {optional_record.module} | " in optional_text
    assert f"task={optional_record.task_id}" in optional_text
    assert optional_text.index('"a": 1') < optional_text.index('"b": 2')


def test_write_disabled_file_output(project_root: Path) -> None:
    """验证关闭文件输出后不会创建输出目录"""
    writer = LogWriter(
        LogPolicy(write_to_file=False),
        LogPathConfig(root_dir=Path("logs")),
    )
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    result = writer.write(record)

    assert result.ok is True
    assert not (project_root / OUTPUT_DIR).exists()


def test_write_default_file(project_root: Path) -> None:
    """验证 write 会写入默认日志文件并写入格式化后的内容"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("output/logs"), default_file_name="test.log"),
    )
    record = LogRecord(
        level="warning",
        message="persist me",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="log",
    )

    result = writer.write(record)
    content = (project_root / writer.get_log_file_path()).read_text(encoding="utf-8")

    assert result.ok is True
    assert (project_root / writer.get_log_file_path()).exists()
    assert content == f"{writer.format_record(record)}\n"


def test_write_task_file(project_root: Path) -> None:
    """验证 write 会写入任务专属日志文件且不会创建默认日志文件"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("output/logs"), default_file_name="test.log"),
    )
    record = LogRecord(
        level="info",
        message="task log",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        task_id="task-001",
    )

    result = writer.write(record)

    assert result.ok is True
    assert (project_root / writer.get_log_file_path(record.task_id)).exists()
    assert not (project_root / writer.get_log_file_path()).exists()


def test_write_open_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证打开日志文件失败时会返回失败结果、错误信息与异常文本"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("logs"), default_file_name="test.log"),
    )
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
    assert result.error is not None
    assert result.data["exception"] is not None


def test_write_mkdir_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证创建日志目录失败时会返回失败结果"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("logs"), default_file_name="test.log"),
    )
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
