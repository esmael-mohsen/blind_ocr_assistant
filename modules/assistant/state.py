"""Assistant workflow state and result models for Phase 9."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import hashlib
from typing import Any


class WorkflowMode(str, Enum):
    """Current high-level workflow mode."""

    IDLE = "idle"
    LISTENING = "listening"
    CAPTURING = "capturing"
    SELECTING_FRAME = "selecting_frame"
    OCR = "ocr"
    CLEANING = "cleaning"
    READING = "reading"
    TRANSLATING = "translating"
    RECOVERING = "recovering"
    SHUTTING_DOWN = "shutting_down"


class WorkflowStatus(str, Enum):
    """Stable workflow result status."""

    SUCCESS = "success"
    FAILED = "failed"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    SHUTDOWN = "shutdown"


class SpokenStatusCategory(str, Enum):
    """Categories for user-facing spoken status."""

    CONFIRMATION = "confirmation"
    PROGRESS = "progress"
    FALLBACK = "fallback"
    SUCCESS = "success"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    RECOVERY = "recovery"
    SHUTDOWN = "shutdown"


class WorkflowErrorCode(str, Enum):
    """Stable Phase 9 workflow error categories."""

    WORKFLOW_BUSY = "WORKFLOW_BUSY"
    COMMAND_UNAVAILABLE = "COMMAND_UNAVAILABLE"
    CAMERA_UNAVAILABLE = "CAMERA_UNAVAILABLE"
    CAPTURE_TIMEOUT = "CAPTURE_TIMEOUT"
    NO_ACCEPTABLE_FRAME = "NO_ACCEPTABLE_FRAME"
    IMAGE_NOT_READY_FOR_OCR = "IMAGE_NOT_READY_FOR_OCR"
    OCR_FAILED = "OCR_FAILED"
    NO_TEXT_DETECTED = "NO_TEXT_DETECTED"
    CLEANUP_EMPTY_TEXT = "CLEANUP_EMPTY_TEXT"
    TRANSLATION_UNAVAILABLE = "TRANSLATION_UNAVAILABLE"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    TTS_UNAVAILABLE = "TTS_UNAVAILABLE"
    TTS_FAILED = "TTS_FAILED"
    COMPONENT_TIMEOUT = "COMPONENT_TIMEOUT"
    RESOURCE_RELEASE_FAILED = "RESOURCE_RELEASE_FAILED"
    WORKFLOW_UNEXPECTED_ERROR = "WORKFLOW_UNEXPECTED_ERROR"
    SHUTDOWN_REQUESTED = "SHUTDOWN_REQUESTED"


SENSITIVE_WORKFLOW_METADATA_KEYS = {
    "artifact_path",
    "clean_text",
    "command_phrase",
    "command_snippet",
    "command_transcript",
    "debug_path",
    "depth",
    "depth_map",
    "image",
    "image_array",
    "image_bytes",
    "ocr_text",
    "password",
    "raw_image",
    "raw_ocr_text",
    "raw_speech",
    "raw_text",
    "secret",
    "snippet",
    "source_text",
    "speech_input",
    "text",
    "token",
    "translated_text",
}


def _enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_enum_value(item) for item in value]
    if isinstance(value, list):
        return [_enum_value(item) for item in value]
    return value


def sanitize_workflow_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return workflow metadata safe for default logs."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_WORKFLOW_METADATA_KEYS:
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        safe[key] = _enum_value(value)
    return {key: value for key, value in safe.items() if value is not None}


def normalize_workflow_language(value: str | None) -> str:
    """Normalize workflow language labels."""
    raw_value = getattr(value, "value", value)
    normalized = str(raw_value or "unknown").strip().lower()
    aliases = {
        "ar": "ar",
        "ara": "ar",
        "arabic": "ar",
        "en": "en",
        "eng": "en",
        "english": "en",
        "mixed": "mixed",
        "unknown": "unknown",
        "": "unknown",
    }
    return aliases.get(normalized, "unknown")


def _request_id(intent: str, language_hint: str) -> str:
    digest = hashlib.sha256(f"{intent}:{language_hint}".encode("utf-8")).hexdigest()[:12]
    return f"workflow:{digest}"


@dataclass(frozen=True)
class WorkflowFailure:
    """Structured workflow failure with spoken guidance."""

    code: WorkflowErrorCode
    message: str
    guidance: str
    recoverable: bool = True
    source: str | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.message.strip() or not self.guidance.strip():
            raise ValueError("workflow failure requires message and guidance")
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "error_code": self.code,
                    "recoverable": self.recoverable,
                    "source": self.source,
                }
            ),
        )


@dataclass(frozen=True)
class SpokenStatus:
    """One user-facing spoken status message."""

    category: SpokenStatusCategory | str
    message: str
    workflow_status: WorkflowMode
    requires_speech: bool = True
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("spoken status message is required")
        category = (
            self.category
            if isinstance(self.category, SpokenStatusCategory)
            else SpokenStatusCategory(str(self.category))
        )
        object.__setattr__(self, "category", category)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "category": category,
                    "workflow_status": self.workflow_status,
                    "requires_speech": self.requires_speech,
                }
            ),
        )


@dataclass(frozen=True)
class WorkflowRequest:
    """One command-driven or operational workflow request."""

    intent: str
    language_hint: str = "unknown"
    allow_online: bool = True
    allow_offline: bool = True
    high_accuracy: bool = False
    request_id: str | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        language_hint = normalize_workflow_language(self.language_hint)
        object.__setattr__(self, "language_hint", language_hint)
        if self.request_id is None:
            object.__setattr__(self, "request_id", _request_id(self.intent, language_hint))
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "request_id": self.request_id,
                    "intent": self.intent,
                    "language_hint": language_hint,
                    "allow_online": self.allow_online,
                    "allow_offline": self.allow_offline,
                    "high_accuracy": self.high_accuracy,
                }
            ),
        )


@dataclass(frozen=True)
class ReadWorkflowResult:
    """Full outcome of one read workflow attempt."""

    success: bool
    status: WorkflowStatus
    capture_success: bool = False
    frame_selected: bool = False
    ocr_success: bool = False
    cleanup_success: bool = False
    reading_started: bool = False
    selected_ocr_engine: str | None = None
    language: str = "unknown"
    fallback_used: bool = False
    offline_route_used: bool = False
    high_accuracy_used: bool = False
    duration_ms: int = 0
    guidance: str = ""
    error: WorkflowFailure | None = None
    raw_text: str = ""
    clean_text: str = ""
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.guidance.strip():
            raise ValueError("read workflow result requires guidance")
        if not self.success and self.error is None:
            raise ValueError("failed read workflow result requires error")
        language = normalize_workflow_language(self.language)
        object.__setattr__(self, "language", language)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "success": self.success,
                    "status": self.status,
                    "capture_success": self.capture_success,
                    "frame_selected": self.frame_selected,
                    "ocr_success": self.ocr_success,
                    "cleanup_success": self.cleanup_success,
                    "reading_started": self.reading_started,
                    "selected_ocr_engine": self.selected_ocr_engine,
                    "language": language,
                    "fallback_used": self.fallback_used,
                    "offline_route_used": self.offline_route_used,
                    "high_accuracy_used": self.high_accuracy_used,
                    "duration_ms": max(0, self.duration_ms),
                    "error_code": self.error.code if self.error else None,
                }
            ),
        )

    @classmethod
    def ok(
        cls,
        *,
        selected_ocr_engine: str,
        language: str,
        guidance: str,
        raw_text: str = "",
        clean_text: str = "",
        fallback_used: bool = False,
        offline_route_used: bool = False,
        high_accuracy_used: bool = False,
        duration_ms: int = 0,
    ) -> "ReadWorkflowResult":
        return cls(
            success=True,
            status=WorkflowStatus.SUCCESS,
            capture_success=True,
            frame_selected=True,
            ocr_success=True,
            cleanup_success=True,
            reading_started=True,
            selected_ocr_engine=selected_ocr_engine,
            language=language,
            fallback_used=fallback_used,
            offline_route_used=offline_route_used,
            high_accuracy_used=high_accuracy_used,
            duration_ms=duration_ms,
            guidance=guidance,
            raw_text=raw_text,
            clean_text=clean_text,
        )

    @classmethod
    def failure(
        cls,
        *,
        error: WorkflowFailure,
        guidance: str | None = None,
        status: WorkflowStatus = WorkflowStatus.FAILED,
        duration_ms: int = 0,
    ) -> "ReadWorkflowResult":
        return cls(
            success=False,
            status=status,
            duration_ms=duration_ms,
            guidance=guidance or error.guidance,
            error=error,
        )


@dataclass(frozen=True)
class TranslationWorkflowResult:
    """Outcome of translating latest clean text."""

    success: bool
    status: WorkflowStatus
    target_language: str
    source_language: str = "unknown"
    translated_text: str = ""
    translated_text_available: bool = False
    reading_handoff_attempted: bool = False
    reading_handoff_success: bool = False
    fallback_used: bool = False
    duration_ms: int = 0
    guidance: str = ""
    error: WorkflowFailure | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.guidance.strip():
            raise ValueError("translation workflow result requires guidance")
        if not self.success and self.error is None:
            raise ValueError("failed translation workflow result requires error")
        target = normalize_workflow_language(self.target_language)
        source = normalize_workflow_language(self.source_language)
        object.__setattr__(self, "target_language", target)
        object.__setattr__(self, "source_language", source)
        available = bool(self.translated_text.strip()) if self.success else False
        object.__setattr__(self, "translated_text_available", available)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "success": self.success,
                    "status": self.status,
                    "target_language": target,
                    "source_language": source,
                    "translated_text_available": available,
                    "reading_handoff_attempted": self.reading_handoff_attempted,
                    "reading_handoff_success": self.reading_handoff_success,
                    "fallback_used": self.fallback_used,
                    "duration_ms": max(0, self.duration_ms),
                    "error_code": self.error.code if self.error else None,
                }
            ),
        )

    @classmethod
    def ok(
        cls,
        *,
        target_language: str,
        source_language: str,
        translated_text: str,
        guidance: str,
        reading_handoff_attempted: bool = False,
        reading_handoff_success: bool = False,
        fallback_used: bool = False,
        duration_ms: int = 0,
    ) -> "TranslationWorkflowResult":
        return cls(
            success=True,
            status=WorkflowStatus.SUCCESS,
            target_language=target_language,
            source_language=source_language,
            translated_text=translated_text,
            reading_handoff_attempted=reading_handoff_attempted,
            reading_handoff_success=reading_handoff_success,
            fallback_used=fallback_used,
            duration_ms=duration_ms,
            guidance=guidance,
        )

    @classmethod
    def failure(
        cls,
        *,
        target_language: str,
        source_language: str = "unknown",
        error: WorkflowFailure,
        guidance: str | None = None,
        status: WorkflowStatus = WorkflowStatus.FAILED,
        fallback_used: bool = False,
        duration_ms: int = 0,
    ) -> "TranslationWorkflowResult":
        return cls(
            success=False,
            status=status,
            target_language=target_language,
            source_language=source_language,
            fallback_used=fallback_used,
            duration_ms=duration_ms,
            guidance=guidance or error.guidance,
            error=error,
        )


@dataclass(frozen=True)
class AssistantState:
    """Latest in-memory assistant state."""

    current_mode: WorkflowMode = WorkflowMode.IDLE
    last_raw_text: str = ""
    last_clean_text: str = ""
    last_translated_text: str = ""
    last_language: str = "unknown"
    last_ocr_engine: str | None = None
    fallback_used: bool = False
    is_reading: bool = False
    is_paused: bool = False
    internet_available: bool | None = None
    last_guidance: str = ""
    last_result: Any | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        language = normalize_workflow_language(self.last_language)
        object.__setattr__(self, "last_language", language)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "current_mode": self.current_mode,
                    "last_language": language,
                    "last_ocr_engine": self.last_ocr_engine,
                    "fallback_used": self.fallback_used,
                    "is_reading": self.is_reading,
                    "is_paused": self.is_paused,
                    "internet_available": self.internet_available,
                    "has_raw_text": bool(self.last_raw_text),
                    "has_clean_text": bool(self.last_clean_text),
                    "has_translated_text": bool(self.last_translated_text),
                    "has_last_result": self.last_result is not None,
                }
            ),
        )

    def with_updates(self, **updates: Any) -> "AssistantState":
        """Return a copy of state with updates."""
        return replace(self, **updates)

    def with_successful_read(
        self,
        *,
        raw_text: str,
        clean_text: str,
        language: str,
        selected_ocr_engine: str | None,
        fallback_used: bool,
        guidance: str,
        result: ReadWorkflowResult | None = None,
    ) -> "AssistantState":
        """Record the latest successful read without persisting it."""
        return replace(
            self,
            current_mode=WorkflowMode.READING,
            last_raw_text=raw_text,
            last_clean_text=clean_text,
            last_language=language,
            last_ocr_engine=selected_ocr_engine,
            fallback_used=fallback_used,
            is_reading=True,
            is_paused=False,
            last_guidance=guidance,
            last_result=result,
        )

    def with_successful_translation(
        self,
        *,
        translated_text: str,
        guidance: str,
        result: TranslationWorkflowResult | None = None,
    ) -> "AssistantState":
        """Record latest successful translation without clearing clean text."""
        return replace(
            self,
            current_mode=WorkflowMode.TRANSLATING,
            last_translated_text=translated_text,
            last_guidance=guidance,
            last_result=result,
        )

    def with_failure(self, result: Any, *, mode: WorkflowMode = WorkflowMode.RECOVERING) -> "AssistantState":
        """Record recoverable failure guidance without clearing latest text."""
        return replace(
            self,
            current_mode=mode,
            last_guidance=getattr(result, "guidance", ""),
            last_result=result,
        )

    def clear_for_shutdown(self) -> "AssistantState":
        """Clear in-memory user content for process shutdown."""
        return replace(
            self,
            current_mode=WorkflowMode.SHUTTING_DOWN,
            last_raw_text="",
            last_clean_text="",
            last_translated_text="",
            last_language="unknown",
            last_ocr_engine=None,
            fallback_used=False,
            is_reading=False,
            is_paused=False,
            last_guidance="Assistant stopped.",
            last_result=None,
        )


@dataclass(frozen=True)
class AssistantSession:
    """One running assistant session."""

    state: AssistantState = field(default_factory=AssistantState)
    workflow_active: bool = False
    shutdown_requested: bool = False
    last_result: Any | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_workflow_metadata(
                {
                    "workflow_active": self.workflow_active,
                    "shutdown_requested": self.shutdown_requested,
                    "current_mode": self.state.current_mode,
                    "has_last_result": self.last_result is not None,
                }
            ),
        )

    def with_updates(self, **updates: Any) -> "AssistantSession":
        """Return a copy of session with updates."""
        return replace(self, **updates)

    def request_shutdown(self) -> "AssistantSession":
        """Mark the session as shutting down and clear volatile user content."""
        return replace(
            self,
            state=self.state.clear_for_shutdown(),
            workflow_active=False,
            shutdown_requested=True,
        )


__all__ = [
    "AssistantSession",
    "AssistantState",
    "ReadWorkflowResult",
    "SENSITIVE_WORKFLOW_METADATA_KEYS",
    "SpokenStatus",
    "SpokenStatusCategory",
    "TranslationWorkflowResult",
    "WorkflowErrorCode",
    "WorkflowFailure",
    "WorkflowMode",
    "WorkflowRequest",
    "WorkflowStatus",
    "normalize_workflow_language",
    "sanitize_workflow_metadata",
]
