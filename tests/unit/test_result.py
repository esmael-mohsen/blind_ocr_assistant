"""Operation Result helper tests."""

from __future__ import annotations

import pytest

from modules.common.result import Result, fail, ok


def test_ok_result_contains_value_and_message() -> None:
    result = ok({"ready": True}, "ready")

    assert result.success is True
    assert result.value == {"ready": True}
    assert result.error_code is None
    assert result.message == "ready"


def test_fail_result_requires_error_code() -> None:
    result = fail("BOOTSTRAP_FAILED", "bootstrap failed")

    assert result.success is False
    assert result.value is None
    assert result.error_code == "BOOTSTRAP_FAILED"
    assert result.message == "bootstrap failed"


def test_fail_result_rejects_missing_error_code() -> None:
    with pytest.raises(ValueError):
        Result.fail("", "missing code")

