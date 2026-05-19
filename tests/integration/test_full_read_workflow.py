"""Integration tests for the Phase 9 full read workflow."""

from __future__ import annotations

from types import SimpleNamespace

from modules.assistant.workflow import AssistantWorkflow
from modules.voice.command_models import CommandIntent, CommandPath, CommandResult


class Boundary:
    def __init__(self, result):
        self.result = result

    def __call__(self, *args, **kwargs):
        return self.result


class DialogueStub:
    def handle_command(self, phrase, language_hint="unknown", **kwargs):
        return CommandResult.recognized(
            intent=CommandIntent.READ,
            language=language_hint,
            path=CommandPath.PARSER,
            guidance="Read command recognized.",
        )


class ReadingStub:
    def __init__(self):
        self.read_text = None
        self.language = None

    def start_reading(self, clean_text, language="mixed", **kwargs):
        self.read_text = clean_text
        self.language = language
        return SimpleNamespace(success=True)


def test_mocked_full_read_workflow_from_command_to_reading():
    frame = SimpleNamespace(rgb_image=b"image-bytes")
    reading = ReadingStub()
    workflow = AssistantWorkflow(
        dialogue_manager=DialogueStub(),
        capture_burst=Boundary(
            SimpleNamespace(
                success=True,
                candidates=[frame],
                selection_result=SimpleNamespace(success=True, selected_frame=frame),
            )
        ),
        run_ocr_cascade=Boundary(
            SimpleNamespace(
                success=True,
                selected_engine="ocr_space",
                selected_result=SimpleNamespace(raw_text="raw text"),
                fallback_used=False,
                offline_route_used=False,
                high_accuracy_used=False,
                duration_ms=20,
                guidance="OCR text is ready.",
            )
        ),
        clean_ocr_text=Boundary(
            SimpleNamespace(
                success=True,
                raw_text="raw text",
                clean_text="clean text",
                language="english",
                guidance="Text is ready.",
            )
        ),
        reading_controller=reading,
    )

    result = workflow.handle_command("read text", language_hint="en")

    assert result.success is True
    assert reading.read_text == "clean text"
    assert reading.language == "en"
    assert workflow.get_state().last_clean_text == "clean text"
