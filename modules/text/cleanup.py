"""Text cleanup models and helpers for Phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import re
from typing import Any


class TextCleanupStatus(StrEnum):
    """Stable cleanup result status."""

    CLEAN = "clean"
    EMPTY = "empty"
    NOISY = "noisy"
    UNCERTAIN_LANGUAGE = "uncertain_language"
    INVALID_INPUT = "invalid_input"


class CleanupWarning(StrEnum):
    """Non-fatal cleanup warnings safe for logs and later guidance."""

    EMPTY_INPUT = "EMPTY_INPUT"
    NOISY_TEXT = "NOISY_TEXT"
    UNCERTAIN_LANGUAGE = "UNCERTAIN_LANGUAGE"
    MIXED_DIRECTION = "MIXED_DIRECTION"
    PRESERVED_UNCERTAIN_FRAGMENT = "PRESERVED_UNCERTAIN_FRAGMENT"
    UNSUPPORTED_LANGUAGE_HINT = "UNSUPPORTED_LANGUAGE_HINT"
    PUNCTUATION_NORMALIZED = "PUNCTUATION_NORMALIZED"
    LINE_BREAKS_NORMALIZED = "LINE_BREAKS_NORMALIZED"


class DetectedLanguage(StrEnum):
    """Supported Phase 5 language classifications."""

    ARABIC = "arabic"
    ENGLISH = "english"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class TextDirection(StrEnum):
    """Supported text direction classifications."""

    RTL = "rtl"
    LTR = "ltr"
    MIXED = "mixed"
    UNKNOWN = "unknown"


SENSITIVE_TEXT_METADATA_KEYS = {
    "clean_text",
    "debug_path",
    "raw_text",
    "secret",
    "snippet",
    "text",
    "token",
}


def sanitize_text_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return text metadata safe for default logs."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_TEXT_METADATA_KEYS:
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        if isinstance(value, StrEnum):
            safe[key] = value.value
        elif isinstance(value, tuple):
            safe[key] = [item.value if isinstance(item, StrEnum) else item for item in value]
        else:
            safe[key] = value
    return safe


@dataclass(frozen=True)
class TextCleanupRequest:
    """Raw OCR text input for Phase 5 cleanup."""

    raw_text: str
    language_hints: tuple[str, ...] = ()
    source_engine: str | None = None
    preserve_paragraphs: bool = True
    sensitive_text_logging_enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.raw_text, str):
            raise TypeError("raw_text must be a string")
        if not isinstance(self.language_hints, tuple):
            object.__setattr__(self, "language_hints", tuple(self.language_hints))


@dataclass(frozen=True)
class TextCleanupResult:
    """Structured text cleanup result."""

    success: bool
    raw_text: str
    clean_text: str
    status: TextCleanupStatus
    language: DetectedLanguage
    direction: TextDirection
    guidance: str
    warnings: tuple[CleanupWarning, ...] = ()
    source_engine: str | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.raw_text, str) or not isinstance(self.clean_text, str):
            raise TypeError("raw_text and clean_text must be strings")
        if not self.guidance.strip():
            raise ValueError("guidance is required")
        if self.status == TextCleanupStatus.EMPTY:
            if self.clean_text != "":
                raise ValueError("empty cleanup status requires empty clean_text")
            if self.language != DetectedLanguage.UNKNOWN:
                raise ValueError("empty cleanup status requires unknown language")
            if self.direction != TextDirection.UNKNOWN:
                raise ValueError("empty cleanup status requires unknown direction")
        metadata = {
            "success": self.success,
            "status": self.status,
            "language": self.language,
            "direction": self.direction,
            "warning_codes": self.warnings,
            "raw_length": len(self.raw_text),
            "clean_length": len(self.clean_text),
            "source_engine": self.source_engine,
        }
        object.__setattr__(self, "safe_metadata", sanitize_text_metadata(metadata))


def clean_ocr_text(request: TextCleanupRequest | str) -> TextCleanupResult:
    """Clean raw OCR text while preserving the original input."""
    if isinstance(request, str):
        request = TextCleanupRequest(raw_text=request)

    raw_text = request.raw_text
    if not raw_text.strip():
        return TextCleanupResult(
            success=True,
            raw_text=raw_text,
            clean_text="",
            status=TextCleanupStatus.EMPTY,
            language=DetectedLanguage.UNKNOWN,
            direction=TextDirection.UNKNOWN,
            warnings=(CleanupWarning.EMPTY_INPUT,),
            guidance="No readable text was available.",
            source_engine=request.source_engine,
        )

    warnings: list[CleanupWarning] = []
    text = _normalize_line_breaks(raw_text, preserve_paragraphs=request.preserve_paragraphs)
    if text != raw_text:
        warnings.append(CleanupWarning.LINE_BREAKS_NORMALIZED)

    before_punctuation = text
    text = _normalize_punctuation_spacing(text)
    if text != before_punctuation:
        warnings.append(CleanupWarning.PUNCTUATION_NORMALIZED)

    text = _normalize_inline_whitespace(text)
    noisy = _has_uncertain_garbage(text)
    if noisy:
        warnings.append(CleanupWarning.PRESERVED_UNCERTAIN_FRAGMENT)
        warnings.append(CleanupWarning.NOISY_TEXT)

    text = text.strip()
    from modules.text.rtl_fixer import detect_text_direction, preserve_logical_order

    text = preserve_logical_order(text)
    direction_info = detect_text_direction(text)
    if direction_info.direction == TextDirection.MIXED:
        warnings.append(CleanupWarning.MIXED_DIRECTION)

    from modules.text.language_detector import detect_language

    language_result = detect_language(text)
    warnings.extend(language_result.warnings)
    if language_result.language == DetectedLanguage.UNKNOWN:
        status = TextCleanupStatus.UNCERTAIN_LANGUAGE
    elif noisy:
        status = TextCleanupStatus.NOISY
    else:
        status = TextCleanupStatus.CLEAN
    return TextCleanupResult(
        success=True,
        raw_text=raw_text,
        clean_text=text,
        status=status,
        language=language_result.language,
        direction=direction_info.direction,
        warnings=_deduplicate_warnings(warnings),
        guidance="Text may contain unclear OCR fragments."
        if noisy
        else "Text language is uncertain."
        if language_result.language == DetectedLanguage.UNKNOWN
        else "Text is ready for reading.",
        source_engine=request.source_engine,
    )


def should_include_text_in_logs(*, debug_mode: bool, sensitive_text_logging: bool) -> bool:
    """Return whether raw and clean text may be included in logs."""
    return bool(debug_mode and sensitive_text_logging)


def text_log_metadata(
    result: TextCleanupResult,
    *,
    debug_mode: bool = False,
    sensitive_text_logging: bool = False,
) -> dict[str, Any]:
    """Build privacy-preserving text cleanup metadata for logs."""
    metadata = sanitize_text_metadata(result.safe_metadata)
    if should_include_text_in_logs(
        debug_mode=debug_mode,
        sensitive_text_logging=sensitive_text_logging,
    ):
        metadata["raw_text"] = result.raw_text
        metadata["clean_text"] = result.clean_text
    return metadata


def _normalize_line_breaks(text: str, *, preserve_paragraphs: bool) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n\s*\n", text.strip())
    normalized: list[str] = []
    for paragraph in paragraphs:
        lines = [line.strip() for line in paragraph.split("\n")]
        if _has_list_like_lines(lines) or _has_language_shift_lines(lines):
            normalized.append("\n".join(line for line in lines if line))
        else:
            normalized.append(" ".join(line for line in lines if line))
    separator = "\n\n" if preserve_paragraphs else " "
    return separator.join(part for part in normalized if part)


def _has_list_like_lines(lines: list[str]) -> bool:
    return any(re.match(r"^([-*•]|\d+[.)])\s+", line) for line in lines)


def _has_language_shift_lines(lines: list[str]) -> bool:
    non_empty = [line for line in lines if line]
    if len(non_empty) < 2:
        return False
    scripts = {_line_script(line) for line in non_empty}
    scripts.discard("unknown")
    return len(scripts) > 1


def _line_script(line: str) -> str:
    has_arabic = bool(re.search(r"[\u0600-\u06FF]", line))
    has_latin = bool(re.search(r"[A-Za-z]", line))
    if has_arabic and not has_latin:
        return "arabic"
    if has_latin and not has_arabic:
        return "latin"
    if has_arabic and has_latin:
        return "mixed"
    return "unknown"


def _normalize_punctuation_spacing(text: str) -> str:
    punctuation = r"\.,!\?:;،؛؟"
    text = re.sub(rf"\s+([{punctuation}])", r"\1", text)
    text = re.sub(rf"([{punctuation}])(?=[^\s\n\d{punctuation}])", r"\1 ", text)
    return text


def _normalize_inline_whitespace(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines)


def _has_uncertain_garbage(text: str) -> bool:
    return bool(re.search(r"[#@$%^&*_~|\\/<>{}\[\]=]{3,}", text))


def _deduplicate_warnings(warnings: list[CleanupWarning]) -> tuple[CleanupWarning, ...]:
    deduped: list[CleanupWarning] = []
    for warning in warnings:
        if warning not in deduped:
            deduped.append(warning)
    return tuple(deduped)


__all__ = [
    "CleanupWarning",
    "DetectedLanguage",
    "TextCleanupRequest",
    "TextCleanupResult",
    "TextCleanupStatus",
    "TextDirection",
    "clean_ocr_text",
    "sanitize_text_metadata",
    "should_include_text_in_logs",
    "text_log_metadata",
]
