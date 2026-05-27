from ..models import ToolDef, ToolParam

WRITE_FILE = ToolDef(
    name="write_file",
    description="将内容写入本地文件",
    params=(
        ToolParam("file_path", "string", "文件路径，含目录结构", required=True),
        ToolParam("content", "string", "Markdown 格式的文件内容", required=True),
    ),
)
