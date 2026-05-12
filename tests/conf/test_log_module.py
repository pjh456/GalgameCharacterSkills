from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from gal_chara_skill.conf.module.log import LogPathConfig, LogPolicy
from gal_chara_skill.core.paths import LOGS_DIR


def test_log_policy() -> None:
    """验证 LogPolicy 会保存显式提供的配置值"""
    config = LogPolicy(
        level="debug",
        write_to_console=True,
        write_to_file=False,
        max_write_attempts=5,
    )

    assert config == LogPolicy(
        level="debug",
        write_to_console=True,
        write_to_file=False,
        max_write_attempts=5,
    )


def test_log_policy_frozen() -> None:
    """验证 LogPolicy 为不可变数据类"""
    config = LogPolicy()

    with pytest.raises(FrozenInstanceError):
        config.level = "debug"  # pyright: ignore[reportAttributeAccessIssue]


def test_log_path_config() -> None:
    """验证 LogPathConfig 会保存显式提供的路径配置值"""
    config = LogPathConfig(root_dir=Path("custom-logs"), default_file_name="task.log")

    assert config == LogPathConfig(
        root_dir=Path("custom-logs"),
        default_file_name="task.log",
    )


def test_log_path_config_default_root() -> None:
    """验证 LogPathConfig 默认使用核心层定义的日志目录"""
    config = LogPathConfig()

    assert config.root_dir == LOGS_DIR
