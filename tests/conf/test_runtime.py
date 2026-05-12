from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import pytest

from gal_chara_skill.conf.module.log import LogPathConfig
from gal_chara_skill.conf.runtime import RuntimeConfig
from gal_chara_skill.core.paths import WorkspacePaths


def test_runtime_config_frozen() -> None:
    """验证 RuntimeConfig 为不可变数据类"""
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    with pytest.raises(FrozenInstanceError):
        settings.model_name = "other-model"  # pyright: ignore[reportAttributeAccessIssue]


def test_runtime_config_workspace_paths() -> None:
    """验证 RuntimeConfig 支持显式注入工作区路径布局"""
    workspace_paths = WorkspacePaths(project_root=Path("workspace"))
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
        workspace_paths=workspace_paths,
    )

    assert settings.workspace_paths is workspace_paths
    assert settings.log_path_config is not None
    assert settings.log_path_config.root_dir == workspace_paths.logs_dir


def test_runtime_config_explicit_log_path_config() -> None:
    """验证 RuntimeConfig 不会覆盖显式提供的日志路径配置"""
    workspace_paths = WorkspacePaths(project_root=Path("workspace"))
    log_path_config = LogPathConfig(root_dir=Path("custom-logs"))
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
        workspace_paths=workspace_paths,
        log_path_config=log_path_config,
    )

    assert settings.log_path_config is log_path_config
