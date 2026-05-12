from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from gal_chara_skill.conf.module.log import LogPolicy


def test_log_policy_frozen() -> None:
    """验证 LogPolicy 为不可变数据类"""
    config = LogPolicy()

    with pytest.raises(FrozenInstanceError):
        config.level = "debug"  # pyright: ignore[reportAttributeAccessIssue]
