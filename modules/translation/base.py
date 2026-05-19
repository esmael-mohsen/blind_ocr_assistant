"""Translation engine boundary for Phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import time
from typing import Protocol

from modules.translation.translation_models import (
    TranslationError,
    TranslationErrorCode,
    TranslationLanguage,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
)


ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
ENGLISH_RE = re.compile(r"[A-Za-z]")
SUPPORTED_DIRECTIONS = {
    (TranslationLanguage.ARABIC, TranslationLanguage.ENGLISH),
    (TranslationLanguage.ENGLISH, TranslationLanguage.ARABIC),
}


class TranslationEngine(Protocol):
    """Protocol for replaceable translation engines."""

    name: str
    path: TranslationPath

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate clean text or return a structured failure."""


@dataclass
class MockTranslationEngine:
    """Deterministic in-memory translation engine for controller tests."""

    name: str = "mock"
    path: TranslationPath = TranslationPath.ONLINE
    responses: dict[tuple[str, str], str] = field(default_factory=dict)
    supported_directions: tuple[tuple[str, str], ...] = (
        ("ar", "en"),
        ("en", "ar"),
    )
    fail_code: TranslationErrorCode | None = None
    raise_on_translate: Exception | None = None
    duration_ms: int | None = None
    calls: list[TranslationRequest] = field(default_factory=list)

    def translate(self, request: TranslationRequest) -> TranslationResult:
        self.calls.append(request)
        if self.raise_on_translate is not None:
            raise self.raise_on_translate
        direction = (request.source_language.value, request.target_language.value)
        if direction not in self.supported_directions:
            return _failure_for_path(
                path=self.path,
                source_language=request.source_language,
                target_language=request.target_language,
                engine_name=self.name,
                code=TranslationErrorCode.UNSUPPORTED_LANGUAGE,
                message="translation direction is not supported",
                guidance="This translation direction is not supported.",
            )
        if self.fail_code is not None:
            return _failure_for_path(
                path=self.path,
                source_language=request.source_language,
                target_language=request.target_language,
                engine_name=self.name,
                code=self.fail_code,
                message="mock translation failure",
                guidance="The translation provider could not translate the text.",
            )
        translated_text = self.responses.get(direction, f"{self.name} translation")
        return TranslationResult.ok(
            source_language=request.source_language,
            target_language=request.target_language,
            translated_text=translated_text,
            engine_name=self.name,
            path=self.path,
            duration_ms=self.duration_ms,
            is_valid=validate_translation_result(
                translated_text,
                source_text=request.source_text,
                target_language=request.target_language,
            ),
            guidance="Translation is ready.",
        )


def is_supported_direction(
    source_language: TranslationLanguage,
    target_language: TranslationLanguage,
) -> bool:
    """Return whether Phase 7 supports the requested translation direction."""
    return (source_language, target_language) in SUPPORTED_DIRECTIONS


def validate_translation_result(
    translated_text: str,
    *,
    source_text: str,
    target_language: TranslationLanguage,
    no_op: bool = False,
) -> bool:
    """Validate translated output before the controller accepts it."""
    candidate = (translated_text or "").strip()
    if not candidate:
        return False
    if no_op:
        return candidate == source_text.strip()
    if candidate == source_text.strip():
        return False
    if target_language == TranslationLanguage.ENGLISH:
        return bool(ENGLISH_RE.search(candidate)) and not bool(ARABIC_RE.search(candidate))
    if target_language == TranslationLanguage.ARABIC:
        return bool(ARABIC_RE.search(candidate))
    return False


def translate_safely(
    engine: TranslationEngine,
    request: TranslationRequest,
) -> TranslationResult:
    """Call a provider and convert unexpected exceptions to structured results."""
    started = time.monotonic()
    try:
        return engine.translate(request)
    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        path = getattr(engine, "path", TranslationPath.ONLINE)
        code = (
            TranslationErrorCode.ONLINE_TRANSLATION_FAILED
            if path == TranslationPath.ONLINE
            else TranslationErrorCode.OFFLINE_TRANSLATION_FAILED
        )
        return TranslationResult.failure(
            source_language=request.source_language,
            target_language=request.target_language,
            path=path,
            engine_name=getattr(engine, "name", None),
            duration_ms=duration_ms,
            error=TranslationError(
                code=code,
                message=f"translation provider raised {type(exc).__name__}",
                engine_name=getattr(engine, "name", None),
            ),
            guidance="The translation provider failed unexpectedly.",
        )


def provider_unavailable_result(
    *,
    path: TranslationPath,
    source_language: TranslationLanguage,
    target_language: TranslationLanguage,
    engine_name: str,
    guidance: str,
) -> TranslationResult:
    """Build a provider-unavailable result for online or offline engines."""
    code = (
        TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE
        if path == TranslationPath.ONLINE
        else TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE
    )
    return _failure_for_path(
        path=path,
        source_language=source_language,
        target_language=target_language,
        engine_name=engine_name,
        code=code,
        message=guidance,
        guidance=guidance,
    )


def _failure_for_path(
    *,
    path: TranslationPath,
    source_language: TranslationLanguage,
    target_language: TranslationLanguage,
    engine_name: str | None,
    code: TranslationErrorCode,
    message: str,
    guidance: str,
) -> TranslationResult:
    return TranslationResult.failure(
        source_language=source_language,
        target_language=target_language,
        path=path,
        engine_name=engine_name,
        error=TranslationError(
            code=code,
            message=message,
            engine_name=engine_name,
        ),
        guidance=guidance,
    )


__all__ = [
    "ARABIC_RE",
    "ENGLISH_RE",
    "MockTranslationEngine",
    "SUPPORTED_DIRECTIONS",
    "TranslationEngine",
    "is_supported_direction",
    "provider_unavailable_result",
    "translate_safely",
    "validate_translation_result",
]
