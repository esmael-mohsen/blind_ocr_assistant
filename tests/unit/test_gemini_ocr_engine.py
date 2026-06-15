"""Gemini OCR engine tests."""

from __future__ import annotations

from modules.ocr.gemini_ocr_engine import GeminiOCREngine
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest


class FakeTimeout(Exception):
    pass


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


def _gemini_payload(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_missing_credential_returns_structured_failure() -> None:
    engine = GeminiOCREngine(api_key="")

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MISSING_CREDENTIAL


def test_online_engine_requires_allow_online() -> None:
    engine = GeminiOCREngine(api_key="key")

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=False))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MISSING_CREDENTIAL


def test_mocked_success_response_excludes_text_and_image_from_metadata() -> None:
    def post(*_args, **kwargs):
        assert kwargs["json"]["contents"][0]["parts"][0]["inline_data"]["data"]
        return FakeResponse(_gemini_payload("مرحبا\nHello"))

    engine = GeminiOCREngine(api_key="key", post_func=post)

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is True
    assert result.engine_name == "gemini"
    assert result.raw_text == "مرحبا\nHello"
    assert "مرحبا" not in str(result.metadata)
    assert "image" not in str(result.metadata)
    assert "inline_data" not in str(result.metadata)


def test_empty_response_returns_no_text_detected() -> None:
    engine = GeminiOCREngine(
        api_key="key",
        post_func=lambda *_args, **_kwargs: FakeResponse(_gemini_payload("")),
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.NO_TEXT_DETECTED


def test_provider_http_error_returns_provider_error() -> None:
    engine = GeminiOCREngine(
        api_key="key",
        post_func=lambda *_args, **_kwargs: FakeResponse(
            {"error": {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}},
            status_code=429,
        ),
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_PROVIDER_ERROR
    assert result.metadata["status_code"] == 429
    assert result.metadata["provider_error_status"] == "RESOURCE_EXHAUSTED"
    assert "quota exceeded" not in str(result.metadata)


def test_malformed_response_returns_failure() -> None:
    engine = GeminiOCREngine(
        api_key="key",
        post_func=lambda *_args, **_kwargs: FakeResponse({}),
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MALFORMED_RESPONSE


def test_timeout_returns_structured_failure() -> None:
    def post(*_args, **_kwargs):
        raise FakeTimeout("slow")

    engine = GeminiOCREngine(
        api_key="key",
        post_func=post,
        timeout_exceptions=(FakeTimeout,),
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_PROVIDER_TIMEOUT
