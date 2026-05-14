from __future__ import annotations

from pathlib import Path

import pytest

from gal_chara_skill.core.result import Result
from gal_chara_skill.fs import LogIO


def test_read(project_root: Path) -> None:
    """验证 read 会读取结构化日志文件中的 JSONL 记录"""
    target = project_root / "logs" / "app.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text('{"message": "hello"}\n{"message": "world"}\n', encoding="utf-8")

    result = LogIO.read(target)

    assert result.ok is True
    assert result.unwrap() == [{"message": "hello"}, {"message": "world"}]


def test_append_record(project_root: Path) -> None:
    """验证 append_record 会向结构化日志追加一条 JSONL 记录"""
    target = project_root / "logs" / "app.jsonl"

    result = LogIO.append_record(
        target,
        {"message": "hello"},
    )

    assert result.ok is True
    assert LogIO.read(target).unwrap() == [{"message": "hello"}]


def test_append_record_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append_record 会透传底层 JSONL 追加失败"""
    def fail_record_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "JSONL 序列化失败",
            code="fs_parse_failed",
            path="logs/app.jsonl",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.JsonlIO.append", fail_record_append)

    result = LogIO.append_record(
        "logs/app.jsonl",
        {"message": "hello"},
    )

    assert result.ok is False
    assert result.code == "fs_parse_failed"
    assert result.data["path"] == "logs/app.jsonl"


def test_append_log(project_root: Path) -> None:
    """验证 append_log 会向文本日志追加一行内容并自动补换行"""
    target = project_root / "logs" / "app.log"

    result = LogIO.append_log(target, "2026-05-12T10:30:45 | INFO | hello", encoding="utf-8")

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "2026-05-12T10:30:45 | INFO | hello\n"


def test_append_log_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append_log 会透传底层文本追加失败"""
    def fail_log_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "追加文本文件失败",
            code="fs_write_failed",
            path="logs/app.log",
            exception="disk full",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.TextIO.append", fail_log_append)

    result = LogIO.append_log(
        "logs/app.log",
        "line",
        encoding="utf-8",
    )

    assert result.ok is False
    assert result.code == "fs_write_failed"
    assert result.data["path"] == "logs/app.log"
    assert result.data["exception"] == "disk full"


def test_rewrite_log(project_root: Path) -> None:
    """验证 rewrite_log 会覆盖写入完整文本日志内容"""
    target = project_root / "logs" / "app.log"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")

    result = LogIO.rewrite_log(
        target,
        ["line-1", "line-2"],
        encoding="utf-8",
    )

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "line-1\nline-2\n"
