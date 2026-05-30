from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING

from numpydoc_decorator import doc

from ..conf.checkpoint import TaskCheckpoint
from ..conf.state import SliceState
from ..conf.task import SliceSummaryTaskConfig
from ..core.async_lock import AsyncLock
from ..core.result import Result
from ..fs.text import TextIO
from ..llm.tools import write_file_tool
from ..prompts.summarize import build_summarize_prompt
from .base import StageHandler
from .slicer import Slicer
from .tool_handler import ToolHandler

if TYPE_CHECKING:
    from ..conf.stage import StageContext

@doc(summary="切片总结任务的蒸馏阶段：并行 LLM 调用、聚合结果、写入 checkpoint")
class SummarizeStage(StageHandler[SliceSummaryTaskConfig]):
    def __init__(self) -> None:
        self._lock = AsyncLock()

    @doc(
        summary="调用 LLM 逐一生成切片摘要并聚合",
        parameters={
            "ctx": "阶段执行的共享上下文",
            "config": "切片总结任务配置，包含角色名、模型参数和并行度",
        },
        returns="成功时返回空 Result，失败时返回错误原因",
    )
    async def execute(self, ctx: StageContext, config: SliceSummaryTaskConfig) -> Result[None]:
        parallelism = config.slice_config.parallelism

        pending = [s for s in ctx.state.slice_states if s.status == "pending"]
        total_batches = (len(pending) + parallelism - 1) // parallelism

        for i in range(0, len(pending), parallelism):
            batch = pending[i : i + parallelism]
            batch_num = i // parallelism + 1
            tasks = [self._process_slice(s, config, ctx) for s in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            ok_count = 0
            fail_count = 0
            for s, result in zip(batch, results, strict=True):
                if isinstance(result, (KeyboardInterrupt, SystemExit)):
                    raise result
                if isinstance(result, BaseException):
                    s.status = "failed"
                    s.error_message = str(result)
                    s.attempt_count += 1
                    fail_count += 1
                elif result.ok:
                    s.status = "completed"
                    ctx.state.completed_slices.append(s.slice_index)
                    ok_count += 1
                else:
                    s.status = "failed"
                    s.error_message = result.error
                    s.attempt_count += 1
                    fail_count += 1

            ctx.logger.info("batch 完成", batch_num=batch_num, total_batches=total_batches,
                batch_size=len(batch), ok=ok_count, fail=fail_count)
            self._save_checkpoint(ctx, config)

        ctx.state.metadata.pop("slice_contents", None)
        ctx.logger.info("Summarize 阶段完成",
            completed=len(ctx.state.completed_slices),
            total=len(ctx.state.slice_states),
            summaries=len(ctx.state.metadata.get("summaries", [])))
        return Result.success()

    def _save_checkpoint(self, ctx: StageContext, config: SliceSummaryTaskConfig) -> None:
        checkpoint = TaskCheckpoint(task_config=config, task_state=ctx.state)
        result = ctx.checkpoint_store.save(checkpoint, ctx.workspace)
        ctx.logger.debug("checkpoint 已保存", task_id=ctx.state.task_id,
            completed_slices=len(ctx.state.completed_slices), ok=result.ok)

    async def _process_slice(
        self,
        slice_state: SliceState,
        config: SliceSummaryTaskConfig,
        ctx: StageContext,
    ) -> Result[str]:
        slices: list[str] = ctx.state.metadata.get("slice_contents", [])
        idx = slice_state.slice_index
        if idx < 0 or idx >= len(slices):
            return Result.failure(
                f"切片索引 {idx} 越界 (0..{len(slices) - 1 if slices else -1})",
                code="executor_slice_bounds",
            )
        content = slices[idx]

        output_path = ctx.workspace.summaries_dir / f"{config.role_name}_slice_{idx:03d}.md"

        messages = build_summarize_prompt(
            role_name=config.role_name,
            content=content,
            instruction=config.extra_instruction,
            vndb_data=config.vndb_data if config.use_vndb else None,
        )
        messages[1] = replace(
            messages[1], content=f"{messages[1].content}\n\n保存路径: {output_path}"
        )

        content_tokens = Slicer.count_tokens(content)

        tools = [write_file_tool()]
        ctx.logger.debug("LLM 请求", slice=idx, model=ctx.llm_client.config.model_name,
            msgs=len(messages), tools=len(tools), content_tokens=content_tokens,
            temperature=config.temperature, max_tokens=config.max_output_tokens)

        result = await ctx.llm_client.acomplete(
            messages,
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
            tools=tools,
        )
        if not result.ok:
            ctx.logger.error("LLM 调用失败", slice=idx, code=result.code, error=result.error)
            return Result.failure_from(result)

        completion = result.unwrap()
        usage = completion.usage
        ctx.logger.debug("LLM 响应", slice=idx, tokens_in=usage.prompt_tokens,
            tokens_out=usage.completion_tokens, total=usage.total_tokens,
            finish_reason=completion.finish_reason)

        choice = completion.message
        messages.append(choice)

        if choice.tool_calls:
            ctx.logger.debug("工具调用", slice=idx, tool_count=len(choice.tool_calls))
            for tc in choice.tool_calls:
                tool_result = ToolHandler.handle(tc, ToolHandler.default_executor)
                messages.append(tool_result)

        read_result = TextIO.read(output_path)
        if read_result.ok:
            summary = read_result.unwrap()
            ctx.logger.debug("摘要文件读取成功", slice=idx, path=str(output_path),
                chars=len(summary))
        else:
            summary = choice.content
            ctx.logger.warning("摘要文件不存在, 使用原始响应", slice=idx, path=str(output_path))
            if not summary:
                ctx.logger.error("LLM 无产出", slice=idx)
                return Result.failure("LLM 未产出有效内容", code="executor_empty_response")

        async with self._lock:
            ctx.state.metadata.setdefault("summaries", []).append(summary)
        return Result.success(summary)


__all__ = ["SummarizeStage"]
