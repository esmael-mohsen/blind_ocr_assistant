"""Tests for deterministic Phase 6 text segmentation."""

from __future__ import annotations

from modules.text.segmentation import split_paragraphs, split_sentences
from modules.voice.voice_models import SegmentType


def test_split_paragraphs_uses_blank_line_boundaries() -> None:
    text = "First paragraph line.\nStill first.\n\nSecond paragraph."

    paragraphs = split_paragraphs(text, language="en", parent_text_id="doc")

    assert [segment.text for segment in paragraphs] == [
        "First paragraph line.\nStill first.",
        "Second paragraph.",
    ]
    assert [segment.segment_type for segment in paragraphs] == [
        SegmentType.PARAGRAPH,
        SegmentType.PARAGRAPH,
    ]
    assert [segment.segment_id for segment in paragraphs] == [
        "doc:paragraph:0",
        "doc:paragraph:1",
    ]


def test_split_sentences_supports_english_punctuation() -> None:
    sentences = split_sentences(
        "First sentence. Second question? Third exclamation!",
        language="en",
        parent_text_id="doc",
    )

    assert [segment.text for segment in sentences] == [
        "First sentence.",
        "Second question?",
        "Third exclamation!",
    ]


def test_split_sentences_supports_arabic_punctuation() -> None:
    sentences = split_sentences(
        "هذا نص أول. هل هذا واضح؟ نعم!",
        language="ar",
        parent_text_id="doc",
    )

    assert [segment.text for segment in sentences] == [
        "هذا نص أول.",
        "هل هذا واضح؟",
        "نعم!",
    ]


def test_split_sentences_preserves_mixed_logical_order() -> None:
    sentences = split_sentences(
        "Take one tablet daily. الجرعة بعد الطعام.",
        language="mixed",
        parent_text_id="doc",
    )

    assert [segment.text for segment in sentences] == [
        "Take one tablet daily.",
        "الجرعة بعد الطعام.",
    ]
    assert [segment.segment_id for segment in sentences] == [
        "doc:sentence:0",
        "doc:sentence:1",
    ]


def test_segmentation_discards_empty_segments() -> None:
    assert split_paragraphs(" \n\n  ", parent_text_id="doc") == []
    assert split_sentences(" \n\n  ", parent_text_id="doc") == []


def test_segmentation_fixture_documents_repeat_cases() -> None:
    fixture = "tests/fixtures/text/segmentation_cases.md"
    text = open(fixture, encoding="utf-8").read()

    assert "English" in text
    assert "Arabic" in text
    assert "Mixed" in text
    assert split_sentences("First sentence. Second sentence?", parent_text_id="doc")
    assert split_paragraphs("One.\n\nTwo.", parent_text_id="doc")
