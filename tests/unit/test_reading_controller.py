"""Tests for Phase 6 reading controller behavior."""

from __future__ import annotations

from modules.assistant.reading_controller import ReadingController
from modules.voice.tts_engine import MockTTSEngine
from modules.voice.voice_models import (
    SpeechOperation,
    TTSErrorCode,
)


def test_start_reading_speaks_clean_arabic_text_and_sets_active_state() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)

    result = controller.start_reading("هذا نص جاهز للقراءة.", language="ar")

    assert result.success is True
    assert engine.spoken_requests[0].text == "هذا نص جاهز للقراءة."
    assert engine.spoken_requests[0].language == "ar"
    state = controller.get_state()
    assert state.is_active is True
    assert state.is_paused is False
    assert state.last_operation == SpeechOperation.READ_ALL


def test_start_reading_speaks_clean_english_text() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)

    result = controller.start_reading("Clean text is ready.", language="en")

    assert result.success is True
    assert engine.spoken_requests[0].text == "Clean text is ready."
    assert engine.spoken_requests[0].language == "en"


def test_start_reading_preserves_mixed_logical_order() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    text = "Take one tablet daily. الجرعة بعد الطعام."

    result = controller.start_reading(text, language="mixed")

    assert result.success is True
    assert "Take one tablet daily." in engine.spoken_requests[0].text
    assert engine.spoken_requests[0].language == "en"
    assert engine.spoken_requests[1].language == "ar"


def test_start_reading_mixed_text_even_when_detected_as_english() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    text = "TOTAL PLUS\nجرعة يومية"

    result = controller.start_reading(text, language="en")

    assert result.success is True
    assert [request.language for request in engine.spoken_requests] == ["en", "ar"]


def test_arabic_reading_with_english_abbreviations_uses_one_arabic_tts_request() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    text = "هذا شرح عن IR و NLP في المحاضرة."

    result = controller.start_reading(text, language="ar")

    assert result.success is True
    assert len(engine.spoken_requests) == 1
    assert engine.spoken_requests[0].text == text
    assert engine.spoken_requests[0].language == "ar"


def test_start_reading_empty_text_returns_guidance_without_engine_call() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)

    result = controller.start_reading("   ", language="en")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TTSErrorCode.NO_READABLE_TEXT
    assert engine.spoken_requests == []
    assert controller.get_state().is_active is False


def test_start_reading_engine_failure_leaves_inactive_state() -> None:
    engine = MockTTSEngine(fail_next_speak=True)
    controller = ReadingController(engine=engine)

    result = controller.start_reading("Clean text.", language="en")

    assert result.success is False
    assert controller.get_state().is_active is False
    assert controller.get_state().is_paused is False


def test_stop_active_and_inactive_are_idempotent() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    controller.start_reading("Clean text.", language="en")

    first = controller.stop()
    second = controller.stop()

    assert first.success is True
    assert second.success is True
    assert engine.stopped is True
    assert controller.get_state().is_active is False
    assert controller.get_state().is_paused is False


def test_native_pause_and_continue_update_state() -> None:
    engine = MockTTSEngine(supports_pause=True, supports_resume=True)
    controller = ReadingController(engine=engine)
    controller.start_reading("First sentence. Second sentence.", language="en")

    pause_result = controller.pause()
    continue_result = controller.continue_reading()

    assert pause_result.success is True
    assert continue_result.success is True
    assert engine.paused is True
    assert engine.resumed is True
    assert controller.get_state().is_active is True
    assert controller.get_state().is_paused is False


def test_pause_fallback_stops_and_continue_replays_current_segment() -> None:
    engine = MockTTSEngine(supports_pause=False, supports_resume=False)
    controller = ReadingController(engine=engine)
    controller.start_reading("First sentence. Second sentence.", language="en")

    pause_result = controller.pause()
    continue_result = controller.continue_reading()

    assert pause_result.success is True
    assert pause_result.fallback_used is True
    assert engine.stopped is True
    assert controller.get_state().is_active is True
    assert controller.get_state().is_paused is False
    assert continue_result.success is True
    assert continue_result.fallback_used is True
    assert engine.spoken_requests[-1].operation == SpeechOperation.CONTINUE
    assert engine.spoken_requests[-1].text == "First sentence. Second sentence."


def test_set_rate_clamps_and_applies_to_future_requests() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)

    low = controller.set_rate(20)
    controller.start_reading("Clean text.", language="en")
    high = controller.set_rate(999)
    controller.start_reading("More clean text.", language="en")

    assert low.success is True
    assert high.success is True
    assert engine.spoken_requests[0].rate_wpm == 80
    assert engine.spoken_requests[1].rate_wpm == 220


def test_repeat_last_sentence_speaks_only_tracked_sentence() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    controller.start_reading("First sentence. Second sentence.", language="en")

    result = controller.repeat_last_sentence()

    assert result.success is True
    assert engine.spoken_requests[-1].operation == SpeechOperation.REPEAT_SENTENCE
    assert engine.spoken_requests[-1].text == "First sentence."
    assert "Second sentence" not in engine.spoken_requests[-1].text


def test_repeat_last_paragraph_speaks_only_tracked_paragraph() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    controller.start_reading("First paragraph.\n\nSecond paragraph.", language="en")

    result = controller.repeat_last_paragraph()

    assert result.success is True
    assert engine.spoken_requests[-1].operation == SpeechOperation.REPEAT_PARAGRAPH
    assert engine.spoken_requests[-1].text == "First paragraph."
    assert "Second paragraph" not in engine.spoken_requests[-1].text


def test_repeat_without_history_returns_guidance_without_speech() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)

    sentence = controller.repeat_last_sentence()
    paragraph = controller.repeat_last_paragraph()

    assert sentence.success is False
    assert paragraph.success is False
    assert sentence.error is not None
    assert paragraph.error is not None
    assert sentence.error.code == TTSErrorCode.NOTHING_TO_REPEAT
    assert paragraph.error.code == TTSErrorCode.NOTHING_TO_REPEAT
    assert engine.spoken_requests == []


def test_tts_failure_preserves_prior_successful_repeat_history() -> None:
    engine = MockTTSEngine()
    controller = ReadingController(engine=engine)
    controller.start_reading("First sentence. Second sentence.", language="en")
    first_history = controller.get_state().last_sentence
    engine.fail_next_speak = True

    result = controller.repeat_last_sentence()

    assert result.success is False
    assert controller.get_state().is_active is False
    assert controller.get_state().last_sentence == first_history
