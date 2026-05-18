"""Phase 4 OCR quality scoring tests."""

from __future__ import annotations

from modules.ocr.ocr_quality import (
    LanguageMixStatus,
    OCRQualityIssue,
    assess_ocr_quality,
)


def test_quality_accepts_scores_at_threshold_and_rejects_below() -> None:
    acceptable = assess_ocr_quality("This is readable printed text.", threshold=0.70)
    weak = assess_ocr_quality("Hi", threshold=0.70)

    assert acceptable.is_acceptable is True
    assert acceptable.quality_score >= 0.70
    assert weak.is_acceptable is False
    assert weak.quality_score < 0.70


def test_quality_classifies_empty_and_short_text() -> None:
    empty = assess_ocr_quality("")
    short = assess_ocr_quality("A")

    assert OCRQualityIssue.EMPTY_TEXT in empty.issues
    assert empty.is_acceptable is False
    assert OCRQualityIssue.VERY_SHORT_TEXT in short.issues
    assert short.is_acceptable is False


def test_quality_classifies_symbol_heavy_repeated_and_spaced_text() -> None:
    symbol_heavy = assess_ocr_quality("@@@ ### $$$ text")
    repeated = assess_ocr_quality("aaaaaa bbbbbb cccccc")
    spaced = assess_ocr_quality("T h i s   i s   b r o k e n")

    assert OCRQualityIssue.SYMBOL_HEAVY_TEXT in symbol_heavy.issues
    assert OCRQualityIssue.REPEATED_CHARACTERS in repeated.issues
    assert OCRQualityIssue.EXCESSIVE_SPACING in spaced.issues


def test_quality_supports_arabic_english_and_mixed_text() -> None:
    arabic = assess_ocr_quality("هذه جملة عربية واضحة للقراءة")
    english = assess_ocr_quality("This is a clear English sentence for reading")
    mixed = assess_ocr_quality("This invoice رقم 123 contains Arabic and English")

    assert arabic.language_mix_status == LanguageMixStatus.ARABIC
    assert english.language_mix_status == LanguageMixStatus.ENGLISH
    assert mixed.language_mix_status == LanguageMixStatus.MIXED
    assert arabic.is_acceptable is True
    assert english.is_acceptable is True
    assert mixed.is_acceptable is True
