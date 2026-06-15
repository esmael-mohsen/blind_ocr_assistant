"""Phase 4 OCR cascade routing tests."""

from __future__ import annotations

from modules.ocr.ocr_cascade import (
    AttemptStatus,
    OCRCascadeErrorCode,
    OCRCascadeRequest,
    run_ocr_cascade,
)
from modules.ocr.ocr_models import OCRErrorCode, OCRRequest, OCRResult


class FakeEngine:
    def __init__(self, engine_name: str, results: list[OCRResult], available: bool = True):
        self.engine_name = engine_name
        self.results = list(results)
        self.available = available
        self.calls = 0

    def is_available(self) -> bool:
        return self.available

    def recognize(self, request: OCRRequest) -> OCRResult:
        self.calls += 1
        if self.results:
            return self.results.pop(0)
        return OCRResult.failure_result(
            engine_name=self.engine_name,
            error_code=OCRErrorCode.OCR_UNEXPECTED_ERROR,
            error_message="no mocked result",
            duration_ms=1,
        )


def _success(
    engine: str,
    text: str = "Readable text for OCR cascade",
    *,
    duration_ms: int = 10,
    quality_score: float | None = None,
) -> OCRResult:
    return OCRResult.success_result(
        engine_name=engine,
        raw_text=text,
        duration_ms=duration_ms,
        quality_score=quality_score,
    )


def _failure(engine: str, code: OCRErrorCode = OCRErrorCode.WEAK_OCR_RESULT) -> OCRResult:
    return OCRResult.failure_result(
        engine_name=engine,
        error_code=code,
        error_message=code.value,
        duration_ms=10,
    )


def _engines(
    online: OCRResult,
    local: OCRResult | None = None,
    emergency: OCRResult | None = None,
) -> dict[str, FakeEngine]:
    return {
        "online": FakeEngine("ocr_space", [online]),
        "local": FakeEngine("paddleocr", [local or _success("paddleocr")]),
        "emergency": FakeEngine("tesseract", [emergency or _success("tesseract")]),
    }


def test_good_online_result_is_accepted_without_fallback() -> None:
    engines = _engines(_success("ocr_space"))

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image"), engines)

    assert result.success is True
    assert result.selected_engine == "ocr_space"
    assert result.fallback_used is False
    assert engines["online"].calls == 1
    assert engines["local"].calls == 0
    assert engines["emergency"].calls == 0


def test_gemini_primary_result_is_accepted_before_local_fallbacks() -> None:
    engines = {
        "gemini": FakeEngine("gemini", [_success("gemini", "Arabic text is readable")]),
        "local": FakeEngine("paddleocr", [_success("paddleocr")]),
        "emergency": FakeEngine("tesseract", [_success("tesseract")]),
    }

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image"),
        engines,
        preferred_online_engine="gemini",
    )

    assert result.success is True
    assert result.selected_engine == "gemini"
    assert result.fallback_used is False
    assert engines["gemini"].calls == 1
    assert engines["local"].calls == 0
    assert engines["emergency"].calls == 0


def test_weak_gemini_result_triggers_local_accuracy_fallback() -> None:
    engines = {
        "gemini": FakeEngine("gemini", [_success("gemini", "A")]),
        "local": FakeEngine("paddleocr", [_success("paddleocr", "Local result is readable")]),
        "emergency": FakeEngine("tesseract", [_success("tesseract")]),
    }

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image"),
        engines,
        preferred_online_engine="gemini",
    )

    assert result.success is True
    assert result.selected_engine == "paddleocr"
    assert result.fallback_used is True
    assert [attempt.engine_name for attempt in result.attempts] == ["gemini", "paddleocr"]


def test_weak_online_result_triggers_local_accuracy_fallback() -> None:
    engines = _engines(
        _success("ocr_space", "A"),
        local=_success("paddleocr", "Local result is readable"),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image"), engines)

    assert result.success is True
    assert result.selected_engine == "paddleocr"
    assert result.fallback_used is True
    assert [attempt.engine_name for attempt in result.attempts] == ["ocr_space", "paddleocr"]
    assert result.attempts[0].status == AttemptStatus.WEAK


def test_weak_local_result_triggers_emergency_fallback() -> None:
    engines = _engines(
        _success("ocr_space", "A"),
        local=_success("paddleocr", "B"),
        emergency=_success("tesseract", "Emergency OCR result is readable"),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image"), engines)

    assert result.success is True
    assert result.selected_engine == "tesseract"
    assert [attempt.engine_name for attempt in result.attempts] == [
        "ocr_space",
        "paddleocr",
        "tesseract",
    ]


def test_all_engines_failed_returns_structured_failure() -> None:
    engines = _engines(
        _failure("ocr_space"),
        local=_failure("paddleocr"),
        emergency=_failure("tesseract"),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image"), engines)

    assert result.success is False
    assert result.error is not None
    assert result.error.error_code == OCRCascadeErrorCode.ALL_OCR_ENGINES_FAILED
    assert "try again" in result.guidance.lower()


def test_skips_online_ocr_when_online_availability_check_is_unavailable() -> None:
    engines = _engines(
        _success("ocr_space"),
        local=_success("paddleocr", "Local offline OCR is readable"),
    )

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image"),
        engines,
        online_status_provider=lambda: False,
    )

    assert result.success is True
    assert result.offline_route_used is True
    assert result.selected_engine == "paddleocr"
    assert engines["online"].calls == 0
    assert result.attempts[0].engine_name == "ocr_space"
    assert result.attempts[0].status == AttemptStatus.SKIPPED
    assert result.attempts[0].error_code == OCRCascadeErrorCode.ONLINE_OCR_UNAVAILABLE


def test_skips_online_ocr_when_allow_online_is_false() -> None:
    engines = _engines(
        _success("ocr_space"),
        local=_success("paddleocr", "Local-only route is readable"),
    )

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image", allow_online=False),
        engines,
    )

    assert result.success is True
    assert result.offline_route_used is True
    assert result.selected_engine == "paddleocr"
    assert engines["online"].calls == 0
    assert engines["local"].calls == 1


def test_online_availability_timeout_routes_to_local_accuracy_fallback() -> None:
    engines = _engines(
        _success("ocr_space"),
        local=_success("paddleocr", "Local timeout fallback is readable"),
    )

    def unavailable() -> bool:
        raise TimeoutError("availability check timed out")

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image"),
        engines,
        online_status_provider=unavailable,
    )

    assert result.success is True
    assert result.offline_route_used is True
    assert result.selected_engine == "paddleocr"
    assert engines["online"].calls == 0
    assert result.attempts[0].error_code == OCRCascadeErrorCode.ONLINE_OCR_TIMEOUT


def test_local_accuracy_failure_offline_triggers_emergency_ocr() -> None:
    engines = _engines(
        _success("ocr_space"),
        local=_failure("paddleocr"),
        emergency=_success("tesseract", "Emergency offline OCR is readable"),
    )

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image", allow_online=False),
        engines,
    )

    assert result.success is True
    assert result.offline_route_used is True
    assert result.selected_engine == "tesseract"
    assert engines["online"].calls == 0
    assert engines["local"].calls == 1
    assert engines["emergency"].calls == 1


def test_each_allowed_engine_is_attempted_at_most_once_per_cascade_request() -> None:
    engines = _engines(
        _success("ocr_space", "A"),
        local=_success("paddleocr", "B"),
        emergency=_success("tesseract", "C"),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image"), engines)

    assert result.success is False
    assert engines["online"].calls == 1
    assert engines["local"].calls == 1
    assert engines["emergency"].calls == 1


def test_high_accuracy_compares_online_primary_and_local_before_selection() -> None:
    engines = _engines(
        _success("ocr_space", "Online candidate text", quality_score=0.78),
        local=_success("paddleocr", "Local candidate text", quality_score=0.88),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image", high_accuracy=True), engines)

    assert result.success is True
    assert result.high_accuracy_used is True
    assert result.selected_engine == "paddleocr"
    assert engines["online"].calls == 1
    assert engines["local"].calls == 1
    assert engines["emergency"].calls == 0


def test_high_accuracy_selects_higher_quality_acceptable_result() -> None:
    engines = _engines(
        _success("ocr_space", "Online high quality text", quality_score=0.94),
        local=_success("paddleocr", "Local lower quality text", quality_score=0.80),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image", high_accuracy=True), engines)

    assert result.success is True
    assert result.selected_engine == "ocr_space"
    assert result.quality_report is not None
    assert result.quality_report.quality_score == 0.94


def test_high_accuracy_prefers_local_when_scores_are_similar() -> None:
    engines = _engines(
        _success("ocr_space", "Online similar quality text", quality_score=0.90),
        local=_success("paddleocr", "Local similar quality text", quality_score=0.87),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image", high_accuracy=True), engines)

    assert result.success is True
    assert result.selected_engine == "paddleocr"


def test_high_accuracy_uses_shorter_duration_as_final_tie_breaker() -> None:
    engines = _engines(
        _success("ocr_space", "Online equal score text", duration_ms=45, quality_score=0.86),
        local=_success("paddleocr", "Local equal score text", duration_ms=12, quality_score=0.86),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image", high_accuracy=True), engines)

    assert result.success is True
    assert result.selected_result is not None
    assert result.selected_result.duration_ms == 12


def test_high_accuracy_attempts_emergency_only_when_compared_candidates_are_weak() -> None:
    engines = _engines(
        _success("ocr_space", "A", quality_score=0.20),
        local=_success("paddleocr", "B", quality_score=0.20),
        emergency=_success("tesseract", "Emergency candidate text", quality_score=0.82),
    )

    result = run_ocr_cascade(OCRCascadeRequest(image=b"image", high_accuracy=True), engines)

    assert result.success is True
    assert result.selected_engine == "tesseract"
    assert engines["emergency"].calls == 1


def test_high_accuracy_offline_skips_online_comparison_and_uses_local_candidates() -> None:
    engines = _engines(
        _success("ocr_space", "Online should not run", quality_score=0.99),
        local=_success("paddleocr", "Local offline high accuracy text", quality_score=0.80),
    )

    result = run_ocr_cascade(
        OCRCascadeRequest(image=b"image", high_accuracy=True, allow_online=False),
        engines,
    )

    assert result.success is True
    assert result.offline_route_used is True
    assert result.high_accuracy_used is True
    assert result.selected_engine == "paddleocr"
    assert engines["online"].calls == 0
    assert engines["local"].calls == 1
