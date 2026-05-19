"""Integration tests for the Phase 9 full translate workflow."""

from __future__ import annotations

from types import SimpleNamespace

from modules.assistant.workflow import AssistantWorkflow


class TranslationStub:
    def __init__(self):
        self.calls = []

    def translate_latest(self, clean_text, target_language="en", **kwargs):
        self.calls.append((clean_text, target_language, kwargs))
        return SimpleNamespace(
            success=True,
            translated_text=f"{target_language}:{clean_text}",
            source_language=kwargs.get("source_language", "unknown"),
            target_language=target_language,
            fallback_used=False,
            duration_ms=10,
            guidance="The translated text is being read.",
            reading_handoff_attempted=True,
            reading_handoff_success=True,
        )


def test_read_state_then_translate_to_english_and_arabic():
    translation = TranslationStub()
    workflow = AssistantWorkflow(translation_controller=translation)
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw",
            clean_text="clean",
            language="ar",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Read.",
        )
    )

    english = workflow.run_translation_workflow("en")
    arabic = workflow.run_translation_workflow("ar")

    assert english.success is True
    assert arabic.success is True
    assert translation.calls[0][0] == "clean"
    assert translation.calls[0][1] == "en"
    assert translation.calls[1][1] == "ar"
    assert workflow.get_state().last_translated_text == "ar:clean"
