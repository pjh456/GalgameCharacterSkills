from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.log import LogConfig


def test_log_config() -> None:
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
