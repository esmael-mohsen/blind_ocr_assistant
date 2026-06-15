"""Tests for Phase 9 assistant workflow orchestration."""

from __future__ import annotations

from types import SimpleNamespace

from modules.assistant.state import WorkflowErrorCode, WorkflowMode
from modules.assistant.workflow import AssistantWorkflow
from modules.voice.command_models import CommandIntent, CommandPath, CommandResult


class Boundary:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


def test_workflow_constructor_accepts_injected_boundaries():
    capture = Boundary("capture")
    ocr = Boundary("ocr")
    cleanup = Boundary("cleanup")
    logger = Boundary()

    workflow = AssistantWorkflow(
        dialogue_manager=object(),
        capture_burst=capture,
        select_best_frame=Boundary("frame"),
        run_ocr_cascade=ocr,
        clean_ocr_text=cleanup,
        reading_controller=object(),
        translation_controller=object(),
        online_status_provider=Boundary(True),
        clock=lambda: 123.0,
        logger=logger,
    )

    assert workflow.capture_burst is capture
    assert workflow.run_ocr_cascade is ocr
    assert workflow.clean_ocr_text is cleanup
    assert workflow.clock() == 123.0
    assert workflow.get_state().current_mode == WorkflowMode.IDLE


def test_workflow_active_and_shutdown_guards():
    workflow = AssistantWorkflow()
    workflow.session = workflow.session.with_updates(workflow_active=True)

    busy = workflow.run_read_workflow()
    assert busy.success is False
    assert busy.error.code == WorkflowErrorCode.WORKFLOW_BUSY
    assert "already" in busy.guidance.lower() or "busy" in busy.guidance.lower()

    workflow.session = workflow.session.with_updates(workflow_active=False).request_shutdown()
    stopped = workflow.run_read_workflow()
    assert stopped.success is False
    assert stopped.error.code == WorkflowErrorCode.SHUTDOWN_REQUESTED


def test_shutdown_sets_final_state_and_runs_cleanup_hooks():
    calls = []
    workflow = AssistantWorkflow(cleanup_hooks=[lambda: calls.append("clean")])
    workflow.session = workflow.session.with_updates(workflow_active=True)

    result = workflow.shutdown()

    assert result.success is True
    assert result.guidance == "Assistant stopped."
    assert calls == ["clean"]
    assert workflow.session.shutdown_requested is True
    assert workflow.session.workflow_active is False
    assert workflow.get_state().current_mode == WorkflowMode.SHUTTING_DOWN


def test_shutdown_stops_active_speech_when_available():
    class ReadingStopStub:
        def __init__(self):
            self.calls = 0

        def stop(self):
            self.calls += 1
            return SimpleNamespace(success=True)

    reading = ReadingStopStub()
    workflow = AssistantWorkflow(reading_controller=reading)
    workflow.session = workflow.session.with_updates(workflow_active=True)

    result = workflow.shutdown()

    assert result.success is True
    assert reading.calls == 1
    assert workflow.session.workflow_active is False


def test_voice_stop_remains_playback_control_not_shutdown():
    stop_result = CommandResult.recognized(
        intent=CommandIntent.STOP,
        language="en",
        path=CommandPath.PARSER,
        guidance="Reading stopped.",
    )
    workflow = AssistantWorkflow(dialogue_manager=DialogueStub(stop_result))

    result = workflow.handle_command("stop", language_hint="en")

    assert result is stop_result
    assert workflow.session.shutdown_requested is False
    assert workflow.get_state().current_mode == WorkflowMode.IDLE


class DialogueStub:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def handle_command(self, phrase, language_hint="unknown", **kwargs):
        self.calls.append((phrase, language_hint, kwargs))
        return self.result


class ReadingStub:
    def __init__(self, success=True):
        self.success = success
        self.calls = []

    def start_reading(self, clean_text, language="mixed", **kwargs):
        self.calls.append((clean_text, language, kwargs))
        return SimpleNamespace(success=self.success, guidance="Reading is starting.")


def _read_command(language="ar"):
    return CommandResult.recognized(
        intent=CommandIntent.READ,
        language=language,
        path=CommandPath.PARSER,
        guidance="Read command recognized.",
    )


def _successful_workflow(language="english", fallback_used=False):
    calls = []
    selected_frame = SimpleNamespace(rgb_image=b"image-bytes")
    capture = Boundary(
        SimpleNamespace(
            success=True,
            candidates=[selected_frame],
            selection_result=SimpleNamespace(success=True, selected_frame=selected_frame),
            guidance="Captured frames.",
        )
    )
    ocr_result = SimpleNamespace(raw_text="raw secret text", engine_name="ocr_space")
    ocr = Boundary(
        SimpleNamespace(
            success=True,
            selected_engine="paddleocr" if fallback_used else "ocr_space",
            selected_result=ocr_result,
            fallback_used=fallback_used,
            offline_route_used=False,
            high_accuracy_used=False,
            duration_ms=42,
            guidance="OCR text is ready.",
        )
    )
    cleanup = Boundary(
        SimpleNamespace(
            success=True,
            clean_text="clean secret text",
            raw_text="raw secret text",
            language=language,
            guidance="Text is ready for reading.",
        )
    )
    reading = ReadingStub()
    workflow = AssistantWorkflow(
        dialogue_manager=DialogueStub(_read_command("ar")),
        capture_burst=capture,
        run_ocr_cascade=ocr,
        clean_ocr_text=cleanup,
        reading_controller=reading,
        clock=Boundary(1000.0),
    )
    return workflow, capture, ocr, cleanup, reading, calls


def test_arabic_read_command_runs_workflow_in_order():
    workflow, capture, ocr, cleanup, reading, _ = _successful_workflow(language="arabic")

    result = workflow.handle_command("اقرأ النص", language_hint="ar")

    assert result.success is True
    assert capture.calls
    assert ocr.calls
    assert cleanup.calls
    assert reading.calls == [("clean secret text", "ar", {})]
    assert workflow.get_state().last_clean_text == "clean secret text"
    assert workflow.get_state().last_raw_text == "raw secret text"
    assert workflow.get_state().last_language == "ar"
    assert workflow.get_state().last_ocr_engine == "ocr_space"


def test_english_read_command_runs_workflow_in_order():
    workflow, _, _, _, reading, _ = _successful_workflow(language="english")
    workflow.dialogue_manager = DialogueStub(_read_command("en"))

    result = workflow.handle_command("read text", language_hint="en")

    assert result.success is True
    assert reading.calls == [("clean secret text", "en", {})]
    assert workflow.get_state().last_language == "en"
    assert "Reading is starting" in result.guidance


def test_read_workflow_records_fallback_engine_and_spoken_progress():
    workflow, _, _, _, _, _ = _successful_workflow(language="mixed", fallback_used=True)

    result = workflow.run_read_workflow()

    assert result.success is True
    assert result.selected_ocr_engine == "paddleocr"
    assert result.fallback_used is True
    assert workflow.get_state().fallback_used is True
    assert workflow.get_state().last_ocr_engine == "paddleocr"
    assert "fallback" in result.guidance.lower()


class TranslationStub:
    def __init__(self, success=True, translated_text="translated secret", fallback_used=False):
        self.success = success
        self.translated_text = translated_text
        self.fallback_used = fallback_used
        self.calls = []

    def translate_latest(self, clean_text, target_language="en", **kwargs):
        self.calls.append((clean_text, target_language, kwargs))
        return SimpleNamespace(
            success=self.success,
            translated_text=self.translated_text,
            source_language=kwargs.get("source_language", "unknown"),
            target_language=target_language,
            fallback_used=self.fallback_used,
            duration_ms=30,
            guidance="The translated text is being read."
            if self.success
            else "Translation failed.",
            reading_handoff_attempted=self.success,
            reading_handoff_success=self.success,
        )


def _translation_command(intent, target_language, language="en"):
    return CommandResult.recognized(
        intent=intent,
        language=language,
        path=CommandPath.PARSER,
        target_language=target_language,
        guidance="Translate command recognized.",
    )


def test_translate_to_english_uses_latest_clean_arabic_text():
    translation = TranslationStub(translated_text="english translation")
    workflow = AssistantWorkflow(
        dialogue_manager=DialogueStub(
            _translation_command(CommandIntent.TRANSLATE_TO_ENGLISH, "en", "ar")
        ),
        translation_controller=translation,
    )
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw Arabic",
            clean_text="clean Arabic",
            language="ar",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Reading is starting.",
        )
    )

    result = workflow.handle_command("translate to english", language_hint="ar")

    assert result.success is True
    assert translation.calls == [
        (
            "clean Arabic",
            "en",
            {
                "source_language": "ar",
                "explicit_source_language": False,
                "allow_online": True,
                "allow_offline": True,
            },
        )
    ]
    assert workflow.get_state().last_translated_text == "english translation"


def test_translate_to_arabic_uses_latest_clean_english_text():
    translation = TranslationStub(translated_text="arabic translation", fallback_used=True)
    workflow = AssistantWorkflow(
        dialogue_manager=DialogueStub(
            _translation_command(CommandIntent.TRANSLATE_TO_ARABIC, "ar", "en")
        ),
        translation_controller=translation,
    )
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw English",
            clean_text="clean English",
            language="en",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Reading is starting.",
        )
    )

    result = workflow.handle_command("translate to arabic", language_hint="en")

    assert result.success is True
    assert result.target_language == "ar"
    assert result.fallback_used is True
    assert workflow.get_state().last_translated_text == "arabic translation"


def test_translate_from_mixed_text_uses_opposite_source_direction():
    translation = TranslationStub(translated_text="arabic translation")
    workflow = AssistantWorkflow(
        dialogue_manager=DialogueStub(
            _translation_command(CommandIntent.TRANSLATE_TO_ARABIC, "ar", "en")
        ),
        translation_controller=translation,
    )
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw mixed",
            clean_text="TOTAL PLUS\nجرعة يومية",
            language="mixed",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Reading is starting.",
        )
    )

    result = workflow.handle_command("translate to arabic", language_hint="en")

    assert result.success is True
    assert translation.calls[0][2]["source_language"] == "en"
    assert translation.calls[0][2]["explicit_source_language"] is True


def test_failed_read_attempt_does_not_clear_latest_clean_text():
    workflow = AssistantWorkflow()
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="previous raw",
            clean_text="previous clean",
            language="en",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Previous read.",
        )
    )

    result = workflow.run_read_workflow()

    assert result.success is False
    assert workflow.get_state().last_clean_text == "previous clean"
