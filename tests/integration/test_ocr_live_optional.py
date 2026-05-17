"""Optional live OCR tests."""

from __future__ import annotations

import os

import pytest

from modules.ocr.ocr_models import OCRRequest
from modules.ocr.ocr_space_client import OCRSpaceClient


@pytest.mark.live_ocr
def test_live_ocr_space_is_opt_in() -> None:
    api_key = os.getenv("OCR_SPACE_API_KEY", "")
    if not api_key:
        pytest.skip("OCR_SPACE_API_KEY is not configured; live OCR is opt-in")

    client = OCRSpaceClient(api_key=api_key)
    result = client.recognize(
        OCRRequest(image_bytes=b"not-a-real-image", allow_online=True)
    )

    assert result.engine_name == "ocr_space"
