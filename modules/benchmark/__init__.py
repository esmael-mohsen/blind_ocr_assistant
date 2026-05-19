"""Benchmark package for Phase 10 OCR measurement and tuning."""

from modules.benchmark.benchmark_models import (
    BenchmarkDataset,
    BenchmarkError,
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkRunStatus,
    BenchmarkSample,
    ExpectedTextReference,
    FailureCategory,
    KnownFailureCase,
    LanguageLabel,
    OCRPath,
    PrivacyClassification,
    RecommendationState,
    ResultStatus,
    TuningRecommendation,
    TuningTargetArea,
    sanitize_metadata,
)
from modules.benchmark.dataset_loader import load_benchmark_dataset
from modules.benchmark.expected_text import (
    ExpectedTextComparison,
    compare_expected_text,
    expected_match_score,
    load_expected_text,
    normalize_expected_text,
)
from modules.benchmark.result_writer import (
    best_paths_by_scenario,
    build_summary,
    extract_known_failures,
    make_run_id,
    reserve_run_directory,
    write_run_outputs,
)
from modules.benchmark.runner import BenchmarkRunner, resolve_requested_paths
from modules.benchmark.tuning import can_accept_recommendation, generate_tuning_recommendations


__all__ = [
    "BenchmarkDataset",
    "BenchmarkError",
    "BenchmarkResult",
    "BenchmarkRun",
    "BenchmarkRunStatus",
    "BenchmarkRunner",
    "BenchmarkSample",
    "ExpectedTextComparison",
    "ExpectedTextReference",
    "FailureCategory",
    "KnownFailureCase",
    "LanguageLabel",
    "OCRPath",
    "PrivacyClassification",
    "RecommendationState",
    "ResultStatus",
    "TuningRecommendation",
    "TuningTargetArea",
    "best_paths_by_scenario",
    "build_summary",
    "can_accept_recommendation",
    "compare_expected_text",
    "expected_match_score",
    "extract_known_failures",
    "generate_tuning_recommendations",
    "load_benchmark_dataset",
    "load_expected_text",
    "make_run_id",
    "normalize_expected_text",
    "reserve_run_directory",
    "resolve_requested_paths",
    "sanitize_metadata",
    "write_run_outputs",
]
