"""Benchmark runner tests."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from modules.benchmark.benchmark_models import FailureCategory, ResultStatus
from modules.benchmark.dataset_loader import load_benchmark_dataset
from modules.benchmark.runner import BenchmarkRunner, map_failure_category, resolve_requested_paths
from modules.ocr.ocr_models import OCRErrorCode, OCRResult


def _dataset():
    return load_benchmark_dataset("tests/benchmark/manifest.json")


def test_cli_help_and_contract_flags_do_not_start_live_assistant() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_ocr.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--dataset" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--paths" in result.stdout
    assert "--offline" in result.stdout
    assert "--debug-text" in result.stdout
    assert "assistant" not in result.stderr.lower()


def test_runner_orchestrates_all_samples_with_mocked_success(tmp_path: Path) -> None:
    dataset = _dataset()

    def invoker(sample, path):
        expected = dataset.expected_texts.get(sample.expected_text_id or "")
        text = expected.text_path.read_text(encoding="utf-8") if expected else "Readable fallback text"
        return OCRResult.success_result(
            engine_name=path,
            raw_text=text,
            duration_ms=5,
            quality_score=0.9,
        )

    run, summary = BenchmarkRunner(
        dataset=dataset,
        output_dir=tmp_path,
        paths=("cascade",),
        invokers={"cascade": invoker},
    ).run()

    assert summary["result_count"] == len(dataset.samples)
    assert summary["status_counts"]["success"] == len(dataset.samples)
    assert (run.result_directory / "results.json").exists()


def test_runner_handles_weak_rejected_unavailable_and_offline_paths(tmp_path: Path) -> None:
    dataset = _dataset()

    def weak(sample, path):
        return OCRResult.failure_result(
            engine_name=path,
            error_code=OCRErrorCode.WEAK_OCR_RESULT,
            error_message="weak",
            duration_ms=3,
        )

    def reject(sample):
        if sample.sample_id == dataset.samples[0].sample_id:
            return SimpleNamespace(is_acceptable=False)
        return SimpleNamespace(is_acceptable=True)

    _, summary = BenchmarkRunner(
        dataset=dataset,
        output_dir=tmp_path,
        paths=("ocr_space", "paddleocr", "cascade"),
        offline=True,
        invokers={"paddleocr": weak, "cascade": weak},
        quality_gate=reject,
    ).run()

    assert summary["status_counts"]["failed"] >= 1
    assert summary["status_counts"]["unavailable"] >= len(dataset.samples) - 1
    assert summary["unavailable_path_counts"]["ocr_space"] >= len(dataset.samples) - 1


def test_path_resolution_and_failure_category_mapping() -> None:
    assert resolve_requested_paths("compare") == ("ocr_space", "paddleocr", "tesseract", "cascade")
    assert resolve_requested_paths("online,paddle") == ("ocr_space", "paddleocr")
    assert map_failure_category(OCRErrorCode.NO_TEXT_DETECTED) is FailureCategory.NO_TEXT_DETECTED
    assert map_failure_category(OCRErrorCode.OCR_PROVIDER_TIMEOUT) is FailureCategory.PATH_TIMEOUT
    assert map_failure_category(OCRErrorCode.OCR_MODEL_LOAD_ERROR) is FailureCategory.LOCAL_UNAVAILABLE


def test_runner_continues_through_timeout_and_unexpected_failure(tmp_path: Path) -> None:
    dataset = _dataset()

    def timeout(sample, path):
        raise TimeoutError("too slow")

    def unexpected(sample, path):
        raise RuntimeError("boom")

    _, summary = BenchmarkRunner(
        dataset=dataset,
        output_dir=tmp_path,
        paths=("paddleocr", "tesseract"),
        invokers={"paddleocr": timeout, "tesseract": unexpected},
    ).run()

    assert summary["result_count"] == len(dataset.samples) * 2
    assert ResultStatus.FAILED.value in summary["status_counts"]
