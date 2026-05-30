from __future__ import annotations

from gal_chara_skill.llm.models import ChatMessage
from gal_chara_skill.prompts.summarize import build_summarize_prompt
from gal_chara_skill.prompts.skills import build_skills_prompt
from gal_chara_skill.prompts.chara_card import build_chara_card_prompt
from gal_chara_skill.prompts.compress import build_compress_prompt


def test_build_summarize_prompt() -> None:
    messages = build_summarize_prompt(
        role_name="Alice",
        content="Alice went to the store.",
        instruction="Focus on habits.",
    )
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert "Alice" in messages[0].content
    assert "Alice went to the store" in messages[1].content


def test_build_skills_prompt() -> None:
    messages = build_skills_prompt(
        role_name="Alice",
        summaries="Alice is a brave warrior.",
    )
    assert len(messages) == 2
    assert messages[0].role == "system"
    assert "Alice" in messages[0].content


def test_build_chara_card_prompt() -> None:
    messages = build_chara_card_prompt(
        role_name="Alice",
        content="Alice is a brave warrior.",
    )
    assert len(messages) == 2
    assert messages[0].role == "system"


def test_build_compress_prompt() -> None:
    messages = build_compress_prompt(
        files={"summary_001.md": "Alice has blue hair.", "summary_002.md": "Alice has blue hair."},
        group_index=0,
        total_groups=1,
    )
    assert len(messages) == 2
    assert messages[0].role == "system"
