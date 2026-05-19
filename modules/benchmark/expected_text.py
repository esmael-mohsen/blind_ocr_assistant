"""Expected-text loading and conservative comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re

from modules.benchmark.benchmark_models import BenchmarkError, ExpectedTextReference


WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ExpectedTextComparison:
    """Expected-text comparison outcome."""

    available: bool
    score: float | None
    reason: str | None = None


def normalize_expected_text(text: str) -> str:
    """Normalize harmless whitespace while preserving meaningful characters."""

    return WHITESPACE_RE.sub(" ", text or "").strip()


def load_expected_text(reference: ExpectedTextReference) -> str:
    """Read a non-empty safe expected text reference."""

    path = Path(reference.text_path)
    if not path.exists():
        raise BenchmarkError(f"expected text file missing: {path}")
    text = path.read_text(encoding="utf-8")
    normalized = normalize_expected_text(text)
    if not normalized:
        raise BenchmarkError("expected text must be non-empty")
    return normalized


def expected_match_score(actual_text: str, expected_text: str) -> float:
    """Return a 0..1 similarity score after conservative normalization."""

    actual = normalize_expected_text(actual_text)
    expected = normalize_expected_text(expected_text)
    if not expected:
        return 0.0
    if not actual:
        return 0.0
    if actual == expected:
        return 1.0
    return max(0.0, min(1.0, SequenceMatcher(None, actual, expected).ratio()))


def compare_expected_text(
    actual_text: str,
    reference: ExpectedTextReference | None,
) -> ExpectedTextComparison:
    """Compare actual OCR text with expected text when a reference exists."""

    if reference is None:
        return ExpectedTextComparison(available=False, score=None, reason="expected_text_missing")
    expected_text = load_expected_text(reference)
    return ExpectedTextComparison(
        available=True,
        score=expected_match_score(actual_text, expected_text),
    )


__all__ = [
    "ExpectedTextComparison",
    "compare_expected_text",
    "expected_match_score",
    "load_expected_text",
    "normalize_expected_text",
]
