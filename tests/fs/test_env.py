from __future__ import annotations

from gal_chara_skill.fs import env


def test_read_success(project_root) -> None:
    """验证 read 会读取 .env 键值对内容"""
    target = project_root / ".env"
    target.write_text("API_KEY=secret\nMODEL=gpt\n", encoding="utf-8")

    result = env.read(target)

    assert result.unwrap() == {"API_KEY": "secret", "MODEL": "gpt"}


def test_read_ignores_blank_lines_and_comments(project_root) -> None:
    """验证 read 会跳过空行与注释行"""
    target = project_root / ".env"
    target.write_text("\n# comment\nAPI_KEY=secret\n", encoding="utf-8")

    result = env.read(target)

    assert result.unwrap() == {"API_KEY": "secret"}


def test_read_strips_quoted_value(project_root) -> None:
    """验证 read 会移除值外层的成对引号"""
    target = project_root / ".env"
    target.write_text('NAME="alice"\nROLE=\'character\'\n', encoding="utf-8")

    result = env.read(target)

    assert result.unwrap() == {"NAME": "alice", "ROLE": "character"}


def test_read_missing_file(project_root) -> None:
    """验证 read 在文件不存在时会返回失败结果"""
    result = env.read(project_root / ".env")

    assert result.ok is False


def test_read_missing_file_code(project_root) -> None:
    """验证 read 在文件不存在时会返回底层错误码"""
    result = env.read(project_root / ".env")

    assert result.code == "fs_not_found"

def test_read_missing_file_source(project_root) -> None:
    """验证 read 在底层读取失败时会补充 env 来源信息"""
    result = env.read(project_root / ".env")

    assert result.data["source"] == "env"


def test_read_invalid_line(project_root) -> None:
    """验证 read 在行内缺少等号时会返回失败结果"""
    target = project_root / ".env"
    target.write_text("BROKEN\n", encoding="utf-8")

    result = env.read(target)

    assert result.ok is False


def test_read_invalid_line_code(project_root) -> None:
    """验证 read 在行内缺少等号时会返回固定错误码"""
    target = project_root / ".env"
    target.write_text("BROKEN\n", encoding="utf-8")

    result = env.read(target)

    assert result.code == "fs_parse_failed"


def test_read_empty_key(project_root) -> None:
    """验证 read 在键名为空时会返回失败结果"""
    target = project_root / ".env"
    target.write_text(" =value\n", encoding="utf-8")

    result = env.read(target)

    assert result.ok is False


def test_write_success(project_root) -> None:
    """验证 write 会写入 .env 键值对内容"""
    target = project_root / ".env"

    result = env.write(target, {"API_KEY": "secret", "MODEL": "gpt"})

    assert result.ok is True
    assert env.read(target).unwrap() == {"API_KEY": "secret", "MODEL": "gpt"}


def test_write_quotes_space_value(project_root) -> None:
    """验证 write 处理包含空白字符的值后仍可被正确读回"""
    target = project_root / ".env"
    values = {"DISPLAY_NAME": "alice scene"}

    env.write(target, values)

    assert env.read(target).unwrap() == values


def test_write_quotes_hash_value(project_root) -> None:
    """验证 write 处理包含井号的值后仍可被正确读回"""
    target = project_root / ".env"
    values = {"PROMPT": "hello # world"}

    env.write(target, values)

    assert env.read(target).unwrap() == values


def test_write_empty_value(project_root) -> None:
    """验证 write 处理空字符串后仍可被正确读回"""
    target = project_root / ".env"
    values = {"EMPTY": ""}

    env.write(target, values)

    assert env.read(target).unwrap() == values


def test_write_escapes_double_quote(project_root) -> None:
    """验证 write 处理包含双引号的值后仍可被正确读回"""
    target = project_root / ".env"
    values = {"QUOTE": 'say "hello"'}

    env.write(target, values)

    assert env.read(target).unwrap() == values


def test_write_trailing_newline(project_root) -> None:
    """验证 write 在存在键值对时会追加文件末尾换行"""
    target = project_root / ".env"

    env.write(target, {"API_KEY": "secret"})

    assert target.read_text(encoding="utf-8").endswith("\n")


def test_write_empty_mapping(project_root) -> None:
    """验证 write 在空映射时会写出空文件内容"""
    target = project_root / ".env"

    env.write(target, {})

    assert target.read_text(encoding="utf-8") == ""
