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
        "GEMINI_API_KEY",
        "ASSISTANT_GEMINI_OCR_ENABLED",
        "ASSISTANT_GEMINI_OCR_MODEL",
        "ASSISTANT_GEMINI_OCR_TIMEOUT_SECONDS",
        "ASSISTANT_GEMINI_OCR_FALLBACK_LOCAL",
        "ASSISTANT_GEMINI_TRANSLATION_ENABLED",
        "ASSISTANT_GEMINI_TRANSLATION_MODEL",
        "ASSISTANT_GEMINI_TRANSLATION_TIMEOUT_SECONDS",
        "ASSISTANT_CAMERA_SOURCE",
        "ASSISTANT_MICROPHONE_INDEX",
        "ASSISTANT_VOICE_REPLY_STYLE",
        "ASSISTANT_WELCOME_LANGUAGE",
        "ASSISTANT_COMMAND_CONFIRM_EXIT",
        "ASSISTANT_VOICE_TRANSCRIPT_LOGS_ENABLED",
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
    assert config.gemini_api_key == ""
    assert config.assistant_gemini_ocr_enabled is True
    assert config.assistant_gemini_ocr_model == "gemini-2.5-flash-lite"
    assert config.assistant_gemini_ocr_timeout_seconds == 20.0
    assert config.assistant_gemini_ocr_fallback_local is True
    assert config.assistant_gemini_translation_enabled is True
    assert config.assistant_gemini_translation_model == "gemini-2.5-flash-lite"
    assert config.assistant_gemini_translation_timeout_seconds == 20.0
    assert config.assistant_camera_source == ""
    assert config.assistant_camera_index == 0
    assert config.assistant_voice_enabled is True
    assert config.assistant_microphone_index is None
    assert config.assistant_runtime_mode == "laptop"
    assert config.assistant_show_window is True
    assert config.assistant_default_language == "auto"
    assert config.assistant_audio_cues_enabled is True
    assert config.assistant_guided_capture_enabled is True
    assert config.assistant_guided_capture_timeout_seconds == 8.0
    assert config.assistant_tts_provider == "auto"
    assert config.assistant_stt_provider == "auto"
    assert config.assistant_frame_analysis_interval_seconds == 0.35
    assert config.assistant_stable_text_frames == 3
    assert config.assistant_text_confidence_threshold == 0.55
    assert config.assistant_guidance_cooldown_seconds == 3.0
    assert config.assistant_capture_override_enabled is True
    assert config.assistant_quiet_mode is False
    assert config.assistant_voice_reply_style == "normal"
    assert config.assistant_welcome_language == "auto"
    assert config.assistant_command_confirm_exit is True
    assert config.assistant_terminal_logs_enabled is True
    assert config.assistant_voice_transcript_logs_enabled is False


def test_frame_capture_count_is_bounded(monkeypatch) -> None:
    monkeypatch.setenv("FRAME_CAPTURE_COUNT", "999")
    assert load_config().frame_capture_count == 20

    monkeypatch.setenv("FRAME_CAPTURE_COUNT", "-5")
    assert load_config().frame_capture_count == 1

    monkeypatch.setenv("FRAME_CAPTURE_COUNT", "not-a-number")
    assert load_config().frame_capture_count == 15


def test_assistant_camera_source_can_be_droidcam_url(monkeypatch) -> None:
    monkeypatch.setenv("ASSISTANT_CAMERA_SOURCE", "http://192.168.1.4:4747/video")

    assert load_config().assistant_camera_source == "http://192.168.1.4:4747/video"


def test_voice_reply_style_and_welcome_language_are_bounded(monkeypatch) -> None:
    monkeypatch.setenv("ASSISTANT_VOICE_REPLY_STYLE", "verbose")
    monkeypatch.setenv("ASSISTANT_WELCOME_LANGUAGE", "ar")
    assert load_config().assistant_voice_reply_style == "verbose"
    assert load_config().assistant_welcome_language == "ar"

    monkeypatch.setenv("ASSISTANT_VOICE_REPLY_STYLE", "loud")
    monkeypatch.setenv("ASSISTANT_WELCOME_LANGUAGE", "fr")
    assert load_config().assistant_voice_reply_style == "normal"
    assert load_config().assistant_welcome_language == "auto"
