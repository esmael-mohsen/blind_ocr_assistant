"""Phase 5 text cleanup behavior tests."""

from __future__ import annotations

from modules.text import (
    CleanupWarning,
    DetectedLanguage,
    TextCleanupRequest,
    TextCleanupStatus,
    TextDirection,
    clean_ocr_text,
)


def test_cleanup_preserves_raw_text_and_produces_separate_clean_text() -> None:
    raw_text = "  This   is\nreadable text .  "

    result = clean_ocr_text(TextCleanupRequest(raw_text=raw_text))

    assert result.success is True
    assert result.raw_text == raw_text
    assert result.clean_text == "This is readable text."
    assert result.raw_text != result.clean_text


def test_cleanup_normalizes_repeated_spaces_and_tabs() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="Read\t\tthis     text"))

    assert result.clean_text == "Read this text"
    assert result.status == TextCleanupStatus.CLEAN


def test_cleanup_collapses_single_line_breaks_and_preserves_paragraphs() -> None:
    result = clean_ocr_text(
        TextCleanupRequest(raw_text="This is a\nwrapped sentence.\n\nNext paragraph.")
    )

    assert result.clean_text == "This is a wrapped sentence.\n\nNext paragraph."
    assert CleanupWarning.LINE_BREAKS_NORMALIZED in result.warnings


def test_cleanup_preserves_list_like_line_breaks() -> None:
    result = clean_ocr_text(
        TextCleanupRequest(raw_text="Shopping list\n- milk\n- bread\n1. apples")
    )

    assert result.clean_text == "Shopping list\n- milk\n- bread\n1. apples"


def test_cleanup_normalizes_arabic_and_english_punctuation_spacing() -> None:
    result = clean_ocr_text(
        TextCleanupRequest(raw_text="Hello , world !\nمرحبا ، العالم ؟")
    )

    assert result.clean_text == "Hello, world!\nمرحبا، العالم؟"
    assert CleanupWarning.PUNCTUATION_NORMALIZED in result.warnings


def test_cleanup_preserves_uncertain_garbage_fragments_with_warnings() -> None:
    raw_text = "Invoice total ### 125.00"

    result = clean_ocr_text(TextCleanupRequest(raw_text=raw_text))

    assert "###" in result.clean_text
    assert result.status == TextCleanupStatus.NOISY
    assert CleanupWarning.PRESERVED_UNCERTAIN_FRAGMENT in result.warnings
    assert CleanupWarning.NOISY_TEXT in result.warnings


def test_cleanup_handles_empty_input_with_guidance_and_unknown_defaults() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="   \n\t  "))

    assert result.success is True
    assert result.clean_text == ""
    assert result.status == TextCleanupStatus.EMPTY
    assert result.language == DetectedLanguage.UNKNOWN
    assert result.direction == TextDirection.UNKNOWN
    assert CleanupWarning.EMPTY_INPUT in result.warnings
    assert "no readable text" in result.guidance.lower()


def test_cleanup_is_idempotent_for_cleaned_text() -> None:
    raw_text = "Hello ,   world !\n\nNext   paragraph."
    first = clean_ocr_text(TextCleanupRequest(raw_text=raw_text))
    second = clean_ocr_text(TextCleanupRequest(raw_text=first.clean_text))

    assert second.clean_text == first.clean_text


def test_cleanup_preserves_arabic_readability_with_spacing_noise() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="مرحبا   ،   يا عالم   !"))

    assert result.clean_text == "مرحبا، يا عالم!"
    assert result.direction == TextDirection.RTL


def test_cleanup_preserves_english_readability_with_spacing_noise() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="Read   this   clear text ."))

    assert result.clean_text == "Read this clear text."
    assert result.direction == TextDirection.LTR


def test_cleanup_preserves_mixed_numbers_dates_prices_and_symbols() -> None:
    result = clean_ocr_text(
        TextCleanupRequest(raw_text="Total المجموع : 125.50 EGP\nDate : 2026-05-18")
    )

    assert "Total" in result.clean_text
    assert "المجموع" in result.clean_text
    assert "125.50" in result.clean_text
    assert "2026-05-18" in result.clean_text
    assert result.direction == TextDirection.MIXED


def test_cleanup_preserves_arabic_diacritics_and_punctuation() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="قَرَأَ الطالبُ النصَّ ، جيداً ؟"))

    assert "قَرَأَ" in result.clean_text
    assert "النصَّ" in result.clean_text
    assert "،" in result.clean_text
    assert "؟" in result.clean_text


def test_cleanup_adds_mixed_direction_warning() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="Receipt الإجمالي 99 EGP"))

    assert result.direction == TextDirection.MIXED
    assert CleanupWarning.MIXED_DIRECTION in result.warnings


def test_cleanup_integrates_language_detection_result() -> None:
    arabic = clean_ocr_text(TextCleanupRequest(raw_text="مرحبا بالعالم"))
    english = clean_ocr_text(TextCleanupRequest(raw_text="Readable English text"))
    mixed = clean_ocr_text(TextCleanupRequest(raw_text="Total المجموع"))

    assert arabic.language == DetectedLanguage.ARABIC
    assert english.language == DetectedLanguage.ENGLISH
    assert mixed.language == DetectedLanguage.MIXED


def test_cleanup_marks_uncertain_language_when_detection_is_unknown() -> None:
    result = clean_ocr_text(TextCleanupRequest(raw_text="### 123 !!!"))

    assert result.language == DetectedLanguage.UNKNOWN
    assert result.status == TextCleanupStatus.UNCERTAIN_LANGUAGE
    assert CleanupWarning.UNCERTAIN_LANGUAGE in result.warnings
