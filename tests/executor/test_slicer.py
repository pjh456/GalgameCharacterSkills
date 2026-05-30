from __future__ import annotations

from gal_chara_skill.stages.slicer import Slicer


def test_count_tokens() -> None:
    tokens = Slicer.count_tokens("Hello, world!")
    assert tokens > 0


def test_count_tokens_empty() -> None:
    tokens = Slicer.count_tokens("")
    assert tokens == 0


def test_slice_text_single_slice() -> None:
    text = "Hello world.\nThis is a test."
    slices = Slicer.slice_text(text, max_tokens=100)
    assert len(slices) == 1
    assert slices[0] == text


def test_slice_text_multiple_slices() -> None:
    text = "\n".join(f"Line {i}: This is some test content for slicing purposes." for i in range(1000))
    slices = Slicer.slice_text(text, max_tokens=100)

    assert len(slices) > 1
    combined = "".join(slices)
    assert combined == text


def test_slice_text_empty() -> None:
    slices = Slicer.slice_text("", max_tokens=100)
    assert slices == [""]


def test_slice_text_exact_multiple() -> None:
    text = "Hello world.\nThis is a test."
    tokens = Slicer.count_tokens(text)
    slices = Slicer.slice_text(text, max_tokens=tokens)
    assert len(slices) == 1


def test_slice_text_just_over() -> None:
    text = "Hello world.\nThis is a test."
    tokens = Slicer.count_tokens(text)
    slices = Slicer.slice_text(text, max_tokens=max(1, tokens - 1))
    assert len(slices) >= 2
