from __future__ import annotations

from typing import TYPE_CHECKING

from ...conf.task import GenerationTaskConfig
from ...core.result import Result
from ...fs.text import TextIO
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor


@doc(summary="生成任务的写入阶段：将产物写入输出目录")
class FinalizeStage(StageHandler[GenerationTaskConfig]):
    def execute(self, executor: TaskExecutor, config: GenerationTaskConfig) -> Result[None]:
        output = executor.state.metadata.get("generation_output", "")
        output_path = executor.workspace.output_dir / f"{config.role_name}_{config.kind}.md"

        write_result = TextIO.write(output_path, output)
        if not write_result.ok:
            executor._log("error", f"Write output failed: {write_result.error}")
            return Result.failure_from(write_result)

        executor._log("info", f"Output written to: {output_path}")
        return Result.success()


__all__ = ["FinalizeStage"]
