"""CLI contract tests for the Phase 0 bootstrap entrypoint."""

from __future__ import annotations

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "main.py", *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_help_command_exits_successfully() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "Integrated Blind OCR Assistant runtime" in result.stdout
    assert "--self-check" in result.stdout


def test_self_check_exits_successfully() -> None:
    result = run_cli("--self-check")

    assert result.returncode == 0
    assert "Phase 0 self-check: PASS" in result.stdout
    assert "core bootstrap checks passed" in result.stdout
