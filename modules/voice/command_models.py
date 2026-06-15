"""Shared command data models for Phase 8."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


class CommandIntent(str, Enum):
    """Supported command intents for Phase 8."""

    READ = "read"
    STOP = "stop"
    CONTINUE = "continue"
    REPEAT_SENTENCE = "repeat_sentence"
    REPEAT_PARAGRAPH = "repeat_paragraph"
    TRANSLATE_TO_ARABIC = "translate_to_arabic"
    TRANSLATE_TO_ENGLISH = "translate_to_english"
    HELP = "help"
    CANCEL = "cancel"
    STATUS = "status"
    WHAT_DO_YOU_SEE = "what_do_you_see"
    REPEAT_GUIDANCE = "repeat_guidance"
    READ_AGAIN = "read_again"
    CAPTURE_NOW = "capture_now"
    SWITCH_ARABIC = "switch_arabic"
    SWITCH_ENGLISH = "switch_english"
    QUIET_MODE = "quiet_mode"
    VERBOSE_MODE = "verbose_mode"
    VOICE_TEST = "voice_test"
    EXIT = "exit"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"


class CommandPath(str, Enum):
    """Recognition path used for a command result."""

    ONLINE = "online"
    LOCAL = "local"
    PARSER = "parser"


class CommandConfidence(str, Enum):
    """Command recognition confidence categories."""

    HIGH = "high"
    LOW = "low"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


class CommandOperation(str, Enum):
    """Stable command operation names."""

    RECOGNIZE = "recognize"
    ROUTE = "route"
    GUIDANCE = "guidance"


class CommandErrorCode(str, Enum):
    """Stable command error categories."""

    NO_COMMAND_INPUT = "NO_COMMAND_INPUT"
    UNKNOWN_COMMAND = "UNKNOWN_COMMAND"
    AMBIGUOUS_COMMAND = "AMBIGUOUS_COMMAND"
    LOW_CONFIDENCE_COMMAND = "LOW_CONFIDENCE_COMMAND"
    ONLINE_STT_UNAVAILABLE = "ONLINE_STT_UNAVAILABLE"
    ONLINE_STT_FAILED = "ONLINE_STT_FAILED"
    LOCAL_STT_UNAVAILABLE = "LOCAL_STT_UNAVAILABLE"
    LOCAL_STT_FAILED = "LOCAL_STT_FAILED"
    ROUTING_TARGET_UNAVAILABLE = "ROUTING_TARGET_UNAVAILABLE"
    COMMAND_ROUTING_FAILED = "COMMAND_ROUTING_FAILED"
    ALL_RECOGNIZERS_FAILED = "ALL_RECOGNIZERS_FAILED"


SENSITIVE_COMMAND_METADATA_KEYS = {
    "clean_text",
    "command_snippet",
    "endpoint_secret",
    "phrase",
    "raw_ocr_text",
    "raw_speech",
    "raw_text",
    "recognized_phrase",
    "secret",
    "snippet",
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


def sanitize_command_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return command metadata safe for default logs."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_COMMAND_METADATA_KEYS:
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        safe[key] = _enum_value(value)
    return safe


def normalize_command_language(value: str | None) -> str:
    """Normalize language hints to Phase 8 command language labels."""
    normalized = (value or "unknown").strip().lower()
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


@dataclass(frozen=True)
class CommandError:
    """Structured command failure without sensitive phrase content."""

    code: CommandErrorCode
    message: str
    recoverable: bool = True
    recognizer_name: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message is required")

    @property
    def safe_metadata(self) -> dict[str, Any]:
        return sanitize_command_metadata(
            {
                "error_code": self.code,
                "recoverable": self.recoverable,
                "recognizer_name": self.recognizer_name,
            }
        )


@dataclass(frozen=True)
class CommandRequest:
    """One spoken or transcript-level command attempt."""

    phrase: str
    language_hint: str = "unknown"
    allow_online: bool = True
    allow_local: bool = True
    operation: CommandOperation = CommandOperation.RECOGNIZE
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.phrase, str):
            raise TypeError("phrase must be a string")
        language_hint = normalize_command_language(self.language_hint)
        object.__setattr__(self, "language_hint", language_hint)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_command_metadata(
                {
                    "language_hint": language_hint,
                    "allow_online": self.allow_online,
                    "allow_local": self.allow_local,
                    "operation": self.operation,
                    "phrase_length": len(self.phrase.strip()),
                }
            ),
        )


@dataclass(frozen=True)
class CommandResult:
    """Structured result for command recognition and optional routing."""

    success: bool
    intent: CommandIntent
    language: str = "unknown"
    path: CommandPath = CommandPath.PARSER
    fallback_used: bool = False
    confidence: CommandConfidence = CommandConfidence.NONE
    target_language: str | None = None
    routed: bool = False
    routed_success: bool = False
    duration_ms: int | None = None
    error: CommandError | None = None
    guidance: str = ""
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.success and self.error is None:
            raise ValueError("error is required for failed command result")
        if not self.guidance.strip():
            raise ValueError("guidance is required")
        language = normalize_command_language(self.language)
        object.__setattr__(self, "language", language)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_command_metadata(
                {
                    "success": self.success,
                    "intent": self.intent,
                    "language": language,
                    "path": self.path,
                    "fallback_used": self.fallback_used,
                    "confidence": self.confidence,
                    "target_language": self.target_language,
                    "routed": self.routed,
                    "routed_success": self.routed_success,
                    "duration_ms": self.duration_ms,
                    "error_code": self.error.code if self.error else None,
                }
            ),
        )

    @classmethod
    def recognized(
        cls,
        *,
        intent: CommandIntent,
        language: str,
        path: CommandPath,
        guidance: str,
        fallback_used: bool = False,
        confidence: CommandConfidence = CommandConfidence.HIGH,
        target_language: str | None = None,
        routed: bool = False,
        routed_success: bool = False,
        duration_ms: int | None = None,
    ) -> "CommandResult":
        return cls(
            success=True,
            intent=intent,
            language=language,
            path=path,
            fallback_used=fallback_used,
            confidence=confidence,
            target_language=target_language,
            routed=routed,
            routed_success=routed_success,
            duration_ms=duration_ms,
            guidance=guidance,
        )

    @classmethod
    def failure(
        cls,
        *,
        intent: CommandIntent,
        language: str,
        path: CommandPath,
        error: CommandError | None = None,
        guidance: str,
        fallback_used: bool = False,
        confidence: CommandConfidence = CommandConfidence.NONE,
        target_language: str | None = None,
        routed: bool = False,
        routed_success: bool = False,
        duration_ms: int | None = None,
    ) -> "CommandResult":
        return cls(
            success=False,
            intent=intent,
            language=language,
            path=path,
            fallback_used=fallback_used,
            confidence=confidence,
            target_language=target_language,
            routed=routed,
            routed_success=routed_success,
            duration_ms=duration_ms,
            error=error,
            guidance=guidance,
        )

    def with_updates(self, **updates: Any) -> "CommandResult":
        """Return a copy of the command result with updated fields."""
        return replace(self, **updates)


@dataclass(frozen=True)
class DialogueState:
    """Latest-only safe command state."""

    last_intent: CommandIntent | None = None
    selected_path: CommandPath | None = None
    fallback_used: bool = False
    last_result: CommandResult | None = None
    last_guidance: str = ""
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_command_metadata(
                {
                    "last_intent": self.last_intent,
                    "selected_path": self.selected_path,
                    "fallback_used": self.fallback_used,
                    "has_last_result": self.last_result is not None,
                    "last_success": self.last_result.success
                    if self.last_result
                    else None,
                    "last_error_code": self.last_result.error.code
                    if self.last_result and self.last_result.error
                    else None,
                }
            ),
        )

    def with_result(self, result: CommandResult) -> "DialogueState":
        """Replace latest command state with a safe command result."""
        return replace(
            self,
            last_intent=result.intent,
            selected_path=result.path,
            fallback_used=result.fallback_used,
            last_result=result,
            last_guidance=result.guidance,
        )


@dataclass(frozen=True)
class CommandFeedback:
    """Spoken confirmation or recovery guidance."""

    guidance: str
    intent: CommandIntent
    requires_action: bool = False
    examples_available: bool = False
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.guidance.strip():
            raise ValueError("guidance is required")
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_command_metadata(
                {
                    "intent": self.intent,
                    "requires_action": self.requires_action,
                    "examples_available": self.examples_available,
                }
            ),
        )


__all__ = [
    "CommandConfidence",
    "CommandError",
    "CommandErrorCode",
    "CommandFeedback",
    "CommandIntent",
    "CommandOperation",
    "CommandPath",
    "CommandRequest",
    "CommandResult",
    "DialogueState",
    "SENSITIVE_COMMAND_METADATA_KEYS",
    "normalize_command_language",
    "sanitize_command_metadata",
]
