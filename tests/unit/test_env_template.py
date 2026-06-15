"""Environment template safety tests."""

from __future__ import annotations

from pathlib import Path


def test_env_example_uses_optional_services_and_safe_defaults() -> None:
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "OCR_SPACE_API_KEY=" in content
    assert "LIBRETRANSLATE_URL=" in content
    assert "LIBRETRANSLATE_API_KEY=" in content
    assert "GEMINI_API_KEY=" in content
    assert "DEBUG_SAVE_IMAGES=false" in content
    assert "SENSITIVE_TEXT_LOGGING=false" in content
    assert "LOG_LEVEL=INFO" in content
    assert "FRAME_CAPTURE_COUNT=15" in content
    assert "ASSISTANT_CAMERA_INDEX=0" in content
    assert "ASSISTANT_CAMERA_SOURCE=" in content
    assert "ASSISTANT_VOICE_ENABLED=true" in content
    assert "ASSISTANT_MICROPHONE_INDEX=" in content
    assert "ASSISTANT_RUNTIME_MODE=laptop" in content
    assert "ASSISTANT_SHOW_WINDOW=true" in content
    assert "ASSISTANT_AUDIO_CUES_ENABLED=true" in content
    assert "ASSISTANT_GUIDED_CAPTURE_ENABLED=true" in content
    assert "ASSISTANT_TTS_PROVIDER=auto" in content
    assert "ASSISTANT_STT_PROVIDER=auto" in content
    assert "ASSISTANT_FRAME_ANALYSIS_INTERVAL_SECONDS=0.35" in content
    assert "ASSISTANT_STABLE_TEXT_FRAMES=3" in content
    assert "ASSISTANT_TEXT_CONFIDENCE_THRESHOLD=0.55" in content
    assert "ASSISTANT_CAPTURE_OVERRIDE_ENABLED=true" in content
    assert "ASSISTANT_QUIET_MODE=false" in content
    assert "ASSISTANT_VOICE_REPLY_STYLE=normal" in content
    assert "ASSISTANT_WELCOME_LANGUAGE=auto" in content
    assert "ASSISTANT_COMMAND_CONFIRM_EXIT=true" in content
    assert "ASSISTANT_TERMINAL_LOGS_ENABLED=true" in content
    assert "ASSISTANT_VOICE_TRANSCRIPT_LOGS_ENABLED=false" in content
    assert "ASSISTANT_GEMINI_OCR_ENABLED=true" in content
    assert "ASSISTANT_GEMINI_OCR_MODEL=gemini-2.5-flash-lite" in content
    assert "ASSISTANT_GEMINI_OCR_TIMEOUT_SECONDS=20" in content
    assert "ASSISTANT_GEMINI_OCR_FALLBACK_LOCAL=true" in content
    assert "ASSISTANT_GEMINI_TRANSLATION_ENABLED=true" in content
    assert "ASSISTANT_GEMINI_TRANSLATION_MODEL=gemini-2.5-flash-lite" in content
    assert "ASSISTANT_GEMINI_TRANSLATION_TIMEOUT_SECONDS=20" in content
    assert "paid" not in content.lower()
