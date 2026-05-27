from __future__ import annotations

from typing import TYPE_CHECKING

from ...conf.task import GenerationTaskConfig
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
            executor.logger.info("Skills 产物已落盘", folder=output)
            return Result.success()

        output_path = executor.workspace.cards_dir / f"{config.role_name}.json"
        write_result = await TextIO.awrite(output_path, output)
        if not write_result.ok:
            executor.logger.error("角色卡写入失败", path=str(output_path),
                error=write_result.error, code=write_result.code)
            return Result.failure_from(write_result)

        executor.logger.info("角色卡写入完成", path=str(output_path), chars=len(output))
        return Result.success()
__all__ = ["FinalizeStage"]
