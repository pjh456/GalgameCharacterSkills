from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.task import (
    BaseTaskConfig,
    GenerationTaskConfig,
    SliceConfig,
    SliceSummaryTaskConfig,
)


def test_base_task_config_default_system_prompt() -> None:
    """验证 BaseTaskConfig 默认系统提示词为空"""
    config = BaseTaskConfig(role_name="Alice")

    assert config.system_prompt == ""


def test_base_task_config_default_extra_instruction() -> None:
    """验证 BaseTaskConfig 默认额外指令为空"""
    config = BaseTaskConfig(role_name="Alice")

    assert config.extra_instruction == ""


def test_base_task_config_default_use_vndb() -> None:
    """验证 BaseTaskConfig 默认不启用 VNDB"""
    config = BaseTaskConfig(role_name="Alice")

    assert config.use_vndb is False


def test_base_task_config_default_temperature() -> None:
    """验证 BaseTaskConfig 默认温度为 0.7"""
    config = BaseTaskConfig(role_name="Alice")

    assert config.temperature == 0.7


def test_base_task_config_default_max_output_tokens() -> None:
    """验证 BaseTaskConfig 默认最大输出 token 数为 4096"""
    config = BaseTaskConfig(role_name="Alice")

    assert config.max_output_tokens == 4096


def test_base_task_config_custom_system_prompt() -> None:
    """验证 BaseTaskConfig 会保存显式传入的系统提示词"""
    config = BaseTaskConfig(role_name="Alice", system_prompt="system")

    assert config.system_prompt == "system"


def test_base_task_config_custom_extra_instruction() -> None:
    """验证 BaseTaskConfig 会保存显式传入的额外指令"""
    config = BaseTaskConfig(role_name="Alice", extra_instruction="extra")

    assert config.extra_instruction == "extra"


def test_base_task_config_custom_use_vndb() -> None:
    """验证 BaseTaskConfig 会保存显式传入的 VNDB 开关"""
    config = BaseTaskConfig(role_name="Alice", use_vndb=True)

    assert config.use_vndb is True


def test_base_task_config_custom_temperature() -> None:
    """验证 BaseTaskConfig 会保存显式传入的温度"""
    config = BaseTaskConfig(role_name="Alice", temperature=0.2)

    assert config.temperature == 0.2


def test_base_task_config_custom_max_output_tokens() -> None:
    """验证 BaseTaskConfig 会保存显式传入的最大输出 token 数"""
    config = BaseTaskConfig(role_name="Alice", max_output_tokens=2048)

    assert config.max_output_tokens == 2048


def test_base_task_config_frozen() -> None:
    """验证 BaseTaskConfig 为不可变数据类"""
    config = BaseTaskConfig(role_name="Alice")

    with pytest.raises(FrozenInstanceError):
        config.role_name = "Bob" # pyright: ignore[reportAttributeAccessIssue]


def test_slice_config_default_max_tokens() -> None:
    """验证 SliceConfig 默认最大 token 数为 12000"""
    config = SliceConfig()

    assert config.max_tokens == 12000


def test_slice_config_default_parallelism() -> None:
    """验证 SliceConfig 默认并发数为 4"""
    config = SliceConfig()

    assert config.parallelism == 4


def test_slice_config_custom_max_tokens() -> None:
    """验证 SliceConfig 会保存显式传入的最大 token 数"""
    config = SliceConfig(max_tokens=8000)

    assert config.max_tokens == 8000


def test_slice_config_custom_parallelism() -> None:
    """验证 SliceConfig 会保存显式传入的并发数"""
    config = SliceConfig(parallelism=8)

    assert config.parallelism == 8


def test_slice_summary_task_config_default_kind() -> None:
    """验证 SliceSummaryTaskConfig 默认任务类型为 summarize"""
    config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt", "b.txt"),
    )

    assert config.kind == "summarize"


def test_slice_summary_task_config_default_slice_config() -> None:
    """验证 SliceSummaryTaskConfig 默认使用新的 SliceConfig 实例"""
    config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt", "b.txt"),
    )

    assert config.slice_config == SliceConfig()


def test_slice_summary_task_config_input_files() -> None:
    """验证 SliceSummaryTaskConfig 会保存输入文件列表"""
    config = SliceSummaryTaskConfig(
        role_name="Alice",
        input_files=("a.txt", "b.txt"),
    )

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


def test_generation_task_config_kind() -> None:
    """验证 GenerationTaskConfig 会保存生成任务类型"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
    )

    assert config.kind == "skills"


def test_generation_task_config_chara_card_kind() -> None:
    """验证 GenerationTaskConfig 支持 chara_card 任务类型"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="chara_card",
        summary_task_id="task-001",
    )

    assert config.kind == "chara_card"


def test_generation_task_config_summary_task_id() -> None:
    """验证 GenerationTaskConfig 会保存上游总结任务编号"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
    )

    assert config.summary_task_id == "task-001"


def test_generation_task_config_extra_instruction() -> None:
    """验证 GenerationTaskConfig 会保存额外指令"""
    config = GenerationTaskConfig(
        role_name="Alice",
        kind="skills",
        summary_task_id="task-001",
        extra_instruction="focus on combat style",
    )

    assert config.extra_instruction == "focus on combat style"
