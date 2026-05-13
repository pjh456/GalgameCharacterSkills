from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gal_chara_skill.conf.module.log import LogPathConfig
from gal_chara_skill.fs import JsonlIO
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.reader import LogReader
from gal_chara_skill.log.writer import LogWriter
from gal_chara_skill.conf.module.log import LogPolicy


def test_read_missing_file_returns_empty_list(project_root: Path) -> None:
    """验证日志文件不存在时 read 返回空列表"""
    del project_root
    reader = LogReader(LogPathConfig(root_dir=Path("output/logs")))

    result = reader.read()

    assert result.ok is True
    assert result.unwrap() == []


def test_read_records(project_root: Path) -> None:
    """验证 reader 可以读取 writer 写出的 JSONL 日志记录"""
    path_config = LogPathConfig(root_dir=Path("output/logs"), default_file_name="app.log")
    writer = LogWriter(LogPolicy(), path_config)
    reader = LogReader(path_config)
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="log",
    )

    writer.write(record)

    assert reader.read().unwrap() == [record]
    assert (project_root / "output/logs/app.log").exists()


def test_read_invalid_jsonl(project_root: Path) -> None:
    """验证 reader 在底层 JSONL 无法解析时返回失败结果"""
    path_config = LogPathConfig(root_dir=Path("output/logs"), default_file_name="broken.log")
    reader = LogReader(path_config)
    target = project_root / reader.get_log_file_path()
    target.parent.mkdir(parents=True)
    target.write_text("{broken}\n", encoding="utf-8")

    result = reader.read()

    assert result.ok is False
    assert result.code == "fs_parse_failed"


def test_read_invalid_record(project_root: Path) -> None:
    """验证 reader 在日志记录结构错误时返回失败结果并附带记录索引"""
    path_config = LogPathConfig(root_dir=Path("output/logs"), default_file_name="invalid.log")
    reader = LogReader(path_config)
    JsonlIO.write(project_root / reader.get_log_file_path(), [{"level": "info"}])

    result = reader.read()

    assert result.ok is False
    assert result.code == "log_parse_failed"
    assert result.data["index"] == 0


def test_query(project_root: Path) -> None:
    """验证 query 可以按任务、级别与模块过滤日志记录"""
    del project_root
    path_config = LogPathConfig(root_dir=Path("output/logs"), default_file_name="app.log")
    writer = LogWriter(LogPolicy(), path_config)
    reader = LogReader(path_config)
    first = LogRecord(
        level="info",
        message="first",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="fs",
    )
    second = LogRecord(
        level="error",
        message="second",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="log",
    )
    task_record = LogRecord(
        level="info",
        message="task",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="fs",
        task_id="task-001",
    )

    writer.write(first)
    writer.write(second)
    writer.write(task_record)

    assert reader.query(level="info").unwrap() == [first]
    assert reader.query(module="log").unwrap() == [second]
    assert reader.query(task_id="task-001", level="info", module="fs").unwrap() == [task_record]


def test_query_returns_read_failure(project_root: Path) -> None:
    """验证 query 会透传 read 的失败结果"""
    path_config = LogPathConfig(root_dir=Path("output/logs"), default_file_name="broken.log")
    reader = LogReader(path_config)
    target = project_root / reader.get_log_file_path()
    target.parent.mkdir(parents=True)
    target.write_text("{broken}\n", encoding="utf-8")

    result = reader.query(level="info")

    assert result.ok is False
    assert result.code == "fs_parse_failed"
