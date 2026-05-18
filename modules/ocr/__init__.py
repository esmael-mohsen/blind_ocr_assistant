"""OCR engine package."""

from modules.ocr.base import OCRBaseEngine, ocr_log_metadata
from modules.ocr.ocr_cascade import (
    AttemptStatus,
    CascadeRouteMode,
    OCRCascadeError,
    OCRCascadeErrorCode,
    OCRCascadeRequest,
    OCRCascadeResult,
    OCRAttempt,
    cascade_log_metadata,
    run_ocr_cascade,
    sanitize_cascade_metadata,
    should_include_ocr_text_in_logs,
)
from modules.ocr.ocr_models import OCRErrorCode, OCRMode, OCRRequest, OCRResult
from modules.ocr.ocr_quality import (
    LanguageMixStatus,
    OCRQualityIssue,
    OCRQualityReport,
    assess_ocr_quality,
)

__all__ = [
    "OCRBaseEngine",
    "AttemptStatus",
    "CascadeRouteMode",
    "LanguageMixStatus",
    "OCRCascadeError",
    "OCRCascadeErrorCode",
    "OCRCascadeRequest",
    "OCRCascadeResult",
    "OCRAttempt",
    "OCRErrorCode",
    "OCRMode",
    "OCRQualityIssue",
    "OCRQualityReport",
    "OCRRequest",
    "OCRResult",
    "assess_ocr_quality",
    "cascade_log_metadata",
    "ocr_log_metadata",
    "run_ocr_cascade",
    "sanitize_cascade_metadata",
    "should_include_ocr_text_in_logs",
]
