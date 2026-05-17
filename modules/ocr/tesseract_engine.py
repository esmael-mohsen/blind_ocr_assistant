"""Emergency Tesseract OCR engine."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable

from modules.ocr.base import OCRBaseEngine
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest, OCRResult


Checker = Callable[[], bool]
Runner = Callable[[bytes | str, str], str]


class TesseractEngine(OCRBaseEngine):
    """Emergency OCR wrapper for Tesseract ara+eng."""

    engine_name = "tesseract"

    def __init__(
        self,
        *,
        languages: str = "ara+eng",
        executable_checker: Checker | None = None,
        language_checker: Checker | None = None,
        runner: Runner | None = None,
    ) -> None:
        self.languages = languages
        self._executable_checker = executable_checker
        self._language_checker = language_checker
        self._runner = runner

    def is_available(self) -> bool:
        return self._has_executable() and self._has_language_data()

    def recognize(self, request: OCRRequest) -> OCRResult:
        started = self.now()
        if not request.allow_offline:
            return self.failure(
                OCRErrorCode.OCR_EXECUTABLE_NOT_FOUND,
                "Emergency OCR is disabled for this request.",
                started_at=started,
            )
        if not self._has_executable():
            return self.failure(
                OCRErrorCode.OCR_EXECUTABLE_NOT_FOUND,
                "Tesseract executable was not found.",
                started_at=started,
            )
        if not self._has_language_data():
            return self.failure(
                OCRErrorCode.OCR_LANGUAGE_DATA_MISSING,
                "Tesseract Arabic/English language data is missing.",
                started_at=started,
            )

        source = self._read_image(request, started)
        if isinstance(source, OCRResult):
            return source

        try:
            text = self._run(source, self.languages)
        except Exception as exc:
            return self.failure(
                OCRErrorCode.OCR_UNEXPECTED_ERROR,
                f"Tesseract OCR failed unexpectedly: {exc}",
                started_at=started,
            )
        return self.classify_text(
            raw_text=text,
            duration_ms=self.duration_ms(started),
        )

    def _has_executable(self) -> bool:
        if self._executable_checker is not None:
            return self._executable_checker()
        return shutil.which("tesseract") is not None

    def _has_language_data(self) -> bool:
        if self._language_checker is not None:
            return self._language_checker()
        try:
            completed = subprocess.run(
                ["tesseract", "--list-langs"],
                check=False,
                text=True,
                capture_output=True,
            )
        except OSError:
            return False
        langs = set(completed.stdout.split())
        return {"ara", "eng"}.issubset(langs)

    def _read_image(self, request: OCRRequest, started: float) -> bytes | str | OCRResult:
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

    def _run(self, source: bytes | str, languages: str) -> str:
        if self._runner is not None:
            return self._runner(source, languages)
        if isinstance(source, bytes):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(source)
                source_path = tmp.name
            try:
                return self._run_subprocess(source_path, languages)
            finally:
                Path(source_path).unlink(missing_ok=True)
        return self._run_subprocess(source, languages)

    @staticmethod
    def _run_subprocess(source_path: str, languages: str) -> str:
        completed = subprocess.run(
            ["tesseract", source_path, "stdout", "-l", languages],
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "tesseract failed")
        return completed.stdout
