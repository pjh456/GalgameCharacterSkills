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
        summaries = await self._compress(summaries_list, config, executor)

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

        result = executor.llm_client.complete(
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
    ) -> str:
        if len(summaries) <= 1:
            return "\n\n---\n\n".join(summaries)

        files = {f"summary_{i:03d}.md": s for i, s in enumerate(summaries)}
        messages = build_compress_prompt(files=files, group_index=0, total_groups=1)

        result = executor.llm_client.complete(
            messages,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
        )
        if result.ok:
            compressed = result.unwrap().choices[0].message.content
            executor._log("debug", "Compression completed")
            return compressed

        executor._log("warning", f"Compression skipped due to error: {result.error}")
        return "\n\n---\n\n".join(summaries)


__all__ = ["GenerateStage"]
