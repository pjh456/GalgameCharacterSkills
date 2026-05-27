from ..models import ToolDef, ToolParam


def write_field(field_names: list[str]) -> ToolDef:
    return ToolDef(
        name="write_field",
        description="写入角色卡 JSON 的一个字段，可多次调用写入不同字段",
        params=(
            ToolParam(
                "field_name", "string",
                f"要写入的字段名，可选: {', '.join(field_names)}",
                required=True, enum=field_names,
            ),
            ToolParam(
                "content", "string",
                "该字段的内容，列表字段请传 JSON 数组字符串",
                required=True,
            ),
            ToolParam(
                "is_complete", "boolean",
                "是否为最后一个字段，设为 true 则系统将完成角色卡生成",
            ),
        ),
    )
