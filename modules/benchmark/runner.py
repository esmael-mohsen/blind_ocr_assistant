"""Benchmark runner orchestration for Phase 10."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import platform
import time
from typing import Any, Callable

from modules.benchmark.benchmark_models import (
    BenchmarkDataset,
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkRunStatus,
    BenchmarkSample,
    FailureCategory,
    OCRPath,
    ResultStatus,
    sanitize_metadata,
)
from modules.benchmark.expected_text import compare_expected_text
from modules.benchmark.result_writer import make_run_id, reserve_run_directory, write_run_outputs
from modules.benchmark.tuning import generate_tuning_recommendations
from modules.ocr.ocr_models import OCRErrorCode, OCRResult


OCRInvoker = Callable[[BenchmarkSample, str], Any]
QualityGate = Callable[[BenchmarkSample], Any]


DEFAULT_PATHS = (OCRPath.CASCADE.value,)
COMPARISON_PATHS = (
    OCRPath.OCR_SPACE.value,
    OCRPath.PADDLEOCR.value,
    OCRPath.TESSERACT.value,
    OCRPath.CASCADE.value,
)
LOCAL_PATHS = {OCRPath.PADDLEOCR.value, OCRPath.TESSERACT.value, OCRPath.CASCADE.value}
ONLINE_PATHS = {OCRPath.OCR_SPACE.value}


@dataclass
class BenchmarkRunner:
    """Run a manifest-defined benchmark through existing OCR boundaries."""

    dataset: BenchmarkDataset
    output_dir: Path = Path("benchmark_results")
    paths: tuple[str, ...] = DEFAULT_PATHS
    offline: bool = False
    debug_text: bool = False
    invokers: dict[str, OCRInvoker] = field(default_factory=dict)
    quality_gate: QualityGate | None = None

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.paths = resolve_requested_paths(self.paths, offline=self.offline)

    def run(self) -> tuple[BenchmarkRun, dict[str, Any]]:
        """Execute one benchmark run and write safe local outputs."""

        run_id = make_run_id()
        result_dir = reserve_run_directory(self.output_dir, run_id)
        run = BenchmarkRun(
            run_id=run_id,
            dataset_id=self.dataset.dataset_id,
            started_at=time_to_datetime(),
            requested_paths=self.paths,
            result_directory=result_dir,
            status=BenchmarkRunStatus.RUNNING,
            environment=safe_environment(self.paths, offline=self.offline),
        )
        results: list[BenchmarkResult] = []
        try:
            for sample in self.dataset.samples:
                results.extend(self._run_sample(run.run_id, sample))
            recommendations = generate_tuning_recommendations(run.run_id, results)
            summary = write_run_outputs(
                run,
                self.dataset,
                results,
                recommendations=recommendations,
            )
            status = (
                BenchmarkRunStatus.SUCCESS
                if all(result.status is ResultStatus.SUCCESS for result in results)
                else BenchmarkRunStatus.PARTIAL
            )
            run = run.transition(status)
            return run, summary
        except KeyboardInterrupt:
            write_run_outputs(run, self.dataset, results)
            raise
        except Exception:
            if results:
                write_run_outputs(run, self.dataset, results)
            raise

    def _run_sample(self, run_id: str, sample: BenchmarkSample) -> list[BenchmarkResult]:
        quality_result = self._quality_decision(sample)
        if quality_result is not None:
            return [
                BenchmarkResult.failure_result(
                    run_id=run_id,
                    sample=sample,
                    ocr_path=path,
                    duration_ms=0,
                    failure_category=FailureCategory.IMAGE_REJECTED,
                    safe_metadata={"quality_gate": "rejected"},
                )
                for path in self.paths
            ]
        return [self._run_path(run_id, sample, path) for path in self.paths]

    def _quality_decision(self, sample: BenchmarkSample) -> Any | None:
        if self.quality_gate is None:
            return None
        report = self.quality_gate(sample)
        if getattr(report, "is_acceptable", True):
            return None
        return report

    def _run_path(self, run_id: str, sample: BenchmarkSample, path: str) -> BenchmarkResult:
        if self.offline and path in ONLINE_PATHS:
            return BenchmarkResult.failure_result(
                run_id=run_id,
                sample=sample,
                ocr_path=path,
                duration_ms=0,
                failure_category=FailureCategory.ONLINE_DISABLED,
                status=ResultStatus.UNAVAILABLE,
                safe_metadata={"offline": True},
            )
        invoker = self.invokers.get(path)
        if invoker is None:
            category = (
                FailureCategory.ONLINE_UNAVAILABLE
                if path in ONLINE_PATHS
                else FailureCategory.ENGINE_UNAVAILABLE
            )
            return BenchmarkResult.failure_result(
                run_id=run_id,
                sample=sample,
                ocr_path=path,
                duration_ms=0,
                failure_category=category,
                status=ResultStatus.UNAVAILABLE,
                safe_metadata={"engine_available": False},
            )
        started = time.perf_counter()
        try:
            outcome = invoker(sample, path)
            duration_ms = _duration_ms(started, outcome)
            return benchmark_result_from_outcome(
                run_id=run_id,
                sample=sample,
                ocr_path=path,
                outcome=outcome,
                duration_ms=duration_ms,
                expected_reference=self.dataset.expected_texts.get(sample.expected_text_id or ""),
            )
        except TimeoutError:
            return BenchmarkResult.failure_result(
                run_id=run_id,
                sample=sample,
                ocr_path=path,
                duration_ms=_duration_ms(started),
                failure_category=FailureCategory.PATH_TIMEOUT,
                safe_metadata={"timeout": True},
            )
        except Exception as exc:
            return BenchmarkResult.failure_result(
                run_id=run_id,
                sample=sample,
                ocr_path=path,
                duration_ms=_duration_ms(started),
                failure_category=FailureCategory.UNEXPECTED_FAILURE,
                safe_metadata={"exception_type": type(exc).__name__},
            )


def resolve_requested_paths(paths: tuple[str, ...] | list[str] | str | None, *, offline: bool = False) -> tuple[str, ...]:
    """Resolve CLI path options into known existing OCR paths."""

    if paths is None:
        resolved = list(DEFAULT_PATHS)
    elif isinstance(paths, str):
        lowered = paths.lower().strip()
        resolved = list(COMPARISON_PATHS if lowered in {"all", "compare", "comparison"} else _split_paths(lowered))
    else:
        resolved = []
        for value in paths:
            resolved.extend(_split_paths(str(value)))
    normalized: list[str] = []
    for path in resolved:
        path = _normalize_path_name(path)
        if path not in normalized:
            normalized.append(path)
    if offline and OCRPath.OCR_SPACE.value in normalized:
        return tuple(normalized)
    return tuple(normalized or DEFAULT_PATHS)


def benchmark_result_from_outcome(
    *,
    run_id: str,
    sample: BenchmarkSample,
    ocr_path: str,
    outcome: Any,
    duration_ms: int,
    expected_reference: Any | None = None,
) -> BenchmarkResult:
    """Convert existing OCR/cascade/image-quality outcomes into benchmark records."""

    if isinstance(outcome, BenchmarkResult):
        return outcome
    if _is_cascade_result(outcome):
        return _cascade_to_result(run_id, sample, ocr_path, outcome, expected_reference, duration_ms)
    if isinstance(outcome, OCRResult):
        return _ocr_result_to_benchmark(run_id, sample, ocr_path, outcome, expected_reference, duration_ms)
    if isinstance(outcome, dict):
        return _dict_to_benchmark(run_id, sample, ocr_path, outcome, expected_reference, duration_ms)
    raw_text = str(getattr(outcome, "raw_text", "") or getattr(outcome, "text", "") or "")
    success = bool(getattr(outcome, "success", bool(raw_text.strip())))
    if success:
        return _success_from_text(
            run_id,
            sample,
            ocr_path,
            raw_text,
            duration_ms,
            quality_score=getattr(outcome, "quality_score", None),
            fallback_used=bool(getattr(outcome, "fallback_used", False)),
            expected_reference=expected_reference,
            safe_metadata=sanitize_metadata(getattr(outcome, "safe_metadata", {})),
        )
    return BenchmarkResult.failure_result(
        run_id=run_id,
        sample=sample,
        ocr_path=ocr_path,
        duration_ms=duration_ms,
        failure_category=FailureCategory.UNEXPECTED_FAILURE,
        safe_metadata={"outcome_type": type(outcome).__name__},
    )


def safe_environment(paths: tuple[str, ...], *, offline: bool) -> dict[str, Any]:
    """Return safe local environment metadata."""

    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "requested_paths": list(paths),
        "offline": offline,
    }


def time_to_datetime() -> Any:
    """Create a timestamp without importing assistant workflow code."""

    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def _split_paths(value: str) -> list[str]:
    return [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]


def _normalize_path_name(value: str) -> str:
    aliases = {
        "ocrspace": OCRPath.OCR_SPACE.value,
        "online": OCRPath.OCR_SPACE.value,
        "paddle": OCRPath.PADDLEOCR.value,
        "local": OCRPath.PADDLEOCR.value,
        "emergency": OCRPath.TESSERACT.value,
    }
    normalized = aliases.get(value.lower().strip(), value.lower().strip())
    allowed = {path.value for path in OCRPath}
    if normalized not in allowed:
        raise ValueError(f"unsupported OCR benchmark path: {value}")
    return normalized


def _duration_ms(started: float, outcome: Any | None = None) -> int:
    duration = getattr(outcome, "duration_ms", None)
    if isinstance(outcome, dict):
        duration = outcome.get("duration_ms", duration)
    if duration is not None:
        return max(0, int(duration))
    return max(0, int((time.perf_counter() - started) * 1000))


def _is_cascade_result(outcome: Any) -> bool:
    return hasattr(outcome, "selected_engine") and hasattr(outcome, "selected_result")


def _cascade_to_result(
    run_id: str,
    sample: BenchmarkSample,
    ocr_path: str,
    outcome: Any,
    expected_reference: Any | None,
    duration_ms: int,
) -> BenchmarkResult:
    if getattr(outcome, "success", False) and getattr(outcome, "selected_result", None) is not None:
        selected = outcome.selected_result
        quality_report = getattr(outcome, "quality_report", None)
        return _success_from_text(
            run_id,
            sample,
            ocr_path,
            selected.raw_text,
            duration_ms,
            quality_score=getattr(quality_report, "quality_score", selected.quality_score),
            fallback_used=bool(getattr(outcome, "fallback_used", False)),
            expected_reference=expected_reference,
            safe_metadata=getattr(outcome, "safe_metadata", {}),
        )
    error = getattr(outcome, "error", None)
    return BenchmarkResult.failure_result(
        run_id=run_id,
        sample=sample,
        ocr_path=ocr_path,
        duration_ms=duration_ms,
        failure_category=map_failure_category(getattr(error, "error_code", None)),
        safe_metadata=getattr(outcome, "safe_metadata", {}),
    )


def _ocr_result_to_benchmark(
    run_id: str,
    sample: BenchmarkSample,
    ocr_path: str,
    result: OCRResult,
    expected_reference: Any | None,
    duration_ms: int,
) -> BenchmarkResult:
    if result.success:
        return _success_from_text(
            run_id,
            sample,
            ocr_path,
            result.raw_text,
            duration_ms,
            quality_score=result.quality_score,
            fallback_used=result.fallback_used,
            expected_reference=expected_reference,
            safe_metadata=result.metadata,
        )
    return BenchmarkResult.failure_result(
        run_id=run_id,
        sample=sample,
        ocr_path=ocr_path,
        duration_ms=duration_ms,
        failure_category=map_failure_category(result.error_code),
        safe_metadata=result.metadata,
    )


def _dict_to_benchmark(
    run_id: str,
    sample: BenchmarkSample,
    ocr_path: str,
    outcome: dict[str, Any],
    expected_reference: Any | None,
    duration_ms: int,
) -> BenchmarkResult:
    raw_text = str(outcome.get("raw_text") or outcome.get("text") or "")
    success = bool(outcome.get("success", bool(raw_text.strip())))
    if success:
        return _success_from_text(
            run_id,
            sample,
            ocr_path,
            raw_text,
            duration_ms,
            quality_score=outcome.get("quality_score"),
            fallback_used=bool(outcome.get("fallback_used", False)),
            expected_reference=expected_reference,
            safe_metadata=outcome.get("metadata", {}),
        )
    return BenchmarkResult.failure_result(
        run_id=run_id,
        sample=sample,
        ocr_path=ocr_path,
        duration_ms=duration_ms,
        failure_category=map_failure_category(outcome.get("error_code")),
        status=ResultStatus.UNAVAILABLE if outcome.get("unavailable") else ResultStatus.FAILED,
        safe_metadata=outcome.get("metadata", {}),
    )


def _success_from_text(
    run_id: str,
    sample: BenchmarkSample,
    ocr_path: str,
    raw_text: str,
    duration_ms: int,
    *,
    quality_score: float | None,
    fallback_used: bool,
    expected_reference: Any | None,
    safe_metadata: dict[str, Any],
) -> BenchmarkResult:
    comparison = compare_expected_text(raw_text, expected_reference)
    if not raw_text.strip():
        return BenchmarkResult.failure_result(
            run_id=run_id,
            sample=sample,
            ocr_path=ocr_path,
            duration_ms=duration_ms,
            failure_category=FailureCategory.NO_TEXT_DETECTED,
            safe_metadata=safe_metadata,
        )
    return BenchmarkResult.success_result(
        run_id=run_id,
        sample=sample,
        ocr_path=ocr_path,
        duration_ms=duration_ms,
        text_length=len(raw_text),
        quality_score=quality_score,
        expected_match_score=comparison.score,
        fallback_used=fallback_used,
        safe_metadata=safe_metadata,
    )


def map_failure_category(error_code: Any) -> FailureCategory:
    """Map OCR/cascade exceptions and codes to benchmark categories."""

    value = getattr(error_code, "value", str(error_code or "")).lower()
    if "timeout" in value:
        return FailureCategory.PATH_TIMEOUT
    if "online" in value:
        return FailureCategory.ONLINE_UNAVAILABLE
    if "local" in value or "model_load" in value or "executable" in value or "language_data" in value:
        return FailureCategory.LOCAL_UNAVAILABLE
    if "no_text" in value:
        return FailureCategory.NO_TEXT_DETECTED
    if "weak" in value:
        return FailureCategory.WEAK_OCR_RESULT
    if "image_not_ready" in value:
        return FailureCategory.IMAGE_REJECTED
    if error_code is OCRErrorCode.OCR_MISSING_CREDENTIAL:
        return FailureCategory.ONLINE_UNAVAILABLE
    return FailureCategory.UNEXPECTED_FAILURE


__all__ = [
    "BenchmarkRunner",
    "benchmark_result_from_outcome",
    "map_failure_category",
    "resolve_requested_paths",
    "safe_environment",
]
