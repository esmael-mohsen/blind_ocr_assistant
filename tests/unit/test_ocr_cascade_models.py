"""Phase 4 OCR cascade model tests."""

from __future__ import annotations

import pytest

from modules.ocr.ocr_cascade import (
    AttemptStatus,
    CascadeRouteMode,
    OCRCascadeError,
    OCRCascadeErrorCode,
    OCRCascadeRequest,
    OCRCascadeResult,
    OCRAttempt,
    sanitize_cascade_metadata,
)
from modules.ocr.ocr_models import OCRErrorCode, OCRResult
from modules.ocr.ocr_quality import (
    LanguageMixStatus,
    OCRQualityIssue,
    OCRQualityReport,
)


def _ocr_result(engine_name: str = "ocr_space", text: str = "Readable text") -> OCRResult:
    return OCRResult.success_result(
        engine_name=engine_name,
        raw_text=text,
        duration_ms=25,
    )


def _quality(score: float = 0.8) -> OCRQualityReport:
    return OCRQualityReport(
        is_acceptable=score >= 0.70,
        quality_score=score,
        threshold=0.70,
        issues=(),
        language_mix_status=LanguageMixStatus.ENGLISH,
        guidance="OCR text is readable.",
    )


def test_cascade_request_defaults_and_validation() -> None:
    request = OCRCascadeRequest(image=b"image-bytes")

    assert request.allow_online is True
    assert request.allow_offline is True
    assert request.high_accuracy is False
    assert request.image_ready_for_ocr is True
    assert request.quality_threshold == 0.70
    assert request.max_attempts_per_engine == 1
    assert request.sensitive_text_logging_enabled is False

    with pytest.raises(ValueError, match="one OCR route"):
        OCRCascadeRequest(image=b"image", allow_online=False, allow_offline=False)

    with pytest.raises(ValueError, match="quality_threshold"):
        OCRCascadeRequest(image=b"image", quality_threshold=1.5)

    with pytest.raises(ValueError, match="max_attempts"):
        OCRCascadeRequest(image=b"image", max_attempts_per_engine=0)


def test_image_not_ready_request_allows_missing_image() -> None:
    request = OCRCascadeRequest(image=None, image_ready_for_ocr=False)

    assert request.image is None
    assert request.image_ready_for_ocr is False

    with pytest.raises(ValueError, match="image"):
        OCRCascadeRequest(image=None, image_ready_for_ocr=True)


def test_attempt_quality_result_error_and_safe_metadata() -> None:
    quality = _quality()
    attempt = OCRAttempt(
        engine_name="ocr_space",
        attempt_order=0,
        status=AttemptStatus.SUCCESS,
        duration_ms=25,
        ocr_result=_ocr_result(),
        quality_report=quality,
        metadata={
            "raw_text": "private",
            "clean_text": "private",
            "image": b"payload",
            "safe_value": "kept",
        },
    )

    assert attempt.safe_metadata["safe_value"] == "kept"
    assert attempt.safe_metadata["engine_name"] == "ocr_space"
    assert "raw_text" not in attempt.safe_metadata
    assert "image" not in attempt.safe_metadata

    error = OCRCascadeError(
        error_code=OCRCascadeErrorCode.ALL_OCR_ENGINES_FAILED,
        message="all failed",
        guidance="Try again.",
    )
    result = OCRCascadeResult(
        success=False,
        selected_engine=None,
        selected_result=None,
        attempts=[attempt],
        fallback_used=True,
        offline_route_used=False,
        high_accuracy_used=False,
        duration_ms=25,
        error=error,
        guidance="Try again.",
    )

    assert result.error == error
    assert result.safe_metadata["fallback_used"] is True
    assert result.safe_metadata["attempted_engines"] == ["ocr_space"]
    assert "selected_result" not in result.safe_metadata


def test_success_result_requires_selected_result_and_quality() -> None:
    quality = _quality()
    attempt = OCRAttempt(
        engine_name="ocr_space",
        attempt_order=0,
        status=AttemptStatus.SUCCESS,
        duration_ms=25,
        ocr_result=_ocr_result(),
        quality_report=quality,
    )
    result = OCRCascadeResult(
        success=True,
        selected_engine="ocr_space",
        selected_result=attempt.ocr_result,
        attempts=[attempt],
        fallback_used=False,
        offline_route_used=False,
        high_accuracy_used=False,
        quality_report=quality,
        duration_ms=25,
        guidance="Ready.",
    )

    assert result.selected_engine == "ocr_space"
    assert result.safe_metadata["selected_engine"] == "ocr_space"

    with pytest.raises(ValueError, match="selected_result"):
        OCRCascadeResult(
            success=True,
            selected_engine="ocr_space",
            selected_result=None,
            attempts=[attempt],
            fallback_used=False,
            offline_route_used=False,
            high_accuracy_used=False,
            duration_ms=25,
            guidance="Ready.",
        )


def test_ocr_quality_report_issue_validation() -> None:
    report = OCRQualityReport(
        is_acceptable=False,
        quality_score=0.1,
        threshold=0.70,
        issues=(OCRQualityIssue.EMPTY_TEXT,),
        language_mix_status=LanguageMixStatus.UNKNOWN,
        guidance="No text was detected.",
    )

    assert report.is_acceptable is False
    assert report.issues == (OCRQualityIssue.EMPTY_TEXT,)

    with pytest.raises(ValueError, match="acceptable"):
        OCRQualityReport(
            is_acceptable=True,
            quality_score=0.1,
            threshold=0.70,
            issues=(),
            language_mix_status=LanguageMixStatus.ENGLISH,
            guidance="bad",
        )


def test_sanitize_cascade_metadata_blocks_sensitive_values() -> None:
    safe = sanitize_cascade_metadata(
        {
            "raw_text": "private",
            "clean_text": "private",
            "ocr_text": "private",
            "image": b"payload",
            "uploaded_payload": b"payload",
            "token": "secret",
            "debug_path": "debug/private.txt",
            "engine_name": "ocr_space",
            "duration_ms": 10,
            "route_mode": CascadeRouteMode.NORMAL,
            "error_code": OCRErrorCode.WEAK_OCR_RESULT,
        }
    )

    assert safe == {
        "engine_name": "ocr_space",
        "duration_ms": 10,
        "route_mode": CascadeRouteMode.NORMAL.value,
        "error_code": OCRErrorCode.WEAK_OCR_RESULT.value,
    }
