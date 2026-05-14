from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.core.result import Result
from gal_chara_skill.fs import JsonlIO
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.writer import LogWriter


def test_get_log_file_path() -> None:
    """验证 writer 会根据是否提供任务编号返回文本与结构化日志路径"""
    path_config = LogPathConfig(root_dir=Path("logs"), default_file_name="test.log")
    writer = LogWriter(LogPolicy(), path_config)

    assert writer.get_log_file_path() == Path("logs") / "test.log"
    assert writer.get_log_file_path("task-001") == Path("logs") / "task-001.log"
    assert writer.get_structured_log_file_path() == Path("logs") / "test.jsonl"
    assert writer.get_structured_log_file_path("task-001") == Path("logs") / "task-001.jsonl"


def test_write_disabled_file_output(project_root: Path) -> None:
    """验证关闭文件输出后不会创建输出目录"""
    output_dir = Path("output")
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
    assert not (project_root / output_dir).exists()


def test_write_default_file(project_root: Path) -> None:
    """验证 write 会同时写入文本日志和结构化日志"""
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
    text_content = (project_root / writer.get_log_file_path()).read_text(encoding="utf-8")
    records = JsonlIO.read(project_root / writer.get_structured_log_file_path()).unwrap()

    assert result.ok is True
    assert (project_root / writer.get_log_file_path()).exists()
    assert (project_root / writer.get_structured_log_file_path()).exists()
    assert text_content == f"{record.to_text()}\n"
    assert records == [record.to_dict()]


def test_write_task_file(project_root: Path) -> None:
    """验证 write 会写入任务专属文本日志和结构化日志且不会创建默认日志文件"""
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
    assert (project_root / writer.get_structured_log_file_path(record.task_id)).exists()
    assert not (project_root / writer.get_log_file_path()).exists()
    assert not (project_root / writer.get_structured_log_file_path()).exists()


def test_write_text_log_failure(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """验证文本日志追加失败后会按结构化日志重建文本视图并返回成功"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("logs"), default_file_name="test.log"),
    )
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def fail_text_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "写入文本文件失败",
            code="fs_write_failed",
            path=str(writer.get_log_file_path()),
            exception="disk full",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO.append_log", fail_text_append)

    result = writer.write(record)

    assert result.ok is True
    assert result.data["log_rebuilt"] is True
    assert result.data["log_append_error"] == "写入文本文件失败"
    assert (project_root / writer.get_log_file_path()).read_text(encoding="utf-8") == f"{record.to_text()}\n"


def test_write_structured_log_failure(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """验证结构化日志写入失败时会返回失败结果且不会生成文本日志"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("logs"), default_file_name="test.log"),
    )
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def fail_structured_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "cannot append",
            code="fs_write_failed",
            path=str(writer.get_structured_log_file_path()),
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO.append_record", fail_structured_append)

    result = writer.write(record)

    assert result.ok is False
    assert result.code == "fs_write_failed"
    assert result.data["path"] == str(writer.get_structured_log_file_path())
    assert not (project_root / writer.get_log_file_path()).exists()


def test_write_structured_log_exception(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """验证结构化日志写入抛异常时会返回日志写入失败结果并附带 JSONL 路径"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("logs"), default_file_name="test.log"),
    )
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def fail_structured_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "写入结构化日志失败",
            code="fs_write_failed",
            path=str(writer.get_structured_log_file_path()),
            exception="structured disk full",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO.append_record", fail_structured_append)

    result = writer.write(record)

    assert result.ok is False
    assert result.code == "fs_write_failed"
    assert result.data["path"] == str(writer.get_structured_log_file_path())
    assert result.data["exception"] == "structured disk full"
    assert not (project_root / writer.get_log_file_path()).exists()


def test_write_text_log_rewrite_failure(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """验证文本追加与重建都失败时，结构化主数据仍保留且结果标记为退化成功"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("logs"), default_file_name="test.log"),
    )
    record = LogRecord(
        level="error",
        message="boom",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    def fail_text_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "写入文本文件失败",
            code="fs_write_failed",
            path=str(writer.get_log_file_path()),
            exception="disk full",
        )

    def fail_rewrite(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "重建日志视图失败",
            code="fs_write_failed",
            path=str(writer.get_log_file_path()),
            exception="still full",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO.append_log", fail_text_append)
    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO.rewrite_log", fail_rewrite)

    result = writer.write(record)

    assert result.ok is True
    assert result.data["log_view_degraded"] is True
    assert result.data["log_append_error"] == "写入文本文件失败"
    assert result.data["log_rewrite_error"] == "重建日志视图失败"
    assert JsonlIO.read(project_root / writer.get_structured_log_file_path()).unwrap() == [record.to_dict()]


def test_write_uses_shared_path_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证不同 LogWriter 实例写同一路径时会复用同一把锁"""
    root_dir = Path("logs")
    first = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=root_dir, default_file_name="shared.log"),
    )
    second = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=root_dir, default_file_name="shared.log"),
    )

    captured_locks: list[threading.Lock] = []
    original_get_lock = LogWriter._get_lock

    def capture_lock(cls: type[LogWriter], path: Path) -> threading.Lock:
        lock = original_get_lock(path)
        captured_locks.append(lock)
        return lock

    monkeypatch.setattr(LogWriter, "_get_lock", classmethod(capture_lock))

    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
    )

    first.write(record)
    second.write(record)

    assert len(captured_locks) == 2
    assert captured_locks[0] is captured_locks[1]


def test_write_serializes_concurrent_writes(project_root: Path) -> None:
    """验证并发写同一日志文件时，每条日志都完整落盘"""
    writer = LogWriter(
        LogPolicy(),
        LogPathConfig(root_dir=Path("output/logs"), default_file_name="shared.log"),
    )
    total_records = 20

    def write_one(index: int) -> None:
        record = LogRecord(
            level="info",
            message=f"line-{index}",
            timestamp=datetime(2026, 5, 12, 10, 30, 45),
        )
        result = writer.write(record)
        assert result.ok is True

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(write_one, index) for index in range(total_records)]
        for future in futures:
            future.result()

    text_log_file = project_root / "output/logs/shared.log"
    structured_log_file = project_root / "output/logs/shared.jsonl"
    lines = text_log_file.read_text(encoding="utf-8").splitlines()
    records = JsonlIO.read(structured_log_file).unwrap()

    assert len(lines) == total_records
    assert len(records) == total_records
    assert all("INFO" in line for line in lines)
    assert {record["message"] for record in records} == {
        f"line-{index}" for index in range(total_records)
    }
