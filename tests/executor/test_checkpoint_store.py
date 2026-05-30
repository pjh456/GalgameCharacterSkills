from __future__ import annotations

from pathlib import Path

from gal_chara_skill.conf.checkpoint import TaskCheckpoint
from gal_chara_skill.conf.state import TaskState
from gal_chara_skill.conf.task import SliceSummaryTaskConfig, SliceConfig
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.conf.checkpoint import CheckpointStore
from gal_chara_skill.fs import JsonIO


def test_save_and_load(project_root: Path) -> None:
    workspace = WorkspacePaths(project_root=project_root)
    checkpoint_dir = workspace.checkpoints_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    store = CheckpointStore()
    task_config = SliceSummaryTaskConfig(
        role_name="TestChar",
        input_files=("a.txt",),
        slice_config=SliceConfig(max_tokens=1000, parallelism=2),
    )
    task_state = TaskState(task_id="test-001", current_stage="summarizing")
    checkpoint = TaskCheckpoint(task_config=task_config, task_state=task_state)

    save_result = store.save(checkpoint, workspace)
    assert save_result.ok is True

    load_result = store.load("test-001", workspace)
    assert load_result.ok is True
    restored = load_result.unwrap()
    assert restored is not None
    assert restored.task_state.task_id == "test-001"
    assert restored.task_state.current_stage == "summarizing"


def test_load_nonexistent(project_root: Path) -> None:
    workspace = WorkspacePaths(project_root=project_root)
    workspace.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    store = CheckpointStore()
    result = store.load("nonexistent", workspace)
    assert result.ok is True
    assert result.value is None
