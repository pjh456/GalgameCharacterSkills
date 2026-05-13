from __future__ import annotations

from pathlib import Path
from typing import IO

import pytest
from gal_chara_skill.fs import yaml


def test_read(project_root: Path) -> None:
    """验证 read 会正确处理对象、数组、空文件、缺失文件、目录与非法 YAML"""
    object_path = project_root / "config.yaml"
    array_path = project_root / "list.yaml"
    empty_path = project_root / "empty.yaml"
    broken_path = project_root / "broken.yaml"
    dir_path = project_root / "nested"
    missing_path = project_root / "missing.yaml"
    object_path.write_text("name: alice\nage: 500\n", encoding="utf-8")
    array_path.write_text("- 1\n- 2\n- 3\n", encoding="utf-8")
    empty_path.write_text("", encoding="utf-8")
    broken_path.write_text("name: [alice\n", encoding="utf-8")
    dir_path.mkdir()

    object_result = yaml.read(object_path)
    array_result = yaml.read(array_path)
    empty_result = yaml.read(empty_path)
    missing_result = yaml.read(missing_path)
    dir_result = yaml.read(dir_path)
    broken_result = yaml.read(broken_path)

    assert object_result.unwrap() == {"name": "alice", "age": 500}
    assert array_result.unwrap() == [1, 2, 3]
    assert empty_result.ok is True
    assert empty_result.value is None
    assert missing_result.ok is False
    assert dir_result.ok is False
    assert broken_result.ok is False


def test_read_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 read 在底层打开文件失败时会返回失败结果"""
    target = Path("config.yaml")

    def raise_open(
        self: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[str]:
        del self, mode, buffering, encoding, errors, newline
        raise OSError("disk error")

    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(Path, "open", raise_open)

    result = yaml.read(target)

    assert result.ok is False


def test_write(project_root: Path) -> None:
    """验证 write 会写入可反序列化的 YAML 数据"""
    target = project_root / "config" / "settings.yaml"

    result = yaml.write(target, {"name": "alice", "age": 500})

    assert result.ok is True
    assert yaml.read(target).unwrap() == {"name": "alice", "age": 500}
    assert target.read_text(encoding="utf-8").endswith("\n")


def test_write_atomic_replace_failure(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证 YAML 原子写入在替换失败时不会破坏原有文件内容"""
    target = project_root / "config.yaml"
    target.write_text("name: old\n", encoding="utf-8")

    def raise_replace(src: str | Path, dst: str | Path) -> None:
        del src, dst
        raise OSError("cannot replace file")

    monkeypatch.setattr("gal_chara_skill.fs.text.os.replace", raise_replace)

    result = yaml.write(target, {"name": "new"}, create_parent=False)

    assert result.ok is False
    assert yaml.read(target).unwrap() == {"name": "old"}


def test_write_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 write 在数据不可序列化时会返回失败结果"""

    def raise_dump(*args: object, **kwargs: object) -> str:
        del args, kwargs
        raise yaml.yaml.YAMLError("cannot dump")

    monkeypatch.setattr("gal_chara_skill.fs.yaml.yaml.safe_dump", raise_dump)

    result = yaml.write("config.yaml", {"name": "alice"})

    assert result.ok is False
