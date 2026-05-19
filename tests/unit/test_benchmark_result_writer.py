"""Benchmark result writer tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.benchmark.benchmark_models import (
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkRunStatus,
    FailureCategory,
    LanguageLabel,
    ResultStatus,
)
from modules.benchmark.dataset_loader import load_benchmark_dataset
from modules.benchmark.result_writer import (
    best_paths_by_scenario,
    build_summary,
    extract_known_failures,
    make_run_id,
    reserve_run_directory,
    write_known_failures,
    write_run_outputs,
)


def _dataset():
    return load_benchmark_dataset("tests/benchmark/manifest.json")


def _run(tmp_path: Path) -> BenchmarkRun:
    return BenchmarkRun(
        run_id=make_run_id(),
        dataset_id="phase10-controlled",
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        requested_paths=("cascade",),
        result_directory=tmp_path / "run",
        status=BenchmarkRunStatus.RUNNING,
    )


def test_timestamped_run_directories_do_not_overwrite(tmp_path: Path) -> None:
    run_id = "20260519-010203-phase10"
    first = reserve_run_directory(tmp_path, run_id)

    assert first.exists()
    with pytest.raises(Exception, match="already exists"):
        reserve_run_directory(tmp_path, run_id)


def test_write_run_outputs_shapes_summary_and_known_failures(tmp_path: Path) -> None:
    dataset = _dataset()
    sample = dataset.samples[0]
    results = [
        BenchmarkResult.success_result(
            run_id="run",
            sample=sample,
            ocr_path="cascade",
            duration_ms=5,
            text_length=30,
            quality_score=0.9,
            expected_match_score=0.8,
        ),
        BenchmarkResult.failure_result(
            run_id="run",
            sample=dataset.samples[1],
            ocr_path="paddleocr",
            duration_ms=2,
            failure_category=FailureCategory.WEAK_OCR_RESULT,
        ),
    ]
    run = _run(tmp_path)

    summary = write_run_outputs(run, dataset, results)

    assert (run.result_directory / "results.json").exists()
    assert (run.result_directory / "summary.json").exists()
    assert (run.result_directory / "known_failures.md").exists()
    assert summary["result_count"] == 2
    payload = json.loads((run.result_directory / "results.json").read_text(encoding="utf-8"))
    assert "raw_text" not in json.dumps(payload)


def test_best_path_selection_prefers_match_quality_success_then_duration(tmp_path: Path) -> None:
    dataset = _dataset()
    sample = dataset.samples[0]
    fast = BenchmarkResult.success_result(
        run_id="run",
        sample=sample,
        ocr_path="tesseract",
        duration_ms=3,
        text_length=10,
        quality_score=0.8,
        expected_match_score=0.7,
    )
    accurate = BenchmarkResult.success_result(
        run_id="run",
        sample=sample,
        ocr_path="paddleocr",
        duration_ms=20,
        text_length=10,
        quality_score=0.9,
        expected_match_score=0.95,
    )

    assert best_paths_by_scenario([fast, accurate])["book_page"] == "paddleocr"


def test_known_failure_generation_covers_required_categories(tmp_path: Path) -> None:
    dataset = _dataset()
    categories = [
        FailureCategory.IMAGE_REJECTED,
        FailureCategory.WEAK_OCR_RESULT,
        FailureCategory.NO_TEXT_DETECTED,
        FailureCategory.ENGINE_UNAVAILABLE,
        FailureCategory.PATH_TIMEOUT,
        FailureCategory.UNEXPECTED_FAILURE,
    ]
    results = [
        BenchmarkResult.failure_result(
            run_id="run",
            sample=dataset.samples[index],
            ocr_path="cascade",
            duration_ms=1,
            failure_category=category,
            status=ResultStatus.UNAVAILABLE
            if category is FailureCategory.ENGINE_UNAVAILABLE
            else ResultStatus.FAILED,
        )
        for index, category in enumerate(categories)
    ]
    failures = extract_known_failures(results)
    out = tmp_path / "known_failures.md"
    write_known_failures(out, failures)

    text = out.read_text(encoding="utf-8")
    assert len(failures) == len(categories)
    assert "raw_text" not in text
    assert "debug_path" not in text
    assert LanguageLabel.ENGLISH.value == "en"


def test_summary_contains_engine_counts_duration_quality_and_unavailable(tmp_path: Path) -> None:
    dataset = _dataset()
    result = BenchmarkResult.failure_result(
        run_id="run",
        sample=dataset.samples[0],
        ocr_path="ocr_space",
        duration_ms=4,
        failure_category=FailureCategory.ONLINE_UNAVAILABLE,
        status=ResultStatus.UNAVAILABLE,
    )
    summary = build_summary(run=_run(tmp_path), dataset=dataset, results=[result])

    assert summary["per_engine_success_counts"]["ocr_space"]["unavailable"] == 1
    assert summary["per_engine_duration_ms"]["ocr_space"]["count"] == 1.0
    assert summary["unavailable_path_counts"]["ocr_space"] == 1
