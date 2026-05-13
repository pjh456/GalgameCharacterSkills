from __future__ import annotations

from gal_chara_skill.fs import EnvIO


def test_read(project_root) -> None:
    """验证 read 会正确处理有效内容、注释空行、缺失文件与非法行"""
    valid_path = project_root / "valid.env"
    quoted_path = project_root / "quoted.env"
    broken_path = project_root / "broken.env"
    empty_key_path = project_root / "empty-key.env"
    missing_path = project_root / ".env"
    valid_path.write_text("API_KEY=secret\nMODEL=gpt\n", encoding="utf-8")
    quoted_path.write_text('\n# comment\nNAME="alice"\nROLE=\'character\'\n', encoding="utf-8")
    broken_path.write_text("BROKEN\n", encoding="utf-8")
    empty_key_path.write_text(" =value\n", encoding="utf-8")

    valid_result = EnvIO.read(valid_path)
    quoted_result = EnvIO.read(quoted_path)
    missing_result = EnvIO.read(missing_path)
    broken_result = EnvIO.read(broken_path)
    empty_key_result = EnvIO.read(empty_key_path)

    assert valid_result.unwrap() == {"API_KEY": "secret", "MODEL": "gpt"}
    assert quoted_result.unwrap() == {"NAME": "alice", "ROLE": "character"}
    assert missing_result.ok is False
    assert missing_result.data["source"] == "env"
    assert broken_result.ok is False
    assert empty_key_result.ok is False


def test_write(project_root) -> None:
    """验证 write 写出的常见值形态都可以被 read 正确读回"""
    values_list = [
        {"API_KEY": "secret", "MODEL": "gpt"},
        {"DISPLAY_NAME": "alice scene"},
        {"PROMPT": "hello # world"},
        {"EMPTY": ""},
        {"QUOTE": 'say "hello"'},
    ]

    for index, values in enumerate(values_list):
        target = project_root / f"{index}.env"

        result = EnvIO.write(target, values)

        assert result.ok is True
        assert EnvIO.read(target).unwrap() == values


def test_write_empty(project_root) -> None:
    """验证 write 会为非空映射追加换行，并能写出空映射"""
    non_empty_target = project_root / "non-empty.env"
    empty_target = project_root / "empty.env"

    EnvIO.write(non_empty_target, {"API_KEY": "secret"})
    EnvIO.write(empty_target, {})

    assert non_empty_target.read_text(encoding="utf-8").endswith("\n")
    assert empty_target.read_text(encoding="utf-8") == ""
