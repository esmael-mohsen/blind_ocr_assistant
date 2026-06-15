"""Gemini OCR engine using inline image understanding."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Callable

from config import DEFAULT_OCR_TIMEOUT_SECONDS
from modules.ocr.base import OCRBaseEngine
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest, OCRResult


PostFunc = Callable[..., Any]

GEMINI_OCR_PROMPT = (
    "Extract only the visible printed text from this image. "
    "Support Arabic, English, and mixed Arabic-English text. "
    "Do not translate. Do not explain. Do not summarize. "
    "Do not invent missing words. Preserve line breaks when useful. "
    "If there is no readable text, return an empty response."
)


class GeminiOCREngine(OCRBaseEngine):
    """OCR adapter for Gemini image understanding."""

    engine_name = "gemini"

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "gemini-2.5-flash-lite",
        endpoint_template: str = (
            "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        ),
        timeout_seconds: float = DEFAULT_OCR_TIMEOUT_SECONDS,
        post_func: PostFunc | None = None,
        timeout_exceptions: tuple[type[BaseException], ...] | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint_template = endpoint_template
        self.timeout_seconds = timeout_seconds
        self._post_func = post_func
        self._timeout_exceptions = timeout_exceptions

    def is_available(self) -> bool:
        return bool(self.api_key)

    def recognize(self, request: OCRRequest) -> OCRResult:
        started = self.now()
        if not request.allow_online or not self.api_key:
            return self.failure(
                OCRErrorCode.OCR_MISSING_CREDENTIAL,
                "Gemini OCR credential is not configured or online OCR is disabled.",
                started_at=started,
                metadata=self._metadata(),
            )

        image_result = self._read_image(request, started)
        if isinstance(image_result, OCRResult):
            return image_result

        try:
            response = self._post(
                self.endpoint,
                params={"key": self.api_key},
                json=self._payload(image_result),
                timeout=request.timeout_seconds or self.timeout_seconds,
            )
        except self.timeout_exceptions as exc:
            return self.failure(
                OCRErrorCode.OCR_PROVIDER_TIMEOUT,
                f"Gemini OCR provider timed out: {exc}",
                started_at=started,
                metadata=self._metadata(),
            )
        except Exception as exc:  # pragma: no cover - defensive provider path
            return self.failure(
                OCRErrorCode.OCR_PROVIDER_ERROR,
                f"Gemini OCR provider request failed: {exc}",
                started_at=started,
                metadata=self._metadata(),
            )

        return self._parse_response(response, started)

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
        except Exception:  # pragma: no cover - requests should usually exist
            return (TimeoutError,)

    def _post(self, *args: Any, **kwargs: Any) -> Any:
        if self._post_func is not None:
            return self._post_func(*args, **kwargs)
        import requests

        return requests.post(*args, **kwargs)

    def _read_image(self, request: OCRRequest, started: float) -> bytes | OCRResult:
        if request.image_bytes is not None:
            return request.image_bytes
        path = Path(request.image_path or "")
        if not path.exists():
            return self.failure(
                OCRErrorCode.OCR_IMAGE_NOT_FOUND,
                f"OCR image was not found: {path}",
                started_at=started,
                metadata=self._metadata(),
            )
        return path.read_bytes()

    def _payload(self, image_bytes: bytes) -> dict[str, Any]:
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": _detect_mime_type(image_bytes),
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                        {"text": GEMINI_OCR_PROMPT},
                    ]
                }
            ]
        }

    def _parse_response(self, response: Any, started: float) -> OCRResult:
        status_code = int(getattr(response, "status_code", 200) or 200)
        try:
            payload = response.json()
        except Exception:
            return self.failure(
                OCRErrorCode.OCR_MALFORMED_RESPONSE,
                "Gemini OCR provider returned malformed JSON.",
                started_at=started,
                metadata=self._metadata(status_code=status_code),
            )

        if status_code >= 400:
            return self.failure(
                OCRErrorCode.OCR_PROVIDER_ERROR,
                f"Gemini OCR provider returned HTTP {status_code}.",
                started_at=started,
                metadata=self._metadata(
                    status_code=status_code,
                    provider_error_status=_provider_error_status(payload),
                ),
            )

        text = _extract_text(payload)
        if text is None:
            return self.failure(
                OCRErrorCode.OCR_MALFORMED_RESPONSE,
                "Gemini OCR provider response did not contain text output.",
                started_at=started,
                metadata=self._metadata(status_code=status_code),
            )
        return self.classify_text(
            raw_text=text,
            duration_ms=self.duration_ms(started),
            metadata=self._metadata(status_code=status_code),
        )

    def _metadata(
        self,
        *,
        status_code: int | None = None,
        provider_error_status: str | None = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {"model": self.model}
        if status_code is not None:
            metadata["status_code"] = status_code
        if provider_error_status:
            metadata["provider_error_status"] = provider_error_status
        return metadata


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
    if not isinstance(status, str):
        return None
    return status[:80]


def _detect_mime_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


__all__ = ["GEMINI_OCR_PROMPT", "GeminiOCREngine"]
