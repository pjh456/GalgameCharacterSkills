from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ...conf.state import SliceState
from ...conf.task import SliceSummaryTaskConfig
from ...core.executors import Executors
from ...core.result import Result
from ...fs.text import TextIO
from ..slicer import Slicer
from .base import StageHandler
from numpydoc_decorator import doc

if TYPE_CHECKING:
    from ..task_executor import TaskExecutor


@doc(summary="切片总结任务的准备阶段：读取输入文件、切片、初始化 SliceState")
class PrepareStage(StageHandler[SliceSummaryTaskConfig]):
    @staticmethod
    @doc(
        summary="从 input 目录读取文件并切片",
        parameters={
            "input_files": "待读取的输入文件名元组",
            "input_dir": "输入文件所在目录",
            "max_tokens": "单个切片允许的最大 token 数",
        },
        returns="成功时 value 为 (切片列表, 原始行列表)，读取或切片失败时返回错误",
    )
    def _read_and_slice(
        input_files: tuple[str, ...],
        input_dir: Path,
        max_tokens: int,
    ) -> Result[tuple[list[str], list[str]]]:
        all_lines: list[str] = []

        for input_file in input_files:
            read_result = TextIO.read_auto_encodings(input_dir / input_file)
            if not read_result.ok:
                return Result.failure_from(read_result, error=f"读取文件失败: {input_file}")
            all_lines.extend(read_result.unwrap().splitlines(keepends=True))

        if not all_lines:
            return Result.failure(
                "输入文件未读取到任何内容",
                code="executor_empty_input",
            )

        text = "".join(all_lines)
        slices = Slicer.slice_text(text, max_tokens)
        return Result.success((slices, all_lines))

    async def execute(self, executor: TaskExecutor, config: SliceSummaryTaskConfig) -> Result[None]:
        result = await Executors.run_in_pool(
            PrepareStage._read_and_slice,
            config.input_files,
            executor.workspace.input_dir,
            config.slice_config.max_tokens,
        )
        if not result.ok:
            return Result.failure_from(result)

        slices, _ = result.unwrap()

        executor.state.slice_states = [
            SliceState(slice_index=i, source_file="merged", source_slice_index=i)
            for i in range(len(slices))
        ]
        executor.state.metadata["slice_contents"] = slices
        executor._log("info", f"Prepared {len(slices)} slices from {len(config.input_files)} file(s)")
        return Result.success()


__all__ = ["PrepareStage"]
