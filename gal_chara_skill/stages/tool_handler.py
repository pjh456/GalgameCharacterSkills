from __future__ import annotations

from typing import Callable

from numpydoc_decorator import doc

from ..fs.text import TextIO
from ..llm.models import ChatMessage, ToolCall


@doc(summary="工具调用处理器，将 LLM tool_calls 转译为文件系统操作")
class ToolHandler:

    @staticmethod
    @doc(
        summary="执行单个工具调用并返回结果消息",
        parameters={
            "tool_call": "LLM 返回的工具调用",
            "execute": "工具执行函数，签名为 (name, args) -> str",
        },
        returns="role=tool 的结果消息，失败时 content 为错误说明",
    )
    def handle(
        tool_call: ToolCall,
        execute: Callable[[str, dict], str],
    ) -> ChatMessage:
        result_text = execute(tool_call.name, tool_call.arguments)
        return ChatMessage(role="tool", content=result_text, tool_call_id=tool_call.id)

    @staticmethod
    @doc(
        summary="默认工具执行器：write_file 写入文件系统",
        parameters={
            "name": "工具函数名",
            "args": "工具参数",
        },
        returns="执行结果文本",
    )
    def default_executor(name: str, args: dict) -> str:
        if name == "write_file":
            file_path = args.get("file_path", "")
            content = args.get("content", "")
            if not file_path or not content:
                return "缺少必要参数: file_path 或 content"
            write_result = TextIO.write(file_path, content)
            if write_result.ok:
                return f"文件写入成功: {file_path}"
            return f"文件写入失败: {write_result.error}"
        return f"未知工具: {name}"


__all__ = ["ToolHandler"]
