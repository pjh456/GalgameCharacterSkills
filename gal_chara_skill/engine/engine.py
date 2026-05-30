from __future__ import annotations

from typing import Any

from numpydoc_decorator import doc

from ..conf.checkpoint import CheckpointStore
from ..conf.runtime import RuntimeConfig
from ..conf.stage import StageContext
from ..conf.state import TaskState
from ..conf.task import GenerationTaskConfig, SliceSummaryTaskConfig, TaskConfig
from ..core.result import Result
from ..fs.text import TextIO
from ..llm.client import LlmClient
from ..log.logger import Logger
from ..log.writer import LogWriter
from ..net.client import NetClient
from ..stages import FinalizeStage, GenerateStage, PrepareStage, SummarizeStage
from .task_executor import TaskExecutor


@doc(summary="流程编排引擎，组装依赖、选择 stage 序列、发起执行", parameters={"runtime": "一次运行共享的基础配置"})
class Engine:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime

    @doc(
        summary="从零开始执行蒸馏任务",
        parameters={"task_config": "任务配置"},
        returns="成功时返回空 Result，失败时返回错误原因",
    )
    def run(self, task_config: TaskConfig) -> Result[None]:
        state = TaskState(task_id=task_config.role_name)
        return self._execute(task_config, state)

    @doc(
        summary="从上次检查点恢复执行，若检查点不存在则从零开始",
        parameters={"task_config": "任务配置"},
        returns="同 run()",
    )
    def resume(self, task_config: TaskConfig) -> Result[None]:
        checkpoint_store = CheckpointStore()
        load_result = checkpoint_store.load(task_config.role_name, self.runtime.workspace_paths)
        if load_result.ok:
            checkpoint = load_result.unwrap()
            if checkpoint is not None:
                state = checkpoint.task_state
                return self._execute(task_config, state)

        state = TaskState(task_id=task_config.role_name)
        return self._execute(task_config, state)

    def _execute(self, task_config: TaskConfig, state: TaskState) -> Result[None]:
        net_client = NetClient(self.runtime.net_config)
        llm_client = LlmClient(self.runtime.llm_config, net_client=net_client)

        if self.runtime.executor_config.preflight_check:
            check = llm_client.check()
            if not check.ok:
                return Result.failure(
                    f"LLM 连接预检失败: {check.error}",
                    code="engine_preflight_failed",
                )

        if self.runtime.log_path_config is None:
            return Result.failure("log_path_config 不可为空", code="engine_config_error")

        logger = Logger(
            self.runtime.log_policy,
            writer=LogWriter(self.runtime.log_policy, self.runtime.log_path_config),
        )
        checkpoint_store = CheckpointStore()
        ctx = StageContext(
            llm_client=llm_client,
            logger=logger,
            state=state,
            checkpoint_store=checkpoint_store,
            workspace=self.runtime.workspace_paths,
            executor_config=self.runtime.executor_config,
        )

        if isinstance(task_config, SliceSummaryTaskConfig):
            stages: list[Any] = [PrepareStage(), SummarizeStage()]
        elif isinstance(task_config, GenerationTaskConfig):
            stages: list[Any] = [GenerateStage(), FinalizeStage()]
        else:
            return Result.failure(
                f"Unknown task config: {type(task_config).__name__}",
                code="engine_unknown_config",
            )

        executor = TaskExecutor(ctx=ctx, stages=stages, config=task_config)
        run_result = executor.run()
        if not run_result.ok:
            return run_result

        if isinstance(task_config, SliceSummaryTaskConfig):
            summaries: list[str] = ctx.state.metadata.get("summaries", [])
            content = "\n\n---\n\n".join(summaries)
            output_path = ctx.workspace.summaries_dir / f"{task_config.role_name}_summary.md"
            write_result = TextIO.write(output_path, content)
            if not write_result.ok:
                logger.error("摘要合并写入失败", path=str(output_path), error=write_result.error, code=write_result.code)
                return Result.failure_from(write_result)
            logger.info("摘要合并完成", path=str(output_path), count=len(summaries), chars=len(content))

        return Result.success()


__all__ = ["Engine"]
