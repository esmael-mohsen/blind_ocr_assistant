"""Scope-boundary tests for Phase 9 assistant workflow integration."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from modules.assistant.workflow import AssistantWorkflow
from modules.voice.command_models import CommandIntent


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / "modules" / "assistant" / "workflow.py"
STATE_PATH = ROOT / "modules" / "assistant" / "state.py"
MAIN_PATH = ROOT / "main.py"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_phase9_workflow_uses_boundaries_not_concrete_engines():
    forbidden_imports = {
        "modules.camera.orbbec_camera",
        "modules.camera.frame_selector",
        "modules.image_processing.preprocessing",
        "modules.image_processing.quality_checker",
        "modules.ocr.ocr_space_client",
        "modules.ocr.paddle_ocr_engine",
        "modules.ocr.tesseract_engine",
        "modules.ocr.ocr_cascade",
        "modules.text.cleanup",
        "modules.translation.argos_fallback",
        "modules.translation.online_translation_stack",
        "modules.voice.stt_online",
        "modules.voice.tts_engine",
        "modules.voice.vosk_fallback",
    }

    assert _imported_modules(WORKFLOW_PATH).isdisjoint(forbidden_imports)
    assert _imported_modules(MAIN_PATH).isdisjoint(forbidden_imports)


def test_runtime_command_categories_are_explicit_and_bounded():
    assert {intent.value for intent in CommandIntent} == {
        "read",
        "stop",
        "continue",
        "repeat_sentence",
        "repeat_paragraph",
        "translate_to_arabic",
        "translate_to_english",
        "help",
        "cancel",
        "status",
        "what_do_you_see",
        "repeat_guidance",
        "read_again",
        "capture_now",
        "switch_arabic",
        "switch_english",
        "quiet_mode",
        "verbose_mode",
        "voice_test",
        "exit",
        "unknown",
        "ambiguous",
    }
    assert "shutdown" not in {intent.value for intent in CommandIntent}


def test_phase9_constructor_exposes_injected_boundaries_only():
    workflow_fields = {field.name for field in fields(AssistantWorkflow)}

    assert workflow_fields == {
        "dialogue_manager",
        "capture_burst",
        "select_best_frame",
        "run_ocr_cascade",
        "clean_ocr_text",
        "reading_controller",
        "translation_controller",
        "online_status_provider",
        "clock",
        "logger",
        "cleanup_hooks",
        "session",
    }


def test_phase9_sources_do_not_introduce_ui_accounts_cloud_or_deployment():
    combined_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (WORKFLOW_PATH, STATE_PATH, MAIN_PATH)
    ).lower()

    forbidden_terms = {
        "fastapi",
        "flask",
        "streamlit",
        "tkinter",
        "sqlalchemy",
        "database",
        "login",
        "account",
        "s3",
        "azure",
        "firebase",
        "cloud_storage",
        "dockerfile",
        "kubernetes",
        "benchmark",
    }

    assert not (forbidden_terms & set(combined_source.split()))
