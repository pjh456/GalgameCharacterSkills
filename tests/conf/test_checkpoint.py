from __future__ import annotations

from gal_chara_skill.conf.checkpoint import TaskCheckpoint
from gal_chara_skill.conf.state import SliceState, TaskState
from gal_chara_skill.conf.task import (
    GenerationTaskConfig,
    SliceConfig,
    SliceSummaryTaskConfig,
)


def test_to_dict_and_from_dict_slice_summary() -> None:
    """验证切片总结任务 checkpoint 可以在字典与模型之间往返转换"""
    source = TaskCheckpoint(
        task_config=SliceSummaryTaskConfig(
            role_name="Alice",
            input_files=("a.txt", "b.txt"),
            slice_config=SliceConfig(max_tokens=1000, parallelism=2),
        ),
        task_state=TaskState(
            task_id="task-001",
            status="running",
            current_stage="summarizing",
            completed_slices=[0],
            slice_states=[
                SliceState(
                    slice_index=0,
                    source_file="a.txt",
                    source_slice_index=0,
                    status="completed",
                    attempt_count=1,
                )
            ],
            metadata={"note": "ok"},
        ),
    )

    data = source.to_dict()
    restored = TaskCheckpoint.from_dict(data).unwrap()

    assert data["task_config"]["input_files"] == ["a.txt", "b.txt"]
    assert restored == source


def test_to_dict_and_from_dict_generation() -> None:
    """验证生成任务 checkpoint 可以在字典与模型之间往返转换"""
    source = TaskCheckpoint(
        task_config=GenerationTaskConfig(
            role_name="Alice",
            kind="skills",
            summary_task_id="summary-001",
        ),
        task_state=TaskState(task_id="task-002", current_stage="generating"),
    )

    restored = TaskCheckpoint.from_dict(source.to_dict()).unwrap()

    assert restored == source


def test_from_dict_invalid_shape() -> None:
    """验证 from_dict 会拒绝非字典和缺失必要字段的数据"""
    not_dict_result = TaskCheckpoint.from_dict([])
    missing_task_result = TaskCheckpoint.from_dict({"task_config": {}, "task_state": {}})
    invalid_config_result = TaskCheckpoint.from_dict(
        {
            "task_config": [],
            "task_state": {
                "task_id": "task-001",
            },
        }
    )
    unknown_task_result = TaskCheckpoint.from_dict(
        {
            "task_config": {
                "kind": "other",
                "role_name": "Alice",
            },
            "task_state": {
                "task_id": "task-001",
            },
        }
    )
    invalid_slice_config_result = TaskCheckpoint.from_dict(
        {
            "task_config": {
                "kind": "summarize",
                "role_name": "Alice",
                "input_files": ["script.txt"],
                "slice_config": [],
            },
            "task_state": {
                "task_id": "task-001",
            },
        }
    )
    invalid_generation_result = TaskCheckpoint.from_dict(
        {
            "task_config": {
                "kind": "skills",
                "role_name": "Alice",
            },
            "task_state": {
                "task_id": "task-001",
            },
        }
    )
    invalid_state_result = TaskCheckpoint.from_dict(
        {
            "task_config": {
                "kind": "summarize",
                "role_name": "Alice",
                "input_files": ["script.txt"],
            },
            "task_state": [],
        }
    )
    invalid_slice_state_result = TaskCheckpoint.from_dict(
        {
            "task_config": {
                "kind": "summarize",
                "role_name": "Alice",
                "input_files": ["script.txt"],
            },
            "task_state": {
                "task_id": "task-001",
                "slice_states": [{}],
            },
        }
    )

    assert not_dict_result.ok is False
    assert missing_task_result.ok is False
    assert invalid_config_result.ok is False
    assert unknown_task_result.ok is False
    assert unknown_task_result.code == "checkpoint_unknown_task_kind"
    assert invalid_slice_config_result.ok is False
    assert invalid_generation_result.ok is False
    assert invalid_state_result.ok is False
    assert invalid_slice_state_result.ok is False
