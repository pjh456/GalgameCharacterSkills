from __future__ import annotations

from typing import Any

from gal_chara_skill.conf.checkpoint import TaskCheckpoint
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.core.result import Result
from gal_chara_skill.fs import JsonIO

from numpydoc_decorator import doc


@doc(summary="检查点持久化工具，负责 TaskCheckpoint 的序列化与反序列化")
class CheckpointStore:
    @doc(
        summary="将检查点保存为 JSON 文件",
        parameters={
            "checkpoint": "需要保存的任务检查点",
            "workspace": "工作区路径布局",
        },
        returns="表示保存结果的显式结果对象",
    )
    def save(
        self,
        checkpoint: TaskCheckpoint,
        workspace: WorkspacePaths,
    ) -> Result[None]:
        path = workspace.checkpoints_dir / f"{checkpoint.task_state.task_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return JsonIO.write(path, checkpoint.to_dict())

    @doc(
        summary="从 JSON 文件加载检查点",
        parameters={
            "task_id": "任务唯一标识",
            "workspace": "工作区路径布局",
        },
        returns="成功时 value 为 TaskCheckpoint，文件不存在时为 None，格式错误时返回失败结果",
    )
    def load(
        self,
        task_id: str,
        workspace: WorkspacePaths,
    ) -> Result[Any]:
        path = workspace.checkpoints_dir / f"{task_id}.json"
        read_result = JsonIO.read(path)
        if not read_result.ok:
            if read_result.code == "fs_not_found":
                return Result.success(None)
            return Result.failure_from(read_result)
        return TaskCheckpoint.from_dict(read_result.unwrap())


__all__ = ["CheckpointStore"]
