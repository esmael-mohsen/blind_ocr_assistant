"""OCR request and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


SUPPORTED_OCR_LANGUAGES = ("ar", "en")


class OCRMode(StrEnum):
    """Supported OCR mode values for Phase 1."""

    NORMAL = "normal"
    HIGH_ACCURACY = "high_accuracy"


class OCRErrorCode(StrEnum):
    """Stable OCR failure codes for later spoken-message mapping."""

    OCR_MISSING_CREDENTIAL = "OCR_MISSING_CREDENTIAL"
    OCR_PROVIDER_TIMEOUT = "OCR_PROVIDER_TIMEOUT"
    OCR_PROVIDER_ERROR = "OCR_PROVIDER_ERROR"
    OCR_MALFORMED_RESPONSE = "OCR_MALFORMED_RESPONSE"
    OCR_IMAGE_NOT_FOUND = "OCR_IMAGE_NOT_FOUND"
    OCR_MODEL_LOAD_ERROR = "OCR_MODEL_LOAD_ERROR"
    OCR_EXECUTABLE_NOT_FOUND = "OCR_EXECUTABLE_NOT_FOUND"
    OCR_LANGUAGE_DATA_MISSING = "OCR_LANGUAGE_DATA_MISSING"
    NO_TEXT_DETECTED = "NO_TEXT_DETECTED"
    WEAK_OCR_RESULT = "WEAK_OCR_RESULT"
    OCR_UNEXPECTED_ERROR = "OCR_UNEXPECTED_ERROR"


@dataclass(frozen=True)
class OCRRequest:
    """One OCR request for one image source."""

    image_path: str | Path | None = None
    image_bytes: bytes | None = None
    language_hints: tuple[str, ...] = SUPPORTED_OCR_LANGUAGES
    mode: OCRMode = OCRMode.NORMAL
    preprocessing_variant: str | None = None
    allow_online: bool = True
    allow_offline: bool = True
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        has_path = self.image_path is not None
        has_bytes = self.image_bytes is not None
        if has_path == has_bytes:
            raise ValueError("Exactly one of image_path or image_bytes is required")
        invalid = set(self.language_hints).difference(SUPPORTED_OCR_LANGUAGES)
        if invalid:
            raise ValueError(f"Unsupported OCR language hints: {sorted(invalid)}")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class OCRResult:
    """Structured result returned by every OCR engine."""

    engine_name: str
    raw_text: str = ""
    clean_text: str | None = None
    confidence: float | None = None
    quality_score: float | None = None
    duration_ms: int = 0
    success: bool = False
    error_code: OCRErrorCode | None = None
    error_message: str | None = None
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        *,
        engine_name: str,
        raw_text: str,
        duration_ms: int,
        confidence: float | None = None,
        quality_score: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "OCRResult":
        if not raw_text.strip():
            raise ValueError("Successful OCR requires non-empty raw_text")
        safe_metadata = _safe_metadata(
            engine_name=engine_name,
            duration_ms=duration_ms,
            success=True,
            error_code=None,
            metadata=metadata,
        )
        return cls(
            engine_name=engine_name,
            raw_text=raw_text,
            confidence=confidence,
            quality_score=quality_score,
            duration_ms=max(0, duration_ms),
            success=True,
            metadata=safe_metadata,
        )

    @classmethod
    def failure_result(
        cls,
        *,
        engine_name: str,
        error_code: OCRErrorCode,
        error_message: str,
        duration_ms: int,
        metadata: dict[str, Any] | None = None,
    ) -> "OCRResult":
        safe_metadata = _safe_metadata(
            engine_name=engine_name,
            duration_ms=duration_ms,
            success=False,
            error_code=error_code,
            metadata=metadata,
        )
        return cls(
            engine_name=engine_name,
            duration_ms=max(0, duration_ms),
            success=False,
            error_code=error_code,
            error_message=error_message,
            metadata=safe_metadata,
        )


def _safe_metadata(
    *,
    engine_name: str,
    duration_ms: int,
    success: bool,
    error_code: OCRErrorCode | None,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    safe = {
        "engine_name": engine_name,
        "duration_ms": max(0, duration_ms),
        "success": success,
    }
    if error_code is not None:
        safe["error_code"] = error_code.value
    for key, value in (metadata or {}).items():
        if key not in {"raw_text", "clean_text", "text", "ocr_text"}:
            safe[key] = value
    return safe
