"""Reading controller for Phase 6 text-to-speech playback."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

from modules.text.segmentation import split_paragraphs, split_sentences
from modules.voice.tts_engine import TTSEngine
from modules.voice.voice_models import (
    ReadingState,
    SegmentType,
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
    TextSegment,
    clamp_speech_rate,
)


def _text_id(clean_text: str) -> str:
    digest = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:12]
    return f"text:{digest}"


@dataclass
class ReadingController:
    """Stateful TTS controller for clean OCR text."""

    engine: TTSEngine
    state: ReadingState = field(default_factory=ReadingState)
    _sentences: list[TextSegment] = field(default_factory=list)
    _paragraphs: list[TextSegment] = field(default_factory=list)

    def get_state(self) -> ReadingState:
        """Return the current in-memory reading state."""
        return self.state

    def start_reading(
        self,
        clean_text: str,
        language: str = "mixed",
        rate_wpm: int | None = None,
    ) -> SpeechResult:
        """Start reading clean text through the configured speech engine."""
        text = clean_text.strip()
        rate = clamp_speech_rate(rate_wpm or self.state.current_rate_wpm)
        if not text:
            result = self._failure(
                operation=SpeechOperation.READ_ALL,
                code=TTSErrorCode.NO_READABLE_TEXT,
                message="No readable text was provided",
                guidance="No readable text is available.",
            )
            self.state = self.state.with_updates(
                is_active=False,
                is_paused=False,
                current_rate_wpm=rate,
                last_operation=SpeechOperation.READ_ALL,
                last_result=result,
                native_pause_active=False,
            )
            return result

        current_text_id = _text_id(text)
        self._sentences = split_sentences(
            text,
            language=language,
            parent_text_id=current_text_id,
        )
        self._paragraphs = split_paragraphs(
            text,
            language=language,
            parent_text_id=current_text_id,
        )
        current_segment = TextSegment(
            segment_id=f"{current_text_id}:full_text:0",
            segment_type=SegmentType.FULL_TEXT,
            order=0,
            text=text,
            language=language,
            parent_text_id=current_text_id,
        )
        request = SpeechRequest(
            text=text,
            language=language,
            rate_wpm=rate,
            operation=SpeechOperation.READ_ALL,
            segment_id=current_segment.segment_id,
            segment_type=SegmentType.FULL_TEXT,
            segment_order=0,
        )
        result = self.engine.speak(request)
        if result.success:
            self.state = self.state.with_updates(
                is_active=True,
                is_paused=False,
                current_text_id=current_text_id,
                current_segment=current_segment,
                current_rate_wpm=rate,
                last_sentence=self._sentences[0] if self._sentences else None,
                last_paragraph=self._paragraphs[0] if self._paragraphs else None,
                last_operation=SpeechOperation.READ_ALL,
                last_result=result,
                native_pause_active=False,
            )
            return result

        self.state = self.state.with_updates(
            is_active=False,
            is_paused=False,
            current_text_id=current_text_id,
            current_segment=current_segment,
            current_rate_wpm=rate,
            last_operation=SpeechOperation.READ_ALL,
            last_result=result,
            native_pause_active=False,
        )
        return result

    def stop(self) -> SpeechResult:
        """Stop reading safely whether or not speech is active."""
        result = self.engine.stop()
        if not result.success:
            result = self._failure(
                operation=SpeechOperation.STOP,
                code=TTSErrorCode.TTS_STOP_FAILED,
                message="TTS engine failed to stop",
                guidance="The speech engine could not stop cleanly.",
            )
        self.state = self.state.with_updates(
            is_active=False,
            is_paused=False,
            last_operation=SpeechOperation.STOP,
            last_result=result,
            native_pause_active=False,
        )
        return result

    def pause(self) -> SpeechResult:
        """Pause reading or degrade to stop-and-replay fallback."""
        if not self.state.is_active:
            result = SpeechResult.ok(
                operation=SpeechOperation.PAUSE,
                engine_name=getattr(self.engine, "name", None),
                guidance="Reading is not active.",
            )
            self.state = self.state.with_updates(
                is_active=False,
                is_paused=False,
                last_operation=SpeechOperation.PAUSE,
                last_result=result,
                native_pause_active=False,
            )
            return result

        if getattr(self.engine, "supports_pause", False):
            result = self.engine.pause()
            if result.success:
                self.state = self.state.with_updates(
                    is_active=False,
                    is_paused=True,
                    last_operation=SpeechOperation.PAUSE,
                    last_result=result,
                    native_pause_active=True,
                )
                return result

        self.engine.stop()
        result = SpeechResult.ok(
            operation=SpeechOperation.PAUSE,
            engine_name=getattr(self.engine, "name", None),
            guidance=(
                "Pause is not supported by this speech engine. "
                "Reading stopped and will continue by replaying the current segment."
            ),
            fallback_used=True,
        )
        self.state = self.state.with_updates(
            is_active=False,
            is_paused=True,
            last_operation=SpeechOperation.PAUSE,
            last_result=result,
            native_pause_active=False,
        )
        return result

    def continue_reading(self) -> SpeechResult:
        """Continue reading from native pause or replay the current segment."""
        if self.state.is_paused and self.state.native_pause_active:
            result = self.engine.resume()
            if result.success:
                self.state = self.state.with_updates(
                    is_active=True,
                    is_paused=False,
                    last_operation=SpeechOperation.CONTINUE,
                    last_result=result,
                    native_pause_active=False,
                )
                return result

        segment = self.state.current_segment
        if segment is None:
            result = self._failure(
                operation=SpeechOperation.CONTINUE,
                code=TTSErrorCode.NO_READABLE_TEXT,
                message="No current segment is available to continue",
                guidance="There is no reading to continue.",
            )
            self.state = self.state.with_updates(
                is_active=False,
                is_paused=False,
                last_operation=SpeechOperation.CONTINUE,
                last_result=result,
                native_pause_active=False,
            )
            return result

        request = SpeechRequest.from_segment(
            segment,
            rate_wpm=self.state.current_rate_wpm,
            operation=SpeechOperation.CONTINUE,
        )
        result = self.engine.speak(request)
        if result.success:
            result = SpeechResult.ok(
                operation=SpeechOperation.CONTINUE,
                engine_name=result.engine_name,
                duration_ms=result.duration_ms,
                guidance="Continuing by replaying the current segment.",
                fallback_used=not getattr(self.engine, "supports_resume", False),
            )
            self.state = self.state.with_updates(
                is_active=True,
                is_paused=False,
                current_segment=segment,
                last_operation=SpeechOperation.CONTINUE,
                last_result=result,
                native_pause_active=False,
            )
            return result

        self.state = self.state.with_updates(
            is_active=False,
            is_paused=False,
            last_operation=SpeechOperation.CONTINUE,
            last_result=result,
            native_pause_active=False,
        )
        return result

    def set_rate(self, rate_wpm: int) -> SpeechResult:
        """Set the speech rate for future speech requests."""
        rate = clamp_speech_rate(rate_wpm)
        result = SpeechResult.ok(
            operation=SpeechOperation.SET_RATE,
            engine_name=getattr(self.engine, "name", None),
            guidance="Speech rate updated.",
        )
        self.state = self.state.with_updates(
            current_rate_wpm=rate,
            last_operation=SpeechOperation.SET_RATE,
            last_result=result,
        )
        return result

    def repeat_last_sentence(self) -> SpeechResult:
        """Repeat the last tracked sentence segment."""
        return self._repeat_segment(
            segment=self.state.last_sentence,
            operation=SpeechOperation.REPEAT_SENTENCE,
            no_history_guidance="There is no sentence to repeat.",
        )

    def repeat_last_paragraph(self) -> SpeechResult:
        """Repeat the last tracked paragraph segment."""
        return self._repeat_segment(
            segment=self.state.last_paragraph,
            operation=SpeechOperation.REPEAT_PARAGRAPH,
            no_history_guidance="There is no paragraph to repeat.",
        )

    def _repeat_segment(
        self,
        *,
        segment: TextSegment | None,
        operation: SpeechOperation,
        no_history_guidance: str,
    ) -> SpeechResult:
        if segment is None:
            result = self._failure(
                operation=operation,
                code=TTSErrorCode.NOTHING_TO_REPEAT,
                message="No repeat history is available",
                guidance=no_history_guidance,
            )
            self.state = self.state.with_updates(
                is_active=False,
                is_paused=False,
                last_operation=operation,
                last_result=result,
                native_pause_active=False,
            )
            return result

        request = SpeechRequest.from_segment(
            segment,
            rate_wpm=self.state.current_rate_wpm,
            operation=operation,
        )
        result = self.engine.speak(request)
        if result.success:
            updates = {
                "is_active": True,
                "is_paused": False,
                "current_segment": segment,
                "last_operation": operation,
                "last_result": result,
                "native_pause_active": False,
            }
            if operation == SpeechOperation.REPEAT_SENTENCE:
                updates["last_sentence"] = segment
            elif operation == SpeechOperation.REPEAT_PARAGRAPH:
                updates["last_paragraph"] = segment
            self.state = self.state.with_updates(**updates)
            return result

        self.state = self.state.with_updates(
            is_active=False,
            is_paused=False,
            last_operation=operation,
            last_result=result,
            native_pause_active=False,
        )
        return result

    def _failure(
        self,
        *,
        operation: SpeechOperation,
        code: TTSErrorCode,
        message: str,
        guidance: str,
    ) -> SpeechResult:
        return SpeechResult.failure(
            operation=operation,
            engine_name=getattr(self.engine, "name", None),
            error=TTSError(
                code=code,
                message=message,
                engine_name=getattr(self.engine, "name", None),
            ),
            guidance=guidance,
        )


__all__ = [
    "ReadingController",
]
