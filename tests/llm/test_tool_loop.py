import importlib.util
import sys
import types
import uuid
from pathlib import Path


def _load_tool_loop_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "galgame_character_skills" / "llm" / "tool_loop.py"

    pkg = sys.modules.get("galgame_character_skills")
    if pkg is None:
        pkg = types.ModuleType("galgame_character_skills")
        pkg.__path__ = [str(root / "galgame_character_skills")]
        sys.modules["galgame_character_skills"] = pkg

    llm_pkg = sys.modules.get("galgame_character_skills.llm")
    if llm_pkg is None:
        llm_pkg = types.ModuleType("galgame_character_skills.llm")
        llm_pkg.__path__ = [str(root / "galgame_character_skills" / "llm")]
        sys.modules["galgame_character_skills.llm"] = llm_pkg

    utils_pkg = sys.modules.get("galgame_character_skills.utils")
    if utils_pkg is None:
        utils_pkg = types.ModuleType("galgame_character_skills.utils")
        utils_pkg.__path__ = [str(root / "galgame_character_skills" / "utils")]
        sys.modules["galgame_character_skills.utils"] = utils_pkg

    dummy_ckpt_mod = types.ModuleType("galgame_character_skills.utils.checkpoint_manager")
    dummy_ckpt_mod.CheckpointManager = type("DummyCheckpointManager", (), {})
    sys.modules["galgame_character_skills.utils.checkpoint_manager"] = dummy_ckpt_mod

    mod_name = f"galgame_character_skills.llm.tool_loop_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tool_call(name, arguments, call_id="tc-1"):
    function = types.SimpleNamespace(name=name, arguments=arguments)
    return types.SimpleNamespace(id=call_id, function=function)


def _response_with_tool_calls(tool_calls, content=""):
    message = types.SimpleNamespace(content=content, tool_calls=tool_calls)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def _response_with_content(content):
    message = types.SimpleNamespace(content=content)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def test_run_character_card_tool_loop_success(monkeypatch):
    tool_loop = _load_tool_loop_module()
    saves = []

    class FakeCheckpointManager:
        def save_llm_state(self, checkpoint_id, **kwargs):
            saves.append((checkpoint_id, kwargs))

    monkeypatch.setattr(tool_loop, "CheckpointManager", FakeCheckpointManager)

    fields = {"name": "Alice", "description": "", "character_book_entries": [{"id": 1}]}
    messages = [{"role": "system", "content": "x"}]
    send_calls = {"count": 0}

    def fake_send_message(msgs, tools=None, use_counter=False):
        send_calls["count"] += 1
        if send_calls["count"] == 1:
            return _response_with_tool_calls(
                [_tool_call("write_field", '{"field_name":"description","content":"desc","is_complete":false}')],
                content="tool phase",
            )
        return _response_with_content('{"name":"Alice2"}')

    class FakeToolGateway:
        @staticmethod
        def parse_llm_json_response(content):
            return {"name": "Alice2"}

    result = tool_loop.run_character_card_tool_loop(
        send_message=fake_send_message,
        tool_gateway=FakeToolGateway(),
        tools=[{"type": "function"}],
        messages=messages,
        fields_data=fields,
        checkpoint_id="ckpt-1",
        initial_tool_call_count=0,
        max_tool_calls=5,
    )

    assert result["success"] is True
    assert fields["description"] == "desc"
    assert fields["name"] == "Alice2"
    assert send_calls["count"] == 2
    assert len(saves) >= 2
    assert "character_book_entries" not in saves[0][1]["fields_data"]


def test_run_character_card_tool_loop_failure_with_resume_flag(monkeypatch):
    tool_loop = _load_tool_loop_module()
    saves = []

    class FakeCheckpointManager:
        def save_llm_state(self, checkpoint_id, **kwargs):
            saves.append(kwargs)

    monkeypatch.setattr(tool_loop, "CheckpointManager", FakeCheckpointManager)

    result = tool_loop.run_character_card_tool_loop(
        send_message=lambda msgs, tools=None, use_counter=False: None,
        tool_gateway=types.SimpleNamespace(parse_llm_json_response=lambda x: {}),
        tools=[{"type": "function"}],
        messages=[{"role": "system", "content": "x"}],
        fields_data={"name": "A", "character_book_entries": []},
        checkpoint_id="ckpt-2",
        initial_tool_call_count=0,
        max_tool_calls=3,
    )

    assert result == {"success": False, "message": "LLM交互失败", "can_resume": True}
    assert any("last_response" in call and call["last_response"] is None for call in saves)
