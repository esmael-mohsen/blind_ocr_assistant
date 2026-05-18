"""Privacy tests for Phase 6 TTS metadata."""

from __future__ import annotations

from modules.assistant.reading_controller import ReadingController
from modules.voice.tts_engine import MockTTSEngine


def test_start_reading_safe_metadata_excludes_spoken_text() -> None:
    private_text = "Patient name: Private Person. Medicine code 12345."
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)

    result = controller.start_reading(private_text, language="en")
    state = controller.get_state()

    metadata_blob = f"{result.safe_metadata} {state.safe_metadata}"
    assert private_text not in metadata_blob
    assert "Private Person" not in metadata_blob
    assert "Medicine code" not in metadata_blob
    assert "text_length" not in result.safe_metadata
    assert state.safe_metadata["is_active"] is True


def test_empty_text_guidance_does_not_log_text_snippets() -> None:
    controller = ReadingController(engine=MockTTSEngine())

    result = controller.start_reading("   ", language="en")

    assert result.success is False
    assert "   " not in str(result.safe_metadata)
    assert "guidance" not in result.safe_metadata
