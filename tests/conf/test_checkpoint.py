from __future__ import annotations

from gal_chara_skill.conf.checkpoint import CheckpointData
from gal_chara_skill.conf.context import TaskContext
from gal_chara_skill.conf.task import GenerationTaskConfig, SliceSummaryTaskConfig


def test_checkpoint_data() -> None:
    """验证 CheckpointData 会保存任务配置与任务上下文对象"""
    summary_config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt",),
    )
    generation_config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
    )
    task_context = TaskContext(task_id="task-001")

    summary_checkpoint = CheckpointData(task_config=summary_config, task_context=task_context)
    generation_checkpoint = CheckpointData(task_config=generation_config, task_context=task_context)

    assert summary_checkpoint.task_config is summary_config
    assert generation_checkpoint.task_config is generation_config
    assert summary_checkpoint.task_context is task_context
