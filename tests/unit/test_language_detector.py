"""Phase 5 language detection tests."""

from __future__ import annotations

from modules.text import (
    CleanupWarning,
    DetectedLanguage,
    TextDirection,
    detect_language,
)


def test_detect_language_classifies_arabic_english_and_mixed() -> None:
    arabic = detect_language("مرحبا بالعالم")
    english = detect_language("Readable English text")
    mixed = detect_language("Total المجموع")

    assert arabic.language == DetectedLanguage.ARABIC
    assert arabic.direction == TextDirection.RTL
    assert english.language == DetectedLanguage.ENGLISH
    assert english.direction == TextDirection.LTR
    assert mixed.language == DetectedLanguage.MIXED
    assert mixed.direction == TextDirection.MIXED


def test_detect_language_uses_sixty_percent_dominant_threshold() -> None:
    english_dominant = detect_language("abcdef ابجد")
    mixed_no_dominant = detect_language("abcde ابجد")

    assert english_dominant.language == DetectedLanguage.ENGLISH
    assert english_dominant.dominant_ratio == 0.60
    assert mixed_no_dominant.language == DetectedLanguage.MIXED


def test_detect_language_returns_unknown_for_empty_short_and_symbol_heavy_text() -> None:
    empty = detect_language("")
    short = detect_language("Hi")
    symbols = detect_language("### 123 !!!")

    assert empty.language == DetectedLanguage.UNKNOWN
    assert short.language == DetectedLanguage.UNKNOWN
    assert symbols.language == DetectedLanguage.UNKNOWN
    assert CleanupWarning.UNCERTAIN_LANGUAGE in short.warnings


def test_detect_language_populates_confidence_counts_ratio_warnings_and_direction() -> None:
    result = detect_language("Receipt الإجمالي 99 EGP")

    assert result.language == DetectedLanguage.MIXED
    assert result.confidence > 0
    assert result.arabic_character_count > 0
    assert result.english_character_count > 0
    assert result.language_character_count == (
        result.arabic_character_count + result.english_character_count
    )
    assert 0.0 <= result.dominant_ratio <= 1.0
    assert result.direction == TextDirection.MIXED
    assert CleanupWarning.MIXED_DIRECTION in result.warnings
