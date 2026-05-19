"""Environment template safety tests."""

from __future__ import annotations

from pathlib import Path


def test_env_example_uses_optional_services_and_safe_defaults() -> None:
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "OCR_SPACE_API_KEY=" in content
    assert "LIBRETRANSLATE_URL=" in content
    assert "LIBRETRANSLATE_API_KEY=" in content
    assert "DEBUG_SAVE_IMAGES=false" in content
    assert "SENSITIVE_TEXT_LOGGING=false" in content
    assert "LOG_LEVEL=INFO" in content
    assert "FRAME_CAPTURE_COUNT=15" in content
    assert "paid" not in content.lower()

