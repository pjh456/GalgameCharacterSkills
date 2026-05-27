from ..models import ToolDef, ToolParam

REMOVE_DUPLICATES = ToolDef(
    name="remove_duplicate_sections",
    description="通过指定文件名和内容来移除文件中的重复片段",
    params=(
        ToolParam("file_sections", "array", "要去重的文件片段列表", required=True),
    ),
)
