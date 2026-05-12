from __future__ import annotations

from gal_chara_skill.conf.checkpoint import TaskCheckpoint
from gal_chara_skill.conf.state import TaskState
from gal_chara_skill.conf.task import GenerationTaskConfig, SliceSummaryTaskConfig


def test_task_checkpoint() -> None:
    """验证 TaskCheckpoint 会保存任务配置与任务状态对象"""
    summary_config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt",),
    )
    generation_config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
    )
    task_state = TaskState(task_id="task-001")

    summary_checkpoint = TaskCheckpoint(task_config=summary_config, task_state=task_state)
    generation_checkpoint = TaskCheckpoint(task_config=generation_config, task_state=task_state)

    assert summary_checkpoint.task_config is summary_config
    assert generation_checkpoint.task_config is generation_config
    assert summary_checkpoint.task_state is task_state
