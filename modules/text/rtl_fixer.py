"""RTL handling helpers for Phase 5."""

from __future__ import annotations

import re

from modules.text.cleanup import TextDirection
from modules.text.language_detector import DirectionInfo


ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")


def detect_text_direction(text: str) -> DirectionInfo:
    """Detect coarse text direction while preserving logical order."""
    has_rtl = bool(ARABIC_RE.search(text or ""))
    has_ltr = bool(LATIN_RE.search(text or ""))
    if has_rtl and has_ltr:
        direction = TextDirection.MIXED
    elif has_rtl:
        direction = TextDirection.RTL
    elif has_ltr:
        direction = TextDirection.LTR
    else:
        direction = TextDirection.UNKNOWN
    return DirectionInfo(
        direction=direction,
        has_rtl=has_rtl,
        has_ltr=has_ltr,
        logical_order_preserved=True,
    )


def preserve_logical_order(text: str) -> str:
    """Return text unchanged because speech/translation need logical order."""
    return text


__all__ = [
    "detect_text_direction",
    "preserve_logical_order",
]
