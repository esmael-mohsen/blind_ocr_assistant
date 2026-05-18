"""Privacy-safe OCR cascade logging tests."""

from __future__ import annotations

from modules.ocr.ocr_cascade import (
    AttemptStatus,
    OCRCascadeError,
    OCRCascadeErrorCode,
    OCRCascadeResult,
    OCRAttempt,
    cascade_log_metadata,
    sanitize_cascade_metadata,
    should_include_ocr_text_in_logs,
)
from modules.ocr.ocr_models import OCRResult
from modules.ocr.ocr_quality import OCRQualityReport


def _successful_result(raw_text: str = "Sensitive receipt text") -> OCRCascadeResult:
    ocr_result = OCRResult.success_result(
        engine_name="paddleocr",
        raw_text=raw_text,
        duration_ms=12,
        quality_score=0.84,
    )
    quality = OCRQualityReport(is_acceptable=True, quality_score=0.84)
    attempt = OCRAttempt(
        engine_name="paddleocr",
        attempt_order=0,
        status=AttemptStatus.SUCCESS,
        duration_ms=12,
        ocr_result=ocr_result,
        quality_report=quality,
        metadata={"raw_text": raw_text, "image_bytes": b"private"},
    )
    return OCRCascadeResult(
        success=True,
        selected_engine="paddleocr",
        selected_result=ocr_result,
        attempts=[attempt],
        fallback_used=False,
        offline_route_used=True,
        high_accuracy_used=False,
        duration_ms=12,
        quality_report=quality,
        guidance="OCR text is ready for reading.",
    )


def test_safe_metadata_excludes_text_images_payloads_secrets_and_debug_paths() -> None:
    metadata = sanitize_cascade_metadata(
        {
            "raw_text": "private",
            "clean_text": "private",
            "image": b"private",
            "image_bytes": b"private",
            "uploaded_payload": {"raw_text": "private"},
            "secret": "private",
            "token": "private",
            "debug_path": "C:/private/debug.txt",
            "duration_ms": 15,
        }
    )

    assert metadata == {"duration_ms": 15}


def test_default_log_metadata_excludes_ocr_text() -> None:
    result = _successful_result("Bank account text")

    metadata = cascade_log_metadata(result)

    assert "ocr_text" not in metadata
    assert "Bank account text" not in str(metadata)


def test_ocr_text_is_logged_only_when_debug_and_sensitive_logging_are_enabled() -> None:
    result = _successful_result("Debug-only OCR text")

    assert should_include_ocr_text_in_logs(
        debug_mode=True,
        sensitive_text_logging=True,
    )
    assert not should_include_ocr_text_in_logs(
        debug_mode=True,
        sensitive_text_logging=False,
    )
    assert not should_include_ocr_text_in_logs(
        debug_mode=False,
        sensitive_text_logging=True,
    )
    assert "ocr_text" not in cascade_log_metadata(
        result,
        debug_mode=True,
        sensitive_text_logging=False,
    )
    assert cascade_log_metadata(
        result,
        debug_mode=True,
        sensitive_text_logging=True,
    )["ocr_text"] == "Debug-only OCR text"


def test_cascade_log_metadata_includes_path_duration_quality_fallback_and_errors() -> None:
    attempt = OCRAttempt(
        engine_name="ocr_space",
        attempt_order=0,
        status=AttemptStatus.FAILED,
        duration_ms=9,
        error_code=OCRCascadeErrorCode.ONLINE_OCR_UNAVAILABLE,
    )
    error = OCRCascadeError(
        error_code=OCRCascadeErrorCode.ALL_OCR_ENGINES_FAILED,
        message="All engines failed.",
        guidance="Please try again.",
    )
    result = OCRCascadeResult(
        success=False,
        selected_engine=None,
        selected_result=None,
        attempts=[attempt],
        fallback_used=True,
        offline_route_used=True,
        high_accuracy_used=False,
        duration_ms=9,
        error=error,
        guidance=error.guidance,
    )

    metadata = cascade_log_metadata(result)

    assert metadata["attempted_path"] == ["ocr_space:failed"]
    assert metadata["selected_engine"] is None
    assert metadata["duration_ms"] == 9
    assert metadata["fallback_used"] is True
    assert metadata["error_code"] == OCRCascadeErrorCode.ALL_OCR_ENGINES_FAILED.value
