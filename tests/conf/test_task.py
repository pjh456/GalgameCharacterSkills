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


def test_base_task_config_to_dict() -> None:
    """验证 BaseTaskConfig 提供默认的持久化字典转换"""
    config = BaseTaskConfig(
        role_name="Alice",
        system_prompt="sys",
        extra_instruction="extra",
        use_vndb=True,
        temperature=0.3,
        max_output_tokens=1024,
    )

    assert config.to_dict() == {
        "role_name": "Alice",
        "system_prompt": "sys",
        "extra_instruction": "extra",
        "use_vndb": True,
        "temperature": 0.3,
        "max_output_tokens": 1024,
    }


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


def test_slice_summary_task_config_to_dict_and_from_dict() -> None:
    """验证切片总结任务配置可以在字典与模型之间往返转换"""
    source = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt", "b.txt"),
        slice_config=SliceConfig(max_tokens=1000, parallelism=2),
    )

    data = source.to_dict()
    restored = BaseTaskConfig.from_dict(data).unwrap()

    assert data["input_files"] == ["a.txt", "b.txt"]
    assert restored == source


def test_generation_task_config_chara_card() -> None:
    """验证 GenerationTaskConfig 支持 chara_card 任务类型"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="chara_card",
        summary_task_id="task-001",
    )

    assert config.kind == "chara_card"


def test_generation_task_config_to_dict_and_from_dict() -> None:
    """验证生成任务配置可以在字典与模型之间往返转换"""
    source = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="summary-001",
    )

    restored = BaseTaskConfig.from_dict(source.to_dict()).unwrap()

    assert restored == source


def test_base_task_config_from_dict_invalid_shape() -> None:
    """验证 BaseTaskConfig.from_dict 会拒绝非法结构"""
    not_dict_result = BaseTaskConfig.from_dict([])
    missing_field_result = BaseTaskConfig.from_dict({"kind": "skills", "role_name": "Alice"})
    invalid_slice_config_result = BaseTaskConfig.from_dict(
        {
            "kind": "summarize",
            "role_name": "Alice",
            "input_files": ["script.txt"],
            "slice_config": [],
        }
    )
    unknown_kind_result = BaseTaskConfig.from_dict({"kind": "other", "role_name": "Alice"})

    assert not_dict_result.ok is False
    assert missing_field_result.ok is False
    assert invalid_slice_config_result.ok is False
    assert unknown_kind_result.ok is False
    assert unknown_kind_result.code == "checkpoint_unknown_task_kind"
