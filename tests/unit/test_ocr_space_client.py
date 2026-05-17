"""Online OCR client tests."""

from __future__ import annotations

from modules.ocr.ocr_models import OCRErrorCode, OCRRequest
from modules.ocr.ocr_space_client import OCRSpaceClient


class FakeTimeout(Exception):
    pass


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


def test_missing_credential_returns_structured_failure() -> None:
    client = OCRSpaceClient(api_key="")

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MISSING_CREDENTIAL


def test_online_engine_requires_allow_online() -> None:
    client = OCRSpaceClient(api_key="free")

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=False))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MISSING_CREDENTIAL


def test_mocked_success_response_excludes_raw_text_from_metadata() -> None:
    def post(*_args, **_kwargs):
        return FakeResponse(
            {
                "IsErroredOnProcessing": False,
                "ParsedResults": [{"ParsedText": "Hello OCR"}],
            }
        )

    client = OCRSpaceClient(api_key="free", post_func=post)

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is True
    assert result.raw_text == "Hello OCR"
    assert "Hello OCR" not in str(result.metadata)


def test_malformed_response_returns_failure() -> None:
    client = OCRSpaceClient(api_key="free", post_func=lambda *_args, **_kwargs: FakeResponse({}))

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_MALFORMED_RESPONSE


def test_timeout_retries_once_then_fails() -> None:
    calls = {"count": 0}

    def post(*_args, **_kwargs):
        calls["count"] += 1
        raise FakeTimeout("timeout")

    client = OCRSpaceClient(
        api_key="free",
        retry_count=1,
        post_func=post,
        timeout_exceptions=(FakeTimeout,),
    )

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert calls["count"] == 2
    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_PROVIDER_TIMEOUT


def test_transient_timeout_can_succeed_on_retry() -> None:
    calls = {"count": 0}

    def post(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise FakeTimeout("timeout")
        return FakeResponse(
            {
                "IsErroredOnProcessing": False,
                "ParsedResults": [{"ParsedText": "Retry success"}],
            }
        )

    client = OCRSpaceClient(
        api_key="free",
        retry_count=1,
        post_func=post,
        timeout_exceptions=(FakeTimeout,),
    )

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is True
    assert result.raw_text == "Retry success"
    assert calls["count"] == 2


def test_provider_error_returns_failure() -> None:
    client = OCRSpaceClient(
        api_key="free",
        post_func=lambda *_args, **_kwargs: FakeResponse(
            {"IsErroredOnProcessing": True, "ErrorMessage": ["bad image"]}
        ),
    )

    result = client.recognize(OCRRequest(image_bytes=b"image", allow_online=True))

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_PROVIDER_ERROR


def test_missing_image_path_returns_failure(tmp_path) -> None:
    client = OCRSpaceClient(api_key="free")

    result = client.recognize(
        OCRRequest(image_path=tmp_path / "missing.png", allow_online=True)
    )

    assert result.success is False
    assert result.error_code == OCRErrorCode.OCR_IMAGE_NOT_FOUND
