from __future__ import annotations

from pathlib import Path

import pytest

from gal_chara_skill.fs import path


def test_resolve_string() -> None:
    """验证 resolve 会将字符串路径转换为 Path 对象"""
    result = path.resolve("output/logs")

    assert result == Path("output/logs")


def test_resolve_path() -> None:
    """验证 resolve 会保留传入的 Path 路径值"""
    result = path.resolve(Path("output/logs"))

    assert result == Path("output/logs")


def test_exists_true(project_root: Path) -> None:
    """验证 exists 在路径存在时返回 True"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    assert path.exists(target) is True


def test_exists_false(project_root: Path) -> None:
    """验证 exists 在路径不存在时返回 False"""
    assert path.exists(project_root / "missing.txt") is False


def test_is_file_true(project_root: Path) -> None:
    """验证 is_file 在目标为文件时返回 True"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    assert path.is_file(target) is True


def test_is_file_false_for_directory(project_root: Path) -> None:
    """验证 is_file 在目标为目录时返回 False"""
    target = project_root / "nested"
    target.mkdir()

    assert path.is_file(target) is False


def test_is_dir_true(project_root: Path) -> None:
    """验证 is_dir 在目标为目录时返回 True"""
    target = project_root / "nested"
    target.mkdir()

    assert path.is_dir(target) is True


def test_is_dir_false_for_file(project_root: Path) -> None:
    """验证 is_dir 在目标为文件时返回 False"""
    target = project_root / "demo.txt"
    target.write_text("hello", encoding="utf-8")

    assert path.is_dir(target) is False


def test_ensure_dir_success(project_root: Path) -> None:
    """验证 ensure_dir 会创建目标目录并返回成功结果"""
    target = project_root / "output" / "logs"

    result = path.ensure_dir(target)

    assert result.ok is True
    assert target.exists()
    assert target.is_dir()


def test_ensure_dir_value(project_root: Path) -> None:
    """验证 ensure_dir 成功时会返回创建后的目录路径"""
    target = project_root / "output" / "logs"

    result = path.ensure_dir(target)

    assert result.unwrap() == target


def test_ensure_dir_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 ensure_dir 在创建目录失败时会返回失败结果"""
    target = Path("output/logs")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = path.ensure_dir(target)

    assert result.ok is False


def test_ensure_dir_failure_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 ensure_dir 创建目录失败时会返回固定错误码"""
    target = Path("output/logs")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = path.ensure_dir(target)

    assert result.code == "fs_write_failed"


def test_ensure_parent_dir_success(project_root: Path) -> None:
    """验证 ensure_parent_dir 会创建目标文件的父目录"""
    target = project_root / "output" / "logs" / "app.log"

    result = path.ensure_parent_dir(target)

    assert result.ok is True
    assert target.parent.exists()
    assert target.parent.is_dir()


def test_ensure_parent_dir_value(project_root: Path) -> None:
    """验证 ensure_parent_dir 成功时会返回父目录路径"""
    target = project_root / "output" / "logs" / "app.log"

    result = path.ensure_parent_dir(target)

    assert result.unwrap() == target.parent


def test_ensure_parent_dir_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 ensure_parent_dir 在创建父目录失败时会返回失败结果"""
    target = Path("output/logs/app.log")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = path.ensure_parent_dir(target)

    assert result.ok is False


def test_ensure_parent_dir_failure_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 ensure_parent_dir 创建父目录失败时会返回父目录路径"""
    target = Path("output/logs/app.log")

    def raise_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        del self, mode, parents, exist_ok
        raise OSError("cannot create parent dir")

    monkeypatch.setattr(Path, "mkdir", raise_mkdir)

    result = path.ensure_parent_dir(target)

    assert result.data["path"] == str(target.parent)
