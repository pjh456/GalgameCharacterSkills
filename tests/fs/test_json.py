from __future__ import annotations

from pathlib import Path
from typing import IO

import pytest
from gal_chara_skill.fs import json


def test_read_success_object(project_root: Path) -> None:
    """验证 read 会读取 JSON 对象内容"""
    target = project_root / "config.json"
    target.write_text('{"name": "alice"}', encoding="utf-8")

    result = json.read(target)

    assert result.unwrap() == {"name": "alice"}


def test_read_success_array(project_root: Path) -> None:
    """验证 read 会读取 JSON 数组内容"""
    target = project_root / "list.json"
    target.write_text('[1, 2, 3]', encoding="utf-8")

    result = json.read(target)

    assert result.unwrap() == [1, 2, 3]


def test_read_missing_file(project_root: Path) -> None:
    """验证 read 在文件不存在时会返回失败结果"""
    result = json.read(project_root / "missing.json")

    assert result.ok is False


def test_read_missing_file_code(project_root: Path) -> None:
    """验证 read 在文件不存在时会返回固定错误码"""
    result = json.read(project_root / "missing.json")

    assert result.code == "fs_not_found"


def test_read_directory(project_root: Path) -> None:
    """验证 read 在目标为目录时会返回失败结果"""
    target = project_root / "nested"
    target.mkdir()

    result = json.read(target)

    assert result.ok is False


def test_read_directory_code(project_root: Path) -> None:
    """验证 read 在目标为目录时会返回固定错误码"""
    target = project_root / "nested"
    target.mkdir()

    result = json.read(target)

    assert result.code == "fs_not_file"


def test_read_invalid_json(project_root: Path) -> None:
    """验证 read 在 JSON 内容非法时会返回失败结果"""
    target = project_root / "broken.json"
    target.write_text('{"name": }', encoding="utf-8")

    result = json.read(target)

    assert result.ok is False


def test_read_invalid_json_code(project_root: Path) -> None:
    """验证 read 在 JSON 内容非法时会返回固定错误码"""
    target = project_root / "broken.json"
    target.write_text('{"name": }', encoding="utf-8")

    result = json.read(target)

    assert result.code == "fs_parse_failed"


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


def test_read_failure_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 read 在底层打开文件失败时会返回固定错误码"""
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

    assert result.code == "fs_read_failed"


def test_write_success(project_root: Path) -> None:
    """验证 write 会将 Python 对象写入 JSON 文件"""
    target = project_root / "config" / "settings.json"

    result = json.write(target, {"name": "alice", "age": 500})

    assert result.ok is True
    assert json.read(target).unwrap() == {"name": "alice", "age": 500}


def test_write_trailing_newline(project_root: Path) -> None:
    """验证 write 写出的 JSON 文件末尾会带换行"""
    target = project_root / "config.json"

    json.write(target, {"name": "alice"})

    assert target.read_text(encoding="utf-8").endswith("\n")


def test_write_serialize_failure() -> None:
    """验证 write 在数据不可序列化时会返回失败结果"""
    result = json.write("config.json", {"items": {1, 2, 3}})

    assert result.ok is False


def test_write_serialize_failure_code() -> None:
    """验证 write 在数据不可序列化时会返回固定错误码"""
    result = json.write("config.json", {"items": {1, 2, 3}})

    assert result.code == "fs_parse_failed"
