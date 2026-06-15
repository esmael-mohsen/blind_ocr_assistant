"""OCR cascade models and routing helpers for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from config import (
    DEFAULT_OCR_HIGH_ACCURACY_TIE_DELTA,
    DEFAULT_OCR_MAX_ATTEMPTS_PER_ENGINE,
    DEFAULT_OCR_QUALITY_THRESHOLD,
)
from modules.ocr.ocr_models import OCRErrorCode, OCRMode, OCRRequest, OCRResult
from modules.ocr.ocr_quality import OCRQualityReport, assess_ocr_quality


class OCRCascadeErrorCode(StrEnum):
    """Stable OCR cascade failure codes."""

    IMAGE_NOT_READY_FOR_OCR = "IMAGE_NOT_READY_FOR_OCR"
    ONLINE_OCR_UNAVAILABLE = "ONLINE_OCR_UNAVAILABLE"
    ONLINE_OCR_TIMEOUT = "ONLINE_OCR_TIMEOUT"
    WEAK_OCR_RESULT = "WEAK_OCR_RESULT"
    LOCAL_OCR_UNAVAILABLE = "LOCAL_OCR_UNAVAILABLE"
    EMERGENCY_OCR_UNAVAILABLE = "EMERGENCY_OCR_UNAVAILABLE"
    NO_TEXT_DETECTED = "NO_TEXT_DETECTED"
    ALL_OCR_ENGINES_FAILED = "ALL_OCR_ENGINES_FAILED"
    OCR_CASCADE_UNEXPECTED_ERROR = "OCR_CASCADE_UNEXPECTED_ERROR"


class AttemptStatus(StrEnum):
    """One OCR engine attempt outcome."""

    SKIPPED = "skipped"
    SUCCESS = "success"
    WEAK = "weak"
    FAILED = "failed"
    TIMEOUT = "timeout"


class CascadeRouteMode(StrEnum):
    """Cascade routing mode."""

    NORMAL = "normal"
    OFFLINE = "offline"
    HIGH_ACCURACY = "high_accuracy"


SENSITIVE_CASCADE_KEYS = {
    "artifact_path",
    "clean_text",
    "debug_path",
    "image",
    "image_bytes",
    "image_payload",
    "ocr_text",
    "password",
    "raw_text",
    "secret",
    "selected_result",
    "text",
    "token",
    "uploaded_payload",
}


def sanitize_cascade_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return OCR cascade metadata safe for default logs."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_CASCADE_KEYS:
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        if isinstance(value, StrEnum):
            safe[key] = value.value
        else:
            safe[key] = value
    return safe


@dataclass(frozen=True)
class OCRCascadeRequest:
    """One OCR cascade decision request."""

    image: bytes | str | None
    language_hints: tuple[str, ...] = ("ar", "en")
    allow_online: bool = True
    allow_offline: bool = True
    high_accuracy: bool = False
    image_ready_for_ocr: bool = True
    quality_threshold: float = DEFAULT_OCR_QUALITY_THRESHOLD
    max_attempts_per_engine: int = DEFAULT_OCR_MAX_ATTEMPTS_PER_ENGINE
    sensitive_text_logging_enabled: bool = False

    def __post_init__(self) -> None:
        if self.image_ready_for_ocr and self.image is None:
            raise ValueError("image is required when image_ready_for_ocr=True")
        if not self.allow_online and not self.allow_offline:
            raise ValueError("at least one OCR route must be allowed")
        if not 0.0 < self.quality_threshold <= 1.0:
            raise ValueError("quality_threshold must be between 0 and 1")
        if self.max_attempts_per_engine < 1:
            raise ValueError("max_attempts_per_engine must be >= 1")

    @property
    def mode(self) -> OCRMode:
        return OCRMode.HIGH_ACCURACY if self.high_accuracy else OCRMode.NORMAL

    def to_ocr_request(self) -> OCRRequest:
        if isinstance(self.image, bytes):
            return OCRRequest(
                image_bytes=self.image,
                language_hints=self.language_hints,
                mode=self.mode,
                allow_online=self.allow_online,
                allow_offline=self.allow_offline,
            )
        return OCRRequest(
            image_path=str(self.image),
            language_hints=self.language_hints,
            mode=self.mode,
            allow_online=self.allow_online,
            allow_offline=self.allow_offline,
        )


@dataclass(frozen=True)
class OCRCascadeError:
    """Expected OCR cascade failure with user-safe guidance."""

    error_code: OCRCascadeErrorCode
    message: str
    guidance: str

    def __post_init__(self) -> None:
        if not self.message.strip() or not self.guidance.strip():
            raise ValueError("cascade error requires message and guidance")


@dataclass(frozen=True)
class OCRAttempt:
    """One OCR engine attempt or skip in the cascade path."""

    engine_name: str
    attempt_order: int
    status: AttemptStatus
    duration_ms: int = 0
    ocr_result: OCRResult | None = None
    quality_report: OCRQualityReport | None = None
    error_code: OCRCascadeErrorCode | OCRErrorCode | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.engine_name.strip():
            raise ValueError("engine_name is required")
        if self.attempt_order < 0:
            raise ValueError("attempt_order must be non-negative")
        metadata = {
            "engine_name": self.engine_name,
            "attempt_order": self.attempt_order,
            "status": self.status.value,
            "duration_ms": max(0, self.duration_ms),
            **self.metadata,
        }
        if self.error_code is not None:
            metadata["error_code"] = self.error_code.value
        if self.quality_report is not None:
            metadata["quality_score"] = self.quality_report.quality_score
            metadata["quality_acceptable"] = self.quality_report.is_acceptable
        object.__setattr__(self, "safe_metadata", sanitize_cascade_metadata(metadata))


@dataclass(frozen=True)
class OCRCascadeResult:
    """Final OCR cascade decision result."""

    success: bool
    selected_engine: str | None
    selected_result: OCRResult | None
    attempts: list[OCRAttempt]
    fallback_used: bool
    offline_route_used: bool
    high_accuracy_used: bool
    duration_ms: int
    guidance: str
    quality_report: OCRQualityReport | None = None
    error: OCRCascadeError | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if self.success:
            if self.selected_engine is None or self.selected_result is None:
                raise ValueError("successful cascade requires selected_result")
            if self.quality_report is None or not self.quality_report.is_acceptable:
                raise ValueError("successful cascade requires acceptable quality")
        elif self.error is None:
            raise ValueError("failed cascade requires error")
        if not self.guidance.strip():
            raise ValueError("cascade result guidance is required")
        metadata = {
            "success": self.success,
            "selected_engine": self.selected_engine,
            "attempted_engines": [attempt.engine_name for attempt in self.attempts],
            "attempt_count": len(self.attempts),
            "fallback_used": self.fallback_used,
            "offline_route_used": self.offline_route_used,
            "high_accuracy_used": self.high_accuracy_used,
            "duration_ms": max(0, self.duration_ms),
        }
        if self.quality_report is not None:
            metadata["quality_score"] = self.quality_report.quality_score
        if self.error is not None:
            metadata["error_code"] = self.error.error_code.value
        object.__setattr__(self, "safe_metadata", sanitize_cascade_metadata(metadata))


def should_include_ocr_text_in_logs(*, debug_mode: bool, sensitive_text_logging: bool) -> bool:
    """Return whether raw OCR text may be included in logs."""
    return bool(debug_mode and sensitive_text_logging)


def cascade_log_metadata(
    result: OCRCascadeResult,
    *,
    debug_mode: bool = False,
    sensitive_text_logging: bool = False,
) -> dict[str, Any]:
    """Build privacy-preserving cascade metadata for logs."""
    metadata = {
        **result.safe_metadata,
        "attempted_path": [
            f"{attempt.engine_name}:{attempt.status.value}" for attempt in result.attempts
        ],
        "attempts": [attempt.safe_metadata for attempt in result.attempts],
    }
    if result.quality_report is not None:
        metadata["quality_acceptable"] = result.quality_report.is_acceptable
    safe_metadata = sanitize_cascade_metadata(metadata)
    if should_include_ocr_text_in_logs(
        debug_mode=debug_mode,
        sensitive_text_logging=sensitive_text_logging,
    ) and result.selected_result is not None:
        safe_metadata["ocr_text"] = result.selected_result.raw_text
    return safe_metadata


def run_ocr_cascade(
    request: OCRCascadeRequest,
    engines: dict[str, Any],
    online_status_provider: Any | None = None,
    preferred_online_engine: str = "online",
) -> OCRCascadeResult:
    """Run the Phase 4 OCR cascade using injected OCR engines."""
    if not request.image_ready_for_ocr:
        error = OCRCascadeError(
            OCRCascadeErrorCode.IMAGE_NOT_READY_FOR_OCR,
            "The selected image is not ready for OCR.",
            "The image is not clear enough. Please recapture it.",
        )
        return OCRCascadeResult(
            success=False,
            selected_engine=None,
            selected_result=None,
            attempts=[],
            fallback_used=False,
            offline_route_used=False,
            high_accuracy_used=request.high_accuracy,
            duration_ms=0,
            error=error,
            guidance=error.guidance,
        )

    online_key = _online_key(engines, preferred_online_engine)
    route, offline_route_used, online_skip_error = _planned_route(
        request,
        online_status_provider,
        online_key=online_key,
    )
    attempts: list[OCRAttempt] = []
    if online_skip_error is not None:
        attempts.append(
            OCRAttempt(
                engine_name=_engine_name(_resolve_engine(engines, online_key), online_key),
                attempt_order=0,
                status=AttemptStatus.SKIPPED,
                error_code=online_skip_error,
                metadata={"route": CascadeRouteMode.OFFLINE},
            )
        )

    if request.high_accuracy:
        return _run_high_accuracy_route(
            request=request,
            engines=engines,
            route=route,
            attempts=attempts,
            offline_route_used=offline_route_used,
            online_key=online_key,
        )

    return _run_normal_route(
        request=request,
        engines=engines,
        route=route,
        attempts=attempts,
        offline_route_used=offline_route_used,
    )


def _run_normal_route(
    *,
    request: OCRCascadeRequest,
    engines: dict[str, Any],
    route: tuple[str, ...],
    attempts: list[OCRAttempt],
    offline_route_used: bool,
) -> OCRCascadeResult:
    for index, key in enumerate(route, start=len(attempts)):
        attempt = _attempt_engine(engines, key, index, request)
        attempts.append(attempt)
        if (
            attempt.status == AttemptStatus.SUCCESS
            and attempt.quality_report is not None
            and attempt.quality_report.is_acceptable
        ):
            return _success_result(
                selected_attempt=attempt,
                attempts=attempts,
                fallback_used=_fallback_used(attempts),
                offline_route_used=offline_route_used,
                high_accuracy_used=False,
                duration_ms=sum(a.duration_ms for a in attempts),
            )

    return _all_failed_result(
        attempts=attempts,
        fallback_used=_fallback_used(attempts),
        offline_route_used=offline_route_used,
        high_accuracy_used=False,
        duration_ms=sum(a.duration_ms for a in attempts),
    )


def _run_high_accuracy_route(
    *,
    request: OCRCascadeRequest,
    engines: dict[str, Any],
    route: tuple[str, ...],
    attempts: list[OCRAttempt],
    offline_route_used: bool,
    online_key: str,
) -> OCRCascadeResult:
    compared_keys = tuple(key for key in route if key in {online_key, "local"})
    emergency_allowed = "emergency" in route

    for key in compared_keys:
        attempts.append(_attempt_engine(engines, key, len(attempts), request))

    acceptable = [
        attempt
        for attempt in attempts
        if attempt.status == AttemptStatus.SUCCESS
        and attempt.quality_report is not None
        and attempt.quality_report.is_acceptable
    ]
    if acceptable:
        selected = _select_high_accuracy_attempt(acceptable)
        return _success_result(
            selected_attempt=selected,
            attempts=attempts,
            fallback_used=_fallback_used(attempts),
            offline_route_used=offline_route_used,
            high_accuracy_used=True,
            duration_ms=sum(a.duration_ms for a in attempts),
        )

    if emergency_allowed:
        emergency_attempt = _attempt_engine(engines, "emergency", len(attempts), request)
        attempts.append(emergency_attempt)
        if (
            emergency_attempt.status == AttemptStatus.SUCCESS
            and emergency_attempt.quality_report is not None
            and emergency_attempt.quality_report.is_acceptable
        ):
            return _success_result(
                selected_attempt=emergency_attempt,
                attempts=attempts,
                fallback_used=True,
                offline_route_used=offline_route_used,
                high_accuracy_used=True,
                duration_ms=sum(a.duration_ms for a in attempts),
            )

    return _all_failed_result(
        attempts=attempts,
        fallback_used=_fallback_used(attempts),
        offline_route_used=offline_route_used,
        high_accuracy_used=True,
        duration_ms=sum(a.duration_ms for a in attempts),
    )


def _normal_route(online_key: str) -> tuple[str, ...]:
    return (online_key, "local", "emergency")


def _offline_route() -> tuple[str, ...]:
    return ("local", "emergency")


def _planned_route(
    request: OCRCascadeRequest,
    online_status_provider: Any | None,
    *,
    online_key: str,
) -> tuple[tuple[str, ...], bool, OCRCascadeErrorCode | None]:
    if not request.allow_online:
        return (
            _offline_route() if request.allow_offline else (),
            True,
            OCRCascadeErrorCode.ONLINE_OCR_UNAVAILABLE,
        )

    online_available, skip_error = _online_available(online_status_provider)
    if not online_available:
        return (
            _offline_route() if request.allow_offline else (),
            True,
            skip_error or OCRCascadeErrorCode.ONLINE_OCR_UNAVAILABLE,
        )

    if not request.allow_offline:
        return (online_key,), False, None
    return _normal_route(online_key), False, None


def _online_available(
    online_status_provider: Any | None,
) -> tuple[bool, OCRCascadeErrorCode | None]:
    if online_status_provider is None:
        return True, None
    try:
        return bool(online_status_provider()), None
    except TimeoutError:
        return False, OCRCascadeErrorCode.ONLINE_OCR_TIMEOUT
    except OSError:
        return False, OCRCascadeErrorCode.ONLINE_OCR_UNAVAILABLE


def _engine_available(engine: Any) -> bool:
    checker = getattr(engine, "is_available", None)
    return bool(checker()) if callable(checker) else True


def _resolve_engine(engines: dict[str, Any], key: str) -> Any | None:
    aliases = {
        "online": ("online", "ocr_space", "ocrspace"),
        "gemini": ("gemini", "online"),
        "local": ("local", "paddleocr", "paddle"),
        "emergency": ("emergency", "tesseract"),
    }
    for alias in aliases.get(key, (key,)):
        if alias in engines:
            return engines[alias]
    return None


def _engine_name(engine: Any, fallback: str) -> str:
    return str(getattr(engine, "engine_name", fallback)) if engine is not None else fallback


def _recognize(engine: Any, request: OCRCascadeRequest) -> OCRResult:
    return engine.recognize(request.to_ocr_request())


def _attempt_engine(
    engines: dict[str, Any],
    key: str,
    attempt_order: int,
    request: OCRCascadeRequest,
) -> OCRAttempt:
    engine = _resolve_engine(engines, key)
    if engine is None or not _engine_available(engine):
        return OCRAttempt(
            engine_name=_engine_name(engine, key),
            attempt_order=attempt_order,
            status=AttemptStatus.SKIPPED,
            error_code=_unavailable_error_for_key(key),
        )

    result = _recognize(engine, request)
    quality = _quality_for_result(result, request)
    status = _attempt_status(result, quality)
    return OCRAttempt(
        engine_name=result.engine_name,
        attempt_order=attempt_order,
        status=status,
        duration_ms=result.duration_ms,
        ocr_result=result,
        quality_report=quality if result.success else None,
        error_code=_error_code_for_attempt(result, quality, status),
        metadata={"route_key": key},
    )


def _quality_for_result(result: OCRResult, request: OCRCascadeRequest) -> OCRQualityReport:
    quality = assess_ocr_quality(
        result.raw_text if result.success else "",
        request.language_hints,
        request.quality_threshold,
    )
    if not result.success or result.quality_score is None:
        return quality

    score = max(0.0, min(1.0, result.quality_score))
    is_acceptable = score >= request.quality_threshold and not any(
        issue.value in {"empty_text", "very_short_text"} for issue in quality.issues
    )
    return OCRQualityReport(
        is_acceptable=is_acceptable,
        quality_score=score,
        threshold=request.quality_threshold,
        issues=quality.issues,
        language_mix_status=quality.language_mix_status,
        guidance="OCR text is readable."
        if is_acceptable
        else "OCR text was too weak; trying another OCR option.",
    )


def _attempt_status(result: OCRResult, quality: OCRQualityReport) -> AttemptStatus:
    if not result.success:
        if result.error_code == OCRErrorCode.OCR_PROVIDER_TIMEOUT:
            return AttemptStatus.TIMEOUT
        return AttemptStatus.FAILED
    if not quality.is_acceptable:
        return AttemptStatus.WEAK
    return AttemptStatus.SUCCESS


def _error_code_for_attempt(
    result: OCRResult,
    quality: OCRQualityReport,
    status: AttemptStatus,
) -> OCRCascadeErrorCode | OCRErrorCode | None:
    if status == AttemptStatus.SUCCESS:
        return None
    if status == AttemptStatus.WEAK:
        return OCRCascadeErrorCode.WEAK_OCR_RESULT
    if result.error_code is not None:
        return result.error_code
    return OCRCascadeErrorCode.OCR_CASCADE_UNEXPECTED_ERROR


def _unavailable_error_for_key(key: str) -> OCRCascadeErrorCode:
    if key in {"online", "gemini"}:
        return OCRCascadeErrorCode.ONLINE_OCR_UNAVAILABLE
    if key == "local":
        return OCRCascadeErrorCode.LOCAL_OCR_UNAVAILABLE
    return OCRCascadeErrorCode.EMERGENCY_OCR_UNAVAILABLE


def _fallback_used(attempts: list[OCRAttempt]) -> bool:
    return len([attempt for attempt in attempts if attempt.status != AttemptStatus.SKIPPED]) > 1


def _select_high_accuracy_attempt(attempts: list[OCRAttempt]) -> OCRAttempt:
    by_score = sorted(
        attempts,
        key=lambda attempt: (
            attempt.quality_report.quality_score if attempt.quality_report else 0.0,
            -attempt.duration_ms,
        ),
        reverse=True,
    )
    best = by_score[0]
    best_score = best.quality_report.quality_score if best.quality_report else 0.0
    similar = [
        attempt
        for attempt in attempts
        if attempt.quality_report is not None
        and best_score - attempt.quality_report.quality_score < HIGH_ACCURACY_TIE_DELTA
    ]
    local_attempts = [attempt for attempt in similar if attempt.engine_name == "paddleocr"]
    if local_attempts:
        return min(local_attempts, key=lambda attempt: attempt.duration_ms)
    return min(similar, key=lambda attempt: attempt.duration_ms)


def _online_key(engines: dict[str, Any], preferred_online_engine: str) -> str:
    preferred = (preferred_online_engine or "online").strip() or "online"
    if preferred in engines:
        return preferred
    if "online" in engines:
        return "online"
    return preferred


def _success_result(
    *,
    selected_attempt: OCRAttempt,
    attempts: list[OCRAttempt],
    fallback_used: bool,
    offline_route_used: bool,
    high_accuracy_used: bool,
    duration_ms: int,
) -> OCRCascadeResult:
    return OCRCascadeResult(
        success=True,
        selected_engine=selected_attempt.engine_name,
        selected_result=selected_attempt.ocr_result,
        attempts=attempts,
        fallback_used=fallback_used,
        offline_route_used=offline_route_used,
        high_accuracy_used=high_accuracy_used,
        quality_report=selected_attempt.quality_report,
        duration_ms=duration_ms,
        guidance=_success_guidance(
            fallback_used=fallback_used,
            offline_route_used=offline_route_used,
            high_accuracy_used=high_accuracy_used,
        ),
    )


def _success_guidance(
    *,
    fallback_used: bool,
    offline_route_used: bool,
    high_accuracy_used: bool,
) -> str:
    if high_accuracy_used:
        return "OCR text is ready after comparing available OCR results."
    if offline_route_used:
        return "OCR text is ready using the offline OCR route."
    if fallback_used:
        return "OCR text is ready after fallback OCR."
    return "OCR text is ready for reading."


def _all_failed_result(
    *,
    attempts: list[OCRAttempt],
    fallback_used: bool,
    offline_route_used: bool,
    high_accuracy_used: bool,
    duration_ms: int,
) -> OCRCascadeResult:
    error = OCRCascadeError(
        OCRCascadeErrorCode.ALL_OCR_ENGINES_FAILED,
        "All allowed OCR engines failed or returned weak text.",
        "I could not read the text clearly. Please try again.",
    )
    return OCRCascadeResult(
        success=False,
        selected_engine=None,
        selected_result=None,
        attempts=attempts,
        fallback_used=fallback_used,
        offline_route_used=offline_route_used,
        high_accuracy_used=high_accuracy_used,
        duration_ms=duration_ms,
        error=error,
        guidance=error.guidance,
    )


HIGH_ACCURACY_TIE_DELTA = DEFAULT_OCR_HIGH_ACCURACY_TIE_DELTA


__all__ = [
    "AttemptStatus",
    "CascadeRouteMode",
    "HIGH_ACCURACY_TIE_DELTA",
    "OCRCascadeError",
    "OCRCascadeErrorCode",
    "OCRCascadeRequest",
    "OCRCascadeResult",
    "OCRAttempt",
    "cascade_log_metadata",
    "run_ocr_cascade",
    "sanitize_cascade_metadata",
    "should_include_ocr_text_in_logs",
]
