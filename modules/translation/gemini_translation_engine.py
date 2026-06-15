"""Gemini-backed Arabic/English translation engine."""

from __future__ import annotations

from typing import Any, Callable
import time

from modules.translation.base import validate_translation_result
from modules.translation.translation_models import (
    TranslationError,
    TranslationErrorCode,
    TranslationPath,
    TranslationRequest,
    TranslationResult,
)


PostFunc = Callable[..., Any]


class GeminiTranslationEngine:
    """Online translation adapter using Gemini text generation."""

    name = "gemini_translation"
    path = TranslationPath.ONLINE

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "gemini-2.5-flash-lite",
        endpoint_template: str = (
            "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        ),
        timeout_seconds: float = 20.0,
        post_func: PostFunc | None = None,
        timeout_exceptions: tuple[type[BaseException], ...] | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint_template = endpoint_template
        self.timeout_seconds = timeout_seconds
        self._post_func = post_func
        self._timeout_exceptions = timeout_exceptions

    def translate(self, request: TranslationRequest) -> TranslationResult:
        started = time.monotonic()
        if not request.allow_online or not self.api_key:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE,
                "Gemini translation is not configured or online translation is disabled.",
                started,
            )

        try:
            response = self._post(
                self.endpoint,
                params={"key": self.api_key},
                json=self._payload(request),
                timeout=self.timeout_seconds,
            )
        except self.timeout_exceptions:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Gemini translation timed out.",
                started,
            )
        except Exception as exc:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                f"Gemini translation failed: {type(exc).__name__}",
                started,
            )

        return self._parse_response(response, request, started)

    @property
    def endpoint(self) -> str:
        return self.endpoint_template.format(model=self.model)

    @property
    def timeout_exceptions(self) -> tuple[type[BaseException], ...]:
        if self._timeout_exceptions is not None:
            return self._timeout_exceptions
        try:
            import requests

            return (requests.Timeout,)
        except Exception:  # pragma: no cover
            return (TimeoutError,)

    def _post(self, *args: Any, **kwargs: Any) -> Any:
        if self._post_func is not None:
            return self._post_func(*args, **kwargs)
        import requests

        return requests.post(*args, **kwargs)

    def _payload(self, request: TranslationRequest) -> dict[str, Any]:
        target_name = "Arabic" if request.target_language.value == "ar" else "English"
        source_name = "Arabic" if request.source_language.value == "ar" else "English"
        prompt = (
            f"Translate the following {source_name} text into {target_name}. "
            "Return only the translated text. Do not explain. Do not summarize. "
            "Preserve meaning, numbers, names, and line breaks when useful. "
            "Do not add information that is not present in the source text.\n\n"
            f"{request.source_text}"
        )
        return {"contents": [{"parts": [{"text": prompt}]}]}

    def _parse_response(
        self,
        response: Any,
        request: TranslationRequest,
        started: float,
    ) -> TranslationResult:
        status_code = int(getattr(response, "status_code", 200) or 200)
        try:
            payload = response.json()
        except Exception:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Gemini translation returned malformed JSON.",
                started,
                status_code=status_code,
            )

        if status_code >= 400:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                f"Gemini translation returned HTTP {status_code}.",
                started,
                status_code=status_code,
                provider_error_status=_provider_error_status(payload),
            )

        translated_text = _extract_text(payload)
        if translated_text is None:
            return self._failure(
                request,
                TranslationErrorCode.ONLINE_TRANSLATION_FAILED,
                "Gemini translation response did not contain text output.",
                started,
                status_code=status_code,
            )

        translated_text = translated_text.strip()
        is_valid = validate_translation_result(
            translated_text,
            source_text=request.source_text,
            target_language=request.target_language,
        )
        return TranslationResult.ok(
            source_language=request.source_language,
            target_language=request.target_language,
            translated_text=translated_text,
            engine_name=self.name,
            path=self.path,
            duration_ms=self._duration_ms(started),
            is_valid=is_valid,
            guidance="Translation is ready.",
        ).with_updates(
            provider_metadata={
                "model": self.model,
                "status_code": status_code,
            }
        )

    def _failure(
        self,
        request: TranslationRequest,
        code: TranslationErrorCode,
        message: str,
        started: float,
        *,
        status_code: int | None = None,
        provider_error_status: str | None = None,
    ) -> TranslationResult:
        metadata: dict[str, Any] = {"model": self.model}
        if status_code is not None:
            metadata["status_code"] = status_code
        if provider_error_status:
            metadata["provider_error_status"] = provider_error_status
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
            provider_metadata=metadata,
        )

    @staticmethod
    def _duration_ms(started: float) -> int:
        return int((time.monotonic() - started) * 1000)


def _extract_text(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts", [])
    if not isinstance(parts, list):
        return None
    return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))


def _provider_error_status(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    if not isinstance(error, dict):
        return None
    status = error.get("status")
    return status[:80] if isinstance(status, str) else None


__all__ = ["GeminiTranslationEngine"]
