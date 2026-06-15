"""Shared translation data models for Phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


class TranslationLanguage(str, Enum):
    """Supported Phase 7 translation language categories."""

    ARABIC = "ar"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class TranslationPath(str, Enum):
    """Translation path selected for a result."""

    ONLINE = "online"
    OFFLINE = "offline"
    NO_OP = "no_op"


class TranslationOperation(str, Enum):
    """Stable translation operation names."""

    TRANSLATE = "translate"
    GUIDANCE = "guidance"


class TranslationErrorCode(str, Enum):
    """Stable translation failure categories."""

    NO_TEXT_TO_TRANSLATE = "NO_TEXT_TO_TRANSLATE"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    LANGUAGE_DIRECTION_REQUIRED = "LANGUAGE_DIRECTION_REQUIRED"
    TRANSLATION_NOT_NEEDED = "TRANSLATION_NOT_NEEDED"
    ONLINE_TRANSLATION_UNAVAILABLE = "ONLINE_TRANSLATION_UNAVAILABLE"
    ONLINE_TRANSLATION_FAILED = "ONLINE_TRANSLATION_FAILED"
    OFFLINE_TRANSLATION_UNAVAILABLE = "OFFLINE_TRANSLATION_UNAVAILABLE"
    OFFLINE_TRANSLATION_FAILED = "OFFLINE_TRANSLATION_FAILED"
    INVALID_TRANSLATION_RESULT = "INVALID_TRANSLATION_RESULT"
    ALL_TRANSLATION_PROVIDERS_FAILED = "ALL_TRANSLATION_PROVIDERS_FAILED"
    READING_HANDOFF_FAILED = "READING_HANDOFF_FAILED"


SENSITIVE_TRANSLATION_METADATA_KEYS = {
    "clean_text",
    "endpoint_secret",
    "raw_text",
    "secret",
    "source_snippet",
    "source_text",
    "snippet",
    "text",
    "token",
    "translated_snippet",
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


def sanitize_translation_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return translation metadata safe for default logs."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_TRANSLATION_METADATA_KEYS:
            continue
        if isinstance(value, (bytes, bytearray)):
            continue
        safe[key] = _enum_value(value)
    return safe


def normalize_language(value: str | TranslationLanguage | None) -> TranslationLanguage:
    """Normalize common language labels to Phase 7 language values."""
    if isinstance(value, TranslationLanguage):
        return value
    normalized = (value or TranslationLanguage.UNKNOWN.value).strip().lower()
    aliases = {
        "arabic": TranslationLanguage.ARABIC,
        "ar": TranslationLanguage.ARABIC,
        "english": TranslationLanguage.ENGLISH,
        "en": TranslationLanguage.ENGLISH,
        "mixed": TranslationLanguage.MIXED,
        "unknown": TranslationLanguage.UNKNOWN,
        "": TranslationLanguage.UNKNOWN,
    }
    return aliases.get(normalized, TranslationLanguage.UNKNOWN)


@dataclass(frozen=True)
class TranslationError:
    """Structured translation failure without sensitive text content."""

    code: TranslationErrorCode
    message: str
    recoverable: bool = True
    engine_name: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message is required")

    @property
    def safe_metadata(self) -> dict[str, Any]:
        return sanitize_translation_metadata(
            {
                "error_code": self.code,
                "recoverable": self.recoverable,
                "engine_name": self.engine_name,
            }
        )


@dataclass(frozen=True)
class TranslationRequest:
    """A request to translate Phase 5 clean text."""

    source_text: str
    source_language: str | TranslationLanguage
    target_language: str | TranslationLanguage
    allow_online: bool = True
    allow_offline: bool = True
    explicit_source_language: bool = False
    operation: TranslationOperation = TranslationOperation.TRANSLATE
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.source_text, str):
            raise TypeError("source_text must be a string")
        source_language = normalize_language(self.source_language)
        target_language = normalize_language(self.target_language)
        object.__setattr__(self, "source_language", source_language)
        object.__setattr__(self, "target_language", target_language)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_translation_metadata(
                {
                    "source_language": source_language,
                    "target_language": target_language,
                    "allow_online": self.allow_online,
                    "allow_offline": self.allow_offline,
                    "explicit_source_language": self.explicit_source_language,
                    "operation": self.operation,
                    "source_text_length": len(self.source_text.strip()),
                }
            ),
        )


@dataclass(frozen=True)
class TranslationResult:
    """Structured result for a translation operation."""

    success: bool
    source_language: str | TranslationLanguage
    target_language: str | TranslationLanguage
    translated_text: str = ""
    engine_name: str | None = None
    path: TranslationPath = TranslationPath.ONLINE
    fallback_used: bool = False
    duration_ms: int | None = None
    is_valid: bool = False
    reading_handoff_attempted: bool = False
    reading_handoff_success: bool = False
    error: TranslationError | None = None
    guidance: str = ""
    operation: TranslationOperation = TranslationOperation.TRANSLATE
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        if not self.success and self.error is None:
            raise ValueError("error is required for failed translation result")
        source_language = normalize_language(self.source_language)
        target_language = normalize_language(self.target_language)
        object.__setattr__(self, "source_language", source_language)
        object.__setattr__(self, "target_language", target_language)
        object.__setattr__(self, "translated_text", self.translated_text.strip())
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_translation_metadata(
                {
                    "success": self.success,
                    "source_language": source_language,
                    "target_language": target_language,
                    "translated_text_length": len(self.translated_text.strip()),
                    "engine_name": self.engine_name,
                    "path": self.path,
                    "fallback_used": self.fallback_used,
                    "duration_ms": self.duration_ms,
                    "is_valid": self.is_valid,
                    "reading_handoff_attempted": self.reading_handoff_attempted,
                    "reading_handoff_success": self.reading_handoff_success,
                    "error_code": self.error.code if self.error else None,
                    "operation": self.operation,
                    **self.provider_metadata,
                }
            ),
        )

    @classmethod
    def ok(
        cls,
        *,
        source_language: str | TranslationLanguage,
        target_language: str | TranslationLanguage,
        translated_text: str,
        engine_name: str | None = None,
        path: TranslationPath = TranslationPath.ONLINE,
        fallback_used: bool = False,
        duration_ms: int | None = None,
        is_valid: bool = True,
        reading_handoff_attempted: bool = False,
        reading_handoff_success: bool = False,
        guidance: str = "Translation is ready.",
        provider_metadata: dict[str, Any] | None = None,
    ) -> "TranslationResult":
        return cls(
            success=True,
            source_language=source_language,
            target_language=target_language,
            translated_text=translated_text,
            engine_name=engine_name,
            path=path,
            fallback_used=fallback_used,
            duration_ms=duration_ms,
            is_valid=is_valid,
            reading_handoff_attempted=reading_handoff_attempted,
            reading_handoff_success=reading_handoff_success,
            guidance=guidance,
            provider_metadata=provider_metadata or {},
        )

    @classmethod
    def failure(
        cls,
        *,
        source_language: str | TranslationLanguage,
        target_language: str | TranslationLanguage,
        path: TranslationPath,
        engine_name: str | None = None,
        error: TranslationError | None = None,
        guidance: str = "Translation failed.",
        fallback_used: bool = False,
        duration_ms: int | None = None,
        reading_handoff_attempted: bool = False,
        reading_handoff_success: bool = False,
        provider_metadata: dict[str, Any] | None = None,
    ) -> "TranslationResult":
        return cls(
            success=False,
            source_language=source_language,
            target_language=target_language,
            engine_name=engine_name,
            path=path,
            fallback_used=fallback_used,
            duration_ms=duration_ms,
            error=error,
            guidance=guidance,
            reading_handoff_attempted=reading_handoff_attempted,
            reading_handoff_success=reading_handoff_success,
            provider_metadata=provider_metadata or {},
        )

    def with_updates(self, **updates: Any) -> "TranslationResult":
        """Return a copy of the result with updated fields."""
        return replace(self, **updates)


@dataclass(frozen=True)
class TranslationState:
    """Latest-only in-memory translation state."""

    current_source_text_id: str | None = None
    latest_translated_text: str | None = None
    source_language: TranslationLanguage | None = None
    target_language: TranslationLanguage | None = None
    selected_path: TranslationPath | None = None
    fallback_used: bool = False
    reading_handoff_attempted: bool = False
    reading_handoff_success: bool = False
    last_operation: TranslationOperation | None = None
    last_result: TranslationResult | None = None
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_translation_metadata(
                {
                    "current_source_text_id": self.current_source_text_id,
                    "has_latest_translation": self.latest_translated_text is not None,
                    "latest_translated_text_length": len(self.latest_translated_text or ""),
                    "source_language": self.source_language,
                    "target_language": self.target_language,
                    "selected_path": self.selected_path,
                    "fallback_used": self.fallback_used,
                    "reading_handoff_attempted": self.reading_handoff_attempted,
                    "reading_handoff_success": self.reading_handoff_success,
                    "last_operation": self.last_operation,
                    "last_success": self.last_result.success if self.last_result else None,
                    "last_error_code": self.last_result.error.code
                    if self.last_result and self.last_result.error
                    else None,
                }
            ),
        )

    def with_updates(self, **updates: Any) -> "TranslationState":
        """Return a copy of the translation state with updated fields."""
        return replace(self, **updates)

    def with_success(
        self,
        *,
        source_text_id: str,
        translated_text: str,
        result: TranslationResult,
    ) -> "TranslationState":
        """Replace latest state with a successful translation result."""
        return replace(
            self,
            current_source_text_id=source_text_id,
            latest_translated_text=translated_text,
            source_language=result.source_language,
            target_language=result.target_language,
            selected_path=result.path,
            fallback_used=result.fallback_used,
            reading_handoff_attempted=result.reading_handoff_attempted,
            reading_handoff_success=result.reading_handoff_success,
            last_operation=result.operation,
            last_result=result,
        )


@dataclass(frozen=True)
class TranslationControlRequest:
    """A later command-level request to translate the latest clean text."""

    target_language: str | TranslationLanguage
    source_language: str | TranslationLanguage | None = None
    allow_online: bool = True
    allow_offline: bool = True
    read_result: bool = True
    safe_metadata: dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        target_language = normalize_language(self.target_language)
        source_language = (
            normalize_language(self.source_language)
            if self.source_language is not None
            else None
        )
        object.__setattr__(self, "target_language", target_language)
        object.__setattr__(self, "source_language", source_language)
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_translation_metadata(
                {
                    "target_language": target_language,
                    "source_language": source_language,
                    "allow_online": self.allow_online,
                    "allow_offline": self.allow_offline,
                    "read_result": self.read_result,
                }
            ),
        )


__all__ = [
    "SENSITIVE_TRANSLATION_METADATA_KEYS",
    "TranslationControlRequest",
    "TranslationError",
    "TranslationErrorCode",
    "TranslationLanguage",
    "TranslationOperation",
    "TranslationPath",
    "TranslationRequest",
    "TranslationResult",
    "TranslationState",
    "normalize_language",
    "sanitize_translation_metadata",
]
