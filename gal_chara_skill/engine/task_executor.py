from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING

from numpydoc_decorator import doc

from ..core.result import Result

if TYPE_CHECKING:
    from ..conf.stage import StageContext
    from ..conf.task import TaskConfig
    from ..stages.base import StageHandler


@doc(
    summary="瘦身版 TaskExecutor，仅迭代 stage 序列，流程编排由 Engine 负责",
    parameters={
        "ctx": "Stage 执行上下文，由 Engine 组装后注入各 stage",
        "stages": "待执行的 Stage 处理器列表，按顺序逐个迭代",
        "config": "任务静态配置，透传给各 stage.execute()",
    },
)
class TaskExecutor:
    def __init__(
        self,
        *,
        ctx: StageContext,
        stages: list[StageHandler],
        config: TaskConfig,
    ) -> None:
        self.ctx = ctx
        self.stages = stages
        self.config = config

    @doc(
        summary="同步执行入口，启动 event loop 运行异步 stage 序列",
        returns="成功时返回空 Result，首个 stage 失败时返回其错误",
    )
    def run(self) -> Result[None]:
        return asyncio.run(self.arun())

    @doc(
        summary="异步执行入口，逐个 await stage.execute()，首个失败立即返回",
        returns="成功时返回空 Result，首个 stage 失败时返回其错误",
    )
    async def arun(self) -> Result[None]:
        self.ctx.state.status = "running"
        task_kind = type(self.config).__name__
        role = getattr(self.config, "role_name", "unknown")
        self.ctx.logger.info("任务开始", kind=task_kind, role=role)

        try:
            with self.ctx.logger.timed("任务完成, 耗时 {elapsed:.1f}s", kind=task_kind, role=role):
                for stage in self.stages:
                    result = await stage.execute(self.ctx, self.config)
                    if not result.ok:
                        return result
                self.ctx.state.status = "completed"
                return Result.success()
        except Exception as exc:
            self.ctx.state.status = "failed"
            self.ctx.state.error_message = traceback.format_exc()
            self.ctx.logger.error("任务异常", exception=str(exc), traceback=traceback.format_exc())
            return Result.failure(str(exc), code="executor_failed", exception=str(exc))


__all__ = ["TaskExecutor"]
