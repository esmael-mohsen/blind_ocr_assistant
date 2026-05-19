"""Scope-boundary tests for Phase 11 deployment hardening."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ROOT = ROOT / "modules" / "deployment"
MAIN_PATH = ROOT / "main.py"
SERVICE_TEMPLATE = ROOT / "deploy" / "blind-ocr-assistant.service.template"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_deployment_code_does_not_import_concrete_new_engines_or_ui() -> None:
    forbidden_imports = {
        "fastapi",
        "flask",
        "streamlit",
        "tkinter",
        "boto3",
        "sqlalchemy",
    }
    imported = set()
    for path in DEPLOYMENT_ROOT.glob("*.py"):
        imported.update(_imported_modules(path))

    assert imported.isdisjoint(forbidden_imports)


def test_phase11_does_not_add_command_categories_or_enable_service_startup() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [*DEPLOYMENT_ROOT.glob("*.py"), MAIN_PATH, SERVICE_TEMPLATE]
    ).lower()
    forbidden_terms = {
        "openai",
        "aws",
        "azure",
        "firebase",
        "login",
        "account",
        "systemctl enable blind-ocr-assistant",
    }

    assert not (forbidden_terms & set(source.split()))
    assert "wantedby=multi-user.target" in source
