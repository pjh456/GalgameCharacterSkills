from __future__ import annotations

from typing import TYPE_CHECKING

from ...conf.state import SliceState
from ...conf.task import SliceSummaryTaskConfig
from ...core.result import Result
from ...fs.text import TextIO
from ..slicer import Slicer
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor


@doc(summary="切片总结任务的准备阶段：读取输入文件、切片、初始化 SliceState")
class PrepareStage(StageHandler[SliceSummaryTaskConfig]):
    def execute(self, executor: TaskExecutor, config: SliceSummaryTaskConfig) -> Result[None]:
        all_lines: list[str] = []

        for input_file in config.input_files:
            read_result = TextIO.read_auto_encodings(executor.workspace.input_dir / input_file)
            if not read_result.ok:
                return Result.failure_from(read_result, error=f"Failed to read: {input_file}")
            all_lines.extend(read_result.unwrap().splitlines(keepends=True))

        text = "".join(all_lines)
        slices = Slicer.slice_text(text, config.slice_config.max_tokens)

        executor.state.slice_states = [
            SliceState(slice_index=i, source_file="merged", source_slice_index=i)
            for i in range(len(slices))
        ]
        executor.state.metadata["slice_contents"] = slices
        executor.state.metadata["total_slices"] = len(slices)
        executor._log("info", f"Prepared {len(slices)} slices from {len(config.input_files)} file(s)")
        return Result.success()


__all__ = ["PrepareStage"]
