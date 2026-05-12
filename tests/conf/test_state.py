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
