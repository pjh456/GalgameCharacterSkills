from __future__ import annotations

import pytest

from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.llm.models import ChatCompletionRequest, ChatMessage
from gal_chara_skill.llm.providers.openai import OpenAIProvider, _dedup_path
from gal_chara_skill.llm.providers.registry import ProviderNotFoundError, resolve_provider


class TestDedupPath:
    def test_no_duplicate(self) -> None:
        result = _dedup_path("https://api.openai.com", "/v1/chat/completions", version_prefix="/v1")
        assert result == "https://api.openai.com/v1/chat/completions"

    def test_strips_duplicate_prefix(self) -> None:
        result = _dedup_path("https://api.openai.com/v1", "/v1/chat/completions", version_prefix="/v1")
        assert result == "https://api.openai.com/v1/chat/completions"

    def test_strips_duplicate_with_trailing_slash(self) -> None:
        result = _dedup_path("https://api.openai.com/v1/", "/v1/chat/completions", version_prefix="/v1")
        assert result == "https://api.openai.com/v1/chat/completions"

    def test_no_match_different_prefix(self) -> None:
        result = _dedup_path("https://api.openai.com/v1", "/v1beta/models", version_prefix="/v1beta")
        assert result == "https://api.openai.com/v1/v1beta/models"


class TestResolveProvider:
    def test_resolve_openai(self) -> None:
        provider = resolve_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_resolve_unknown_raises(self) -> None:
        with pytest.raises(ProviderNotFoundError, match="Unknown provider"):
            resolve_provider("anthropic")


class TestOpenAIProvider:
    def _make_config(self, *, base_url: str = "https://api.openai.com") -> LlmConfig:
        return LlmConfig(base_url=base_url, api_key="test-key", model_name="test-model")

    def test_chat_path(self) -> None:
        provider = OpenAIProvider()
        config = self._make_config()
        result = provider.chat_path(config)
        assert result == "https://api.openai.com/v1/chat/completions"

    def test_chat_path_avoid_duplicate_v1(self) -> None:
        provider = OpenAIProvider()
        config = self._make_config(base_url="https://api.openai.com/v1")
        result = provider.chat_path(config)
        assert result == "https://api.openai.com/v1/chat/completions"

    def test_chat_headers(self) -> None:
        provider = OpenAIProvider()
        config = self._make_config()
        headers = provider.chat_headers(config)
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"

    def test_build_chat_request(self) -> None:
        provider = OpenAIProvider()
        request = ChatCompletionRequest(
            model="test-model",
            messages=[ChatMessage(role="user", content="hello")],
            temperature=0.5,
            max_tokens=100,
        )
        body = provider.build_chat_request(request)
        assert body == {
            "model": "test-model",
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.5,
            "max_tokens": 100,
        }

    def test_parse_chat_response(self) -> None:
        provider = OpenAIProvider()
        data = {
            "id": "chatcmpl-001",
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        result = provider.parse_chat_response(data, url="https://test/api")
        assert result.ok is True
        assert result.unwrap().id == "chatcmpl-001"
