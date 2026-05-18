"""Phase 3 camera module scope-boundary tests."""

from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_PREFIXES = (
    "modules.assistant",
    "modules.ocr",
    "modules.text",
    "modules.translation",
    "modules.voice",
)


def test_camera_modules_do_not_import_later_workflow_layers() -> None:
    camera_dir = Path("modules/camera")
    offenders: list[str] = []

    for path in camera_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name.startswith(FORBIDDEN_PREFIXES):
                    offenders.append(f"{path}:{name}")

    assert offenders == []
