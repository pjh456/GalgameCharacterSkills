from __future__ import annotations

from pathlib import Path

from gal_chara_skill.conf.constants import (
    CARDS_DIR,
    CHECKPOINTS_DIR,
    INPUT_DIR,
    LOGS_DIR,
    OUTPUT_DIR,
    PROJECT_ROOT,
    SKILLS_DIR,
    SLICES_DIR,
    SUMMARIES_DIR,
)


def test_paths() -> None:
    """验证常量路径会按预期层级组织在项目目录下"""
    assert PROJECT_ROOT == Path(".")
    assert INPUT_DIR == PROJECT_ROOT / "input"
    assert OUTPUT_DIR == PROJECT_ROOT / "output"
    assert SLICES_DIR == OUTPUT_DIR / "slices"
    assert CHECKPOINTS_DIR == OUTPUT_DIR / "checkpoints"
    assert SUMMARIES_DIR == OUTPUT_DIR / "summaries"
    assert SKILLS_DIR == OUTPUT_DIR / "skills"
    assert CARDS_DIR == OUTPUT_DIR / "cards"
    assert LOGS_DIR == OUTPUT_DIR / "logs"
