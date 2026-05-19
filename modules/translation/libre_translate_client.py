"""LibreTranslate client boundary for Phase 7."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from modules.translation.base import validate_translation_result
from modules.translation.translation_models import (
    TranslationError,
    TranslationErrorCode,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
)


PostFunc = Callable[..., Any]


@dataclass(init=False)
class LibreTranslateClient:
    """Free LibreTranslate-compatible online provider."""

    endpoint: str = "https://libretranslate.com/translate"
    api_key: str = ""
    timeout_seconds: float = 10.0
    post_func: PostFunc | None = None
    _timeout_exceptions: tuple[type[BaseException], ...] | None = None
    name: str = "libre_translate"
    path: TranslationPath = TranslationPath.ONLINE

    def __init__(
        self,
        *,
        endpoint: str = "https://libretranslate.com/translate",
        api_key: str = "",
        timeout_seconds: float = 10.0,
        post_func: PostFunc | None = None,
        timeout_exceptions: tuple[type[BaseException], ...] | None = None,
        name: str = "libre_translate",
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.post_func = post_func
        self._timeout_exceptions = timeout_exceptions
        self.name = name
        self.path = TranslationPath.ONLINE

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """Translate clean text through a LibreTranslate-compatible endpoint."""
        started = time.monotonic()
        if not request.allow_online:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                "Online translation is disabled.",
                started,
            )

        try:
            payload = {
                "q": request.source_text,
                "source": request.source_language.value,
                "target": request.target_language.value,
                "format": "text",
            }
            if self.api_key.strip():
                payload["api_key"] = self.api_key
            response = self._post(
                json={
                    **payload,
                },
                timeout=self.timeout_seconds,
            )
        except self.timeout_exceptions:
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
                f"Online translation request failed: {type(exc).__name__}",
                started,
            )

        if getattr(response, "status_code", 200) >= 400:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                f"Online translation service returned status {response.status_code}.",
                started,
            )

        try:
            payload = response.json()
        except Exception:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation returned invalid JSON.",
                started,
            )

        if not isinstance(payload, dict):
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation returned an invalid payload.",
                started,
            )
        if payload.get("error"):
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation service returned an error.",
                started,
            )

        translated_text = str(payload.get("translatedText", "")).strip()
        if not translated_text:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Online translation returned empty translated text.",
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
            guidance="Translation is ready.",
        )

    @property
    def timeout_exceptions(self) -> tuple[type[BaseException], ...]:
        if self._timeout_exceptions is not None:
            return self._timeout_exceptions
        try:
            import requests

            return (requests.Timeout,)
        except Exception:  # pragma: no cover - requests should usually exist
            return (TimeoutError,)

    def _post(self, **kwargs: Any) -> Any:
        if self.post_func is not None:
            return self.post_func(self.endpoint, **kwargs)
        import requests

        return requests.post(self.endpoint, **kwargs)

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
    "LibreTranslateClient",
]
