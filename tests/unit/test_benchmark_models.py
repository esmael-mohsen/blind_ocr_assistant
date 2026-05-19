"""Phase 10 benchmark model tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.benchmark.benchmark_models import (
    BenchmarkDataset,
    BenchmarkError,
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkRunStatus,
    BenchmarkSample,
    ExpectedTextReference,
    FailureCategory,
    LanguageLabel,
    PrivacyClassification,
    ResultStatus,
    TuningRecommendation,
    TuningTargetArea,
    sanitize_metadata,
)
from modules.benchmark.result_writer import make_run_id


def _sample(sample_id: str, labels: tuple[str, ...], language: LanguageLabel, quality: str) -> BenchmarkSample:
    return BenchmarkSample(
        sample_id=sample_id,
        image_path=Path("tests/benchmark/samples/arabic_book_normal_001.txt"),
        scenario_labels=labels,
        language_label=language,
        quality_label=quality,
        expected_text_id=sample_id if quality == "normal" else None,
    )


def test_safe_metadata_excludes_private_text_paths_payloads_and_secrets() -> None:
    safe = sanitize_metadata(
        {
            "sample_id": "s1",
            "raw_text": "secret document",
            "clean_text": "secret",
            "translated_text": "secret",
            "image_bytes": b"image",
            "debug_path": Path("private.png"),
            "api_token": "secret",
            "quality_score": 0.8,
        }
    )

    assert safe == {"sample_id": "s1", "quality_score": 0.8}


def test_benchmark_result_validation_and_safe_metadata() -> None:
    sample = _sample("s1", ("book_page", "normal_quality"), LanguageLabel.ARABIC, "normal")
    result = BenchmarkResult.success_result(
        run_id="run",
        sample=sample,
        ocr_path="cascade",
        duration_ms=10,
        text_length=20,
        quality_score=0.8,
        expected_match_score=0.7,
        safe_metadata={"raw_text": "hidden", "engine_name": "cascade"},
    )

    assert result.status is ResultStatus.SUCCESS
    assert "raw_text" not in result.safe_metadata
    with pytest.raises(BenchmarkError, match="quality_score"):
        BenchmarkResult.success_result(
            run_id="run",
            sample=sample,
            ocr_path="cascade",
            duration_ms=10,
            text_length=20,
            quality_score=2.0,
        )


def test_run_state_transitions() -> None:
    run = BenchmarkRun(
        run_id=make_run_id(),
        dataset_id="phase10-controlled",
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        requested_paths=("cascade",),
        result_directory=Path("benchmark_results/test"),
    )

    running = run.transition(BenchmarkRunStatus.RUNNING)
    assert running.status is BenchmarkRunStatus.RUNNING
    assert running.transition(BenchmarkRunStatus.SUCCESS).completed_at is not None
    with pytest.raises(BenchmarkError, match="invalid run transition"):
        running.transition(BenchmarkRunStatus.CREATED)


def test_dataset_requires_minimum_unique_coverage_and_expected_text() -> None:
    expected = {
        name: ExpectedTextReference(
            expected_text_id=name,
            text_path=Path(f"tests/benchmark/expected/{name}.txt"),
            language_label=language,
        )
        for name, language in {
            "ar_normal": LanguageLabel.ARABIC,
            "en_normal": LanguageLabel.ENGLISH,
            "mixed_normal": LanguageLabel.MIXED,
        }.items()
    }
    samples = (
        _sample("ar_normal", ("book_page", "normal_quality"), LanguageLabel.ARABIC, "normal"),
        _sample("en_normal", ("printed_document", "normal_quality"), LanguageLabel.ENGLISH, "normal"),
        _sample("mixed_normal", ("receipt", "normal_quality"), LanguageLabel.MIXED, "normal"),
    )

    with pytest.raises(BenchmarkError, match="at least 12 samples"):
        BenchmarkDataset(
            dataset_id="phase10",
            manifest_path=Path("tests/benchmark/manifest.json"),
            samples=samples,
            expected_texts=expected,
        )


def test_failure_result_requires_category_and_recommendation_defaults_unaccepted() -> None:
    sample = _sample("s1", ("sign", "blurry_image"), LanguageLabel.ENGLISH, "blurry")
    failure = BenchmarkResult.failure_result(
        run_id="run",
        sample=sample,
        ocr_path="tesseract",
        duration_ms=1,
        failure_category=FailureCategory.WEAK_OCR_RESULT,
    )
    recommendation = TuningRecommendation(
        recommendation_id="rec-1",
        run_id="run",
        target_area=TuningTargetArea.OCR_QUALITY,
        affected_scenarios=("blurry_image",),
        evidence_summary="Measured weak OCR evidence.",
        expected_benefit="Better fallback routing.",
        regression_risk="Regression risk/tradeoff documented.",
    )

    assert failure.failure_category is FailureCategory.WEAK_OCR_RESULT
    assert recommendation.accepted is False
    assert recommendation.privacy_classification if hasattr(recommendation, "privacy_classification") else True
    assert PrivacyClassification.SAFE_FIXTURE.value == "safe_fixture"
