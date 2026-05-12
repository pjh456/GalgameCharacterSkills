from __future__ import annotations

from gal_chara_skill.conf.state import SliceState, TaskState


def test_slice_state() -> None:
    """验证 SliceState 会保存显式传入的配置值"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
        status="running",
        attempt_count=3,
        error_message="failed",
    )

    assert state.status == "running"
    assert state.attempt_count == 3
    assert state.error_message == "failed"


def test_task_state() -> None:
    """验证 TaskState 会保存显式传入的配置值"""
    slice_state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )
    state = TaskState(
        task_id="task-001",
        current_stage="summarizing",
        completed_slices=[1, 2],
        slice_states=[slice_state],
        metadata={"stage": "running"},
        error_message="failed",
    )

    assert state.current_stage == "summarizing"
    assert state.completed_slices == [1, 2]
    assert state.slice_states == [slice_state]
    assert state.metadata == {"stage": "running"}
    assert state.error_message == "failed"


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
