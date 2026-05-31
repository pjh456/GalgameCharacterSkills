from __future__ import annotations

import asyncio

import pytest

from gal_chara_skill.conf.module.llm import LlmConfig
from gal_chara_skill.conf.module.net import NetConfig
from gal_chara_skill.core.result import Result
from gal_chara_skill.llm.client import LlmClient
from gal_chara_skill.llm.errors import LlmErrors
from gal_chara_skill.llm.models import ChatCompletion, ChatCompletionRequest, ChatMessage
from gal_chara_skill.llm.providers.openai import OpenAIProvider
from gal_chara_skill.net.client import NetClient
from gal_chara_skill.net.models import HttpResponse, JsonResponse


def _make_chat_response(data: dict) -> JsonResponse:
    return JsonResponse(
        response=HttpResponse(
            status_code=200,
            url="https://api.example.com/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            body=b"",
        ),
        data=data,
    )


def build_minimal_response() -> dict:
    return {
        "id": "chatcmpl-001",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "model": "test-model",
        "created": 1234567890,
    }


def build_flat_response() -> dict:
    return {
        "message": {"role": "assistant", "content": "Hello!"},
        "finish_reason": "stop",
        "id": "chatcmpl-001",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "model": "test-model",
        "created": 1234567890,
    }


class TestChatMessage:
    def test_to_dict(self) -> None:
        msg = ChatMessage(role="user", content="hello")
        assert msg.to_dict() == {"role": "user", "content": "hello"}

    def test_from_dict_valid(self) -> None:
        result = ChatMessage.from_dict({"role": "user", "content": "hello"})
        assert result.unwrap() == ChatMessage(role="user", content="hello")

    def test_from_dict_invalid_role(self) -> None:
        result = ChatMessage.from_dict({"role": "admin", "content": "hello"})
        assert result.ok is False

    def test_from_dict_empty_content(self) -> None:
        result = ChatMessage.from_dict({"role": "user", "content": ""})
        assert result.ok is True

    def test_from_dict_missing_field(self) -> None:
        result = ChatMessage.from_dict({"role": "user"})
        assert result.ok is True

    def test_from_dict_not_dict(self) -> None:
        result = ChatMessage.from_dict("invalid")
        assert result.ok is False


class TestChatCompletion:
    def test_from_dict_valid(self) -> None:
        data = build_flat_response()
        result = ChatCompletion.from_dict(data)
        completion = result.unwrap()

        assert completion.id == "chatcmpl-001"
        assert completion.message.role == "assistant"
        assert completion.message.content == "Hello!"
        assert completion.usage.prompt_tokens == 10
        assert completion.usage.completion_tokens == 5

    def test_from_dict_missing_id(self) -> None:
        result = ChatCompletion.from_dict({})
        assert result.ok is False


class TestOpenAIProvider:
    def test_parse_chat_response_valid(self) -> None:
        data = build_minimal_response()
        provider = OpenAIProvider()
        result = provider.parse_chat_response(data, url="https://test/api")
        assert result.ok is True
        assert result.unwrap().id == "chatcmpl-001"

    def test_parse_chat_response_missing_choices(self) -> None:
        provider = OpenAIProvider()
        result = provider.parse_chat_response({}, url="https://test/api")
        assert result.ok is False

    def test_parse_chat_response_empty_choices(self) -> None:
        provider = OpenAIProvider()
        data = {**build_minimal_response(), "choices": []}
        result = provider.parse_chat_response(data, url="https://test/api")
        assert result.ok is False

    def test_parse_chat_response_not_dict(self) -> None:
        provider = OpenAIProvider()
        result = provider.parse_chat_response("invalid", url="https://test/api")
        assert result.ok is False
        assert result.code == "llm_parse_failed"
        assert result.data["url"] == "https://test/api"

    def test_parse_chat_response_inner_failure(self) -> None:
        provider = OpenAIProvider()
        result = provider.parse_chat_response({"choices": [{}]}, url="https://test/api")
        assert result.ok is False


class TestLlmErrors:
    def test_completion_parse_failed(self) -> None:
        upstream = Result.failure("boom", code="net_http_error", status_code=500)
        result = LlmErrors.completion_parse_failed("https://test/api", upstream)
        assert result.ok is False
        assert result.code == "net_http_error"
        assert result.data["url"] == "https://test/api"


class TestLlmClient:
    def _make_client(
        self,
        *,
        base_url: str = "https://api.example.com",
        api_key: str = "test-key",
        model_name: str = "test-model",
    ) -> LlmClient:
        config = LlmConfig(base_url=base_url, api_key=api_key, model_name=model_name)
        net_client = NetClient(NetConfig())
        return LlmClient(config=config, net_client=net_client)

    def test_request_to_dict(self) -> None:
        messages = [ChatMessage(role="user", content="hello")]
        request = ChatCompletionRequest(
            model="test-model",
            messages=messages,
            temperature=0.5,
            max_tokens=100,
        )

        body = request.to_dict()

        assert body["model"] == "test-model"
        assert body["messages"] == [{"role": "user", "content": "hello"}]
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 100

    def test_request_to_dict_with_extra(self) -> None:
        messages = [ChatMessage(role="system", content="prompt")]
        request = ChatCompletionRequest(
            model="test-model",
            messages=messages,
            temperature=0.0,
            max_tokens=10,
            extra={"top_p": 0.9},
        )

        body = request.to_dict()

        assert body["top_p"] == 0.9

    def test_complete_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()
        response_data = build_minimal_response()

        def fake_request_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.success(_make_chat_response(response_data))

        monkeypatch.setattr(client.net_client, "request_json", fake_request_json)

        messages = [ChatMessage(role="user", content="hello")]
        result = client.complete(messages)

        assert result.ok is True
        completion = result.unwrap()
        assert completion.message.content == "Hello!"

    def test_complete_net_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()

        def fake_request_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.failure("网络错误", code="net_http_error", status_code=500)

        monkeypatch.setattr(client.net_client, "request_json", fake_request_json)

        result = client.complete([ChatMessage(role="user", content="hello")])

        assert result.ok is False

    def test_complete_parse_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()
        bad_data = {"id": "x", "choices": []}

        def fake_request_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.success(_make_chat_response(bad_data))

        monkeypatch.setattr(client.net_client, "request_json", fake_request_json)

        result = client.complete([ChatMessage(role="user", content="hello")])

        assert result.ok is False

    def test_acomplete_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()
        response_data = build_minimal_response()

        async def fake_arequest_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.success(_make_chat_response(response_data))

        monkeypatch.setattr(client.net_client, "arequest_json", fake_arequest_json)

        async def main() -> None:
            messages = [ChatMessage(role="user", content="hello")]
            result = await client.acomplete(messages)
            assert result.ok is True
            assert result.unwrap().message.content == "Hello!"

        asyncio.run(main())


class TestAsyncNativeClient:
    """Tests for native async acomplete + acomplete_with_tools after refactoring."""

    def _make_client(
        self,
        *,
        base_url: str = "https://api.example.com",
        api_key: str = "test-key",
        model_name: str = "test-model",
    ) -> LlmClient:
        config = LlmConfig(base_url=base_url, api_key=api_key, model_name=model_name)
        net_client = NetClient(NetConfig())
        return LlmClient(config=config, net_client=net_client)

    @pytest.mark.asyncio
    async def test_acomplete_native_async_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()
        response_data = build_minimal_response()

        async def fake_arequest_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.success(_make_chat_response(response_data))

        monkeypatch.setattr(client.net_client, "arequest_json", fake_arequest_json)

        messages = [ChatMessage(role="user", content="hello")]
        result = await client.acomplete(messages)
        assert result.ok
        assert result.unwrap().message.content == "Hello!"

    @pytest.mark.asyncio
    async def test_acomplete_native_async_net_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()

        async def fake_arequest_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.failure("网络错误", code="net_http_error", status_code=500)

        monkeypatch.setattr(client.net_client, "arequest_json", fake_arequest_json)

        messages = [ChatMessage(role="user", content="hello")]
        result = await client.acomplete(messages)
        assert not result.ok

    @pytest.mark.asyncio
    async def test_acomplete_with_tools_single_round(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()
        response_data = build_minimal_response()

        call_count = 0

        async def fake_arequest_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            nonlocal call_count
            call_count += 1
            return Result.success(_make_chat_response(response_data))

        monkeypatch.setattr(client.net_client, "arequest_json", fake_arequest_json)

        messages = [ChatMessage(role="user", content="hello")]
        result = await client.acomplete_with_tools(
            messages,
            tools=[],
            tool_handler=lambda tc: ChatMessage(role="tool", content="ok", tool_call_id=tc.id),
        )
        assert result.ok
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_acomplete_with_tools_multi_round(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()

        rounds = [0]

        def build_tool_call_response() -> dict:
            if rounds[0] == 0:
                return {
                    "id": "chatcmpl-tc",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "write_file",
                                    "arguments": '{"file_path": "/test.md", "content": "hi"}',
                                },
                            }],
                        },
                        "finish_reason": "tool_calls",
                    }],
                }
            return build_minimal_response()

        async def fake_arequest_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            data = build_tool_call_response()
            rounds[0] += 1
            return Result.success(_make_chat_response(data))

        monkeypatch.setattr(client.net_client, "arequest_json", fake_arequest_json)

        messages = [ChatMessage(role="user", content="hello")]
        result = await client.acomplete_with_tools(
            messages,
            tools=[],
            tool_handler=lambda tc: ChatMessage(role="tool", content="ok", tool_call_id=tc.id),
        )
        assert result.ok
        assert rounds[0] == 2

    @pytest.mark.asyncio
    async def test_acomplete_with_tools_exhaustion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._make_client()

        tool_call_data = {
            "id": "chatcmpl-loop",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_loop",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": '{"file_path": "/test.md", "content": "loop"}',
                        },
                    }],
                },
                "finish_reason": "tool_calls",
            }],
        }

        async def fake_arequest_json(*args: object, **kwargs: object) -> Result[JsonResponse]:
            return Result.success(_make_chat_response(tool_call_data))

        monkeypatch.setattr(client.net_client, "arequest_json", fake_arequest_json)

        messages = [ChatMessage(role="user", content="hello")]
        result = await client.acomplete_with_tools(
            messages,
            tools=[],
            tool_handler=lambda tc: ChatMessage(role="tool", content="ok", tool_call_id=tc.id),
            max_iterations=2,
        )
        assert not result.ok
        assert result.code == "tool_loop_exhausted"