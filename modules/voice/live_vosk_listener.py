"""Live microphone command listener backed by Vosk."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import queue
import time
from typing import Any


@dataclass
class LiveVoskCommandListener:
    """Small blocking Vosk listener for one short command at a time."""

    model_path: str | Path
    sample_rate: int = 16000
    phrase_timeout_seconds: float = 8.0
    device_index: int | None = None

    def __post_init__(self) -> None:
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._model: Any | None = None
        self._stream: Any | None = None

    def __enter__(self) -> "LiveVoskCommandListener":
        self.open()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def open(self) -> None:
        if self._stream is not None:
            return
        model_path = Path(self.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Vosk model path not found: {model_path}")
        import sounddevice as sd
        import vosk

        self._model = vosk.Model(str(model_path))
        self._stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            device=self.device_index,
            callback=self._callback,
        )
        self._stream.start()

    def close(self) -> None:
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None

    def listen_once(self) -> str:
        """Return one recognized command transcript or an empty string on timeout."""
        if self._model is None:
            self.open()
        import vosk

        self._drain_audio()
        recognizer = vosk.KaldiRecognizer(self._model, self.sample_rate)
        deadline = time.monotonic() + self.phrase_timeout_seconds
        latest_partial = ""
        while time.monotonic() < deadline:
            try:
                data = self._audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if recognizer.AcceptWaveform(data):
                text = self._result_text(recognizer.Result())
                if text:
                    return text
            else:
                latest_partial = self._result_text(
                    recognizer.PartialResult(), key="partial"
                )
        return self._result_text(recognizer.FinalResult()) or latest_partial

    def _callback(
        self, indata: bytes, _frames: int, _time: object, status: object
    ) -> None:
        if status:
            return
        self._audio_queue.put(bytes(indata))

    def _drain_audio(self) -> None:
        while True:
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                return

    @staticmethod
    def _result_text(payload: str, *, key: str = "text") -> str:
        try:
            result = json.loads(payload)
        except json.JSONDecodeError:
            return ""
        return str(result.get(key, "")).strip().lower()


__all__ = ["LiveVoskCommandListener"]
