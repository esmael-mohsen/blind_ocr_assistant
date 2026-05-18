"""Phase 5 text cleanup model tests."""

from __future__ import annotations

import pytest

from modules.text import (
    CleanupWarning,
    DetectedLanguage,
    DirectionInfo,
    LanguageDetectionResult,
    TextCleanupRequest,
    TextCleanupResult,
    TextCleanupStatus,
    TextDirection,
    sanitize_text_metadata,
)


def test_text_cleanup_request_preserves_raw_text_and_defaults() -> None:
    raw_text = "  Raw OCR\ntext  "

    request = TextCleanupRequest(raw_text=raw_text, language_hints=("ar", "en"))

    assert request.raw_text == raw_text
    assert request.language_hints == ("ar", "en")
    assert request.preserve_paragraphs is True
    assert request.sensitive_text_logging_enabled is False


def test_text_cleanup_request_rejects_non_text_input() -> None:
    with pytest.raises(TypeError, match="raw_text"):
        TextCleanupRequest(raw_text=None)  # type: ignore[arg-type]


def test_text_cleanup_result_builds_text_free_safe_metadata() -> None:
    result = TextCleanupResult(
        success=True,
        raw_text="private raw text",
        clean_text="private clean text",
        status=TextCleanupStatus.CLEAN,
        language=DetectedLanguage.ENGLISH,
        direction=TextDirection.LTR,
        warnings=(CleanupWarning.PUNCTUATION_NORMALIZED,),
        guidance="Text is ready for reading.",
        source_engine="paddleocr",
    )

    assert result.safe_metadata["success"] is True
    assert result.safe_metadata["status"] == "clean"
    assert result.safe_metadata["language"] == "english"
    assert result.safe_metadata["direction"] == "ltr"
    assert result.safe_metadata["warning_codes"] == ["PUNCTUATION_NORMALIZED"]
    assert result.safe_metadata["raw_length"] == len("private raw text")
    assert result.safe_metadata["clean_length"] == len("private clean text")
    assert "raw_text" not in result.safe_metadata
    assert "clean_text" not in result.safe_metadata
    assert "private" not in str(result.safe_metadata)


def test_text_cleanup_result_requires_guidance_and_valid_empty_state() -> None:
    with pytest.raises(ValueError, match="guidance"):
        TextCleanupResult(
            success=True,
            raw_text="text",
            clean_text="text",
            status=TextCleanupStatus.CLEAN,
            language=DetectedLanguage.ENGLISH,
            direction=TextDirection.LTR,
            guidance="",
        )

    empty = TextCleanupResult(
        success=True,
        raw_text="   ",
        clean_text="",
        status=TextCleanupStatus.EMPTY,
        language=DetectedLanguage.UNKNOWN,
        direction=TextDirection.UNKNOWN,
        warnings=(CleanupWarning.EMPTY_INPUT,),
        guidance="No readable text was available.",
    )

    assert empty.status == TextCleanupStatus.EMPTY
    assert empty.language == DetectedLanguage.UNKNOWN
    assert empty.direction == TextDirection.UNKNOWN


def test_language_detection_result_tracks_evidence_and_direction() -> None:
    result = LanguageDetectionResult(
        language=DetectedLanguage.MIXED,
        confidence=0.72,
        arabic_character_count=12,
        english_character_count=8,
        language_character_count=20,
        dominant_ratio=0.60,
        direction=TextDirection.MIXED,
        warnings=(CleanupWarning.MIXED_DIRECTION,),
    )

    assert result.language == DetectedLanguage.MIXED
    assert result.confidence == 0.72
    assert result.dominant_ratio == 0.60
    assert result.direction == TextDirection.MIXED
    assert result.warnings == (CleanupWarning.MIXED_DIRECTION,)


def test_language_detection_result_validates_score_ranges() -> None:
    with pytest.raises(ValueError, match="confidence"):
        LanguageDetectionResult(
            language=DetectedLanguage.ENGLISH,
            confidence=1.5,
            arabic_character_count=0,
            english_character_count=10,
            language_character_count=10,
            dominant_ratio=1.0,
            direction=TextDirection.LTR,
        )


def test_direction_info_records_logical_order() -> None:
    info = DirectionInfo(
        direction=TextDirection.MIXED,
        has_rtl=True,
        has_ltr=True,
        logical_order_preserved=True,
    )

    assert info.direction == TextDirection.MIXED
    assert info.has_rtl is True
    assert info.has_ltr is True
    assert info.logical_order_preserved is True


def test_sanitize_text_metadata_removes_sensitive_text_values() -> None:
    safe = sanitize_text_metadata(
        {
            "raw_text": "private",
            "clean_text": "private",
            "text": "private",
            "snippet": "private",
            "debug_path": "C:/private/debug.txt",
            "secret": "private",
            "token": "private",
            "status": TextCleanupStatus.CLEAN,
            "raw_length": 7,
        }
    )

    assert safe == {"status": "clean", "raw_length": 7}
