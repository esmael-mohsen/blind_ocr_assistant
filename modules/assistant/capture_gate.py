"""Capture gating for read-when-ready runtime behavior."""

from __future__ import annotations

from dataclasses import dataclass

from modules.assistant.runtime_state import FrameReadiness


@dataclass(frozen=True)
class CaptureGate:
    """Decide when preview readiness is enough to start OCR."""

    capture_override_enabled: bool = True

    def can_capture(self, readiness: FrameReadiness, *, override: bool = False) -> bool:
        if override:
            return self.capture_override_enabled
        return readiness.ready_to_capture

    def message_for_block(self, readiness: FrameReadiness) -> str:
        return readiness.guidance or "Keep the text in view until it is clear."


__all__ = ["CaptureGate"]
