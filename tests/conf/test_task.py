from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.task import (
    BaseTaskConfig,
    GenerationTaskConfig,
    SliceConfig,
    SliceSummaryTaskConfig,
)


def test_base_task_config_defaults() -> None:
    """验证 BaseTaskConfig 会使用预期默认值"""
    config = BaseTaskConfig(role_name="Alice")

    assert config.system_prompt == ""
    assert config.extra_instruction == ""
    assert config.use_vndb is False
    assert config.temperature == 0.7
    assert config.max_output_tokens == 4096


def test_base_task_config_custom_values() -> None:
    """验证 BaseTaskConfig 会保存显式传入的配置值"""
    config = BaseTaskConfig(
        role_name="Alice",
        system_prompt="system",
        extra_instruction="extra",
        use_vndb=True,
        temperature=0.2,
        max_output_tokens=2048,
    )

    assert config.system_prompt == "system"
    assert config.extra_instruction == "extra"
    assert config.use_vndb is True
    assert config.temperature == 0.2
    assert config.max_output_tokens == 2048


def test_base_task_config_frozen() -> None:
    """验证 BaseTaskConfig 为不可变数据类"""
    config = BaseTaskConfig(role_name="Alice")

    with pytest.raises(FrozenInstanceError):
        config.role_name = "Bob"  # pyright: ignore[reportAttributeAccessIssue]


def test_slice_config_defaults() -> None:
    """验证 SliceConfig 会使用预期默认值"""
    config = SliceConfig()

    assert config.max_tokens == 12000
    assert config.parallelism == 4


def test_slice_config_custom_values() -> None:
    """验证 SliceConfig 会保存显式传入的配置值"""
    config = SliceConfig(max_tokens=8000, parallelism=8)

    assert config.max_tokens == 8000
    assert config.parallelism == 8


def test_slice_summary_task_config_defaults() -> None:
    """验证 SliceSummaryTaskConfig 会使用预期默认值"""
    config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt", "b.txt"),
    )

    assert config.kind == "summarize"
    assert config.slice_config == SliceConfig()
    assert config.input_files == ("a.txt", "b.txt")


def test_slice_summary_task_config_independent_slice_config() -> None:
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


def test_generation_task_config_custom_values() -> None:
    """验证 GenerationTaskConfig 会保存显式传入的配置值"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
        extra_instruction="focus on combat style",
    )

    assert config.kind == "skills"
    assert config.summary_task_id == "task-001"
    assert config.extra_instruction == "focus on combat style"


def test_generation_task_config_supports_chara_card_kind() -> None:
    """验证 GenerationTaskConfig 支持 chara_card 任务类型"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="chara_card",
        summary_task_id="task-001",
    )

    assert config.kind == "chara_card"
