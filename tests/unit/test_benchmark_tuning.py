"""Benchmark tuning recommendation tests."""

from __future__ import annotations

from modules.benchmark.benchmark_models import (
    BenchmarkResult,
    FailureCategory,
    LanguageLabel,
    ResultStatus,
    TuningRecommendation,
    TuningTargetArea,
)
from modules.benchmark.dataset_loader import load_benchmark_dataset
from modules.benchmark.tuning import can_accept_recommendation, generate_tuning_recommendations


def _dataset():
    return load_benchmark_dataset("tests/benchmark/manifest.json")


def test_tuning_generates_recommendations_from_rejected_weak_and_failed_results() -> None:
    dataset = _dataset()
    results = [
        BenchmarkResult.failure_result(
            run_id="run",
            sample=dataset.samples[0],
            ocr_path="cascade",
            duration_ms=0,
            failure_category=FailureCategory.IMAGE_REJECTED,
        ),
        BenchmarkResult.failure_result(
            run_id="run",
            sample=dataset.samples[1],
            ocr_path="cascade",
            duration_ms=1,
            failure_category=FailureCategory.WEAK_OCR_RESULT,
        ),
        BenchmarkResult.failure_result(
            run_id="run",
            sample=dataset.samples[2],
            ocr_path="cascade",
            duration_ms=50,
            failure_category=FailureCategory.PATH_TIMEOUT,
        ),
    ]

    recommendations = generate_tuning_recommendations("run", results)

    assert {item.target_area for item in recommendations} == {
        TuningTargetArea.IMAGE_QUALITY,
        TuningTargetArea.OCR_QUALITY,
        TuningTargetArea.FRAME_SELECTION,
    }
    assert all(item.accepted is False for item in recommendations)
    assert all(item.evidence_result_ids for item in recommendations)


def test_tuning_acceptance_blocks_missing_evidence_tradeoffs_and_normal_regression() -> None:
    dataset = _dataset()
    baseline = [
        BenchmarkResult.success_result(
            run_id="run",
            sample=dataset.samples[0],
            ocr_path="cascade",
            duration_ms=1,
            text_length=10,
            expected_match_score=0.9,
        )
    ]
    candidate = [
        BenchmarkResult.success_result(
            run_id="run",
            sample=dataset.samples[0],
            ocr_path="cascade",
            duration_ms=1,
            text_length=10,
            expected_match_score=0.5,
        )
    ]
    rec = TuningRecommendation(
        recommendation_id="rec",
        run_id="run",
        target_area=TuningTargetArea.OCR_QUALITY,
        affected_scenarios=("normal_quality",),
        evidence_summary="Measured evidence.",
        expected_benefit="Benefit.",
        regression_risk="Regression risk/tradeoff documented.",
    )

    assert not can_accept_recommendation(rec, baseline, candidate)
    assert not can_accept_recommendation(
        TuningRecommendation(
            recommendation_id="rec2",
            run_id="run",
            target_area=TuningTargetArea.OCR_QUALITY,
            affected_scenarios=("normal_quality",),
            evidence_summary="Measured evidence.",
            expected_benefit="Benefit.",
            regression_risk="No detail.",
        ),
        baseline,
        baseline,
    )
    assert LanguageLabel.ARABIC.value == "ar"
    assert ResultStatus.SUCCESS.value == "success"
