from __future__ import annotations

from datetime import datetime
from pathlib import Path

from gal_chara_skill.conf.module.log import LogPathConfig
from gal_chara_skill.fs import JsonlIO
from gal_chara_skill.log.models import LogRecord
from gal_chara_skill.log.reader import LogReader
from gal_chara_skill.log.writer import LogWriter
from gal_chara_skill.conf.module.log import LogPolicy


def test_read_missing_file_returns_empty_list(project_root: Path, log_path_config: LogPathConfig) -> None:
    del project_root
    reader = LogReader(log_path_config)

    result = reader.read()

    assert result.ok is True
    assert result.unwrap() == []


def test_read_records(project_root: Path, log_path_config: LogPathConfig) -> None:
    writer = LogWriter(LogPolicy(), log_path_config)
    reader = LogReader(log_path_config)
    record = LogRecord(
        level="info",
        message="hello",
        timestamp=datetime(2026, 5, 12, 10, 30, 45),
        module="log",
    )

    writer.write(record)

    assert reader.read().unwrap() == [record]
    assert (project_root / writer.get_log_file_path()).exists()
    assert (project_root / writer.get_structured_log_file_path()).exists()


def test_read_invalid_jsonl(project_root: Path, log_path_config: LogPathConfig) -> None:
    reader = LogReader(log_path_config)
    target = project_root / reader.get_log_file_path()
    target.parent.mkdir(parents=True)
    target.write_text("{broken}\n", encoding="utf-8")

    result = reader.read()

    assert result.ok is False
    assert result.code == "fs_parse_failed"


def test_read_invalid_record(project_root: Path, log_path_config: LogPathConfig) -> None:
    reader = LogReader(log_path_config)
    JsonlIO.write(project_root / reader.get_log_file_path(), [{"level": "info"}])

    result = reader.read()

    assert result.ok is False
    assert result.code == "log_parse_failed"
    assert result.data["index"] == 0


def test_query(project_root: Path, log_path_config: LogPathConfig) -> None:
    del project_root
    writer = LogWriter(LogPolicy(), log_path_config)
    reader = LogReader(log_path_config)
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


def test_query_returns_read_failure(project_root: Path, log_path_config: LogPathConfig) -> None:
    reader = LogReader(log_path_config)
    target = project_root / reader.get_log_file_path()
    target.parent.mkdir(parents=True)
    target.write_text("{broken}\n", encoding="utf-8")

    result = reader.query(level="info")

    assert result.ok is False
    assert result.code == "fs_parse_failed"


def test_aread(project_root: Path, log_path_config: LogPathConfig) -> None:
    import asyncio

    log_dir = log_path_config.root_dir
    log_dir.mkdir(parents=True)
    config = log_path_config
    log_file = config.root_dir / "test.jsonl"
    log_file.write_text(
        '{"level":"info","message":"hello","timestamp":"2026-05-12T10:30:45","module":null,"task_id":null,"data":{}}\n',
        encoding="utf-8",
    )

    reader = LogReader(config)

    async def main() -> None:
        result = await reader.aread()
        assert result.ok is True
        assert len(result.unwrap()) == 1
        assert result.unwrap()[0].message == "hello"

    asyncio.run(main())


def test_aquery(project_root: Path, log_path_config: LogPathConfig) -> None:
    import asyncio

    log_dir = log_path_config.root_dir
    log_dir.mkdir(parents=True)
    config = log_path_config
    log_file = config.root_dir / "test.jsonl"
    log_file.write_text(
        '{"level":"info","message":"hello","timestamp":"2026-05-12T10:30:45","module":null,"task_id":null,"data":{}}\n'
        '{"level":"error","message":"world","timestamp":"2026-05-12T10:31:00","module":null,"task_id":null,"data":{}}\n',
        encoding="utf-8",
    )

    reader = LogReader(config)

    async def main() -> None:
        result = await reader.aquery(level="error")
        assert result.ok is True
        records = result.unwrap()
        assert len(records) == 1
        assert records[0].message == "world"

    asyncio.run(main())
