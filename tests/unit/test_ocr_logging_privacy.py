"""OCR logging privacy tests."""

from __future__ import annotations

from modules.ocr.base import ocr_log_metadata
from modules.ocr.ocr_models import OCRResult


def test_ocr_log_metadata_excludes_raw_text_by_default() -> None:
    result = OCRResult.success_result(
        engine_name="engine",
        raw_text="sensitive medicine label",
        duration_ms=9,
    )

    metadata = ocr_log_metadata(result)

    assert metadata["engine_name"] == "engine"
    assert metadata["success"] is True
    assert "sensitive medicine label" not in str(metadata)


def test_ocr_log_metadata_includes_raw_text_only_when_enabled() -> None:
    result = OCRResult.success_result(
        engine_name="engine",
        raw_text="debug text",
        duration_ms=9,
    )

    metadata = ocr_log_metadata(result, include_raw_text=True)

    assert metadata["raw_text"] == "debug text"
