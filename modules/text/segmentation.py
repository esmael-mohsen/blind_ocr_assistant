"""Deterministic text segmentation helpers for Phase 6."""

from __future__ import annotations

import re

from modules.voice.voice_models import SegmentType, TextSegment


_PARAGRAPH_SPLIT_RE = re.compile(r"(?:\r?\n\s*){2,}")
_SENTENCE_SPLIT_RE = re.compile(r"[^.!?\u061f\u06d4]+[.!?\u061f\u06d4]+|[^.!?\u061f\u06d4]+$")


def split_paragraphs(
    text: str,
    *,
    language: str = "mixed",
    parent_text_id: str = "current",
) -> list[TextSegment]:
    """Split clean text into paragraph segments using blank-line boundaries."""
    if not text.strip():
        return []
    parts = [
        part.strip()
        for part in _PARAGRAPH_SPLIT_RE.split(text.strip())
        if part.strip()
    ]
    return [
        TextSegment(
            segment_id=f"{parent_text_id}:paragraph:{index}",
            segment_type=SegmentType.PARAGRAPH,
            order=index,
            text=part,
            language=language,
            parent_text_id=parent_text_id,
        )
        for index, part in enumerate(parts)
    ]


def split_sentences(
    text: str,
    *,
    language: str = "mixed",
    parent_text_id: str = "current",
) -> list[TextSegment]:
    """Split clean text into sentence segments using Arabic and English punctuation."""
    if not text.strip():
        return []
    normalized = re.sub(r"\s+", " ", text.strip())
    parts = [match.group(0).strip() for match in _SENTENCE_SPLIT_RE.finditer(normalized)]
    parts = [part for part in parts if part]
    return [
        TextSegment(
            segment_id=f"{parent_text_id}:sentence:{index}",
            segment_type=SegmentType.SENTENCE,
            order=index,
            text=part,
            language=language,
            parent_text_id=parent_text_id,
        )
        for index, part in enumerate(parts)
    ]


__all__ = [
    "split_paragraphs",
    "split_sentences",
]
