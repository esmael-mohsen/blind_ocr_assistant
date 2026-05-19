"""Privacy tests for Phase 10 benchmark outputs."""

from __future__ import annotations

import json
from pathlib import Path

from modules.benchmark.benchmark_models import BenchmarkRun, BenchmarkRunStatus
from modules.benchmark.benchmark_models import (
    BenchmarkResult,
    FailureCategory,
    TuningRecommendation,
    TuningTargetArea,
    sanitize_metadata,
)
from modules.benchmark.dataset_loader import load_benchmark_dataset
from modules.benchmark.result_writer import make_run_id
from modules.benchmark.result_writer import recommendation_to_dict, result_to_dict, write_run_outputs


FORBIDDEN = [
    "raw secret text",
    "clean secret text",
    "translated secret text",
    "private image bytes",
    "image_bytes",
    "api_token",
    "debug_path",
]


def _run(tmp_path: Path) -> BenchmarkRun:
    return BenchmarkRun(
        run_id=make_run_id(),
        dataset_id="phase10-controlled",
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        requested_paths=("cascade",),
        result_directory=tmp_path / "run",
        status=BenchmarkRunStatus.RUNNING,
    )


def test_result_and_summary_outputs_exclude_private_text_payloads_and_secrets(tmp_path) -> None:
    dataset = load_benchmark_dataset("tests/benchmark/manifest.json")
    result = BenchmarkResult.failure_result(
        run_id="run",
        sample=dataset.samples[0],
        ocr_path="cascade",
        duration_ms=1,
        failure_category=FailureCategory.WEAK_OCR_RESULT,
        safe_metadata={
            "raw_text": "raw secret text",
            "clean_text": "clean secret text",
            "translated_text": "translated secret text",
            "image_payload": b"private image bytes",
            "api_token": "token",
            "engine_name": "cascade",
        },
    )
    run = _run(tmp_path)

    write_run_outputs(run, dataset, [result])
    output = "\n".join(
        [
            (run.result_directory / "results.json").read_text(encoding="utf-8"),
            (run.result_directory / "summary.json").read_text(encoding="utf-8"),
            (run.result_directory / "known_failures.md").read_text(encoding="utf-8"),
        ]
    )

    assert all(value not in output for value in FORBIDDEN)
    assert json.loads((run.result_directory / "summary.json").read_text(encoding="utf-8"))["privacy"][
        "contains_secrets"
    ] is False


def test_tuning_recommendations_are_serialized_without_private_fields() -> None:
    recommendation = TuningRecommendation(
        recommendation_id="rec",
        run_id="run",
        target_area=TuningTargetArea.OCR_QUALITY,
        affected_scenarios=("receipt",),
        evidence_summary="Measured evidence.",
        expected_benefit="Improves fallback.",
        regression_risk="Regression risk/tradeoff documented.",
    )

    payload = json.dumps(recommendation_to_dict(recommendation))
    assert "raw_text" not in payload
    assert "secret" not in payload
    assert sanitize_metadata({"raw_text": "hidden", "sample_id": "s1"}) == {"sample_id": "s1"}


def test_result_serialization_omits_raw_ocr_text() -> None:
    dataset = load_benchmark_dataset("tests/benchmark/manifest.json")
    result = BenchmarkResult.success_result(
        run_id="run",
        sample=dataset.samples[0],
        ocr_path="cascade",
        duration_ms=1,
        text_length=20,
        safe_metadata={"raw_text": "private content", "sample_id": "safe"},
    )

    payload = json.dumps(result_to_dict(result))
    assert "private content" not in payload
