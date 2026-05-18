"""Developer camera script tests."""

from __future__ import annotations

from scripts import test_camera


def test_camera_script_non_live_mode_avoids_hardware(capsys) -> None:
    exit_code = test_camera.main([])
    output = capsys.readouterr().out.lower()

    assert exit_code == 0
    assert "live camera validation skipped" in output
