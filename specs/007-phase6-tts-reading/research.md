# Phase 6 Research: TTS Reading Controller

## Decision: Use a local eSpeak NG adapter behind a TTS engine interface

**Rationale**: The project constitution and implementation plan require an
initial free local TTS path. eSpeak NG is lightweight, available on Raspberry Pi
Linux distributions, and suitable for deterministic process-boundary tests when
subprocess calls are mocked. Hiding eSpeak NG behind an interface keeps later
Piper or other free local engines replaceable without changing the reading
controller.

**Alternatives considered**: Paid cloud TTS was rejected by the cost policy.
Online-only free TTS was rejected because Phase 6 must remain usable offline.
Piper was kept as a later improvement because it adds heavier model and voice
asset management that is not needed for the first reading controller.

## Decision: Keep reading controller input limited to Phase 5 clean text

**Rationale**: Phase 6 should read approved clean text and preserve Phase 5
logical order. It must not re-clean OCR output, run OCR, translate, capture
images, or parse user voice commands. This keeps the phase independently
testable and prevents engine-specific TTS behavior from leaking into OCR or text
cleanup.

**Alternatives considered**: Combining cleanup and reading in one controller was
rejected because it would duplicate Phase 5 behavior and blur ownership.
Combining voice command parsing with playback control was rejected because that
belongs to a later command-system phase.

## Decision: Clamp speech rate to 80-220 words per minute with a 150 default

**Rationale**: The accepted clarification defines these bounds. Clamping gives a
safe, predictable behavior for all callers and prevents invalid values from
reaching the engine adapter.

**Alternatives considered**: Rejecting invalid rates was rejected because
assistive voice control benefits from forgiving behavior. Allowing engine-native
unbounded values was rejected because it would make behavior inconsistent across
future TTS engines.

## Decision: Segment paragraphs by blank lines and sentences by Arabic and English punctuation

**Rationale**: The accepted clarification defines blank-line paragraph
boundaries and Arabic/English sentence-ending punctuation. Deterministic
segmentation supports repeat behavior without needing NLP models or network
services and preserves the logical order supplied by Phase 5.

**Alternatives considered**: Model-based sentence segmentation was rejected as
too heavy and unnecessary for Phase 6. Splitting only on periods was rejected
because Arabic punctuation and mixed text must be supported.

## Decision: Treat the last successfully requested segment as repeatable history

**Rationale**: TTS engines may not expose precise spoken progress. Tracking the
last requested sentence and paragraph gives deterministic repeat behavior and
avoids guessing ahead. If progress is unknown, continue and repeat operations
use the current segment rather than assuming a later one.

**Alternatives considered**: Tracking actual audio playback progress was
rejected for this phase because eSpeak NG process control does not provide a
portable segment-progress callback. Restarting the whole text for repeat was
rejected because users need sentence and paragraph-level recovery.

## Decision: Implement pause fallback by stopping safely and replaying the current segment

**Rationale**: Native pause/resume may not be available in every free local TTS
engine. The accepted clarification requires a safe stop, preserved current
segment, and clear guidance that continue will replay the segment.

**Alternatives considered**: Reporting pause as unsupported without a usable
continue path was rejected because it weakens accessibility. Simulating precise
pause offsets was rejected because it would require audio progress tracking that
is outside Phase 6.

## Decision: Failed speech leaves reading inactive and preserves prior repeat history

**Rationale**: A failed engine invocation should not leave the assistant in a
misleading active state. Preserving the last successful sentence or paragraph
lets the user recover from a transient failure without losing known-good repeat
history.

**Alternatives considered**: Clearing all reading state on failure was rejected
because it discards useful recovery context. Leaving reading active was rejected
because it misrepresents the audible state.

## Decision: Log only safe speech metadata by default

**Rationale**: Spoken text can contain sensitive documents, receipts, medicine
instructions, or personal information. Default logs should include operation,
engine name, success/failure, duration, rate, fallback use, and error category
only, never raw text, clean text, spoken text, or snippets.

**Alternatives considered**: Logging text snippets for debugging was rejected as
a default behavior. Any sensitive text logging must remain explicitly configured
outside Phase 6 defaults.
