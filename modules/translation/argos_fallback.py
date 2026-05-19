"""Argos Translate fallback boundary for Phase 7."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any

from modules.translation.base import validate_translation_result
from modules.translation.translation_models import (
    TranslationError,
    TranslationErrorCode,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
)


LanguageLoader = Callable[[], list[Any]]


@dataclass
class ArgosTranslateFallback:
    """Local Argos Translate fallback with lazy package/model loading."""

    language_loader: LanguageLoader | None = None
    name: str = "argos_translate"
    path: TranslationPath = TranslationPath.OFFLINE
    _languages: list[Any] | None = None

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate clean text with local Argos resources when available."""
        started = time.monotonic()
        if not request.allow_offline:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE,
                "Offline translation is disabled.",
                started,
            )

        try:
            languages = self._load_languages()
        except ImportError:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE,
                "Argos Translate is not installed.",
                started,
            )
        except Exception as exc:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE,
                f"Argos Translate resources could not load: {type(exc).__name__}",
                started,
            )

        source = self._find_language(languages, request.source_language.value)
        target = self._find_language(languages, request.target_language.value)
        if source is None or target is None:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE,
                "Offline translation languages are not installed.",
                started,
            )

        translation = source.get_translation(target)
        if translation is None:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE,
                "Offline translation model is not installed.",
                started,
            )

        try:
            translated_text = str(translation.translate(request.source_text)).strip()
        except Exception as exc:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_FAILED,
                f"Offline translation failed: {type(exc).__name__}",
                started,
            )

        if not translated_text:
            return self._failure(
                request,
                TranslationErrorCode.OFFLINE_TRANSLATION_FAILED,
                "Offline translation returned empty translated text.",
                started,
            )

        return TranslationResult.ok(
            source_language=request.source_language,
            target_language=request.target_language,
            translated_text=translated_text,
            engine_name=self.name,
            path=self.path,
            duration_ms=self._duration_ms(started),
            is_valid=validate_translation_result(
                translated_text,
                source_text=request.source_text,
                target_language=request.target_language,
            ),
            guidance="Fallback translation is ready.",
        )

    def _load_languages(self) -> list[Any]:
        if self._languages is not None:
            return self._languages
        if self.language_loader is not None:
            self._languages = self.language_loader()
            return self._languages
        from argostranslate import translate

        self._languages = list(translate.get_installed_languages())
        return self._languages

    @staticmethod
    def _find_language(languages: list[Any], code: str) -> Any | None:
        for language in languages:
            if getattr(language, "code", None) == code:
                return language
        return None

    def _failure(
        self,
        request: TranslationRequest,
        code: TranslationErrorCode,
        message: str,
        started: float,
    ) -> TranslationResult:
        return TranslationResult.failure(
            source_language=request.source_language,
            target_language=request.target_language,
            path=self.path,
            engine_name=self.name,
            duration_ms=self._duration_ms(started),
            error=TranslationError(
                code=code,
                message=message,
                engine_name=self.name,
            ),
            guidance=message,
        )

    @staticmethod
    def _duration_ms(started: float) -> int:
        return int((time.monotonic() - started) * 1000)


__all__ = [
    "ArgosTranslateFallback",
]
