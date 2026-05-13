from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.net import NetConfig


def test_net_config_frozen() -> None:
    """验证 NetConfig 为不可变数据类"""
    config = NetConfig()

    with pytest.raises(FrozenInstanceError):
        config.timeout = 30  # pyright: ignore[reportAttributeAccessIssue]


def test_net_config_defaults() -> None:
    """验证 NetConfig 会提供默认请求超时和重试次数"""
    config = NetConfig()

    assert config.timeout == 60
    assert config.max_retries == 3
