from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.log import LogConfig
from gal_chara_skill.conf.settings import GlobalSettings, get_global_settings, set_global_settings


def test_get_global_settings_uninitialized() -> None:
    """验证未初始化全局设置时，get_global_settings 会抛出异常"""
    with pytest.raises(RuntimeError):
        get_global_settings()


def test_set_global_settings_registers_instance() -> None:
    """验证 set_global_settings 会注册并覆盖全局设置对象"""
    first = GlobalSettings(
        base_url="https://first.example.com",
        api_key="first",
        model_name="model-a",
    )
    second = GlobalSettings(
        base_url="https://second.example.com",
        api_key="second",
        model_name="model-b",
    )

    set_global_settings(first)
    assert get_global_settings() is first

    set_global_settings(second)
    assert get_global_settings() is second


def test_global_settings_defaults() -> None:
    """验证 GlobalSettings 会使用预期默认值"""
    settings = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    assert settings.request_timeout == 60
    assert settings.max_retries == 3
    assert settings.log_config == LogConfig()


def test_global_settings_custom_log_config() -> None:
    """验证 GlobalSettings 会保存显式提供的日志配置"""
    log_config = LogConfig(level="debug", write_to_console=True)
    settings = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
        log_config=log_config,
    )

    assert settings.log_config is log_config


def test_global_settings_frozen() -> None:
    """验证 GlobalSettings 为不可变数据类"""
    settings = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    with pytest.raises(FrozenInstanceError):
        settings.model_name = "other-model"  # pyright: ignore[reportAttributeAccessIssue]
