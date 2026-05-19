"""Privacy-safe benchmark data models for Phase 10."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any


MINIMUM_SAMPLE_COUNT = 12
REQUIRED_LABELS = frozenset(
    {
        "ar",
        "en",
        "mixed",
        "book_page",
        "printed_document",
        "medicine_package",
        "receipt",
        "sign",
        "low_light",
        "angled_image",
        "far_image",
        "blurry_image",
    }
)
NORMAL_QUALITY_LABELS = frozenset({"normal", "normal_quality"})
DIFFICULT_QUALITY_LABELS = frozenset({"low_light", "angled", "far", "blurry"})
SENSITIVE_KEYS = frozenset(
    {
        "artifact_path",
        "clean_text",
        "debug_path",
        "endpoint",
        "image",
        "image_bytes",
        "image_path",
        "image_payload",
        "ocr_text",
        "password",
        "private_path",
        "raw_text",
        "secret",
        "text",
        "token",
        "translated_text",
        "uploaded_payload",
    }
)


class BenchmarkError(ValueError):
    """Expected benchmark configuration or validation failure."""


class LanguageLabel(StrEnum):
    """Supported coarse language labels for benchmark samples."""

    ARABIC = "ar"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PrivacyClassification(StrEnum):
    """Privacy classification for benchmark fixtures."""

    SAFE_FIXTURE = "safe_fixture"
    MANUAL_PRIVATE = "manual_private"
    DEBUG_ONLY = "debug_only"


class BenchmarkRunStatus(StrEnum):
    """Lifecycle states for one benchmark run."""

    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class ResultStatus(StrEnum):
    """Per-sample benchmark outcome status."""

    SUCCESS = "success"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class OCRPath(StrEnum):
    """Existing OCR paths that Phase 10 may measure."""

    OCR_SPACE = "ocr_space"
    PADDLEOCR = "paddleocr"
    TESSERACT = "tesseract"
    CASCADE = "cascade"


class FailureCategory(StrEnum):
    """Stable benchmark failure categories."""

    DATASET_MISSING = "dataset_missing"
    MANIFEST_INVALID = "manifest_invalid"
    SAMPLE_MISSING = "sample_missing"
    EXPECTED_TEXT_MISSING = "expected_text_missing"
    UNSUPPORTED_IMAGE_FILE = "unsupported_image_file"
    IMAGE_REJECTED = "image_rejected"
    ONLINE_DISABLED = "online_disabled"
    ONLINE_UNAVAILABLE = "online_unavailable"
    LOCAL_UNAVAILABLE = "local_unavailable"
    PATH_TIMEOUT = "path_timeout"
    WEAK_OCR_RESULT = "weak_ocr_result"
    NO_TEXT_DETECTED = "no_text_detected"
    ENGINE_UNAVAILABLE = "engine_unavailable"
    UNEXPECTED_FAILURE = "unexpected_benchmark_failure"
    INTERRUPTED = "interrupted_benchmark_run"


class TuningTargetArea(StrEnum):
    """Benchmark tuning areas that can receive recommendations."""

    IMAGE_QUALITY = "image_quality"
    OCR_QUALITY = "ocr_quality"
    PREPROCESSING = "preprocessing"
    FRAME_SELECTION = "frame_selection"


class RecommendationState(StrEnum):
    """Recommendation acceptance lifecycle."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


def now_utc() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(timezone.utc)


def sanitize_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return metadata safe for default benchmark outputs."""

    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        lowered = key.lower()
        if lowered in SENSITIVE_KEYS or any(token in lowered for token in ("secret", "token", "password")):
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        if isinstance(value, Path):
            continue
        if isinstance(value, StrEnum):
            safe[key] = value.value
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple)):
            safe[key] = [item.value if isinstance(item, StrEnum) else item for item in value]
        elif isinstance(value, dict):
            nested = sanitize_metadata(value)
            if nested:
                safe[key] = nested
    return safe


def _validate_score(value: float | None, field_name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise BenchmarkError(f"{field_name} must be between 0.0 and 1.0")


def _non_empty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise BenchmarkError(f"{field_name} is required")


@dataclass(frozen=True)
class ExpectedTextReference:
    """Safe expected text reference for selected benchmark samples."""

    expected_text_id: str
    text_path: Path
    language_label: LanguageLabel = LanguageLabel.UNKNOWN
    normalization_policy: str = "preserve_meaning"
    privacy_classification: PrivacyClassification = PrivacyClassification.SAFE_FIXTURE

    def __post_init__(self) -> None:
        _non_empty(self.expected_text_id, "expected_text_id")
        object.__setattr__(self, "text_path", Path(self.text_path))
        if not self.normalization_policy.strip():
            raise BenchmarkError("normalization_policy is required")
        if self.privacy_classification is not PrivacyClassification.SAFE_FIXTURE:
            raise BenchmarkError("expected text references must be safe fixtures")


@dataclass(frozen=True)
class BenchmarkSample:
    """One benchmark image or safe controlled fixture."""

    sample_id: str
    image_path: Path
    scenario_labels: tuple[str, ...]
    language_label: LanguageLabel
    quality_label: str
    expected_text_id: str | None = None
    privacy_classification: PrivacyClassification = PrivacyClassification.SAFE_FIXTURE
    notes: str | None = None

    def __post_init__(self) -> None:
        _non_empty(self.sample_id, "sample_id")
        object.__setattr__(self, "image_path", Path(self.image_path))
        labels = tuple(label.strip() for label in self.scenario_labels if label.strip())
        if not labels:
            raise BenchmarkError("scenario_labels are required")
        object.__setattr__(self, "scenario_labels", labels)
        _non_empty(self.quality_label, "quality_label")

    @property
    def coverage_labels(self) -> set[str]:
        """Return labels used for dataset coverage checks."""

        labels = set(self.scenario_labels)
        labels.add(self.language_label.value)
        labels.add(self.quality_label)
        return labels

    @property
    def is_normal_language_sample(self) -> bool:
        """Return whether exact expected text is mandatory."""

        return (
            self.language_label
            in {LanguageLabel.ARABIC, LanguageLabel.ENGLISH, LanguageLabel.MIXED}
            and self.quality_label in NORMAL_QUALITY_LABELS
        )

    @property
    def is_difficult_sample(self) -> bool:
        """Return whether this sample belongs to a difficult capture scenario."""

        return self.quality_label in DIFFICULT_QUALITY_LABELS or bool(
            DIFFICULT_QUALITY_LABELS.intersection(self.scenario_labels)
        )


@dataclass(frozen=True)
class BenchmarkDataset:
    """One manifest-defined benchmark dataset."""

    dataset_id: str
    manifest_path: Path
    samples: tuple[BenchmarkSample, ...]
    expected_texts: dict[str, ExpectedTextReference] = field(default_factory=dict)
    minimum_sample_count: int = MINIMUM_SAMPLE_COUNT
    created_for_phase: str = "phase10"

    def __post_init__(self) -> None:
        _non_empty(self.dataset_id, "dataset_id")
        object.__setattr__(self, "manifest_path", Path(self.manifest_path))
        object.__setattr__(self, "samples", tuple(self.samples))
        if self.minimum_sample_count < 1:
            raise BenchmarkError("minimum_sample_count must be positive")
        validate_dataset(self)


@dataclass(frozen=True)
class BenchmarkResult:
    """One benchmark measurement for one sample and one OCR path."""

    run_id: str
    sample_id: str
    ocr_path: str
    scenario_labels: tuple[str, ...]
    language_label: LanguageLabel
    status: ResultStatus
    success: bool
    duration_ms: int
    text_length: int = 0
    quality_score: float | None = None
    expected_match_score: float | None = None
    fallback_used: bool = False
    failure_category: FailureCategory | None = None
    safe_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _non_empty(self.run_id, "run_id")
        _non_empty(self.sample_id, "sample_id")
        _non_empty(self.ocr_path, "ocr_path")
        if self.duration_ms < 0:
            raise BenchmarkError("duration_ms must be non-negative")
        if self.text_length < 0:
            raise BenchmarkError("text_length must be non-negative")
        _validate_score(self.quality_score, "quality_score")
        _validate_score(self.expected_match_score, "expected_match_score")
        if self.status is ResultStatus.SUCCESS and not self.success:
            raise BenchmarkError("success status requires success=True")
        if self.status is not ResultStatus.SUCCESS and self.failure_category is None:
            raise BenchmarkError("failed or unavailable results require failure_category")
        object.__setattr__(self, "scenario_labels", tuple(self.scenario_labels))
        metadata = {
            "sample_id": self.sample_id,
            "ocr_path": self.ocr_path,
            **sanitize_metadata(self.safe_metadata),
        }
        if self.failure_category is not None:
            metadata["failure_category"] = self.failure_category.value
        object.__setattr__(self, "safe_metadata", metadata)

    @classmethod
    def success_result(
        cls,
        *,
        run_id: str,
        sample: BenchmarkSample,
        ocr_path: str,
        duration_ms: int,
        text_length: int,
        quality_score: float | None = None,
        expected_match_score: float | None = None,
        fallback_used: bool = False,
        safe_metadata: dict[str, Any] | None = None,
    ) -> "BenchmarkResult":
        return cls(
            run_id=run_id,
            sample_id=sample.sample_id,
            ocr_path=ocr_path,
            scenario_labels=sample.scenario_labels,
            language_label=sample.language_label,
            status=ResultStatus.SUCCESS,
            success=True,
            duration_ms=duration_ms,
            text_length=text_length,
            quality_score=quality_score,
            expected_match_score=expected_match_score,
            fallback_used=fallback_used,
            safe_metadata=safe_metadata or {},
        )

    @classmethod
    def failure_result(
        cls,
        *,
        run_id: str,
        sample: BenchmarkSample,
        ocr_path: str,
        duration_ms: int,
        failure_category: FailureCategory,
        status: ResultStatus = ResultStatus.FAILED,
        quality_score: float | None = None,
        expected_match_score: float | None = None,
        safe_metadata: dict[str, Any] | None = None,
    ) -> "BenchmarkResult":
        return cls(
            run_id=run_id,
            sample_id=sample.sample_id,
            ocr_path=ocr_path,
            scenario_labels=sample.scenario_labels,
            language_label=sample.language_label,
            status=status,
            success=False,
            duration_ms=duration_ms,
            quality_score=quality_score,
            expected_match_score=expected_match_score,
            failure_category=failure_category,
            safe_metadata=safe_metadata or {},
        )


@dataclass(frozen=True)
class TuningRecommendation:
    """Evidence-based tuning recommendation that is not applied automatically."""

    recommendation_id: str
    run_id: str
    target_area: TuningTargetArea
    affected_scenarios: tuple[str, ...]
    evidence_summary: str
    expected_benefit: str
    regression_risk: str
    current_value: float | str | None = None
    proposed_value: float | str | None = None
    accepted: bool = False
    state: RecommendationState = RecommendationState.PROPOSED
    evidence_result_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "run_id",
            "evidence_summary",
            "expected_benefit",
            "regression_risk",
        ):
            _non_empty(str(getattr(self, field_name)), field_name)
        object.__setattr__(self, "affected_scenarios", tuple(sorted(set(self.affected_scenarios))))
        if self.accepted and self.state is not RecommendationState.ACCEPTED:
            object.__setattr__(self, "state", RecommendationState.ACCEPTED)


@dataclass(frozen=True)
class KnownFailureCase:
    """Privacy-safe known OCR failure case derived from benchmark results."""

    failure_id: str
    sample_id: str
    scenario_labels: tuple[str, ...]
    failure_category: FailureCategory
    likely_cause: str
    user_impact: str
    recommended_follow_up: str

    def __post_init__(self) -> None:
        for field_name in (
            "failure_id",
            "sample_id",
            "likely_cause",
            "user_impact",
            "recommended_follow_up",
        ):
            _non_empty(str(getattr(self, field_name)), field_name)
        object.__setattr__(self, "scenario_labels", tuple(sorted(set(self.scenario_labels))))


@dataclass(frozen=True)
class BenchmarkRun:
    """One timestamped benchmark execution."""

    run_id: str
    dataset_id: str
    started_at: datetime
    requested_paths: tuple[str, ...]
    result_directory: Path
    status: BenchmarkRunStatus = BenchmarkRunStatus.CREATED
    completed_at: datetime | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    results: tuple[BenchmarkResult, ...] = ()
    tuning_recommendations: tuple[TuningRecommendation, ...] = ()
    known_failures: tuple[KnownFailureCase, ...] = ()

    def __post_init__(self) -> None:
        _non_empty(self.run_id, "run_id")
        _non_empty(self.dataset_id, "dataset_id")
        object.__setattr__(self, "requested_paths", tuple(self.requested_paths))
        object.__setattr__(self, "result_directory", Path(self.result_directory))
        object.__setattr__(self, "environment", sanitize_metadata(self.environment))

    def transition(self, status: BenchmarkRunStatus) -> "BenchmarkRun":
        """Return a copy moved to a valid lifecycle state."""

        valid = {
            BenchmarkRunStatus.CREATED: {
                BenchmarkRunStatus.RUNNING,
                BenchmarkRunStatus.FAILED,
            },
            BenchmarkRunStatus.RUNNING: {
                BenchmarkRunStatus.SUCCESS,
                BenchmarkRunStatus.PARTIAL,
                BenchmarkRunStatus.FAILED,
                BenchmarkRunStatus.INTERRUPTED,
            },
            BenchmarkRunStatus.SUCCESS: set(),
            BenchmarkRunStatus.PARTIAL: set(),
            BenchmarkRunStatus.FAILED: set(),
            BenchmarkRunStatus.INTERRUPTED: set(),
        }
        if status not in valid[self.status]:
            raise BenchmarkError(f"invalid run transition {self.status.value}->{status.value}")
        completed = now_utc() if status not in {BenchmarkRunStatus.CREATED, BenchmarkRunStatus.RUNNING} else None
        return replace(self, status=status, completed_at=completed)


def validate_dataset(dataset: BenchmarkDataset) -> None:
    """Validate sample count, uniqueness, coverage, and expected text policy."""

    if len(dataset.samples) < dataset.minimum_sample_count:
        raise BenchmarkError("benchmark dataset must contain at least 12 samples")

    sample_ids = [sample.sample_id for sample in dataset.samples]
    if len(set(sample_ids)) != len(sample_ids):
        raise BenchmarkError("benchmark sample IDs must be unique")

    labels: set[str] = set()
    for sample in dataset.samples:
        labels.update(sample.coverage_labels)
    missing = REQUIRED_LABELS.difference(labels)
    if missing:
        raise BenchmarkError(f"benchmark dataset missing required labels: {sorted(missing)}")

    for sample in dataset.samples:
        if sample.privacy_classification not in set(PrivacyClassification):
            raise BenchmarkError("unsupported privacy classification")
        if sample.is_normal_language_sample and not sample.expected_text_id:
            raise BenchmarkError("normal Arabic, English, and mixed samples require expected text")
        if sample.expected_text_id and sample.expected_text_id not in dataset.expected_texts:
            raise BenchmarkError(f"sample references unknown expected text: {sample.expected_text_id}")

    difficult = [sample for sample in dataset.samples if sample.is_difficult_sample]
    difficult_with_expected = [sample for sample in difficult if sample.expected_text_id]
    if difficult and len(difficult_with_expected) / len(difficult) < 0.5:
        raise BenchmarkError("expected text must cover at least half of difficult samples")


__all__ = [
    "BenchmarkDataset",
    "BenchmarkError",
    "BenchmarkResult",
    "BenchmarkRun",
    "BenchmarkRunStatus",
    "BenchmarkSample",
    "ExpectedTextReference",
    "FailureCategory",
    "KnownFailureCase",
    "LanguageLabel",
    "OCRPath",
    "PrivacyClassification",
    "RecommendationState",
    "REQUIRED_LABELS",
    "ResultStatus",
    "TuningRecommendation",
    "TuningTargetArea",
    "sanitize_metadata",
    "validate_dataset",
]
