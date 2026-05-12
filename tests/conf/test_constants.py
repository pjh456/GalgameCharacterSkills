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


def test_project_root() -> None:
    """验证 PROJECT_ROOT 指向当前相对根目录"""
    assert PROJECT_ROOT == Path(".")


def test_input_dir() -> None:
    """验证 INPUT_DIR 位于项目根目录下的 input 文件夹"""
    assert INPUT_DIR == PROJECT_ROOT / "input"


def test_output_dir() -> None:
    """验证 OUTPUT_DIR 位于项目根目录下的 output 文件夹"""
    assert OUTPUT_DIR == PROJECT_ROOT / "output"


def test_slices_dir() -> None:
    """验证 SLICES_DIR 位于输出目录下的 slices 文件夹"""
    assert SLICES_DIR == OUTPUT_DIR / "slices"


def test_checkpoints_dir() -> None:
    """验证 CHECKPOINTS_DIR 位于输出目录下的 checkpoints 文件夹"""
    assert CHECKPOINTS_DIR == OUTPUT_DIR / "checkpoints"


def test_summaries_dir() -> None:
    """验证 SUMMARIES_DIR 位于输出目录下的 summaries 文件夹"""
    assert SUMMARIES_DIR == OUTPUT_DIR / "summaries"


def test_skills_dir() -> None:
    """验证 SKILLS_DIR 位于输出目录下的 skills 文件夹"""
    assert SKILLS_DIR == OUTPUT_DIR / "skills"


def test_cards_dir() -> None:
    """验证 CARDS_DIR 位于输出目录下的 cards 文件夹"""
    assert CARDS_DIR == OUTPUT_DIR / "cards"


def test_logs_dir() -> None:
    """验证 LOGS_DIR 位于输出目录下的 logs 文件夹"""
    assert LOGS_DIR == OUTPUT_DIR / "logs"
