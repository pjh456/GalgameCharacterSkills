from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.log import LogConfig
from gal_chara_skill.conf.runtime import RuntimeConfig


def test_runtime_config_log_config() -> None:
    """验证 RuntimeConfig 会保存显式提供的日志配置"""
    log_config = LogConfig(level="debug", write_to_console=True)
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
        log_config=log_config,
    )

    assert settings.log_config is log_config


def test_runtime_config_frozen() -> None:
    """验证 RuntimeConfig 为不可变数据类"""
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    with pytest.raises(FrozenInstanceError):
        settings.model_name = "other-model"  # pyright: ignore[reportAttributeAccessIssue]
