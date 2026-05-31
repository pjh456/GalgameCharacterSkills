from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from numpydoc_decorator import doc

from ..core.result import Result
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

    @staticmethod
    @doc(
        summary="填充 JSON 模板中的占位符并写入输出文件",
        parameters={
            "template_path": "JSON 模板文件路径",
            "output_path": "输出文件路径",
            "field_mappings": "占位符到值的映射字典",
            "workspace": "工作区路径（用于 ensure_parent_dir）",
        },
        returns="成功时 value 为输出路径，失败时返回错误原因",
    )
    def fill_json_template(
        template_path: str,
        output_path: str,
        field_mappings: dict[str, Any],
    ) -> Result[str]:
        read_result = TextIO.read(template_path)
        if not read_result.ok:
            return Result.failure_from(read_result, error="模板文件读取失败")

        template = read_result.unwrap()

        for placeholder, value in field_mappings.items():
            if isinstance(value, (list, dict)):
                json_value = json.dumps(value, ensure_ascii=False)
                template = template.replace(placeholder, json_value)

        for placeholder, value in field_mappings.items():
            if isinstance(value, str):
                escaped_value = json.dumps(value, ensure_ascii=False)
                template = template.replace(f'"{placeholder}"', escaped_value)

        try:
            parsed = json.loads(template)
            template = json.dumps(parsed, ensure_ascii=False, indent=4)
        except json.JSONDecodeError as e:
            return Result.failure(
                f"模板填充后 JSON 无效: {e}",
                code="llm_parse_failed",
            )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        write_result = TextIO.write(output_path, template)
        if not write_result.ok:
            return Result.failure_from(write_result, error="模板输出写入失败")

        return Result.success(output_path)

    @staticmethod
    @doc(
        summary="将 entries 列表格式化为 SillyTavern V2 扩展格式的 lorebook 条目",
        parameters={
            "entries": "原始条目列表，每个条目需包含 keys, comment, content",
            "start_id": "起始 ID，递增分配",
        },
        returns="格式化后的 lorebook entries 列表",
    )
    def build_lorebook_entries(entries: list[dict[str, Any]], start_id: int = 0) -> Result[list[dict[str, Any]]]:
        if not isinstance(entries, list):
            return Result.failure("entries 必须是列表", code="executor_validation_failed")
        if not isinstance(start_id, int):
            return Result.failure("start_id 必须是整数", code="executor_validation_failed")

        formatted_entries = []
        for i, entry in enumerate(entries):
            formatted_entry = {
                "id": start_id + i,
                "keys": entry.get("keys", []),
                "secondary_keys": [],
                "comment": entry.get("comment", ""),
                "content": entry.get("content", ""),
                "constant": False,
                "selective": True,
                "insertion_order": 100,
                "enabled": True,
                "position": "before_char",
                "use_regex": True,
                "extensions": {
                    "position": 0,
                    "exclude_recursion": False,
                    "display_index": i,
                    "probability": 100,
                    "useProbability": True,
                    "depth": 4,
                    "selectiveLogic": 0,
                    "outlet_name": "",
                    "group": "",
                    "group_override": False,
                    "group_weight": 100,
                    "prevent_recursion": False,
                    "delay_until_recursion": False,
                    "scan_depth": None,
                    "match_whole_words": None,
                    "use_group_scoring": False,
                    "case_sensitive": None,
                    "automation_id": "",
                    "role": 0,
                    "vectorized": False,
                    "sticky": 0,
                    "cooldown": 0,
                    "delay": 0,
                    "match_persona_description": False,
                    "match_character_description": False,
                    "match_character_personality": False,
                    "match_character_depth_prompt": False,
                    "match_scenario": False,
                    "match_creator_notes": False,
                    "triggers": [],
                    "ignore_budget": False,
                },
            }
            formatted_entries.append(formatted_entry)
        return Result.success(formatted_entries)

    @staticmethod
    @doc(
        summary="合并多组 lorebook 条目，按 keys 去重并拼接 content",
        parameters={"entries_list": "多组 entries 的列表"},
        returns="合并去重后的 entries 列表",
    )
    def merge_lorebook_entries(entries_list: list[list[dict[str, Any]]]) -> Result[list[dict[str, Any]]]:
        merged: dict[tuple, dict[str, Any]] = {}
        for entries in entries_list:
            for entry in entries:
                key = tuple(sorted(entry.get("keys", [])))
                if key in merged:
                    existing = merged[key]
                    existing["content"] += "\n\n" + entry.get("content", "")
                else:
                    merged[key] = entry.copy()
        return Result.success(list(merged.values()))


__all__ = ["ToolHandler"]
