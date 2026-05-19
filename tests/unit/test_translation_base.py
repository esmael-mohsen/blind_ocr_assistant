"""Tests for Phase 7 translation engine boundary and validation."""

from __future__ import annotations

from modules.translation.base import (
    MockTranslationEngine,
    TranslationEngine,
    is_supported_direction,
    translate_safely,
    validate_translation_result,
)
from modules.translation.translation_models import (
    TranslationErrorCode,
    TranslationLanguage,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
)


def _request(
    *,
    source_text: str = "مرحبا",
    source_language: TranslationLanguage = TranslationLanguage.ARABIC,
    target_language: TranslationLanguage = TranslationLanguage.ENGLISH,
) -> TranslationRequest:
    return TranslationRequest(
        source_text=source_text,
        source_language=source_language,
        target_language=target_language,
    )


def test_translation_engine_protocol_accepts_mock_engine() -> None:
    engine: TranslationEngine = MockTranslationEngine(
        responses={
            ("ar", "en"): "Hello",
        }
    )

    result = engine.translate(_request())

    assert result.success is True
    assert result.translated_text == "Hello"
    assert result.path == TranslationPath.ONLINE
    assert engine.calls[0].source_text == "مرحبا"


def test_mock_engine_returns_unsupported_language_failure() -> None:
    engine = MockTranslationEngine(supported_directions=(("en", "ar"),))

    result = engine.translate(_request())

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.UNSUPPORTED_LANGUAGE


def test_translate_safely_maps_provider_exceptions_to_structured_failure() -> None:
    engine = MockTranslationEngine(raise_on_translate=RuntimeError("network broke"))

    result = translate_safely(engine, _request())

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ONLINE_TRANSLATION_FAILED
    assert "مرحبا" not in str(result.safe_metadata)


def test_supported_directions_are_arabic_english_only() -> None:
    assert is_supported_direction(
        TranslationLanguage.ARABIC,
        TranslationLanguage.ENGLISH,
    )
    assert is_supported_direction(
        TranslationLanguage.ENGLISH,
        TranslationLanguage.ARABIC,
    )
    assert not is_supported_direction(
        TranslationLanguage.MIXED,
        TranslationLanguage.ENGLISH,
    )


def test_validation_rejects_empty_wrong_language_and_unchanged_results() -> None:
    assert not validate_translation_result(
        "",
        source_text="مرحبا",
        target_language=TranslationLanguage.ENGLISH,
    )
    assert not validate_translation_result(
        "مرحبا",
        source_text="مرحبا",
        target_language=TranslationLanguage.ENGLISH,
    )
    assert not validate_translation_result(
        "مرحبا",
        source_text="hello",
        target_language=TranslationLanguage.ENGLISH,
    )


def test_validation_accepts_arabic_english_and_same_language_no_op() -> None:
    assert validate_translation_result(
        "Hello",
        source_text="مرحبا",
        target_language=TranslationLanguage.ENGLISH,
    )
    assert validate_translation_result(
        "مرحبا",
        source_text="hello",
        target_language=TranslationLanguage.ARABIC,
    )
    assert validate_translation_result(
        "hello",
        source_text="hello",
        target_language=TranslationLanguage.ENGLISH,
        no_op=True,
    )


def test_engine_safe_metadata_excludes_text() -> None:
    result = TranslationResult.ok(
        source_language=TranslationLanguage.ARABIC,
        target_language=TranslationLanguage.ENGLISH,
        translated_text="Hello",
        engine_name="mock",
        path=TranslationPath.ONLINE,
    )

    assert "Hello" not in str(result.safe_metadata)
    assert "translated_text" not in result.safe_metadata
