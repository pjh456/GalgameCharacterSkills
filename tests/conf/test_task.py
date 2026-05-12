from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.task import (
    BaseTaskConfig,
    GenerationTaskConfig,
    SliceConfig,
    SliceSummaryTaskConfig,
)


def test_base_task_config() -> None:
    """验证 BaseTaskConfig 为不可变数据类"""
    config = BaseTaskConfig(role_name="Alice")

    with pytest.raises(FrozenInstanceError):
        config.role_name = "Bob"  # pyright: ignore[reportAttributeAccessIssue]


def test_slice_summary_task_config() -> None:
    """验证不同 SliceSummaryTaskConfig 实例不会共享切片配置对象"""
    first = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt",),
    )
    second = SliceSummaryTaskConfig(
        role_name="Bob",
        input_files=("b.txt",),
    )

    assert first.slice_config is not second.slice_config


def test_generation_task_config_chara_card() -> None:
    """验证 GenerationTaskConfig 支持 chara_card 任务类型"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="chara_card",
        summary_task_id="task-001",
    )

    assert config.kind == "chara_card"
