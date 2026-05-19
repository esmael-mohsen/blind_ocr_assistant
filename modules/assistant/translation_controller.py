"""Translation controller for Phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

from modules.translation.base import (
    TranslationEngine,
    translate_safely,
    validate_translation_result,
)
from modules.translation.translation_models import (
    TranslationError,
    TranslationErrorCode,
    TranslationLanguage,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
    TranslationState,
    normalize_language,
)


def _text_id(clean_text: str) -> str:
    digest = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:12]
    return f"text:{digest}"


@dataclass
class TranslationController:
    """Stateful translation controller for latest clean OCR text."""

    online_engine: TranslationEngine | None = None
    offline_engine: TranslationEngine | None = None
    reading_controller: object | None = None
    state: TranslationState = field(default_factory=TranslationState)

    def get_state(self) -> TranslationState:
        """Return the current latest-only translation state."""
        return self.state

    def translate_latest(
        self,
        clean_text: str,
        target_language: str = "en",
        source_language: str = "unknown",
        explicit_source_language: bool = False,
        allow_online: bool = True,
        allow_offline: bool = True,
        read_result: bool = True,
    ) -> TranslationResult:
        """Translate clean text through configured engines."""
        text = (clean_text or "").strip()
        target = normalize_language(target_language)
        source = normalize_language(source_language)
        if not text:
            result = self._failure(
                source_language=source,
                target_language=target,
                path=TranslationPath.NO_OP,
                code=TranslationErrorCode.NO_TEXT_TO_TRANSLATE,
                message="No clean text was provided for translation",
                guidance="No readable text is available to translate.",
                recoverable=False,
            )
            self.state = self.state.with_updates(last_result=result)
            return result

        if self._is_unsupported_target(target_language, target):
            result = self._failure(
                source_language=source,
                target_language=target,
                path=TranslationPath.NO_OP,
                code=TranslationErrorCode.UNSUPPORTED_LANGUAGE,
                message="Unsupported target language",
                guidance="Only Arabic and English translation are supported.",
                recoverable=False,
            )
            self.state = self.state.with_updates(last_result=result)
            return result

        if self._is_unsupported_source(source_language, source):
            result = self._failure(
                source_language=source,
                target_language=target,
                path=TranslationPath.NO_OP,
                code=TranslationErrorCode.UNSUPPORTED_LANGUAGE,
                message="Unsupported source language",
                guidance="Only Arabic and English source languages are supported.",
                recoverable=False,
            )
            self.state = self.state.with_updates(last_result=result)
            return result

        if source in {
            TranslationLanguage.MIXED,
            TranslationLanguage.UNKNOWN,
        } and not explicit_source_language:
            result = self._failure(
                source_language=source,
                target_language=target,
                path=TranslationPath.NO_OP,
                code=TranslationErrorCode.LANGUAGE_DIRECTION_REQUIRED,
                message="Explicit source language is required",
                guidance="Please choose Arabic to English or English to Arabic before translating.",
                recoverable=True,
            )
            self.state = self.state.with_updates(last_result=result)
            return result

        if source == target and source in {
            TranslationLanguage.ARABIC,
            TranslationLanguage.ENGLISH,
        }:
            no_op = TranslationResult.ok(
                source_language=source,
                target_language=target,
                translated_text=text,
                engine_name="translation_controller",
                path=TranslationPath.NO_OP,
                is_valid=True,
                guidance="Translation was not needed.",
            )
            accepted = self._with_reading_handoff(no_op, read_result=read_result)
            if accepted.reading_handoff_attempted and accepted.reading_handoff_success:
                accepted = accepted.with_updates(
                    guidance="Translation was not needed, so the text is being read."
                )
            self.state = self.state.with_success(
                source_text_id=_text_id(text),
                translated_text=accepted.translated_text,
                result=accepted,
            )
            return accepted

        request = TranslationRequest(
            source_text=text,
            source_language=source,
            target_language=target,
            allow_online=allow_online,
            allow_offline=allow_offline,
            explicit_source_language=explicit_source_language,
        )

        if not allow_online or self.online_engine is None:
            online_result = self._failure(
                source_language=source,
                target_language=target,
                path=TranslationPath.ONLINE,
                code=TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                message="Online translation is unavailable",
                guidance="Online translation is unavailable.",
            )
            result = self._attempt_offline_or_return(
                request,
                prior_result=online_result,
                read_result=read_result,
            )
            return self._record_result(text, result)

        online_result = translate_safely(self.online_engine, request)
        if not online_result.success:
            result = self._attempt_offline_or_return(
                request,
                prior_result=online_result,
                read_result=read_result,
            )
            return self._record_result(text, result)

        if not validate_translation_result(
            online_result.translated_text,
            source_text=text,
            target_language=target,
        ):
            invalid = self._failure(
                source_language=source,
                target_language=target,
                path=online_result.path,
                code=TranslationErrorCode.INVALID_TRANSLATION_RESULT,
                message="Provider returned an invalid translation result",
                guidance="The translation result was not reliable.",
                engine_name=online_result.engine_name,
            )
            result = self._attempt_offline_or_return(
                request,
                prior_result=invalid,
                read_result=read_result,
            )
            return self._record_result(text, result)

        accepted = self._with_reading_handoff(
            online_result.with_updates(is_valid=True),
            read_result=read_result,
        )
        return self._record_result(text, accepted)

    def _attempt_offline_or_return(
        self,
        request: TranslationRequest,
        *,
        prior_result: TranslationResult,
        read_result: bool,
    ) -> TranslationResult:
        if not request.allow_offline or self.offline_engine is None:
            return prior_result

        offline_result = translate_safely(self.offline_engine, request)
        if offline_result.success and validate_translation_result(
            offline_result.translated_text,
            source_text=request.source_text,
            target_language=request.target_language,
        ):
            return self._with_reading_handoff(
                offline_result.with_updates(is_valid=True, fallback_used=True),
                read_result=read_result,
            )

        if offline_result.success:
            offline_result = self._failure(
                source_language=request.source_language,
                target_language=request.target_language,
                path=offline_result.path,
                code=TranslationErrorCode.INVALID_TRANSLATION_RESULT,
                message="Offline provider returned an invalid translation result",
                guidance="The fallback translation result was not reliable.",
                engine_name=offline_result.engine_name,
            )

        return self._failure(
            source_language=request.source_language,
            target_language=request.target_language,
            path=TranslationPath.OFFLINE,
            code=TranslationErrorCode.ALL_TRANSLATION_PROVIDERS_FAILED,
            message="All allowed translation providers failed",
            guidance="Translation failed. Try again with a clearer text direction or check the offline translation setup.",
            engine_name=offline_result.engine_name,
            recoverable=True,
        ).with_updates(fallback_used=True)

    def _record_result(
        self,
        source_text: str,
        result: TranslationResult,
    ) -> TranslationResult:
        if not result.success:
            self.state = self.state.with_updates(last_result=result)
            return result
        self.state = self.state.with_success(
            source_text_id=_text_id(source_text),
            translated_text=result.translated_text,
            result=result,
        )
        return result

    def _with_reading_handoff(
        self,
        result: TranslationResult,
        *,
        read_result: bool,
    ) -> TranslationResult:
        if not read_result or self.reading_controller is None:
            guidance = (
                result.guidance
                if result.path == TranslationPath.NO_OP
                else "Translation is ready to read."
            )
            return result.with_updates(
                reading_handoff_attempted=False,
                reading_handoff_success=False,
                guidance=guidance,
            )
        try:
            speech_result = self.reading_controller.start_reading(
                result.translated_text,
                language=result.target_language.value,
            )
            success = bool(getattr(speech_result, "success", False))
        except Exception:
            success = False
        return result.with_updates(
            reading_handoff_attempted=True,
            reading_handoff_success=success,
            guidance=(
                (
                    "Translation was not needed, so the text is being read."
                    if result.path == TranslationPath.NO_OP
                    else "The translated text is being read."
                )
                if success
                else (
                    "Translation was not needed, but reading could not start."
                    if result.path == TranslationPath.NO_OP
                    else "Translation is ready, but reading could not start."
                )
            ),
        )

    @staticmethod
    def _is_unsupported_target(
        original: str,
        normalized: TranslationLanguage,
    ) -> bool:
        original_value = (original or "").strip().lower()
        supported_labels = {"ar", "arabic", "en", "english"}
        return normalized not in {
            TranslationLanguage.ARABIC,
            TranslationLanguage.ENGLISH,
        } or original_value not in supported_labels

    @staticmethod
    def _is_unsupported_source(
        original: str,
        normalized: TranslationLanguage,
    ) -> bool:
        original_value = (original or "").strip().lower()
        supported_labels = {"ar", "arabic", "en", "english", "mixed", "unknown", ""}
        return original_value not in supported_labels or normalized not in {
            TranslationLanguage.ARABIC,
            TranslationLanguage.ENGLISH,
            TranslationLanguage.MIXED,
            TranslationLanguage.UNKNOWN,
        }

    def _failure(
        self,
        *,
        source_language: TranslationLanguage,
        target_language: TranslationLanguage,
        path: TranslationPath,
        code: TranslationErrorCode,
        message: str,
        guidance: str,
        engine_name: str | None = None,
        recoverable: bool = True,
    ) -> TranslationResult:
        return TranslationResult.failure(
            source_language=source_language,
            target_language=target_language,
            path=path,
            engine_name=engine_name,
            error=TranslationError(
                code=code,
                message=message,
                recoverable=recoverable,
                engine_name=engine_name,
            ),
            guidance=guidance,
        )


__all__ = [
    "TranslationController",
]
