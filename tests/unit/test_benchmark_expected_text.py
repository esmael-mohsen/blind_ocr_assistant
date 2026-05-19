"""Expected text normalization and scoring tests."""

from __future__ import annotations

from pathlib import Path

from modules.benchmark.benchmark_models import ExpectedTextReference, LanguageLabel
from modules.benchmark.expected_text import (
    compare_expected_text,
    expected_match_score,
    load_expected_text,
    normalize_expected_text,
)


def test_normalization_collapses_whitespace_and_preserves_meaningful_characters() -> None:
    text = "Receipt\n total   25.50 EGP رقم 123!"

    assert normalize_expected_text(text) == "Receipt total 25.50 EGP رقم 123!"


def test_match_score_bounds_for_arabic_english_mixed_and_missing_expected() -> None:
    assert expected_match_score("هذه جملة عربية", "هذه جملة عربية") == 1.0
    assert 0.0 <= expected_match_score("This invoice رقم 123", "This invoice رقم 124") <= 1.0
    assert expected_match_score("", "Expected text") == 0.0
    assert compare_expected_text("text", None).available is False


def test_load_expected_text_reads_non_empty_safe_fixture(tmp_path: Path) -> None:
    text_file = tmp_path / "expected.txt"
    text_file.write_text("Line one\nline two", encoding="utf-8")
    reference = ExpectedTextReference(
        expected_text_id="expected",
        text_path=text_file,
        language_label=LanguageLabel.ENGLISH,
    )

    assert load_expected_text(reference) == "Line one line two"
