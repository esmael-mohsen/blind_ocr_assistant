"""Free online OCR engine client."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from config import DEFAULT_OCR_RETRY_COUNT, DEFAULT_OCR_TIMEOUT_SECONDS
from modules.ocr.base import OCRBaseEngine
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest, OCRResult


PostFunc = Callable[..., Any]


class OCRSpaceClient(OCRBaseEngine):
    """Client for the free OCR.space OCR path."""

    engine_name = "ocr_space"

    def __init__(
        self,
        *,
        api_key: str = "",
        endpoint: str = "https://api.ocr.space/parse/image",
        timeout_seconds: float = DEFAULT_OCR_TIMEOUT_SECONDS,
        retry_count: int = DEFAULT_OCR_RETRY_COUNT,
        post_func: PostFunc | None = None,
        timeout_exceptions: tuple[type[BaseException], ...] | None = None,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.retry_count = max(0, retry_count)
        self._post_func = post_func
        self._timeout_exceptions = timeout_exceptions

    def is_available(self) -> bool:
        return bool(self.api_key)

    def recognize(self, request: OCRRequest) -> OCRResult:
        started = self.now()
        if not request.allow_online or not self.api_key:
            return self.failure(
                OCRErrorCode.OCR_MISSING_CREDENTIAL,
                "Free online OCR credential is not configured or online OCR is disabled.",
                started_at=started,
            )

        image_result = self._read_image(request, started)
        if isinstance(image_result, OCRResult):
            return image_result

        attempts = self.retry_count + 1
        last_timeout: BaseException | None = None
        for attempt in range(attempts):
            try:
                response = self._post(
                    files={"file": ("image", image_result)},
                    data={"apikey": self.api_key, "language": "ara,eng"},
                    timeout=request.timeout_seconds or self.timeout_seconds,
                )
                return self._parse_response(response, started, attempt=attempt)
            except self.timeout_exceptions as exc:
                last_timeout = exc
                continue
            except Exception as exc:  # pragma: no cover - defensive provider path
                return self.failure(
                    OCRErrorCode.OCR_PROVIDER_ERROR,
                    f"Online OCR provider request failed: {exc}",
                    started_at=started,
                )

        return self.failure(
            OCRErrorCode.OCR_PROVIDER_TIMEOUT,
            f"Online OCR provider timed out: {last_timeout}",
            started_at=started,
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
        if self._post_func is not None:
            return self._post_func(self.endpoint, **kwargs)
        import requests

        return requests.post(self.endpoint, **kwargs)

    def _read_image(self, request: OCRRequest, started: float) -> bytes | OCRResult:
        if request.image_bytes is not None:
            return request.image_bytes
        path = Path(request.image_path or "")
        if not path.exists():
            return self.failure(
                OCRErrorCode.OCR_IMAGE_NOT_FOUND,
                f"OCR image was not found: {path}",
                started_at=started,
            )
        return path.read_bytes()

    def _parse_response(self, response: Any, started: float, *, attempt: int) -> OCRResult:
        try:
            payload = response.json()
        except Exception:
            return self.failure(
                OCRErrorCode.OCR_MALFORMED_RESPONSE,
                "Online OCR provider returned malformed JSON.",
                started_at=started,
            )

        if not isinstance(payload, dict) or "IsErroredOnProcessing" not in payload:
            return self.failure(
                OCRErrorCode.OCR_MALFORMED_RESPONSE,
                "Online OCR provider response was missing required fields.",
                started_at=started,
            )

        if payload.get("IsErroredOnProcessing"):
            message = payload.get("ErrorMessage") or payload.get("ErrorDetails")
            return self.failure(
                OCRErrorCode.OCR_PROVIDER_ERROR,
                f"Online OCR provider error: {message}",
                started_at=started,
            )

        parsed_results = payload.get("ParsedResults")
        if not isinstance(parsed_results, list) or not parsed_results:
            return self.failure(
                OCRErrorCode.OCR_MALFORMED_RESPONSE,
                "Online OCR provider response did not contain parsed text.",
                started_at=started,
            )
        text = "\n".join(str(item.get("ParsedText", "")) for item in parsed_results)
        return self.classify_text(
            raw_text=text,
            duration_ms=self.duration_ms(started),
            metadata={"attempt": attempt + 1},
        )
