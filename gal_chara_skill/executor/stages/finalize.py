from __future__ import annotations

from typing import TYPE_CHECKING

from ...conf.task import GenerationTaskConfig
from ...core.executors import Executors
from ...core.result import Result
from ...fs.text import TextIO
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor


@doc(summary="生成任务的写入阶段：skills 产物由 tool-calling 直接写入，chara_card 写入 JSON 到输出目录")
class FinalizeStage(StageHandler[GenerationTaskConfig]):
    async def execute(self, executor: TaskExecutor, config: GenerationTaskConfig) -> Result[None]:
        output = executor.state.metadata.get("generation_output", "")

        if config.kind == "skills":
            executor._log("info", f"Skills 产物已写入: {output}")
            return Result.success()

        output_path = executor.workspace.cards_dir / f"{config.role_name}.json"
        write_result = await Executors.run_in_pool(
            TextIO.write, output_path, output,
        )
        if not write_result.ok:
            executor._log("error", f"写入输出失败: {write_result.error}")
            return Result.failure_from(write_result)

        executor._log("info", f"角色卡已写入: {output_path}")
        return Result.success()
__all__ = ["FinalizeStage"]
