"""Language detection models and helpers for Phase 5."""

from __future__ import annotations

from dataclasses import dataclass
import re

from modules.text.cleanup import CleanupWarning, DetectedLanguage, TextDirection


@dataclass(frozen=True)
class DirectionInfo:
    """Text direction evidence for later workflows."""

    direction: TextDirection
    has_rtl: bool
    has_ltr: bool
    logical_order_preserved: bool = True


@dataclass(frozen=True)
class LanguageDetectionResult:
    """Deterministic language classification evidence."""

    language: DetectedLanguage
    confidence: float
    arabic_character_count: int
    english_character_count: int
    language_character_count: int
    dominant_ratio: float
    direction: TextDirection
    warnings: tuple[CleanupWarning, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not 0.0 <= self.dominant_ratio <= 1.0:
            raise ValueError("dominant_ratio must be between 0 and 1")
        counts = (
            self.arabic_character_count,
            self.english_character_count,
            self.language_character_count,
        )
        if any(count < 0 for count in counts):
            raise ValueError("language evidence counts must be non-negative")
        if (
            self.arabic_character_count + self.english_character_count
            > self.language_character_count
        ):
            raise ValueError("language evidence counts exceed total")


ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
ENGLISH_RE = re.compile(r"[A-Za-z]")
MIN_LANGUAGE_EVIDENCE = 3
DOMINANT_LANGUAGE_RATIO = 0.60


def detect_language(text: str) -> LanguageDetectionResult:
    """Detect Arabic, English, mixed, or unknown using deterministic evidence."""
    value = text or ""
    arabic_count = len(ARABIC_RE.findall(value))
    english_count = len(ENGLISH_RE.findall(value))
    total = arabic_count + english_count
    if total == 0:
        return _unknown_result(arabic_count, english_count, total)

    dominant_count = max(arabic_count, english_count)
    dominant_ratio = round(dominant_count / total, 2)
    has_arabic = arabic_count >= MIN_LANGUAGE_EVIDENCE
    has_english = english_count >= MIN_LANGUAGE_EVIDENCE
    warnings: list[CleanupWarning] = []

    if total < MIN_LANGUAGE_EVIDENCE:
        warnings.append(CleanupWarning.UNCERTAIN_LANGUAGE)
        return _unknown_result(arabic_count, english_count, total, warnings=warnings)

    if has_arabic and has_english:
        if dominant_ratio >= DOMINANT_LANGUAGE_RATIO:
            language = (
                DetectedLanguage.ARABIC
                if arabic_count >= english_count
                else DetectedLanguage.ENGLISH
            )
        else:
            language = DetectedLanguage.MIXED
        direction = TextDirection.MIXED if language == DetectedLanguage.MIXED else (
            TextDirection.RTL if language == DetectedLanguage.ARABIC else TextDirection.LTR
        )
        warnings.append(CleanupWarning.MIXED_DIRECTION)
    elif has_arabic:
        language = DetectedLanguage.ARABIC
        direction = TextDirection.RTL
    elif has_english:
        language = DetectedLanguage.ENGLISH
        direction = TextDirection.LTR
    else:
        warnings.append(CleanupWarning.UNCERTAIN_LANGUAGE)
        return _unknown_result(arabic_count, english_count, total, warnings=warnings)

    confidence = dominant_ratio if language != DetectedLanguage.MIXED else _mixed_confidence(
        arabic_count,
        english_count,
        total,
    )
    return LanguageDetectionResult(
        language=language,
        confidence=confidence,
        arabic_character_count=arabic_count,
        english_character_count=english_count,
        language_character_count=total,
        dominant_ratio=dominant_ratio,
        direction=direction,
        warnings=tuple(warnings),
    )


def _unknown_result(
    arabic_count: int,
    english_count: int,
    total: int,
    *,
    warnings: list[CleanupWarning] | None = None,
) -> LanguageDetectionResult:
    return LanguageDetectionResult(
        language=DetectedLanguage.UNKNOWN,
        confidence=0.0,
        arabic_character_count=arabic_count,
        english_character_count=english_count,
        language_character_count=total,
        dominant_ratio=0.0 if total == 0 else round(max(arabic_count, english_count) / total, 2),
        direction=TextDirection.UNKNOWN,
        warnings=tuple(warnings or (CleanupWarning.UNCERTAIN_LANGUAGE,)),
    )


def _mixed_confidence(arabic_count: int, english_count: int, total: int) -> float:
    balance = 1.0 - (abs(arabic_count - english_count) / total)
    return round(max(0.0, min(1.0, balance)), 2)


__all__ = [
    "DirectionInfo",
    "LanguageDetectionResult",
    "detect_language",
]
