"""Shared voice and TTS data models for Phase 6."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


MIN_SPEECH_RATE_WPM = 80
MAX_SPEECH_RATE_WPM = 220
DEFAULT_SPEECH_RATE_WPM = 150


class SpeechOperation(str, Enum):
    """Stable TTS operation names."""

    READ_ALL = "read_all"
    STOP = "stop"
    PAUSE = "pause"
    CONTINUE = "continue"
    SET_RATE = "set_rate"
    REPEAT_SENTENCE = "repeat_sentence"
    REPEAT_PARAGRAPH = "repeat_paragraph"
    GUIDANCE = "guidance"


class SegmentType(str, Enum):
    """Supported text segment types."""

    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FULL_TEXT = "full_text"


class ReadingControlType(str, Enum):
    """Playback control commands accepted by the reading controller."""

    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    CONTINUE = "continue"
    SET_RATE = "set_rate"
    REPEAT_SENTENCE = "repeat_sentence"
    REPEAT_PARAGRAPH = "repeat_paragraph"


class TTSErrorCode(str, Enum):
    """Stable TTS error categories."""

    NO_READABLE_TEXT = "NO_READABLE_TEXT"
    TTS_ENGINE_UNAVAILABLE = "TTS_ENGINE_UNAVAILABLE"
    TTS_ENGINE_FAILURE = "TTS_ENGINE_FAILURE"
    TTS_STOP_FAILED = "TTS_STOP_FAILED"
    TTS_PAUSE_UNSUPPORTED = "TTS_PAUSE_UNSUPPORTED"
    TTS_RESUME_UNSUPPORTED = "TTS_RESUME_UNSUPPORTED"
    NOTHING_TO_REPEAT = "NOTHING_TO_REPEAT"
    INVALID_COMMAND = "INVALID_COMMAND"
    UNEXPECTED_TTS_ERROR = "UNEXPECTED_TTS_ERROR"


SENSITIVE_SPEECH_METADATA_KEYS = {
    "clean_text",
    "guidance",
    "paragraph",
    "raw_text",
    "secret",
    "sentence",
    "snippet",
    "spoken_text",
    "text",
    "token",
}


def _enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_enum_value(item) for item in value]
    if isinstance(value, list):
        return [_enum_value(item) for item in value]
    return value


def sanitize_speech_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return speech metadata safe for default logs."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_SPEECH_METADATA_KEYS:
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        safe[key] = _enum_value(value)
    return safe


def clamp_speech_rate(rate_wpm: int | None) -> int:
    """Clamp speech rate to the Phase 6 supported range."""
    if rate_wpm is None:
        return DEFAULT_SPEECH_RATE_WPM
    return max(MIN_SPEECH_RATE_WPM, min(MAX_SPEECH_RATE_WPM, int(rate_wpm)))


@dataclass(frozen=True)
class TTSError:
    """Structured TTS failure without sensitive text content."""

    code: TTSErrorCode
    message: str
    recoverable: bool = True
    engine_name: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message is required")

    @property
    def safe_metadata(self) -> dict[str, Any]:
        return sanitize_speech_metadata(
            {
                "error_code": self.code,
                "recoverable": self.recoverable,
                "engine_name": self.engine_name,
            }
        )


@dataclass(frozen=True)
class TextSegment:
    """A sentence or paragraph prepared for speech or repeat."""

    segment_id: str
    segment_type: SegmentType
    order: int
    text: str
    language: str = "mixed"
    parent_text_id: str | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.segment_id.strip():
            raise ValueError("segment_id is required")
        if self.order < 0:
            raise ValueError("order must be non-negative")
        if not self.text.strip():
            raise ValueError("segment text is required")
        object.__setattr__(self, "text", self.text.strip())
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_speech_metadata(
                {
                    "segment_id": self.segment_id,
                    "segment_type": self.segment_type,
                    "segment_order": self.order,
                    "language": self.language,
                    "parent_text_id": self.parent_text_id,
                    "text_length": len(self.text.strip()),
                }
            ),
        )


@dataclass(frozen=True)
class SpeechRequest:
    """A single request to speak clean text."""

    text: str
    language: str = "mixed"
    rate_wpm: int | None = None
    operation: SpeechOperation = SpeechOperation.READ_ALL
    segment_id: str | None = None
    segment_type: SegmentType | None = None
    segment_order: int | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        text = self.text.strip()
        if not text:
            raise ValueError("text is required")
        rate = clamp_speech_rate(self.rate_wpm)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "rate_wpm", rate)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_speech_metadata(
                {
                    "language": self.language,
                    "rate_wpm": rate,
                    "operation": self.operation,
                    "segment_id": self.segment_id,
                    "segment_type": self.segment_type,
                    "segment_order": self.segment_order,
                    "text_length": len(text),
                }
            ),
        )

    @classmethod
    def from_segment(
        cls,
        segment: TextSegment,
        *,
        rate_wpm: int | None = None,
        operation: SpeechOperation,
    ) -> "SpeechRequest":
        """Build a request for a tracked text segment."""
        return cls(
            text=segment.text,
            language=segment.language,
            rate_wpm=rate_wpm,
            operation=operation,
            segment_id=segment.segment_id,
            segment_type=segment.segment_type,
            segment_order=segment.order,
        )


@dataclass(frozen=True)
class SpeechResult:
    """Structured result for a TTS operation."""

    success: bool
    operation: SpeechOperation
    engine_name: str | None = None
    duration_ms: int | None = None
    error: TTSError | None = None
    guidance: str = ""
    fallback_used: bool = False
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.success and self.error is None:
            raise ValueError("error is required for failed speech result")
        metadata = {
            "success": self.success,
            "operation": self.operation,
            "engine_name": self.engine_name,
            "duration_ms": self.duration_ms,
            "fallback_used": self.fallback_used,
            "error_code": self.error.code if self.error else None,
        }
        object.__setattr__(self, "safe_metadata", sanitize_speech_metadata(metadata))

    @classmethod
    def ok(
        cls,
        *,
        operation: SpeechOperation,
        engine_name: str | None = None,
        duration_ms: int | None = None,
        guidance: str = "Speech operation completed.",
        fallback_used: bool = False,
    ) -> "SpeechResult":
        return cls(
            success=True,
            operation=operation,
            engine_name=engine_name,
            duration_ms=duration_ms,
            guidance=guidance,
            fallback_used=fallback_used,
        )

    @classmethod
    def failure(
        cls,
        *,
        operation: SpeechOperation,
        engine_name: str | None = None,
        error: TTSError | None = None,
        guidance: str = "Speech operation failed.",
        fallback_used: bool = False,
    ) -> "SpeechResult":
        return cls(
            success=False,
            operation=operation,
            engine_name=engine_name,
            error=error,
            guidance=guidance,
            fallback_used=fallback_used,
        )


@dataclass(frozen=True)
class ReadingState:
    """In-memory reading session state."""

    is_active: bool = False
    is_paused: bool = False
    current_text_id: str | None = None
    current_segment: TextSegment | None = None
    current_rate_wpm: int = DEFAULT_SPEECH_RATE_WPM
    last_sentence: TextSegment | None = None
    last_paragraph: TextSegment | None = None
    last_operation: SpeechOperation | None = None
    last_result: SpeechResult | None = None
    native_pause_active: bool = False
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "current_rate_wpm",
            clamp_speech_rate(self.current_rate_wpm),
        )
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_speech_metadata(
                {
                    "is_active": self.is_active,
                    "is_paused": self.is_paused,
                    "current_text_id": self.current_text_id,
                    "current_rate_wpm": clamp_speech_rate(self.current_rate_wpm),
                    "current_segment_id": self.current_segment.segment_id
                    if self.current_segment
                    else None,
                    "last_sentence_id": self.last_sentence.segment_id
                    if self.last_sentence
                    else None,
                    "last_paragraph_id": self.last_paragraph.segment_id
                    if self.last_paragraph
                    else None,
                    "last_operation": self.last_operation,
                    "native_pause_active": self.native_pause_active,
                }
            ),
        )

    def with_updates(self, **updates: Any) -> "ReadingState":
        """Return a copy of the reading state with updated fields."""
        return replace(self, **updates)


@dataclass(frozen=True)
class ReadingControlCommand:
    """Playback control command model for later routing."""

    command_type: ReadingControlType
    requested_rate_wpm: int | None = None
    language: str | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        rate = (
            clamp_speech_rate(self.requested_rate_wpm)
            if self.requested_rate_wpm is not None
            else None
        )
        object.__setattr__(self, "requested_rate_wpm", rate)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_speech_metadata(
                {
                    "command_type": self.command_type,
                    "requested_rate_wpm": rate,
                    "language": self.language,
                }
            ),
        )


__all__ = [
    "DEFAULT_SPEECH_RATE_WPM",
    "MAX_SPEECH_RATE_WPM",
    "MIN_SPEECH_RATE_WPM",
    "ReadingControlCommand",
    "ReadingControlType",
    "ReadingState",
    "SegmentType",
    "SpeechOperation",
    "SpeechRequest",
    "SpeechResult",
    "TTSError",
    "TTSErrorCode",
    "TextSegment",
    "clamp_speech_rate",
    "sanitize_speech_metadata",
]
