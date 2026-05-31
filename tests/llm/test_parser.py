from __future__ import annotations

from gal_chara_skill.llm.parser import parse_llm_json_response


class TestParseLlmJsonResponse:
    def test_direct_json_object(self) -> None:
        result = parse_llm_json_response('{"key": "value"}')
        assert result.ok
        assert result.unwrap() == {"key": "value"}

    def test_direct_json_array(self) -> None:
        result = parse_llm_json_response("[1, 2, 3]")
        assert result.ok
        assert result.unwrap() == [1, 2, 3]

    def test_code_fence_json_tag(self) -> None:
        content = 'Some text\n```json\n{"a": 1}\n```\nMore text'
        result = parse_llm_json_response(content)
        assert result.ok
        assert result.unwrap() == {"a": 1}

    def test_code_fence_no_tag(self) -> None:
        content = '```\n{"b": 2}\n```'
        result = parse_llm_json_response(content)
        assert result.ok
        assert result.unwrap() == {"b": 2}

    def test_regex_brace_extraction(self) -> None:
        content = 'Here is data: {"x": [1, 2]} end'
        result = parse_llm_json_response(content)
        assert result.ok
        assert result.unwrap() == {"x": [1, 2]}

    def test_empty_content(self) -> None:
        result = parse_llm_json_response("")
        assert not result.ok
        assert result.code == "llm_parse_failed"

    def test_no_json_found(self) -> None:
        result = parse_llm_json_response("plain text no json here")
        assert not result.ok
        assert result.code == "llm_parse_failed"

    def test_malformed_json(self) -> None:
        result = parse_llm_json_response("{bad: json}")
        assert not result.ok
        assert result.code == "llm_parse_failed"
