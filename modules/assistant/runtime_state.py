"""Runtime state snapshots for the event-driven assistant."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from time import monotonic


class RuntimeSystemMode(str, Enum):
    """User-visible runtime mode."""

    LISTENING = "LISTENING"
    SEARCHING_TEXT = "SEARCHING_TEXT"
    READY_TO_CAPTURE = "READY_TO_CAPTURE"
    CAPTURING = "CAPTURING"
    OCR_RUNNING = "OCR_RUNNING"
    READING = "READING"
    TRANSLATING = "TRANSLATING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


class RuntimeJobType(str, Enum):
    """Background job categories."""

    OCR = "ocr"
    TRANSLATION = "translation"
    TTS = "tts"


class RuntimeJobStatus(str, Enum):
    """Background job lifecycle state."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class FrameReadiness:
    """Latest cheap frame-analysis result used before OCR."""

    has_text: bool = False
    text_confidence: float = 0.0
    stable_frames: int = 0
    centered: bool = True
    position_hint: str = "unknown"
    horizontal_offset: float = 0.0
    vertical_offset: float = 0.0
    size_hint: str = "unknown"
    brightness_ok: bool = False
    blur_ok: bool = False
    ready_to_capture: bool = False
    guidance_code: str = "warming_up"
    guidance: str = "Point the camera toward printed text."
    quality_summary: str = "quality not checked"


@dataclass(frozen=True)
class RuntimeJob:
    """Privacy-safe status for one background operation."""

    job_id: str
    job_type: RuntimeJobType
    status: RuntimeJobStatus
    progress_label: str
    provider_attempts: tuple[str, ...] = ()
    started_at: float = field(default_factory=monotonic)
    finished_at: float | None = None
    error: str = ""

    def with_updates(self, **updates: object) -> "RuntimeJob":
        return replace(self, **updates)


@dataclass(frozen=True)
class RuntimeStateSnapshot:
    """Immutable-ish snapshot consumed by GUI, voice guidance, and tests."""

    mode: RuntimeSystemMode = RuntimeSystemMode.LISTENING
    active_job: RuntimeJob | None = None
    latest_frame_readiness: FrameReadiness = field(default_factory=FrameReadiness)
    latest_guidance: str = "Say read text when you are ready."
    latest_result_summary: str = ""
    provider_attempts: tuple[str, ...] = ()
    error: str = ""
    quiet_mode: bool = False
    verbose_mode: bool = False

    def with_updates(self, **updates: object) -> "RuntimeStateSnapshot":
        return replace(self, **updates)


__all__ = [
    "FrameReadiness",
    "RuntimeJob",
    "RuntimeJobStatus",
    "RuntimeJobType",
    "RuntimeStateSnapshot",
    "RuntimeSystemMode",
]
