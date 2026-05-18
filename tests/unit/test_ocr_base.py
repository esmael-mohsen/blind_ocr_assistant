"""OCR base interface tests."""

from __future__ import annotations

from modules.ocr.base import OCRBaseEngine
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest


class DummyEngine(OCRBaseEngine):
    engine_name = "dummy"

    def is_available(self) -> bool:
        return True

    def recognize(self, request: OCRRequest):
        return self.classify_text(
            raw_text=request.image_bytes.decode("utf-8"),
            duration_ms=1,
        )


def test_base_engine_classifies_meaningful_text() -> None:
    engine = DummyEngine()

    result = engine.recognize(OCRRequest(image_bytes=b"hello world"))

    assert result.success is True
    assert result.engine_name == "dummy"
    assert result.raw_text == "hello world"


def test_base_engine_classifies_no_text_and_weak_text() -> None:
    engine = DummyEngine()

    empty = engine.classify_text(raw_text="", duration_ms=1)
    weak = engine.classify_text(raw_text="@@@", duration_ms=1)

    assert empty.error_code == OCRErrorCode.NO_TEXT_DETECTED
    assert weak.error_code == OCRErrorCode.WEAK_OCR_RESULT


def test_timed_failure_contains_duration() -> None:
    engine = DummyEngine()

    result = engine.failure(
        OCRErrorCode.OCR_UNEXPECTED_ERROR,
        "Unexpected",
        started_at=engine.now() - 0.001,
    )

    assert result.success is False
    assert result.duration_ms >= 0
