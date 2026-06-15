"""Tests for progress audio cues."""

from __future__ import annotations

import time

from modules.assistant.audio_cues import AudioCueManager


def test_audio_cue_manager_starts_and_stops() -> None:
    calls = []
    manager = AudioCueManager(
        enabled=True,
        beep_func=lambda frequency, duration: calls.append((frequency, duration)),
        interval_seconds=0.01,
    )

    manager.start("ocr")
    time.sleep(0.03)
    manager.stop()

    assert manager.active_label == ""
    assert calls


def test_audio_cue_manager_disabled_does_not_beep() -> None:
    calls = []
    manager = AudioCueManager(enabled=False, beep_func=lambda *_args: calls.append("beep"))

    manager.start("ocr")
    manager.stop()

    assert calls == []
