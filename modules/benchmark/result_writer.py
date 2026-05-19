"""Timestamped privacy-safe benchmark result writing."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from modules.benchmark.benchmark_models import (
    BenchmarkDataset,
    BenchmarkError,
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkRunStatus,
    FailureCategory,
    KnownFailureCase,
    RecommendationState,
    ResultStatus,
    TuningRecommendation,
    sanitize_metadata,
)


def make_run_id(now: datetime | None = None) -> str:
    """Return a timestamped run ID."""

    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S-%f")
    return f"{stamp}-{uuid4().hex[:8]}-phase10"


def reserve_run_directory(output_dir: str | Path, run_id: str) -> Path:
    """Create a unique result directory without overwriting an older run."""

    root = Path(output_dir)
    target = root / run_id
    if target.exists():
        raise BenchmarkError(f"benchmark result directory already exists: {target}")
    target.mkdir(parents=True, exist_ok=False)
    return target


def write_run_outputs(
    run: BenchmarkRun,
    dataset: BenchmarkDataset,
    results: list[BenchmarkResult],
    *,
    recommendations: list[TuningRecommendation] | None = None,
) -> dict[str, Any]:
    """Write results.json, summary.json, and known_failures.md for one run."""

    run.result_directory.mkdir(parents=True, exist_ok=True)
    recommendations = recommendations or []
    known_failures = extract_known_failures(results)
    status = _aggregate_status(results)
    results_payload = {
        "run_id": run.run_id,
        "dataset_id": dataset.dataset_id,
        "status": status.value,
        "results": [result_to_dict(result) for result in results],
    }
    summary_payload = build_summary(
        run=run,
        dataset=dataset,
        results=results,
        recommendations=recommendations,
        known_failures=known_failures,
    )
    _write_json(run.result_directory / "results.json", results_payload)
    _write_json(run.result_directory / "summary.json", summary_payload)
    write_known_failures(run.result_directory / "known_failures.md", known_failures)
    return summary_payload


def build_summary(
    *,
    run: BenchmarkRun,
    dataset: BenchmarkDataset,
    results: list[BenchmarkResult],
    recommendations: list[TuningRecommendation] | None = None,
    known_failures: list[KnownFailureCase] | None = None,
) -> dict[str, Any]:
    """Build aggregate safe benchmark summary."""

    status_counts = Counter(result.status.value for result in results)
    engine_counts: dict[str, Counter[str]] = defaultdict(Counter)
    duration_by_engine: dict[str, list[int]] = defaultdict(list)
    quality_by_engine: dict[str, list[float]] = defaultdict(list)
    unavailable_by_engine: Counter[str] = Counter()
    scenario_counts: dict[str, Counter[str]] = defaultdict(Counter)
    language_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for result in results:
        engine_counts[result.ocr_path][result.status.value] += 1
        duration_by_engine[result.ocr_path].append(result.duration_ms)
        if result.quality_score is not None:
            quality_by_engine[result.ocr_path].append(result.quality_score)
        if result.status is ResultStatus.UNAVAILABLE:
            unavailable_by_engine[result.ocr_path] += 1
        for label in result.scenario_labels:
            scenario_counts[label][result.status.value] += 1
        language_counts[result.language_label.value][result.status.value] += 1

    return {
        "run_id": run.run_id,
        "dataset_id": dataset.dataset_id,
        "sample_count": len(dataset.samples),
        "result_count": len(results),
        "status": _aggregate_status(results).value,
        "status_counts": dict(status_counts),
        "scenario_counts": _counter_map_to_dict(scenario_counts),
        "language_counts": _counter_map_to_dict(language_counts),
        "per_engine_success_counts": _counter_map_to_dict(engine_counts),
        "per_engine_duration_ms": {
            engine: _number_summary(values) for engine, values in duration_by_engine.items()
        },
        "per_engine_quality": {
            engine: _number_summary(values) for engine, values in quality_by_engine.items()
        },
        "unavailable_path_counts": dict(unavailable_by_engine),
        "best_paths_by_scenario": best_paths_by_scenario(results),
        "tuning_recommendations": [
            recommendation_to_dict(recommendation) for recommendation in recommendations or []
        ],
        "known_failure_count": len(known_failures or []),
        "privacy": {
            "contains_raw_text": False,
            "contains_clean_text": False,
            "contains_translated_text": False,
            "contains_image_payloads": False,
            "contains_secrets": False,
        },
    }


def best_paths_by_scenario(results: list[BenchmarkResult]) -> dict[str, str]:
    """Select best OCR path by scenario using match, quality, success, duration."""

    by_scenario: dict[str, list[BenchmarkResult]] = defaultdict(list)
    for result in results:
        for label in result.scenario_labels:
            by_scenario[label].append(result)
    best: dict[str, str] = {}
    for label, scenario_results in by_scenario.items():
        winner = sorted(
            scenario_results,
            key=lambda item: (
                item.expected_match_score if item.expected_match_score is not None else -1.0,
                item.quality_score if item.quality_score is not None else -1.0,
                1 if item.success else 0,
                -item.duration_ms,
            ),
            reverse=True,
        )[0]
        best[label] = winner.ocr_path
    return best


def extract_known_failures(results: list[BenchmarkResult]) -> list[KnownFailureCase]:
    """Create grouped known failure cases from non-successful results."""

    failures: list[KnownFailureCase] = []
    for index, result in enumerate(
        [item for item in results if item.status is not ResultStatus.SUCCESS],
        start=1,
    ):
        category = result.failure_category or FailureCategory.UNEXPECTED_FAILURE
        failures.append(
            KnownFailureCase(
                failure_id=f"kf-{index:03d}",
                sample_id=result.sample_id,
                scenario_labels=result.scenario_labels,
                failure_category=category,
                likely_cause=_likely_cause(category),
                user_impact=_user_impact(category),
                recommended_follow_up=_recommended_follow_up(category),
            )
        )
    return failures


def write_known_failures(path: str | Path, failures: list[KnownFailureCase]) -> None:
    """Render grouped known failures without private OCR or image content."""

    lines = ["# Known OCR Failure Cases", ""]
    if not failures:
        lines.extend(["No known failures were recorded for this benchmark run.", ""])
    else:
        for failure in failures:
            lines.extend(
                [
                    f"## {failure.failure_id}: {failure.failure_category.value}",
                    "",
                    f"- Sample: {failure.sample_id}",
                    f"- Scenarios: {', '.join(failure.scenario_labels)}",
                    f"- Likely cause: {failure.likely_cause}",
                    f"- User impact: {failure.user_impact}",
                    f"- Recommended follow-up: {failure.recommended_follow_up}",
                    "",
                ]
            )
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def result_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    """Serialize one result without raw text or image content."""

    return {
        "sample_id": result.sample_id,
        "ocr_path": result.ocr_path,
        "scenario_labels": list(result.scenario_labels),
        "language_label": result.language_label.value,
        "success": result.success,
        "status": result.status.value,
        "duration_ms": result.duration_ms,
        "text_length": result.text_length,
        "quality_score": result.quality_score,
        "expected_match_score": result.expected_match_score,
        "fallback_used": result.fallback_used,
        "failure_category": result.failure_category.value if result.failure_category else None,
        "safe_metadata": sanitize_metadata(result.safe_metadata),
    }


def recommendation_to_dict(recommendation: TuningRecommendation) -> dict[str, Any]:
    """Serialize one recommendation safely."""

    payload = asdict(recommendation)
    payload["target_area"] = recommendation.target_area.value
    payload["state"] = (
        RecommendationState.ACCEPTED.value if recommendation.accepted else recommendation.state.value
    )
    payload["affected_scenarios"] = list(recommendation.affected_scenarios)
    payload["evidence_result_ids"] = list(recommendation.evidence_result_ids)
    return sanitize_metadata(payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _aggregate_status(results: list[BenchmarkResult]) -> BenchmarkRunStatus:
    if not results:
        return BenchmarkRunStatus.FAILED
    if all(result.status is ResultStatus.SUCCESS for result in results):
        return BenchmarkRunStatus.SUCCESS
    if any(result.status is ResultStatus.SUCCESS for result in results):
        return BenchmarkRunStatus.PARTIAL
    return BenchmarkRunStatus.PARTIAL


def _counter_map_to_dict(value: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: dict(counter) for key, counter in value.items()}


def _number_summary(values: list[int | float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "min": 0.0, "max": 0.0, "average": 0.0}
    return {
        "count": float(len(values)),
        "min": float(min(values)),
        "max": float(max(values)),
        "average": float(sum(values) / len(values)),
    }


def _likely_cause(category: FailureCategory) -> str:
    if category is FailureCategory.IMAGE_REJECTED:
        return "capture quality"
    if category in {FailureCategory.ONLINE_DISABLED, FailureCategory.ONLINE_UNAVAILABLE}:
        return "online OCR availability"
    if category in {FailureCategory.LOCAL_UNAVAILABLE, FailureCategory.ENGINE_UNAVAILABLE}:
        return "local OCR availability"
    if category is FailureCategory.PATH_TIMEOUT:
        return "OCR path timeout"
    if category in {FailureCategory.WEAK_OCR_RESULT, FailureCategory.NO_TEXT_DETECTED}:
        return "OCR quality"
    return "unknown"


def _user_impact(category: FailureCategory) -> str:
    if category is FailureCategory.IMAGE_REJECTED:
        return "The assistant would ask the user to recapture before reading."
    if category in {FailureCategory.WEAK_OCR_RESULT, FailureCategory.NO_TEXT_DETECTED}:
        return "The assistant may avoid reading unreliable or missing text."
    return "The assistant should continue to the next available OCR path."


def _recommended_follow_up(category: FailureCategory) -> str:
    if category is FailureCategory.IMAGE_REJECTED:
        return "Review image quality thresholds and capture guidance."
    if category is FailureCategory.WEAK_OCR_RESULT:
        return "Review preprocessing and OCR quality threshold evidence."
    if category is FailureCategory.NO_TEXT_DETECTED:
        return "Review text-region detection and OCR path routing."
    if category in {FailureCategory.ONLINE_DISABLED, FailureCategory.ONLINE_UNAVAILABLE}:
        return "Confirm online OCR configuration remains optional."
    if category in {FailureCategory.LOCAL_UNAVAILABLE, FailureCategory.ENGINE_UNAVAILABLE}:
        return "Confirm offline OCR dependency installation guidance."
    return "Inspect safe benchmark metadata and rerun the controlled fixture."


__all__ = [
    "best_paths_by_scenario",
    "build_summary",
    "extract_known_failures",
    "make_run_id",
    "recommendation_to_dict",
    "reserve_run_directory",
    "result_to_dict",
    "write_known_failures",
    "write_run_outputs",
]
