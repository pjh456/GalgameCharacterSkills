from __future__ import annotations

from pathlib import Path

import pytest

from gal_chara_skill.fs import path


def test_resolve() -> None:
    """验证 resolve 会正确处理字符串路径与 Path 对象"""
    expected = Path("output/logs")

    assert path.resolve("output/logs") == expected
    assert path.resolve(expected) == expected


def test_exists(project_root: Path) -> None:
    """验证 exists 会区分已存在路径与不存在路径"""
    existing = project_root / "demo.txt"
    missing = project_root / "missing.txt"
    existing.write_text("hello", encoding="utf-8")

    assert path.exists(existing) is True
    assert path.exists(missing) is False


def test_is_file(project_root: Path) -> None:
    """验证 is_file 会区分文件与目录"""
    file_path = project_root / "demo.txt"
    dir_path = project_root / "nested"
    file_path.write_text("hello", encoding="utf-8")
    dir_path.mkdir()

    assert path.is_file(file_path) is True
    assert path.is_file(dir_path) is False


def test_is_dir(project_root: Path) -> None:
    """验证 is_dir 会区分目录与文件"""
    file_path = project_root / "demo.txt"
    dir_path = project_root / "nested"
    file_path.write_text("hello", encoding="utf-8")
    dir_path.mkdir()

    assert path.is_dir(dir_path) is True
    assert path.is_dir(file_path) is False


def test_ensure_dir(project_root: Path) -> None:
    """验证 ensure_dir 会创建目标目录并返回该目录路径"""
    target = project_root / "output" / "logs"

    result = path.ensure_dir(target)

    assert result.ok is True
    assert result.unwrap() == target
    assert target.exists()
    assert target.is_dir()


def test_ensure_dir_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 ensure_dir 在创建目录失败时会返回失败结果"""
    target = Path("output/logs")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = path.ensure_dir(target)

    assert result.ok is False


def test_ensure_parent_dir(project_root: Path) -> None:
    """验证 ensure_parent_dir 会创建父目录并返回父目录路径"""
    target = project_root / "output" / "logs" / "app.log"

    result = path.ensure_parent_dir(target)

    assert result.ok is True
    assert result.unwrap() == target.parent
    assert target.parent.exists()
    assert target.parent.is_dir()


def test_ensure_parent_dir_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 ensure_parent_dir 在创建父目录失败时会返回失败结果与父目录路径"""
    target = Path("output/logs/app.log")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = path.ensure_parent_dir(target)

    assert result.ok is False
    assert result.data["path"] == str(target.parent)
