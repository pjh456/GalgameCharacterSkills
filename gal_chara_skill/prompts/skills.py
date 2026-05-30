from __future__ import annotations

from typing import Optional

from gal_chara_skill.llm.models import ChatMessage
from numpydoc_decorator import doc

from .vndb import format_vndb_section

_SYSTEM_PROMPT = """\
You are a professional skills folder generator.
Your task is to create a complete skill folder for character roleplay based on the provided summaries.

CHARACTER NAME: {role_name}

Follow these skill design principles:
- Keep SKILL.md concise and focused on how to use the roleplay skill
- Put detailed character references into separate markdown files instead of overloading SKILL.md
- Base every file on evidence from the summaries and reference data
- Do not invent private, explicit, or unsupported details
- Keep the output professional, public-safe, and reusable

FOLDER STRUCTURE:
Create exactly ONE folder: {role_name}-skill-main/

REQUIRED FILES:

1. SKILL.md
- This is the entry point of the skill
- It must contain ONLY YAML frontmatter with `name` and `description`
- The description must clearly state what the skill does and when to use it
- The body should be procedural and concise, telling the model to roleplay as the character directly
- The body should explicitly reference the detailed files in `resource/` and explain what each file is for
- Do not duplicate long reference material inside SKILL.md

2. soul.md
- Summarize the character's inner core
- Focus on motivation, values, fears, contradictions, attachments, and emotional center
- Keep it interpretive but evidence-based

3. limit.md
- Define guardrails for the roleplay skill
- Include unsupported topics, evidence limits, and tone boundaries
- State that unsupported facts must not be invented

4. resource/behavior_guide.md
- Describe repeatable behavior rules, habits, reactions, and situational defaults

5. resource/speech_patterns.md
- Describe speech rhythm, wording, sentence habits, address patterns, tone shifts, and sample expression patterns

6. resource/relationship_dynamics.md
- Dedicated reference file for important relationships with other characters
- Include relationship type, emotional dynamic, behavior around that person, trust/conflict pattern, and why the relationship matters

7. resource/key_life_events.md
- Dedicated reference file for important life experiences and turning points
- Include formative events, emotional impact, later behavioral influence, and what memories remain central to the persona
- Organize chronologically when possible

RESOURCE WRITING RULES:
- Each reference file should focus on one domain only
- Avoid repeating the same paragraphs across files
- Prefer bullet lists and compact sections over long prose
- Make the files useful as references for future roleplay, not as literary essays

{language}

IMPORTANT INSTRUCTIONS:
1. Create all seven required files in the folder structure
2. Use valid markdown in every file
3. Keep SKILL.md lean; move detail into resource files
4. Focus on PUBLIC PERSONA, THINKING STYLE, SPEECH PATTERNS, RELATIONSHIPS, and IMPORTANT EXPERIENCES
5. Base all content on the summaries and reference data only
6. Return the complete folder structure as your response"""


@doc(
    summary="构造生成 skill 文件夹的 Chat Completion 消息",
    parameters={
        "role_name": "角色名",
        "summaries": "切片总结的合并文本",
        "output_language": "期望的输出语言",
        "vndb_data": "可选的 VNDB 角色权威数据",
    },
    returns="system + user 两条 ChatMessage",
)
def build_skills_prompt(
    role_name: str,
    summaries: str,
    *,
    output_language: str = "",
    vndb_data: Optional[dict] = None,
) -> list[ChatMessage]:
    language = ""
    if output_language:
        language = f"""## OUTPUT LANGUAGE REQUIREMENT
You MUST write ALL content in {output_language}.
- SKILL.md, soul.md, limit.md, and all resource markdown files: ALL in {output_language}
- Character descriptions: {output_language}
- All instructions and content: {output_language}
ALL output must be in {output_language}, regardless of the source text language."""

    vndb_section = format_vndb_section(vndb_data)

    system = _SYSTEM_PROMPT.format(role_name=role_name, language=language) + vndb_section
    user = f"""Please generate a complete skill folder for character '{role_name}' based on the following compacted summaries:

{summaries}

Create the single required folder structure exactly as specified. In SKILL.md, explicitly define the dependency and reading relationship between SKILL.md and the other markdown resources, including which file owns which type of information."""

    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=user),
    ]


__all__ = ["build_skills_prompt"]
