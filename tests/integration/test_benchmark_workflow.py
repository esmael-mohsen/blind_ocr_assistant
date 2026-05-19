"""Phase 10 benchmark workflow integration tests."""

from __future__ import annotations

import json
from pathlib import Path

from modules.benchmark.dataset_loader import load_benchmark_dataset
from modules.benchmark.runner import BenchmarkRunner
from modules.ocr.ocr_models import OCRResult


def _fixture_text(dataset, sample) -> str:
    reference = dataset.expected_texts.get(sample.expected_text_id or "")
    return reference.text_path.read_text(encoding="utf-8") if reference else "Readable synthetic fallback text."


def test_full_mocked_benchmark_run_writes_timestamped_outputs(tmp_path: Path) -> None:
    dataset = load_benchmark_dataset("tests/benchmark/manifest.json")

    def invoker(sample, path):
        return OCRResult.success_result(
            engine_name=path,
            raw_text=_fixture_text(dataset, sample),
            duration_ms=4,
            quality_score=0.9,
        )

    run, summary = BenchmarkRunner(
        dataset=dataset,
        output_dir=tmp_path,
        paths=("cascade",),
        invokers={"cascade": invoker},
    ).run()

    assert run.result_directory.parent == tmp_path
    assert summary["result_count"] == len(dataset.samples)
    assert (run.result_directory / "results.json").exists()
    assert (run.result_directory / "summary.json").exists()
    assert (run.result_directory / "known_failures.md").exists()


def test_multi_path_comparison_and_offline_mode(tmp_path: Path) -> None:
    dataset = load_benchmark_dataset("tests/benchmark/manifest.json")

    def invoker(sample, path):
        return OCRResult.success_result(
            engine_name=path,
            raw_text=_fixture_text(dataset, sample),
            duration_ms=2 if path == "paddleocr" else 10,
            quality_score=0.95 if path == "paddleocr" else 0.8,
        )

    run, summary = BenchmarkRunner(
        dataset=dataset,
        output_dir=tmp_path,
        paths=("ocr_space", "paddleocr", "tesseract", "cascade"),
        offline=True,
        invokers={"paddleocr": invoker, "tesseract": invoker, "cascade": invoker},
    ).run()
    results = json.loads((run.result_directory / "results.json").read_text(encoding="utf-8"))

    assert summary["result_count"] == len(dataset.samples) * 4
    assert summary["unavailable_path_counts"]["ocr_space"] == len(dataset.samples)
    assert any(item["ocr_path"] == "paddleocr" for item in results["results"])


def test_benchmark_run_includes_tuning_recommendations_for_failures(tmp_path: Path) -> None:
    dataset = load_benchmark_dataset("tests/benchmark/manifest.json")

    def weak(sample, path):
        return OCRResult.failure_result(
            engine_name=path,
            error_code=__import__("modules.ocr.ocr_models", fromlist=["OCRErrorCode"]).OCRErrorCode.WEAK_OCR_RESULT,
            error_message="weak",
            duration_ms=1,
        )

    _, summary = BenchmarkRunner(
        dataset=dataset,
        output_dir=tmp_path,
        paths=("cascade",),
        invokers={"cascade": weak},
    ).run()

    assert summary["tuning_recommendations"]
    assert summary["tuning_recommendations"][0]["accepted"] is False
