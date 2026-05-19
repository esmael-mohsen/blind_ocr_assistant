"""Tests for Phase 7 translation data models."""

from __future__ import annotations

import pytest

from modules.translation.translation_models import (
    TranslationControlRequest,
    TranslationError,
    TranslationErrorCode,
    TranslationLanguage,
    TranslationOperation,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
    TranslationState,
    sanitize_translation_metadata,
)


def test_translation_request_records_safe_metadata_without_text() -> None:
    request = TranslationRequest(
        source_text="Private medicine instruction",
        source_language=TranslationLanguage.ENGLISH,
        target_language=TranslationLanguage.ARABIC,
        allow_online=True,
        allow_offline=True,
        operation=TranslationOperation.TRANSLATE,
    )

    assert request.source_text == "Private medicine instruction"
    assert request.safe_metadata["source_language"] == "en"
    assert request.safe_metadata["target_language"] == "ar"
    assert request.safe_metadata["source_text_length"] == len(
        "Private medicine instruction"
    )
    assert "source_text" not in request.safe_metadata
    assert "text" not in request.safe_metadata


def test_translation_result_success_and_failure_metadata() -> None:
    result = TranslationResult.ok(
        source_language=TranslationLanguage.ARABIC,
        target_language=TranslationLanguage.ENGLISH,
        translated_text="Hello",
        engine_name="mock",
        path=TranslationPath.ONLINE,
        guidance="Translation is ready.",
    )

    assert result.success is True
    assert result.safe_metadata["path"] == "online"
    assert result.safe_metadata["translated_text_length"] == len("Hello")
    assert "translated_text" not in result.safe_metadata
    assert "guidance" not in result.safe_metadata

    error = TranslationError(
        code=TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
        message="provider failed",
        engine_name="mock",
    )
    failure = TranslationResult.failure(
        source_language=TranslationLanguage.ARABIC,
        target_language=TranslationLanguage.ENGLISH,
        path=TranslationPath.ONLINE,
        engine_name="mock",
        error=error,
        guidance="Translation failed.",
    )

    assert failure.success is False
    assert failure.safe_metadata["error_code"] == "ONLINE_TRANSLATION_FAILED"


def test_translation_result_failure_requires_error() -> None:
    with pytest.raises(ValueError, match="error is required"):
        TranslationResult.failure(
            source_language=TranslationLanguage.ENGLISH,
            target_language=TranslationLanguage.ARABIC,
            path=TranslationPath.OFFLINE,
            guidance="Translation failed.",
        )


def test_translation_error_safe_metadata() -> None:
    error = TranslationError(
        code=TranslationErrorCode.NO_TEXT_TO_TRANSLATE,
        message="no text",
        recoverable=False,
    )

    assert error.safe_metadata == {
        "error_code": "NO_TEXT_TO_TRANSLATE",
        "recoverable": False,
        "engine_name": None,
    }


def test_translation_state_defaults_and_updates_are_private() -> None:
    state = TranslationState()
    assert state.latest_translated_text is None
    assert state.safe_metadata["has_latest_translation"] is False

    result = TranslationResult.ok(
        source_language=TranslationLanguage.ENGLISH,
        target_language=TranslationLanguage.ARABIC,
        translated_text="مرحبا",
        engine_name="mock",
        path=TranslationPath.ONLINE,
    )
    updated = state.with_success(
        source_text_id="text:abc",
        translated_text="مرحبا",
        result=result,
    )

    assert updated.current_source_text_id == "text:abc"
    assert updated.latest_translated_text == "مرحبا"
    assert updated.safe_metadata["has_latest_translation"] is True
    assert "مرحبا" not in str(updated.safe_metadata)


def test_translation_control_request_normalizes_languages() -> None:
    control = TranslationControlRequest(
        target_language="ar",
        source_language="en",
        allow_online=False,
        read_result=True,
    )

    assert control.target_language == TranslationLanguage.ARABIC
    assert control.source_language == TranslationLanguage.ENGLISH
    assert control.safe_metadata["target_language"] == "ar"


def test_sanitize_translation_metadata_removes_sensitive_keys() -> None:
    assert sanitize_translation_metadata(
        {
            "raw_text": "secret",
            "clean_text": "secret",
            "source_text": "secret",
            "translated_text": "secret",
            "source_snippet": "secret",
            "translated_snippet": "secret",
            "token": "secret",
            "path": TranslationPath.NO_OP,
        }
    ) == {"path": "no_op"}
