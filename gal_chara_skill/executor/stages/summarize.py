from __future__ import annotations

import asyncio
from threading import Lock
from typing import TYPE_CHECKING

from ...conf.checkpoint import TaskCheckpoint
from ...conf.state import SliceState
from ...conf.task import SliceSummaryTaskConfig
from ...core.result import Result
from ..prompts.summarize import build_summarize_prompt
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor

_SUMMARIES_LOCK = Lock()


@doc(summary="切片总结任务的蒸馏阶段：并行 LLM 调用、聚合结果、写入 checkpoint")
class SummarizeStage(StageHandler[SliceSummaryTaskConfig]):
    async def execute(self, executor: TaskExecutor, config: SliceSummaryTaskConfig) -> Result[None]:
        parallelism = config.slice_config.parallelism

        pending = [s for s in executor.state.slice_states if s.status == "pending"]

        for i in range(0, len(pending), parallelism):
            batch = pending[i : i + parallelism]
            tasks = [self._process_slice(s, config, executor) for s in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for s, result in zip(batch, results):
                if isinstance(result, BaseException) and not isinstance(result, Exception):
                    raise result
                if isinstance(result, Exception):
                    s.status = "failed"
                    s.error_message = str(result)
                    s.attempt_count += 1
                elif result.ok:
                    s.status = "completed"
                    executor.state.completed_slices.append(s.slice_index)
                else:
                    s.status = "failed"
                    s.error_message = result.error
                    s.attempt_count += 1

            executor._log("info", f"Summarized batch: {len(batch)} slices")
            self._save_checkpoint(executor, config)

        executor.state.metadata.pop("slice_contents", None)
        return Result.success()

    def _save_checkpoint(self, executor: TaskExecutor, config: SliceSummaryTaskConfig) -> None:
        checkpoint = TaskCheckpoint(task_config=config, task_state=executor.state)
        executor.checkpoint_store.save(checkpoint, executor.workspace)

    async def _process_slice(
        self,
        slice_state: SliceState,
        config: SliceSummaryTaskConfig,
        executor: TaskExecutor,
    ) -> Result[str]:
        slices: list[str] = executor.state.metadata.get("slice_contents", [])
        idx = slice_state.slice_index
        if idx < 0 or idx >= len(slices):
            return Result.failure(
                f"切片索引 {idx} 越界 (0..{len(slices) - 1 if slices else -1})",
                code="executor_slice_bounds",
            )
        content = slices[idx]

        messages = build_summarize_prompt(
            role_name=config.role_name,
            content=content,
            instruction=config.extra_instruction,
        )
        result = await executor.llm_client.acomplete(
            messages,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
        )
        if not result.ok:
            return Result.failure_from(result)

        completion = result.unwrap()
        if not completion.choices:
            executor._log("error", f"LLM 返回空 choices，切片 {slice_state.slice_index}")
            return Result.failure("LLM 返回空 choices", code="executor_empty_response")

        summary = completion.choices[0].message.content
        if summary is None:
            executor._log("error", f"LLM 返回 None 内容，切片 {slice_state.slice_index}")
            return Result.failure("LLM 返回 None 内容", code="executor_empty_response")

        with _SUMMARIES_LOCK:
            executor.state.metadata.setdefault("summaries", []).append(summary)
        return Result.success(summary)


__all__ = ["SummarizeStage"]
