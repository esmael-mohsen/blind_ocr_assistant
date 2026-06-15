"""Gemini translation engine tests."""

from __future__ import annotations

from modules.translation.gemini_translation_engine import GeminiTranslationEngine
from modules.translation.translation_models import (
    TranslationErrorCode,
    TranslationLanguage,
    TranslationRequest,
)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


def _gemini_payload(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_gemini_translation_success_excludes_sensitive_text_from_metadata() -> None:
    def post(*_args, **kwargs):
        assert kwargs["json"]["contents"][0]["parts"][0]["text"]
        return FakeResponse(_gemini_payload("مرحبا بالعالم."))

    engine = GeminiTranslationEngine(api_key="key", post_func=post)

    result = engine.translate(
        TranslationRequest(
            source_text="Hello world.",
            source_language=TranslationLanguage.ENGLISH,
            target_language=TranslationLanguage.ARABIC,
        )
    )

    assert result.success is True
    assert result.engine_name == "gemini_translation"
    assert result.translated_text == "مرحبا بالعالم."
    assert "Hello world" not in str(result.safe_metadata)
    assert "مرحبا" not in str(result.safe_metadata)
    assert "gemini" in str(result.safe_metadata)


def test_gemini_translation_missing_key_returns_unavailable() -> None:
    engine = GeminiTranslationEngine(api_key="")

    result = engine.translate(
        TranslationRequest(
            source_text="Hello.",
            source_language="en",
            target_language="ar",
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE


def test_gemini_translation_http_error_returns_provider_failure() -> None:
    engine = GeminiTranslationEngine(
        api_key="key",
        post_func=lambda *_args, **_kwargs: FakeResponse(
            {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota"}},
            status_code=429,
        ),
    )

    result = engine.translate(
        TranslationRequest(
            source_text="Hello.",
            source_language="en",
            target_language="ar",
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ONLINE_TRANSLATION_FAILED
    assert result.safe_metadata["status_code"] == 429
    assert result.safe_metadata["provider_error_status"] == "RESOURCE_EXHAUSTED"
    assert "quota" not in str(result.safe_metadata)

