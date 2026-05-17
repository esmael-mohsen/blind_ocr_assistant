"""Local accuracy OCR engine tests."""

from __future__ import annotations

import subprocess
import sys

from modules.ocr.ocr_models import OCRErrorCode, OCRRequest
from modules.ocr.paddle_ocr_engine import PaddleOCREngine


class FakePaddleFactory:
    def __init__(self, result):
        self.calls = 0
        self.result = result

    def __call__(self):
        self.calls += 1
        return self

    def ocr(self, _image, cls=True):
        return self.result


def test_engine_does_not_load_model_until_recognize() -> None:
    factory = FakePaddleFactory([[["box", ("Lazy text", 0.95)]]])
    engine = PaddleOCREngine(model_factory=factory)

    assert engine.model_loaded is False
    assert factory.calls == 0


def test_mocked_success_loads_model_once_and_maps_result() -> None:
    factory = FakePaddleFactory([[["box", ("Paddle text", 0.95)]]])
    engine = PaddleOCREngine(model_factory=factory)

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))

    assert result.success is True
    assert result.raw_text == "Paddle text"
    assert result.confidence == 0.95
    assert factory.calls == 1


def test_model_load_failure_returns_structured_failure() -> None:
    def fail_factory():
        raise RuntimeError("model missing")

    engine = PaddleOCREngine(model_factory=fail_factory)

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MODEL_LOAD_ERROR


def test_empty_and_weak_output_are_failures() -> None:
    empty_engine = PaddleOCREngine(model_factory=FakePaddleFactory([]))
    weak_engine = PaddleOCREngine(model_factory=FakePaddleFactory([[["box", ("@@@", 0.2)]]]))

    empty = empty_engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))
    weak = weak_engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=True))

    assert empty.error_code == OCRErrorCode.NO_TEXT_DETECTED
    assert weak.error_code == OCRErrorCode.WEAK_OCR_RESULT


def test_allow_offline_false_returns_model_load_error() -> None:
    engine = PaddleOCREngine(model_factory=FakePaddleFactory([[["box", ("text", 0.9)]]]))

    result = engine.recognize(OCRRequest(image_bytes=b"image", allow_offline=False))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MODEL_LOAD_ERROR


def test_project_import_and_help_do_not_load_paddle_module() -> None:
    code = (
        "import sys; "
        "import main; "
        "\ntry:\n"
        "    main.main(['--help'])\n"
        "except SystemExit:\n"
        "    pass\n"
        "print('paddleocr' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip().endswith("False")
