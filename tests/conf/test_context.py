from __future__ import annotations

from gal_chara_skill.conf.context import SliceState, TaskContext


def test_slice_state_defaults() -> None:
    """验证 SliceState 会使用预期默认值"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )

    assert state.status == "pending"
    assert state.attempt_count == 0
    assert state.error_message is None


def test_slice_state_custom_values() -> None:
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


def test_task_context_defaults() -> None:
    """验证 TaskContext 会使用预期默认值"""
    context = TaskContext(task_id="task-001")

    assert context.status == "pending"
    assert context.current_stage == "pending"
    assert context.completed_slices == []
    assert context.slice_states == []
    assert context.metadata == {}
    assert context.error_message is None


def test_task_context_custom_values() -> None:
    """验证 TaskContext 会保存显式传入的配置值"""
    slice_state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )
    context = TaskContext(
        task_id="task-001",
        current_stage="summarizing",
        completed_slices=[1, 2],
        slice_states=[slice_state],
        metadata={"stage": "running"},
        error_message="failed",
    )

    assert context.current_stage == "summarizing"
    assert context.completed_slices == [1, 2]
    assert context.slice_states == [slice_state]
    assert context.metadata == {"stage": "running"}
    assert context.error_message == "failed"


def test_task_context_independent_mutable_fields() -> None:
    """验证不同 TaskContext 实例不会共享可变字段"""
    first = TaskContext(task_id="task-001")
    second = TaskContext(task_id="task-002")

    first.completed_slices.append(1)
    first.slice_states.append(
        SliceState(slice_index=0, source_file="script.txt", source_slice_index=0)
    )
    first.metadata["stage"] = "running"

    assert second.completed_slices == []
    assert second.slice_states == []
    assert second.metadata == {}
