from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ...conf.task import GenerationTaskConfig
from ...core.result import Result
from ..prompts.chara_card import build_chara_card_prompt
from ..prompts.compress import build_compress_prompt
from ..prompts.skills import build_skills_prompt
from ..slicer import Slicer
from ..tool_handler import ToolHandler
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor

_FIELD_NAMES = [
    "name", "description", "personality", "first_mes", "mes_example",
    "scenario", "system_prompt", "post_history_instructions", "depth_prompt",
]


@doc(summary="生成任务的生成阶段：compress 去重 + skills/chara_card 生成")
class GenerateStage(StageHandler[GenerationTaskConfig]):
    async def execute(self, executor: TaskExecutor, config: GenerationTaskConfig) -> Result[None]:
        summaries_list: list[str] = executor.state.metadata.get("summaries", [])
        executor.logger.info("压缩开始", count=len(summaries_list))

        compress_result = await self._compress(summaries_list, config, executor)
        if compress_result.ok:
            summaries = compress_result.unwrap()
        else:
            executor.logger.warning("压缩失败, 退回原始拼接", error=compress_result.error, code=compress_result.code)
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
            executor.logger.debug("压缩跳过: 仅 1 篇摘要")
            return Result.success("\n\n---\n\n".join(summaries))

        before_tokens = Slicer.count_tokens("\n\n---\n\n".join(summaries))
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

        loop_result = await executor.llm_client.acomplete_with_tools(
            messages, tools,
            tool_handler=lambda tc: ToolHandler.handle(tc, _compress_executor),
            temperature=config.temperature, max_tokens=config.max_output_tokens,
            max_iterations=executor.executor_config.compress_max_iterations,
        )
        if not loop_result.ok:
            executor.logger.error("压缩 LLM 调用失败", error=loop_result.error, code=loop_result.code)
            return Result.failure_from(loop_result, error="压缩 LLM 调用失败")

        compressed = "\n\n---\n\n".join(files.values())
        after_tokens = Slicer.count_tokens(compressed)
        reduction = (1 - after_tokens / before_tokens) * 100 if before_tokens else 0
        executor.logger.debug("压缩完成", before_tokens=before_tokens, after_tokens=after_tokens,
            reduction=f"{reduction:.1f}%")
        return Result.success(compressed)

    async def _generate_skills(
        self,
        summaries: str,
        config: GenerationTaskConfig,
        executor: TaskExecutor,
    ) -> Result[None]:
        summary_tokens = Slicer.count_tokens(summaries)
        messages = build_skills_prompt(
            role_name=config.role_name,
            summaries=summaries,
            vndb_data=config.vndb_data if config.use_vndb else None,
        )
        executor.logger.debug("Skills prompt 已构建", role=config.role_name,
            summary_tokens=summary_tokens, msgs=len(messages))

        tools = [ToolHandler.write_file_tool()]

        loop_result = await executor.llm_client.acomplete_with_tools(
            messages, tools,
            tool_handler=lambda tc: ToolHandler.handle(tc, ToolHandler.default_executor),
            temperature=config.temperature, max_tokens=config.max_output_tokens,
            max_iterations=executor.executor_config.skills_max_iterations,
        )
        if not loop_result.ok:
            executor.logger.error("Skills 生成失败", error=loop_result.error, code=loop_result.code)
            return Result.failure_from(loop_result)

        output_folder = executor.workspace.skills_dir / f"{config.role_name}-skill-main"
        executor.state.metadata["generation_output"] = str(output_folder)
        executor.logger.info("Skills 生成完成", folder=str(output_folder),
            max_iterations=executor.executor_config.skills_max_iterations)
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
            vndb_data=config.vndb_data if config.use_vndb else None,
        )
        executor.logger.debug("Chara card prompt 已构建", role=config.role_name, msgs=len(messages))

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

        loop_result = await executor.llm_client.acomplete_with_tools(
            messages, tools,
            tool_handler=lambda tc: ToolHandler.handle(tc, _field_executor),
            temperature=config.temperature, max_tokens=config.max_output_tokens,
            max_iterations=executor.executor_config.chara_card_max_iterations,
        )
        if not loop_result.ok:
            executor.logger.error("角色卡生成失败", error=loop_result.error, code=loop_result.code)
            return Result.failure_from(loop_result)

        output = json.dumps(fields_data, ensure_ascii=False, indent=2)
        executor.state.metadata["generation_output"] = output
        executor.logger.info("角色卡生成完成", kind=config.kind, fields=len(fields_data), chars=len(output))
        return Result.success()


__all__ = ["GenerateStage"]
