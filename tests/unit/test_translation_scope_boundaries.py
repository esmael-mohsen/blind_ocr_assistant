"""Scope-boundary tests for Phase 7 translation behavior."""

from __future__ import annotations

from pathlib import Path
import sys

from modules.assistant.translation_controller import TranslationController
from modules.translation.base import MockTranslationEngine


FORBIDDEN_SOURCE_IMPORTS = (
    "modules.camera",
    "modules.ocr",
    "modules.image_processing",
    "modules.text.cleanup",
    "modules.voice.command_parser",
    "modules.voice.vosk_fallback",
    "modules.voice.stt_online",
    "modules.assistant.dialogue_manager",
)


def test_translation_controller_source_does_not_import_out_of_scope_modules() -> None:
    source = Path("modules/assistant/translation_controller.py").read_text(
        encoding="utf-8"
    )

    for forbidden in FORBIDDEN_SOURCE_IMPORTS:
        assert forbidden not in source


def test_translate_latest_does_not_load_out_of_scope_modules() -> None:
    for module_name in list(sys.modules):
        if module_name.startswith(
            (
                "modules.camera",
                "modules.ocr",
                "modules.image_processing",
                "modules.text.cleanup",
                "modules.assistant.dialogue_manager",
            )
        ):
            sys.modules.pop(module_name)

    controller = TranslationController(
        online_engine=MockTranslationEngine(responses={("en", "ar"): "مرحبا."})
    )
    controller.translate_latest("Hello.", target_language="ar", source_language="en")

    assert not any(name.startswith("modules.camera") for name in sys.modules)
    assert not any(name.startswith("modules.ocr") for name in sys.modules)
    assert not any(name.startswith("modules.image_processing") for name in sys.modules)
    assert "modules.text.cleanup" not in sys.modules
    assert "modules.assistant.dialogue_manager" not in sys.modules
