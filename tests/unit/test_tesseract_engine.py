"""Emergency OCR engine tests."""

from __future__ import annotations

from modules.ocr.ocr_models import OCRErrorCode, OCRRequest
from modules.ocr.tesseract_engine import TesseractEngine


def test_missing_executable_returns_availability_false() -> None:
    engine = TesseractEngine(executable_checker=lambda: False)

    assert engine.is_available() is False
    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))
    assert result.error_code == OCRErrorCode.OCR_EXECUTABLE_NOT_FOUND


def test_missing_language_data_returns_structured_failure() -> None:
    engine = TesseractEngine(
        executable_checker=lambda: True,
        language_checker=lambda: False,
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))

    assert result.error_code == OCRErrorCode.OCR_LANGUAGE_DATA_MISSING


def test_mocked_success_maps_result_and_metadata_is_safe() -> None:
    engine = TesseractEngine(
        executable_checker=lambda: True,
        language_checker=lambda: True,
        runner=lambda _source, _langs: "Emergency OCR text",
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))

    assert result.success is True
    assert result.raw_text == "Emergency OCR text"
    assert "Emergency OCR text" not in str(result.metadata)


def test_no_text_and_weak_result_are_structured_failures() -> None:
    no_text = TesseractEngine(
        executable_checker=lambda: True,
        language_checker=lambda: True,
        runner=lambda _source, _langs: "",
    )
    weak_text = TesseractEngine(
        executable_checker=lambda: True,
        language_checker=lambda: True,
        runner=lambda _source, _langs: "@@@",
    )

    assert no_text.recognize(
        OCRRequest(image_bytes=b"image", allow_offline=True)
    ).error_code == OCRErrorCode.NO_TEXT_DETECTED
    assert weak_text.recognize(
        OCRRequest(image_bytes=b"image", allow_offline=True)
    ).error_code == OCRErrorCode.WEAK_OCR_RESULT


def test_unexpected_runner_failure_returns_structured_failure() -> None:
    def runner(_source, _langs):
        raise RuntimeError("boom")

    engine = TesseractEngine(
        executable_checker=lambda: True,
        language_checker=lambda: True,
        runner=runner,
    )

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))

    assert result.error_code == OCRErrorCode.OCR_UNEXPECTED_ERROR


def test_allow_offline_false_returns_executable_error() -> None:
    engine = TesseractEngine(executable_checker=lambda: True)

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=False))

    assert result.error_code == OCRErrorCode.OCR_EXECUTABLE_NOT_FOUND
