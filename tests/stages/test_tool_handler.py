from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from gal_chara_skill.core.result import Result
from gal_chara_skill.llm.models import ToolCall
from gal_chara_skill.stages.tool_handler import ToolHandler


def test_handle_returns_tool_message() -> None:
    tc = ToolCall(id="call_1", name="test_tool", arguments={"key": "value"})

    def _executor(name: str, args: dict) -> str:
        return f"executed {name} with {args}"

    msg = ToolHandler.handle(tc, _executor)
    assert msg.role == "tool"
    assert msg.tool_call_id == "call_1"
    assert msg.content == "executed test_tool with {'key': 'value'}"


def test_default_executor_write_file_success() -> None:
    with patch("gal_chara_skill.stages.tool_handler.TextIO.write") as mock_write:
        mock_write.return_value = Result.success(None)
        result = ToolHandler.default_executor("write_file", {"file_path": "/tmp/test.md", "content": "hello"})
        assert "文件写入成功" in result
        assert "/tmp/test.md" in result
        mock_write.assert_called_once_with("/tmp/test.md", "hello")


def test_default_executor_write_file_failure() -> None:
    with patch("gal_chara_skill.stages.tool_handler.TextIO.write") as mock_write:
        mock_write.return_value = Result.failure("disk full", code="fs_write_error")
        result = ToolHandler.default_executor("write_file", {"file_path": "/tmp/test.md", "content": "hello"})
        assert "文件写入失败" in result


def test_default_executor_missing_params() -> None:
    result = ToolHandler.default_executor("write_file", {})
    assert "缺少必要参数" in result


def test_default_executor_unknown_tool() -> None:
    result = ToolHandler.default_executor("unknown_tool", {})
    assert "未知工具" in result


import json


class TestFillJsonTemplate:
    def test_success(self, tmp_path: Path) -> None:
        template = tmp_path / "template.json"
        template.write_text('{"name": "__NAME__", "age": "__AGE__"}', encoding="utf-8")
        output = tmp_path / "output.json"

        result = ToolHandler.fill_json_template(
            str(template), str(output),
            {"__NAME__": "Alice", "__AGE__": "25"},
        )
        assert result.ok
        assert output.exists()
        content = json.loads(output.read_text(encoding="utf-8"))
        assert content["name"] == "Alice"
        assert content["age"] == "25"

    def test_missing_template(self, tmp_path: Path) -> None:
        result = ToolHandler.fill_json_template(
            str(tmp_path / "nonexistent.json"),
            str(tmp_path / "out.json"),
            {},
        )
        assert not result.ok

    def test_invalid_json_after_fill(self, tmp_path: Path) -> None:
        template = tmp_path / "template.json"
        template.write_text("{__UNESCAPED__}", encoding="utf-8")
        output = tmp_path / "output.json"

        result = ToolHandler.fill_json_template(
            str(template), str(output),
            {"__UNESCAPED__": "unquoted string"},
        )
        assert not result.ok

    def test_list_field_fill(self, tmp_path: Path) -> None:
        template = tmp_path / "template.json"
        template.write_text('{"tags": __TAGS__}', encoding="utf-8")
        output = tmp_path / "output.json"

        result = ToolHandler.fill_json_template(
            str(template), str(output),
            {"__TAGS__": ["tag1", "tag2"]},
        )
        assert result.ok
        content = json.loads(output.read_text(encoding="utf-8"))
        assert content["tags"] == ["tag1", "tag2"]


class TestBuildLorebookEntries:
    def test_single_entry(self) -> None:
        entries = [{"keys": ["key1"], "comment": "test", "content": "Hello"}]
        result = ToolHandler.build_lorebook_entries(entries)
        assert result.ok
        formatted = result.unwrap()
        assert len(formatted) == 1
        assert formatted[0]["id"] == 0
        assert formatted[0]["keys"] == ["key1"]
        assert formatted[0]["extensions"]["display_index"] == 0
        assert formatted[0]["extensions"]["probability"] == 100
        assert "extensions" in formatted[0]
        assert len(formatted[0]["extensions"]) >= 30

    def test_multiple_entries_with_ids(self) -> None:
        entries = [
            {"keys": ["a"], "content": "A"},
            {"keys": ["b"], "content": "B"},
        ]
        result = ToolHandler.build_lorebook_entries(entries, start_id=10)
        assert result.ok
        formatted = result.unwrap()
        assert formatted[0]["id"] == 10
        assert formatted[1]["id"] == 11

    def test_invalid_entries_type(self) -> None:
        result = ToolHandler.build_lorebook_entries("not a list", 0)  # type: ignore[arg-type]
        assert not result.ok
        assert result.code == "executor_validation_failed"

    def test_invalid_start_id_type(self) -> None:
        result = ToolHandler.build_lorebook_entries([], "not int")  # type: ignore[arg-type]
        assert not result.ok


class TestMergeLorebookEntries:
    def test_merge_by_keys(self) -> None:
        entries_list = [
            [{"keys": ["key1", "key2"], "content": "Content A"}],
            [{"keys": ["key2", "key1"], "content": "Content B"}],
        ]
        result = ToolHandler.merge_lorebook_entries(entries_list)
        assert result.ok
        merged = result.unwrap()
        assert len(merged) == 1
        assert "Content A" in merged[0]["content"]
        assert "Content B" in merged[0]["content"]

    def test_no_duplicates(self) -> None:
        entries_list = [
            [{"keys": ["a"], "content": "A"}],
            [{"keys": ["b"], "content": "B"}],
        ]
        result = ToolHandler.merge_lorebook_entries(entries_list)
        assert result.ok
        assert len(result.unwrap()) == 2
