"""Phase 5 RTL handling tests."""

from __future__ import annotations

from modules.text import TextDirection, detect_text_direction, preserve_logical_order


def test_detect_text_direction_identifies_arabic_rtl() -> None:
    info = detect_text_direction("مرحبا بالعالم")

    assert info.direction == TextDirection.RTL
    assert info.has_rtl is True
    assert info.has_ltr is False
    assert info.logical_order_preserved is True


def test_preserve_logical_order_does_not_reverse_arabic_text() -> None:
    text = "مرحبا بالعالم"

    assert preserve_logical_order(text) == text


def test_detect_text_direction_identifies_mixed_arabic_english() -> None:
    info = detect_text_direction("Total المجموع 125")

    assert info.direction == TextDirection.MIXED
    assert info.has_rtl is True
    assert info.has_ltr is True


def test_preserve_logical_order_keeps_mixed_segments_in_input_order() -> None:
    text = "Total المجموع 125 EGP"

    assert preserve_logical_order(text) == text
