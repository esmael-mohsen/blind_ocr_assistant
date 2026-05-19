"""Configuration default tests."""

from __future__ import annotations

from config import load_config


def test_config_defaults_are_safe(monkeypatch) -> None:
    for name in (
        "DEBUG_SAVE_IMAGES",
        "SENSITIVE_TEXT_LOGGING",
        "LOG_LEVEL",
        "FRAME_CAPTURE_COUNT",
        "OCR_SPACE_API_KEY",
        "LIBRETRANSLATE_URL",
        "LIBRETRANSLATE_API_KEY",
    ):
        monkeypatch.setenv(name, "")

    config = load_config()

    assert config.languages == ("ar", "en")
    assert config.online_first is True
    assert config.offline_fallback is True
    assert config.debug_save_images is False
    assert config.sensitive_text_logging is False
    assert config.log_level == "INFO"
    assert config.frame_capture_count == 15
    assert config.ocr_space_api_key == ""
    assert config.libretranslate_url == ""
    assert config.libretranslate_api_key == ""


def test_frame_capture_count_is_bounded(monkeypatch) -> None:
    monkeypatch.setenv("FRAME_CAPTURE_COUNT", "999")
    assert load_config().frame_capture_count == 20

    monkeypatch.setenv("FRAME_CAPTURE_COUNT", "-5")
    assert load_config().frame_capture_count == 1

    monkeypatch.setenv("FRAME_CAPTURE_COUNT", "not-a-number")
    assert load_config().frame_capture_count == 15

