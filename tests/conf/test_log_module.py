from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.log import LOG_LEVEL_ORDER, LogConfig


def test_log_level_order_debug() -> None:
    """验证 debug 级别排序值为 10"""
    assert LOG_LEVEL_ORDER["debug"] == 10


def test_log_level_order_info() -> None:
    """验证 info 级别排序值为 20"""
    assert LOG_LEVEL_ORDER["info"] == 20


def test_log_level_order_warning() -> None:
    """验证 warning 级别排序值为 30"""
    assert LOG_LEVEL_ORDER["warning"] == 30


def test_log_level_order_error() -> None:
    """验证 error 级别排序值为 40"""
    assert LOG_LEVEL_ORDER["error"] == 40


def test_log_config_default_level() -> None:
    """验证 LogConfig 默认日志级别为 info"""
    config = LogConfig()

    assert config.level == "info"


def test_log_config_default_write_to_console() -> None:
    """验证 LogConfig 默认不开启控制台输出"""
    config = LogConfig()

    assert config.write_to_console is False


def test_log_config_default_write_to_file() -> None:
    """验证 LogConfig 默认开启文件输出"""
    config = LogConfig()

    assert config.write_to_file is True


def test_log_config_default_file_name() -> None:
    """验证 LogConfig 默认日志文件名为 app.log"""
    config = LogConfig()

    assert config.default_file_name == "app.log"


def test_log_config_default_max_write_attempts() -> None:
    """验证 LogConfig 默认最大写入次数为 3"""
    config = LogConfig()

    assert config.max_write_attempts == 3


def test_log_config_custom_values() -> None:
    """验证 LogConfig 会保存显式提供的多个配置值"""
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


def test_log_config_custom_level() -> None:
    """验证 LogConfig 会保存显式提供的日志级别"""
    config = LogConfig(level="debug")

    assert config.level == "debug"


def test_log_config_custom_write_to_console() -> None:
    """验证 LogConfig 会保存显式提供的控制台输出开关"""
    config = LogConfig(write_to_console=True)

    assert config.write_to_console is True


def test_log_config_custom_write_to_file() -> None:
    """验证 LogConfig 会保存显式提供的文件输出开关"""
    config = LogConfig(write_to_file=False)

    assert config.write_to_file is False


def test_log_config_custom_file_name() -> None:
    """验证 LogConfig 会保存显式提供的日志文件名"""
    config = LogConfig(default_file_name="task.log")

    assert config.default_file_name == "task.log"


def test_log_config_custom_max_write_attempts() -> None:
    """验证 LogConfig 会保存显式提供的最大写入次数"""
    config = LogConfig(max_write_attempts=5)

    assert config.max_write_attempts == 5


def test_log_config_frozen() -> None:
    """验证 LogConfig 为不可变数据类"""
    config = LogConfig()

    with pytest.raises(FrozenInstanceError):
        config.level = "debug" # pyright: ignore[reportAttributeAccessIssue]
