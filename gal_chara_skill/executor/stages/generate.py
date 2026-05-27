from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ...conf.task import GenerationTaskConfig
from ...core.result import Result
from ..prompts.chara_card import build_chara_card_prompt
from ..prompts.compress import build_compress_prompt
from ..prompts.skills import build_skills_prompt
from ..tool_handler import ToolHandler
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor

_MAX_TOOL_ITERATIONS = 20

_FIELD_NAMES = [
    "name", "description", "personality", "first_mes", "mes_example",
    "scenario", "system_prompt", "post_history_instructions", "depth_prompt",
]


@doc(summary="生成任务的生成阶段：compress 去重 + skills/chara_card 生成")
class GenerateStage(StageHandler[GenerationTaskConfig]):
    async def execute(self, executor: TaskExecutor, config: GenerationTaskConfig) -> Result[None]:
        summaries_list: list[str] = executor.state.metadata.get("summaries", [])
        compress_result = await self._compress(summaries_list, config, executor)
        if compress_result.ok:
            summaries = compress_result.unwrap()
        else:
            executor._log("warning", f"压缩失败，退回原始拼接: {compress_result.error}")
            summaries = "\n\n---\n\n".join(summaries_list)

        if config.kind == "skills":
            return await self._generate_skills(summaries, config, executor)
        return await self._generate_chara_card(summaries, config, executor)

    async def _compress(
        self,
        summaries: list[str],
        config: GenerationTaskConfig,
        executor: TaskExecutor,
    ) -> Result[str]:
        if len(summaries) <= 1:
            return Result.success("\n\n---\n\n".join(summaries))

        files = {f"summary_{i:03d}.md": s for i, s in enumerate(summaries)}
        messages = build_compress_prompt(files=files, group_index=0, total_groups=1)
        tools = [ToolHandler.remove_duplicates_tool()]

        def _compress_executor(name: str, args: dict) -> str:
            if name == "remove_duplicate_sections":
                file_sections = args.get("file_sections", [])
                removed = 0
                for fs in file_sections:
                    fname = fs.get("filename", "")
                    content_to_remove = fs.get("content", "")
                    if fname in files and content_to_remove:
                        original = files[fname]
                        if content_to_remove in original:
                            files[fname] = original.replace(content_to_remove, "", 1)
                            removed += 1
                return f"已从 {removed} 个文件片段中移除重复"
            return f"未知工具: {name}"

        for _ in range(_MAX_TOOL_ITERATIONS):
            result = await executor.llm_client.acomplete(
                messages,
                temperature=config.temperature,
                max_tokens=config.max_output_tokens,
                tools=tools,
            )
            if not result.ok:
                return Result.failure_from(result, error="压缩 LLM 调用失败")

            choice = result.unwrap().choices[0]
            messages.append(choice.message)

            if not choice.message.tool_calls:
                break

            for tc in choice.message.tool_calls:
                tool_result = ToolHandler.handle(tc, _compress_executor)
                messages.append(tool_result)

        compressed = "\n\n---\n\n".join(files.values())
        executor._log("debug", "压缩完成")
        return Result.success(compressed)

    async def _generate_skills(
        self,
        summaries: str,
        config: GenerationTaskConfig,
        executor: TaskExecutor,
    ) -> Result[None]:
        messages = build_skills_prompt(
            role_name=config.role_name,
            summaries=summaries,
        )
        tools = [ToolHandler.write_file_tool()]

        for _ in range(_MAX_TOOL_ITERATIONS):
            result = await executor.llm_client.acomplete(
                messages,
                temperature=config.temperature,
                max_tokens=config.max_output_tokens,
                tools=tools,
            )
            if not result.ok:
                return Result.failure_from(result)

            choice = result.unwrap().choices[0]
            messages.append(choice.message)

            if not choice.message.tool_calls:
                break

            for tc in choice.message.tool_calls:
                tool_result = ToolHandler.handle(tc, ToolHandler.default_executor)
                messages.append(tool_result)

        output_folder = executor.workspace.skills_dir / f"{config.role_name}-skill-main"
        executor.state.metadata["generation_output"] = str(output_folder)
        executor._log("info", f"Skills generation completed: {output_folder}")
        return Result.success()

    async def _generate_chara_card(
        self,
        summaries: str,
        config: GenerationTaskConfig,
        executor: TaskExecutor,
    ) -> Result[None]:
        messages = build_chara_card_prompt(
            role_name=config.role_name,
            content=summaries,
            instruction=config.extra_instruction,
        )
        tools = [ToolHandler.write_field_tool(_FIELD_NAMES)]
        fields_data: dict[str, str] = {}

        def _field_executor(name: str, args: dict) -> str:
            if name == "write_field":
                field_name = args.get("field_name", "")
                if field_name in ("creatorcomment", "creator_notes", "world_name"):
                    return f"系统自动生成字段，已忽略: {field_name}"
                content = args.get("content", "")
                fields_data[field_name] = content
                return f"字段 {field_name} 写入成功"
            return f"未知工具: {name}"

        for _ in range(_MAX_TOOL_ITERATIONS):
            result = await executor.llm_client.acomplete(
                messages,
                temperature=config.temperature,
                max_tokens=config.max_output_tokens,
                tools=tools,
            )
            if not result.ok:
                return Result.failure_from(result)

            choice = result.unwrap().choices[0]
            messages.append(choice.message)

            if not choice.message.tool_calls:
                break

            for tc in choice.message.tool_calls:
                tool_result = ToolHandler.handle(tc, _field_executor)
                messages.append(tool_result)

        output = json.dumps(fields_data, ensure_ascii=False, indent=2)
        executor.state.metadata["generation_output"] = output
        executor._log("info", f"Character card generation completed: kind={config.kind}")
        return Result.success()


__all__ = ["GenerateStage"]
