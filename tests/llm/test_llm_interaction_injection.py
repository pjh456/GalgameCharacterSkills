from galgame_character_skills.llm.llm_interaction import LLMInteraction
from galgame_character_skills.llm import llm_interaction as llm_interaction_module


class _FakeRuntime:
    def __init__(self):
        self.events = []

    def log_request_start(self, **kwargs):
        self.events.append(("start", kwargs))

    def log_request_success(self, **kwargs):
        self.events.append(("success", kwargs))

    def log_response_preview(self, response):
        self.events.append(("preview", response))

    def log_request_failed(self, **kwargs):
        self.events.append(("failed", kwargs))


class _FakeTransport:
    def __init__(self):
        self.last_kwargs = None
        self.last_retries = None

    def complete_with_retry(
        self,
        kwargs,
        max_retries,
        on_attempt_failed=None,
        on_retry_wait=None,
        on_success=None,
        on_final_failure=None,
    ):
        self.last_kwargs = kwargs
        self.last_retries = max_retries
        response = {"mock": True}
        if on_success:
            on_success(response)
        return response


def test_llm_interaction_uses_injected_runtime_and_transport():
    runtime = _FakeRuntime()
    transport = _FakeTransport()
    tool_gateway = object()
    client = LLMInteraction(tool_gateway=tool_gateway, transport=transport, runtime=runtime)
    client.set_config(baseurl="https://api.deepseek.com", modelname="chat-model", apikey="secret-key", max_retries=5)

    response = client.send_message(messages=[{"role": "user", "content": "hello"}], tools=None, use_counter=False)

    assert response == {"mock": True}
    assert client.tool_gateway is tool_gateway
    assert transport.last_retries == 5
    assert transport.last_kwargs["model"] == "deepseek/chat-model"
    assert transport.last_kwargs["api_key"] == "secret-key"
    assert transport.last_kwargs["api_base"] == "https://api.deepseek.com"
    assert any(event[0] == "start" for event in runtime.events)
    assert any(event[0] == "success" for event in runtime.events)
    assert any(event[0] == "preview" for event in runtime.events)

def test_build_runtime_delegates_to_runtime_class():
    class _RuntimeClass:
        def __init__(self, total_requests=0):
            self.total_requests = total_requests

    original_runtime_cls = LLMInteraction._runtime_cls
    try:
        LLMInteraction._runtime_cls = _RuntimeClass
        runtime = LLMInteraction.build_runtime(11)
        assert isinstance(runtime, _RuntimeClass)
        assert runtime.total_requests == 11
    finally:
        LLMInteraction._runtime_cls = original_runtime_cls


def test_generate_character_card_with_tools_delegates_to_flow(monkeypatch):
    captured = {}
    client = LLMInteraction(tool_gateway="gateway", transport=_FakeTransport(), runtime=_FakeRuntime())

    def fake_generate_character_card(**kwargs):
        captured.update(kwargs)
        return {"success": True}

    monkeypatch.setattr(llm_interaction_module, "generate_character_card", fake_generate_character_card)

    result = client.generate_character_card_with_tools(
        role_name="Alice",
        all_analyses=[{"a": 1}],
        all_lorebook_entries=[{"entry": 1}],
        output_path="out.json",
        creator="me",
        vndb_data={"name": "Alice"},
        output_language="zh",
        checkpoint_id="ckpt-1",
        ckpt_messages=[{"role": "assistant", "content": "x"}],
        ckpt_fields_data={"name": "Alice"},
        ckpt_iteration_count=3,
        save_llm_state_fn="save-fn",
    )

    assert result == {"success": True}
    assert captured["tool_gateway"] == "gateway"
    assert captured["lang_names"] == {"zh": "中文", "en": "English", "ja": "日本語"}
    assert callable(captured["format_vndb_section"])
    assert captured["role_name"] == "Alice"
    assert captured["output_path"] == "out.json"
