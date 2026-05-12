from __future__ import annotations

from gal_chara_skill.conf.context import SliceState, TaskContext


def test_slice_state_default_status() -> None:
    """验证 SliceState 默认状态为 pending"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )

    assert state.status == "pending"


def test_slice_state_default_attempt_count() -> None:
    """验证 SliceState 默认重试次数为 0"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )

    assert state.attempt_count == 0


def test_slice_state_default_error_message() -> None:
    """验证 SliceState 默认无错误信息"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )

    assert state.error_message is None


def test_slice_state_custom_status() -> None:
    """验证 SliceState 会保存显式传入的状态"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
        status="running",
    )

    assert state.status == "running"


def test_slice_state_custom_attempt_count() -> None:
    """验证 SliceState 会保存显式传入的重试次数"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
        attempt_count=3,
    )

    assert state.attempt_count == 3


def test_slice_state_custom_error_message() -> None:
    """验证 SliceState 会保存显式传入的错误信息"""
    state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
        error_message="failed",
    )

    assert state.error_message == "failed"


def test_task_context_default_status() -> None:
    """验证 TaskContext 默认状态为 pending"""
    context = TaskContext(task_id="task-001")

    assert context.status == "pending"


def test_task_context_default_stage() -> None:
    """验证 TaskContext 默认阶段为 pending"""
    context = TaskContext(task_id="task-001")

    assert context.current_stage == "pending"


def test_task_context_default_completed_slices() -> None:
    """验证 TaskContext 默认已完成切片列表为空"""
    context = TaskContext(task_id="task-001")

    assert context.completed_slices == []


def test_task_context_default_slice_states() -> None:
    """验证 TaskContext 默认切片状态列表为空"""
    context = TaskContext(task_id="task-001")

    assert context.slice_states == []


def test_task_context_default_metadata() -> None:
    """验证 TaskContext 默认元数据为空字典"""
    context = TaskContext(task_id="task-001")

    assert context.metadata == {}


def test_task_context_default_error_message() -> None:
    """验证 TaskContext 默认无错误信息"""
    context = TaskContext(task_id="task-001")

    assert context.error_message is None


def test_task_context_custom_stage() -> None:
    """验证 TaskContext 会保存显式传入的阶段"""
    context = TaskContext(task_id="task-001", current_stage="summarizing")

    assert context.current_stage == "summarizing"


def test_task_context_custom_completed_slices() -> None:
    """验证 TaskContext 会保存显式传入的已完成切片列表"""
    context = TaskContext(task_id="task-001", completed_slices=[1, 2])

    assert context.completed_slices == [1, 2]


def test_task_context_custom_slice_states() -> None:
    """验证 TaskContext 会保存显式传入的切片状态列表"""
    slice_state = SliceState(
        slice_index=0,
        source_file="script.txt",
        source_slice_index=0,
    )
    context = TaskContext(task_id="task-001", slice_states=[slice_state])

    assert context.slice_states == [slice_state]


def test_task_context_custom_metadata() -> None:
    """验证 TaskContext 会保存显式传入的元数据"""
    context = TaskContext(task_id="task-001", metadata={"stage": "running"})

    assert context.metadata == {"stage": "running"}


def test_task_context_custom_error_message() -> None:
    """验证 TaskContext 会保存显式传入的错误信息"""
    context = TaskContext(task_id="task-001", error_message="failed")

    assert context.error_message == "failed"


def test_task_context_independent_completed_slices() -> None:
    """验证不同 TaskContext 实例不会共享已完成切片列表"""
    first = TaskContext(task_id="task-001")
    second = TaskContext(task_id="task-002")

    first.completed_slices.append(1)

    assert second.completed_slices == []


def test_task_context_independent_slice_states() -> None:
    """验证不同 TaskContext 实例不会共享切片状态列表"""
    first = TaskContext(task_id="task-001")
    second = TaskContext(task_id="task-002")

    first.slice_states.append(
        SliceState(slice_index=0, source_file="script.txt", source_slice_index=0)
    )

    assert second.slice_states == []


def test_task_context_independent_metadata() -> None:
    """验证不同 TaskContext 实例不会共享元数据字典"""
    first = TaskContext(task_id="task-001")
    second = TaskContext(task_id="task-002")

    first.metadata["stage"] = "running"

    assert second.metadata == {}
