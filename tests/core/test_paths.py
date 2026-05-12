from __future__ import annotations

from pathlib import Path

from gal_chara_skill.core.paths import WorkspacePaths


def test_workspace_paths_derives_standard_directories() -> None:
    """验证 WorkspacePaths 会按约定派生标准工作区目录"""
    workspace_paths = WorkspacePaths(project_root=Path("workspace"))

    assert workspace_paths.input_dir == Path("workspace/input")
    assert workspace_paths.output_dir == Path("workspace/output")
    assert workspace_paths.slices_dir == Path("workspace/output/slices")
    assert workspace_paths.checkpoints_dir == Path("workspace/output/checkpoints")
    assert workspace_paths.summaries_dir == Path("workspace/output/summaries")
    assert workspace_paths.skills_dir == Path("workspace/output/skills")
    assert workspace_paths.cards_dir == Path("workspace/output/cards")
    assert workspace_paths.logs_dir == Path("workspace/output/logs")
