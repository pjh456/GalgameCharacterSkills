from __future__ import annotations

from pathlib import Path
from typing import IO

import pytest

from gal_chara_skill.fs import text


def test_read_success(project_root: Path) -> None:
    """验证 read 会读取文本文件内容"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    result = text.read(target)

    assert result.unwrap() == "hello"


def test_read_missing_file(project_root: Path) -> None:
    """验证 read 在文件不存在时会返回失败结果"""
    result = text.read(project_root / "missing.txt")

    assert result.ok is False


def test_read_missing_file_code(project_root: Path) -> None:
    """验证 read 在文件不存在时会返回固定错误码"""
    result = text.read(project_root / "missing.txt")

    assert result.code == "fs_not_found"


def test_read_directory(project_root: Path) -> None:
    """验证 read 在目标路径为目录时会返回失败结果"""
    target = project_root / "nested"
    target.mkdir()

    result = text.read(target)

    assert result.ok is False


def test_read_directory_code(project_root: Path) -> None:
    """验证 read 在目标路径为目录时会返回固定错误码"""
    target = project_root / "nested"
    target.mkdir()

    result = text.read(target)

    assert result.code == "fs_not_file"


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


def test_read_failure_code(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证 read 在底层读取失败时会返回固定错误码"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    def raise_read_text(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        del self, encoding, errors
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(Path, "read_text", raise_read_text)

    result = text.read(target)

    assert result.code == "fs_read_failed"


def test_write_success(project_root: Path) -> None:
    """验证 write 会写入文本文件内容"""
    target = project_root / "notes" / "demo.txt"

    result = text.write(target, "hello")

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "hello"


def test_write_create_parent_false_existing_parent(project_root: Path) -> None:
    """验证 write 在关闭父目录创建时仍可写入已存在目录中的文件"""
    target = project_root / "notes" / "demo.txt"
    target.parent.mkdir()

    result = text.write(target, "hello", create_parent=False)

    assert result.ok is True


def test_write_create_parent_false_missing_parent(project_root: Path) -> None:
    """验证 write 在关闭父目录创建且目录不存在时会返回失败结果"""
    target = project_root / "notes" / "demo.txt"

    result = text.write(target, "hello", create_parent=False)

    assert result.ok is False


def test_write_failure_code(project_root: Path) -> None:
    """验证 write 在关闭父目录创建且目录不存在时会返回固定错误码"""
    target = project_root / "notes" / "demo.txt"

    result = text.write(target, "hello", create_parent=False)

    assert result.code == "fs_write_failed"


def test_write_parent_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 write 在父目录创建失败时会返回失败结果"""
    target = Path("notes/demo.txt")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = text.write(target, "hello")

    assert result.ok is False


def test_append_success(project_root: Path) -> None:
    """验证 append 会在文件末尾追加文本内容"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    result = text.append(target, " world")

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "hello world"


def test_append_create_parent(project_root: Path) -> None:
    """验证 append 会自动创建缺失的父目录"""
    target = project_root / "logs" / "app.log"

    result = text.append(target, "line 1")

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "line 1"


def test_append_parent_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append 在父目录创建失败时会返回失败结果"""
    target = Path("logs/app.log")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = text.append(target, "line 1")

    assert result.ok is False


def test_append_open_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 append 在打开文件失败时会返回失败结果"""
    target = Path("logs/app.log")

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

    result = text.append(target, "line 1", create_parent=False)

    assert result.ok is False
