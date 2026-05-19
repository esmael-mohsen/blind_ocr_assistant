"""Privacy tests for Phase 9 assistant workflow metadata."""

from __future__ import annotations

from types import SimpleNamespace

from modules.assistant.state import sanitize_workflow_metadata
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
    def start_reading(self, clean_text, language="mixed", **kwargs):
        return SimpleNamespace(success=True)


def test_read_workflow_safe_metadata_excludes_sensitive_payloads():
    frame = SimpleNamespace(rgb_image=b"image secret")
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
                selected_result=SimpleNamespace(raw_text="raw OCR secret"),
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
                raw_text="raw OCR secret",
                clean_text="clean secret",
                language="english",
                guidance="Text is ready.",
            )
        ),
        reading_controller=ReadingStub(),
    )

    result = workflow.handle_command("read text", language_hint="en")

    assert result.success is True
    metadata = {
        **result.safe_metadata,
        **workflow.get_state().safe_metadata,
        **sanitize_workflow_metadata(
            {
                "image": b"image secret",
                "raw_text": "raw OCR secret",
                "clean_text": "clean secret",
                "translated_text": "translated secret",
                "command_transcript": "read text",
                "speech_input": "audio secret",
                "snippet": "secret",
                "secret": "secret",
                "debug_path": "debug.png",
            }
        ),
    }

    joined = repr(metadata)
    assert "raw OCR secret" not in joined
    assert "clean secret" not in joined
    assert "translated secret" not in joined
    assert "read text" not in joined
    assert "audio secret" not in joined
    assert "debug.png" not in joined
    assert metadata["selected_ocr_engine"] == "ocr_space"


def test_translation_workflow_safe_metadata_excludes_sensitive_payloads():
    class TranslationStub:
        def translate_latest(self, clean_text, target_language="en", **kwargs):
            return type(
                "Result",
                (),
                {
                    "success": True,
                    "translated_text": "translated secret",
                    "source_language": kwargs.get("source_language", "unknown"),
                    "target_language": target_language,
                    "fallback_used": False,
                    "duration_ms": 3,
                    "guidance": "The translated text is being read.",
                    "reading_handoff_attempted": True,
                    "reading_handoff_success": True,
                },
            )()

    workflow = AssistantWorkflow(translation_controller=TranslationStub())
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw secret",
            clean_text="clean secret",
            language="en",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Read.",
        )
    )

    result = workflow.run_translation_workflow("ar")

    assert result.success is True
    joined = repr({**result.safe_metadata, **workflow.get_state().safe_metadata})
    assert "clean secret" not in joined
    assert "translated secret" not in joined
    assert result.safe_metadata["target_language"] == "ar"


def test_shutdown_safe_metadata_excludes_sensitive_payloads():
    workflow = AssistantWorkflow()
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw secret",
            clean_text="clean secret",
            language="en",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Read.",
        ).with_successful_translation(
            translated_text="translated secret",
            guidance="Translated.",
        )
    )

    result = workflow.shutdown()

    joined = repr({**result.safe_metadata, **workflow.session.safe_metadata})
    assert "raw secret" not in joined
    assert "clean secret" not in joined
    assert "translated secret" not in joined
    assert result.status.value == "shutdown"
