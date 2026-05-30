from __future__ import annotations

from typing import TYPE_CHECKING

from numpydoc_decorator import doc

from ..conf.task import GenerationTaskConfig
from ..core.result import Result
from ..fs.text import TextIO
from .base import StageHandler

if TYPE_CHECKING:
    from ..conf.stage import StageContext


@doc(summary="生成任务的写入阶段：skills 产物由 tool-calling 直接写入，chara_card 写入 JSON 到输出目录")
class FinalizeStage(StageHandler[GenerationTaskConfig]):
    @doc(
        summary="将生成产物写入文件系统",
        parameters={
            "ctx": "阶段执行的共享上下文",
            "config": "生成任务配置，包含产物类型和角色名",
        },
        returns="成功时返回空 Result，失败时返回错误原因",
    )
    async def execute(self, ctx: StageContext, config: GenerationTaskConfig) -> Result[None]:
        output = ctx.state.metadata.get("generation_output", "")

        if config.kind == "skills":
            ctx.logger.info("Skills 产物已落盘", folder=output)
            return Result.success()

        output_path = ctx.workspace.cards_dir / f"{config.role_name}.json"
        write_result = await TextIO.awrite(output_path, output)
        if not write_result.ok:
            ctx.logger.error("角色卡写入失败", path=str(output_path),
                error=write_result.error, code=write_result.code)
            return Result.failure_from(write_result)

        ctx.logger.info("角色卡写入完成", path=str(output_path), chars=len(output))
        return Result.success()
__all__ = ["FinalizeStage"]
