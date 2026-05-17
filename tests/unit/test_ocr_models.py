"""OCR request/result model tests."""

from __future__ import annotations

import pytest

from modules.ocr.ocr_models import (
    OCRErrorCode,
    OCRMode,
    OCRRequest,
    OCRResult,
)


def test_request_requires_exactly_one_image_source() -> None:
    request = OCRRequest(image_bytes=b"image")
    assert request.image_bytes == b"image"
    assert request.image_path is None
    assert request.language_hints == ("ar", "en")
    assert request.mode == OCRMode.NORMAL

    with pytest.raises(ValueError):
        OCRRequest()

    with pytest.raises(ValueError):
        OCRRequest(image_path="sample.png", image_bytes=b"image")


def test_request_rejects_invalid_language_and_timeout() -> None:
    with pytest.raises(ValueError):
        OCRRequest(image_bytes=b"image", language_hints=("fr",))

    with pytest.raises(ValueError):
        OCRRequest(image_bytes=b"image", timeout_seconds=0)


def test_success_result_requires_meaningful_text_and_safe_metadata() -> None:
    result = OCRResult.success_result(
        engine_name="engine",
        raw_text="Readable text",
        duration_ms=12,
        confidence=0.9,
    )

    assert result.success is True
    assert result.error_code is None
    assert result.metadata["engine_name"] == "engine"
    assert "Readable text" not in str(result.metadata)

    with pytest.raises(ValueError):
        OCRResult.success_result(engine_name="engine", raw_text="", duration_ms=1)


def test_failure_result_requires_error_details() -> None:
    result = OCRResult.failure_result(
        engine_name="engine",
        error_code=OCRErrorCode.NO_TEXT_DETECTED,
        error_message="No text found",
        duration_ms=5,
    )

    assert result.success is False
    assert result.raw_text == ""
    assert result.error_code == OCRErrorCode.NO_TEXT_DETECTED
    assert result.error_message == "No text found"
