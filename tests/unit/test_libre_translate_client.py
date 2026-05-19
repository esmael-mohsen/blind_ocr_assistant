"""Tests for the Phase 7 LibreTranslate client."""

from __future__ import annotations

from modules.translation.libre_translate_client import LibreTranslateClient
from modules.translation.translation_models import (
    TranslationErrorCode,
    TranslationLanguage,
    TranslationRequest,
)


class ResponseStub:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> object:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _request(*, allow_online: bool = True) -> TranslationRequest:
    return TranslationRequest(
        source_text="مرحبا",
        source_language=TranslationLanguage.ARABIC,
        target_language=TranslationLanguage.ENGLISH,
        allow_online=allow_online,
    )


def test_allow_online_false_returns_unavailable_without_sending_text() -> None:
    calls: list[dict[str, object]] = []
    client = LibreTranslateClient(post_func=lambda *args, **kwargs: calls.append(kwargs))

    result = client.translate(_request(allow_online=False))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE
    assert calls == []


def test_http_success_maps_translated_text_and_safe_metadata() -> None:
    captured: dict[str, object] = {}

    def post_func(endpoint: str, **kwargs: object) -> ResponseStub:
        captured.update(kwargs)
        return ResponseStub({"translatedText": "Hello"})

    client = LibreTranslateClient(post_func=post_func)

    result = client.translate(_request())

    assert result.success is True
    assert result.translated_text == "Hello"
    assert captured["json"] == {
        "q": "مرحبا",
        "source": "ar",
        "target": "en",
        "format": "text",
    }
    assert "Hello" not in str(result.safe_metadata)


def test_api_key_is_included_only_when_configured() -> None:
    captured: dict[str, object] = {}

    def post_func(endpoint: str, **kwargs: object) -> ResponseStub:
        captured.update(kwargs)
        return ResponseStub({"translatedText": "Hello"})

    client = LibreTranslateClient(post_func=post_func, api_key="demo-key")

    result = client.translate(_request())

    assert result.success is True
    assert isinstance(captured.get("json"), dict)
    assert captured["json"]["api_key"] == "demo-key"


def test_service_unavailable_timeout_invalid_json_and_empty_text_fail() -> None:
    unavailable = LibreTranslateClient(
        post_func=lambda *args, **kwargs: ResponseStub({"error": "down"}, status_code=503)
    )
    timeout = LibreTranslateClient(
        post_func=lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("slow")),
        timeout_exceptions=(TimeoutError,),
    )
    invalid_json = LibreTranslateClient(
        post_func=lambda *args, **kwargs: ResponseStub(ValueError("bad json"))
    )
    empty = LibreTranslateClient(
        post_func=lambda *args, **kwargs: ResponseStub({"translatedText": "   "})
    )

    results = [
        unavailable.translate(_request()),
        timeout.translate(_request()),
        invalid_json.translate(_request()),
        empty.translate(_request()),
    ]

    assert [result.success for result in results] == [False, False, False, False]
    assert {result.error.code for result in results if result.error} == {
        TranslationErrorCode.ONLINE_TRANSLATION_FAILED
    }
