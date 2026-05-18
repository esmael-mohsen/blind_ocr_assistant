"""Quickstart command contract tests."""

from __future__ import annotations

from pathlib import Path


def test_quickstart_documents_phase0_validation_commands() -> None:
    content = Path("specs/001-phase0-bootstrap/quickstart.md").read_text(
        encoding="utf-8"
    )

    assert "python main.py --help" in content
    assert "python main.py --self-check" in content
    assert "python -m pytest" in content
    assert "No camera, audio device, internet connection" in content
    assert "full assistive" in content
    assert "workflow are intentionally deferred" in content
