from __future__ import annotations

from pathlib import Path
from typing import IO

import pytest
from gal_chara_skill.fs import json


def test_read(project_root: Path) -> None:
    """验证 read 会正确处理对象、数组、缺失文件、目录与非法 JSON"""
    object_path = project_root / "config.json"
    array_path = project_root / "list.json"
    broken_path = project_root / "broken.json"
    dir_path = project_root / "nested"
    missing_path = project_root / "missing.json"
    object_path.write_text('{"name": "alice"}', encoding="utf-8")
    array_path.write_text('[1, 2, 3]', encoding="utf-8")
    broken_path.write_text('{"name": }', encoding="utf-8")
    dir_path.mkdir()

    object_result = json.read(object_path)
    array_result = json.read(array_path)
    missing_result = json.read(missing_path)
    dir_result = json.read(dir_path)
    broken_result = json.read(broken_path)

    assert object_result.unwrap() == {"name": "alice"}
    assert array_result.unwrap() == [1, 2, 3]
    assert missing_result.ok is False
    assert dir_result.ok is False
    assert broken_result.ok is False


def test_read_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 read 在底层打开文件失败时会返回失败结果"""
    target = Path("config.json")

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

    result = json.read(target)

    assert result.ok is False


def test_write(project_root: Path) -> None:
    """验证 write 会写入可序列化数据并在文件末尾追加换行"""
    target = project_root / "config" / "settings.json"

    result = json.write(target, {"name": "alice", "age": 500})

    assert result.ok is True
    assert json.read(target).unwrap() == {"name": "alice", "age": 500}
    assert target.read_text(encoding="utf-8").endswith("\n")


def test_write_failure() -> None:
    """验证 write 在数据不可序列化时会返回失败结果"""
    result = json.write("config.json", {"items": {1, 2, 3}})

    assert result.ok is False
