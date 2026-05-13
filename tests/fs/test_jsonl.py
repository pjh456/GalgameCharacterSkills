from __future__ import annotations

from pathlib import Path
from typing import IO

import pytest
from gal_chara_skill.fs import jsonl


def test_read(project_root: Path) -> None:
    """验证 read 会正确处理多行对象、数组、空行、缺失文件、目录与非法 JSONL"""
    target = project_root / "records.jsonl"
    broken_path = project_root / "broken.jsonl"
    dir_path = project_root / "nested"
    missing_path = project_root / "missing.jsonl"
    target.write_text('{"name": "alice"}\n\n[1, 2, 3]\n', encoding="utf-8")
    broken_path.write_text('{"name": "alice"}\n{"broken": }\n', encoding="utf-8")
    dir_path.mkdir()

    read_result = jsonl.read(target)
    missing_result = jsonl.read(missing_path)
    dir_result = jsonl.read(dir_path)
    broken_result = jsonl.read(broken_path)

    assert read_result.unwrap() == [{"name": "alice"}, [1, 2, 3]]
    assert missing_result.ok is False
    assert dir_result.ok is False
    assert broken_result.ok is False
    assert broken_result.code == "fs_parse_failed"
    assert broken_result.data["line"] == 2


def test_read_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """验证 read 在底层打开文件失败时会返回失败结果"""
    target = Path("records.jsonl")

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

    result = jsonl.read(target)

    assert result.ok is False
    assert result.code == "fs_read_failed"


def test_write(project_root: Path) -> None:
    """验证 write 会覆盖写入可反序列化的 JSONL 数据并在每行末尾换行"""
    target = project_root / "logs" / "records.jsonl"

    result = jsonl.write(target, [{"name": "alice"}, [1, 2, 3]])

    assert result.ok is True
    assert jsonl.read(target).unwrap() == [{"name": "alice"}, [1, 2, 3]]
    assert target.read_text(encoding="utf-8").endswith("\n")


def test_append(project_root: Path) -> None:
    """验证 append 会向 JSONL 文件追加一行数据"""
    target = project_root / "records.jsonl"

    first_result = jsonl.append(target, {"name": "alice"})
    second_result = jsonl.append(target, {"name": "bob"})

    assert first_result.ok is True
    assert second_result.ok is True
    assert jsonl.read(target).unwrap() == [{"name": "alice"}, {"name": "bob"}]


def test_write_atomic_replace_failure(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证 JSONL 原子写入在替换失败时不会破坏原有文件内容"""
    target = project_root / "records.jsonl"
    target.write_text('{"name": "old"}\n', encoding="utf-8")

    def raise_replace(src: str | Path, dst: str | Path) -> None:
        del src, dst
        raise OSError("cannot replace file")

    monkeypatch.setattr("gal_chara_skill.fs.text.os.replace", raise_replace)

    result = jsonl.write(target, [{"name": "new"}], create_parent=False)

    assert result.ok is False
    assert jsonl.read(target).unwrap() == [{"name": "old"}]


def test_write_failure() -> None:
    """验证 write 在任意一行不可序列化时会返回失败结果并附带行索引"""
    result = jsonl.write("records.jsonl", [{"ok": True}, {"items": {1, 2, 3}}])

    assert result.ok is False
    assert result.code == "fs_parse_failed"
    assert result.data["index"] == 1


def test_append_failure() -> None:
    """验证 append 在数据不可序列化时会返回失败结果"""
    result = jsonl.append("records.jsonl", {"items": {1, 2, 3}})

    assert result.ok is False
    assert result.code == "fs_parse_failed"
