from __future__ import annotations

from typing import TYPE_CHECKING

from ...conf.task import GenerationTaskConfig
from ...core.result import Result
from ..prompts.chara_card import build_chara_card_prompt
from ..prompts.compress import build_compress_prompt
from ..prompts.skills import build_skills_prompt
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor


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
            messages = build_skills_prompt(
                role_name=config.role_name,
                summaries=summaries,
            )
        else:
            messages = build_chara_card_prompt(
                role_name=config.role_name,
                content=summaries,
                instruction=config.extra_instruction,
            )

        result = await executor.llm_client.acomplete(
            messages,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
        )
        if not result.ok:
            return Result.failure_from(result)

        output = result.unwrap().choices[0].message.content
        executor.state.metadata["generation_output"] = output
        executor._log("info", f"Generation completed: kind={config.kind}")
        return Result.success()

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

        result = await executor.llm_client.acomplete(
            messages,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
        )
        if not result.ok:
            return Result.failure_from(result, error="压缩 LLM 调用失败")

        compressed = result.unwrap().choices[0].message.content
        executor._log("debug", "压缩完成")
        return Result.success(compressed)


__all__ = ["GenerateStage"]
