from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.conf.runtime import RuntimeConfig


def test_runtime_config_log_policy() -> None:
    """验证 RuntimeConfig 会保存显式提供的日志行为配置"""
    log_policy = LogPolicy(level="debug", write_to_console=True)
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
        log_policy=log_policy,
    )

    assert settings.log_policy is log_policy


def test_runtime_config_log_path_config() -> None:
    """验证 RuntimeConfig 会保存显式提供的日志路径配置"""
    path_config = LogPathConfig(root_dir=Path("custom-logs"), default_file_name="task.log")
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
        log_path_config=path_config,
    )

    assert settings.log_path_config is path_config


def test_runtime_config_frozen() -> None:
    """验证 RuntimeConfig 为不可变数据类"""
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    with pytest.raises(FrozenInstanceError):
        settings.model_name = "other-model"  # pyright: ignore[reportAttributeAccessIssue]
