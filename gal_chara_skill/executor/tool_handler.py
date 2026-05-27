from __future__ import annotations

from typing import Callable

from numpydoc_decorator import doc

from ..core.result import Result
from ..fs.text import TextIO
from ..llm.models import ChatMessage, ToolCall

_WRITE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "将内容写入本地文件",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "文件路径，含目录结构",
                },
                "content": {
                    "type": "string",
                    "description": "Markdown 格式的文件内容",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}

_REMOVE_DUPLICATES_TOOL = {
    "type": "function",
    "function": {
        "name": "remove_duplicate_sections",
        "description": "通过指定文件名和内容来移除文件中的重复片段",
        "parameters": {
            "type": "object",
            "properties": {
                "file_sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "包含重复内容的文件名",
                            },
                            "content": {
                                "type": "string",
                                "description": "要移除的重复内容，须与文件中原文完全一致",
                            },
                        },
                        "required": ["filename", "content"],
                    },
                },
            },
            "required": ["file_sections"],
        },
    },
}


def _build_write_field_tool(field_names: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "write_field",
            "description": "写入角色卡 JSON 的一个字段，可多次调用写入不同字段",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string",
                        "description": f"要写入的字段名，可选: {', '.join(field_names)}",
                        "enum": field_names,
                    },
                    "content": {
                        "type": "string",
                        "description": "该字段的内容，列表字段请传 JSON 数组字符串",
                    },
                    "is_complete": {
                        "type": "boolean",
                        "description": "是否为最后一个字段，设为 true 则系统将完成角色卡生成",
                    },
                },
                "required": ["field_name", "content"],
            },
        },
    }


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

    @staticmethod
    @doc(
        summary="获取 write_file 工具定义",
        returns="OpenAI 格式的工具定义字典",
    )
    def write_file_tool() -> dict:
        return _WRITE_FILE_TOOL

    @staticmethod
    @doc(
        summary="获取 remove_duplicate_sections 工具定义",
        returns="OpenAI 格式的工具定义字典",
    )
    def remove_duplicates_tool() -> dict:
        return _REMOVE_DUPLICATES_TOOL

    @staticmethod
    @doc(
        summary="获取 write_field 工具定义",
        parameters={"field_names": "允许写入的字段名列表"},
        returns="OpenAI 格式的工具定义字典",
    )
    def write_field_tool(field_names: list[str]) -> dict:
        return _build_write_field_tool(field_names)


__all__ = ["ToolHandler"]
