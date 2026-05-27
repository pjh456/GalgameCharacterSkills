from __future__ import annotations

from typing import Optional

from numpydoc_decorator import doc

from ..conf.state import TaskState
from ..conf.task import GenerationTaskConfig, SliceSummaryTaskConfig, TaskConfig
from ..conf.module.executor import ExecutorConfig
from ..conf.module.log import LogLevel
from ..core.paths import WorkspacePaths
from ..core.result import Result
from ..llm.client import LlmClient
from ..log.models import LogRecord
from ..log.writer import LogWriter
from .checkpoint import CheckpointStore
from .stages.finalize import FinalizeStage
from .stages.generate import GenerateStage
from .stages.prepare import PrepareStage
from .stages.summarize import SummarizeStage


@doc(
    summary="任务执行器，按 TaskConfig 子类型路由到对应的阶段处理器序列",
    parameters={
        "config": "任务静态配置",
        "llm_client": "LLM 调用客户端",
        "workspace": "工作区路径布局",
        "log_writer": "日志写入器",
        "executor_config": "阶段级工具调用配置，默认使用 ExecutorConfig()",
        "state": "任务运行时状态，为 None 时创建新任务",
    },
)
class TaskExecutor:
    def __init__(
        self,
        config: TaskConfig,
        *,
        llm_client: LlmClient,
        workspace: WorkspacePaths,
        log_writer: LogWriter,
        executor_config: ExecutorConfig = ExecutorConfig(),
        state: Optional[TaskState] = None,
    ) -> None:
        self.config = config
        self.llm_client = llm_client
        self.workspace = workspace
        self.log_writer = log_writer
        self.executor_config = executor_config
        self.state = state or TaskState(task_id=config.role_name)
        self.checkpoint_store = CheckpointStore()

    @doc(
        summary="同步执行入口，在事件循环中运行 arun",
        returns="表示整体执行结果的显式结果对象",
    )
    def run(self) -> Result[None]:
        import asyncio

        if self.executor_config.preflight_check:
            check_result = self.llm_client.check()
            if not check_result.ok:
                return Result.failure(
                    f"LLM 连接预检失败: {check_result.error}",
                    code="executor_preflight_failed",
                )

        return asyncio.run(self.arun())

    @doc(
        summary="异步执行入口，按 TaskConfig 子类型路由到对应的阶段处理器序列",
        returns="成功时返回空，失败或异常时返回错误原因",
    )
    async def arun(self) -> Result[None]:
        self._log("info", f"Task started")
        self.state.status = "running"

        try:
            if isinstance(self.config, SliceSummaryTaskConfig):
                result = await self._run_summarize()
            elif isinstance(self.config, GenerationTaskConfig):
                result = await self._run_generation()
            else:
                return Result.failure(
                    f"Unknown task config type: {type(self.config).__name__}",
                    code="executor_invalid_config",
                )

            if not result.ok:
                return result

            self.state.status = "completed"
            self._log("info", "Task completed")
            return Result.success()

        except Exception as exc:
            self.state.status = "failed"
            self.state.error_message = str(exc)
            self._log("error", f"Task failed: {exc}")
            return Result.failure(str(exc), code="executor_failed", exception=str(exc))

    @doc(
        summary="执行切片总结流水线：准备 + 蒸馏 + 写入切片总结文件",
        returns="成功时返回空，失败时返回错误原因",
    )
    async def _run_summarize(self) -> Result[None]:
        config = self.config
        assert isinstance(config, SliceSummaryTaskConfig)

        prepare_result = await PrepareStage().execute(self, config)
        if not prepare_result.ok:
            return prepare_result

        summarize_result = await SummarizeStage().execute(self, config)
        if not summarize_result.ok:
            return summarize_result

        return self._write_summaries(config)

    @doc(
        summary="将切片总结结果拼接为 Markdown 并写入 summaries 目录",
        parameters={"config": "切片总结任务配置"},
        returns="表示写入结果的显式结果对象",
    )
    def _write_summaries(self, config: SliceSummaryTaskConfig) -> Result[None]:
        from ..fs.text import TextIO

        summaries: list[str] = self.state.metadata.get("summaries", [])
        content = "\n\n---\n\n".join(summaries)
        output_path = self.workspace.summaries_dir / f"{config.role_name}_summary.md"

        write_result = TextIO.write(output_path, content)
        if not write_result.ok:
            self._log("error", f"Write summaries failed: {write_result.error}")
            return Result.failure_from(write_result)

        self._log("info", f"Summaries written to: {output_path}")
        return Result.success()

    @doc(
        summary="执行生成产物流水线：生成 + 写入最终产物文件",
        returns="成功时返回空，失败时返回错误原因",
    )
    async def _run_generation(self) -> Result[None]:
        config = self.config
        assert isinstance(config, GenerationTaskConfig)

        generate_result = await GenerateStage().execute(self, config)
        if not generate_result.ok:
            return generate_result

        return await FinalizeStage().execute(self, config)

    @doc(
        summary="写入一条结构化日志记录",
        parameters={
            "level": "日志级别",
            "message": "日志正文",
        },
    )
    def _log(self, level: LogLevel, message: str) -> None:
        from datetime import datetime

        record = LogRecord(
            level=level,
            message=message,
            timestamp=datetime.now(),
            module="executor",
            task_id=self.state.task_id,
        )
        self.log_writer.write(record)


__all__ = ["TaskExecutor"]
