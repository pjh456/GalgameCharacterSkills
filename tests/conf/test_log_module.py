from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.log import LOG_LEVEL_ORDER, LogConfig


def test_log_level_order_values() -> None:
    """验证日志级别排序映射值符合预期"""
    assert LOG_LEVEL_ORDER == {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "error": 40,
    }


def test_log_config_defaults() -> None:
    """验证 LogConfig 会使用预期默认值"""
    config = LogConfig()

    assert config.level == "info"
    assert config.write_to_console is False
    assert config.write_to_file is True
    assert config.default_file_name == "app.log"
    assert config.max_write_attempts == 3


def test_log_config_custom_values() -> None:
    """验证 LogConfig 会保存显式提供的配置值"""
    config = LogConfig(
        level="debug",
        write_to_console=True,
        write_to_file=False,
        default_file_name="task.log",
        max_write_attempts=5,
    )

    assert config == LogConfig(
        level="debug",
        write_to_console=True,
        write_to_file=False,
        default_file_name="task.log",
        max_write_attempts=5,
    )


def test_log_config_frozen() -> None:
    """验证 LogConfig 为不可变数据类"""
    config = LogConfig()

    with pytest.raises(FrozenInstanceError):
        config.level = "debug"  # pyright: ignore[reportAttributeAccessIssue]
