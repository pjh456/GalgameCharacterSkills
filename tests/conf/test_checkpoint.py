from __future__ import annotations

from pathlib import Path

import pytest
from gal_chara_skill.conf.checkpoint import CheckpointStore, TaskCheckpoint
from gal_chara_skill.conf.state import SliceState, TaskState
from gal_chara_skill.conf.task import (
    GenerationTaskConfig,
    SliceConfig,
    SliceSummaryTaskConfig,
)
from gal_chara_skill.core.paths import WorkspacePaths
from gal_chara_skill.core.result import Result
from gal_chara_skill.fs import json


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


def test_save_and_load(project_root: Path) -> None:
    """验证 checkpoint 可以保存到标准工作区并读回"""
    workspace_paths = WorkspacePaths(project_root=project_root)
    store = CheckpointStore(workspace_paths)
    source = TaskCheckpoint(
        task_config=SliceSummaryTaskConfig(
            role_name="Alice",
            input_files=("script.txt",),
        ),
        task_state=TaskState(task_id="task-003"),
    )

    save_result = store.save(source)
    load_result = store.load("task-003")

    assert save_result.ok is True
    assert save_result.unwrap() == project_root / "output/checkpoints/task-003.json"
    assert load_result.unwrap() == source


def test_load_missing(project_root: Path) -> None:
    """验证 load 在 checkpoint 文件不存在时返回失败结果"""
    workspace_paths = WorkspacePaths(project_root=project_root)
    store = CheckpointStore(workspace_paths)

    result = store.load("missing")

    assert result.ok is False
    assert result.code == "fs_not_found"


def test_load_invalid_json(project_root: Path) -> None:
    """验证 load 在 checkpoint JSON 无法解析时返回失败结果"""
    workspace_paths = WorkspacePaths(project_root=project_root)
    store = CheckpointStore(workspace_paths)
    target = store.get_path("broken")
    target.parent.mkdir(parents=True)
    target.write_text("{broken", encoding="utf-8")

    result = store.load("broken")

    assert result.ok is False
    assert result.code == "fs_parse_failed"


def test_load_unknown_task_kind(project_root: Path) -> None:
    """验证 load 在任务类型未知时返回失败结果"""
    workspace_paths = WorkspacePaths(project_root=project_root)
    store = CheckpointStore(workspace_paths)
    target = store.get_path("unknown")
    json.write(
        target,
        {
            "task_config": {
                "kind": "other",
                "role_name": "Alice",
            },
            "task_state": {
                "task_id": "unknown",
            },
        },
    )

    result = store.load("unknown")

    assert result.ok is False
    assert result.code == "checkpoint_unknown_task_kind"


def test_load_invalid_checkpoint_shape(project_root: Path) -> None:
    """验证 load 会把 checkpoint 结构错误包装为带路径的失败结果"""
    workspace_paths = WorkspacePaths(project_root=project_root)
    store = CheckpointStore(workspace_paths)
    target = store.get_path("invalid")
    json.write(target, [])

    result = store.load("invalid")

    assert result.ok is False
    assert result.code == "checkpoint_invalid"
    assert result.data["checkpoint_path"] == str(target)


def test_save_failure(monkeypatch: pytest.MonkeyPatch, project_root: Path) -> None:
    """验证 save 会包装底层写入失败并保留 checkpoint 路径"""
    workspace_paths = WorkspacePaths(project_root=project_root)
    store = CheckpointStore(workspace_paths)
    source = TaskCheckpoint(
        task_config=SliceSummaryTaskConfig(
            role_name="Alice",
            input_files=("script.txt",),
        ),
        task_state=TaskState(task_id="task-004"),
    )

    def fail_write(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return Result.failure(
            "cannot write",
            code="fs_write_failed",
            path="raw-path",
        )

    monkeypatch.setattr("gal_chara_skill.conf.checkpoint.fs.json.write", fail_write)

    result = store.save(source)

    assert result.ok is False
    assert result.code == "fs_write_failed"
    assert result.data["path"] == "raw-path"
    assert result.data["checkpoint_path"] == str(
        workspace_paths.checkpoints_dir / "task-004.json"
    )


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
    assert invalid_slice_config_result.ok is False
    assert invalid_generation_result.ok is False
    assert invalid_state_result.ok is False
    assert invalid_slice_state_result.ok is False
