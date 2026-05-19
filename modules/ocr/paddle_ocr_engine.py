"""Local accuracy OCR engine with lazy loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from modules.ocr.base import OCRBaseEngine
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest, OCRResult

ModelFactory = Callable[[], Any]


class PaddleOCREngine(OCRBaseEngine):
    """PaddleOCR wrapper that avoids heavy import/model load until first use."""

    engine_name = "paddleocr"

    def __init__(self, *, model_factory: ModelFactory | None = None) -> None:
        self._model_factory = model_factory
        self._model: Any | None = None

    @property
    def model_loaded(self) -> bool:
        return self._model is not None

    def is_available(self) -> bool:
        if self._model_factory is not None:
            return True
        try:
            import importlib.util

            return importlib.util.find_spec("paddleocr") is not None
        except Exception:
            return False

    def recognize(self, request: OCRRequest) -> OCRResult:
        started = self.now()
        if not request.allow_offline:
            return self.failure(
                OCRErrorCode.OCR_MODEL_LOAD_ERROR,
                "Offline local accuracy OCR is disabled for this request.",
                started_at=started,
            )

        image_result = self._read_image(request, started)
        if isinstance(image_result, OCRResult):
            return image_result

        try:
            model = self._load_model()
            raw_result = model.ocr(image_result, cls=True)
        except Exception as exc:
            return self.failure(
                OCRErrorCode.OCR_MODEL_LOAD_ERROR,
                f"Local accuracy OCR model could not run: {exc}",
                started_at=started,
            )

        text, confidence = self._extract_text(raw_result)
        return self.classify_text(
            raw_text=text,
            duration_ms=self.duration_ms(started),
            confidence=confidence,
        )

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self._model_factory is not None:
            self._model = self._model_factory()
            return self._model

        from paddleocr import PaddleOCR  # type: ignore

        self._model = PaddleOCR(use_textline_orientation=True, lang="ar")
        return self._model

    def _read_image(
        self, request: OCRRequest, started: float
    ) -> bytes | str | OCRResult:
        if request.image_bytes is not None:
            return request.image_bytes
        path = Path(request.image_path or "")
        if not path.exists():
            return self.failure(
                OCRErrorCode.OCR_IMAGE_NOT_FOUND,
                f"OCR image was not found: {path}",
                started_at=started,
            )
        return str(path)

    @staticmethod
    def _extract_text(raw_result: Any) -> tuple[str, float | None]:
        texts: list[str] = []
        confidences: list[float] = []
        for page in raw_result or []:
            for item in page or []:
                if len(item) < 2:
                    continue
                value = item[1]
                if isinstance(value, (tuple, list)) and value:
                    texts.append(str(value[0]))
                    if len(value) > 1:
                        try:
                            confidences.append(float(value[1]))
                        except (TypeError, ValueError):
                            pass
        confidence = sum(confidences) / len(confidences) if confidences else None
        return "\n".join(texts), confidence
