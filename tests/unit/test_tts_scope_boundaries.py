"""Scope-boundary tests for Phase 6 reading behavior."""

from __future__ import annotations

from pathlib import Path
import sys

from modules.assistant.reading_controller import ReadingController
from modules.voice.tts_engine import MockTTSEngine


FORBIDDEN_IMPORTS = (
    "modules.camera",
    "modules.ocr",
    "modules.image_processing",
    "modules.translation",
    "modules.voice.command_parser",
    "modules.voice.vosk_fallback",
    "modules.voice.stt_online",
    "modules.assistant.dialogue_manager",
)


def test_reading_controller_source_does_not_import_out_of_scope_modules() -> None:
    source = Path("modules/assistant/reading_controller.py").read_text(encoding="utf-8")

    for forbidden in FORBIDDEN_IMPORTS:
        assert forbidden not in source


def test_start_reading_does_not_load_out_of_scope_modules() -> None:
    for module_name in list(sys.modules):
        if module_name.startswith(("modules.camera", "modules.translation")):
            sys.modules.pop(module_name)

    controller = ReadingController(engine=MockTTSEngine())
    controller.start_reading("Clean text.", language="en")

    assert not any(name.startswith("modules.camera") for name in sys.modules)
    assert not any(name.startswith("modules.translation") for name in sys.modules)
