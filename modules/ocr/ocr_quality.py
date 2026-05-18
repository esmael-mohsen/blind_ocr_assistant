"""Deterministic OCR text quality scoring for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from config import DEFAULT_OCR_QUALITY_THRESHOLD


class OCRQualityIssue(StrEnum):
    """Stable OCR text quality issues used by cascade routing."""

    EMPTY_TEXT = "empty_text"
    VERY_SHORT_TEXT = "very_short_text"
    SYMBOL_HEAVY_TEXT = "symbol_heavy_text"
    EXCESSIVE_SPACING = "excessive_spacing"
    REPEATED_CHARACTERS = "repeated_characters"
    ARABIC_FRAGMENTATION = "arabic_fragmentation"


class LanguageMixStatus(StrEnum):
    """Coarse language mix classification for OCR output."""

    ARABIC = "arabic"
    ENGLISH = "english"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class OCRQualityReport:
    """Deterministic OCR output quality decision."""

    is_acceptable: bool
    quality_score: float
    threshold: float = DEFAULT_OCR_QUALITY_THRESHOLD
    issues: tuple[OCRQualityIssue, ...] = ()
    language_mix_status: LanguageMixStatus = LanguageMixStatus.UNKNOWN
    guidance: str = "OCR text is readable."

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        if not 0.0 < self.threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if self.is_acceptable and self.quality_score < self.threshold:
            raise ValueError("acceptable OCR quality requires score at threshold")
        if not self.guidance.strip():
            raise ValueError("quality guidance is required")


ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")


def assess_ocr_quality(
    text: str,
    language_hints: tuple[str, ...] | None = None,
    threshold: float = DEFAULT_OCR_QUALITY_THRESHOLD,
) -> OCRQualityReport:
    """Score OCR text using deterministic, transparent heuristics."""
    normalized = (text or "").strip()
    issues: list[OCRQualityIssue] = []
    if not normalized:
        return OCRQualityReport(
            is_acceptable=False,
            quality_score=0.0,
            threshold=threshold,
            issues=(OCRQualityIssue.EMPTY_TEXT,),
            language_mix_status=LanguageMixStatus.UNKNOWN,
            guidance="No text was detected. Try capturing the image again.",
        )

    score = 1.0
    letters_or_digits = [char for char in normalized if char.isalpha() or char.isdigit()]
    if len(letters_or_digits) < 6:
        issues.append(OCRQualityIssue.VERY_SHORT_TEXT)
        score -= 0.45

    non_space = [char for char in normalized if not char.isspace()]
    symbols = [char for char in non_space if not char.isalnum()]
    if non_space and len(symbols) / len(non_space) > 0.35:
        issues.append(OCRQualityIssue.SYMBOL_HEAVY_TEXT)
        score -= 0.35

    if re.search(r"(.)\1{4,}", normalized):
        issues.append(OCRQualityIssue.REPEATED_CHARACTERS)
        score -= 0.3

    single_letter_words = re.findall(r"\b[\w\u0600-\u06FF]\b", normalized)
    words = re.findall(r"[\w\u0600-\u06FF]+", normalized)
    if len(words) >= 5 and len(single_letter_words) / max(len(words), 1) > 0.45:
        issues.append(OCRQualityIssue.EXCESSIVE_SPACING)
        score -= 0.35

    arabic_chars = ARABIC_RE.findall(normalized)
    if arabic_chars:
        arabic_singletons = re.findall(r"(?<![\u0600-\u06FF])[\u0600-\u06FF](?![\u0600-\u06FF])", normalized)
        if len(arabic_chars) >= 6 and len(arabic_singletons) / len(arabic_chars) > 0.4:
            issues.append(OCRQualityIssue.ARABIC_FRAGMENTATION)
            score -= 0.35

    language_status = _language_mix_status(normalized)
    score = max(0.0, min(1.0, score))
    is_acceptable = score >= threshold and not _has_blocking_issue(issues)
    return OCRQualityReport(
        is_acceptable=is_acceptable,
        quality_score=score,
        threshold=threshold,
        issues=tuple(issues),
        language_mix_status=language_status,
        guidance="OCR text is readable."
        if is_acceptable
        else "OCR text was too weak; trying another OCR option.",
    )


def _language_mix_status(text: str) -> LanguageMixStatus:
    has_arabic = bool(ARABIC_RE.search(text))
    has_latin = bool(LATIN_RE.search(text))
    if has_arabic and has_latin:
        return LanguageMixStatus.MIXED
    if has_arabic:
        return LanguageMixStatus.ARABIC
    if has_latin:
        return LanguageMixStatus.ENGLISH
    return LanguageMixStatus.UNKNOWN


def _has_blocking_issue(issues: list[OCRQualityIssue]) -> bool:
    return OCRQualityIssue.EMPTY_TEXT in issues or OCRQualityIssue.VERY_SHORT_TEXT in issues


__all__ = [
    "LanguageMixStatus",
    "OCRQualityIssue",
    "OCRQualityReport",
    "assess_ocr_quality",
]
