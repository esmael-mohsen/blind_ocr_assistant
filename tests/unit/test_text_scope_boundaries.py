"""Phase 5 text module scope boundary tests."""

from __future__ import annotations

import ast
from pathlib import Path


PHASE5_FILES = (
    Path("modules/text/cleanup.py"),
    Path("modules/text/language_detector.py"),
    Path("modules/text/rtl_fixer.py"),
)

FORBIDDEN_MODULES = (
    "modules.assistant",
    "modules.camera",
    "modules.image_processing",
    "modules.ocr.ocr_cascade",
    "modules.translation",
    "modules.voice",
)


def test_text_phase_does_not_import_adjacent_or_later_workflows() -> None:
    violations: list[str] = []
    for path in PHASE5_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported = [node.module]
            else:
                continue

            for module_name in imported:
                if module_name.startswith(FORBIDDEN_MODULES):
                    violations.append(f"{path}: imports {module_name}")

    assert violations == []
