from __future__ import annotations

from pathlib import Path
from typing import IO

import pytest

from gal_chara_skill.fs import text


def test_read(project_root: Path) -> None:
    """验证 read 会正确处理成功、文件不存在与目标为目录的情况"""
    file_path = project_root / "demo.txt"
    dir_path = project_root / "nested"
    missing_path = project_root / "missing.txt"
    file_path.write_text("hello", encoding="utf-8")
    dir_path.mkdir()

    success = text.read(file_path)
    missing = text.read(missing_path)
    directory = text.read(dir_path)

    assert success.unwrap() == "hello"
    assert missing.ok is False
    assert directory.ok is False


def test_read_failure(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证 read 在底层读取失败时会返回失败结果"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    def raise_read_text(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        del self, encoding, errors
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(Path, "read_text", raise_read_text)

    result = text.read(target)

    assert result.ok is False


def test_write(project_root: Path) -> None:
    """验证 write 会在不同父目录创建模式下正确写入或失败"""
    auto_create_target = project_root / "notes" / "auto.txt"
    existing_parent_target = project_root / "existing" / "demo.txt"
    missing_parent_target = project_root / "missing-parent" / "demo.txt"
    existing_parent_target.parent.mkdir()

    auto_create = text.write(auto_create_target, "hello")
    existing_parent = text.write(existing_parent_target, "hello", create_parent=False)
    missing_parent = text.write(missing_parent_target, "hello", create_parent=False)

    assert auto_create.ok is True
    assert auto_create_target.read_text(encoding="utf-8") == "hello"
    assert existing_parent.ok is True
    assert missing_parent.ok is False


def test_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 write 在父目录创建失败时会返回失败结果"""
    target = Path("notes/demo.txt")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = text.write(target, "hello")

    assert result.ok is False


def test_append(project_root: Path) -> None:
    """验证 append 会正确追加内容并可自动创建父目录"""
    existing_target = project_root / "demo.txt"
    create_parent_target = project_root / "logs" / "app.log"
    existing_target.write_text("hello", encoding="utf-8")

    existing_result = text.append(existing_target, " world")
    create_parent_result = text.append(create_parent_target, "line 1")

    assert existing_result.ok is True
    assert existing_target.read_text(encoding="utf-8") == "hello world"
    assert create_parent_result.ok is True
    assert create_parent_target.read_text(encoding="utf-8") == "line 1"


def test_append_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append 在父目录创建失败或打开文件失败时会返回失败结果"""
    parent_failure_target = Path("logs/app.log")
    open_failure_target = Path("logs/app.log")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)
    parent_failure = text.append(parent_failure_target, "line 1")

    monkeypatch.undo()

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[str]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", raise_open)
    open_failure = text.append(open_failure_target, "line 1", create_parent=False)

    assert parent_failure.ok is False
    assert open_failure.ok is False
