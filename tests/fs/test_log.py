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


def test_append(project_root: Path) -> None:
    """验证 append 会同时追加文本日志与结构化日志"""
    text_path = project_root / "logs" / "app.log"
    structured_path = project_root / "logs" / "app.jsonl"

    result = LogIO.append(
        text_path,
        structured_path,
        "2026-05-12T10:30:45 | INFO | hello",
        {"message": "hello"},
    )

    assert result.ok is True
    assert text_path.read_text(encoding="utf-8") == "2026-05-12T10:30:45 | INFO | hello\n"
    assert LogIO.read(structured_path).unwrap() == [{"message": "hello"}]


def test_append_text_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append 在文本日志写入失败时会直接返回该失败结果"""
    def fail_text_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "追加文本文件失败",
            code="fs_write_failed",
            path="logs/app.log",
            exception="disk full",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO._append_text_line", fail_text_append)

    result = LogIO.append(
        "logs/app.log",
        "logs/app.jsonl",
        "line",
        {"message": "hello"},
    )

    assert result.ok is False
    assert result.code == "fs_write_failed"
    assert result.data["path"] == "logs/app.log"
    assert result.data["exception"] == "disk full"


def test_append_structured_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append 在结构化日志写入失败时会返回该失败结果"""
    def fail_structured_append(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "JSONL 序列化失败",
            code="fs_parse_failed",
            path="logs/app.jsonl",
        )

    monkeypatch.setattr("gal_chara_skill.fs.log.LogIO._append_structured_record", fail_structured_append)

    result = LogIO.append(
        "logs/app.log",
        "logs/app.jsonl",
        "line",
        {"message": object()},
    )

    assert result.ok is False
    assert result.code == "fs_parse_failed"
    assert result.data["path"] == "logs/app.jsonl"
