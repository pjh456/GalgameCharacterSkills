from __future__ import annotations

from gal_chara_skill.conf.state import SliceState, TaskState


def test_task_state_independent_fields() -> None:
    """验证不同 TaskState 实例不会共享可变字段"""
    first = TaskState(task_id="task-001")
    second = TaskState(task_id="task-002")

    first.completed_slices.append(1)
    first.slice_states.append(
        SliceState(slice_index=0, source_file="script.txt", source_slice_index=0)
    )
    first.metadata["stage"] = "running"

    assert second.completed_slices == []
    assert second.slice_states == []
    assert second.metadata == {}


def test_slice_state_to_dict_and_from_dict() -> None:
    """验证切片状态可以在字典与模型之间往返转换"""
    source = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=1,
        status="completed",
        attempt_count=2,
        error_message="ok",
    )

    restored = SliceState.from_dict(source.to_dict()).unwrap()

    assert restored == source


def test_task_state_to_dict_and_from_dict() -> None:
    """验证任务状态可以在字典与模型之间往返转换"""
    source = TaskState(
        task_id="task-001",
        status="running",
        current_stage="summarizing",
        completed_slices=[0],
        slice_states=[
            SliceState(slice_index=0, source_file="script.txt", source_slice_index=0)
        ],
        metadata={"note": "ok"},
    )

    restored = TaskState.from_dict(source.to_dict()).unwrap()

    assert restored == source


def test_state_from_dict_invalid_shape() -> None:
    """验证状态反序列化会拒绝非法结构"""
    invalid_slice_state_result = SliceState.from_dict([])
    missing_slice_field_result = SliceState.from_dict({})
    invalid_task_state_result = TaskState.from_dict([])
    missing_task_field_result = TaskState.from_dict({})
    invalid_nested_slice_result = TaskState.from_dict(
        {
            "task_id": "task-001",
            "slice_states": [{}],
        }
    )

    assert invalid_slice_state_result.ok is False
    assert missing_slice_field_result.ok is False
    assert invalid_task_state_result.ok is False
    assert missing_task_field_result.ok is False
    assert invalid_nested_slice_result.ok is False
