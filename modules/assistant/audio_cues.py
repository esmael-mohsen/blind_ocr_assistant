"""Small non-verbal audio cues for long-running runtime operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import os
import threading
import time


BeepFunc = Callable[[int, int], None]


def _default_beep(frequency_hz: int, duration_ms: int) -> None:
    if os.name == "nt":
        try:
            import winsound

            winsound.Beep(frequency_hz, duration_ms)
            return
        except Exception:
            return


@dataclass
class AudioCueManager:
    """Loop a gentle progress beep until stopped."""

    enabled: bool = True
    beep_func: BeepFunc = _default_beep
    frequency_hz: int = 520
    duration_ms: int = 35
    interval_seconds: float = 1.15
    _running: threading.Event = field(default_factory=threading.Event, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    active_label: str = ""

    def start(self, label: str = "loading") -> None:
        if not self.enabled or self._running.is_set():
            return
        self.active_label = label
        self._running.set()
        self._thread = threading.Thread(target=self._loop, name="assistant-audio-cue", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        self.active_label = ""
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _loop(self) -> None:
        while self._running.is_set():
            try:
                self.beep_func(self.frequency_hz, self.duration_ms)
            except Exception:
                pass
            time.sleep(self.interval_seconds)


__all__ = ["AudioCueManager"]
