from __future__ import annotations

from typing import Any, Optional

from numpydoc_decorator import doc


@doc(
    summary="将 VNDB 角色数据格式化为追加到 system prompt 的 markdown 段落",
    parameters={"vndb_data": "VNDB API 返回的角色数据字典，为 None 或空时返回空字符串"},
    returns="格式化的 markdown 字符串，含 name、age、traits 等字段；无数据时返回空字符串",
)
def format_vndb_section(vndb_data: Optional[dict[str, Any]]) -> str:
    if not vndb_data:
        return ""

    lines = ["\n\n## VNDB Character Information\n"]

    field_map = [
        ("name", "Name"),
        ("original_name", "Original Name"),
        ("aliases", "Aliases"),
        ("description", "Description"),
        ("age", "Age"),
        ("birthday", "Birthday"),
        ("blood_type", "Blood Type"),
        ("height", "Height (cm)"),
        ("weight", "Weight (kg)"),
    ]

    for key, label in field_map:
        value = vndb_data.get(key)
        if value:
            if key == "aliases" and isinstance(value, list):
                value = ", ".join(value)
            lines.append(f"- **{label}**: {value}")

    if vndb_data.get("bust") and vndb_data.get("waist") and vndb_data.get("hips"):
        lines.append(
            f"- **Measurements**: {vndb_data['bust']}-{vndb_data['waist']}-{vndb_data['hips']}cm"
        )

    traits = vndb_data.get("traits", [])
    if traits:
        lines.append(f"- **Traits**: {', '.join(traits)}")

    vns = vndb_data.get("vns", [])
    if vns:
        lines.append(f"- **Visual Novels**: {', '.join(vns[:3])}")

    return "\n".join(lines)


__all__ = ["format_vndb_section"]
