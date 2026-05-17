"""Shared OCR engine interface and helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import monotonic
from typing import Any

from modules.ocr.ocr_models import OCRErrorCode, OCRRequest, OCRResult


class OCRBaseEngine(ABC):
    """Base class for Phase 1 OCR engines."""

    engine_name = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the engine appears usable in this environment."""

    @abstractmethod
    def recognize(self, request: OCRRequest) -> OCRResult:
        """Run OCR for one request and return a structured result."""

    @staticmethod
    def now() -> float:
        return monotonic()

    @staticmethod
    def duration_ms(started_at: float) -> int:
        return max(0, int((monotonic() - started_at) * 1000))

    def classify_text(
        self,
        *,
        raw_text: str,
        duration_ms: int,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OCRResult:
        """Convert raw OCR text into success/no-text/weak-result semantics."""
        text = raw_text.strip()
        if not text:
            return OCRResult.failure_result(
                engine_name=self.engine_name,
                error_code=OCRErrorCode.NO_TEXT_DETECTED,
                error_message="No text was detected.",
                duration_ms=duration_ms,
                metadata=metadata,
            )
        if self.is_weak_text(text):
            return OCRResult.failure_result(
                engine_name=self.engine_name,
                error_code=OCRErrorCode.WEAK_OCR_RESULT,
                error_message="OCR text was too weak to accept.",
                duration_ms=duration_ms,
                metadata=metadata,
            )
        return OCRResult.success_result(
            engine_name=self.engine_name,
            raw_text=text,
            duration_ms=duration_ms,
            confidence=confidence,
            metadata=metadata,
        )

    def failure(
        self,
        error_code: OCRErrorCode,
        message: str,
        *,
        started_at: float,
        metadata: dict[str, Any] | None = None,
    ) -> OCRResult:
        return OCRResult.failure_result(
            engine_name=self.engine_name,
            error_code=error_code,
            error_message=message,
            duration_ms=self.duration_ms(started_at),
            metadata=metadata,
        )

    @staticmethod
    def is_weak_text(text: str) -> bool:
        letters_or_digits = [char for char in text if char.isalpha() or char.isdigit()]
        if len(letters_or_digits) < 2:
            return True
        symbol_count = sum(1 for char in text if not char.isalnum() and not char.isspace())
        return symbol_count > len(letters_or_digits)


def ocr_log_metadata(
    result: OCRResult,
    *,
    include_raw_text: bool = False,
) -> dict[str, Any]:
    """Return log-safe OCR metadata, excluding raw text by default."""
    metadata = dict(result.metadata)
    metadata.update(
        {
            "engine_name": result.engine_name,
            "duration_ms": result.duration_ms,
            "success": result.success,
        }
    )
    if result.error_code is not None:
        metadata["error_code"] = result.error_code.value
    if include_raw_text:
        metadata["raw_text"] = result.raw_text
    return metadata
