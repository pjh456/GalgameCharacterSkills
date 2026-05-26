from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import pytest

from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.conf.runtime import RuntimeConfig
from gal_chara_skill.core.paths import WorkspacePaths


def test_runtime_config_frozen() -> None:
    settings = RuntimeConfig(
        llm_config=LlmConfig(base_url="https://example.com", api_key="secret", model_name="test-model"),
        net_config=NetConfig(),
        workspace_paths=WorkspacePaths(project_root=Path("workspace")),
    )

    with pytest.raises(FrozenInstanceError):
        settings.log_policy = LogPolicy()  # pyright: ignore[reportAttributeAccessIssue]


def test_runtime_config_workspace_paths() -> None:
    workspace_paths = WorkspacePaths(project_root=Path("workspace"))
    net_config = NetConfig()
    llm_config = LlmConfig(base_url="https://example.com", api_key="secret", model_name="test-model")
    settings = RuntimeConfig(
        llm_config=llm_config,
        net_config=net_config,
        workspace_paths=workspace_paths,
    )

    assert settings.llm_config is llm_config
    assert settings.net_config is net_config
    assert settings.workspace_paths is workspace_paths
    assert settings.log_path_config is not None
    assert settings.log_path_config.root_dir == workspace_paths.logs_dir


def test_runtime_config_explicit_log_path_config() -> None:
    workspace_paths = WorkspacePaths(project_root=Path("workspace"))
    log_path_config = LogPathConfig(root_dir=Path("custom-logs"))
    settings = RuntimeConfig(
        llm_config=LlmConfig(base_url="https://example.com", api_key="secret", model_name="test-model"),
        net_config=NetConfig(),
        workspace_paths=workspace_paths,
        log_path_config=log_path_config,
    )

    assert settings.log_path_config is log_path_config
