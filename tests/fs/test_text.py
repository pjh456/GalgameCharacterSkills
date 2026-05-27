from __future__ import annotations

from pathlib import Path
from typing import IO, Optional

import pytest

from gal_chara_skill.core.result import Result
from gal_chara_skill.fs import TextIO


def test_read(project_root: Path) -> None:
    """验证 read 会正确处理成功、文件不存在与目标为目录的情况"""
    file_path = project_root / "demo.txt"
    dir_path = project_root / "nested"
    missing_path = project_root / "missing.txt"
    file_path.write_text("hello", encoding="utf-8")
    dir_path.mkdir()

    success = TextIO.read(file_path)
    missing = TextIO.read(missing_path)
    directory = TextIO.read(dir_path)

    assert success.unwrap() == "hello"
    assert missing.ok is False
    assert directory.ok is False


def test_read_failure(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证 read 在底层读取失败时会返回失败结果"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    def raise_read_text(self: Path, encoding: Optional[str] = None, errors: Optional[str] = None) -> str:
        del self, encoding, errors
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(Path, "read_text", raise_read_text)

    result = TextIO.read(target)

    assert result.ok is False


def test_write(project_root: Path) -> None:
    """验证 write 会在不同父目录创建模式下正确写入或失败"""
    auto_create_target = project_root / "notes" / "auto.txt"
    existing_parent_target = project_root / "existing" / "demo.txt"
    missing_parent_target = project_root / "missing-parent" / "demo.txt"
    existing_parent_target.parent.mkdir()

    auto_create = TextIO.write(auto_create_target, "hello")
    existing_parent = TextIO.write(existing_parent_target, "hello", create_parent=False)
    missing_parent = TextIO.write(missing_parent_target, "hello", create_parent=False)

    assert auto_create.ok is True
    assert auto_create_target.read_text(encoding="utf-8") == "hello"
    assert existing_parent.ok is True
    assert missing_parent.ok is False


def test_write_atomic_overwrite(project_root: Path) -> None:
    """验证 write 默认使用原子覆盖写入更新已有文件"""
    target = project_root / "notes" / "atomic.txt"
    target.parent.mkdir()
    target.write_text("old", encoding="utf-8")

    result = TextIO.write(target, "new")

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "new"


def test_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 write 在父目录创建失败时会返回失败结果"""
    target = Path("notes/demo.txt")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = TextIO.write(target, "hello")

    assert result.ok is False


def test_write_atomic_replace_failure(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证原子写入在替换目标文件失败时会返回失败结果且保留原文件内容"""
    target = project_root / "notes" / "demo.txt"
    target.parent.mkdir()
    target.write_text("old", encoding="utf-8")

    def raise_replace(src: str | Path, dst: str | Path) -> None:
        del src, dst
        raise OSError("cannot replace file")

    monkeypatch.setattr("gal_chara_skill.fs.text.os.replace", raise_replace)
    monkeypatch.setattr("shutil.copy2", raise_replace)

    result = TextIO.write(target, "new")

    assert result.ok is False
    assert target.read_text(encoding="utf-8") == "old"


def test_append(project_root: Path) -> None:
    """验证 append 会正确追加内容并可自动创建父目录"""
    existing_target = project_root / "demo.txt"
    create_parent_target = project_root / "logs" / "app.log"
    existing_target.write_text("hello", encoding="utf-8")

    existing_result = TextIO.append(existing_target, " world")
    create_parent_result = TextIO.append(create_parent_target, "line 1")

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
    parent_failure = TextIO.append(parent_failure_target, "line 1")

    monkeypatch.undo()

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO[str]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", raise_open)
    open_failure = TextIO.append(open_failure_target, "line 1", create_parent=False)

    assert parent_failure.ok is False
    assert open_failure.ok is False


def test_aread(project_root: Path) -> None:
    import asyncio

    file_path = project_root / "demo.txt"
    file_path.write_text("hello", encoding="utf-8")

    async def main() -> None:
        result = await TextIO.aread(file_path)
        assert result.unwrap() == "hello"

    asyncio.run(main())


def test_awrite(project_root: Path) -> None:
    import asyncio

    file_path = project_root / "notes" / "async.txt"

    async def main() -> None:
        result = await TextIO.awrite(file_path, "async content")  # pyright: ignore[reportGeneralTypeIssues]
        assert result.ok is True
        assert file_path.read_text(encoding="utf-8") == "async content"

    asyncio.run(main())


def test_aappend(project_root: Path) -> None:
    import asyncio

    file_path = project_root / "demo.txt"
    file_path.write_text("hello", encoding="utf-8")

    async def main() -> None:
        result = await TextIO.aappend(file_path, " world")  # pyright: ignore[reportGeneralTypeIssues]
        assert result.ok is True
        assert file_path.read_text(encoding="utf-8") == "hello world"

    asyncio.run(main())


def test_read_auto_encodings_utf8(project_root: Path) -> None:
    file_path = project_root / "demo.txt"
    file_path.write_text("hello", encoding="utf-8")

    result = TextIO.read_auto_encodings(file_path)
    assert result.ok is True
    assert result.unwrap() == "hello"


def test_read_auto_encodings_gb18030(project_root: Path) -> None:
    file_path = project_root / "demo.txt"
    content = "你好，世界！\n文件内容测试。".encode("gb18030")
    file_path.write_bytes(content)

    result = TextIO.read_auto_encodings(file_path)
    assert result.ok is True
    assert "你好" in result.unwrap()


def test_read_auto_encodings_all_fail(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    file_path = project_root / "demo.txt"
    file_path.write_text("hello", encoding="utf-8")

    def fail_read(*args: object, **kwargs: object) -> Result[str]:
        return Result.failure("fail", code="fs_read_failed")

    monkeypatch.setattr(TextIO, "read", fail_read)

    result = TextIO.read_auto_encodings(file_path)
    assert result.ok is False
    assert result.code == "fs_read_failed"
