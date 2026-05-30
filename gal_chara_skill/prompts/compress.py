from __future__ import annotations

from numpydoc_decorator import doc

from gal_chara_skill.llm.models import ChatMessage

_SYSTEM_PROMPT = """\
You are an aggressive text deduplication assistant. Your task is to analyze multiple summary files and identify ALL duplicate content for maximum compression.

## Guidelines:
1. Analyze content across ALL files in the group thoroughly
2. Identify ANY sections that contain the same information, even if phrased slightly differently
3. Mark ALL duplicate sections for removal from later files
4. Focus on: character descriptions, events, relationships, personality traits, speech patterns
5. If the same information appears in multiple files, it IS a duplicate

## How to respond:
1. Read through all files in the group
2. Identify ALL duplicate sections (same information appearing in multiple files)
3. For each duplicate:
   - Keep the first occurrence (in the earliest file)
   - Mark ALL subsequent occurrences for removal
4. Return a list of duplicates in JSON format with the file name and the exact content to remove

## Important:
- Remove ALL duplicates aggressively - we want maximum compression
- If information appears in File 1 and File 2, remove it from File 2
- If information appears in File 1, File 3, and File 5, remove it from File 3 and File 5
- BE AGGRESSIVE - mark every duplicate you find
- FORMAT DOES NOT MATTER - removing content may break file structure, that's OK
- The remaining content will be reprocessed later, so only semantic uniqueness matters"""

_USER_TEMPLATE = """\
Please analyze the following {file_count} files and identify ALL duplicate sections for aggressive compression.

## Group Information:
- This is group {group_index} of {total_groups}
- Total files in this group: {file_count}
- Files are shown in order (File 1 is the earliest, File N is the latest)

## Files to Analyze:
{files_content}

## Instructions:
1. Compare content across ALL files thoroughly
2. Identify EVERY section that appears in multiple files (even partially)
3. For each duplicate section:
   - Keep it ONLY in the earliest file where it appears
   - Mark it for removal in ALL later files

Return your findings as a JSON list of objects with "filename" and "content" keys.
If no duplicates exist, return an empty list."""


@doc(
    summary="构造跨切片去重的 Chat Completion 消息",
    parameters={
        "files": "文件名到内容的映射字典",
        "group_index": "当前组编号（从 0 开始）",
        "total_groups": "总组数",
    },
    returns="system + user 两条 ChatMessage",
)
def build_compress_prompt(
    files: dict[str, str],
    *,
    group_index: int,
    total_groups: int,
) -> list[ChatMessage]:
    files_display = []
    for idx, (filename, content) in enumerate(files.items()):
        files_display.append(f"\n{'=' * 60}\nFILE {idx + 1}: {filename}\n{'=' * 60}\n{content}")

    user = _USER_TEMPLATE.format(
        file_count=len(files),
        group_index=group_index + 1,
        total_groups=total_groups,
        files_content="\n".join(files_display),
    )

    return [
        ChatMessage(role="system", content=_SYSTEM_PROMPT),
        ChatMessage(role="user", content=user),
    ]


__all__ = ["build_compress_prompt"]
