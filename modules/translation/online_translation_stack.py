"""Online translation engines for Phase 7.

Required stack order:

1) Google (deep_translator.GoogleTranslator)
2) MyMemory (deep_translator.MyMemoryTranslator)

The TranslationController remains responsible for offline fallback routing (Argos).
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import time
from typing import Callable

from modules.common.logging import LOGGER_NAME
from modules.translation.base import translate_safely, validate_translation_result
from modules.translation.translation_models import (
    TranslationError,
    TranslationErrorCode,
    TranslationLanguage,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
)


TranslateFunc = Callable[[str, str, str], str]


def _is_truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _allow_sensitive_text_logs(logger: logging.Logger) -> bool:
    """Return whether full text may be logged.

    Project policy: require both debug logging and explicit opt-in.
    """

    return bool(logger.isEnabledFor(logging.DEBUG) and _is_truthy_env("SENSITIVE_TEXT_LOGGING"))


def _split_into_chunks(text: str, *, max_chars: int) -> list[str]:
    """Split text into safe chunks without dropping content.

    This is intentionally simple (whitespace-aware) to keep behavior predictable.
    """

    cleaned = (text or "").strip()
    if not cleaned:
        return []
    if max_chars <= 0 or len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    remaining = cleaned
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break

        window = remaining[:max_chars]
        split_at = max(
            window.rfind("\n\n"),
            window.rfind("\n"),
            window.rfind("\t"),
            window.rfind(" "),
        )
        if split_at < max_chars // 2:
            split_at = max_chars

        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()

    return chunks


def _is_supported_language(language: TranslationLanguage) -> bool:
    return language in {TranslationLanguage.ARABIC, TranslationLanguage.ENGLISH}


@dataclass(init=False)
class GoogleTranslatorEngine:
    """Online translation via deep_translator.GoogleTranslator."""

    name: str = "google_translator"
    path: TranslationPath = TranslationPath.ONLINE
    timeout_seconds: float = 10.0
    max_chars_per_request: int = 4000
    translate_func: TranslateFunc | None = None

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        max_chars_per_request: int = 4000,
        translate_func: TranslateFunc | None = None,
        name: str = "google_translator",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_chars_per_request = max_chars_per_request
        self.translate_func = translate_func
        self.name = name
        self.path = TranslationPath.ONLINE

    def translate(self, request: TranslationRequest) -> TranslationResult:
        started = time.monotonic()
        logger = logging.getLogger(LOGGER_NAME)
        text = (request.source_text or "").strip()

        if not text:
            return self._failure(
                request,
                TranslationErrorCode.NO_TEXT_TO_TRANSLATE,
                "No text was provided for translation.",
                started,
            )

        if not request.allow_online:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                "Online translation is disabled.",
                started,
            )

        if not _is_supported_language(request.source_language) or not _is_supported_language(
            request.target_language
        ):
            return self._failure(
                request,
                TranslationErrorCode.UNSUPPORTED_LANGUAGE,
                "Unsupported language direction.",
                started,
            )

        logger.info(
            "TRANSLATION_PROVIDER_ATTEMPT provider=%s path=%s source=%s target=%s length=%s",
            self.name,
            self.path.value,
            request.source_language.value,
            request.target_language.value,
            len(text),
        )

        try:
            translated = self._translate_text(text, request)
        except ImportError:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                "deep-translator is not installed.",
                started,
            )
        except TimeoutError:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation timed out.",
                started,
            )
        except Exception as exc:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                f"Online translation failed: {type(exc).__name__}",
                started,
            )

        if not translated.strip():
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation returned empty translated text.",
                started,
            )

        is_valid = validate_translation_result(
            translated,
            source_text=text,
            target_language=request.target_language,
        )
        result = TranslationResult.ok(
            source_language=request.source_language,
            target_language=request.target_language,
            translated_text=translated,
            engine_name=self.name,
            path=self.path,
            duration_ms=self._duration_ms(started),
            is_valid=is_valid,
            guidance="Translation is ready.",
        )

        logger.info(
            "TRANSLATION_PROVIDER_RESULT provider=%s success=%s valid=%s duration_ms=%s",
            self.name,
            result.success,
            result.is_valid,
            result.duration_ms,
        )
        if _allow_sensitive_text_logs(logger):
            logger.debug(
                "TRANSLATION_PROVIDER_TEXT provider=%s translated_text=%r",
                self.name,
                result.translated_text,
            )
        return result

    def _translate_text(self, text: str, request: TranslationRequest) -> str:
        chunks = _split_into_chunks(text, max_chars=self.max_chars_per_request)
        if not chunks:
            return ""

        if self.translate_func is not None:
            translated_chunks = [
                str(
                    self.translate_func(
                        chunk,
                        request.source_language.value,
                        request.target_language.value,
                    )
                ).strip()
                for chunk in chunks
            ]
            return " ".join(part for part in translated_chunks if part)

        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(
            source=request.source_language.value,
            target=request.target_language.value,
        )
        translated_chunks = [str(translator.translate(chunk)).strip() for chunk in chunks]
        return " ".join(part for part in translated_chunks if part)

    def _failure(
        self,
        request: TranslationRequest,
        code: TranslationErrorCode,
        message: str,
        started: float,
    ) -> TranslationResult:
        logging.getLogger(LOGGER_NAME).info(
            "TRANSLATION_PROVIDER_RESULT provider=%s success=false code=%s",
            self.name,
            code.value,
        )
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


@dataclass(init=False)
class MyMemoryTranslatorEngine:
    """Online translation via deep_translator.MyMemoryTranslator."""

    name: str = "mymemory_translator"
    path: TranslationPath = TranslationPath.ONLINE
    timeout_seconds: float = 10.0
    max_chars_per_request: int = 500
    translate_func: TranslateFunc | None = None

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        max_chars_per_request: int = 500,
        translate_func: TranslateFunc | None = None,
        name: str = "mymemory_translator",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_chars_per_request = max_chars_per_request
        self.translate_func = translate_func
        self.name = name
        self.path = TranslationPath.ONLINE

    def translate(self, request: TranslationRequest) -> TranslationResult:
        started = time.monotonic()
        logger = logging.getLogger(LOGGER_NAME)
        text = (request.source_text or "").strip()

        if not text:
            return self._failure(
                request,
                TranslationErrorCode.NO_TEXT_TO_TRANSLATE,
                "No text was provided for translation.",
                started,
            )

        if not request.allow_online:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                "Online translation is disabled.",
                started,
            )

        if not _is_supported_language(request.source_language) or not _is_supported_language(
            request.target_language
        ):
            return self._failure(
                request,
                TranslationErrorCode.UNSUPPORTED_LANGUAGE,
                "Unsupported language direction.",
                started,
            )

        logger.info(
            "TRANSLATION_PROVIDER_ATTEMPT provider=%s path=%s source=%s target=%s length=%s",
            self.name,
            self.path.value,
            request.source_language.value,
            request.target_language.value,
            len(text),
        )

        try:
            translated = self._translate_text(text, request)
        except ImportError:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                "deep-translator is not installed.",
                started,
            )
        except TimeoutError:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation timed out.",
                started,
            )
        except Exception as exc:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                f"Online translation failed: {type(exc).__name__}",
                started,
            )

        if not translated.strip():
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation returned empty translated text.",
                started,
            )

        is_valid = validate_translation_result(
            translated,
            source_text=text,
            target_language=request.target_language,
        )
        result = TranslationResult.ok(
            source_language=request.source_language,
            target_language=request.target_language,
            translated_text=translated,
            engine_name=self.name,
            path=self.path,
            duration_ms=self._duration_ms(started),
            is_valid=is_valid,
            guidance="Translation is ready.",
        )

        logger.info(
            "TRANSLATION_PROVIDER_RESULT provider=%s success=%s valid=%s duration_ms=%s",
            self.name,
            result.success,
            result.is_valid,
            result.duration_ms,
        )
        if _allow_sensitive_text_logs(logger):
            logger.debug(
                "TRANSLATION_PROVIDER_TEXT provider=%s translated_text=%r",
                self.name,
                result.translated_text,
            )
        return result

    def _translate_text(self, text: str, request: TranslationRequest) -> str:
        chunks = _split_into_chunks(text, max_chars=self.max_chars_per_request)
        if not chunks:
            return ""

        if self.translate_func is not None:
            translated_chunks = [
                str(
                    self.translate_func(
                        chunk,
                        request.source_language.value,
                        request.target_language.value,
                    )
                ).strip()
                for chunk in chunks
            ]
            return " ".join(part for part in translated_chunks if part)

        from deep_translator import MyMemoryTranslator

        translator = MyMemoryTranslator(
            source=request.source_language.value,
            target=request.target_language.value,
        )
        translated_chunks = [str(translator.translate(chunk)).strip() for chunk in chunks]
        return " ".join(part for part in translated_chunks if part)

    def _failure(
        self,
        request: TranslationRequest,
        code: TranslationErrorCode,
        message: str,
        started: float,
    ) -> TranslationResult:
        logging.getLogger(LOGGER_NAME).info(
            "TRANSLATION_PROVIDER_RESULT provider=%s success=false code=%s",
            self.name,
            code.value,
        )
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


@dataclass(init=False)
class OnlineFallbackTranslationEngine:
    """Try a primary online engine, then a backup online engine.

    This preserves the TranslationController online/offline routing contract while
    ensuring online fallback order is: Google -> MyMemory.
    """

    primary: object
    backup: object
    name: str = "online_fallback"
    path: TranslationPath = TranslationPath.ONLINE

    def __init__(
        self,
        *,
        primary: object,
        backup: object,
        name: str = "online_fallback",
    ) -> None:
        self.primary = primary
        self.backup = backup
        self.name = name
        self.path = TranslationPath.ONLINE

    def translate(self, request: TranslationRequest) -> TranslationResult:
        logger = logging.getLogger(LOGGER_NAME)
        if not request.allow_online:
            return TranslationResult.failure(
                source_language=request.source_language,
                target_language=request.target_language,
                path=self.path,
                engine_name=self.name,
                error=TranslationError(
                    code=TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                    message="Online translation is disabled.",
                    engine_name=self.name,
                ),
                guidance="Online translation is unavailable.",
            )

        failures: list[TranslationResult] = []
        for engine in (self.primary, self.backup):
            engine_name = getattr(engine, "name", None) or self.name
            logger.info(
                "TRANSLATION_STACK_ATTEMPT provider=%s",
                engine_name,
            )
            result = translate_safely(engine, request)
            if result.success and validate_translation_result(
                result.translated_text,
                source_text=request.source_text,
                target_language=request.target_language,
            ):
                logger.info(
                    "TRANSLATION_STACK_SUCCESS provider=%s",
                    result.engine_name or engine_name,
                )
                return result.with_updates(is_valid=True)

            if result.success:
                result = TranslationResult.failure(
                    source_language=request.source_language,
                    target_language=request.target_language,
                    path=self.path,
                    engine_name=result.engine_name or engine_name,
                    duration_ms=result.duration_ms,
                    error=TranslationError(
                        code=TranslationErrorCode.INVALID_TRANSLATION_RESULT,
                        message="Provider returned an invalid translation result",
                        engine_name=result.engine_name or engine_name,
                    ),
                    guidance="The translation result was not reliable.",
                )
            failures.append(result)
            logger.info(
                "TRANSLATION_STACK_FAILURE provider=%s code=%s",
                result.engine_name or engine_name,
                result.error.code.value if result.error else "UNKNOWN",
            )

        return failures[-1] if failures else TranslationResult.failure(
            source_language=request.source_language,
            target_language=request.target_language,
            path=self.path,
            engine_name=self.name,
            error=TranslationError(
                code=TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                message="Online translation providers failed.",
                engine_name=self.name,
            ),
            guidance="Online translation failed.",
        )


__all__ = [
    "GoogleTranslatorEngine",
    "MyMemoryTranslatorEngine",
    "OnlineFallbackTranslationEngine",
]
