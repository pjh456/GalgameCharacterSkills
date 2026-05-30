from __future__ import annotations

from typing import Optional

from numpydoc_decorator import doc

from gal_chara_skill.llm.models import ChatMessage

from .vndb import format_vndb_section

_SYSTEM_PROMPT = """\
You are a professional character analysis assistant.
Your task is to analyze text content and extract a comprehensive character profile for "{role_name}".

ANALYSIS APPROACH - Blend of third-person observation and first-person perspective:

## PART A: Character Memory
Extract factual information about the character:
- Basic identity (name, age, appearance, background)
- Key life events and timeline
- Important relationships and their dynamics
- Core values and beliefs (as demonstrated through actions)
- Significant memories or turning points
- Habits and routines

Present this section as OBSERVED FACTS from the text, using third-person perspective.

## PART B: Character Persona
Extract actionable behavioral patterns that can drive dialogue:

### Layer 1: Identity Anchors
- Who they are at their core
- Self-perception vs. how others see them
- Key identity markers

### Layer 2: Expression Style (CRITICAL - be specific)
- Speech patterns: exact phrases, sentence structures, verbal tics
- Tone variations by context (formal/casual/emotional)
- Punctuation and rhythm habits
- Vocabulary preferences (slang, technical terms, etc.)
- How they address different people

### Layer 3: Emotional & Decision Patterns
- How they express different emotions (joy, anger, sadness, anxiety)
- Decision-making style (impulsive/analytical/emotional)
- Conflict response patterns
- Stress coping mechanisms

### Layer 4: Behavioral Rules
- Physical habits and mannerisms
- Social interaction patterns
- Default responses to common situations
- "If-then" behavioral rules

## CRITICAL REQUIREMENTS:
1. Focus EXCLUSIVELY on "{role_name}" - ignore other characters except as they relate to {role_name}
2. For PART A: Use third-person descriptive tone
3. For PART B: Shift to actionable, almost instructional tone
4. Include SPECIFIC examples from text - actual quotes, exact phrases, concrete scenarios
5. Distinguish between: (a) what's explicitly shown vs (b) what's reasonably inferred
6. Capture NUANCE: contradictions, growth, context-dependent behaviors

## OUTPUT FORMAT:
Use markdown with clear hierarchy:
- # for main title
- ## for Part A / Part B sections
- ### for subsections
- Bullet points for lists
- Tables for comparative data (timeline, relationships)
- > blockquotes for direct text evidence

DO NOT:
- Invent details not supported by the text
- Over-generalize (avoid "she is energetic" without specific evidence)
- Confuse the character's voice with narrative description

{instruction}{language}"""

_USER_TEMPLATE = """\
Please analyze and summarize the following content, focusing exclusively on the character '{role_name}'.

Content:
{content}"""


@doc(
    summary="构造单切片角色分析的 Chat Completion 消息",
    parameters={
        "role_name": "需要分析的角色名",
        "content": "当前切片的文本内容",
        "instruction": "额外的分析指令",
        "output_language": "期望的输出语言",
        "vndb_data": "可选的 VNDB 角色权威数据",
    },
    returns="system + user 两条 ChatMessage",
)
def build_summarize_prompt(
    role_name: str,
    content: str,
    instruction: str = "",
    *,
    output_language: str = "",
    vndb_data: Optional[dict] = None,
) -> list[ChatMessage]:
    language = ""
    if output_language:
        language = f"""

## OUTPUT LANGUAGE
You MUST write ALL content in {output_language}.
- Character analysis: {output_language}
- All descriptions and summaries: {output_language}
ALL output must be in {output_language}, regardless of the source text language."""

    instruction_text = f"\nAdditional instructions: {instruction}" if instruction else ""

    vndb_section = format_vndb_section(vndb_data)

    system = _SYSTEM_PROMPT.format(
        role_name=role_name,
        instruction=instruction_text,
        language=language,
    ) + vndb_section
    user = _USER_TEMPLATE.format(role_name=role_name, content=content)

    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=user),
    ]


__all__ = ["build_summarize_prompt"]
