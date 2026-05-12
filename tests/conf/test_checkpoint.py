from __future__ import annotations

from gal_chara_skill.conf.checkpoint import CheckpointData
from gal_chara_skill.conf.context import TaskContext
from gal_chara_skill.conf.task import GenerationTaskConfig, SliceSummaryTaskConfig


def test_checkpoint_data_slice_summary_config() -> None:
    """验证 CheckpointData 会保存切片总结任务配置"""
    task_config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt",),
    )
    task_context = TaskContext(task_id="task-001")

    checkpoint = CheckpointData(task_config=task_config, task_context=task_context)

    assert checkpoint.task_config is task_config


def test_checkpoint_data_generation_config() -> None:
    """验证 CheckpointData 会保存生成任务配置"""
    task_config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
    )
    task_context = TaskContext(task_id="task-001")

    checkpoint = CheckpointData(task_config=task_config, task_context=task_context)

    assert checkpoint.task_config is task_config


def test_checkpoint_data_task_context() -> None:
    """验证 CheckpointData 会保存任务上下文对象"""
    task_config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt",),
    )
    task_context = TaskContext(task_id="task-001")

    checkpoint = CheckpointData(task_config=task_config, task_context=task_context)

    assert checkpoint.task_context is task_context
