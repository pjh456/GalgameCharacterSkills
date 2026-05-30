from __future__ import annotations

from typing import Optional

from numpydoc_decorator import doc

from gal_chara_skill.llm.models import ChatMessage

from .vndb import format_vndb_section

_SYSTEM_PROMPT = """\
You are a professional character analysis and lorebook extraction assistant.
Your task is to analyze text content and extract:
1. Character profile for "{role_name}"
2. Worldbook/Lorebook entries from the text

## OUTPUT FORMAT
You must return a JSON object with the following structure:

```json
{{
    "character_analysis": {{
        "name": "Character name",
        "part_a_memory": {{
            "basic_identity": "Basic identity: age, appearance (height, weight, hair/eye color, distinctive features)",
            "key_life_events": ["Event 1", "Event 2", "Turning point..."],
            "relationships": ["Relationship dynamics with family/friends/rivals..."],
            "core_values": "Core values and beliefs demonstrated through actions",
            "significant_memories": "Formative experiences that shaped the character",
            "habits_routines": "Daily patterns, preferences, rituals"
        }},
        "part_b_persona": {{
            "identity_anchors": "Core identity, self-perception vs others' perception",
            "expression_style": {{
                "speech_patterns": "Language patterns: common sentence structures, verbal tics, catchphrases",
                "tone_variations": "Tone shifts across contexts (formal/casual/emotional)",
                "punctuation_rhythm": "Speaking pace, pauses, emphasis",
                "vocabulary": "Word preferences: slang, technical terms, archaic words, pet phrases",
                "address_patterns": "Self-reference and how they address others"
            }},
            "emotional_patterns": {{
                "emotional_expression": "How emotions manifest (joy/anger/sadness/anxiety/fear)",
                "decision_style": "Decision-making approach (impulsive/analytical/emotional/intuitive)",
                "conflict_response": "Conflict response patterns (avoidance/confrontation/compromise)",
                "stress_coping": "Stress coping mechanisms"
            }},
            "behavioral_rules": {{
                "physical_habits": "Body habits (gestures, postures, movements)",
                "social_patterns": "Social interaction patterns (initiator/responder/observer)",
                "default_responses": "Default reactions to common situations",
                "if_then_rules": "Situation-triggered behavioral rules"
            }}
        }},
        "appearance": "Appearance description, all physical traits",
        "personality_traits": ["Trait 1", "Trait 2"],
        "speech_patterns": "Language style summary",
        "background": "Background story and experiences",
        "relationships": ["Relationship 1 description", "Relationship 2 description"],
        "key_events": ["Important event 1", "Important event 2"],
        "behavior_patterns": "Behavior patterns and habits"
    }},
    "lorebook_entries": [
        {{
            "keys": ["keyword1", "keyword2", "alias"],
            "comment": "Entry name/notes",
            "content": "Content to insert when keywords are triggered"
        }}
    ]
}}
```

## CHARACTER ANALYSIS GUIDELINES
- Include SPECIFIC examples from text - actual quotes, exact phrases, concrete scenarios
- Distinguish between: (a) what's explicitly shown vs (b) what's reasonably inferred
- Capture NUANCE: contradictions, character growth, context-dependent behaviors
- Avoid over-generalization - provide evidence for each trait

## LOREBOOK ENTRIES GUIDELINES
Entry Types to Extract:
- Locations: Places mentioned (cities, buildings, regions, landmarks)
- Organizations: Groups, factions, institutions, clubs, companies
- Concepts: Important ideas, systems, rules, cultural practices, beliefs
- Items: Significant objects with meaning (gifts, heirlooms, tools)
- Events: Historical or significant happenings, ceremonies, incidents
- Other Characters: Important people related to {role_name}

Entry Quality Standards:
- Have 2-5 relevant keywords including aliases/variations
- Content should be from {role_name}'s perspective and voice
- Include concrete details from the text, not generic descriptions
- Capture the emotional tone and relationship dynamics
- Each entry should reveal something about {role_name}'s worldview or experience

## LANGUAGE REQUIREMENT
You MUST write ALL content in the same language as the source text.
- If the source text is in Japanese, write the analysis and lorebook entries in Japanese
- If the source text is in Chinese, write in Chinese
- If the source text is in English, write in English
- Character dialogue should match the original text's language

## CRITICAL REQUIREMENTS
1. Return ONLY valid JSON
2. Be thorough - extract ALL relevant lorebook entries you can find
3. Focus on information that helps understand {role_name}'s world
4. Do not invent details not supported by the text

{instruction}"""

_USER_TEMPLATE = """\
Please analyze the following content and extract character analysis and lorebook entries for '{role_name}'.

Content:
{content}"""


@doc(
    summary="构造生成角色卡 + 世界书的 Chat Completion 消息",
    parameters={
        "role_name": "角色名",
        "content": "切片总结的合并文本",
        "instruction": "额外的生成指令",
        "output_language": "期望的输出语言",
        "vndb_data": "可选的 VNDB 角色权威数据",
    },
    returns="system + user 两条 ChatMessage",
)
def build_chara_card_prompt(
    role_name: str,
    content: str,
    instruction: str = "",
    *,
    output_language: str = "",
    vndb_data: Optional[dict] = None,
) -> list[ChatMessage]:
    instruction_text = f"\nAdditional instructions: {instruction}" if instruction else ""

    vndb_section = format_vndb_section(vndb_data)

    language = ""
    if output_language:
        language = """
...
"""
        system = _SYSTEM_PROMPT.format(
            role_name=role_name,
            instruction=instruction_text + language,
        ) + vndb_section
    else:
        system = _SYSTEM_PROMPT.format(role_name=role_name, instruction=instruction_text) + vndb_section

    user = _USER_TEMPLATE.format(role_name=role_name, content=content)

    return [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=user),
    ]


__all__ = ["build_chara_card_prompt"]
