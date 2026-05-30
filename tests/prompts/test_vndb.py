from __future__ import annotations

from gal_chara_skill.prompts.vndb import format_vndb_section


def test_format_vndb_section_none() -> None:
    result = format_vndb_section(None)
    assert result == ""


def test_format_vndb_section_empty_dict() -> None:
    result = format_vndb_section({})
    assert result == ""


def test_format_vndb_section_full_data() -> None:
    data = {
        "name": "TestChar",
        "original_name": "テスト",
        "aliases": ["Test", "TC"],
        "description": "A test character.",
        "age": 20,
        "birthday": "01/01",
        "blood_type": "A",
        "height": 170,
        "weight": 60,
        "bust": 88,
        "waist": 60,
        "hips": 90,
        "traits": ["Kind", "Brave"],
        "vns": ["Test VN", "Another VN"],
    }
    result = format_vndb_section(data)
    assert "## VNDB Character Information" in result
    assert "**Name**: TestChar" in result
    assert "**Original Name**: テスト" in result
    assert "**Aliases**: Test, TC" in result
    assert "**Description**: A test character." in result
    assert "**Age**: 20" in result
    assert "**Birthday**: 01/01" in result
    assert "**Blood Type**: A" in result
    assert "**Height (cm)**: 170" in result
    assert "**Weight (kg)**: 60" in result
    assert "**Measurements**: 88-60-90cm" in result
    assert "**Traits**: Kind, Brave" in result
    assert "**Visual Novels**: Test VN, Another VN" in result


def test_format_vndb_section_minimal_data() -> None:
    data = {"name": "Minimal"}
    result = format_vndb_section(data)
    assert "**Name**: Minimal" in result
    assert "Aliases" not in result
    assert "Age" not in result


def test_format_vndb_section_traits_only() -> None:
    data = {"name": "TraitOnly", "traits": ["Silent"]}
    result = format_vndb_section(data)
    assert "**Traits**: Silent" in result


def test_format_vndb_section_vns_truncated() -> None:
    data = {
        "name": "VNChar",
        "vns": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    }
    result = format_vndb_section(data)
    assert "**Visual Novels**: Alpha, Beta, Gamma" in result
    assert "Delta" not in result
