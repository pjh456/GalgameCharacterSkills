from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from gal_chara_skill.conf.runtime import RuntimeConfig


def test_runtime_config_frozen() -> None:
    """验证 RuntimeConfig 为不可变数据类"""
    settings = RuntimeConfig(
        base_url="https://example.com",
        api_key="secret",
        model_name="test-model",
    )

    with pytest.raises(FrozenInstanceError):
        settings.model_name = "other-model"  # pyright: ignore[reportAttributeAccessIssue]
