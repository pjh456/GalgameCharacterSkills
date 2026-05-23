from __future__ import annotations

from gal_chara_skill.core.result import Result
from gal_chara_skill.core.validate import FieldRule, validate_dict_fields


@validate_dict_fields(
    error="格式错误",
    code="invalid",
    name=FieldRule(str, non_empty=True),
    count=FieldRule(int, required=False, default=0),
    tags=FieldRule(list, required=False, default=[], item_type=str, transform=tuple),
)
def load_payload(data: object) -> Result[dict[str, object]]:
    return Result.success(data)


@validate_dict_fields(
    error="格式错误",
    code="invalid",
    child=FieldRule(
        dict,
        transform=lambda value: Result.success({"name": value["name"].upper()}),
    ),
)
def load_nested_payload(data: object) -> Result[dict[str, object]]:
    return Result.success(data)


@validate_dict_fields(
    error="格式错误",
    code="invalid",
    children=FieldRule(
        list,
        item_type=dict,
        item_transform=lambda value: Result.success({"name": value["name"].upper()}),
    ),
)
def load_nested_list_payload(data: object) -> Result[dict[str, object]]:
    return Result.success(data)


def test_validate_dict_fields_applies_defaults_and_transform() -> None:
    """验证字段校验器会补默认值并执行转换"""
    result = load_payload({"name": "alice"})

    assert result.ok is True
    assert result.unwrap() == {
        "name": "alice",
        "count": 0,
        "tags": (),
    }


def test_validate_dict_fields_rejects_invalid_item_type() -> None:
    """验证字段校验器会拒绝列表中的非法元素类型"""
    result = load_payload({"name": "alice", "tags": ["ok", 1]})

    assert result.ok is False
    assert result.code == "invalid"
    assert result.data["field"] == "tags"
    assert result.data["reason"] == "item_type_mismatch"


def test_validate_dict_fields_rejects_bool_for_int() -> None:
    """验证字段校验器不会把布尔值误判为整数"""
    result = load_payload({"name": "alice", "count": True})

    assert result.ok is False
    assert result.code == "invalid"
    assert result.data["field"] == "count"
    assert result.data["reason"] == "type_mismatch"


def test_validate_dict_fields_supports_result_transform() -> None:
    """验证字段校验器支持返回 Result 的字段转换"""
    result = load_nested_payload({"child": {"name": "alice"}})

    assert result.ok is True
    assert result.unwrap() == {"child": {"name": "ALICE"}}


def test_validate_dict_fields_supports_result_item_transform() -> None:
    """验证字段校验器支持列表元素逐项恢复"""
    result = load_nested_list_payload({"children": [{"name": "alice"}, {"name": "bob"}]})

    assert result.ok is True
    assert result.unwrap() == {
        "children": [
            {"name": "ALICE"},
            {"name": "BOB"},
        ]
    }
