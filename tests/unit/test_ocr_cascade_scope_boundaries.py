"""Phase 4 OCR cascade scope boundary tests."""

from __future__ import annotations

import ast
from pathlib import Path


PHASE4_FILES = (
    Path("modules/ocr/ocr_cascade.py"),
    Path("modules/ocr/ocr_quality.py"),
)

FORBIDDEN_MODULES = (
    "modules.assistant",
    "modules.camera",
    "modules.text",
    "modules.translation",
    "modules.voice",
)


def test_ocr_cascade_phase_does_not_import_later_or_adjacent_workflows() -> None:
    violations: list[str] = []
    for path in PHASE4_FILES:
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
