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
