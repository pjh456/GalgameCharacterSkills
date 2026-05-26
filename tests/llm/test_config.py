from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gal_chara_skill.conf.module.llm import LlmConfig


def test_llm_config_frozen() -> None:
    config = LlmConfig(base_url="https://api.example.com", api_key="key", model_name="model")
    with pytest.raises(FrozenInstanceError):
        config.provider = "other"  # pyright: ignore[reportAttributeAccessIssue]


def test_llm_config_defaults() -> None:
    config = LlmConfig(base_url="https://api.example.com", api_key="key", model_name="model")
    assert config.provider == "openai"
    assert config.provider_options == {}


def test_llm_config_explicit_provider() -> None:
    config = LlmConfig(
        base_url="https://api.example.com",
        api_key="key",
        model_name="model",
        provider="openai",
        provider_options={"timeout_override": 120},
    )
    assert config.provider == "openai"
    assert config.provider_options == {"timeout_override": 120}
