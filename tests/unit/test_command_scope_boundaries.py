"""Scope-boundary tests for Phase 8 command-system behavior."""

from __future__ import annotations

from pathlib import Path
import sys

from modules.assistant.dialogue_manager import DialogueManager


FORBIDDEN_SOURCE_IMPORTS = (
    "modules.camera",
    "modules.ocr",
    "modules.image_processing",
    "modules.text.cleanup",
    "modules.translation.",
    "modules.voice.tts_engine",
    "modules.assistant.main_loop",
)


def test_dialogue_manager_source_does_not_import_out_of_scope_modules() -> None:
    source = Path("modules/assistant/dialogue_manager.py").read_text(encoding="utf-8")

    for forbidden in FORBIDDEN_SOURCE_IMPORTS:
        assert forbidden not in source


def test_help_command_does_not_load_out_of_scope_modules() -> None:
    removed_modules = {}
    for module_name in list(sys.modules):
        if module_name.startswith(
            (
                "modules.camera",
                "modules.ocr",
                "modules.image_processing",
                "modules.text.cleanup",
                "modules.translation",
            )
        ):
            removed_modules[module_name] = sys.modules.pop(module_name)

    try:
        manager = DialogueManager()
        result = manager.handle_command("help", language_hint="en")

        assert result.success is True
        assert not any(name.startswith("modules.camera") for name in sys.modules)
        assert not any(name.startswith("modules.ocr") for name in sys.modules)
        assert not any(
            name.startswith("modules.image_processing") for name in sys.modules
        )
        assert "modules.text.cleanup" not in sys.modules
        assert not any(name.startswith("modules.translation") for name in sys.modules)
    finally:
        sys.modules.update(removed_modules)
