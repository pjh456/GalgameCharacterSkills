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
    """验证 set_global_settings 会注册全局设置对象"""
    config = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    set_global_settings(config)

    assert get_global_settings() is config


def test_set_global_settings_overwrites_previous_instance() -> None:
    """验证后一次 set_global_settings 会覆盖之前的全局设置"""
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
    set_global_settings(second)

    assert get_global_settings() is second


def test_global_settings_default_request_timeout() -> None:
    """验证 GlobalSettings 默认请求超时为 60"""
    settings = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    assert settings.request_timeout == 60


def test_global_settings_default_max_retries() -> None:
    """验证 GlobalSettings 默认最大重试次数为 3"""
    settings = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    assert settings.max_retries == 3


def test_global_settings_default_log_config() -> None:
    """验证未显式提供日志配置时，GlobalSettings 会使用默认 LogConfig"""
    settings = GlobalSettings(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

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
        settings.model_name = "other-model" # pyright: ignore[reportAttributeAccessIssue]
